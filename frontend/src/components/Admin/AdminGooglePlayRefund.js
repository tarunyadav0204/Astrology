import React, { useState, useEffect } from 'react';
import './AdminGooglePlayRefund.css';

const AdminGooglePlayRefund = () => {
  const [transactions, setTransactions] = useState([]);
  const [listLoading, setListLoading] = useState(false);
  const [searchFrom, setSearchFrom] = useState('');
  const [searchTo, setSearchTo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOrderId, setSearchOrderId] = useState('');

  const [refundModal, setRefundModal] = useState({ open: false, tx: null, amount: '' });
  const [refundSubmitting, setRefundSubmitting] = useState(false);
  const [refundError, setRefundError] = useState(null);
  const [refundResult, setRefundResult] = useState(null);

  const loadTransactions = async (fromDate = '', toDate = '', query = '', orderIdFilter = '') => {
    setListLoading(true);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (query.trim()) params.append('query', query.trim());
      if (orderIdFilter.trim()) params.append('order_id', orderIdFilter.trim());
      const response = await fetch(`/api/credits/admin/google-play-transactions?${params.toString()}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
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
    loadTransactions(searchFrom, searchTo, searchQuery, searchOrderId);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const truncateToken = (token) => {
    if (!token) return '—';
    if (token.length <= 20) return token;
    return `${token.slice(0, 12)}…${token.slice(-8)}`;
  };

  const openRefundModal = (tx) => {
    if (tx.status !== 'Credited') return;
    setRefundModal({ open: true, tx, amount: String(tx.amount) });
    setRefundError(null);
    setRefundResult(null);
  };

  const closeRefundModal = () => {
    setRefundModal({ open: false, tx: null, amount: '' });
    setRefundError(null);
    setRefundResult(null);
  };

  const confirmRefund = async () => {
    const { tx } = refundModal;
    if (!tx) return;
    const amount = parseInt(refundModal.amount, 10);
    if (!amount || amount < 1 || amount > tx.amount) {
      setRefundError('Enter a valid amount (1 to ' + tx.amount + ').');
      return;
    }
    setRefundSubmitting(true);
    setRefundError(null);
    setRefundResult(null);
    try {
      const response = await fetch('/api/credits/admin/google-play-refund', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          userid: tx.userid,
          order_id: tx.order_id,
          amount,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setRefundError(data.detail || data.message || 'Refund failed');
        return;
      }
      setRefundResult(data);
      await loadTransactions(searchFrom, searchTo, searchQuery, searchOrderId);
    } catch (err) {
      setRefundError(err.message || 'Something went wrong.');
    } finally {
      setRefundSubmitting(false);
    }
  };

  return (
    <div className="admin-google-play-refund">
      <div className="play-refund-list-card">
        <h2>Google Play refund</h2>
        <p className="play-refund-desc">
          Click <strong>Refund</strong> on a transaction to refund the payment on Google Play and take back credits in one step. Idempotent and safe to retry.
        </p>
        <p className="play-refund-hint">Default: last 30 days. Use filters and Search to narrow.</p>
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
            <span>Order ID</span>
            <input
              type="text"
              placeholder="Filter by order ID…"
              value={searchOrderId}
              onChange={(e) => setSearchOrderId(e.target.value)}
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
                  <th>Order ID</th>
                  <th>Purchase token</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="play-refund-empty">No Google Play transactions in this period.</td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td className="date-cell">{formatDate(tx.created_at)}</td>
                      <td>{tx.user_name}</td>
                      <td>{tx.user_phone}</td>
                      <td className="order-id-cell">{tx.order_id || '—'}</td>
                      <td className="token-cell" title={tx.purchase_token}>{truncateToken(tx.purchase_token)}</td>
                      <td className="amount-cell">+{tx.amount}</td>
                      <td>
                        <span className={`status-badge status-${tx.status.toLowerCase()}`}>{tx.status}</span>
                      </td>
                      <td>
                        {tx.status === 'Credited' ? (
                          <button
                            type="button"
                            className="play-refund-row-btn"
                            onClick={() => openRefundModal(tx)}
                          >
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
            <h3>Refund this purchase</h3>
            <div className="play-refund-modal-body">
              <p><strong>User:</strong> {refundModal.tx.user_name} · {refundModal.tx.user_phone}</p>
              <p><strong>Order ID:</strong> <code>{refundModal.tx.order_id}</code></p>
              <p><strong>Purchase token:</strong> <code className="token-small">{refundModal.tx.purchase_token || '—'}</code></p>
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
                <span className="label-hint">Max {refundModal.tx.amount} (full refund)</span>
              </label>
            </div>
            {refundError && <div className="play-refund-error">{refundError}</div>}
            {refundResult && (
              <div className="play-refund-statuses">
                <p className="status-line"><span className="status-label">Google Play:</span> {refundResult.google_play}</p>
                <p className="status-line"><span className="status-label">AstroRoshni:</span> {refundResult.astroroshni}{refundResult.credits_deducted != null && refundResult.credits_deducted > 0 ? ` (${refundResult.credits_deducted} credits)` : ''}</p>
              </div>
            )}
            <div className="play-refund-modal-actions">
              <button type="button" className="play-refund-cancel" onClick={closeRefundModal} disabled={refundSubmitting}>
                {refundResult ? 'Close' : 'Cancel'}
              </button>
              {!refundResult && (
                <button type="button" className="play-refund-confirm" onClick={confirmRefund} disabled={refundSubmitting}>
                  {refundSubmitting ? 'Refunding…' : 'Refund (Google Play + take back credits)'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminGooglePlayRefund;
