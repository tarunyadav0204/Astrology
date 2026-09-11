// Text-to-Speech utility for chat responses
export const normalizeAstrologyPronunciation = (text) => String(text || '')
    // Standalone Hindi planet names can be expanded by some voices into their
    // weekday names. Supplying the spoken context word disambiguates them;
    // visible chat text is never changed.
    .replace(/(^|[^\u0900-\u097F])मंगल(?![\u0900-\u097F]|\s*(?:ग्रह|दोष))/g, '$1मंगल ग्रह')
    .replace(/(^|[^\u0900-\u097F])बुध(?![\u0900-\u097F]|\s*ग्रह)/g, '$1बुध ग्रह')
    .replace(/\bMangal\b(?!\s+(?:graha|dosh|vaar|war)\b)/gi, (name) => `${name} graha`)
    .replace(/\bBudh\b(?!\s+(?:graha|vaar|war)\b)/gi, (name) => `${name} graha`);

class TextToSpeech {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isSupported = 'speechSynthesis' in window;
        this.isSpeaking = false;
        this.currentUtterance = null;
        this.provider = 'local';
        this.currentAudio = null;
        this.currentAudioUrl = null;
        this.currentRequest = null;
        this.currentStartWatchdog = null;
        this.playbackEpoch = 0;
        this.prefetchedAudio = new Map();
        this.prefetchInflight = new Map();
        
