import React from 'react';
import './PodcastPromoModal.css';

/**
 * Shown after a completed chat answer to offer “listen as podcast”.
 * Premium answers use included copy (no extra credits).
 */
export default function PodcastPromoModal({ open, onClose, onGenerate, podcastCost, included }) {
  if (!open) return null;

  const cost = podcastCost ?? 2;
  const title = included ? 'You earned a free podcast' : 'Turn this answer into a podcast';
  const body = included
    ? 'This Premium question includes a podcast at no extra cost. Choose English or Hindi to listen.'
    : `Listen to this consultation on the go. Choose English or Hindi — we will generate the audio in that language. First-time generation uses ${cost} credits; replaying the same saved audio is free.`;

  return (
    <div className="podcast-promo-overlay" role="dialog" aria-modal="true" aria-labelledby="podcast-promo-title">
      <div className="podcast-promo-card">
        <h2 id="podcast-promo-title" className="podcast-promo-title">
          {title}
        </h2>
        <p className="podcast-promo-body">
          {body}
        </p>
        <div className="podcast-lang-options">
          <button type="button" className="podcast-lang-option" onClick={() => onGenerate?.('en')}>
            English
          </button>
          <button type="button" className="podcast-lang-option" onClick={() => onGenerate?.('hi')}>
            हिन्दी
          </button>
        </div>
        <div className="podcast-promo-actions">
          <button type="button" className="podcast-promo-btn podcast-promo-btn--secondary" onClick={onClose}>
            Maybe later
          </button>
        </div>
      </div>
    </div>
  );
}
