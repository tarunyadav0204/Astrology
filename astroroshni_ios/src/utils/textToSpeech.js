import * as Speech from 'expo-speech';

export const textToSpeech = {
  speak: (text, options = {}) => {
    const defaultOptions = {
      language: 'en-IN',
      pitch: 1.0,
      rate: 0.9,
    };
    
    Speech.speak(text, { ...defaultOptions, ...options });
  },
  
  stop: () => {
    Speech.stop();
  },
  
  isSpeaking: () => {
    return Speech.isSpeakingAsync();
  },
  
  getAvailableVoices: () => {
    return Speech.getAvailableVoicesAsync();
  }
};
