import * as Speech from 'expo-speech';

export const textToSpeech = {
  speak: (text, options = {}) => {
    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/###\s*(.*?)$/gm, '$1')
      .replace(/•\s*/g, '')
      .replace(/\n+/g, '. ')
      .replace(/\s+/g, ' ')
      .trim();

    Speech.speak(cleanText, {
      language: options.language || 'en-US',
      pitch: options.pitch || 1,
      rate: options.rate || 0.9,
      ...options,
    });
  },

  stop: () => {
    Speech.stop();
  },

  isSpeaking: () => {
    return Speech.isSpeakingAsync();
  },

  getAvailableVoices: () => {
    return Speech.getAvailableVoicesAsync();
  },
};