import { Audio, InterruptionModeIOS, InterruptionModeAndroid } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import { chatAPI } from '../services/api';

let currentSound = null;
/** Callbacks for the currently loaded podcast (onPause, onResume, onStop). Cleared when stop or done. */
let podcastCallbacks = null;
/** Temp file path for current podcast; cleared when playback ends or stops so we can delete it. */
let podcastTempUri = null;
/** Guards seek: only one setPositionAsync at a time; pending seek applied after in-flight seek completes. */
let seekPromise = null;
let pendingSeekMillis = null;

export const textToSpeech = {
  async speak(text, { language = 'english', voiceName, onDone, onError } = {}) {
    try {
      if (!text || !text.trim()) return;

      if (currentSound) {
        try {
          await currentSound.stopAsync();
          await currentSound.unloadAsync();
        } catch {
          // ignore
        }
        currentSound = null;
      }

      const lang = language?.toLowerCase().startsWith('hi') ? 'hi' : 'en';
      console.log('[TTS] Requesting audio from backend', { lang, voiceName, textLength: text.length });
      const response = await chatAPI.tts(text, lang, voiceName);
      console.log('[TTS] Backend response received', { hasData: !!response?.data, keys: Object.keys(response?.data || {}) });
      const base64Audio = response?.data?.audio;
      if (!base64Audio || typeof base64Audio !== 'string') {
        console.warn('[TTS] Missing or invalid audio field in response', response?.data);
        if (onError) onError(new Error('TTS: missing audio data from server'));
        return;
      }
      const dataUri = `data:audio/mpeg;base64,${base64Audio}`;
      console.log('[TTS] Creating sound from data URI, base64Length:', base64Audio.length);

      const { sound } = await Audio.Sound.createAsync({ uri: dataUri });
      console.log('[TTS] Sound created, starting playback');
      currentSound = sound;

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          if (onDone) onDone();
          sound.unloadAsync();
          currentSound = null;
        }
      });

      await sound.playAsync();
    } catch (e) {
      console.error('[TTS] speak error', e);
      if (onError) onError(e);
    }
  },

  async stop() {
    if (currentSound) {
      try {
        await currentSound.stopAsync();
        await currentSound.unloadAsync();
      } catch {
        // ignore
      }
      currentSound = null;
    }
  },

  async isSpeaking() {
    // We don't track this from Audio; keep for API compatibility if needed
    return !!currentSound;
  },

  async playPodcast(messageContent, { language = 'english', messageId, sessionId, preview, onStart, onDone, onError, onPause, onResume, onStop, onProgress } = {}) {
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
      console.log('[Podcast] Requesting podcast audio', { lang, messageId: messageId || 'none', length: messageContent?.length });
      const response = await chatAPI.getPodcastAudio(messageContent, lang, messageId || null, sessionId || null, preview || null);
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

      // Full-volume podcast: speaker (not earpiece), silent mode OK, take over session (DoNotMix) so we are not ducked
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
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
        staysActiveInBackground: false,
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
      const response = await chatAPI.getTtsVoices();
      const voices = response?.data?.voices || [];
      // Map backend voice objects into a simpler shape for UI:
      // identifier = Google voice name, language = first language code
      return voices.map((v) => ({
        identifier: v.name,
        language: (v.language_codes && v.language_codes[0]) || '',
        name: v.name,
        gender: v.ssml_gender,
      }));
    } catch (e) {
      console.error('[TTS] getAvailableVoices error', e);
      // Fallback to a couple of sensible defaults
      return [
        { identifier: 'en-IN-Neural2-A', language: 'en-IN', name: 'English (India) A', gender: 'FEMALE' },
        { identifier: 'hi-IN-Neural2-C', language: 'hi-IN', name: 'Hindi (India) C', gender: 'FEMALE' },
      ];
    }
  },
};

