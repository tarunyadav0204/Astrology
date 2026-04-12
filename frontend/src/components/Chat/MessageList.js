import React from 'react';
import MessageBubble from './MessageBubble';
import FeedbackComponent from './FeedbackComponent';

/** Skip rows that would render only a timestamp (empty bubble body). */
function messageRowShouldRender(message) {
    if (!message) return false;
    if (message.isTyping || message.isProcessing) return true;
    const content = message.content != null ? String(message.content).trim() : '';
    const loading = message.loadingMessage != null ? String(message.loadingMessage).trim() : '';
    if (content || loading) return true;
    if (message.summary_image) return true;
    if (message.role === 'assistant' && message.chartData) return true;
    return false;
}

const MessageList = ({
    messages,
    language = 'english',
    sessionId = null,
    onMessageHover,
    onFollowUpClick,
    onChartRefClick,
    onRestartPolling,
    onDeleteMessage,
    onNativeGateOpenSelectNative,
    onNativeGateOpenAddProfile,
}) => {
    return (
        <div className="message-list">
            {messages.map((message, index) => (
                !messageRowShouldRender(message) ? null : (
                <div
                    key={message.id || message.messageId || index}
                    className={`message-list-item message-list-item--${message.role === 'user' ? 'user' : 'assistant'}`}
                    data-chat-message-index={index}
                    data-chat-scroll-id={
                        message.messageId != null
                            ? String(message.messageId)
                            : message.id != null
                              ? String(message.id)
                              : undefined
                    }
                >
                    <div className="message-list-item__stack">
                        <div 
                            onMouseEnter={(e) => onMessageHover && onMessageHover(message, e.currentTarget)}
                            onMouseLeave={() => onMessageHover && onMessageHover(null, null)}
                        >
                            <MessageBubble 
                                message={message} 
                                language={language}
                                sessionId={sessionId}
                                onFollowUpClick={onFollowUpClick}
                                onChartRefClick={onChartRefClick}
                                onRestartPolling={onRestartPolling}
                                onDeleteMessage={onDeleteMessage}
                                onNativeGateOpenSelectNative={onNativeGateOpenSelectNative}
                                onNativeGateOpenAddProfile={onNativeGateOpenAddProfile}
                            />
                        </div>
                        <FeedbackComponent 
                            message={message} 
                            onFeedbackSubmitted={(messageId, rating) => {
                                console.log('Feedback submitted:', messageId, rating);
                            }}
                        />
                    </div>
                </div>
                )
            ))}
        </div>
    );
};

export default MessageList;