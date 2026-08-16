/**
 * Instant chat typing lines — aligned with mobile `en.json` chat.instantLoader.* (English defaults).
 */
export const INSTANT_LOADER_LINES = [
    'Tara is reading your question…',
    'Checking your chart context…',
    'Looking at the active timing…',
];

export const INSTANT_LOADER_TAKING_LONGER =
    'This is taking a little longer. I am still working on your answer...';

// These are thinking-state changes, not text being typed. Keep each cue still
// long enough to read before moving to the next one.
export const INSTANT_LOADER_WORD_MS = 1700;

export function getInstantLoaderMaxWords() {
    // Two extra beats keep the last cue visible before the longer-wait note.
    return INSTANT_LOADER_LINES.length + 2;
}

/**
 * Reveal one short thought at a time. Earlier versions accumulated paragraphs and
 * looked like a canned loading screen instead of a live conversation.
 */
export function buildInstantTypingLines(wordCount) {
    const maxWords = getInstantLoaderMaxWords();
    const step = Math.max(1, Math.min(wordCount, maxWords));
    const lineIndex = Math.min(step - 1, INSTANT_LOADER_LINES.length - 1);
    const current = {
        key: `instant-line-${lineIndex}`,
        text: INSTANT_LOADER_LINES[lineIndex],
        isComplete: true,
    };
    return {
        lines: [current],
        isTakingLonger: wordCount >= maxWords,
    };
}

/** Split a completed instant answer into readable conversational beats. */
export function splitInstantReply(content, maxPieceLength = 95) {
    const normalized = String(content || '').replace(/\r\n/g, '\n').trim();
    if (!normalized) return [];

    const sentences = normalized
        .split(/\n{2,}/u)
        .flatMap((paragraph) => paragraph.match(/[^.!?।！？]+(?:[.!?।！？]+|$)/gu) || [paragraph])
        .map((part) => part.trim())
        .filter(Boolean);
    const pieces = [];

    sentences.forEach((sentence) => {
        if (sentence.length <= maxPieceLength) {
            pieces.push(sentence);
            return;
        }
        const clauses = (sentence.match(/[^,;:]+(?:[,;:]|$)/gu) || [sentence])
            .map((part) => part.trim())
            .filter(Boolean);
        let buffer = '';
        clauses.forEach((clause) => {
            const candidate = buffer ? `${buffer} ${clause}` : clause;
            if (buffer && candidate.length > maxPieceLength) {
                pieces.push(buffer);
                buffer = clause;
            } else {
                buffer = candidate;
            }
        });
        if (buffer) pieces.push(buffer);
    });

    return pieces.length ? pieces : [normalized];
}

export function getInstantReplyPieceDelay(piece) {
    const length = String(piece || '').length;
    return Math.max(1400, Math.min(2600, 900 + length * 17));
}
