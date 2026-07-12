import { NativeEventEmitter, NativeModules, Platform } from 'react-native';

const nativeModule = NativeModules.SpeechRecognition;
const partialEmitter = nativeModule ? new NativeEventEmitter(nativeModule) : null;

const unavailableMessage =
  Platform.OS === 'android' || Platform.OS === 'ios'
    ? 'Native speech recognition is not available in this build. Please use a development build instead of Expo Go.'
    : 'Native speech recognition is not available on this platform.';

const ensureNativeModule = () => {
  if (!nativeModule) {
    const error = new Error(unavailableMessage);
    error.code = 'not_available';
    throw error;
  }
  return nativeModule;
};

export const speechRecognition = {
  async isAvailable() {
    const module = ensureNativeModule();
    return Boolean(await module.isAvailable());
  },

  async startListening(language) {
    const module = ensureNativeModule();
    return module.startListening(language);
  },

  stopListening() {
    const module = ensureNativeModule();
    module.stopListening();
  },

  cancelListening() {
    const module = ensureNativeModule();
    module.cancelListening();
  },

  addPartialListener(listener) {
    if (!partialEmitter) {
      return { remove() {} };
    }
    return partialEmitter.addListener('SpeechRecognitionPartial', listener);
  },

  addDebugListener(listener) {
    if (!partialEmitter) {
      return { remove() {} };
    }
    return partialEmitter.addListener('SpeechRecognitionDebug', listener);
  },

  getUnavailableMessage() {
    return unavailableMessage;
  },
};
