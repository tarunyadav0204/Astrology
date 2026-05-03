import { Audio, InterruptionModeIOS, InterruptionModeAndroid } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import * as Speech from 'expo-speech';
import { chatAPI } from '../services/api';

let currentSound = null;
let speechTempUri = null;
/** Callbacks for the currently loaded podcast (onPause, onResume, onStop). Cleared when stop or done. */
let podcastCallbacks = null;
/** Temp file path for current podcast; cleared when playback ends or stops so we can delete it. */
let podcastTempUri = null;
/** Guards seek: only one setPositionAsync at a time; pending seek applied after in-flight seek completes. */
let seekPromise = null;
let pendingSeekMillis = null;

const stopLoadedAudio = async () => {
  if (currentSound) {
    try {
      await currentSound.stopAsync();
      await currentSound.unloadAsync();
    } catch {
      // ignore
    }
    currentSound = null;
  }
  if (speechTempUri) {
    FileSystem.deleteAsync(speechTempUri, { idempotent: true }).catch(() => {});
    speechTempUri = null;
  }
};

const normalizeVoice = (voice) => ({
  identifier: voice.identifier,
  language: voice.language || '',
  name: voice.name || voice.identifier || '',
  quality: voice.quality || null,
});

const scoreVoice = (voice, lang) => {
  const identifier = String(voice.identifier || '').toLowerCase();
  const name = String(voice.name || '').toLowerCase();
  const language = String(voice.language || '').toLowerCase();
  let score = 0;

  if (lang === 'hi') {
    if (language === 'hi-in') score += 120;
    else if (language.startsWith('hi')) score += 100;
    else if (language === 'en-in') score += 40;
  } else {
    if (language === 'en-in') score += 120;
    else if (language.startsWith('en')) score += 100;
    else if (language.startsWith('hi')) score += 20;
  }

  if (name.includes('female') || name.includes('woman') || identifier.includes('female')) score += 30;
  if (name.includes('india') || name.includes('indian') || language.endsWith('-in')) score += 20;
  if (voice.quality === 'Enhanced') score += 10;
  if (voice.quality === 'Default') score += 5;

  return score;
};

const pickSystemVoice = async (lang, requestedVoiceName) => {
  try {
    const rawVoices = await Speech.getAvailableVoicesAsync();
    const voices = Array.isArray(rawVoices) ? rawVoices.map(normalizeVoice) : [];
    if (!voices.length) return null;

    if (requestedVoiceName) {
      const requested = String(requestedVoiceName).toLowerCase();
      const exactMatch = voices.find((voice) =>
        String(voice.identifier || '').toLowerCase() === requested ||
        String(voice.name || '').toLowerCase() === requested
      );
      if (exactMatch) return exactMatch;
    }

    const ranked = [...voices].sort((a, b) => scoreVoice(b, lang) - scoreVoice(a, lang));
    return ranked[0] || null;
  } catch (e) {
    console.warn('[TTS] Could not inspect system voices', e?.message || e);
    return null;
  }
};

