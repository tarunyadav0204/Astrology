import React, { useState, useEffect } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminGooglePlayRefund.css';

/**
 * Admin: Play subscription lifecycle events (RTDN + verify/sync), including renewals.
 */
const AdminSubscriptionEvents = () => {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [listLoading, setListLoading] = useState(false);
  const [searchFrom, setSearchFrom] = useState('');
  const [searchTo, setSearchTo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [eventKind, setEventKind] = useState('');
  const [source, setSource] = useState('');
  const [renewalsOnly, setRenewalsOnly] = useState(false);
  const [appliedRange, setAppliedRange] = useState({ from: '', to: '' });

  const limit = 50;

  const loadEvents = async (fromDate, toDate, q, pageNum = 1) => {
    setListLoading(true);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (q.trim()) params.append('query', q.trim());
      if (eventKind) params.append('event_kind', eventKind);
      if (source) params.append('source', source);
      if (renewalsOnly) params.append('renewals_only', 'true');
      params.append('page', String(pageNum));
      params.append('limit', String(limit));
      const response = await fetch(`/api/credits/admin/subscription-events?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to load subscription events');
      const data = await response.json();
      setEvents(data.events || []);
      setTotal(typeof data.total === 'number' ? data.total : 0);
      setAppliedRange({ from: data.from_date || '', to: data.to_date || '' });
      setPage(pageNum);
    } catch (err) {
      console.error(err);
      setEvents([]);
      setTotal(0);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadEvents('', '', '', 1);
  }, []);

  const handleSearch = () => {
    loadEvents(searchFrom, searchTo, searchQuery, 1);
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
        <h2>Subscription events (renewals &amp; purchases)</h2>
        <p className="play-refund-desc">
          Google Play subscription lifecycle from <strong>RTDN (Pub/Sub)</strong> and in-app{' '}
          <strong>verify / sync</strong>. Filter by <strong>when we recorded the event</strong>{' '}
          (<code>processed_at</code>), not subscription start date. Empty until RTDN is wired or users
          verify/sync in the app after deploy.
        </p>
        <p className="play-refund-hint">
          <strong>Renewed</strong> = RTDN type 2 or app detected a longer <code>end_date</code>.{' '}
          <strong>Purchased</strong> = first paid period on that platform. Use &quot;Subscription
          purchases&quot; for entitlement rows (start-date filter). Historical rows: run server
          backfill once (see below).
        </p>
        <p className="play-refund-hint">
          <strong>Backfill past events:</strong> on the server,{' '}
          <code>cd backend &amp;&amp; python3 -m credits.backfill_subscription_events</code> (preview), then{' '}
          <code>--apply</code>. Or POST{' '}
          <code>/api/credits/admin/subscription-events/backfill?dry_run=false</code> as admin. Source
          will show <strong>backfill</strong>; dates use each subscription row&apos;s <code>created_at</code>.
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
            <span>Name / phone / user id</span>
            <input
              type="text"
              placeholder="Optional…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <label>
            <span>Event</span>
            <select value={eventKind} onChange={(e) => setEventKind(e.target.value)}>
              <option value="">All events</option>
              <option value="renewed">Renewed</option>
              <option value="purchased">Purchased</option>
              <option value="upgraded">Upgraded</option>
              <option value="synced">Synced (no change)</option>
              <option value="updated">Updated</option>
              <option value="canceled">Canceled</option>
              <option value="expired">Expired</option>
            </select>
          </label>
          <label>
            <span>Source</span>
            <select value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="">All sources</option>
              <option value="rtdn">RTDN (Google)</option>
              <option value="verify">Verify (purchase)</option>
              <option value="sync">Sync (app open)</option>
              <option value="backfill">Backfill (history)</option>
            </select>
          </label>
          <label className="play-refund-checkbox-label">
            <input
              type="checkbox"
              checked={renewalsOnly}
              onChange={(e) => setRenewalsOnly(e.target.checked)}
            />
            <span>Renewals only</span>
          </label>
          <button type="button" className="play-refund-search-btn" onClick={handleSearch} disabled={listLoading}>
            {listLoading ? 'Loading…' : 'Search'}
          </button>
        </div>
        {listLoading && events.length === 0 ? (
          <div className="play-refund-loading">Loading…</div>
        ) : (
          <>
            <p className="play-refund-hint" style={{ marginTop: 12 }}>
              {total} event{total !== 1 ? 's' : ''} · page {page} of {totalPages}
            </p>
            <div className="play-refund-table-wrap">
              <table className="play-refund-table">
                <thead>
                  <tr>
                    <th>Recorded</th>
                    <th>Event</th>
                    <th>Source</th>
                    <th>User ID</th>
                    <th>User</th>
                    <th>Phone</th>
                    <th>Product</th>
                    <th>Period start</th>
                    <th>Period end</th>
                    <th>RTDN type</th>
                  </tr>
                </thead>
                <tbody>
                  {events.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="play-refund-empty">
                        No events in this period. New verify/sync and RTDN events will appear here after deploy.
                      </td>
                    </tr>
                  ) : (
                    events.map((row) => (
                      <tr
                        key={row.id || row.event_id}
                        className={row.is_renewal ? 'subscription-event-row--renewal' : undefined}
                      >
                        <td className="date-cell">{formatTs(row.processed_at)}</td>
                        <td>
                          <strong>{row.event_label || row.event_kind || '—'}</strong>
                          {row.is_renewal ? (
                            <span className="subscription-event-badge"> renewal</span>
                          ) : null}
                        </td>
                        <td>{row.source || '—'}</td>
                        <td>{row.userid != null ? row.userid : '—'}</td>
                        <td>{row.user_name || '—'}</td>
                        <td>{row.user_phone || '—'}</td>
                        <td className="order-id-cell">{row.product_id || '—'}</td>
                        <td className="date-cell">{row.start_date || '—'}</td>
                        <td className="date-cell">{row.end_date || '—'}</td>
                        <td>{row.notification_type != null ? row.notification_type : '—'}</td>
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
                  onClick={() => loadEvents(searchFrom, searchTo, searchQuery, page - 1)}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="play-refund-search-btn"
                  disabled={page >= totalPages || listLoading}
                  onClick={() => loadEvents(searchFrom, searchTo, searchQuery, page + 1)}
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

export default AdminSubscriptionEvents;
