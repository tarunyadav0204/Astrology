import React, { useState, useRef, useEffect } from 'react';
import './FeedbackComponent.css';

const FeedbackComponent = ({ message, onFeedbackSubmitted }) => {
  const [feedback, setFeedback] = useState({ rating: 0, comment: '', submitted: false });
  const [visible, setVisible] = useState(false);
  const [fadeClass, setFadeClass] = useState('');

  useEffect(() => {
    // Show feedback only for 'answer' type messages from assistant
    if (message.role === 'assistant' && 
        !message.isProcessing && 
        message.messageId && 
        message.message_type === 'answer') {
      const timer = setTimeout(() => {
        setVisible(true);
        setFadeClass('fade-in');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message.isProcessing, message.message_type]);

  const submitFeedback = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/chat/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message_id: String(message.messageId),
          rating: feedback.rating,
          comment: feedback.comment.trim() || null
        })
      });

      if (response.ok) {
        setFeedback(prev => ({ ...prev, submitted: true }));
        if (onFeedbackSubmitted) {
          onFeedbackSubmitted(message.messageId, feedback.rating);
        }
        setTimeout(() => {
          setFadeClass('fade-out');
          setTimeout(() => setVisible(false), 500);
        }, 2000);
      } else {
        alert('Failed to submit feedback');
      }
    } catch (error) {
      alert('Failed to submit feedback');
    }
  };

  const handleStarPress = (rating) => {
    setFeedback(prev => ({ ...prev, rating }));
  };

  const handleSkip = () => {
    setFadeClass('fade-out');
    setTimeout(() => setVisible(false), 300);
  };

  if (!visible) return null;

  return (
    <div className={`feedback-component ${fadeClass}`}>
      {feedback.submitted ? (
        <div className="feedback-thanks">Thanks for your feedback! 🙏</div>
      ) : (
        <>
          <div className="feedback-title">How was this answer?</div>
          <div className="feedback-stars">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleStarPress(star)}
                className="feedback-star"
              >
                <span style={{ color: star <= feedback.rating ? '#FFD700' : '#999' }}>★</span>
              </button>
            ))}
          </div>
          {feedback.rating > 0 && (
            <>
              <textarea
                className="feedback-comment"
                placeholder="Tell us more (optional)"
                value={feedback.comment}
                onChange={(e) => setFeedback(prev => ({ ...prev, comment: e.target.value }))}
                rows={3}
              />
              <div className="feedback-buttons">
                <button className="feedback-submit" onClick={submitFeedback}>
                  Submit
                </button>
                <button className="feedback-skip" onClick={handleSkip}>
                  Skip
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default FeedbackComponent;