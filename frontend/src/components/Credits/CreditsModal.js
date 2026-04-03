import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import './CreditsModal.css';

const CreditsModal = ({ isOpen, onClose }) => {
    const {
        credits,
        fetchBalance,
        fetchCosts,
        chatCost,
        premiumChatCost,
        partnershipCost,
        wealthCost,
        marriageCost,
        healthCost,
        educationCost,
        careerCost,
        loading,
    } = useCredits();
    const [promoCode, setPromoCode] = useState('');
    const [promoLoading, setPromoLoading] = useState(false);
    const [message, setMessage] = useState('');

    const [requestAmount, setRequestAmount] = useState('');
    const [requestReason, setRequestReason] = useState('');
    const [requestLoading, setRequestLoading] = useState(false);
    const [requestMessage, setRequestMessage] = useState('');

    useEffect(() => {
        if (!isOpen) return;
        fetchBalance();
        fetchCosts();
    }, [isOpen, fetchBalance, fetchCosts]);

    const formatCredits = (n) => {
        const x = Number(n);
        if (!Number.isFinite(x)) return '—';
        return `${x} credit${x !== 1 ? 's' : ''}`;
    };

    const costRows = [
        { label: 'Chat (standard)', value: chatCost },
        { label: 'Chat (premium deep)', value: premiumChatCost },
        { label: 'Partnership / compatibility chat', value: partnershipCost },
        { label: 'Marriage analysis', value: marriageCost },
        { label: 'Wealth analysis', value: wealthCost },
        { label: 'Health analysis', value: healthCost },
        { label: 'Education analysis', value: educationCost },
        { label: 'Career guidance', value: careerCost },
    ];

    const handleRedeemPromo = async (e) => {
        e.preventDefault();
        if (!promoCode.trim()) return;

        setPromoLoading(true);
        setMessage('');

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/credits/redeem', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` }),
                },
                body: JSON.stringify({ code: promoCode.trim() }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setMessage(`✅ ${data.message}`);
                setPromoCode('');
                fetchBalance();

                window.dispatchEvent(new CustomEvent('creditUpdated'));
            } else {
                const errorMessage = data.detail || data.message || 'Invalid promo code';
                setMessage(`❌ ${errorMessage}`);
            }
        } catch (error) {
            setMessage('❌ Error redeeming promo code');
        } finally {
            setPromoLoading(false);
        }
    };

    const validateReason = (reason) => {
        return reason
            .replace(/<[^>]*>/g, '')
            .replace(/[<>'"]/g, '')
            .trim()
            .substring(0, 500);
    };

    const handleCreditRequest = async (e) => {
        e.preventDefault();
        if (!requestAmount || !requestReason.trim()) return;

        const sanitizedReason = validateReason(requestReason);
        if (sanitizedReason.length < 10) {
            setRequestMessage('❌ Reason must be at least 10 characters');
            return;
        }

        setRequestLoading(true);
        setRequestMessage('');

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/credits/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` }),
                },
                body: JSON.stringify({
                    amount: parseInt(requestAmount, 10),
                    reason: sanitizedReason,
                }),
            });

            const data = await response.json();

            if (data.success) {
                setRequestMessage(`✅ ${data.message}`);
                setRequestAmount('');
                setRequestReason('');
            } else {
                setRequestMessage(`❌ ${data.message}`);
            }
        } catch (error) {
            setRequestMessage('❌ Error submitting request');
        } finally {
            setRequestLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="credits-modal-overlay" onClick={onClose} role="presentation">
            <div
                className="credits-modal-panel"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-labelledby="credits-modal-title"
            >
                <button type="button" className="credits-modal-close" onClick={onClose} aria-label="Close">
                    ×
                </button>

                <div className="credits-modal-head">
                    <h2 id="credits-modal-title" className="credits-modal-title">
                        Credits
                    </h2>
                    <div className="credits-modal-balance" aria-live="polite">
                        <span className="credits-modal-balance-label">Balance</span>
                        <span className="credits-modal-balance-value">{credits}</span>
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 className="credits-modal-section-title">Redeem promo code</h3>
                    <form onSubmit={handleRedeemPromo} className="credits-modal-form-row credits-modal-form-row--inline">
                        <input
                            type="text"
                            value={promoCode}
                            onChange={(e) => setPromoCode(e.target.value)}
                            placeholder="Enter promo code"
                            className="credits-modal-input"
                            disabled={promoLoading}
                            autoComplete="off"
                        />
                        <button
                            type="submit"
                            disabled={promoLoading || !promoCode.trim()}
                            className="credits-modal-btn-primary"
                        >
                            {promoLoading ? 'Redeeming…' : 'Redeem'}
                        </button>
                    </form>
                    {message && (
                        <div
                            className={`credits-modal-message ${
                                message.includes('✅') ? 'credits-modal-message--ok' : 'credits-modal-message--err'
                            }`}
                        >
                            {message}
                        </div>
                    )}
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 className="credits-modal-section-title">Request credits</h3>
                    <form
                        onSubmit={handleCreditRequest}
                        style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '10px' }}
                    >
                        <input
                            type="number"
                            value={requestAmount}
                            onChange={(e) => setRequestAmount(e.target.value)}
                            placeholder="Credits needed (1–100)"
                            min="1"
                            max="100"
                            className="credits-modal-input"
                            disabled={requestLoading}
                        />
                        <textarea
                            value={requestReason}
                            onChange={(e) => setRequestReason(e.target.value)}
                            placeholder="Reason for request (e.g., student discount, financial hardship)"
                            rows={3}
                            className="credits-modal-textarea"
                            disabled={requestLoading}
                            maxLength={500}
                        />
                        <button
                            type="submit"
                            disabled={requestLoading || !requestAmount || !requestReason.trim()}
                            className="credits-modal-btn-green"
                        >
                            {requestLoading ? 'Submitting…' : 'Submit request'}
                        </button>
                    </form>
                    {requestMessage && (
                        <div
                            className={`credits-modal-message ${
                                requestMessage.includes('✅')
                                    ? 'credits-modal-message--ok'
                                    : 'credits-modal-message--err'
                            }`}
                        >
                            {requestMessage}
                        </div>
                    )}
                </div>

                <div className="credits-modal-costs">
                    <h4 className="credits-modal-costs-title">Typical credit use</h4>
                    <p className="credits-modal-costs-hint">
                        {loading
                            ? 'Loading your rates…'
                            : 'Amounts below follow your account pricing when you are signed in, otherwise standard public rates.'}
                    </p>
                    {loading ? (
                        <p className="credits-modal-costs-loading">Fetching current prices…</p>
                    ) : (
                        costRows.map((row) => (
                            <div key={row.label} className="credits-modal-cost-row">
                                <span className="credits-modal-cost-label">{row.label}</span>
                                <span className="credits-modal-cost-value">{formatCredits(row.value)}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default CreditsModal;
