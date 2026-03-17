/**
 * Lazy access to textToSpeech so expo-av is not loaded at app startup.
 * Loading expo-av on first paint can cause iOS crashes; require it only when
 * the user actually uses TTS/podcast features.
 * If the native module 'ExponentAV' is not in the build, we return a no-op
 * so the app does not crash (podcast/TTS will be disabled until native rebuild).
 */
let _textToSpeech = null;
let _textToSpeechFailed = false;

const noop = () => {};
const noopAsync = () => Promise.resolve();

const noopTts = {
  speak: noopAsync,
  stop: noopAsync,
  isSpeaking: () => Promise.resolve(false),
  playPodcast: noopAsync,
  playPodcastFromStream: noopAsync,
  pausePodcast: noopAsync,
  resumePodcast: noopAsync,
  stopPodcast: noopAsync,
  seekPodcast: noopAsync,
  setPodcastRate: noopAsync,
  getAvailableVoices: () => Promise.resolve([]),
};

export function getTextToSpeech() {
  if (_textToSpeechFailed) return noopTts;
  if (_textToSpeech == null) {
    try {
      _textToSpeech = require('./textToSpeech').textToSpeech;
    } catch (e) {
      _textToSpeechFailed = true;
      if (__DEV__) {
        console.warn('[TTS] Could not load textToSpeech (ExponentAV native module may be missing). Rebuild the app with expo-av linked.', e?.message || e);
      }
      return noopTts;
    }
  }
  return _textToSpeech;
}
