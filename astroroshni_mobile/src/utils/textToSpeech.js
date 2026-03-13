import { Audio } from 'expo-av';
import { chatAPI } from '../services/api';

let currentSound = null;
/** Callbacks for the currently loaded podcast (onPause, onResume, onStop). Cleared when stop or done. */
let podcastCallbacks = null;

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

  async playPodcast(messageContent, { language = 'english', messageId, onStart, onDone, onError, onPause, onResume, onStop } = {}) {
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
      }

      const lang = language?.toLowerCase().startsWith('hi') ? 'hi' : 'en';
      console.log('[Podcast] Requesting podcast audio', { lang, messageId: messageId || 'none', length: messageContent?.length });
      const response = await chatAPI.getPodcastAudio(messageContent, lang, messageId || null);
      const base64Audio = response?.data?.audio;
      if (!base64Audio || typeof base64Audio !== 'string') {
        if (onError) onError(new Error('Podcast: missing audio from server'));
        return;
      }
      const dataUri = `data:audio/mpeg;base64,${base64Audio}`;
      const { sound } = await Audio.Sound.createAsync({ uri: dataUri });
      currentSound = sound;
      podcastCallbacks = { onPause, onResume, onStop };

      sound.setOnPlaybackStatusUpdate((status) => {
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
      console.error('[TTS] playPodcast error', e);
      podcastCallbacks = null;
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

