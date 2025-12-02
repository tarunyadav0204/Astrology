import React from 'react';
import MessageBubble from './MessageBubble';

const MessageList = ({ messages, language = 'english', onMessageHover, onFollowUpClick, onChartRefClick, onRestartPolling }) => {
    return (
        <div className="message-list">
            {messages.map((message, index) => (
                <div 
                    key={message.id || index}
                    onMouseEnter={(e) => onMessageHover && onMessageHover(message, e.currentTarget)}
                    onMouseLeave={() => onMessageHover && onMessageHover(null, null)}
                >
                    <MessageBubble 
                        message={message} 
                        language={language} 
                        onFollowUpClick={onFollowUpClick}
                        onChartRefClick={onChartRefClick}
                        onRestartPolling={onRestartPolling}
                    />
                </div>
            ))}
        </div>
    );
};

export default MessageList;