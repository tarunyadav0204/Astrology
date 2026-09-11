const SENTENCE_END_RE = /[.!?\u0964\u0965]+(?:["'\u2019\u201d)\]]+)?(?=\s|$)/g;

export function takeSpeakableChunks(value, { flush = false } = {}) {
    const text = String(value || '');
    const chunks = [];
    let consumed = 0;
    let match;
    SENTENCE_END_RE.lastIndex = 0;
    while ((match = SENTENCE_END_RE.exec(text)) !== null) {
        const end = match.index + match[0].length;
        const chunk = text.slice(consumed, end).trim();
        if (chunk) chunks.push(chunk);
        consumed = end;
    }
    const remainder = text.slice(consumed).trimStart();
    if (flush && remainder.trim()) {
        chunks.push(remainder.trim());
        return { chunks, remainder: '' };
    }
    return { chunks, remainder };
}

export function speechLocaleForLanguage(language) {
    const normalized = String(language || '').trim().toLowerCase();
    if (normalized === 'hindi' || normalized === 'hi' || normalized.startsWith('hi-')) return 'hi-IN';
    if (normalized === 'english' || normalized === 'en' || normalized.startsWith('en-')) return 'en-IN';
    return normalized || 'en-IN';
}

export function inferSpeechLanguage(text, fallback = 'english') {
    const value = String(text || '');
    if (/[\u0900-\u097f]/.test(value)) return 'hindi';
    return fallback;
}

function comparableSpeechText(value) {
    return String(value || '')
        .toLowerCase()
        .replace(/[^\p{L}\p{N}]+/gu, ' ')
        .trim();
}

export function buildConversationalClosing(answer, followUps = [], language = 'english') {
    const firstFollowUp = Array.isArray(followUps)
        ? String(followUps.find((item) => String(item || '').trim()) || '').trim()
        : '';
    if (firstFollowUp) {
        const normalizedAnswer = comparableSpeechText(answer);
        const normalizedFollowUp = comparableSpeechText(firstFollowUp);
        if (normalizedFollowUp && normalizedAnswer.endsWith(normalizedFollowUp)) return '';
        // Suggestions are commonly phrased in the user's first person. Reading
        // them verbatim would make Tara sound as though she is asking about
        // herself. The normal path uses the guide generator; this is its safe
        // offline fallback.
        return String(language || '').toLowerCase().startsWith('hi')
            ? 'अगर आप चाहें, तो मैं इसी से जुड़े अगले विषय पर और बता सकती हूँ।'
            : 'If you would like, I can continue with the next related part of this reading.';
    }
    return String(language || '').toLowerCase().startsWith('hi')
        ? 'अब आप किस बात को थोड़ा और समझना चाहेंगे?'
        : 'What would you like to understand a little better next?';
}
