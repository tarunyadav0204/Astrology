import textToSpeech from './textToSpeech';

/** Match mobile `SpeechChatScreen` THINKING_HANDOFF_DEFAULTS (short line after listen → API). */
const PHRASES = {
    english: [
        'Got it. Give me a moment.',
        'Okay, I’m looking at that now.',
        'I have what I need. Let me read that for you.',
    ],
    hindi: [
        'ठीक है, मुझे एक क्षण दीजिए।',
        'ठीक है, मैं अभी इसे देख रही हूँ।',
        'मुझे आपका सवाल समझ आ गया। मैं अभी बताती हूँ।',
    ],
};

let leadInIndex = 0;

export async function speakThinkingHandoff(language = 'english') {
    if (!textToSpeech?.isSupported) return;
    const isHindi = String(language || '').toLowerCase().startsWith('hi');
    const phrases = isHindi ? PHRASES.hindi : PHRASES.english;
    const i = leadInIndex % phrases.length;
    leadInIndex += 1;
    const phrase = phrases[i];
    await new Promise((resolve) => {
        textToSpeech.speak(phrase, {
            rate: 0.95,
            pitch: 1,
            lang: isHindi ? 'hi-IN' : 'en-IN',
            onEnd: resolve,
            onError: resolve,
        });
    });
}
