/**
 * Instant chat typing lines — aligned with mobile `en.json` chat.instantLoader.* (English defaults).
 */
export const INSTANT_LOADER_LINES = [
    'I am reading the main chart focus first, so the answer stays connected to the right part of life instead of becoming generic.',
    'Now I am checking the running dasha pattern and seeing which planet is currently carrying more weight in the question.',
    'I am comparing the present transits with the natal promise to separate a short-term signal from a deeper pattern.',
    'The relevant houses are being matched with the question, so the answer can stay specific and practical.',
    'I am checking whether the timing looks active right now, building slowly, or already passing out of focus.',
    'The main signals are being combined now, especially where two or more factors point in the same direction.',
    'I am narrowing the dasha timing so past, current, and upcoming influences are not mixed together.',
    'The transit picture is being checked against the question, especially where it activates the same houses again.',
    'I am looking for repeated house patterns because repeated signals are more useful than one isolated placement.',
    'Your exact question and recent chat context are being kept in view so the reply does not drift into a general reading.',
    'I am separating stronger chart evidence from weaker hints, so the answer can say what is clear and what is uncertain.',
    'Now I am turning the astrology into practical language, without losing the main chart reasoning.',
    'I am keeping the response short enough for instant mode while still answering the real question.',
    'I am turning the chart signals into a short answer you can use, without making it unnecessarily long.',
    'I am reviewing the final wording so the takeaway is clear before the answer appears.',
    'Almost ready. I am tightening the response so it gives you the clearest takeaway first.',
];

export const INSTANT_LOADER_TAKING_LONGER =
    'This is taking a little longer. I am still working on your answer...';

export const INSTANT_LOADER_WORD_MS = 180;

export function getInstantLoaderMaxWords() {
    return INSTANT_LOADER_LINES.reduce((acc, line) => acc + line.split(/\s+/).filter(Boolean).length, 0);
}

/**
 * Progressive word reveal per line (same algorithm as mobile ChatScreen renderInstantTypingIndicator).
 */
export function buildInstantTypingLines(wordCount) {
    const maxWords = getInstantLoaderMaxWords();
    let remaining = Math.max(0, Math.min(wordCount, maxWords));
    const typedLines = [];
    INSTANT_LOADER_LINES.forEach((line, index) => {
        const words = line.split(/\s+/).filter(Boolean);
        if (remaining <= 0) return;
        const visibleWordCount = Math.min(remaining, words.length);
        remaining -= words.length;
        typedLines.push({
            key: `instant-line-${index}`,
            text: words.slice(0, visibleWordCount).join(' '),
            isComplete: visibleWordCount >= words.length,
        });
    });
    return {
        lines: typedLines,
        isTakingLonger: wordCount >= maxWords,
    };
}
