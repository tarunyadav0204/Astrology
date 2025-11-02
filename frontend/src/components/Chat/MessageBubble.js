import React from 'react';

const MessageBubble = ({ message }) => {
    const formatContent = (content) => {
        return content
            .replace(/### (.*?)\n/g, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\* (.*?)\n/g, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    };

    return (
        <div className={`message-bubble ${message.role} ${message.isTyping ? 'typing' : ''}`}>
            <div className="message-content">
                <div 
                    className="message-text"
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