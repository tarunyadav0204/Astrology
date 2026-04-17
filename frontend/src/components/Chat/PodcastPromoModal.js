import React from 'react';
import './PodcastPromoModal.css';

/**
 * Shown after a completed chat answer to upsell “listen as podcast” (credits on first generation).
 */
export default function PodcastPromoModal({ open, onClose, onGenerate, podcastCost }) {
  if (!open) return null;

  const cost = podcastCost ?? 2;

  return (
    <div className="podcast-promo-overlay" role="dialog" aria-modal="true" aria-labelledby="podcast-promo-title">
      <div className="podcast-promo-card">
        <h2 id="podcast-promo-title" className="podcast-promo-title">
          Turn this answer into a podcast
        </h2>
        <p className="podcast-promo-body">
          Listen to this consultation on the go. We will generate natural audio from this reply. First-time
          generation uses {cost} credits; replaying the same saved audio is free.
        </p>
        <div className="podcast-promo-actions">
          <button type="button" className="podcast-promo-btn podcast-promo-btn--secondary" onClick={onClose}>
            Maybe later
          </button>
          <button type="button" className="podcast-promo-btn podcast-promo-btn--primary" onClick={onGenerate}>
            Generate podcast
          </button>
        </div>
      </div>
    </div>
  );
}
