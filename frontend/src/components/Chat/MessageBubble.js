import React from 'react';

const MessageBubble = ({ message }) => {
    const formatContent = (content) => {
        // First, normalize line breaks
        let formatted = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Process headers first with symbols
        formatted = formatted.replace(/### (.*?)\n/g, '<h3 class="chat-header">◆ $1 ◆</h3>\n\n');
        
        // Process bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/gs, '<strong class="chat-bold">$1</strong>');
        
        // Process italics (single asterisks not part of bold)
        formatted = formatted.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="chat-italic">$1</em>');
        
        // Split into paragraphs and process each
        const paragraphs = formatted.split(/\n\s*\n/);
        
        return paragraphs.map(paragraph => {
            paragraph = paragraph.trim();
            if (!paragraph) return '';
            
            // Check if it's a numbered list paragraph
            if (/^\d+\./m.test(paragraph)) {
                const items = paragraph.split(/\n(?=\d+\.)/)
                    .map(item => {
                        const match = item.match(/^(\d+\.)\s*(.*)$/s);
                        if (match) {
                            return `<li class="chat-numbered">▸ ${match[2].replace(/\n/g, ' ').trim()}</li>`;
                        }
                        return '';
                    })
                    .filter(item => item);
                return `<ol class="chat-numbered-list">${items.join('')}</ol>`;
            }
            
            // Check if it's a bullet list paragraph
            if (/^[•*]/m.test(paragraph)) {
                const items = paragraph.split(/\n(?=[•*])/)
                    .map(item => {
                        const match = item.match(/^[•*]\s*(.*)$/s);
                        if (match) {
                            return `<li class="chat-bullet">• ${match[1].replace(/\n/g, ' ').trim()}</li>`;
                        }
                        return '';
                    })
                    .filter(item => item);
                return `<ul class="chat-list">${items.join('')}</ul>`;
            }
            
            // Check for Key Insights section
            if (paragraph.startsWith('Key Insights')) {
                const lines = paragraph.split('\n');
                const title = lines[0];
                const body = lines.slice(1).join(' ').trim();
                return `<div class="chat-insights"><h4>★ ${title}</h4><div class="insights-content">${body}</div></div>`;
            }
            
            // Regular paragraph - replace single line breaks with spaces
            return `<p class="chat-paragraph">${paragraph.replace(/\n/g, ' ')}</p>`;
        }).filter(p => p).join('');
    };

    return (
        <div className={`message-bubble ${message.role} ${message.isTyping ? 'typing' : ''}`}>
            <div className="message-content">
                <div 
                    className="message-text enhanced-formatting"
                    dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
                />
                {message.isTyping && (
                    <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                )}
                <div className="message-timestamp">
                    {new Date(message.timestamp).toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
};

export default MessageBubble;