        // Preload voices
        if (this.isSupported) {
            this.synth.getVoices();
        }
    }

    setProvider(provider) {
        this.provider = provider === 'google' ? 'google' : 'local';
    }

    getProvider() {
        return this.provider;
    }

    _googleAudioKey(text, options = {}) {
        const language = String(options.lang || options.language || 'en-IN').toLowerCase().startsWith('hi') ? 'hi' : 'en';
        return `${language}:${options.voiceName || ''}:${this.cleanText(text)}`;
    }

    async _fetchGoogleAudio(text, options = {}, signal) {
        const language = String(options.lang || options.language || 'en-IN').toLowerCase().startsWith('hi') ? 'hi' : 'en';
        const payload = {
            text: this.cleanText(text),
            lang: language,
            include_timepoints: false,
            prepare_spoken: false,
            audio_format: 'binary',
        };
        if (options.voiceName) payload.voice_name = options.voiceName;
        const token = localStorage.getItem('token');
        const response = await fetch('/api/tts/synthesize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify(payload),
            signal,
        });
        if (!response.ok) throw new Error(`Google TTS failed (${response.status})`);
        const audioBlob = await response.blob();
        if (!audioBlob?.size) throw new Error('Google TTS returned no audio');
        return { audioBlob, response, language };
    }

    prefetch(text, options = {}) {
        if (this.provider !== 'google' || !String(text || '').trim()) return Promise.resolve(null);
        const key = this._googleAudioKey(text, options);
        if (this.prefetchedAudio.has(key)) return Promise.resolve(this.prefetchedAudio.get(key));
        if (this.prefetchInflight.has(key)) return this.prefetchInflight.get(key);
        const request = this._fetchGoogleAudio(text, options)
            .then((result) => {
                this.prefetchedAudio.set(key, result);
                while (this.prefetchedAudio.size > 6) this.prefetchedAudio.delete(this.prefetchedAudio.keys().next().value);
                return result;
            })
            .finally(() => this.prefetchInflight.delete(key));
        this.prefetchInflight.set(key, request);
        return request;
    }

    _releaseServerAudio() {
        if (this.currentAudio) {
            this.currentAudio.onended = null;
            this.currentAudio.onerror = null;
            this.currentAudio.ontimeupdate = null;
            try {
                this.currentAudio.pause();
                this.currentAudio.src = '';
            } catch (_) {
                // Best-effort browser media cleanup.
            }
            this.currentAudio = null;
        }
        if (this.currentAudioUrl) {
            URL.revokeObjectURL(this.currentAudioUrl);
            this.currentAudioUrl = null;
        }
    }

    async _speakWithGoogle(text, options, epoch) {
        const key = this._googleAudioKey(text, options);
        let prepared = this.prefetchedAudio.get(key);
        if (prepared) this.prefetchedAudio.delete(key);
        if (!prepared && this.prefetchInflight.has(key)) {
            prepared = await this.prefetchInflight.get(key);
            this.prefetchedAudio.delete(key);
        }
        if (!prepared) {
            const controller = new AbortController();
            this.currentRequest = controller;
            prepared = await this._fetchGoogleAudio(text, options, controller.signal);
        }
        const { audioBlob, response, language } = prepared;
        if (epoch !== this.playbackEpoch) return;
        console.log('Google TTS audio ready', {
            provider: response.headers.get('X-TTS-Provider') || 'google',
            voiceName: response.headers.get('X-TTS-Voice') || options.voiceName || 'admin-selected',
            language,
        });

        this.currentRequest = null;
        const audioUrl = URL.createObjectURL(audioBlob);
        this.currentAudioUrl = audioUrl;
        const audio = new Audio(audioUrl);
        this.currentAudio = audio;
        // The backend already applies the configured Chirp speaking rate.
        // Applying the browser rate again would compound it and distort Tara.
        audio.playbackRate = 1;
        audio.onplay = () => {
            if (epoch !== this.playbackEpoch) return;
            this.isSpeaking = true;
            options.onStart?.();
        };
        audio.ontimeupdate = () => {
            if (epoch !== this.playbackEpoch) return;
            options.onProgress?.(
                Math.max(0, Number(audio.currentTime || 0) * 1000),
                Math.max(0, Number(audio.duration || 0) * 1000)
            );
        };
        audio.onended = () => {
            if (epoch !== this.playbackEpoch) return;
            this.isSpeaking = false;
            this._releaseServerAudio();
            options.onEnd?.();
        };
        audio.onerror = () => {
            if (epoch !== this.playbackEpoch) return;
            this.isSpeaking = false;
            this._releaseServerAudio();
            options.onError?.(new Error('Google TTS audio playback failed'));
        };
        await audio.play();
        // Some installed/PWA browser builds resolve play() without reliably
        // dispatching the media `play` event. Treat confirmed, unpaused playback
        // as the start signal so the UI does not remain in "thinking" state.
        if (epoch === this.playbackEpoch && !audio.paused && !this.isSpeaking) {
            this.isSpeaking = true;
            options.onStart?.();
        }
    }

    getPreferredVoice(voices = [], requestedLanguage = 'en-US') {
        if (!Array.isArray(voices) || voices.length === 0) return null;

        const requested = String(requestedLanguage || 'en-US').toLowerCase();
        const requestedBase = requested.split('-')[0];
        const matchingVoices = voices.filter((voice) => {
            const voiceLanguage = String(voice?.lang || '').toLowerCase();
            return voiceLanguage === requested || voiceLanguage.startsWith(`${requestedBase}-`);
        });

        return (
            matchingVoices.find((voice) => (
                String(voice?.name || '').toLowerCase().includes('female')
            ))
            || matchingVoices[0]
            || voices.find((voice) => String(voice?.lang || '').toLowerCase().startsWith('en'))
            || voices[0]
            || null
        );
    }

    // Clean markdown and formatting from text
    cleanText(text) {
        return normalizeAstrologyPronunciation(text)
            .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
            .replace(/\*(.*?)\*/g, '$1')     // Remove italics
            .replace(/###\s*(.*?)$/gm, '$1') // Remove headers
            .replace(/•\s*/g, '')            // Remove bullet points
            .replace(/\n+/g, '. ')           // Replace line breaks with periods
            .replace(/\s+/g, ' ')            // Normalize spaces
            .trim();
    }

    _speakWithBrowser(text, options = {}) {
        if (!this.isSupported) {
            console.warn('Text-to-speech not supported');
            return false;
        }

        // Only stop if currently speaking
        if (this.isSpeaking) {
            this.stop();
        }
        
        // Ensure voices are loaded
        const startSpeech = () => {
            const cleanedText = this.cleanText(text);
            this.currentUtterance = new SpeechSynthesisUtterance(cleanedText);
        
            // Configure voice settings
            this.currentUtterance.rate = options.rate || 0.9;
            this.currentUtterance.pitch = options.pitch || 1;
            this.currentUtterance.volume = options.volume || 1;
            
            // Set voice (prefer English female voice first)
            const voices = this.synth.getVoices();
            const requestedLanguage = options.lang || options.language || 'en-US';
            const preferredVoice = this.getPreferredVoice(voices, requestedLanguage);
            
            if (preferredVoice) {
                this.currentUtterance.voice = preferredVoice;
            }
            this.currentUtterance.lang = preferredVoice?.lang || requestedLanguage;

            // Event handlers
            this.currentUtterance.onstart = () => {
                this.isSpeaking = true;
                console.log('Speech started successfully');
                if (options.onStart) options.onStart();
            };

            this.currentUtterance.onend = () => {
                this.isSpeaking = false;
                console.log('Speech ended successfully');
                if (options.onEnd) options.onEnd();
            };

            this.currentUtterance.onerror = (event) => {
                this.isSpeaking = false;
                console.error('Speech synthesis error:', event);
                if (options.onError) options.onError(event);
            };
            this.currentUtterance.onboundary = (event) => {
                if (event?.charIndex == null) return;
                options.onBoundary?.(Number(event.charIndex), cleanedText.length);
            };

            // Start speaking
            console.log('Starting speech with voice:', this.currentUtterance.voice?.name || 'default');
            this.synth.speak(this.currentUtterance);
        };

        // Check if voices are loaded
        const voices = this.synth.getVoices();
        if (voices.length > 0) {
            if (this.isSpeaking) {
                setTimeout(startSpeech, 200);
            } else {
                startSpeech();
            }
        } else {
            // Wait for voices to load
            this.synth.onvoiceschanged = () => {
                if (this.isSpeaking) {
                    setTimeout(startSpeech, 200);
                } else {
                    startSpeech();
                }
            };
        }
        
        return true;
    }

    // Speak with the configured admin provider. Google failures fall back to
    // browser speech, but cancellation never starts a fallback utterance.
    speak(text, options = {}) {
        if (this.provider !== 'google') return this._speakWithBrowser(text, options);
        this.stop();
        const epoch = this.playbackEpoch;
        let playbackStarted = false;
        let fallbackAttempted = false;
        let terminalCallbackSent = false;

        const clearStartWatchdog = () => {
            if (!this.currentStartWatchdog) return;
            clearTimeout(this.currentStartWatchdog);
            this.currentStartWatchdog = null;
        };
        const notifyStart = () => {
            if (terminalCallbackSent || playbackStarted) return;
            playbackStarted = true;
            clearStartWatchdog();
            options.onStart?.();
        };
        const notifyEnd = () => {
            if (terminalCallbackSent) return;
            terminalCallbackSent = true;
            clearStartWatchdog();
            options.onEnd?.();
        };
        const notifyError = (error) => {
            if (terminalCallbackSent) return;
            terminalCallbackSent = true;
            clearStartWatchdog();
            options.onError?.(error);
        };
        const startBrowserFallback = (error) => {
            if (fallbackAttempted || terminalCallbackSent || epoch !== this.playbackEpoch) return;
            fallbackAttempted = true;
            console.warn('Google TTS did not start; using browser speech fallback', error);
            this.currentRequest?.abort();
            this.currentRequest = null;
            this._releaseServerAudio();
            // Invalidate any late Google fetch/play callbacks before starting the
            // local engine. Without this, a delayed network response can cancel
            // or overlap the fallback voice.
            this.playbackEpoch += 1;
            const browserStarted = this._speakWithBrowser(text, {
                ...options,
                onStart: notifyStart,
                onEnd: notifyEnd,
                onError: notifyError,
            });
            if (!browserStarted) {
                notifyError(error || new Error('Speech playback is unavailable'));
                return;
            }
            this.currentStartWatchdog = setTimeout(() => {
                if (!playbackStarted && !terminalCallbackSent) {
                    if (this.synth.speaking || this.synth.pending) this.synth.cancel();
                    notifyError(new Error('Browser speech did not start'));
                }
            }, 5000);
        };

        const googleOptions = {
            ...options,
            onStart: notifyStart,
            onEnd: notifyEnd,
            onError: (error) => {
                if (playbackStarted) notifyError(error);
                else startBrowserFallback(error);
            },
        };
        this.currentStartWatchdog = setTimeout(() => {
            if (!playbackStarted && !terminalCallbackSent) {
                startBrowserFallback(new Error('Google TTS playback start timed out'));
            }
        }, 12000);
        this._speakWithGoogle(text, googleOptions, epoch).catch((error) => {
            if (error?.name === 'AbortError' || epoch !== this.playbackEpoch) return;
            startBrowserFallback(error);
        });
        return true;
    }

    // Stop current speech
    stop() {
        this.playbackEpoch += 1;
        if (this.currentStartWatchdog) {
            clearTimeout(this.currentStartWatchdog);
            this.currentStartWatchdog = null;
        }
        this.currentRequest?.abort();
        this.currentRequest = null;
        this._releaseServerAudio();
        if (this.synth.speaking || this.synth.pending) {
            this.synth.cancel();
        }
        this.isSpeaking = false;
        this.currentUtterance = null;
    }

    // Pause speech
    pause() {
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            return;
        }
        if (this.synth.speaking && !this.synth.paused) {
            this.synth.pause();
        }
    }

    // Resume speech
    resume() {
        if (this.currentAudio?.paused) {
            this.currentAudio.play().catch(() => {});
            return;
        }
        if (this.synth.paused) {
            this.synth.resume();
        }
    }

    // Get available voices
    getVoices() {
        return this.synth.getVoices();
    }
}

export default new TextToSpeech();
