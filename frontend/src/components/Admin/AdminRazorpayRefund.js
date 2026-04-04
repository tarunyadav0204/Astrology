import React, { useState, useEffect } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminGooglePlayRefund.css';

const AdminRazorpayRefund = () => {
  const [transactions, setTransactions] = useState([]);
  const [listLoading, setListLoading] = useState(false);
  const [searchFrom, setSearchFrom] = useState('');
  const [searchTo, setSearchTo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchPaymentId, setSearchPaymentId] = useState('');

  const [refundModal, setRefundModal] = useState({ open: false, tx: null, amount: '', reason: '' });
  const [refundSubmitting, setRefundSubmitting] = useState(false);
  const [refundError, setRefundError] = useState(null);
  const [refundResult, setRefundResult] = useState(null);

  const loadTransactions = async (fromDate = '', toDate = '', query = '', paymentFilter = '') => {
    setListLoading(true);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (query.trim()) params.append('query', query.trim());
      if (paymentFilter.trim()) params.append('payment_id', paymentFilter.trim());
      const response = await fetch(`/api/credits/admin/razorpay-transactions?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to load transactions');
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (err) {
      console.error(err);
      setTransactions([]);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, []);

  const handleSearch = () => {
    loadTransactions(searchFrom, searchTo, searchQuery, searchPaymentId);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const truncateId = (id) => {
    if (!id) return '—';
    if (id.length <= 22) return id;
    return `${id.slice(0, 14)}…${id.slice(-8)}`;
  };

  const formatInr = (tx) => {
    if (tx.amount_paise == null) return '—';
    const rupees = Number(tx.amount_paise) / 100;
    if (!Number.isFinite(rupees)) return '—';
    try {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: tx.currency || 'INR',
        maximumFractionDigits: 2,
      }).format(rupees);
    } catch {
      return `₹${rupees.toFixed(2)}`;
    }
  };

  const openRefundModal = (tx) => {
    if (tx.status !== 'Credited') return;
    setRefundModal({ open: true, tx, amount: String(tx.amount), reason: '' });
    setRefundError(null);
    setRefundResult(null);
  };

  const closeRefundModal = () => {
    setRefundModal({ open: false, tx: null, amount: '', reason: '' });
    setRefundError(null);
    setRefundResult(null);
  };

  const confirmRefundApi = async () => {
    const { tx } = refundModal;
    if (!tx) return;
    const amount = parseInt(refundModal.amount, 10);
    if (!amount || amount < 1 || amount > tx.amount) {
      setRefundError(`Enter a valid amount (1 to ${tx.amount}).`);
      return;
    }
    setRefundSubmitting(true);
    setRefundError(null);
    setRefundResult(null);
    try {
      const response = await fetch('/api/credits/admin/razorpay-refund', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAdminAuthHeaders(),
        },
        body: JSON.stringify({
          userid: tx.userid,
          payment_id: tx.payment_id,
          amount,
          reason: refundModal.reason.trim() || undefined,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setRefundError(data.detail || data.message || 'Refund failed');
        return;
      }
      setRefundResult(data);
      await loadTransactions(searchFrom, searchTo, searchQuery, searchPaymentId);
    } catch (err) {
      setRefundError(err.message || 'Something went wrong.');
    } finally {
      setRefundSubmitting(false);
    }
  };

  const confirmCreditsOnly = async () => {
    const { tx } = refundModal;
    if (!tx) return;
    const amount = parseInt(refundModal.amount, 10);
    if (!amount || amount < 1 || amount > tx.amount) {
      setRefundError(`Enter a valid amount (1 to ${tx.amount}).`);
      return;
    }
    setRefundSubmitting(true);
    setRefundError(null);
    setRefundResult(null);
    try {
      const response = await fetch('/api/credits/admin/reverse-razorpay-purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAdminAuthHeaders(),
        },
        body: JSON.stringify({
          userid: tx.userid,
          payment_id: tx.payment_id,
          amount,
          reason: refundModal.reason.trim() || undefined,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setRefundError(data.detail || data.message || 'Reversal failed');
        return;
      }
      setRefundResult({
        razorpay: '— (manual / dashboard)',
        astroroshni: data.message || 'Credits taken back',
        credits_deducted: data.credits_deducted,
        original_amount: refundModal.tx.amount,
      });
      await loadTransactions(searchFrom, searchTo, searchQuery, searchPaymentId);
    } catch (err) {
      setRefundError(err.message || 'Something went wrong.');
    } finally {
      setRefundSubmitting(false);
    }
  };

  return (
    <div className="admin-google-play-refund">
      <div className="play-refund-list-card">
        <h2>Razorpay credit return</h2>
        <p className="play-refund-desc">
          Web INR purchases (Razorpay). Use <strong>Refund</strong> to call the Razorpay refund API and take back credits in one step, or open the modal and use{' '}
          <strong>Credits only</strong> if you already refunded in the Razorpay Dashboard.
        </p>
        <p className="play-refund-hint">Default: last two years. Filter by date, user, or payment id.</p>
        <div className="play-refund-search">
          <label>
            <span>From</span>
            <input type="date" value={searchFrom} onChange={(e) => setSearchFrom(e.target.value)} />
          </label>
          <label>
            <span>To</span>
            <input type="date" value={searchTo} onChange={(e) => setSearchTo(e.target.value)} />
          </label>
          <label>
            <span>Name / Phone</span>
            <input
              type="text"
              placeholder="Wildcard…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <label>
            <span>Payment ID</span>
            <input
              type="text"
              placeholder="pay_…"
              value={searchPaymentId}
              onChange={(e) => setSearchPaymentId(e.target.value)}
            />
          </label>
          <button type="button" className="play-refund-search-btn" onClick={handleSearch} disabled={listLoading}>
            {listLoading ? 'Loading…' : 'Search'}
          </button>
        </div>
        {listLoading ? (
          <div className="play-refund-loading">Loading transactions…</div>
        ) : (
          <div className="play-refund-table-wrap">
            <table className="play-refund-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>User</th>
                  <th>Phone</th>
                  <th>Payment ID</th>
                  <th>Order ID</th>
                  <th>Credits</th>
                  <th>INR</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="play-refund-empty">
                      No Razorpay web credit transactions in this period.
                    </td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td className="date-cell">{formatDate(tx.created_at)}</td>
                      <td>{tx.user_name}</td>
                      <td>{tx.user_phone}</td>
                      <td className="order-id-cell" title={tx.payment_id}>
                        {truncateId(tx.payment_id)}
                      </td>
                      <td className="token-cell" title={tx.order_id}>
                        {truncateId(tx.order_id)}
                      </td>
                      <td className="amount-cell">+{tx.amount}</td>
                      <td className="amount-cell">{formatInr(tx)}</td>
                      <td>
                        <span className={`status-badge status-${tx.status.toLowerCase()}`}>
                          {tx.status === 'Reversed' && tx.reversed_amount != null && tx.reversed_amount > 0
                            ? tx.reversed_amount < tx.amount
                              ? `Reversed (${tx.reversed_amount}/${tx.amount})`
                              : 'Reversed'
                            : tx.status}
                        </span>
                      </td>
                      <td>
                        {tx.status === 'Credited' ? (
                          <button type="button" className="play-refund-row-btn" onClick={() => openRefundModal(tx)}>
                            Refund
                          </button>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {refundModal.open && refundModal.tx && (
        <div className="play-refund-modal-backdrop" onClick={closeRefundModal}>
          <div className="play-refund-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Refund or take back credits</h3>
            <div className="play-refund-modal-body">
              <p>
                <strong>User:</strong> {refundModal.tx.user_name} · {refundModal.tx.user_phone}
              </p>
              <p>
                <strong>Payment ID:</strong> <code>{refundModal.tx.payment_id}</code>
              </p>
              <p>
                <strong>Order ID:</strong> <code className="token-small">{refundModal.tx.order_id || '—'}</code>
              </p>
              <label>
                <span>Credits to take back</span>
                <input
                  type="number"
                  min={1}
                  max={refundModal.tx.amount}
                  value={refundModal.amount}
                  onChange={(e) => setRefundModal({ ...refundModal, amount: e.target.value })}
                  disabled={refundSubmitting}
                />
                <span className="label-hint">Max {refundModal.tx.amount}</span>
              </label>
              <label>
                <span>Reason</span>
                <textarea
                  placeholder="e.g. Customer request, duplicate charge…"
                  rows={3}
                  value={refundModal.reason}
                  onChange={(e) => setRefundModal({ ...refundModal, reason: e.target.value })}
                  disabled={refundSubmitting}
                />
              </label>
            </div>
            {refundError && <div className="play-refund-error">{refundError}</div>}
            {refundResult && (
              <div className="play-refund-statuses">
                <p className="status-line">
                  <span className="status-label">Razorpay:</span> {refundResult.razorpay}
                </p>
                <p className="status-line">
                  <span className="status-label">AstroRoshni:</span>{' '}
                  {refundResult.credits_deducted != null && refundResult.credits_deducted > 0
                    ? refundResult.original_amount != null &&
                      refundResult.credits_deducted < refundResult.original_amount
                      ? `Partially reversed: ${refundResult.credits_deducted} of ${refundResult.original_amount} credits taken back`
                      : `${refundResult.astroroshni} (${refundResult.credits_deducted} credits)`
                    : refundResult.astroroshni}
                </p>
              </div>
            )}
            <div className="play-refund-modal-actions">
              <button type="button" className="play-refund-cancel" onClick={closeRefundModal} disabled={refundSubmitting}>
                {refundResult ? 'Close' : 'Cancel'}
              </button>
              {!refundResult && (
                <>
                  <button
                    type="button"
                    className="play-refund-cancel"
                    onClick={confirmCreditsOnly}
                    disabled={refundSubmitting}
                  >
                    {refundSubmitting ? '…' : 'Credits only'}
                  </button>
                  <button type="button" className="play-refund-confirm" onClick={confirmRefundApi} disabled={refundSubmitting}>
                    {refundSubmitting ? 'Processing…' : 'Refund (Razorpay API + credits)'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminRazorpayRefund;
