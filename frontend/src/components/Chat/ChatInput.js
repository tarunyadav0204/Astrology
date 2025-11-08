import React, { useState, useEffect } from 'react';

const ChatInput = ({ onSendMessage, isLoading, followUpQuestion = '', onFollowUpUsed = () => {} }) => {
    const [message, setMessage] = useState('');
    
    useEffect(() => {
        if (followUpQuestion) {
            setMessage(followUpQuestion);
            onFollowUpUsed();
        }
    }, [followUpQuestion, onFollowUpUsed]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !isLoading) {
            onSendMessage(message.trim());
            setMessage('');
        }
    };

    const suggestions = [
        "What does my birth chart say about my career?",
        "When is a good time for marriage?",
        "What are my health vulnerabilities?",
        "Tell me about my current dasha period",
        "What do the current transits mean for me?",
        "What are my strengths and weaknesses?"
    ];

    return (
        <div className="chat-input-container">
            {!isLoading && (
                <div className="suggestions">
                    {suggestions.map((suggestion, index) => (
                        <button
                            key={index}
                            className="suggestion-button"
                            onClick={() => setMessage(suggestion)}
                        >
                            {suggestion}
                        </button>
                    ))}
                </div>
            )}
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder={isLoading ? "Analyzing your chart..." : "Ask me about your birth chart..."}
                    disabled={isLoading}
                    className="chat-input"

                />
                <button 
                    type="submit" 
                    disabled={!message.trim() || isLoading}
                    className="send-button"
                >
                    {isLoading ? '...' : 'Send'}
                </button>
            </form>
        </div>
    );
};

export default ChatInput;