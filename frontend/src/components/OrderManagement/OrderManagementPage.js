import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import NavigationHeader from '../Shared/NavigationHeader';
import { authService } from '../../services/authService';
import './OrderManagementPage.css';

const PLAY_SUBSCRIPTIONS_URL = 'https://play.google.com/store/account/subscriptions';

function formatDate(value) {
  if (!value) return 'Not available';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function statusLabel(status) {
  const s = String(status || '').toLowerCase();
  if (s === 'refunded') return 'Refunded';
  if (s === 'partially_refunded') return 'Partially refunded';
  if (s === 'credited') return 'Credited';
  return s ? s.replace(/_/g, ' ') : 'Recorded';
}

function providerLabel(provider) {
  return provider || 'AstroRoshni';
}

function OrderSupportDialog({ order, issueType, onClose, onSubmit, submitting }) {
  const [message, setMessage] = useState('');
  if (!order) return null;

  const issueTitle =
    issueType === 'refund'
      ? 'Request refund'
      : issueType === 'unauthorized'
        ? 'Report unauthorized transaction'
        : 'Get billing help';

  return (
    <div className="order-management-dialog-backdrop" role="presentation">
      <div className="order-management-dialog" role="dialog" aria-modal="true" aria-labelledby="order-support-title">
        <div className="order-management-dialog__header">
          <h2 id="order-support-title">{issueTitle}</h2>
          <button type="button" className="order-management-icon-btn" onClick={onClose} aria-label="Close">
            x
          </button>
        </div>
        <div className="order-management-dialog__order">
          <span>{order.title}</span>
          <strong>{order.support_reference}</strong>
        </div>
        <label htmlFor="order-support-message">Message</label>
        <textarea
          id="order-support-message"
          rows={5}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          maxLength={4000}
          placeholder="Add any context that will help us review this order"
        />
        <div className="order-management-dialog__actions">
          <button type="button" className="order-management-btn order-management-btn--secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="order-management-btn order-management-btn--primary"
            disabled={submitting}
            onClick={() => onSubmit(message)}
          >
            {submitting ? 'Creating ticket...' : 'Create ticket'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function OrderManagementPage({ user, onLogin, onLogout, onAdminClick }) {
  const navigate = useNavigate();
  const isLoggedIn = !!user && !!authService.getToken();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [supportOrder, setSupportOrder] = useState(null);
  const [supportIssue, setSupportIssue] = useState('support');
  const [supportSubmitting, setSupportSubmitting] = useState(false);
  const [notice, setNotice] = useState('');

  const headers = useMemo(() => {
    const token = authService.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, [isLoggedIn]);

  const loadOrders = useCallback(async () => {
    if (!isLoggedIn) {
      setData(null);
      setError('');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/order-management', { headers });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || body.message || 'Could not load orders');
      }
      setData(body);
    } catch (err) {
      setError(err.message || 'Could not load orders');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [headers, isLoggedIn]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const openSupport = (order, issue) => {
    setNotice('');
    setSupportOrder(order);
    setSupportIssue(issue);
  };

  const submitSupport = async (message) => {
    if (!supportOrder) return;
    setSupportSubmitting(true);
    setNotice('');
    try {
      const res = await fetch('/api/order-management/support', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          order_key: supportOrder.order_key,
          issue_type: supportIssue,
          message,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || body.message || 'Could not create support ticket');
      }
      setNotice(`Ticket #${body.ticket_id} created. Our team will review it.`);
      setSupportOrder(null);
    } catch (err) {
      setNotice(err.message || 'Could not create support ticket');
    } finally {
      setSupportSubmitting(false);
    }
  };

  const subscription = data?.subscription || null;
  const orders = data?.orders || [];

  return (
    <div className="order-management-page">
      <Helmet>
        <title>Order Management - AstroRoshni</title>
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
      />

      <main className="order-management-main">
        <header className="order-management-hero">
          <p className="order-management-kicker">Billing center</p>
          <h1>Manage your AstroRoshni orders</h1>
          <p>
            View credit purchases, current membership status, payment references, and billing support
            options for purchases made on AstroRoshni.
          </p>
        </header>

        {!isLoggedIn && (
          <section className="order-management-panel order-management-panel--signin">
            <div>
              <h2>Sign in to view your orders</h2>
              <p>
                For privacy, order history and payment references are shown only after you sign in to
                the AstroRoshni account used for the purchase.
              </p>
            </div>
            <button type="button" className="order-management-btn order-management-btn--primary" onClick={onLogin}>
              Sign in
            </button>
          </section>
        )}

        {isLoggedIn && (
          <>
            <section className="order-management-summary" aria-label="Billing summary">
              <div className="order-management-summary__item">
                <span>Credit balance</span>
                <strong>{loading ? '...' : data?.balance ?? 0}</strong>
              </div>
              <div className="order-management-summary__item">
                <span>Orders</span>
                <strong>{loading ? '...' : orders.length}</strong>
              </div>
              <div className="order-management-summary__item">
                <span>Membership</span>
                <strong>{subscription ? subscription.tier_name : 'None'}</strong>
              </div>
            </section>

            {notice && <div className="order-management-notice">{notice}</div>}
            {error && <div className="order-management-error">{error}</div>}

            {subscription && (
              <section className="order-management-panel">
                <div className="order-management-section-head">
                  <div>
                    <h2>Membership</h2>
                    <p>{subscription.billing_provider === 'google_play' ? 'Managed by Google Play.' : 'Managed on web.'}</p>
                  </div>
                  {subscription.billing_provider === 'google_play' ? (
                    <a
                      className="order-management-btn order-management-btn--secondary"
                      href={PLAY_SUBSCRIPTIONS_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open Play subscriptions
                    </a>
                  ) : (
                    <button
                      type="button"
                      className="order-management-btn order-management-btn--secondary"
                      onClick={() => navigate('/subscription')}
                    >
                      Manage membership
                    </button>
                  )}
                </div>
                <dl className="order-management-details">
                  <div>
                    <dt>Plan</dt>
                    <dd>{subscription.tier_name}</dd>
                  </div>
                  <div>
                    <dt>Discount</dt>
                    <dd>{subscription.discount_percent}% off credit features</dd>
                  </div>
                  <div>
                    <dt>Current period ends</dt>
                    <dd>{formatDate(subscription.end_date)}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{subscription.cancel_at_period_end ? 'Cancels at period end' : 'Active'}</dd>
                  </div>
                </dl>
              </section>
            )}

            <section className="order-management-panel">
              <div className="order-management-section-head">
                <div>
                  <h2>Order history</h2>
                  <p>Credit purchases from web, WhatsApp payment links, and Google Play are listed here.</p>
                </div>
                <button
                  type="button"
                  className="order-management-btn order-management-btn--secondary"
                  onClick={loadOrders}
                  disabled={loading}
                >
                  {loading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>

              {loading && <div className="order-management-empty">Loading orders...</div>}

              {!loading && orders.length === 0 && (
                <div className="order-management-empty">
                  <h3>No orders found</h3>
                  <p>Credit purchases and payment references will appear here after your first order.</p>
                </div>
              )}

              {!loading && orders.length > 0 && (
                <div className="order-management-list">
                  {orders.map((order) => (
                    <article className="order-card" key={order.order_key}>
                      <div className="order-card__main">
                        <div>
                          <span className="order-card__provider">{providerLabel(order.provider)}</span>
                          <h3>{order.title}</h3>
                          <p>{formatDate(order.created_at)}</p>
                        </div>
                        <span className={`order-card__status order-card__status--${order.status}`}>
                          {statusLabel(order.status)}
                        </span>
                      </div>
                      <dl className="order-card__meta">
                        <div>
                          <dt>Amount</dt>
                          <dd>{order.amount_display || 'Not available'}</dd>
                        </div>
                        <div>
                          <dt>Reference</dt>
                          <dd>{order.support_reference || 'Not available'}</dd>
                        </div>
                        <div>
                          <dt>Credits added</dt>
                          <dd>{order.credits_added}</dd>
                        </div>
                        <div>
                          <dt>Balance after</dt>
                          <dd>{order.balance_after}</dd>
                        </div>
                      </dl>
                      <div className="order-card__actions">
                        <button
                          type="button"
                          className="order-management-btn order-management-btn--secondary"
                          onClick={() => openSupport(order, 'support')}
                        >
                          Get help
                        </button>
                        {order.can_request_refund && (
                          <button
                            type="button"
                            className="order-management-btn order-management-btn--secondary"
                            onClick={() => openSupport(order, 'refund')}
                          >
                            Request refund
                          </button>
                        )}
                        <button
                          type="button"
                          className="order-management-btn order-management-btn--link"
                          onClick={() => openSupport(order, 'unauthorized')}
                        >
                          Report unauthorized
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="order-management-help">
              <h2>Need something else?</h2>
              <p>
                For app-store purchases, refunds may need to be completed through Google Play. For web
                payments, our team can review the Razorpay payment reference and credit ledger.
              </p>
              <button
                type="button"
                className="order-management-btn order-management-btn--secondary"
                onClick={() => navigate('/contact')}
              >
                Contact support
              </button>
            </section>
          </>
        )}
      </main>

      <OrderSupportDialog
        order={supportOrder}
        issueType={supportIssue}
        onClose={() => setSupportOrder(null)}
        onSubmit={submitSupport}
        submitting={supportSubmitting}
      />
    </div>
  );
}
