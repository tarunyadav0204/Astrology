import React from 'react';
import './FirstPurchaseOffer.css';

function formatCountdown(seconds) {
    const safe = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(safe / 60);
    return `${minutes}:${String(safe % 60).padStart(2, '0')}`;
}

export default function FirstPurchaseOffer({
    offer,
    remainingSeconds,
    modalOpen,
    onClaim,
    onCloseModal,
}) {
    if (!offer || remainingSeconds <= 0) return null;
    const total = Math.max(1, Number(offer.windowMinutes || 30) * 60);
    const ratio = remainingSeconds / total;
    const stage = ratio > 0.75 ? 'green' : ratio > 0.5 ? 'yellow' : ratio > 0.25 ? 'orange' : 'red';
    const bonus = Number(offer.bonusCredits || 0);
    const totalCredits = Number(offer.purchasedCredits || 50) + bonus;
    const price = offer.price || '₹100';
    const title = bonus >= Number(offer.purchasedCredits || 50)
        ? 'DOUBLE CREDITS UNLOCKED'
        : 'LIMITED-TIME OFFER';

    return (
        <>
            {!modalOpen && (
                <button type="button" className={`first-purchase-offer-chip first-purchase-offer-chip--${stage}`} onClick={onClaim}>
                    <span className="first-purchase-offer-chip__gift">🎁</span>
                    <span className="first-purchase-offer-chip__copy">
                        <strong>{title}</strong>
                        <span>{bonus} bonus credits · {formatCountdown(remainingSeconds)} left</span>
                    </span>
                    <span className="first-purchase-offer-chip__arrow">→</span>
                </button>
            )}
            {modalOpen && (
                <div className="first-purchase-offer-backdrop" role="presentation">
                    <div className="first-purchase-offer-modal" role="dialog" aria-modal="true" aria-labelledby="first-purchase-offer-title">
                        <button type="button" className="first-purchase-offer-close" onClick={onCloseModal} aria-label="Continue reading">×</button>
                        <div className="first-purchase-offer-eyebrow">LIMITED-TIME OFFER</div>
                        <h2 id="first-purchase-offer-title">{title}</h2>
                        <p className="first-purchase-offer-body">
                            For your first purchase, get {bonus} extra credits when you buy {offer.purchasedCredits || 50} credits.
                        </p>
                        <div className="first-purchase-offer-price">Pay {price} · get {totalCredits} credits</div>
                        <div className={`first-purchase-offer-countdown first-purchase-offer-countdown--${stage}`}>
                            ⏰ {formatCountdown(remainingSeconds)} left
                        </div>
                        <button type="button" className="first-purchase-offer-claim" onClick={onClaim}>
                            Claim {totalCredits} credits for {price} →
                        </button>
                        <button type="button" className="first-purchase-offer-continue" onClick={onCloseModal}>Continue reading</button>
                    </div>
                </div>
            )}
        </>
    );
}
