import React from 'react';
import './FloatingChatButton.css';

const FloatingChatButton = ({ onOpenChat }) => {
  return (
    <div className="floating-chat-widget">
      <button className="floating-chat-btn" onClick={onOpenChat}>
        <span className="chat-text-full">⭐ Ask Tara Now</span>
        <span className="chat-text-short">⭐ Ask Tara</span>
        <span className="chat-pulse"></span>
      </button>
    </div>
  );
};

export default FloatingChatButton;
