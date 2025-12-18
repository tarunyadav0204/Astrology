import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';

const ChatInput = ({ onSendMessage, isLoading, followUpQuestion = '', onFollowUpUsed = () => {}, onOpenCreditsModal, onShowEnhancedPopup, isPartnershipMode = false }) => {
    const { credits, chatCost, premiumChatCost, partnershipCost, loading: creditsLoading } = useCredits();
    const [message, setMessage] = useState('');
    const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
    
    useEffect(() => {
        if (followUpQuestion) {
            setMessage(followUpQuestion);
            onFollowUpUsed();
        }
    }, [followUpQuestion, onFollowUpUsed]);

    const currentCost = isPremiumAnalysis ? premiumChatCost : (isPartnershipMode ? partnershipCost : chatCost);
    
    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !isLoading && credits >= currentCost) {
            onSendMessage(message.trim(), { premium_analysis: isPremiumAnalysis });
            setMessage('');
        }
    };

    const suggestions = isPartnershipMode ? [
        "Are we compatible for marriage?",
        "What are our relationship strengths?",
        "What challenges might we face together?",
        "When is a good time for us to get married?",
        "How do our personalities complement each other?",
        "What does our composite chart reveal?"
    ] : [
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
            {!creditsLoading && credits < currentCost && (
                <div className="credit-warning">
                    <span>Insufficient credits ({credits}/{currentCost} required for {isPremiumAnalysis ? 'Premium Deep Analysis' : isPartnershipMode ? 'Partnership Analysis' : 'Standard Analysis'})</span>
                    <button onClick={onOpenCreditsModal} className="get-credits-btn">
                        Get Credits
                    </button>
                </div>
            )}
            <div className="premium-toggle-container" style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                marginBottom: '10px',
                padding: '8px 12px',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '8px',
                fontSize: '14px'
            }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: 'white' }}>
                    <input
                        type="checkbox"
                        checked={isPremiumAnalysis}
                        onChange={(e) => setIsPremiumAnalysis(e.target.checked)}
                        style={{ transform: 'scale(1.2)' }}
                    />
                    <span>🚀 Premium Deep Analysis</span>
                </label>
                <span style={{ 
                    background: isPremiumAnalysis ? 'linear-gradient(45deg, #ff6b35, #ffd700)' : '#666',
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    boxShadow: isPremiumAnalysis ? '0 2px 8px rgba(255, 107, 53, 0.3)' : 'none'
                }}>
                    {isPremiumAnalysis ? premiumChatCost : (isPartnershipMode ? partnershipCost : chatCost)} credits
                </span>
                {isPremiumAnalysis && (
                    <span 
                        className="enhanced-analysis-badge"
                        onClick={() => onShowEnhancedPopup && onShowEnhancedPopup()}
                        style={{ cursor: 'pointer' }}
                    >
                        ✨ Enhanced Analysis
                    </span>
                )}
            </div>
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder={isLoading ? "Analyzing your chart..." : credits < currentCost ? "Insufficient credits" : isPartnershipMode ? "Ask about your compatibility..." : "Ask me about your birth chart..."}
                    disabled={isLoading || credits < currentCost}
                    className="chat-input"
                />
                <button 
                    type="submit" 
                    disabled={!message.trim() || isLoading || credits < currentCost}
                    className="send-button"
                    style={{
                        background: isPremiumAnalysis ? 'linear-gradient(45deg, #ff6b35, #ffd700)' : undefined,
                        boxShadow: isPremiumAnalysis ? '0 2px 12px rgba(255, 107, 53, 0.4)' : undefined
                    }}
                >
                    {isLoading ? '...' : credits < currentCost ? 'No Credits' : isPremiumAnalysis ? '🚀 Send Premium' : isPartnershipMode ? '💕 Send Partnership' : 'Send'}
                </button>
            </form>
            {!creditsLoading && (
                <div className="credit-info">
                    Credits: {credits} | {isPremiumAnalysis ? `Premium: ${premiumChatCost}` : isPartnershipMode ? `Partnership: ${partnershipCost}` : `Standard: ${chatCost}`} credits per question
                </div>
            )}
        </div>
    );
};

export default ChatInput;