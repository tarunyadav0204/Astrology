// Calculations remain a separate panel. message.content always belongs to the LLM.
const SIGNS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

export function buildImmediateChartPreview(chart, title = 'Selected chart · Calculated') {
    if (!chart || typeof chart !== 'object') return null;
    const rows = [];
    const position = (key, symbol, longitude) => {
        if (typeof longitude !== 'number' || !Number.isFinite(longitude)) return;
        const normalized = ((longitude % 360) + 360) % 360;
        rows.push({ key, source: 'calculation', text: `${symbol} ${SIGNS[Math.floor(normalized / 30)]} ${(normalized % 30).toFixed(2)}°` });
    };
    // Language-neutral, already calculated birth-chart facts. No question
    // classification, personal prediction, or guessed language is involved.
    position('natal-ascendant', '↑', chart.ascendant);
    position('natal-moon', '☽', chart.planets?.Moon?.longitude);
    position('natal-sun', '☉', chart.planets?.Sun?.longitude);
    return rows.length ? { type: 'instant_preview', version: 2, source: 'calculation', title, rows } : null;
}

export function mergeChartContext(previous, incoming) {
    if (!incoming?.rows?.length) return previous;
    const rows = new Map((previous?.rows || []).map(row => [row.key, row]));
    incoming.rows.forEach(row => { if (row?.key && row?.text) rows.set(row.key, row); });
    return { ...previous, ...incoming, rows: [...rows.values()] };
}

export function applyInstantProgress(message, payload = {}) {
    if (!message.isTyping && !message.isProcessing && !message.instantStreaming) return message;
    const incoming = payload.instant_preview || payload.preview;
    const preview = mergeChartContext(message.instantPreview, incoming);
    const partial = String(payload.partial_content ?? payload.content ?? '').trim();
    const hasAnswer = Boolean(partial);
    if (!hasAnswer && !incoming?.rows?.length) return message;
    // A calculated preview is metadata, not model output. Keep the waiting
    // state intact until actual LLM text arrives; otherwise a fast local chart
    // calculation makes the typing indicator disappear while routing is still
    // in progress.
    if (!hasAnswer) {
        if (preview === message.instantPreview) return message;
        return {
            ...message,
            instantPreview: preview,
            responseDirection: incoming?.direction || message.responseDirection,
        };
    }
    if (hasAnswer && message.instantPhase === 'answer' && payload.replace !== true
        && partial.length < String(message.content || '').length) return message;
    if (partial === message.content && preview === message.instantPreview && message.instantStreaming) return message;
    return {
        ...message,
        content: hasAnswer ? partial : (message.content || ''),
        instantPreview: preview, loadingMessage: null,
        isTyping: false, isProcessing: false, instantStreaming: true,
        instantPhase: 'answer',
        responseDirection: incoming?.direction || message.responseDirection,
    };
}
