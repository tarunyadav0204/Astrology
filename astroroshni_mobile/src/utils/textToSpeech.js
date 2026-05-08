import { Audio, InterruptionModeIOS, InterruptionModeAndroid } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import * as Speech from 'expo-speech';
import { chatAPI } from '../services/api';

let currentSound = null;
let speechTempUri = null;
let speechCallbacks = null;
/** Callbacks for the currently loaded podcast (onPause, onResume, onStop). Cleared when stop or done. */
let podcastCallbacks = null;
/** Temp file path for current podcast; cleared when playback ends or stops so we can delete it. */
let podcastTempUri = null;
/** Guards seek: only one setPositionAsync at a time; pending seek applied after in-flight seek completes. */
let seekPromise = null;
let pendingSeekMillis = null;
let speechProvider = 'local';

const SPEECH_PROVIDER_LOCAL = 'local';
const SPEECH_PROVIDER_GOOGLE = 'google';

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
  speechCallbacks = null;
  podcastCallbacks = null;
  if (speechTempUri) {
    FileSystem.deleteAsync(speechTempUri, { idempotent: true }).catch(() => {});
    speechTempUri = null;
  }
  if (podcastTempUri) {
    FileSystem.deleteAsync(podcastTempUri, { idempotent: true }).catch(() => {});
    podcastTempUri = null;
  }
};

const normalizeVoice = (voice) => ({
  identifier: voice.identifier,
  language: voice.language || '',
  name: voice.name || voice.identifier || '',
  quality: voice.quality || null,
});

const FEMALE_HINTS = [
  'female', 'woman', 'samantha', 'karen', 'moira', 'tessa', 'veena',
  'aditi', 'neerja', 'priya', 'raveena', 'kavya', 'pooja', 'shruti',
];

const MALE_HINTS = [
  'male', 'man', 'daniel', 'alex', 'fred', 'jorge', 'rishi', 'aarav',
  'male_', '_male',
];

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
    if (language.startsWith('en') && !language.endsWith('-in')) score += 140;
    else if (language === 'en-in') score += 100;
    else if (language.startsWith('en')) score += 90;
    else if (language.startsWith('hi')) score += 10;
  }

  if (FEMALE_HINTS.some((hint) => name.includes(hint) || identifier.includes(hint))) score += 80;
  if (MALE_HINTS.some((hint) => name.includes(hint) || identifier.includes(hint))) score -= 50;
  if (lang !== 'hi' && (name.includes('india') || name.includes('indian') || language.endsWith('-in'))) score -= 20;
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
      if (__DEV__) {
        console.log('[TTS] Ranked system voices', ranked.slice(0, 8).map((voice) => ({
          identifier: voice.identifier,
          name: voice.name,
          language: voice.language,
          quality: voice.quality,
          score: scoreVoice(voice, lang),
        })));
      }
      return ranked[0] || null;
  } catch (e) {
    console.warn('[TTS] Could not inspect system voices', e?.message || e);
    return null;
  }
};

const normalizeSpeechProvider = (provider) => (
  String(provider || '').trim().toLowerCase() === SPEECH_PROVIDER_GOOGLE
    ? SPEECH_PROVIDER_GOOGLE
    : SPEECH_PROVIDER_LOCAL
);

const playbackLangCode = (language) => (
  language?.toLowerCase?.().startsWith?.('hi') ? 'hi' : 'en'
);

const cleanupSpeechPlayback = () => {
  speechCallbacks = null;
  if (speechTempUri) {
    FileSystem.deleteAsync(speechTempUri, { idempotent: true }).catch(() => {});
    speechTempUri = null;
  }
};

const speakLocally = async (text, { language = 'english', voiceName, onDone, onError } = {}) => {
  const lang = playbackLangCode(language);
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
    pitch: lang === 'hi' ? 1.02 : 1.06,
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
};

export const textToSpeech = {
  setSpeechProvider(provider) {
    speechProvider = normalizeSpeechProvider(provider);
  },

  getSpeechProvider() {
    return speechProvider;
  },

  async speak(text, { language = 'english', voiceName, onDone, onError, onTimeline, onProgress } = {}) {
    try {
      if (!text || !text.trim()) return;

      if (speechProvider === SPEECH_PROVIDER_GOOGLE) {
        try {
          await textToSpeech.playServerTts(text, {
            language,
            voiceName,
            onDone,
            onTimeline,
            onProgress,
            suppressErrorCallback: true,
          });
          return;
        } catch (googleError) {
          console.warn('[TTS] Google speech failed, falling back to local speech', googleError?.message || googleError);
        }
      }

      await Speech.stop();
      await stopLoadedAudio();
      await speakLocally(text, { language, voiceName, onDone, onError });
    } catch (e) {
      console.error('[TTS] speak error', e);
      if (onError) onError(e);
    }
  },

  async playServerTts(
    text,
    { language = 'english', voiceName, onDone, onError, onTimeline, onProgress, suppressErrorCallback = false } = {}
  ) {
    try {
      if (!text || !text.trim()) return;

      await Speech.stop();
      await stopLoadedAudio();

      const lang = playbackLangCode(language);
      console.log('[TTS] Requesting backend Google TTS', {
        lang,
        voiceName: voiceName || null,
        length: String(text).trim().length,
      });

      const response = await chatAPI.tts(text, lang, voiceName, true);
      const base64Audio = response?.data?.audio;
      if (!base64Audio || typeof base64Audio !== 'string') {
        throw new Error('Google TTS: missing audio from server');
      }
      const responseTimeline = Array.isArray(response?.data?.timeline) ? response.data.timeline : [];
      if (responseTimeline.length && onTimeline) {
        onTimeline(responseTimeline);
      }

      speechTempUri = `${FileSystem.cacheDirectory}speech_${Date.now()}.mp3`;
      await FileSystem.writeAsStringAsync(speechTempUri, base64Audio, {
        encoding: FileSystem.EncodingType.Base64,
      });

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
        { uri: speechTempUri },
        { progressUpdateIntervalMillis: 80 }
      );
      currentSound = sound;
      speechCallbacks = { onDone, onError, onProgress };
      await sound.setVolumeAsync(1.0);

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status?.isLoaded && speechCallbacks?.onProgress && status.positionMillis != null) {
          speechCallbacks.onProgress(status.positionMillis, status.durationMillis ?? 0);
        }
        if (status?.didJustFinish) {
          const done = speechCallbacks?.onDone;
          speechCallbacks = null;
          sound.unloadAsync().catch(() => {});
          currentSound = null;
          cleanupSpeechPlayback();
          if (done) done();
        }
      });

      await sound.playAsync();
    } catch (e) {
      console.error('[TTS] playServerTts error', e);
      if (currentSound) {
        try {
          await currentSound.unloadAsync();
        } catch {
          // ignore
        }
        currentSound = null;
      }
      cleanupSpeechPlayback();
      if (!suppressErrorCallback && onError) onError(e);
      throw e;
    }
  },

  async stop() {
    const done = speechCallbacks?.onDone;
    try {
      await Speech.stop();
    } catch {
      // ignore
    }
    await stopLoadedAudio();
    if (done) done();
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
        speechCallbacks = null;
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
        speechCallbacks = null;
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
