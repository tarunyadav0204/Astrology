const escapeRegExp = (value) => String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

export const escapeChatHtmlAttribute = (value) => String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

const escapeChatHtmlText = (value) => String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

export const buildGlossaryTooltipHtml = (termText, termKey, definition) => (
    `<span class="tooltip-wrapper" data-term="${escapeChatHtmlAttribute(termKey)}" `
    + `data-definition="${escapeChatHtmlAttribute(definition)}" `
    + 'style="color: #e91e63; font-weight: bold; cursor: pointer; border-bottom: 1px dotted #e91e63;">'
    + `<span class="term-tooltip">${escapeChatHtmlText(termText)}</span></span>`
);

/** Add all tooltips in one pass over visible text, never inside tags/attributes. */
export const autoWrapGlossaryTermsInHtml = (html, glossary) => {
    const keys = Object.keys(glossary || {})
        .filter((key) => key && glossary[key] != null && String(glossary[key]).trim())
        .sort((a, b) => b.length - a.length);
    if (!keys.length) return { html, count: 0 };

    const keyByLowerCase = new Map(keys.map((key) => [key.toLowerCase(), key]));
    const termPattern = new RegExp(`\\b(${keys.map(escapeRegExp).join('|')})\\b`, 'gi');
    let count = 0;
    const wrapped = String(html || '').split(/(<[^>]*>)/g).map((part) => {
        if (!part || part.startsWith('<')) return part;
        return part.replace(termPattern, (match) => {
            const key = keyByLowerCase.get(match.toLowerCase());
            if (!key) return match;
            count += 1;
            return buildGlossaryTooltipHtml(match, key, glossary[key]);
        });
    }).join('');
    return { html: wrapped, count };
};
