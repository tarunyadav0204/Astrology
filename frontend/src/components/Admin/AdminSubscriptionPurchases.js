import React, { useState, useEffect } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminGooglePlayRefund.css';

/**
 * Admin: list paid subscription plan rows (user_subscriptions) with date range on start_date.
 */
const AdminSubscriptionPurchases = () => {
  const [purchases, setPurchases] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [listLoading, setListLoading] = useState(false);
  const [searchFrom, setSearchFrom] = useState('');
  const [searchTo, setSearchTo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [appliedRange, setAppliedRange] = useState({ from: '', to: '' });

  const limit = 50;

  const loadPurchases = async (fromDate, toDate, q, pageNum = 1) => {
    setListLoading(true);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (q.trim()) params.append('query', q.trim());
      params.append('page', String(pageNum));
      params.append('limit', String(limit));
      const response = await fetch(`/api/credits/admin/subscription-purchases?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to load subscription purchases');
      const data = await response.json();
      setPurchases(data.purchases || []);
      setTotal(typeof data.total === 'number' ? data.total : 0);
      setAppliedRange({
        from: data.from_date || '',
        to: data.to_date || '',
      });
      setPage(pageNum);
    } catch (err) {
      console.error(err);
      setPurchases([]);
      setTotal(0);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadPurchases('', '', '', 1);
  }, []);

  const handleSearch = () => {
    loadPurchases(searchFrom, searchTo, searchQuery, 1);
  };

  const formatTs = (value) => {
    if (!value) return '—';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="admin-google-play-refund">
      <div className="play-refund-list-card">
        <h2>Subscription purchases</h2>
        <p className="play-refund-desc">
          Paid plans only (Google Play product id or list price &gt; 0). Filter matches subscription{' '}
          <strong>start date</strong> (period start). <strong>Recorded</strong> is when the row was saved.
        </p>
        <p className="play-refund-hint">
          Active range:{' '}
          {appliedRange.from && appliedRange.to
            ? `${appliedRange.from} → ${appliedRange.to}`
            : '—'}
          . Leave dates empty to use the default (last 30 days).
        </p>
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
            <span>Name / phone</span>
            <input
              type="text"
              placeholder="Optional…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <button type="button" className="play-refund-search-btn" onClick={handleSearch} disabled={listLoading}>
            {listLoading ? 'Loading…' : 'Search'}
          </button>
        </div>
        {listLoading && purchases.length === 0 ? (
          <div className="play-refund-loading">Loading…</div>
        ) : (
          <>
            <p className="play-refund-hint" style={{ marginTop: 12 }}>
              {total} row{total !== 1 ? 's' : ''} · page {page} of {totalPages}
            </p>
            <div className="play-refund-table-wrap">
              <table className="play-refund-table">
                <thead>
                  <tr>
                    <th>Start (plan)</th>
                    <th>Recorded</th>
                    <th>User ID</th>
                    <th>User</th>
                    <th>Phone</th>
                    <th>Plan</th>
                    <th>Tier</th>
                    <th>Platform</th>
                    <th>Product ID</th>
                    <th>End</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {purchases.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="play-refund-empty">
                        No subscription rows in this period.
                      </td>
                    </tr>
                  ) : (
                    purchases.map((row) => (
                      <tr key={`${row.row_id}-${row.userid}-${row.start_date}`}>
                        <td className="date-cell">{formatTs(row.start_date)}</td>
                        <td className="date-cell">{formatTs(row.recorded_at)}</td>
                        <td>{row.userid != null ? row.userid : '—'}</td>
                        <td>{row.user_name || '—'}</td>
                        <td>{row.user_phone || '—'}</td>
                        <td>{row.plan_name || '—'}</td>
                        <td>{row.tier_name || '—'}</td>
                        <td>{row.platform || '—'}</td>
                        <td className="order-id-cell">{row.google_play_product_id || '—'}</td>
                        <td className="date-cell">{formatTs(row.end_date)}</td>
                        <td>{row.status || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="play-refund-search" style={{ marginTop: 16 }}>
                <button
                  type="button"
                  className="play-refund-search-btn"
                  disabled={page <= 1 || listLoading}
                  onClick={() => loadPurchases(searchFrom, searchTo, searchQuery, page - 1)}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="play-refund-search-btn"
                  disabled={page >= totalPages || listLoading}
                  onClick={() => loadPurchases(searchFrom, searchTo, searchQuery, page + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminSubscriptionPurchases;
