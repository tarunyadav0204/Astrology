import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import NavigationHeader from '../Shared/NavigationHeader';
import SubscriptionPlanCard from './SubscriptionPlanCard';
import CreditsModal from '../Credits/CreditsModal';
import { useCredits } from '../../context/CreditContext';
import { loadRazorpayScript } from '../../utils/razorpayCheckout';
import './SubscriptionPage.css';

const PLAY_SUBSCRIPTIONS_URL = 'https://play.google.com/store/account/subscriptions';

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
}

const SubscriptionPage = ({ user, onLogin, onLogout, onAdminClick }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedPlanId = searchParams.get('plan_id');
  const subscriptionFamily = searchParams.get('family') === 'astrologer' ? 'astrologer' : 'vip';
  const isAstrologerPlan = subscriptionFamily === 'astrologer';

  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [keyId, setKeyId] = useState('');
  const [loading, setLoading] = useState(true);
  const [plansError, setPlansError] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [busyPlanId, setBusyPlanId] = useState(null);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);

  const { credits, loading: creditsLoading } = useCredits();
  const isLoggedIn = !!user && !!localStorage.getItem('token');

  const openCreditsModal = useCallback(() => {
    if (!isLoggedIn) {
      if (typeof onLogin === 'function') onLogin();
      return;
    }
    setShowCreditsModal(true);
  }, [isLoggedIn, onLogin]);

  const authHeaders = useCallback(() => {
    const token = localStorage.getItem('token');
    const h = { 'Content-Type': 'application/json' };
    if (token) h.Authorization = `Bearer ${token}`;
    return h;
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setPlansError('');
    try {
      const plansRes = await fetch('/api/credits/razorpay/subscription/plans');
      const plansData = await plansRes.json().catch(() => ({}));
      if (!plansRes.ok) {
        throw new Error(plansData.detail || 'Could not load subscription plans');
      }
      setPlans((plansData.plans || []).filter(
        (plan) => (plan.subscription_family || 'vip') === subscriptionFamily
      ));
      setKeyId(plansData.key_id || '');

      if (isLoggedIn) {
        const subRes = await fetch(
          `/api/credits/subscription?family=${encodeURIComponent(subscriptionFamily)}`,
          { headers: authHeaders() }
        );
        const subData = await subRes.json().catch(() => ({}));
        if (subRes.ok) {
          setSubscription(subData.subscription || null);
        }
      } else {
        setSubscription(null);
      }
    } catch (err) {
      setPlansError(err.message || 'Failed to load subscription information');
      setPlans([]);
    } finally {
      setLoading(false);
    }
  }, [authHeaders, isLoggedIn, subscriptionFamily]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSubscribe = async (plan) => {
    setActionMessage('');
    if (!isLoggedIn) {
      if (typeof onLogin === 'function') onLogin();
      return;
    }
    setBusyPlanId(plan.plan_id);
    try {
      const createRes = await fetch('/api/credits/razorpay/subscription/create', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ plan_id: plan.plan_id }),
      });
      const createData = await createRes.json().catch(() => ({}));
      if (!createRes.ok) {
        throw new Error(createData.detail || createData.message || 'Could not start subscription');
      }

      const Razorpay = await loadRazorpayScript();
      const options = {
        key: createData.key_id || keyId,
        subscription_id: createData.subscription_id,
        name: 'AstroRoshni',
        description: isAstrologerPlan
          ? `${plan.tier_name} — monthly professional tools`
          : `${plan.tier_name} — monthly VIP`,
        theme: { color: '#e91e63' },
        modal: {
          ondismiss: () => setBusyPlanId(null),
        },
        handler: async (response) => {
          try {
            const verifyRes = await fetch('/api/credits/razorpay/subscription/verify', {
              method: 'POST',
              headers: authHeaders(),
              body: JSON.stringify({
                razorpay_subscription_id: response.razorpay_subscription_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            const verifyData = await verifyRes.json().catch(() => ({}));
            if (!verifyRes.ok) {
              throw new Error(verifyData.detail || 'Verification failed');
            }
            setActionMessage(`Your ${plan.tier_name} membership is active. VIP discounts apply on credits immediately.`);
            await loadData();
            window.dispatchEvent(new CustomEvent('creditUpdated'));
          } catch (err) {
            setActionMessage(
              err.message ||
                'Payment succeeded but activation failed. Contact support with your payment receipt if VIP access is missing.'
            );
          } finally {
            setBusyPlanId(null);
          }
        },
      };
      const rzp = new Razorpay(options);
      rzp.open();
    } catch (err) {
      setActionMessage(err.message || 'Could not open checkout');
      setBusyPlanId(null);
    }
  };

  const handleUpgrade = async (plan) => {
    setActionMessage('');
    if (!window.confirm(`Upgrade to ${plan.tier_name}? You may be charged the prorated difference immediately.`)) {
      return;
    }
    setBusyPlanId(plan.plan_id);
    try {
      const res = await fetch('/api/credits/razorpay/subscription/upgrade', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ plan_id: plan.plan_id }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Upgrade failed');
      }
      setActionMessage(
        data.message || `Upgraded to ${plan.tier_name}. VIP discounts apply on credits immediately.`
      );
      await loadData();
      window.dispatchEvent(new CustomEvent('creditUpdated'));
    } catch (err) {
      setActionMessage(err.message || 'Could not upgrade subscription');
    } finally {
      setBusyPlanId(null);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Cancel your subscription at the end of the current billing period?')) return;
    setCancelLoading(true);
    setActionMessage('');
    try {
      const res = await fetch(
        `/api/credits/razorpay/subscription/cancel?family=${encodeURIComponent(subscriptionFamily)}`,
        {
        method: 'POST',
        headers: authHeaders(),
        }
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Cancel failed');
      }
      setActionMessage(data.message || 'Subscription set to cancel at period end.');
      await loadData();
    } catch (err) {
      setActionMessage(err.message || 'Could not cancel subscription');
    } finally {
      setCancelLoading(false);
    }
  };

  const showRazorpayManage =
    subscription && subscription.billing_provider === 'razorpay';
  const showGooglePlayManage =
    subscription && subscription.billing_provider === 'google_play';
  const showPlans =
    isLoggedIn && !showRazorpayManage && !showGooglePlayManage;
  const upgradePlans =
    !isAstrologerPlan && showRazorpayManage && !subscription.cancel_at_period_end
      ? plans.filter((p) => (p.discount_percent || 0) > (subscription.discount_percent || 0))
      : [];

  return (
    <div className="subscription-page">
      <Helmet>
        <title>{isAstrologerPlan ? 'Astrologer License' : 'VIP Membership'} — AstroRoshni</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      <NavigationHeader
        compact
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={!isLoggedIn}
        onHomeClick={() => navigate('/')}
        onCreditsClick={openCreditsModal}
      />

      <main className="subscription-page-main">
        <header className="subscription-page-hero">
          <h1>{isAstrologerPlan ? 'Astrologer License' : 'VIP membership'}</h1>
          <p>{isAstrologerPlan
            ? 'Unlock professional chart activation, timing and whole-chart manifestation tools for ₹100 per month.'
            : 'VIP lowers what you pay in credits for each feature. Your monthly fee keeps that discount active—you still buy credits separately when you’re ready to use the app.'}
          </p>
        </header>

        <section className="subscription-card subscription-card--info" aria-label="How membership works">
          <h2>{isAstrologerPlan ? 'What the license unlocks' : 'Membership vs credits'}</h2>
          {isAstrologerPlan ? (
            <p>
              This subscription unlocks professional learning and testing tools from the chart screen.
              It is separate from VIP and does not add or consume credits.
            </p>
          ) : (
            <>
              <p>
                A subscription does <strong>not</strong> add credits to your account. It only unlocks
                member pricing on chats, analyses, muhurats, and other paid features.
              </p>
              <p>
                Purchase credits anytime in the app or from your account, then spend them as usual—at the
                lower rates shown on each plan below.
              </p>
            </>
          )}
          <button
            type="button"
            className="subscription-btn subscription-btn--secondary"
            onClick={() => navigate('/order-management')}
          >
            View orders and billing support
          </button>
        </section>

        {!isLoggedIn && (
          <section className="subscription-card subscription-card--notice">
            <h2>Sign in required</h2>
            <p>Sign in to view your plan, subscribe, or cancel a web-billed membership.</p>
            {typeof onLogin === 'function' && (
              <button type="button" className="subscription-btn subscription-btn--primary" onClick={onLogin}>
                Sign in
              </button>
            )}
          </section>
        )}

        {loading && (
          <section
            className="subscription-plans-section subscription-plans-loading"
            aria-busy="true"
            aria-live="polite"
            aria-label="Loading membership plans"
          >
            <div className="subscription-plans-loading__status">
              <div className="subscription-plans-loading__spinner" aria-hidden />
              <p className="subscription-plans-loading__text">Loading membership plans…</p>
            </div>
            <div className="subscription-plans-grid subscription-plans-grid--skeleton">
              {[1, 2, 3].map((n) => (
                <div key={n} className="subscription-plan-skeleton" aria-hidden>
                  <div className="subscription-plan-skeleton__title" />
                  <div className="subscription-plan-skeleton__price" />
                  <div className="subscription-plan-skeleton__rows">
                    <div className="subscription-plan-skeleton__row" />
                    <div className="subscription-plan-skeleton__row" />
                    <div className="subscription-plan-skeleton__row" />
                    <div className="subscription-plan-skeleton__row" />
                    <div className="subscription-plan-skeleton__row" />
                  </div>
                  <div className="subscription-plan-skeleton__cta" />
                </div>
              ))}
            </div>
          </section>
        )}

        {!loading && plansError && (
          <section className="subscription-card subscription-card--error">
            <p>{plansError}</p>
            <p className="subscription-hint">
              If this keeps happening, try again later or contact support.
            </p>
          </section>
        )}

        {!loading && showRazorpayManage && (
          <section className="subscription-card">
            <h2>Your plan</h2>
            <dl className="subscription-details">
              <div>
                <dt>Plan</dt>
                <dd>{subscription.tier_name}</dd>
              </div>
              <div>
                <dt>{isAstrologerPlan ? 'Access' : 'Credit discount'}</dt>
                <dd>{isAstrologerPlan ? 'Professional chart tools' : `${subscription.discount_percent}% off`}</dd>
              </div>
              <div>
                <dt>Current period ends</dt>
                <dd>{formatDate(subscription.end_date)}</dd>
              </div>
              <div>
                <dt>Billing</dt>
                <dd>Web (UPI / card)</dd>
              </div>
              {subscription.cancel_at_period_end && (
                <div>
                  <dt>Status</dt>
                  <dd className="subscription-status-cancel-pending">Cancels at period end</dd>
                </div>
              )}
            </dl>
            {!subscription.cancel_at_period_end && (
              <button
                type="button"
                className="subscription-btn subscription-btn--danger"
                onClick={handleCancel}
                disabled={cancelLoading}
              >
                {cancelLoading ? 'Cancelling…' : 'Cancel subscription'}
              </button>
            )}
            {subscription.cancel_at_period_end && (
              <p className="subscription-hint">
                Your membership stays active until {formatDate(subscription.end_date)}. No further
                charges after that date.
              </p>
            )}
          </section>
        )}

        {!loading && upgradePlans.length > 0 && (
          <section className="subscription-plans-section">
            <h2>Upgrade your plan</h2>
            <p className="subscription-hint">
              Upgrades take effect right away. You may be charged a prorated amount for the rest of this
              billing period. If you pay with UPI, cancel and subscribe again to change tier.
            </p>
            <div className="subscription-plans-grid">
              {upgradePlans.map((plan) => (
                <SubscriptionPlanCard
                  key={plan.plan_id}
                  plan={plan}
                  onAction={handleUpgrade}
                  busy={busyPlanId === plan.plan_id}
                  disabled={busyPlanId !== null && busyPlanId !== plan.plan_id}
                  actionLabel="Upgrade"
                  busyLabel="Upgrading…"
                />
              ))}
            </div>
          </section>
        )}

        {!loading && showGooglePlayManage && (
          <section className="subscription-card">
            <h2>Your plan (Google Play)</h2>
            <dl className="subscription-details">
              <div>
                <dt>Plan</dt>
                <dd>{subscription.tier_name}</dd>
              </div>
              <div>
                <dt>Renews / ends</dt>
                <dd>{formatDate(subscription.end_date)}</dd>
              </div>
            </dl>
            <p className="subscription-hint">
              This subscription was purchased through Google Play. Cancel or change it in the Play Store.
            </p>
            <a
              className="subscription-btn subscription-btn--secondary"
              href={PLAY_SUBSCRIPTIONS_URL}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open Google Play subscriptions
            </a>
          </section>
        )}

        {!loading && showPlans && plans.length > 0 && (
          <section className="subscription-plans-section">
            <h2>Choose a plan</h2>
            <p className="subscription-hint">
              {isAstrologerPlan
                ? '₹100 per month. This license can remain active alongside a VIP membership.'
                : 'Monthly fee for your discount tier. Credit balances are bought separately—not included with membership.'}
            </p>
            <div className="subscription-plans-grid">
              {plans.map((plan) => (
                <SubscriptionPlanCard
                  key={plan.plan_id}
                  plan={plan}
                  onAction={handleSubscribe}
                  busy={busyPlanId === plan.plan_id}
                  disabled={busyPlanId !== null && busyPlanId !== plan.plan_id}
                  highlight={String(preselectedPlanId) === String(plan.plan_id)}
                  actionLabel="Subscribe"
                  busyLabel="Opening checkout…"
                />
              ))}
            </div>
            <p className="subscription-razorpay-badge">
              {isAstrologerPlan
                ? 'Secure checkout · access begins after payment verification'
                : 'Secure checkout · member rates apply when you spend credits you’ve purchased'}
            </p>
          </section>
        )}

        {!loading && showPlans && plans.length === 0 && !plansError && (
          <section className="subscription-card">
            <p>Plans are not available right now. Please try again later.</p>
          </section>
        )}

        {actionMessage && (
          <div
            className={`subscription-message ${
              actionMessage.toLowerCase().includes('fail') || actionMessage.toLowerCase().includes('could not')
                ? 'subscription-message--error'
                : 'subscription-message--ok'
            }`}
          >
            {actionMessage}
          </div>
        )}

        <section className="subscription-credits-card" aria-labelledby="subscription-buy-credits-heading">
          <div className="subscription-credits-card__visual" aria-hidden>
            <span className="subscription-credits-card__icon">💳</span>
          </div>
          <div className="subscription-credits-card__body">
            <h2 id="subscription-buy-credits-heading">Buy credits</h2>
            <p className="subscription-credits-card__lead">
              Membership lowers prices—it does not add credits. Top up your wallet to use chats,
              analyses, and muhurats.
            </p>
            {isLoggedIn && !creditsLoading && (
              <p className="subscription-credits-card__balance">
                Your balance: <strong>{credits}</strong> credits
              </p>
            )}
            <div className="subscription-credits-card__actions">
              {isLoggedIn ? (
                <button
                  type="button"
                  className="subscription-btn subscription-btn--primary subscription-credits-card__cta"
                  onClick={() => setShowCreditsModal(true)}
                >
                  Buy credits
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="subscription-btn subscription-btn--primary subscription-credits-card__cta"
                    onClick={() => typeof onLogin === 'function' && onLogin()}
                  >
                    Sign in to buy credits
                  </button>
                  <p className="subscription-credits-card__signin-hint">
                    Sign in to see packs and pay with UPI or card.
                  </p>
                </>
              )}
            </div>
          </div>
        </section>
      </main>

      <CreditsModal
        isOpen={showCreditsModal}
        onClose={() => setShowCreditsModal(false)}
        onLogin={onLogin}
      />
    </div>
  );
};

export default SubscriptionPage;
