import React, { useState, useEffect, useRef } from 'react';
import { useCredits } from '../../context/CreditContext';

const ChatInput = ({
    onSendMessage,
    isLoading,
    followUpQuestion = '',
    onFollowUpUsed = () => {},
    onOpenCreditsModal,
    onShowEnhancedPopup,
    isPartnershipMode = false,
    isMundaneMode = false,
    isLocked = false, // when true, composer is disabled until guided steps are completed
}) => {
    const { credits, chatCost, premiumChatCost, partnershipCost, loading: creditsLoading } = useCredits();
    const [message, setMessage] = useState('');
    const [isPremiumAnalysis, setIsPremiumAnalysis] = useState(false);
    const suggestionsScrollRef = useRef(null);

    const scrollSuggestions = (direction) => {
        const el = suggestionsScrollRef.current;
        if (!el) return;
        el.scrollBy({ left: direction * 280, behavior: 'smooth' });
    };
    
    useEffect(() => {
        if (followUpQuestion) {
            setMessage(followUpQuestion);
            onFollowUpUsed();
        }
    }, [followUpQuestion, onFollowUpUsed]);

    const currentCost = isPremiumAnalysis ? premiumChatCost : (isPartnershipMode ? partnershipCost : chatCost);
    
    const handleSubmit = (e) => {
        e.preventDefault();
        if (isLocked) return;
        if (message.trim() && !isLoading && credits >= currentCost) {
            onSendMessage(message.trim(), { premium_analysis: isPremiumAnalysis });
            setMessage('');
        }
    };

    const suggestions = isMundaneMode
        ? [
            "What are the likely phases for this event category this year?",
            "What risks might show up, and how can we prepare?",
            "Which outcomes look more probable, and when?",
            "What broader macro themes are active right now?",
            "Are there signs of stability or volatility ahead?",
            "What should we watch in the next few months?",
        ]
        : isPartnershipMode
            ? [
                "Are we compatible for marriage?",
                "What are our relationship strengths?",
                "What challenges might we face together?",
                "When is a good time for us to get married?",
                "How do our personalities complement each other?",
                "What does our composite chart reveal?",
            ]
            : [
                "What does my birth chart say about my career?",
                "When is a good time for marriage?",
                "What are my health vulnerabilities?",
                "Tell me about my current dasha period",
                "What do the current transits mean for me?",
                "What are my strengths and weaknesses?",
            ];

    return (
        <div className="chat-input-container">
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
                flexDirection: 'column',
                alignItems: 'stretch',
                gap: '10px',
                marginBottom: '10px',
                padding: '8px 12px',
                background: 'rgba(255,107,53,0.06)',
                border: '1px solid rgba(0,0,0,0.06)',
                borderRadius: '8px',
                fontSize: '14px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#111827' }}>
                        <input
                            type="checkbox"
                            checked={isPremiumAnalysis}
                            onChange={(e) => setIsPremiumAnalysis(e.target.checked)}
                            style={{ transform: 'scale(1.2)' }}
                            disabled={isLocked}
                        />
                        <span>🚀 Premium Deep Analysis</span>
                    </label>
                    <span style={{
                        background: isPremiumAnalysis ? 'linear-gradient(45deg, #ff6b35, #ffd700)' : '#666',
                        color: '#ffffff',
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

                {!isLoading && !isLocked && (
                    <div className="suggestions-scroll-wrapper">
                        <button
                            type="button"
                            className="suggestions-arrow-btn"
                            onClick={() => scrollSuggestions(-1)}
                            aria-label="Scroll suggestions left"
                        >
                            ←
                        </button>
                        <div
                            ref={suggestionsScrollRef}
                            className="suggestions-scroll-row"
                        >
                            {suggestions.map((suggestion, index) => (
                                <button
                                    key={index}
                                    className="suggestion-button suggestion-chip"
                                    onClick={() => setMessage(suggestion)}
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                        <button
                            type="button"
                            className="suggestions-arrow-btn"
                            onClick={() => scrollSuggestions(1)}
                            aria-label="Scroll suggestions right"
                        >
                            →
                        </button>
                    </div>
                )}
            </div>
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder={
                        isLocked
                            ? 'Complete the guided steps above to unlock chat...'
                            : isLoading
                                ? "Analyzing your chart..."
                                : credits < currentCost
                                    ? "Insufficient credits"
                                    : isPartnershipMode
                                        ? "Ask about your compatibility..."
                                        : isMundaneMode
                                            ? "Ask about global events..."
                                            : "Ask me about your birth chart..."
                    }
                    disabled={isLoading || credits < currentCost || isLocked}
                    className="chat-input"
                />
                <button 
                    type="submit" 
                    disabled={!message.trim() || isLoading || credits < currentCost || isLocked}
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