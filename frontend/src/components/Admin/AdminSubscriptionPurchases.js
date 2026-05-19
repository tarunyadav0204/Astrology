import React, { useState, useEffect } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminGooglePlayRefund.css';

const formatOrderLabel = (orderId, renewalIndex) => {
  if (!orderId) return '—';
  if (renewalIndex == null) return orderId;
  return `${orderId} (#${renewalIndex})`;
};

/**
 * Admin: list paid subscription plan rows (user_subscriptions) with date range on start_date.
 */
const AdminSubscriptionPurchases = () => {
  const [purchases, setPurchases] = useState([]);
  const [groups, setGroups] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalGroups, setTotalGroups] = useState(0);
  const [page, setPage] = useState(1);
  const [listLoading, setListLoading] = useState(false);
  const [searchFrom, setSearchFrom] = useState('');
  const [searchTo, setSearchTo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [groupByOrder, setGroupByOrder] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState({});
  const [appliedRange, setAppliedRange] = useState({ from: '', to: '' });

  const limit = 50;

  const loadPurchases = async (fromDate, toDate, q, pageNum = 1) => {
    setListLoading(true);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (q.trim()) params.append('query', q.trim());
      if (groupByOrder) {
        params.append('grouped', 'true');
        params.append('limit', String(limit));
      } else {
        params.append('page', String(pageNum));
        params.append('limit', String(limit));
      }
      const response = await fetch(`/api/credits/admin/subscription-purchases?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to load subscription purchases');
      const data = await response.json();
      if (data.grouped) {
        setGroups(data.groups || []);
        setPurchases([]);
        setTotalGroups(typeof data.total_groups === 'number' ? data.total_groups : 0);
        setTotal(0);
      } else {
        setPurchases(data.purchases || []);
        setGroups([]);
        setTotal(typeof data.total === 'number' ? data.total : 0);
        setTotalGroups(0);
        setPage(pageNum);
      }
      setAppliedRange({
        from: data.from_date || '',
        to: data.to_date || '',
      });
    } catch (err) {
      console.error(err);
      setPurchases([]);
      setGroups([]);
      setTotal(0);
      setTotalGroups(0);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadPurchases('', '', '', 1);
  }, []);

  const handleSearch = () => {
    setExpandedGroups({});
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

  const toggleGroup = (key) => {
    setExpandedGroups((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const groupKey = (g, idx) =>
    `${g.userid}|${g.google_play_product_id}|${g.order_id_base}|${idx}`;

  const renderPurchaseRow = (row, { nested = false } = {}) => (
    <tr
      key={`${row.row_id}-${row.userid}-${row.start_date}`}
      className={nested ? 'subscription-tree-child' : undefined}
    >
      <td className="date-cell">{formatTs(row.start_date)}</td>
      <td className="date-cell">{formatTs(row.recorded_at)}</td>
      <td>{row.userid != null ? row.userid : '—'}</td>
      <td>{row.user_name || '—'}</td>
      <td>{row.user_phone || '—'}</td>
      <td>{row.plan_name || '—'}</td>
      <td>{row.tier_name || '—'}</td>
      <td className="order-id-cell" title={row.google_play_order_id || ''}>
        {formatOrderLabel(row.google_play_order_id, row.renewal_index)}
      </td>
      <td className="order-id-cell" title={row.order_id_base || ''}>
        {row.order_id_base || '—'}
      </td>
      <td>{row.platform || '—'}</td>
      <td className="order-id-cell">{row.google_play_product_id || '—'}</td>
      <td className="date-cell">{formatTs(row.end_date)}</td>
      <td>{row.status || '—'}</td>
      <td>{row.lifecycle_state || '—'}</td>
      <td className="date-cell">{formatTs(row.cancelled_or_ended_at_estimate)}</td>
    </tr>
  );

  return (
    <div className="admin-google-play-refund">
      <div className="play-refund-list-card">
        <h2>Subscription purchases</h2>
        <p className="play-refund-desc">
          Paid plans only. Filter by subscription <strong>start date</strong>.{' '}
          <strong>Order ID</strong> is from Google Play; renewals share a base GPA id with{' '}
          <code>..N</code> suffixes under the same purchase family.
        </p>
        <p className="play-refund-hint">
          Active range:{' '}
          {appliedRange.from && appliedRange.to
            ? `${appliedRange.from} → ${appliedRange.to}`
            : '—'}
          . Leave dates empty for last 30 days.
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
          <label className="play-refund-checkbox-label">
            <input
              type="checkbox"
              checked={groupByOrder}
              onChange={(e) => setGroupByOrder(e.target.checked)}
            />
            <span>Group by order (tree)</span>
          </label>
          <button type="button" className="play-refund-search-btn" onClick={handleSearch} disabled={listLoading}>
            {listLoading ? 'Loading…' : 'Search'}
          </button>
        </div>
        {listLoading && purchases.length === 0 && groups.length === 0 ? (
          <div className="play-refund-loading">Loading…</div>
        ) : (
          <>
            <p className="play-refund-hint" style={{ marginTop: 12 }}>
              {groupByOrder
                ? `${totalGroups} order group${totalGroups !== 1 ? 's' : ''} (showing up to ${limit})`
                : `${total} row${total !== 1 ? 's' : ''} · page ${page} of ${totalPages}`}
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
                    <th>Order ID</th>
                    <th>Order base</th>
                    <th>Platform</th>
                    <th>Product ID</th>
                    <th>End</th>
                    <th>Status</th>
                    <th>State</th>
                    <th>Cancelled/ended (est.)</th>
                  </tr>
                </thead>
                <tbody>
                  {groupByOrder ? (
                    groups.length === 0 ? (
                      <tr>
                        <td colSpan={15} className="play-refund-empty">
                          No subscription rows in this period.
                        </td>
                      </tr>
                    ) : (
                      groups.map((g, idx) => {
                        const key = groupKey(g, idx);
                        const expanded = expandedGroups[key] !== false;
                        const children = g.purchases || [];
                        return (
                          <React.Fragment key={key}>
                            <tr
                              className="subscription-tree-group"
                              onClick={() => toggleGroup(key)}
                              role="button"
                              tabIndex={0}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') toggleGroup(key);
                              }}
                            >
                              <td colSpan={15}>
                                <span className="subscription-tree-toggle">{expanded ? '▼' : '▶'}</span>
                                <strong>{g.order_id_base || 'Unknown order'}</strong>
                                {' · '}
                                {g.user_name || '—'} ({g.userid}) · {g.plan_name || g.tier_name || '—'} ·{' '}
                                {children.length} period{children.length !== 1 ? 's' : ''}
                              </td>
                            </tr>
                            {expanded
                              ? children.map((row) => renderPurchaseRow(row, { nested: true }))
                              : null}
                          </React.Fragment>
                        );
                      })
                    )
                  ) : purchases.length === 0 ? (
                    <tr>
                      <td colSpan={15} className="play-refund-empty">
                        No subscription rows in this period.
                      </td>
                    </tr>
                  ) : (
                    purchases.map((row) => renderPurchaseRow(row))
                  )}
                </tbody>
              </table>
            </div>
            {!groupByOrder && totalPages > 1 && (
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
