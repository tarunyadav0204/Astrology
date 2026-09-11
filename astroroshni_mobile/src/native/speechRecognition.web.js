/**
 * Web Speech API adapter used by SpeechChatScreen on Chrome/PWA.
 * Its Promise contract matches the native module: resolve with the final
 * transcript only after recognition stops, while publishing interim strings.
 */
const getRecognitionCtor = () => {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
};

const toBrowserLanguage = (language) => {
  const raw = String(language || 'english').trim().toLowerCase();
  if (raw === 'hindi' || raw === 'hi' || raw.startsWith('hi-')) return 'hi-IN';
  if (/^[a-z]{2}-[a-z]{2}$/i.test(raw)) return raw;
  return 'en-IN';
};

const recognitionError = (code, fallback) => {
  const error = new Error(fallback || 'Speech recognition failed.');
  error.code = code || 'unknown';
  return error;
};

let activeSession = null;
let partialListener = null;
let debugListener = null;

const mergeTranscriptFragments = (fragments = []) => {
  let merged = [];
  fragments.forEach((fragment) => {
    const next = String(fragment || '').trim().split(/\s+/).filter(Boolean);
    if (!next.length) return;
    if (!merged.length) {
      merged = next;
      return;
    }
    const currentLower = merged.map((word) => word.toLocaleLowerCase());
    const nextLower = next.map((word) => word.toLocaleLowerCase());
    const shared = Math.min(currentLower.length, nextLower.length);
    if (currentLower.slice(0, shared).every((word, index) => word === nextLower[index])) {
      if (next.length > merged.length) merged = next;
      return;
    }
    let overlap = shared;
    while (overlap > 0) {
      const suffix = currentLower.slice(currentLower.length - overlap);
      const prefix = nextLower.slice(0, overlap);
      if (suffix.every((word, index) => word === prefix[index])) break;
      overlap -= 1;
    }
    merged = [...merged, ...next.slice(overlap)];
  });
  return merged.join(' ').trim();
};

const settleSession = (session, error) => {
  if (!session || session.settled) return;
  session.settled = true;
  if (activeSession === session) activeSession = null;
  if (error) session.reject(error);
  else if (session.latestText.trim()) session.resolve(session.latestText.trim());
  else session.reject(recognitionError('no_speech', 'I could not hear any speech. Please try again.'));
};

export const speechRecognition = {
  async isAvailable() {
    return Boolean(getRecognitionCtor());
  },

  startListening(language) {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      return Promise.reject(recognitionError(
        'not_available',
        'Speech recognition is not available in this browser.'
      ));
    }

    if (activeSession) {
      const previous = activeSession;
      previous.cancelled = true;
      try {
        previous.recognition.abort();
      } catch (_) {
        settleSession(previous, recognitionError('cancelled', 'Speech recognition was cancelled.'));
      }
    }

    return new Promise((resolve, reject) => {
      const recognition = new Ctor();
      const session = {
        recognition,
        resolve,
        reject,
        latestText: '',
        settled: false,
        cancelled: false,
      };
      activeSession = session;

      // Keep collecting after the browser marks an individual phrase final.
      // SpeechChatScreen owns the deliberate silence timer and stops us after a
      // natural pause, so a thinking pause does not submit half a question.
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.lang = toBrowserLanguage(language);

      recognition.onstart = () => debugListener?.({ event: 'onReadyForSpeech' });
      recognition.onaudiostart = () => debugListener?.({ event: 'onReadyForSpeech' });
      recognition.onspeechstart = () => debugListener?.({ event: 'onBeginningOfSpeech' });
      recognition.onresult = (event) => {
        const fragments = [];
        let hasFinalResult = false;
        for (let i = 0; i < event.results.length; i += 1) {
          fragments.push(event.results[i][0]?.transcript || '');
          if (event.results[i].isFinal) hasFinalResult = true;
        }
        const text = mergeTranscriptFragments(fragments);
        if (text) {
          session.latestText = text;
          partialListener?.(text);
          debugListener?.({ event: hasFinalResult ? 'onResults' : 'onPartialResults' });
        }
      };

      recognition.onerror = (event) => {
        const browserCode = String(event?.error || 'unknown');
        const code = session.cancelled || browserCode === 'aborted'
          ? 'cancelled'
          : browserCode === 'no-speech'
            ? 'no_speech'
            : browserCode;
        debugListener?.({ event: 'onError', code, message: event?.message || browserCode });
        settleSession(
          session,
          recognitionError(
            code,
            code === 'not-allowed'
              ? 'Microphone access is blocked in Chrome. Allow it in site settings and try again.'
              : code === 'no_speech'
                ? 'I could not hear any speech. Please try again.'
                : 'Speech recognition stopped unexpectedly. Please try again.'
          )
        );
      };

      recognition.onend = () => {
        debugListener?.({ event: 'resolveWithLatestTranscript' });
        if (session.cancelled) {
          settleSession(session, recognitionError('cancelled', 'Speech recognition was cancelled.'));
          return;
        }
        settleSession(session);
      };

      try {
        recognition.start();
      } catch (error) {
        settleSession(session, recognitionError(error?.name || 'start_failed', error?.message));
      }
    });
  },

  stopListening() {
    const session = activeSession;
    if (!session) return;
    try {
      session.recognition.stop();
    } catch (_) {
      settleSession(session);
    }
  },

  cancelListening() {
    const session = activeSession;
    if (!session) return;
    session.cancelled = true;
    try {
      session.recognition.abort();
    } catch (_) {
      settleSession(session, recognitionError('cancelled', 'Speech recognition was cancelled.'));
    }
  },

  addPartialListener(listener) {
    partialListener = listener;
    return {
      remove() {
        if (partialListener === listener) partialListener = null;
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
