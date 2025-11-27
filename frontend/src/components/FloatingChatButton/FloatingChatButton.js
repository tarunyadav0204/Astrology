import React from 'react';
import './FloatingChatButton.css';

const FloatingChatButton = ({ onOpenChat }) => {
  return (
    <div className="floating-chat-widget">
      <button className="floating-chat-btn" onClick={onOpenChat}>
        💬 Ask Question Now
        <span className="chat-pulse"></span>
      </button>
    </div>
  );
};

export default FloatingChatButton;
