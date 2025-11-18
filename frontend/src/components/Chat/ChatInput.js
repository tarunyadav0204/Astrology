import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';

const ChatInput = ({ onSendMessage, isLoading, followUpQuestion = '', onFollowUpUsed = () => {}, onOpenCreditsModal }) => {
    const { credits, chatCost, loading: creditsLoading } = useCredits();
    const [message, setMessage] = useState('');
    
    useEffect(() => {
        if (followUpQuestion) {
            setMessage(followUpQuestion);
            onFollowUpUsed();
        }
    }, [followUpQuestion, onFollowUpUsed]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !isLoading && credits >= chatCost) {
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
            {!creditsLoading && credits < chatCost && (
                <div className="credit-warning">
                    <span>Insufficient credits ({credits}/{chatCost} required)</span>
                    <button onClick={onOpenCreditsModal} className="get-credits-btn">
                        Get Credits
                    </button>
                </div>
            )}
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder={isLoading ? "Analyzing your chart..." : credits < chatCost ? "Insufficient credits" : "Ask me about your birth chart..."}
                    disabled={isLoading || credits < chatCost}
                    className="chat-input"
                />
                <button 
                    type="submit" 
                    disabled={!message.trim() || isLoading || credits < chatCost}
                    className="send-button"
                >
                    {isLoading ? '...' : credits < chatCost ? 'No Credits' : 'Send'}
                </button>
            </form>
            {!creditsLoading && (
                <div className="credit-info">
                    Credits: {credits} | Cost per question: {chatCost}
                </div>
            )}
        </div>
    );
};

export default ChatInput;