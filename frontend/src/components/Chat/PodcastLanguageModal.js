import React from 'react';
import { createPortal } from 'react-dom';
import './PodcastPromoModal.css';

const COPY = {
  en: {
    title: 'Choose podcast language',
    body: "We'll generate the audio in the language you pick. English and Hindi only.",
    premiumBody: 'This Premium answer includes a free podcast. Choose English or Hindi.',
    cancel: 'Cancel',
  },
  hi: {
    title: 'पॉडकास्ट की भाषा चुनें',
    body: 'ऑडियो उसी भाषा में बनेगा जो आप चुनेंगे। केवल अंग्रेज़ी और हिंदी।',
    premiumBody: 'इस प्रीमियम उत्तर में मुफ़्त पॉडकास्ट शामिल है। अंग्रेज़ी या हिंदी चुनें।',
    cancel: 'रद्द करें',
  },
};

/**
 * English / Hindi picker before podcast generate or replay.
 */
export default function PodcastLanguageModal({
  open,
  selectedLang = 'en',
  uiLanguage = 'en',
  included = false,
  onSelect,
  onClose,
}) {
  if (!open || typeof document === 'undefined') return null;

  const ui = String(uiLanguage || '').toLowerCase().startsWith('hi') ? 'hi' : 'en';
  const copy = COPY[ui];
  const selected = String(selectedLang || 'en').toLowerCase().startsWith('hi') ? 'hi' : 'en';

  return createPortal(
    <div
      className="podcast-promo-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="podcast-lang-title"
      onClick={onClose}
    >
      <div className="podcast-promo-card" onClick={(e) => e.stopPropagation()}>
        <h2 id="podcast-lang-title" className="podcast-promo-title">
          {copy.title}
        </h2>
        <p className="podcast-promo-body">{included ? copy.premiumBody : copy.body}</p>
        <div className="podcast-lang-options">
          <button
            type="button"
            className={`podcast-lang-option${selected === 'en' ? ' is-selected' : ''}`}
            onClick={() => onSelect?.('en')}
          >
            English
          </button>
          <button
            type="button"
            className={`podcast-lang-option${selected === 'hi' ? ' is-selected' : ''}`}
            onClick={() => onSelect?.('hi')}
          >
            हिन्दी
          </button>
        </div>
        <div className="podcast-promo-actions">
          <button type="button" className="podcast-promo-btn podcast-promo-btn--secondary" onClick={onClose}>
            {copy.cancel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
