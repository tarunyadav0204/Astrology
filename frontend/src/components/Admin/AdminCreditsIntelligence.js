import React, { useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders, getAdminEndpoint } from '../../services/adminService';

const SOURCE_LABELS = {
  google_play: 'Google Play',
  razorpay: 'Razorpay',
};

const FEATURE_LABELS = {
  chat_question: 'Chat',
  marriage_analysis: 'Marriage',
  wealth_analysis: 'Wealth',
  health_analysis: 'Health',
  education_analysis: 'Education',
  career_analysis: 'Career',
  progeny_analysis: 'Progeny',
  trading_daily: 'Trading Daily',
  trading_calendar: 'Trading Calendar',
  childbirth_planner: 'Childbirth',
  vehicle_purchase: 'Vehicle Muhurat',
  griha_pravesh: 'Griha Pravesh',
  gold_purchase: 'Gold Purchase',
  business_opening: 'Business Opening',
  event_timeline: 'Event Timeline',
  partnership_analysis: 'Partnership',
  karma_analysis: 'Karma',
  mundane_chat: 'Mundane Chat',
  other: 'Other',
};

function toLocalDateStr(date) {
  const y = date.getFullYear();
  const mo = date.getMonth() + 1;
  const day = date.getDate();
  return `${y}-${String(mo).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function getDateRange(preset) {
  const today = new Date();
  const y = today.getFullYear();
  const m = today.getMonth();
  const d = today.getDate();
  let from;
  let to = new Date(y, m, d);

  switch (preset) {
    case 'past_3_months':
      from = new Date(y, m - 2, 1);
      break;
    case 'this_week': {
      const day = today.getDay();
      const daysSinceMonday = day === 0 ? 6 : day - 1;
      from = new Date(today);
      from.setDate(today.getDate() - daysSinceMonday);
      from.setHours(0, 0, 0, 0);
      break;
    }
    case 'last_week': {
      const day = today.getDay();
      const daysSinceMonday = day === 0 ? 6 : day - 1;
      const thisWeekMonday = new Date(today);
      thisWeekMonday.setDate(today.getDate() - daysSinceMonday);
      thisWeekMonday.setHours(0, 0, 0, 0);
      from = new Date(thisWeekMonday);
      from.setDate(thisWeekMonday.getDate() - 7);
      to = new Date(thisWeekMonday);
      to.setDate(thisWeekMonday.getDate() - 1);
      to.setHours(23, 59, 59, 999);
      break;
    }
    case 'ytd':
      from = new Date(y, 0, 1);
      break;
    default:
      from = new Date(y, m, 1);
  }

  return { from_date: toLocalDateStr(from), to_date: toLocalDateStr(to) };
}

function formatInt(value) {
  return Number(value || 0).toLocaleString('en-IN');
}

function formatDateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    timeZone: 'Asia/Kolkata',
  });
}

const PRESET_LABELS = {
  this_month: 'This month',
  past_3_months: 'Past 3 months',
  this_week: 'This week',
  last_week: 'Last week',
  ytd: 'YTD',
  custom: 'Custom',
};

const CAMPAIGN_SEGMENTS = [
  {
    key: 'active_but_slipping',
    title: 'Active but slipping',
    description: 'Users active before, but quiet in the last 7 days.',
  },
  {
    key: 'recent_payers_no_spend',
    title: 'Paid but did not consume',
    description: 'Bought credits in range, but has not spent them yet.',
  },
  {
    key: 'high_balance_inactive',
    title: 'High balance inactive',
    description: 'Large parked wallet and no recent credit activity.',
  },
  {
    key: 'first_time_payers_no_repeat',
    title: 'First-time payer not repeated',
    description: 'First purchase done, but no second purchase yet.',
  },
];

export default function AdminCreditsIntelligence({ onCreateCampaignFromSegment = null }) {
  const [preset, setPreset] = useState('this_month');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [segmentModal, setSegmentModal] = useState(null);

  useEffect(() => {
    if (preset === 'custom' && !fromDate) {
      const range = getDateRange('this_month');
      setFromDate(range.from_date);
      setToDate(range.to_date);
    }
  }, [preset, fromDate]);

  useEffect(() => {
    const range = preset === 'custom'
      ? { from_date: fromDate, to_date: toDate }
      : getDateRange(preset);
    if (preset === 'custom' && (!range.from_date || !range.to_date)) {
      setLoading(false);
      setData(null);
      return;
    }
    setLoading(true);
    setError('');
    const params = new URLSearchParams(range);
    fetch(`${getAdminEndpoint('/credits/admin/intelligence')}?${params.toString()}`, {
      headers: getAdminAuthHeaders(),
    })
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(body.detail || 'Failed to load credits intelligence');
        setData(body);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load credits intelligence');
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [preset, fromDate, toDate]);

  const summary = data?.summary || {};
  const purchaseSources = data?.purchase_sources || [];
  const spendByFeature = data?.spend_by_feature || [];
  const topPayers = data?.top_payers || [];
  const walletBuckets = data?.wallet_buckets || [];
  const dormantBalances = data?.dormant_balances || [];
  const timeSeries = data?.time_series || [];

  const totals = useMemo(
    () =>
      timeSeries.reduce(
        (acc, row) => {
          acc.googlePlay += Number(row.google_play_credits || 0);
          acc.razorpay += Number(row.razorpay_credits || 0);
          acc.spent += Number(row.spent_credits || 0);
          return acc;
        },
        { googlePlay: 0, razorpay: 0, spent: 0 },
      ),
    [timeSeries],
  );

  const openSegment = async (segmentKey, page = 1) => {
    const range = preset === 'custom'
      ? { from_date: fromDate, to_date: toDate }
      : getDateRange(preset);
    setSegmentModal((prev) => ({
      key: segmentKey,
      title: CAMPAIGN_SEGMENTS.find((s) => s.key === segmentKey)?.title || 'Campaign segment',
      description: CAMPAIGN_SEGMENTS.find((s) => s.key === segmentKey)?.description || '',
      loading: true,
      error: '',
      users: prev?.key === segmentKey ? (prev.users || []) : [],
      page,
      limit: 25,
      total: 0,
    }));
    try {
      const params = new URLSearchParams({
        segment_key: segmentKey,
        from_date: range.from_date,
        to_date: range.to_date,
        page: String(page),
        limit: '25',
      });
      const res = await fetch(`${getAdminEndpoint('/credits/admin/intelligence-segment')}?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || 'Failed to load campaign segment');
      setSegmentModal({
        key: segmentKey,
        title: body.segment_label || CAMPAIGN_SEGMENTS.find((s) => s.key === segmentKey)?.title || 'Campaign segment',
        description: body.description || '',
        loading: false,
        error: '',
        users: body.users || [],
        page: body.page || page,
        limit: body.limit || 25,
        total: body.total || 0,
      });
    } catch (err) {
      setSegmentModal((prev) => ({
        ...(prev || {}),
        key: segmentKey,
        loading: false,
        error: err.message || 'Failed to load campaign segment',
        users: [],
      }));
    }
  };

  const createCampaignFromSegment = () => {
    if (!segmentModal || typeof onCreateCampaignFromSegment !== 'function') return;
    const range = preset === 'custom'
      ? { from_date: fromDate, to_date: toDate }
      : getDateRange(preset);
    onCreateCampaignFromSegment({
      name: `${segmentModal.title} campaign`,
      title_template: '',
      body_template: '',
      question_template: '',
      landing_screen: 'chat',
      audience_type: 'credit_intelligence_segment',
      audience_segment_key: segmentModal.key,
      audience_from_date: range.from_date,
      audience_to_date: range.to_date,
    });
  };

  if (loading && !data) return <div className="credits-dashboard-loading">Loading credits intelligence…</div>;
  if (error) return <div className="credits-dashboard-error">{error}</div>;

  return (
    <div className="credits-intelligence">
      <div className="credits-intelligence__header">
        <div>
          <h2>Credits intelligence</h2>
          <p className="credit-settings-hint">
            Payer mix, wallet exposure, credit sinks, and high-signal user summaries for the selected range.
          </p>
        </div>
        <div className="dashboard-controls credits-intelligence__controls">
          <div className="preset-buttons">
            {Object.keys(PRESET_LABELS).map((key) => (
              <button
                key={key}
                type="button"
                className={`preset-btn ${preset === key ? 'active' : ''}`}
                onClick={() => setPreset(key)}
              >
                {PRESET_LABELS[key]}
              </button>
            ))}
          </div>
          {preset === 'custom' && (
            <div className="custom-dates">
              <label>
                From <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
              </label>
              <label>
                To <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
              </label>
            </div>
          )}
        </div>
      </div>

      <div className="stats-grid credits-intelligence__summary-grid">
        <div className="stat-card">
          <h4>Paid credits bought</h4>
          <p>{formatInt(summary.paid_credits)}</p>
          <span>{formatInt(summary.purchase_count)} purchase rows</span>
        </div>
        <div className="stat-card">
          <h4>Credits spent</h4>
          <p>{formatInt(summary.spent_credits)}</p>
          <span>{formatInt(summary.unique_payers)} payers active in range</span>
        </div>
        <div className="stat-card">
          <h4>Repeat payers</h4>
          <p>{formatInt(summary.repeat_payers)}</p>
          <span>{formatInt(summary.first_time_payers)} first-time payers</span>
        </div>
        <div className="stat-card">
          <h4>Wallet liability</h4>
          <p>{formatInt(summary.current_wallet_credits)}</p>
          <span>{formatInt(summary.users_with_balance)} users hold a balance</span>
        </div>
      </div>

      <div className="credits-intelligence__layout">
        <section className="credits-intelligence__panel">
          <div className="credits-intelligence__panel-header">
            <h3>Purchase mix</h3>
            <span>{formatInt(totals.googlePlay + totals.razorpay)} credits</span>
          </div>
          <div className="credits-intelligence__mini-table">
            {purchaseSources.map((row) => (
              <div key={row.source} className="credits-intelligence__mini-row">
                <div>
                  <strong>{SOURCE_LABELS[row.source] || row.source || 'Unknown'}</strong>
                  <span>{formatInt(row.unique_users)} users</span>
                </div>
                <div>
                  <strong>{formatInt(row.credits)}</strong>
                  <span>{formatInt(row.purchase_count)} purchases</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="credits-intelligence__panel">
          <div className="credits-intelligence__panel-header">
            <h3>Wallet balance buckets</h3>
            <span>Current user wallet state</span>
          </div>
          <div className="credits-intelligence__mini-table">
            {walletBuckets.map((row) => (
              <div key={row.bucket} className="credits-intelligence__mini-row">
                <div>
                  <strong>{row.bucket} credits</strong>
                  <span>{formatInt(row.user_count)} users</span>
                </div>
                <div>
                  <strong>{formatInt(row.total_credits)}</strong>
                  <span>credits parked</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="credits-intelligence__panel">
        <div className="credits-intelligence__panel-header">
          <h3>Top credit sinks</h3>
          <span>Most expensive features in selected range</span>
        </div>
        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Spent credits</th>
                <th>Transactions</th>
                <th>Unique users</th>
                <th>Avg credits / tx</th>
              </tr>
            </thead>
            <tbody>
              {spendByFeature.map((row) => (
                <tr key={row.feature}>
                  <td>{FEATURE_LABELS[row.feature] || row.feature || 'Other'}</td>
                  <td>{formatInt(row.spent_credits)}</td>
                  <td>{formatInt(row.spend_count)}</td>
                  <td>{formatInt(row.unique_users)}</td>
                  <td>{row.avg_credits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="credits-intelligence__panel">
        <div className="credits-intelligence__panel-header">
          <h3>Top payers</h3>
          <span>Highest bought users in selected range</span>
        </div>
        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Purchased</th>
                <th>Spent</th>
                <th>Balance</th>
                <th>Purchase count</th>
                <th>Primary source</th>
                <th>Last purchase</th>
              </tr>
            </thead>
            <tbody>
              {topPayers.map((row) => (
                <tr key={row.userid}>
                  <td>
                    <div className="credits-intelligence__user-cell">
                      <strong>{row.user_name || `User ${row.userid}`}</strong>
                      <span>{row.user_phone || `ID ${row.userid}`}</span>
                    </div>
                  </td>
                  <td>{formatInt(row.purchased_credits)}</td>
                  <td>{formatInt(row.spent_credits)}</td>
                  <td>{formatInt(row.current_balance)}</td>
                  <td>{formatInt(row.purchase_count)}</td>
                  <td>{SOURCE_LABELS[row.primary_source] || row.primary_source || 'Unknown'}</td>
                  <td>{formatDateTime(row.last_purchase_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="credits-intelligence__panel">
        <div className="credits-intelligence__panel-header">
          <h3>Campaign segments</h3>
          <span>Load on demand to keep this page light</span>
        </div>
        <div className="credits-intelligence__segment-grid">
          {CAMPAIGN_SEGMENTS.map((segment) => (
            <button
              key={segment.key}
              type="button"
              className="credits-intelligence__segment-card"
              onClick={() => openSegment(segment.key, 1)}
            >
              <strong>{segment.title}</strong>
              <span>{segment.description}</span>
            </button>
          ))}
        </div>
      </section>

      <div className="credits-intelligence__layout">
        <section className="credits-intelligence__panel">
          <div className="credits-intelligence__panel-header">
            <h3>Recent bought vs spent trend</h3>
            <span>Daily rollup</span>
          </div>
          <div className="credits-intelligence__mini-table">
            {timeSeries.slice(-14).map((row) => (
              <div key={row.date} className="credits-intelligence__mini-row">
                <div>
                  <strong>{row.date}</strong>
                  <span>Spent {formatInt(row.spent_credits)}</span>
                </div>
                <div>
                  <strong>GP {formatInt(row.google_play_credits)}</strong>
                  <span>RZP {formatInt(row.razorpay_credits)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="credits-intelligence__panel">
          <div className="credits-intelligence__panel-header">
            <h3>High balance / no-spend watchlist</h3>
            <span>Users worth reviewing</span>
          </div>
          <div className="credits-intelligence__mini-table">
            {dormantBalances.map((row) => (
              <div key={row.userid} className="credits-intelligence__mini-row">
                <div>
                  <strong>{row.user_name || `User ${row.userid}`}</strong>
                  <span>{row.user_phone || `ID ${row.userid}`}</span>
                </div>
                <div>
                  <strong>{formatInt(row.current_balance)} bal</strong>
                  <span>{formatDateTime(row.last_purchase_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {segmentModal ? (
        <div className="ledger-user-modal-backdrop" onClick={() => setSegmentModal(null)} role="presentation">
          <div className="ledger-user-modal credits-intelligence__segment-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
            <div className="ledger-user-modal-header">
              <h2>{segmentModal.title}</h2>
              <p className="ledger-user-modal-sub">{segmentModal.description}</p>
              <button type="button" className="ledger-user-modal-close" onClick={() => setSegmentModal(null)}>
                Close
              </button>
            </div>
            {segmentModal.loading ? (
              <div className="loading">Loading users…</div>
            ) : segmentModal.error ? (
              <div className="search-error">{segmentModal.error}</div>
            ) : (
              <>
                <div className="form-buttons" style={{ marginBottom: '12px' }}>
                  <button type="button" className="create-btn" onClick={createCampaignFromSegment}>
                    Create campaign from this segment
                  </button>
                </div>
                <div className="admin-table-wrapper">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Purchased</th>
                        <th>Spent</th>
                        <th>Balance</th>
                        <th>Last activity</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {segmentModal.users.length ? segmentModal.users.map((row) => (
                        <tr key={`${segmentModal.key}-${row.userid}`}>
                          <td>
                            <div className="credits-intelligence__user-cell">
                              <strong>{row.user_name || `User ${row.userid}`}</strong>
                              <span>{row.user_phone || `ID ${row.userid}`}</span>
                            </div>
                          </td>
                          <td>{formatInt(row.purchased_credits)}</td>
                          <td>{formatInt(row.spent_credits)}</td>
                          <td>{formatInt(row.current_balance)}</td>
                          <td>{formatDateTime(row.last_activity_at || row.last_purchase_at)}</td>
                          <td>{row.campaign_reason || '—'}</td>
                        </tr>
                      )) : (
                        <tr>
                          <td colSpan={6} className="users-table-empty">No users in this segment for the selected range.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                <div className="users-pagination">
                  <span className="users-pagination-info">
                    Showing {segmentModal.users.length ? ((segmentModal.page - 1) * segmentModal.limit) + 1 : 0}
                    {' '}to {Math.min(segmentModal.page * segmentModal.limit, segmentModal.total)} of {segmentModal.total}
                  </span>
                  <button
                    type="button"
                    className="users-pagination-btn"
                    disabled={segmentModal.page <= 1}
                    onClick={() => openSegment(segmentModal.key, segmentModal.page - 1)}
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    className="users-pagination-btn"
                    disabled={segmentModal.page * segmentModal.limit >= segmentModal.total}
                    onClick={() => openSegment(segmentModal.key, segmentModal.page + 1)}
                  >
                    Next
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
