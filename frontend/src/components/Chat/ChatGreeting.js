import React from 'react';

const ChatGreeting = ({ birthData, onOptionSelect }) => {
    const place = birthData?.place && !birthData.place.includes(',') ? 
        birthData.place : 
        `${birthData?.latitude}, ${birthData?.longitude}`;

    return (
        <div className="chat-greeting">
            <div className="greeting-message">
                <h3>Hello {birthData?.name}!</h3>
                <p>I see you were born on {new Date(birthData?.date).toLocaleDateString()} at {place}.</p>
                <p>I'm here to help you understand your birth chart and provide astrological guidance.</p>
            </div>
            
            <div className="greeting-options">
                <h4>Choose your approach:</h4>
                <div className="option-buttons">
                    <button 
                        className="option-btn question-btn"
                        onClick={() => onOptionSelect('question')}
                    >
                        <div className="option-icon">💬</div>
                        <div className="option-text">
                            <strong>Ask Any Question</strong>
                            <span>Get insights about your personality, relationships, career, or any astrological topic</span>
                        </div>
                    </button>
                    
                    <button 
                        className="option-btn periods-btn"
                        onClick={() => onOptionSelect('periods')}
                    >
                        <div className="option-icon">🎯</div>
                        <div className="option-text">
                            <strong>Find Event Periods</strong>
                            <span>Discover high-probability periods when specific events might happen</span>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatGreeting;