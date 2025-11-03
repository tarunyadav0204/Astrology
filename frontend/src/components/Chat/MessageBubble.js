import React from 'react';

const MessageBubble = ({ message }) => {
    const formatContent = (content) => {
        return content
            // Headers with colored styling
            .replace(/### (.*?)\n/g, '<h3 class="chat-header">$1</h3>')
            // Bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong class="chat-bold">$1</strong>')
            // Italics for Sanskrit terms
            .replace(/\*(.*?)\*/g, '<em class="chat-italic">$1</em>')
            // Bullet points
            .replace(/• (.*?)\n/g, '<li class="chat-bullet">$1</li>')
            .replace(/(<li class="chat-bullet">.*<\/li>)/gs, '<ul class="chat-list">$1</ul>')
            // Final thoughts/summary detection
            .replace(/(Final Thoughts|Conclusion|Summary)(.*?)(?=\n\n|$)/gs, '<div class="chat-summary"><h4>$1</h4><p>$2</p></div>')
            // Key insights box
            .replace(/(Key Insights[^:]*:)(.*?)(?=###|Final|Conclusion|$)/gs, '<div class="chat-insights"><h4>$1</h4><div class="insights-content">$2</div></div>')
            // Line breaks
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
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