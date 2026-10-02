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

/** Pause after the server answer arrives, so the first sentence does not pop in instantly. */
export const INSTANT_REPLY_FIRST_PIECE_MS = 0;

export function shouldPaceInstantAnswer({ chatTier, messageType } = {}) {
    if (String(chatTier || '').toLowerCase() !== 'instant') return false;
    const type = String(messageType || 'answer').toLowerCase();
    return type !== 'clarification' && type !== 'native_gate';
}

/** Reveal a completed instant answer a paragraph, or a few lines, at a time. */
export function splitInstantReply(content) {
    const normalized = String(content || '').replace(/\r\n/g, '\n').trim();
    if (!normalized) return [];

    const paragraphs = normalized.split(/\n{2,}/u).map((part) => part.trim()).filter(Boolean);
    if (paragraphs.length > 1) return paragraphs;

    const lines = normalized.split('\n').map((line) => line.trim()).filter(Boolean);
    if (lines.length > 2) {
        const pieces = [];
        for (let index = 0; index < lines.length; index += 3) {
            pieces.push(lines.slice(index, index + 3).join('\n'));
        }
        return pieces;
    }

    const sentences = normalized.match(/[^.!?।！？]+(?:[.!?।！？]+|$)/gu) || [normalized];
    const pieces = [];
    let buffer = '';
    let count = 0;
    sentences.forEach((sentence) => {
        const next = sentence.trim();
        if (!next) return;
        const candidate = buffer ? `${buffer} ${next}` : next;
        if (buffer && (count >= 2 || candidate.length > 420)) {
            pieces.push(buffer);
            buffer = next;
            count = 1;
            return;
        }
        buffer = candidate;
        count += 1;
    });
    if (buffer) pieces.push(buffer);
    return pieces.length ? pieces : [normalized];
}

export function getInstantReplyPieceDelay(piece) {
    const length = String(piece || '').length;
    return Math.max(1700, Math.min(3400, 1100 + length * 8));
}
