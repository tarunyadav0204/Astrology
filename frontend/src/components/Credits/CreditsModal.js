import React, { useState, useEffect, useCallback } from 'react';
import { useCredits } from '../../context/CreditContext';
import { ThemeButton, ThemeInput, ThemeModal } from '../Theme';
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

const CreditsModal = ({ isOpen, onClose, onLogin, firstPurchaseOfferMessageId = null }) => {
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
    const [purchasePromoInput, setPurchasePromoInput] = useState('');
    const [purchasePromoLoading, setPurchasePromoLoading] = useState(false);
    const [purchasePromoMessage, setPurchasePromoMessage] = useState('');
    const [appliedPurchasePromo, setAppliedPurchasePromo] = useState(null);

    const [razorpayCatalog, setRazorpayCatalog] = useState(null);
    const [razorpayCatalogLoading, setRazorpayCatalogLoading] = useState(false);
    const [razorpayCatalogError, setRazorpayCatalogError] = useState('');
    const [purchasingCredits, setPurchasingCredits] = useState(null);
    const [purchaseMessage, setPurchaseMessage] = useState('');

    const authHeaders = useCallback(() => {
        const token = localStorage.getItem('token');
        const h = { 'Content-Type': 'application/json' };
        if (token) {
            h.Authorization = `Bearer ${token}`;
            h['X-AstroRoshni-Authorization'] = `Bearer ${token}`;
        }
        return h;
    }, []);

    const isLoggedIn =
        typeof window !== 'undefined' && typeof localStorage !== 'undefined' && !!localStorage.getItem('token');

    useEffect(() => {
        if (!isOpen) {
            setPurchaseMessage('');
            setPurchasingCredits(null);
            setPurchasePromoMessage('');
        }
    }, [isOpen]);

    // Backup click attribution when opened from the first-purchase offer CTA.
    useEffect(() => {
        if (!isOpen || !firstPurchaseOfferMessageId) return undefined;
        const token = localStorage.getItem('token');
        if (!token) return undefined;
        const mid = String(firstPurchaseOfferMessageId).trim();
        if (!mid) return undefined;
        fetch('/api/credits/first-purchase-offer-funnel/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
                'X-AstroRoshni-Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ event: 'offer_clicked', message_id: mid, platform: 'web' }),
            keepalive: true,
        }).catch(() => {});
        return undefined;
    }, [isOpen, firstPurchaseOfferMessageId]);

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

    const handleApplyPurchasePromo = async (e) => {
        e.preventDefault();
        const code = purchasePromoInput.trim();
        if (!code) return;
        setPurchasePromoLoading(true);
        setPurchasePromoMessage('');
        try {
            const response = await fetch('/api/credits/purchase-promo/preview', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ code, channel: 'web' }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.ok) {
                setAppliedPurchasePromo(null);
                setPurchasePromoMessage(data.message || data.detail || 'This code cannot be used at checkout');
                return;
            }
            setAppliedPurchasePromo(data.promo);
            setPurchasePromoMessage(
                `${data.promo.name}: ${data.promo.percent}% extra credits on this purchase.`
            );
        } catch (_) {
            setAppliedPurchasePromo(null);
            setPurchasePromoMessage('Could not apply this code');
        } finally {
            setPurchasePromoLoading(false);
        }
    };

    const reportPaymentFailure = (payload) => {
        fetch('/api/credits/payment-failure/report', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload),
        }).catch(() => {});
    };

    const handleBuyPack = async (creditsAmount) => {
        setPurchaseMessage('');
        if (!isLoggedIn) {
            setPurchaseMessage('❌ Sign in to buy credits');
            return;
        }
        setPurchasingCredits(creditsAmount);
        let orderId = null;
        try {
            const orderBody = { credits: creditsAmount };
            if (appliedPurchasePromo?.code && Number(creditsAmount) !== 24) {
                orderBody.purchase_promo_code = appliedPurchasePromo.code;
            }
            const mainOrderRequest = () => fetch('/api/credits/razorpay/create-order', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(orderBody),
            });
            const orderRes = await mainOrderRequest();
            const orderData = await orderRes.json().catch(() => ({}));
            if (!orderRes.ok) {
                const error = new Error(orderData.detail || orderData.message || 'Could not start payment');
                error.serverReported = true;
                throw error;
            }
            orderId = orderData.order_id || null;

            const Razorpay = await loadRazorpayScript();

            const checkoutThemeColor = typeof window !== 'undefined'
                ? getComputedStyle(document.documentElement).getPropertyValue('--color-brand').trim()
                : '';
            const options = {
                key: orderData.key_id,
                amount: orderData.amount,
                currency: orderData.currency || 'INR',
                order_id: orderData.order_id,
                name: 'AstroRoshni',
                description: `${orderData.credits} credits`,
                theme: { color: checkoutThemeColor || '#701d3f' },
                modal: {
                    ondismiss: () => setPurchasingCredits(null),
                },
                handler: async (response) => {
                    try {
                        const verifyBody = {
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                        };
                        const mainVerifyRequest = () => fetch('/api/credits/razorpay/verify', {
                            method: 'POST',
                            headers: authHeaders(),
                            body: JSON.stringify(verifyBody),
                        });
                        const verifyRes = await mainVerifyRequest();
                        const verifyData = await verifyRes.json().catch(() => ({}));
                        if (!verifyRes.ok) {
                            const error = new Error(verifyData.detail || verifyData.message || 'Verification failed');
                            error.serverReported = true;
                            throw error;
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
                        if (!err.serverReported) {
                            reportPaymentFailure({
                                provider: 'razorpay',
                                stage: 'credit_client_verify',
                                reference_id: response.razorpay_payment_id || response.razorpay_order_id,
                                product_id: `credits_${creditsAmount}`,
                                error_code: 'client_verify_error',
                                detail: err.message || 'Razorpay payment confirmation failed',
                            });
                        }
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
            if (!err.serverReported) {
                reportPaymentFailure({
                    provider: 'razorpay',
                    stage: 'credit_client_checkout',
                    reference_id: orderId,
                    product_id: `credits_${creditsAmount}`,
                    error_code: 'client_checkout_error',
                    detail: err.message || 'Could not open Razorpay payment',
                });
            }
            setPurchaseMessage(`❌ ${err.message || 'Could not open payment'}`);
            setPurchasingCredits(null);
        }
    };

    return (
        <ThemeModal
            isOpen={isOpen}
            onClose={onClose}
            title="Add AstroRoshni credits"
            description="Choose a pack once, then use your balance across Tara, reports and analysis workspaces."
            size="lg"
            className="credits-modal-panel"
            closeLabel="Close credits"
        >
            <div className="credits-modal-balance" aria-live="polite">
                <div>
                    <span className="credits-modal-balance-label">Available balance</span>
                    <small>Ready across every workspace</small>
                </div>
                <span className="credits-modal-balance-value">{credits}<small>credits</small></span>
            </div>

            <section className="credits-modal-buy-section" aria-labelledby="credits-pack-heading">
                    <div className="credits-modal-section-head">
                        <div>
                            <span>Secure checkout</span>
                            <h3 id="credits-pack-heading" className="credits-modal-section-title">Choose your credit pack</h3>
                        </div>
                        <a href="/subscription" className="credits-modal-vip-link">VIP members save up to 30% <span aria-hidden>↗</span></a>
                    </div>
                    <p className="credits-modal-buy-lead">Pay securely with UPI, cards or netbanking. Packs match the Android app.</p>
                    {isLoggedIn && (
                        <a href="/order-management" className="credits-modal-order-link">
                            Order history and billing support <span aria-hidden>↗</span>
                        </a>
                    )}
                    {!isLoggedIn && (
                        <div className="credits-modal-buy-guest">
                            <p className="credits-modal-buy-guest-text">Sign in to purchase credits.</p>
                            {typeof onLogin === 'function' && (
                                <ThemeButton type="button" className="credits-modal-btn-signin" onClick={onLogin}>
                                    Sign in
                                </ThemeButton>
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
                        <>
                        <form onSubmit={handleApplyPurchasePromo} className="credits-modal-form-row credits-modal-form-row--inline" style={{ marginBottom: '1rem' }}>
                            <ThemeInput
                                type="text"
                                value={purchasePromoInput}
                                onChange={(e) => setPurchasePromoInput(e.target.value)}
                                placeholder="Purchase promo code"
                                className="credits-modal-input"
                                disabled={purchasePromoLoading}
                                autoComplete="off"
                            />
                            <ThemeButton
                                type="submit"
                                disabled={purchasePromoLoading || !purchasePromoInput.trim()}
                                size="md"
                                className="credits-modal-btn-primary"
                            >
                                {purchasePromoLoading ? 'Checking…' : appliedPurchasePromo ? 'Update code' : 'Apply at checkout'}
                            </ThemeButton>
                            {appliedPurchasePromo ? (
                                <ThemeButton
                                    type="button"
                                    size="md"
                                    onClick={() => {
                                        setAppliedPurchasePromo(null);
                                        setPurchasePromoInput('');
                                        setPurchasePromoMessage('');
                                    }}
                                >
                                    Remove
                                </ThemeButton>
                            ) : null}
                        </form>
                        {purchasePromoMessage ? (
                            <div
                                className={`credits-modal-message ${
                                    appliedPurchasePromo ? 'credits-modal-message--ok' : 'credits-modal-message--err'
                                }`}
                            >
                                {purchasePromoMessage}
                            </div>
                        ) : null}
                        <div className="credits-modal-pack-grid">
                            {razorpayCatalog.packs.map((pack, index) => {
                                const isStarter = Number(pack.credits) === 24;
                                const promoPercent = (!isStarter && appliedPurchasePromo)
                                    ? Number(appliedPurchasePromo.percent) || 0
                                    : 0;
                                const promoBonus = promoPercent > 0
                                    ? Math.floor(Number(pack.credits) * promoPercent / 100)
                                    : 0;
                                const displayCredits = promoBonus > 0
                                    ? Number(pack.credits) + promoBonus
                                    : Number(pack.total_credits || pack.credits);
                                return (
                                <button
                                    key={pack.credits}
                                    type="button"
                                    className="credits-modal-pack-card"
                                    onClick={() => handleBuyPack(pack.credits)}
                                    disabled={purchasingCredits !== null}
                                >
                                    <span className="credits-modal-pack-index">{String(index + 1).padStart(2, '0')}</span>
                                    <span className="credits-modal-pack-name">
                                        {pack.name || `${pack.credits} Credits`}
                                        {pack.badge ? (
                                            <span className="credits-modal-pack-badge">{pack.badge}</span>
                                        ) : null}
                                    </span>
                                    <span className="credits-modal-pack-price">{pack.amount_display}</span>
                                    <span className="credits-modal-pack-credits">
                                        {displayCredits} Credits
                                    </span>
                                    {pack.questions != null && promoBonus <= 0 ? (
                                        <span className="credits-modal-pack-questions">
                                            {pack.credits >= 999
                                                ? `${pack.questions} Questions with Tara`
                                                : `${pack.questions} Questions`}
                                        </span>
                                    ) : null}
                                    {promoBonus > 0 ? (
                                        <span className="credits-modal-pack-save">
                                            {pack.credits} + {promoBonus} promo ({promoPercent}%)
                                        </span>
                                    ) : pack.pack_bonus_credits > 0 ? (
                                        <span className="credits-modal-pack-save">
                                            {pack.credits} + {pack.pack_bonus_credits} bonus (5% extra)
                                        </span>
                                    ) : null}
                                    {!promoBonus && pack.credit_campaign ? (
                                        <span className="credits-modal-pack-save">
                                            Special {Number(pack.credit_campaign.multiplier).toLocaleString(undefined, { maximumFractionDigits: 3 })}× offer · ends {new Date(pack.credit_campaign.ends_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                                        </span>
                                    ) : null}
                                    {pack.save_percent > 0 ? (
                                        <span className="credits-modal-pack-save">Save {pack.save_percent}%</span>
                                    ) : null}
                                    {purchasingCredits === pack.credits && (
                                        <span className="credits-modal-pack-busy">Opening…</span>
                                    )}
                                </button>
                                );
                            })}
                        </div>
                        </>
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
            </section>

            <div className="credits-modal-lower-grid">
                <section className="credits-modal-promo" aria-labelledby="credits-promo-heading">
                    <span className="credits-modal-kicker">Have a code?</span>
                    <h3 id="credits-promo-heading" className="credits-modal-section-title">Redeem free credits</h3>
                    <form onSubmit={handleRedeemPromo} className="credits-modal-form-row credits-modal-form-row--inline">
                        <ThemeInput
                            type="text"
                            value={promoCode}
                            onChange={(e) => setPromoCode(e.target.value)}
                            placeholder="Enter promo code"
                            className="credits-modal-input"
                            disabled={promoLoading}
                            autoComplete="off"
                        />
                        <ThemeButton
                            type="submit"
                            disabled={promoLoading || !promoCode.trim()}
                            size="md"
                            className="credits-modal-btn-primary"
                        >
                            {promoLoading ? 'Redeeming…' : 'Redeem'}
                        </ThemeButton>
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
                </section>

                <section className="credits-modal-costs" aria-labelledby="credits-use-heading">
                    <h4 id="credits-use-heading" className="credits-modal-costs-title">Typical credit use</h4>
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
                </section>
            </div>
        </ThemeModal>
    );
};

export default CreditsModal;
