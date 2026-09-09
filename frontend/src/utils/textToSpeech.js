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
        this.playbackEpoch = 0;
        
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

    _releaseServerAudio() {
        if (this.currentAudio) {
            this.currentAudio.onended = null;
            this.currentAudio.onerror = null;
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

    _base64AudioUrl(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let index = 0; index < binary.length; index += 1) {
            bytes[index] = binary.charCodeAt(index);
        }
        const url = URL.createObjectURL(new Blob([bytes], { type: 'audio/mpeg' }));
        this.currentAudioUrl = url;
        return url;
    }

    async _speakWithGoogle(text, options, epoch) {
        const controller = new AbortController();
        this.currentRequest = controller;
        const language = String(options.lang || options.language || 'en-IN').toLowerCase().startsWith('hi')
            ? 'hi'
            : 'en';
        const params = new URLSearchParams({
            text: this.cleanText(text),
            lang: language,
            include_timepoints: 'false',
            prepare_spoken: 'false',
        });
        if (options.voiceName) params.set('voice_name', options.voiceName);
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/tts/synthesize?${params.toString()}`, {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            signal: controller.signal,
        });
        if (!response.ok) throw new Error(`Google TTS failed (${response.status})`);
        const payload = await response.json();
        if (!payload?.audio) throw new Error('Google TTS returned no audio');
        if (epoch !== this.playbackEpoch) return;
        console.log('Google TTS audio ready', {
            provider: payload.provider || 'google',
            voiceName: payload.voice_name || options.voiceName || 'admin-selected',
            language,
        });

        this.currentRequest = null;
        const audio = new Audio(this._base64AudioUrl(payload.audio));
        this.currentAudio = audio;
        // The backend already applies the configured Chirp speaking rate.
        // Applying the browser rate again would compound it and distort Tara.
        audio.playbackRate = 1;
        audio.onplay = () => {
            if (epoch !== this.playbackEpoch) return;
            this.isSpeaking = true;
            options.onStart?.();
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
        this._speakWithGoogle(text, options, epoch).catch((error) => {
            if (error?.name === 'AbortError' || epoch !== this.playbackEpoch) return;
            console.warn('Google TTS unavailable; using browser speech fallback', error);
            this.currentRequest = null;
            this._releaseServerAudio();
            this._speakWithBrowser(text, options);
        });
        return true;
    }

    // Stop current speech
    stop() {
        this.playbackEpoch += 1;
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
        if (this.synth.speaking && !this.synth.paused) {
            this.synth.pause();
        }
    }

    // Resume speech
    resume() {
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
