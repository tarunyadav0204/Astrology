import React from 'react';
import MessageBubble from './MessageBubble';
import FeedbackComponent from './FeedbackComponent';

const MessageList = ({ messages, language = 'english', onMessageHover, onFollowUpClick, onChartRefClick, onRestartPolling, onDeleteMessage }) => {
    return (
        <div className="message-list">
            {messages.map((message, index) => (
                <div key={message.id || index}>
                    <div 
                        onMouseEnter={(e) => onMessageHover && onMessageHover(message, e.currentTarget)}
                        onMouseLeave={() => onMessageHover && onMessageHover(null, null)}
                    >
                        <MessageBubble 
                            message={message} 
                            language={language} 
                            onFollowUpClick={onFollowUpClick}
                            onChartRefClick={onChartRefClick}
                            onRestartPolling={onRestartPolling}
                            onDeleteMessage={onDeleteMessage}
                        />
                    </div>
                    <FeedbackComponent 
                        message={message} 
                        onFeedbackSubmitted={(messageId, rating) => {
                            console.log('Feedback submitted:', messageId, rating);
                        }}
                    />
                </div>
            ))}
        </div>
    );
};

export default MessageList;