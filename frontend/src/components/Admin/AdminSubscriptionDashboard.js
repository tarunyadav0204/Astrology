import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders, getAdminEndpoint } from '../../services/adminService';
import './AdminSubscriptionDashboard.css';

const API = getAdminEndpoint('/credits/admin/subscriptions');
const formatDate = value => value ? new Date(value).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) : '—';
const label = value => String(value || 'Unknown').replace(/_/g, ' ');

export default function AdminSubscriptionDashboard({ initialView = '' }) {
  const [view, setView] = useState(initialView);
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [provider, setProvider] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState({});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState('');

  useEffect(() => { setView(initialView); setPage(1); }, [initialView]);
  const load = useCallback(async (signal) => {
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams({ query: search, provider, view, page: String(page) });
      const response = await fetch(`${API}${['activity', 'unresolved'].includes(view) ? '/activity' : ''}?${params}`, { headers: getAdminAuthHeaders(), signal });
      if (!response.ok) throw new Error('Could not load subscriptions. Please retry.');
      setData(await response.json());
    } catch (e) {
      if (e.name !== 'AbortError') { setError(e.message); setData({}); }
    } finally { if (!signal?.aborted) setLoading(false); }
  }, [search, provider, view, page]);
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const sync = async row => {
    setSyncing(row.external_id); setError(''); setNotice('');
    try {
      const response = await fetch(`${API}/reconcile`, {
        method: 'POST', headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: row.provider, external_id: row.external_id }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Provider sync failed.');
      setNotice(result.issue || 'Provider status refreshed. No payment or cancellation was requested.');
      await load();
    } catch (e) { setError(e.message); }
    finally { setSyncing(''); }
  };

  const changeView = next => { setView(next); setPage(1); setData({}); };
  return <section className="subscription-dashboard">
    <h2>Subscriptions</h2>
    <p>Billing and membership access, across Razorpay and Google Play. All times are IST.</p>
    {!['activity', 'unresolved'].includes(view) && data.summary && <div className="subscription-metrics">
      {[
        ['subscribers', 'Members with access', ''], ['renewing_soon', 'Renewing in 7 days', 'renewing'],
        ['cancelled', 'Cancelled / not renewing', 'cancelled'], ['payment_issues', 'Payment issues', 'payment'],
        ['needs_attention', 'Needs attention', 'attention'], ['unresolved_events', 'Unresolved events', 'unresolved'],
      ].map(([key, title, next]) => <button key={key} onClick={() => changeView(next)}><strong>{data.summary[key]}</strong>{title}</button>)}
    </div>}
    <div className="subscription-views">
      {['', 'renewing', 'cancelled', 'payment', 'attention', 'activity', 'unresolved'].map(key => <button key={key} aria-pressed={view === key} onClick={() => changeView(key)}>
        {({ '': 'Subscribers', renewing: 'Due soon', cancelled: 'Cancellations', payment: 'Payment issues', attention: 'Needs attention', activity: 'Activity', unresolved: 'Unresolved events' })[key]}
      </button>)}
    </div>
    <form className="subscription-filters" onSubmit={e => { e.preventDefault(); setSearch(query.trim()); setPage(1); }}>
      <input aria-label="Search subscriptions" placeholder="Name, phone, user ID or subscription ID" value={query} onChange={e => setQuery(e.target.value)} />
      {!['activity', 'unresolved'].includes(view) && <select aria-label="Payment provider" value={provider} onChange={e => { setProvider(e.target.value); setPage(1); }}>
        <option value="">All providers</option><option value="razorpay">Razorpay</option><option value="google_play">Google Play</option><option value="unknown">Unlinked memberships</option>
      </select>}
      <button type="submit">Search</button><button type="button" onClick={() => load()} disabled={loading}>Refresh</button>
    </form>
    {error && <p role="alert" className="subscription-error">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    {loading ? <p role="status">Loading subscriptions…</p> : <div className="subscription-table-wrap">
      {['activity', 'unresolved'].includes(view) ? <table><thead><tr><th>Event time</th><th>Subscriber</th><th>Provider / subscription</th><th>Event / source</th><th>Actor</th><th>Processing</th></tr></thead>
        <tbody>{(data.events || []).map((event, i) => <tr key={`${event.external_id}-${i}`}>
          <td>{formatDate(event.occurred_at)}<small>Recorded {formatDate(event.received_at)}</small></td>
          <td>{event.user_name || 'Unmatched'}<small>User {event.userid || 'unknown'}</small></td>
          <td>{label(event.provider)}<small>{event.external_id || 'Unlinked'}</small></td>
          <td>{label(event.kind)}<small>{label(event.source)}</small></td>
          <td>{event.actor === 'unknown' ? 'External / unknown' : `${label(event.actor)}${event.actor_userid ? ` #${event.actor_userid}` : ''}`}</td>
          <td>{label(event.processing_status)}{event.error && <small className="subscription-error">{event.error}</small>}</td>
        </tr>)}</tbody></table> : <table><thead><tr><th>Subscriber / plan</th><th>Provider / subscription</th><th>Started</th><th>Billing</th><th>Next charge</th><th>Access until</th><th>Provider check</th></tr></thead>
        <tbody>{(data.subscriptions || []).map(row => <tr key={`${row.provider}:${row.external_id}`}>
          <td><strong>{row.user_name || 'Unmatched'}</strong><small>#{row.userid} · {row.user_phone}</small><small>{row.tier_name || row.plan_name || 'Unknown plan'}</small></td>
          <td>{label(row.provider)}<small>{row.external_id}</small>{row.provider_order_id && <small>{row.provider_order_id}</small>}</td>
          <td>{formatDate(row.subscribed_at)}</td>
          <td><strong>{label(row.billing_status)}</strong><small>Auto-renew: {row.auto_renew == null ? 'Unknown' : row.auto_renew ? 'On' : 'Off'}</small>{row.cancelled_at && <small>Cancelled {formatDate(row.cancelled_at)}</small>}</td>
          <td>{row.auto_renew === false ? 'No next charge' : row.next_charge_at ? formatDate(row.next_charge_at) : 'Not confirmed'}</td>
          <td>{formatDate(row.access_until)}<small>{row.access_status ? `Membership: ${label(row.access_status)}` : 'Membership link missing'}</small></td>
          <td>{formatDate(row.checked_at)}{row.issue && <small className="subscription-error">{row.issue}</small>}
            {!row.external_id.startsWith('membership_') && <button disabled={!!syncing} onClick={() => sync(row)}>{syncing === row.external_id ? 'Checking…' : 'Check provider'}</button>}
          </td>
        </tr>)}</tbody></table>}
      {!(data.events || data.subscriptions || []).length && !error && <p>No matching records.</p>}
    </div>}
    <div className="subscription-pagination"><button disabled={page === 1 || loading} onClick={() => setPage(page-1)}>Previous</button>
      <span>Page {page}{!['activity', 'unresolved'].includes(view) && data.total != null ? ` · ${data.total} subscriptions` : ''}</span>
      <button disabled={loading || (['activity', 'unresolved'].includes(view) ? !data.has_more : page*50 >= (data.total || 0))} onClick={() => setPage(page+1)}>Next</button>
    </div>
  </section>;
}
