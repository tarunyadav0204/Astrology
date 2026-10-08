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
);
