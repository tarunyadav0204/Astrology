import textToSpeech from './textToSpeech';

/** Match mobile `SpeechChatScreen` THINKING_HANDOFF_DEFAULTS (short line after listen → API). */
const PHRASES = [
    'Got it. Give me a moment.',
    'Okay, I’m looking at that now.',
    'I have what I need. Let me read that for you.',
];

let leadInIndex = 0;

export async function speakThinkingHandoff() {
    if (!textToSpeech?.isSupported) return;
    const i = leadInIndex % PHRASES.length;
    leadInIndex += 1;
    const phrase = PHRASES[i];
    await new Promise((resolve) => {
        textToSpeech.speak(phrase, {
            rate: 0.95,
            pitch: 1,
            onEnd: resolve,
            onError: resolve,
        });
    });
}
