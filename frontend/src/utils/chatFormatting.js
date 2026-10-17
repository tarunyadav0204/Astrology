// Simple writers use ##; technical writers also use ### and ####.
// Give both Simple modes the existing section-title styling, including a
// final heading without a trailing newline and headings arriving mid-stream.
export const formatChatHeadings = (content) => String(content || '').replace(
    /^(#{2,4})[ \t]+([^\n]+)$/gm,
    (_, hashes, title) => {
        const tag = hashes.length === 4 ? 'h4' : 'h3';
        const className = hashes.length === 4 ? 'chat-subheader' : 'chat-section-title';
        return `<${tag} class="${className}">${title.trim()}</${tag}>\n`;
    },
).replace(
    /^<strong(?: class="chat-bold")?>([^\n]{1,100}?)<\/strong>\s*:?\s*$/gm,
    (_, title) => `<h4 class="chat-subheader">${title.replace(/:$/, '')}</h4>\n`,
);

export const formatChatLists = (content) => String(content || '')
    .replace(/^(\d+\.\s+[^\n]+)$/gm, '<p class="numbered-item">$1</p>')
    .replace(/(^|\n)[-*]\s+(.+)/g, '$1<li class="chat-bullet">• $2</li>')
    .replace(/((?:<li class="chat-bullet">[^\n]*?<\/li>\s*)+)/g, '<ul class="chat-list">$1</ul>');
