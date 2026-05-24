import React, { useEffect, useCallback } from 'react';
import { APP_CONFIG } from '../../config/app.config';
import './WhatsAppHomeBannerModal.css';

const { imageSrc, ctaHref, storageDismissKey } = APP_CONFIG.whatsappHomeBanner;

/**
 * One-time-per-dismissal (localStorage) promo for AstroRoshni on WhatsApp.
 * Expects a 9:16 portrait image at `public/images/whatsapp-home-banner.png`.
 */
export default function WhatsAppHomeBannerModal({ isOpen, onDismiss }) {
  const handleBackdrop = useCallback(() => {
    onDismiss();
  }, [onDismiss]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') onDismiss();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onDismiss]);

  if (!isOpen) return null;

  return (
    <div
      className="whatsapp-home-banner-modal"
      role="dialog"
      aria-modal="true"
      aria-label="AstroRoshni on WhatsApp"
    >
      <div
        className="whatsapp-home-banner-modal__backdrop"
        onClick={handleBackdrop}
        aria-hidden="true"
      />
      <div className="whatsapp-home-banner-modal__panel">
        <div className="whatsapp-home-banner-modal__frame">
          {ctaHref ? (
            <a
              className="whatsapp-home-banner-modal__link-fill"
              href={ctaHref}
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                className="whatsapp-home-banner-modal__img"
                src={imageSrc}
                alt="AstroRoshni on WhatsApp — open in WhatsApp"
                width={720}
                height={1280}
                loading="eager"
                decoding="async"
              />
            </a>
          ) : (
            <img
              className="whatsapp-home-banner-modal__img"
              src={imageSrc}
              alt="AstroRoshni on WhatsApp"
              width={720}
              height={1280}
              loading="eager"
              decoding="async"
            />
          )}
          <button
            type="button"
            className="whatsapp-home-banner-modal__close"
            onClick={(e) => {
              e.stopPropagation();
              onDismiss();
            }}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        {ctaHref ? (
          <p className="whatsapp-home-banner-modal__hint">Tap the banner to open WhatsApp</p>
        ) : null}
      </div>
    </div>
  );
}

/** @returns {boolean} whether the banner was dismissed and should stay hidden. */
export function isWhatsappHomeBannerDismissed() {
  try {
    return window.localStorage.getItem(storageDismissKey) === '1';
  } catch {
    return false;
  }
}

export function dismissWhatsappHomeBannerPersist() {
  try {
    window.localStorage.setItem(storageDismissKey, '1');
  } catch {
    /* ignore private mode */
  }
}
