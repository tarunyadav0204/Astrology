// Text-to-Speech utility for chat responses
class TextToSpeech {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isSupported = 'speechSynthesis' in window;
        this.isSpeaking = false;
        this.currentUtterance = null;
        
        // Preload voices
        if (this.isSupported) {
            this.synth.getVoices();
        }
    }

    // Clean markdown and formatting from text
    cleanText(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
            .replace(/\*(.*?)\*/g, '$1')     // Remove italics
            .replace(/###\s*(.*?)$/gm, '$1') // Remove headers
            .replace(/•\s*/g, '')            // Remove bullet points
            .replace(/\n+/g, '. ')           // Replace line breaks with periods
            .replace(/\s+/g, ' ')            // Normalize spaces
            .trim();
    }

    // Speak the text
    speak(text, options = {}) {
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
            
            // Set voice (prefer English voices)
            const voices = this.synth.getVoices();
            const englishVoice = voices.find(voice => 
                voice.lang.startsWith('en') && voice.name.includes('Female')
            ) || voices.find(voice => voice.lang.startsWith('en')) || voices[0];
            
            if (englishVoice) {
                this.currentUtterance.voice = englishVoice;
            }

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

    // Stop current speech
    stop() {
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