import React, { useState, useEffect } from 'react';
import './FeedbackComponent.css';

/** Listing for the Android app (same as AstroRoshni homepage CTA). */
const GOOGLE_PLAY_LISTING_URL =
  'https://play.google.com/store/apps/details?id=com.astroroshni.mobile&pcampaignid=web_share';

const FeedbackPlayStoreLink = () => (
  <div className="feedback-play-row">
    <a
      className="feedback-play-link"
      href={GOOGLE_PLAY_LISTING_URL}
      target="_blank"
      rel="noopener noreferrer"
    >
      <span className="feedback-play-icon" aria-hidden>
        ▶
      </span>
      Leave a rating on Google Play
    </a>
    <span className="feedback-play-hint">Helps others discover the app</span>
  </div>
);

const FEEDBACK_PLACEHOLDERS = {
  helpful: 'What was most helpful? (optional)',
  unclear: 'Which part was unclear? (optional)',
  wrong_personal_detail: 'Which personal detail was wrong, and what should it be? (optional)',
  contradicts_earlier_answer: 'What contradicts an earlier answer? Include the earlier statement if possible. (optional)',
};

const FeedbackComponent = ({ message, onFeedbackSubmitted }) => {
  const [feedback, setFeedback] = useState({ reason: null, rating: 0, comment: '', submitted: false });
  const [submitting, setSubmitting] = useState(false);
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
    if (submitting) return;
    setSubmitting(true);
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
          reason: feedback.reason,
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
    } finally { setSubmitting(false); }
  };


  const handleSkip = () => {
    setFadeClass('fade-out');
    setTimeout(() => setVisible(false), 300);
  };

  if (!visible) return null;

  return (
    <div className={`feedback-component ${fadeClass}`}>
      {feedback.submitted ? (
        <>
          <div className="feedback-thanks">Thanks for your feedback! 🙏</div>
          <FeedbackPlayStoreLink />
        </>
      ) : (
        <>
          <div className="feedback-title">How was this answer?</div>
          <div className="feedback-reasons" role="group" aria-label="Answer feedback">
            <button type="button" disabled={submitting} aria-pressed={feedback.reason === 'helpful'} onClick={() => setFeedback(prev => ({ ...prev, reason: 'helpful', rating: 5 }))}>Helpful</button>
            <button type="button" disabled={submitting} aria-pressed={feedback.reason === 'unclear'} onClick={() => setFeedback(prev => ({ ...prev, reason: 'unclear', rating: 2 }))}>Unclear</button>
            <button type="button" disabled={submitting} aria-pressed={feedback.reason === 'wrong_personal_detail'} onClick={() => setFeedback(prev => ({ ...prev, reason: 'wrong_personal_detail', rating: 1 }))}>Wrong personal detail</button>
            <button type="button" disabled={submitting} aria-pressed={feedback.reason === 'contradicts_earlier_answer'} onClick={() => setFeedback(prev => ({ ...prev, reason: 'contradicts_earlier_answer', rating: 1 }))}>Contradicts an earlier answer</button>
          </div>
          {feedback.rating > 0 && (
            <>
              <textarea
                className="feedback-comment"
                placeholder={FEEDBACK_PLACEHOLDERS[feedback.reason]}
                aria-label={FEEDBACK_PLACEHOLDERS[feedback.reason]}
                value={feedback.comment}
                onChange={(e) => setFeedback(prev => ({ ...prev, comment: e.target.value }))}
                rows={3}
              />
              <div className="feedback-buttons">
                <button className="feedback-submit" disabled={submitting} onClick={submitFeedback}>
                  Submit
                </button>
                <button className="feedback-skip" onClick={handleSkip}>
                  Skip
                </button>
              </div>
            </>
          )}
          <div className="feedback-play-divider" aria-hidden />
          <FeedbackPlayStoreLink />
        </>
      )}
    </div>
  );
};

export default FeedbackComponent;
