// Enhanced markdown renderer for blog posts
export const renderMarkdown = (content) => {
    if (!content) return '';
    
    return content
        // Headers
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        
        // Bold and italic
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
        
        // Images
        .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="content-image" />')
        
        // Lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        
        // Line breaks and paragraphs
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
};

export const stripMarkdown = (content) => {
    if (!content) return '';
    
    return content
        .replace(/[#*\[\]()]/g, '')
        .replace(/!\[.*?\]\(.*?\)/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/\n/g, ' ')
        .trim();
};

/**
 * Chat / admin history: decode entities, strip orphan markdown heading lines, then light markdown → HTML.
 * Models often emit a bare "###" or "#" between sections; those must not survive as visible characters.
 */
export function formatChatMessageHtml(content) {
    if (content == null || content === '') return '';

    let decoded = String(content)
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");

    // Entire line is only # … ###### (optional spaces) — nothing to show
    decoded = decoded.replace(/^\s*#{1,6}\s*$/gm, '');
    decoded = decoded.replace(/\n{3,}/g, '\n\n');

    const toH3 = (title) => {
        const s = String(title).trim();
        return s ? `<h3>${s}</h3>` : '';
    };

    decoded = decoded
        .replace(/^####\s+(.+)$/gm, (_, t) => toH3(t))
        .replace(/^###\s+(.+)$/gm, (_, t) => toH3(t))
        .replace(/^##\s+(.+)$/gm, (_, t) => toH3(t))
        .replace(/^#\s+(.+)$/gm, (_, t) => toH3(t));

    return decoded
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\* /g, '<br/>• ')
        .replace(/\n/g, '<br/>')
        .replace(/• \*\*(.*?)\*\*/g, '• <strong>$1</strong>');
}