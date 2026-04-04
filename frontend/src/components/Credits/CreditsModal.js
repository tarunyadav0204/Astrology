import React, { useState, useEffect, useCallback } from 'react';
import { useCredits } from '../../context/CreditContext';
import './CreditsModal.css';

const RAZORPAY_SCRIPT = 'https://checkout.razorpay.com/v1/checkout.js';

function loadRazorpayScript() {
    return new Promise((resolve, reject) => {
        if (typeof window !== 'undefined' && window.Razorpay) {
            resolve(window.Razorpay);
            return;
        }
        const existing = document.querySelector(`script[src="${RAZORPAY_SCRIPT}"]`);
        if (existing) {
            existing.addEventListener('load', () => resolve(window.Razorpay));
            existing.addEventListener('error', () => reject(new Error('Payment script failed to load')));
            return;
        }
        const s = document.createElement('script');
        s.src = RAZORPAY_SCRIPT;
        s.async = true;
        s.onload = () => resolve(window.Razorpay);
        s.onerror = () => reject(new Error('Payment script failed to load'));
        document.body.appendChild(s);
    });
}

const CreditsModal = ({ isOpen, onClose, onLogin }) => {
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

    const [razorpayCatalog, setRazorpayCatalog] = useState(null);
    const [razorpayCatalogLoading, setRazorpayCatalogLoading] = useState(false);
    const [razorpayCatalogError, setRazorpayCatalogError] = useState('');
    const [purchasingCredits, setPurchasingCredits] = useState(null);
    const [purchaseMessage, setPurchaseMessage] = useState('');

    const authHeaders = useCallback(() => {
        const token = localStorage.getItem('token');
        const h = { 'Content-Type': 'application/json' };
        if (token) h.Authorization = `Bearer ${token}`;
        return h;
    }, []);

    const isLoggedIn =
        typeof window !== 'undefined' && typeof localStorage !== 'undefined' && !!localStorage.getItem('token');

    useEffect(() => {
        if (!isOpen) {
            setPurchaseMessage('');
            setPurchasingCredits(null);
        }
    }, [isOpen]);

    useEffect(() => {
        if (!isOpen) return;
        fetchBalance();
        fetchCosts();
    }, [isOpen, fetchBalance, fetchCosts]);

    useEffect(() => {
        if (!isOpen || !isLoggedIn) {
            setRazorpayCatalog(null);
            setRazorpayCatalogError('');
            return;
        }
        let cancelled = false;
        setRazorpayCatalogLoading(true);
        setRazorpayCatalogError('');
        fetch('/api/credits/razorpay/catalog', { headers: authHeaders() })
            .then((res) => {
                if (!res.ok) {
                    return res.json().then((d) => {
                        throw new Error(d.detail || d.message || 'Catalog unavailable');
                    });
                }
                return res.json();
            })
            .then((data) => {
                if (!cancelled) setRazorpayCatalog(data);
            })
            .catch((err) => {
                if (!cancelled) {
                    setRazorpayCatalog(null);
                    setRazorpayCatalogError(err.message || 'Could not load payment options');
                }
            })
            .finally(() => {
                if (!cancelled) setRazorpayCatalogLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [isOpen, isLoggedIn, authHeaders]);

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

    const handleBuyPack = async (creditsAmount) => {
        setPurchaseMessage('');
        if (!isLoggedIn) {
            setPurchaseMessage('❌ Sign in to buy credits');
            return;
        }
        setPurchasingCredits(creditsAmount);
        try {
            const orderRes = await fetch('/api/credits/razorpay/create-order', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ credits: creditsAmount }),
            });
            const orderData = await orderRes.json().catch(() => ({}));
            if (!orderRes.ok) {
                throw new Error(orderData.detail || orderData.message || 'Could not start payment');
            }

            const Razorpay = await loadRazorpayScript();

            const options = {
                key: orderData.key_id,
                amount: orderData.amount,
                currency: orderData.currency || 'INR',
                order_id: orderData.order_id,
                name: 'AstroRoshni',
                description: `${orderData.credits} credits`,
                theme: { color: '#e91e63' },
                modal: {
                    ondismiss: () => setPurchasingCredits(null),
                },
                handler: async (response) => {
                    try {
                        const verifyRes = await fetch('/api/credits/razorpay/verify', {
                            method: 'POST',
                            headers: authHeaders(),
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature,
                            }),
                        });
                        const verifyData = await verifyRes.json().catch(() => ({}));
                        if (!verifyRes.ok) {
                            throw new Error(verifyData.detail || verifyData.message || 'Verification failed');
                        }
                        const added = verifyData.credits_added;
                        if (added > 0) {
                            setPurchaseMessage(`✅ Added ${added} credits to your balance. Thank you!`);
                        } else {
                            setPurchaseMessage(`✅ ${verifyData.message || 'Your balance is up to date.'}`);
                        }
                        fetchBalance();
                        window.dispatchEvent(new CustomEvent('creditUpdated'));
                    } catch (err) {
                        setPurchaseMessage(
                            `❌ ${err.message || 'Payment succeeded but confirmation failed. If credits are missing, contact support with your payment receipt.'}`
                        );
                    } finally {
                        setPurchasingCredits(null);
                    }
                },
            };

            const rzp = new Razorpay(options);
            rzp.open();
        } catch (err) {
            setPurchaseMessage(`❌ ${err.message || 'Could not open payment'}`);
            setPurchasingCredits(null);
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

                <div className="credits-modal-buy-section">
                    <h3 className="credits-modal-section-title">Buy credits</h3>
                    <p className="credits-modal-buy-lead">Secure checkout (UPI, cards, netbanking) — same packs as the Android app.</p>
                    {!isLoggedIn && (
                        <div className="credits-modal-buy-guest">
                            <p className="credits-modal-buy-guest-text">Sign in to purchase credits.</p>
                            {typeof onLogin === 'function' && (
                                <button type="button" className="credits-modal-btn-signin" onClick={onLogin}>
                                    Sign in
                                </button>
                            )}
                        </div>
                    )}
                    {isLoggedIn && razorpayCatalogLoading && (
                        <p className="credits-modal-buy-loading">Loading payment options…</p>
                    )}
                    {isLoggedIn && razorpayCatalogError && (
                        <div className="credits-modal-message credits-modal-message--err">{razorpayCatalogError}</div>
                    )}
                    {isLoggedIn && razorpayCatalog && razorpayCatalog.packs && (
                        <div className="credits-modal-pack-grid">
                            {razorpayCatalog.packs.map((pack) => (
                                <button
                                    key={pack.credits}
                                    type="button"
                                    className="credits-modal-pack-card"
                                    onClick={() => handleBuyPack(pack.credits)}
                                    disabled={purchasingCredits !== null}
                                >
                                    <span className="credits-modal-pack-credits">{pack.credits}</span>
                                    <span className="credits-modal-pack-label">credits</span>
                                    <span className="credits-modal-pack-price">{pack.amount_display}</span>
                                    {purchasingCredits === pack.credits && (
                                        <span className="credits-modal-pack-busy">Opening…</span>
                                    )}
                                </button>
                            ))}
                        </div>
                    )}
                    {isLoggedIn && !razorpayCatalogLoading && !razorpayCatalogError && razorpayCatalog && (
                        <p className="credits-modal-razorpay-badge" aria-hidden="true">
                            Secured by Razorpay
                        </p>
                    )}
                    {purchaseMessage && (
                        <div
                            className={`credits-modal-message ${
                                purchaseMessage.includes('✅') ? 'credits-modal-message--ok' : 'credits-modal-message--err'
                            }`}
                        >
                            {purchaseMessage}
                        </div>
                    )}
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
