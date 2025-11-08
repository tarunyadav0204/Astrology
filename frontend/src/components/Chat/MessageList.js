import React from 'react';
import MessageBubble from './MessageBubble';

const MessageList = ({ messages, language = 'english', onMessageHover }) => {
    return (
        <div className="message-list">
            {messages.map((message, index) => (
                <div 
                    key={message.id || index}
                    onMouseEnter={(e) => onMessageHover && onMessageHover(message, e.currentTarget)}
                    onMouseLeave={() => onMessageHover && onMessageHover(null, null)}
                >
                    <MessageBubble message={message} language={language} />
                </div>
            ))}
        </div>
    );
};

export default MessageList;