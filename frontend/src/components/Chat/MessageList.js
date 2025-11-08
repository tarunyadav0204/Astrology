import React from 'react';
import MessageBubble from './MessageBubble';

const MessageList = ({ messages, language = 'english' }) => {
    return (
        <div className="message-list">
            {messages.map((message, index) => (
                <MessageBubble key={message.id || index} message={message} language={language} />
            ))}
        </div>
    );
};

export default MessageList;