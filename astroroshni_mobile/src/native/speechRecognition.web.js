/**
 * Web Speech API adapter used by SpeechChatScreen on browsers.
 */
const getRecognitionCtor = () => {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
};

let activeRecognition = null;
let partialListener = null;
let debugListener = null;

export const speechRecognition = {
  async isAvailable() {
    return Boolean(getRecognitionCtor());
  },

  async startListening(language) {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      const error = new Error('Speech recognition is not available in this browser.');
      error.code = 'not_available';
      throw error;
    }
    if (activeRecognition) {
      try {
        activeRecognition.abort();
      } catch (_) {
        /* ignore */
      }
    }
    const recognition = new Ctor();
    activeRecognition = recognition;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = language || 'en-IN';

    recognition.onresult = (event) => {
      let interim = '';
      let finalText = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0]?.transcript || '';
        if (event.results[i].isFinal) finalText += transcript;
        else interim += transcript;
      }
      const text = (finalText || interim || '').trim();
      if (text && partialListener) {
        partialListener({ text, isFinal: Boolean(finalText) });
      }
    };

    recognition.onerror = (event) => {
      debugListener?.({ type: 'error', error: event?.error || 'unknown' });
    };

    recognition.onend = () => {
      if (activeRecognition === recognition) activeRecognition = null;
      debugListener?.({ type: 'end' });
    };

    recognition.start();
    return true;
  },

  stopListening() {
    try {
      activeRecognition?.stop?.();
    } catch (_) {
      /* ignore */
    }
    activeRecognition = null;
  },

  cancelListening() {
    try {
      activeRecognition?.abort?.();
    } catch (_) {
      /* ignore */
    }
    activeRecognition = null;
  },

  addPartialListener(listener) {
    partialListener = (payload) => {
      try {
        listener(payload);
      } catch (_) {
        /* ignore */
      }
    };
    return {
      remove() {
        if (partialListener) partialListener = null;
      },
    };
  },

  addDebugListener(listener) {
    debugListener = listener;
    return {
      remove() {
        if (debugListener === listener) debugListener = null;
      },
    };
  },

  getUnavailableMessage() {
    return 'Speech recognition is not available in this browser.';
  },
};
