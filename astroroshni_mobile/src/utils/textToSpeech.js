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
const serverTtsInflight = new Map();

const SPEECH_PROVIDER_LOCAL = 'local';
const SPEECH_PROVIDER_GOOGLE = 'google';
const markHandledError = (error) => {
  if (error && typeof error === 'object') error.__ttsHandled = true;
  return error;
};

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

const stopLoadedAudioImmediately = () => {
  const sound = currentSound;
  currentSound = null;
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
  if (!sound) return;
  try {
    sound.setOnPlaybackStatusUpdate?.(null);
  } catch {
    // ignore
  }
  sound.stopAsync?.()
    .catch(() => {})
    .finally(() => {
      sound.unloadAsync?.().catch(() => {});
    });
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

const hashText = (value) => {
  const text = String(value || '');
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
};

const getServerTtsCacheKey = (text, { language = 'english', voiceName, cacheKey, prepareSpoken = false } = {}) => (
  String(cacheKey || '').trim()
  || [
    'v2',
    playbackLangCode(language),
    String(voiceName || 'default').trim() || 'default',
    prepareSpoken ? 'prepared' : 'plain',
    hashText(String(text || '').replace(/\s+/g, ' ').trim()),
  ].join('_')
);

const getServerTtsCacheUri = (key) => `${FileSystem.cacheDirectory}tts_${hashText(key)}.mp3`;

const splitForStreamingTts = (text, maxChars = 260) => {
  const raw = String(text || '').replace(/\s+/g, ' ').trim();
  if (!raw) return [];
  const sentences = raw.match(/[^.!?।]+[.!?।]+|[^.!?।]+$/g) || [raw];
  const chunks = [];
  let current = '';
  sentences.forEach((sentence) => {
    const part = sentence.trim();
    if (!part) return;
    const candidate = current ? `${current} ${part}` : part;
    if (candidate.length <= maxChars) {
      current = candidate;
      return;
    }
    if (current) chunks.push(current);
    if (part.length <= maxChars) {
      current = part;
      return;
    }
    for (let i = 0; i < part.length; i += maxChars) {
      chunks.push(part.slice(i, i + maxChars).trim());
    }
    current = '';
  });
  if (current) chunks.push(current);
  return chunks.filter(Boolean);
};

const synthesizeServerTtsToCache = async (
  text,
  { language = 'english', voiceName, cacheKey, prepareSpoken = false } = {}
) => {
  const spoken = String(text || '').trim();
  if (!spoken) return null;
  const key = getServerTtsCacheKey(spoken, { language, voiceName, cacheKey, prepareSpoken });
  const uri = getServerTtsCacheUri(key);
  try {
    const info = await FileSystem.getInfoAsync(uri);
    if (info?.exists && Number(info?.size || 0) > 0) {
      console.log('[TTS] cache hit', { key, uri, size: info.size || null });
      return { uri, key, cached: true };
    }
  } catch {
    // Continue to synthesize if cache inspection fails.
  }

  if (serverTtsInflight.has(key)) {
    return serverTtsInflight.get(key);
  }

  const promise = (async () => {
    const lang = playbackLangCode(language);
    console.log('[TTS] Requesting backend Google TTS', {
      lang,
      voiceName: voiceName || null,
      length: spoken.length,
      cacheKey: key,
      prepareSpoken,
    });

    const response = await chatAPI.tts(spoken, lang, voiceName, false, prepareSpoken);
    const base64Audio = response?.data?.audio;
    if (!base64Audio || typeof base64Audio !== 'string') {
      throw new Error('Google TTS: missing audio from server');
    }
    await FileSystem.writeAsStringAsync(uri, base64Audio, {
      encoding: FileSystem.EncodingType.Base64,
    });
    console.log('[TTS] Google TTS cached', {
      key,
      uri,
      audioChars: base64Audio.length,
    });
    return { uri, key, cached: false };
  })();

  serverTtsInflight.set(key, promise);
  try {
    return await promise;
  } finally {
    serverTtsInflight.delete(key);
  }
};

const cleanupSpeechPlayback = () => {
  speechCallbacks = null;
  if (speechTempUri) {
    FileSystem.deleteAsync(speechTempUri, { idempotent: true }).catch(() => {});
    speechTempUri = null;
  }
};

const speakLocally = async (text, { language = 'english', voiceName, onDone, onError, onStart } = {}) => {
  const lang = playbackLangCode(language);
  const voice = await pickSystemVoice(lang, voiceName);
  const speechLanguage = voice?.language || (lang === 'hi' ? 'hi-IN' : 'en-IN');
  console.log('[TTS] Using system speech voice', {
    lang,
    voiceIdentifier: voice?.identifier || null,
    voiceName: voice?.name || null,
    speechLanguage,
  });

  return new Promise((resolve, reject) => {
    let finished = false;
    const finish = (cb, value, shouldReject = false) => {
      if (finished) return;
      finished = true;
      if (cb) cb(value);
      if (shouldReject) reject(value);
      else resolve(value);
    };

    Speech.speak(text, {
      language: speechLanguage,
      voice: voice?.identifier,
      rate: lang === 'hi' ? 0.92 : 0.95,
      pitch: lang === 'hi' ? 1.02 : 1.06,
      onStart: () => {
        if (onStart) onStart();
      },
      onDone: () => finish(onDone),
      onStopped: () => finish(onDone),
      onError: (e) => {
        console.error('[TTS] system speech error', e);
        finish(onError, markHandledError(e), true);
      },
    });
  });
};

export const textToSpeech = {
  setSpeechProvider(provider) {
    speechProvider = normalizeSpeechProvider(provider);
    console.log('[TTS] setSpeechProvider', { provider: speechProvider });
  },

  getSpeechProvider() {
    return speechProvider;
  },

  async speak(text, { language = 'english', voiceName, provider, cacheKey, prepareSpoken = false, segmented = false, onDone, onError, onProgress, onStart } = {}) {
    try {
      if (!text || !text.trim()) return;
      const effectiveProvider = provider ? normalizeSpeechProvider(provider) : speechProvider;
      console.log('[TTS] speak() called', {
        provider: effectiveProvider,
        language,
        voiceName: voiceName || null,
        textLength: String(text).trim().length,
        preview: String(text).trim().slice(0, 80),
      });

      if (effectiveProvider === SPEECH_PROVIDER_GOOGLE) {
        await textToSpeech.playServerTts(text, {
          language,
          voiceName,
          cacheKey,
          prepareSpoken,
          segmented,
          onDone,
          onError,
          onProgress,
          onStart,
        });
        return;
      }

      await Speech.stop();
      await stopLoadedAudio();
      console.log('[TTS] using local device speech');
      await speakLocally(text, { language, voiceName, onDone, onError, onStart });
    } catch (e) {
      console.error('[TTS] speak error', e);
      if (!e?.__ttsHandled && onError) onError(e);
    }
  },

  async playServerTts(
    text,
    { language = 'english', voiceName, cacheKey, prepareSpoken = false, segmented = false, onDone, onError, onProgress, onStart, suppressErrorCallback = false } = {}
  ) {
    try {
      if (!text || !text.trim()) return;

      await Speech.stop();
      await stopLoadedAudio();

      const streamedChunks = segmented ? splitForStreamingTts(text, 260) : [];
      if (streamedChunks.length > 1) {
        console.log('[TTS] segmented Google TTS playback', {
          chunks: streamedChunks.length,
          totalLength: String(text || '').trim().length,
        });
        let startedCallbackSent = false;
        let elapsedBeforeChunk = 0;
        const notifyStarted = () => {
          if (startedCallbackSent) return;
          startedCallbackSent = true;
          if (onStart) onStart();
        };
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
          allowsRecordingIOS: false,
          playThroughEarpieceAndroid: false,
          shouldDuckAndroid: false,
          interruptionModeIOS: InterruptionModeIOS.DoNotMix,
          interruptionModeAndroid: InterruptionModeAndroid.DoNotMix,
        });
        let nextAudioPromise = synthesizeServerTtsToCache(streamedChunks[0], {
          language,
          voiceName,
          cacheKey: cacheKey ? `${cacheKey}:seg0` : undefined,
          prepareSpoken,
        });
        for (let i = 0; i < streamedChunks.length; i += 1) {
          console.log('[TTS] segmented chunk awaiting audio', {
            index: i + 1,
            chunks: streamedChunks.length,
            length: streamedChunks[i]?.length || 0,
          });
          const cachedAudio = await nextAudioPromise;
          if (i + 1 < streamedChunks.length) {
            nextAudioPromise = synthesizeServerTtsToCache(streamedChunks[i + 1], {
              language,
              voiceName,
              cacheKey: cacheKey ? `${cacheKey}:seg${i + 1}` : undefined,
              prepareSpoken,
            });
          }
          if (!cachedAudio?.uri) throw new Error('Google TTS: missing cached segment audio');
          console.log('[TTS] segmented chunk playback start', {
            index: i + 1,
            chunks: streamedChunks.length,
            uri: cachedAudio.uri,
            cached: Boolean(cachedAudio.cached),
          });
          await new Promise(async (resolve, reject) => {
            let settled = false;
            let progressPollId = null;
            const finish = async (error) => {
              if (settled) return;
              settled = true;
              if (progressPollId) clearInterval(progressPollId);
              try {
                if (currentSound) {
                  await currentSound.unloadAsync();
                  currentSound = null;
                }
              } catch {
                // ignore
              }
              if (error) reject(error);
              else resolve();
            };
            const { sound } = await Audio.Sound.createAsync(
              { uri: cachedAudio.uri },
              { progressUpdateIntervalMillis: 500 }
            );
            currentSound = sound;
            speechCallbacks = { onDone, onError, onProgress };
            await sound.setVolumeAsync(1.0);
            sound.setOnPlaybackStatusUpdate((status) => {
              if (status?.isLoaded && status.positionMillis != null && onProgress) {
                onProgress(elapsedBeforeChunk + status.positionMillis, 0);
              }
              if (status?.isLoaded && Number(status.positionMillis || 0) > 100) {
                notifyStarted();
              }
              if (status?.didJustFinish) {
                const duration = Number(status.durationMillis || 0);
                elapsedBeforeChunk += duration;
                console.log('[TTS] segmented chunk playback finished', {
                  index: i + 1,
                  chunks: streamedChunks.length,
                  durationMillis: duration,
                });
                finish();
              }
            });
            progressPollId = setInterval(() => {
              sound.getStatusAsync()
                .then((status) => {
                  if (!status?.isLoaded) return;
                  if (status.positionMillis != null && onProgress) {
                    onProgress(elapsedBeforeChunk + status.positionMillis, status.durationMillis ?? 0);
                  }
                })
                .catch(() => {});
            }, 500);
            try {
              await sound.playAsync();
              notifyStarted();
            } catch (playError) {
              finish(playError);
            }
          });
        }
        console.log('[TTS] segmented playback finished all chunks', {
          chunks: streamedChunks.length,
        });
        speechCallbacks = null;
        cleanupSpeechPlayback();
        if (onDone) onDone();
        return;
      }

      const cachedAudio = await synthesizeServerTtsToCache(text, {
        language,
        voiceName,
        cacheKey,
        prepareSpoken,
      });
      if (!cachedAudio?.uri) {
        throw new Error('Google TTS: missing cached audio');
      }
      speechTempUri = null;

      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        allowsRecordingIOS: false,
        playThroughEarpieceAndroid: false,
        shouldDuckAndroid: false,
        interruptionModeIOS: InterruptionModeIOS.DoNotMix,
        interruptionModeAndroid: InterruptionModeAndroid.DoNotMix,
      });

      await new Promise(async (resolve, reject) => {
        let settled = false;
        let finishingPlayback = false;
        let startedLogged = false;
        let startedCallbackSent = false;
        let progressPollId = null;
        let playbackFinishTimerId = null;
        const notifyStarted = () => {
          if (startedCallbackSent) return;
          startedCallbackSent = true;
          if (onStart) onStart();
        };
        const finish = async (cb, value, shouldReject = false) => {
          if (settled) return;
          settled = true;
          if (progressPollId) {
            clearInterval(progressPollId);
            progressPollId = null;
          }
          if (playbackFinishTimerId) {
            clearTimeout(playbackFinishTimerId);
            playbackFinishTimerId = null;
          }
          try {
            if (cb) cb(value);
          } finally {
            if (shouldReject) reject(value);
            else resolve(value);
          }
        };

        const { sound } = await Audio.Sound.createAsync(
          { uri: cachedAudio.uri },
          { progressUpdateIntervalMillis: 500 }
        );
        currentSound = sound;
        speechCallbacks = { onDone, onError, onProgress };
        await sound.setVolumeAsync(1.0);
        console.log('[TTS] Google audio prepared', {
          uri: cachedAudio.uri,
          cached: Boolean(cachedAudio.cached),
          cacheKey: cachedAudio.key,
        });

        const completePlayback = () => {
          if (finishingPlayback) return;
          finishingPlayback = true;
          const done = speechCallbacks?.onDone;
          console.log('[TTS] Google playback finished');
          speechCallbacks = null;
          (async () => {
            try {
              await sound.unloadAsync();
            } catch {
              // ignore playback cleanup failures
            }
            if (currentSound === sound) {
              currentSound = null;
            }
            cleanupSpeechPlayback();
            finish(done);
          })();
        };

        const schedulePlaybackWatchdog = (status) => {
          if (playbackFinishTimerId || !status?.isLoaded) return;
          const duration = Number(status.durationMillis || 0);
          const position = Number(status.positionMillis || 0);
          if (!duration || duration <= 0) return;
          const remaining = Math.max(700, duration - position + 1200);
          playbackFinishTimerId = setTimeout(() => {
            console.warn('[TTS] playback finish watchdog fired', {
              durationMillis: duration,
              positionMillis: position,
            });
            completePlayback();
          }, remaining);
        };

        progressPollId = setInterval(() => {
          sound.getStatusAsync()
            .then((status) => {
              if (!status?.isLoaded) return;
              schedulePlaybackWatchdog(status);
              if (speechCallbacks?.onProgress && status.positionMillis != null) {
                speechCallbacks.onProgress(status.positionMillis, status.durationMillis ?? 0);
              }
              const duration = Number(status.durationMillis || 0);
              const position = Number(status.positionMillis || 0);
              if (duration > 0 && position >= duration - 120) {
                completePlayback();
                return;
              }
              if (
                startedCallbackSent
                && position > 250
                && status.isPlaying === false
                && status.isBuffering !== true
              ) {
                console.warn('[TTS] playback stopped without finish event', {
                  durationMillis: duration,
                  positionMillis: position,
                });
                completePlayback();
              }
            })
            .catch(() => {
              // Ignore transient polling failures; status updates may still arrive normally.
            });
        }, 500);

        sound.setOnPlaybackStatusUpdate((status) => {
          if (status?.isLoaded && speechCallbacks?.onProgress && status.positionMillis != null) {
            speechCallbacks.onProgress(status.positionMillis, status.durationMillis ?? 0);
          }
          if (status?.isLoaded) {
            schedulePlaybackWatchdog(status);
          }
          if (
            !startedLogged &&
            status?.isLoaded &&
            status.positionMillis != null &&
            status.positionMillis > 120
          ) {
            startedLogged = true;
            notifyStarted();
            console.log('[TTS] Google playback started', {
              positionMillis: status.positionMillis,
              durationMillis: status.durationMillis ?? 0,
            });
          }
          if (status?.didJustFinish) {
            completePlayback();
            return;
          }
          if (
            startedCallbackSent
            && status?.isLoaded
            && Number(status.positionMillis || 0) > 250
            && status.isPlaying === false
            && status.isBuffering !== true
          ) {
            console.warn('[TTS] playback status stopped without finish event', {
              durationMillis: status.durationMillis ?? 0,
              positionMillis: status.positionMillis ?? 0,
            });
            completePlayback();
          }
        });

        try {
          await sound.playAsync();
          notifyStarted();
        } catch (playError) {
          speechCallbacks = null;
          try {
            await sound.unloadAsync();
          } catch {
            // ignore
          }
          currentSound = null;
          cleanupSpeechPlayback();
          finish(onError, markHandledError(playError), true);
        }
      });
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
      if (!suppressErrorCallback && !e?.__ttsHandled && onError) onError(e);
      throw e;
    }
  },

  async prefetchServerTts(text, { language = 'english', voiceName, cacheKey, prepareSpoken = false } = {}) {
    try {
      return await synthesizeServerTtsToCache(text, {
        language,
        voiceName,
        cacheKey,
        prepareSpoken,
      });
    } catch (e) {
      console.warn('[TTS] prefetchServerTts failed', e?.message || e);
      return null;
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

  stopImmediate() {
    try {
      Speech.stop();
    } catch {
      // ignore
    }
    stopLoadedAudioImmediately();
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