export const textToSpeech = {
  async speak(text, { language = 'english', voiceName, onDone, onError } = {}) {
    try {
      if (!text || !text.trim()) return;

      await Speech.stop();
      await stopLoadedAudio();
      const lang = language?.toLowerCase().startsWith('hi') ? 'hi' : 'en';
      const voice = await pickSystemVoice(lang, voiceName);
      const speechLanguage = voice?.language || (lang === 'hi' ? 'hi-IN' : 'en-IN');
      console.log('[TTS] Using system speech voice', {
        lang,
        voiceIdentifier: voice?.identifier || null,
        voiceName: voice?.name || null,
        speechLanguage,
      });

      Speech.speak(text, {
        language: speechLanguage,
        voice: voice?.identifier,
        rate: lang === 'hi' ? 0.92 : 0.95,
        pitch: 1.0,
        onDone: () => {
          if (onDone) onDone();
        },
        onStopped: () => {
          if (onDone) onDone();
        },
        onError: (e) => {
          console.error('[TTS] system speech error', e);
          if (onError) onError(e);
        },
      });
    } catch (e) {
      console.error('[TTS] speak error', e);
      if (onError) onError(e);
    }
  },

  async stop() {
    try {
      await Speech.stop();
    } catch {
      // ignore
    }
    await stopLoadedAudio();
  },

  async isSpeaking() {
    try {
      return !!currentSound || await Speech.isSpeakingAsync();
    } catch {
      return !!currentSound;
    }
  },

  async playPodcast(messageContent, { language = 'english', messageId, sessionId, preview, nativeName, onStart, onDone, onError, onPause, onResume, onStop, onProgress } = {}) {
    try {
      if (!messageContent || !String(messageContent).trim()) return;

      if (currentSound) {
        try {
          await currentSound.stopAsync();
          await currentSound.unloadAsync();
        } catch {
          // ignore
        }
        currentSound = null;
        podcastCallbacks = null;
        if (podcastTempUri) {
          FileSystem.deleteAsync(podcastTempUri, { idempotent: true }).catch(() => {});
          podcastTempUri = null;
        }
      }

      const lang = language?.toLowerCase().startsWith('hi') ? 'hi' : 'en';
      console.log('[Podcast] Requesting podcast audio', { lang, messageId: messageId || 'none', length: messageContent?.length, nativeName: nativeName || null });
      const response = await chatAPI.getPodcastAudio(messageContent, lang, messageId || null, sessionId || null, preview || null, nativeName || null);
      const base64Audio = response?.data?.audio;
      if (!base64Audio || typeof base64Audio !== 'string') {
        if (onError) onError(new Error('Podcast: missing audio from server'));
        return;
      }

      // On real devices, data URIs often fail for large audio. Write to temp file and use file URI.
      const filename = `podcast_${messageId || Date.now()}.mp3`;
      podcastTempUri = `${FileSystem.cacheDirectory}${filename}`;
      await FileSystem.writeAsStringAsync(podcastTempUri, base64Audio, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Full-volume podcast: speaker (not earpiece), silent mode OK, keep playing when screen off / in background
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
        allowsRecordingIOS: false,
        playThroughEarpieceAndroid: false,
        shouldDuckAndroid: false,
        interruptionModeIOS: InterruptionModeIOS.DoNotMix,
        interruptionModeAndroid: InterruptionModeAndroid.DoNotMix,
      });

      const { sound } = await Audio.Sound.createAsync(
        { uri: podcastTempUri },
        { progressUpdateIntervalMillis: 250 }
      );
      currentSound = sound;
      await sound.setVolumeAsync(1.0);
      podcastCallbacks = { onPause, onResume, onStop, onProgress };

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && podcastCallbacks?.onProgress && status.positionMillis != null) {
          podcastCallbacks.onProgress(status.positionMillis, status.durationMillis ?? 0);
        }
        if (status.didJustFinish) {
          podcastCallbacks = null;
          if (onDone) onDone();
          sound.unloadAsync();
          currentSound = null;
          if (podcastTempUri) {
            FileSystem.deleteAsync(podcastTempUri, { idempotent: true }).catch(() => {});
            podcastTempUri = null;
          }
        }
      });

      await sound.playAsync();
      if (onStart) onStart();
    } catch (e) {
      const status = e?.response?.status;
      const detail = e?.response?.data?.detail;
      if (status >= 500 && detail) {
        console.error('[TTS] playPodcast error', status, detail, e);
      } else {
        console.error('[TTS] playPodcast error', e);
      }
      podcastCallbacks = null;
      if (podcastTempUri) {
        FileSystem.deleteAsync(podcastTempUri, { idempotent: true }).catch(() => {});
        podcastTempUri = null;
      }
      if (onError) onError(e);
    }
  },

  async pausePodcast() {
    if (currentSound && podcastCallbacks) {
      try {
        await currentSound.pauseAsync();
        if (podcastCallbacks.onPause) podcastCallbacks.onPause();
      } catch (e) {
        console.error('[TTS] pausePodcast error', e);
      }
    }
  },

  async resumePodcast() {
    if (currentSound && podcastCallbacks) {
      try {
        await currentSound.playAsync();
        if (podcastCallbacks.onResume) podcastCallbacks.onResume();
      } catch (e) {
        console.error('[TTS] resumePodcast error', e);
      }
    }
  },

  async stopPodcast() {
    seekPromise = null;
    pendingSeekMillis = null;
    if (currentSound) {
      try {
        await currentSound.stopAsync();
        await currentSound.unloadAsync();
      } catch {
        // ignore
      }
      currentSound = null;
      if (podcastCallbacks && podcastCallbacks.onStop) podcastCallbacks.onStop();
      podcastCallbacks = null;
      if (podcastTempUri) {
        FileSystem.deleteAsync(podcastTempUri, { idempotent: true }).catch(() => {});
        podcastTempUri = null;
      }
    }
  },

  async setPodcastRate(rate) {
    if (!currentSound) return;
    try {
      const r = Math.min(2, Math.max(0.5, Number(rate) || 1));
      await currentSound.setRateAsync(r, true);
    } catch (e) {
      console.error('[TTS] setPodcastRate error', e);
    }
  },

  async seekPodcast(positionMillis) {
    if (!currentSound) return;
    const isInterrupted = (e) => e?.message === 'Seeking interrupted.' || String(e?.message || '').includes('Seeking interrupted');
    const doSeek = async (pos) => {
      const posInt = Math.floor(pos);
      try {
        if (!currentSound) return;
        const status = await currentSound.getStatusAsync();
        const wasPlaying = status.isLoaded && status.shouldPlay;
        if (wasPlaying) await currentSound.pauseAsync();
        await currentSound.setPositionAsync(posInt);
        if (wasPlaying) await currentSound.playAsync();
      } catch (e) {
        if (isInterrupted(e)) return; // non-fatal
        console.error('[TTS] seekPodcast error', e);
      } finally {
        seekPromise = null;
        if (currentSound && pendingSeekMillis != null) {
          const next = pendingSeekMillis;
          pendingSeekMillis = null;
          seekPromise = doSeek(next);
        }
      }
    };
    if (seekPromise) {
      pendingSeekMillis = positionMillis;
      return;
    }
    seekPromise = doSeek(positionMillis);
  },

  async playPodcastFromStream(streamUrl, authToken, { onStart, onDone, onError, onPause, onResume, onStop, onProgress } = {}) {
    if (!streamUrl || !authToken) {
      if (onError) onError(new Error('Stream URL and auth token required'));
      return;
    }
    try {
      if (currentSound) {
        try {
          await currentSound.stopAsync();
          await currentSound.unloadAsync();
        } catch {
          // ignore
        }
        currentSound = null;
        podcastCallbacks = null;
        if (podcastTempUri) {
          FileSystem.deleteAsync(podcastTempUri, { idempotent: true }).catch(() => {});
          podcastTempUri = null;
        }
      }
      podcastTempUri = null;

      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
        allowsRecordingIOS: false,
        playThroughEarpieceAndroid: false,
        shouldDuckAndroid: false,
        interruptionModeIOS: InterruptionModeIOS.DoNotMix,
        interruptionModeAndroid: InterruptionModeAndroid.DoNotMix,
      });

      const { sound } = await Audio.Sound.createAsync(
        { uri: streamUrl, headers: { Authorization: `Bearer ${authToken}` } },
        { progressUpdateIntervalMillis: 250 }
      );
      currentSound = sound;
      await sound.setVolumeAsync(1.0);
      podcastCallbacks = { onPause, onResume, onStop, onProgress };

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && podcastCallbacks?.onProgress && status.positionMillis != null) {
          podcastCallbacks.onProgress(status.positionMillis, status.durationMillis ?? 0);
        }
        if (status.didJustFinish) {
          podcastCallbacks = null;
          if (onDone) onDone();
          sound.unloadAsync();
          currentSound = null;
        }
      });

      await sound.playAsync();
      if (onStart) onStart();
    } catch (e) {
      console.error('[TTS] playPodcastFromStream error', e);
      podcastCallbacks = null;
      if (onError) onError(e);
    }
  },

  async getAvailableVoices() {
    try {
      const voices = await Speech.getAvailableVoicesAsync();
      return Array.isArray(voices)
        ? voices.map((voice) => ({
            identifier: voice.identifier,
            language: voice.language || '',
            name: voice.name || voice.identifier || '',
            quality: voice.quality || '',
          }))
        : [];
    } catch (e) {
      console.error('[TTS] getAvailableVoices error', e);
      return [];
    }
  },
};
