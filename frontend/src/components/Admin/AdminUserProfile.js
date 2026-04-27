import React, { useState, useEffect, useCallback } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminUserProfile.css';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function defaultFromDate() {
  const d = new Date();
  d.setDate(d.getDate() - 90);
  return d.toISOString().slice(0, 10);
}

function formatDuration(ms) {
  const n = Number(ms);
  if (!Number.isFinite(n) || n <= 0) return '—';
  const total = Math.round(n / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString();
}

function formatDateTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return '—';
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

function isLikelyMobileUserAgent(ua) {
  const s = String(ua || '').toLowerCase();
  return (
    s.includes('okhttp') ||
    s.includes('dalvik') ||
    s.includes('android') ||
    s.includes('cfnetwork') ||
    s.includes('expo') ||
    s.includes('reactnative')
  );
}

function inferScreenFromPath(path) {
  const p = String(path || '').toLowerCase();
  if (!p.startsWith('/api/')) return 'Other';
  if (p.includes('/chat')) return 'Chat';
  if (p.includes('/birth-chart') || p.includes('/birth-profile')) return 'Birth Profile';
  if (p.includes('/karma')) return 'Karma Analysis';
  if (p.includes('/event-timeline')) return 'Event Timeline';
  if (p.includes('/trading')) return 'Trading';
  if (p.includes('/credit')) return 'Credits';
  if (p.includes('/podcast') || p.includes('/tts')) return 'Podcast / Audio';
  if (p.includes('/muhurat')) return 'Muhurat';
  if (p.includes('/blog')) return 'Blog';
  if (p.includes('/support')) return 'Support';
  if (p.includes('/auth') || p.includes('/login') || p.includes('/signup')) return 'Auth';
  return 'Other';
}

function inferCtaLabel(method, path) {
  const m = String(method || '').toUpperCase();
  const p = String(path || '').toLowerCase();
  if (p.includes('/chat') && (m === 'POST' || p.includes('/send'))) return 'Send message';
  if (p.includes('/chat') && m === 'GET') return 'Open chat/session';
  if (p.includes('/birth-chart') && m === 'POST') return 'Create/Update chart';
  if (p.includes('/credit') && p.includes('/purchase')) return 'Buy credits';
  if (p.includes('/credit') && m === 'GET') return 'Check credits';
  if (p.includes('/trading') && m === 'GET') return 'View trading insight';
  if (p.includes('/event-timeline') && m === 'POST') return 'Generate timeline';
  if (p.includes('/karma') && m === 'POST') return 'Generate karma analysis';
  if (p.includes('/podcast') || p.includes('/tts')) return 'Podcast action';
  if (p.includes('/support')) return 'Contact support';
  return `${m || 'API'} ${p.split('/').filter(Boolean).slice(-1)[0] || 'request'}`;
}

function buildMobileJourney(activityRows) {
  const rows = Array.isArray(activityRows) ? activityRows : [];
  const apiRows = rows
    .filter((r) => String(r.path || '').startsWith('/api/'))
    .filter((r) => String(r.action || '') === 'api_request' || String(r.action || '') === 'api_error')
    .map((r) => ({ ...r, _t: new Date(r.created_at).getTime() }))
    .filter((r) => Number.isFinite(r._t))
    .sort((a, b) => a._t - b._t);

  if (!apiRows.length) {
    return { steps: [], summary: { totalSteps: 0, totalTimeMs: 0, totalApiCalls: 0, mobileRows: 0 } };
  }

  const mobileRowsCount = apiRows.filter((r) => isLikelyMobileUserAgent(r.user_agent)).length;
  const sourceRows = mobileRowsCount > 0 ? apiRows.filter((r) => isLikelyMobileUserAgent(r.user_agent)) : apiRows;

  const steps = [];
  let current = null;
  sourceRows.forEach((row, idx) => {
    const screen = inferScreenFromPath(row.path);
    const cta = inferCtaLabel(row.method, row.path);
    const startMs = row._t;
    const nextMs = idx < sourceRows.length - 1 ? sourceRows[idx + 1]._t : null;

    if (!current || current.screen !== screen) {
      if (current) {
        current.endMs = startMs;
        current.timeSpentMs = Math.max(0, current.endMs - current.startMs);
        current.ctas = Array.from(current.ctas);
        current.paths = Array.from(current.paths).slice(0, 4);
        steps.push(current);
      }
      current = {
        screen,
        startMs,
        endMs: nextMs || startMs,
        apiCalls: 0,
        apiLatencyMs: 0,
        ctas: new Set(),
        paths: new Set(),
      };
    }

    current.apiCalls += 1;
    current.apiLatencyMs += Number(row.duration_ms) || 0;
    current.ctas.add(cta);
    current.paths.add(row.path || '—');
  });

  if (current) {
    current.timeSpentMs = Math.max(0, (current.endMs || current.startMs) - current.startMs);
    current.ctas = Array.from(current.ctas);
    current.paths = Array.from(current.paths).slice(0, 4);
    steps.push(current);
  }

  const totalTimeMs = steps.reduce((acc, s) => acc + (s.timeSpentMs || 0), 0);
  return {
    steps,
    summary: {
      totalSteps: steps.length,
      totalTimeMs,
      totalApiCalls: sourceRows.length,
      mobileRows: mobileRowsCount,
    },
  };
}

function Section({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="admin-user-profile-section">
      <button
        type="button"
        className="admin-user-profile-section-toggle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="admin-user-profile-chevron">{open ? '▼' : '▶'}</span>
        <h3>{title}</h3>
      </button>
      {open && <div className="admin-user-profile-section-body">{children}</div>}
    </section>
  );
}

export default function AdminUserProfile({ initialUserId, initialDateFrom, initialDateTo }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFrom, setDateFrom] = useState(() =>
    initialDateFrom && initialDateTo ? initialDateFrom : defaultFromDate(),
  );
  const [dateTo, setDateTo] = useState(() =>
    initialDateFrom && initialDateTo ? initialDateTo : todayStr(),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const paramsForRange = useCallback(
    () =>
      new URLSearchParams({
        date_from: dateFrom,
        date_to: dateTo,
      }),
    [dateFrom, dateTo],
  );

  const loadByUserId = useCallback(
    async (rawId) => {
      const id = parseInt(String(rawId).trim(), 10);
      if (!id || Number.isNaN(id)) {
        setError('Invalid user id.');
        setData(null);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/admin/users/${id}/profile?${paramsForRange().toString()}`, {
          headers: getAdminAuthHeaders(),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          const msg =
            typeof body.detail === 'string'
              ? body.detail
              : Array.isArray(body.detail)
                ? body.detail.map((d) => (d && d.msg) || d).join(', ')
                : `Request failed: ${res.status}`;
          throw new Error(msg);
        }
        setData(body);
        if (body.user) {
          const u = body.user;
          const label = [u.name, u.phone].filter(Boolean).join(' · ') || `User ${u.userid}`;
          setSearchQuery(label);
        }
      } catch (e) {
        setError(e.message || 'Failed to load profile');
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [paramsForRange],
  );

  const loadBySearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (!q) {
      setError('Enter a name, email, or phone to search.');
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = paramsForRange();
      params.set('q', q);
      const res = await fetch(`/api/admin/users/profile?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          typeof body.detail === 'string'
            ? body.detail
            : Array.isArray(body.detail)
              ? body.detail.map((d) => d.msg || d).join(', ')
              : `Request failed: ${res.status}`;
        throw new Error(msg);
      }
      if (body.ambiguous && body.matches?.length) {
        setData(body);
        return;
      }
      setData(body);
      if (body.user) {
        const u = body.user;
        const label = [u.name, u.phone].filter(Boolean).join(' · ') || `User ${u.userid}`;
        setSearchQuery(label);
      }
    } catch (e) {
      setError(e.message || 'Failed to load profile');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, paramsForRange]);

  useEffect(() => {
    if (initialUserId == null || String(initialUserId).trim() === '') return;
    const id = parseInt(String(initialUserId).trim(), 10);
    if (!id || Number.isNaN(id)) return;
    loadByUserId(id);
  }, [initialUserId]);

  const summary = data?.summary;
  const user = data?.user;
  const showProfile = data && !data.ambiguous && user;
  const journey = buildMobileJourney(data?.bigquery_activity || []);
  const subscriptionRows = data?.subscriptions || [];

  return (
    <div className="users-management admin-user-profile">
      <h2>User profile</h2>
      <p className="admin-user-profile-lead">
        Search by <strong>display name</strong>, <strong>email</strong>, or <strong>phone</strong> (partial match).
        Date range filters Postgres rows and BigQuery activity; AI insight tables use{' '}
        <code>created_at</code> in range.
      </p>

      <div className="users-management-filters admin-user-profile-filters">
        <label className="admin-user-profile-search-label">
          <span>User (name, email, or phone)</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="e.g. Rahul or +91… or user@email.com"
            autoComplete="off"
          />
        </label>
        <label>
          <span>From</span>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label>
          <span>To</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
        <button type="button" className="users-search-btn" onClick={loadBySearch} disabled={loading}>
          {loading ? 'Loading…' : 'Search'}
        </button>
      </div>

      {error && <div className="admin-user-profile-error">{error}</div>}

      {data?.ambiguous && data.matches?.length > 0 && (
        <div className="admin-user-profile-ambiguous">
          <h3>Multiple users match</h3>
          <p>Choose a user to load the full profile.</p>
          <ul className="admin-user-profile-match-list">
            {data.matches.map((m) => (
              <li key={m.userid}>
                <button
                  type="button"
                  className="admin-user-profile-match-btn"
                  onClick={() => loadByUserId(m.userid)}
                  disabled={loading}
                >
                  <span className="admin-user-profile-match-name">{m.name || '—'}</span>
                  <span className="admin-user-profile-match-meta">
                    {m.phone || '—'} · {m.email || 'no email'} · id {m.userid}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showProfile && (
        <>
          <div className="admin-user-profile-summary">
            <h3>Summary</h3>
            <p className="admin-user-profile-userline">
              <strong>{user.name || '—'}</strong>
              {' · '}
              <span>phone {user.phone || '—'}</span>
              {' · '}
              <span>{user.email || 'no email'}</span>
              {' · '}
              <span>role {user.role || 'user'}</span>
              {' · '}
              <span>
                signup{' '}
                {user.signup_client === 'web'
                  ? 'Web'
                  : user.signup_client === 'mobile'
                    ? 'Mobile app'
                    : '—'}
              </span>
              {' · '}
              <span>credits {user.credits_balance ?? '—'}</span>
              {' · '}
              <span>active subscriptions {summary?.active_subscriptions_count ?? 0}</span>
              {' · '}
              <span>userid {user.userid}</span>
            </p>
            <div className="admin-user-profile-summary-grid">
              <div>Chat questions: <strong>{summary?.chat_questions_count ?? 0}</strong></div>
              <div>BigQuery events: <strong>{summary?.bigquery_activity_count ?? 0}</strong></div>
              <div>Health insights: <strong>{summary?.insights_counts?.health ?? 0}</strong></div>
              <div>Wealth insights: <strong>{summary?.insights_counts?.wealth ?? 0}</strong></div>
              <div>Marriage: <strong>{summary?.insights_counts?.marriage ?? 0}</strong></div>
              <div>Education: <strong>{summary?.insights_counts?.education ?? 0}</strong></div>
              <div>Career: <strong>{summary?.insights_counts?.career ?? 0}</strong></div>
              <div>Karma: <strong>{summary?.karma_insights_count ?? 0}</strong></div>
              <div>Event timeline jobs: <strong>{summary?.event_timeline_jobs_count ?? 0}</strong></div>
              <div>Active subscriptions: <strong>{summary?.active_subscriptions_count ?? 0}</strong></div>
              <div>Subscription rows: <strong>{summary?.subscriptions_count ?? 0}</strong></div>
              <div className="admin-user-profile-summary-credits">
                <span className="admin-user-profile-summary-credits-label">
                  Purchased (Google Play &amp; Razorpay)
                </span>
                <strong>{summary?.credits_purchased ?? 0}</strong>
              </div>
              <div className="admin-user-profile-summary-credits">
                <span className="admin-user-profile-summary-credits-label">
                  Credits back / not from store purchase
                </span>
                <strong>{summary?.credits_non_store_total ?? 0}</strong>
                <span className="admin-user-profile-summary-credits-sub">
                  service refunds {summary?.credits_refunds ?? 0} · admin &amp; approvals{' '}
                  {summary?.credits_admin_grants ?? 0} · promo {summary?.credits_promo ?? 0}
                  {Number(summary?.credits_other_received) > 0 && (
                    <> · other {summary?.credits_other_received}</>
                  )}
                </span>
              </div>
              <div className="admin-user-profile-summary-credits">
                <span className="admin-user-profile-summary-credits-label">Total credits received (in range)</span>
                <strong>{summary?.credits_received_total ?? 0}</strong>
              </div>
              <div className="admin-user-profile-summary-credits">
                <span className="admin-user-profile-summary-credits-label">Credits spent</span>
                <strong>{summary?.credits_spent ?? 0}</strong>
              </div>
              <div>Credit transactions: <strong>{summary?.credit_transactions_count ?? 0}</strong></div>
              <div>Trading daily: <strong>{summary?.trading_daily_count ?? 0}</strong></div>
              <div>Trading monthly: <strong>{summary?.trading_monthly_count ?? 0}</strong></div>
            </div>
          </div>

          <Section title={`Subscriptions (${subscriptionRows.length})`} defaultOpen>
            <p className="admin-user-profile-section-note">
              Shows subscription rows stored in our DB. “Bought / recorded” is when the subscription row was created/recorded in our system; “Access end” is the current entitlement end date. Exact Google Play cancellation time is only available if we store subscription lifecycle events separately.
            </p>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>Platform</th>
                    <th>Plan</th>
                    <th>Tier / discount</th>
                    <th>Status</th>
                    <th>Bought / recorded</th>
                    <th>Start</th>
                    <th>Access end</th>
                    <th>Ended</th>
                    <th>Product</th>
                  </tr>
                </thead>
                <tbody>
                  {subscriptionRows.length === 0 ? (
                    <tr><td colSpan={9}>No subscription rows found.</td></tr>
                  ) : (
                    subscriptionRows.map((sub, idx) => {
                      const discount = Number(sub.discount_percent);
                      const tierLine = [
                        sub.tier_name || null,
                        Number.isFinite(discount) ? `${discount}% off` : null,
                      ].filter(Boolean).join(' · ');
                      return (
                        <tr key={sub.subscription_id || `${sub.platform}-${sub.plan_id}-${idx}`}>
                          <td>{sub.platform || '—'}</td>
                          <td>{sub.plan_name || '—'}</td>
                          <td>{tierLine || '—'}</td>
                          <td>{sub.is_current ? 'active/current' : (sub.status || '—')}</td>
                          <td>{formatDateTime(sub.recorded_at || sub.created_at)}</td>
                          <td>{formatDate(sub.start_date)}</td>
                          <td>{formatDate(sub.end_date)}</td>
                          <td>{formatDate(sub.ended_at)}</td>
                          <td className="mono">{sub.google_play_product_id || '—'}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`Chat questions (${data.chat_questions?.length || 0})`} defaultOpen>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Session</th>
                    <th>Question</th>
                    <th>Category</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.chat_questions || []).length === 0 ? (
                    <tr><td colSpan={4}>No rows in range.</td></tr>
                  ) : (
                    data.chat_questions.map((row) => (
                      <tr key={row.message_id}>
                        <td>{row.timestamp ? new Date(row.timestamp).toLocaleString() : '—'}</td>
                        <td className="mono">{row.session_id || '—'}</td>
                        <td>{row.content || '—'}</td>
                        <td>{row.category || row.canonical_question || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`BigQuery activity (${data.bigquery_activity?.length || 0})`}>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Action</th>
                    <th>Path</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.bigquery_activity || []).length === 0 ? (
                    <tr><td colSpan={4}>No rows (check date range or BigQuery config).</td></tr>
                  ) : (
                    data.bigquery_activity.map((row, i) => (
                      <tr key={row.event_id || i}>
                        <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                        <td>{row.action || '—'}</td>
                        <td className="mono narrow">{row.path || '—'}</td>
                        <td>{row.status_code ?? '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`Mobile journey (${journey.summary.totalSteps || 0} steps)`} defaultOpen>
            <div className="admin-user-profile-journey-summary">
              <div><strong>Journey time:</strong> {formatDuration(journey.summary.totalTimeMs)}</div>
              <div><strong>API calls used:</strong> {journey.summary.totalApiCalls}</div>
              <div>
                <strong>Mobile UA rows:</strong>{' '}
                {journey.summary.mobileRows > 0 ? journey.summary.mobileRows : 'none detected (showing all API rows)'}
              </div>
            </div>
            {journey.steps.length === 0 ? (
              <div className="admin-user-profile-empty">No API activity found to build journey in selected range.</div>
            ) : (
              <div className="admin-user-profile-journey-grid">
                {journey.steps.map((step, idx) => (
                  <article className="admin-user-profile-journey-card" key={`${step.screen}-${step.startMs}-${idx}`}>
                    <div className="admin-user-profile-journey-card-head">
                      <span className="admin-user-profile-journey-step">Step {idx + 1}</span>
                      <h4>{step.screen}</h4>
                    </div>
                    <div className="admin-user-profile-journey-times">
                      <span>{formatTime(step.startMs)}</span>
                      <span>to</span>
                      <span>{formatTime(step.endMs)}</span>
                    </div>
                    <div className="admin-user-profile-journey-metrics">
                      <div><strong>Time spent:</strong> {formatDuration(step.timeSpentMs)}</div>
                      <div><strong>Calls:</strong> {step.apiCalls}</div>
                      <div><strong>Total API latency:</strong> {formatDuration(step.apiLatencyMs)}</div>
                    </div>
                    <div className="admin-user-profile-journey-ctas">
                      {step.ctas.map((cta) => (
                        <span key={`${step.startMs}-${cta}`} className="admin-user-profile-journey-chip">
                          {cta}
                        </span>
                      ))}
                    </div>
                    <details className="admin-user-profile-journey-paths">
                      <summary>Endpoints</summary>
                      <ul>
                        {step.paths.map((p) => (
                          <li key={`${step.startMs}-${p}`}><code>{p}</code></li>
                        ))}
                      </ul>
                    </details>
                  </article>
                ))}
              </div>
            )}
          </Section>

          {['health', 'wealth', 'marriage', 'education', 'career'].map((key) => {
            const rows = data.insights?.[key] || [];
            return (
              <Section key={key} title={`AI ${key} insights (${rows.length})`}>
                <div className="admin-user-profile-table-wrap">
                  <table className="admin-user-profile-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>birth_hash</th>
                        <th>Created</th>
                        <th>Preview</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.length === 0 ? (
                        <tr><td colSpan={4}>No rows in range.</td></tr>
                      ) : (
                        rows.map((row) => (
                          <tr key={row.id}>
                            <td>{row.id}</td>
                            <td className="mono">{row.birth_hash || '—'}</td>
                            <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                            <td className="preview">{row.insights_preview || '—'}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </Section>
            );
          })}

          <Section title={`Karma insights (${data.karma_insights?.length || 0})`}>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>chart</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.karma_insights || []).length === 0 ? (
                    <tr><td colSpan={5}>No rows in range.</td></tr>
                  ) : (
                    data.karma_insights.map((row) => (
                      <tr key={row.id}>
                        <td>{row.id}</td>
                        <td className="mono">{row.chart_id || '—'}</td>
                        <td>{row.status || '—'}</td>
                        <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                        <td className="preview">
                          {(row.ai_interpretation_preview || row.karma_context_preview || '—')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`Event timeline jobs (${data.event_timeline_jobs?.length || 0})`}>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>Job</th>
                    <th>Chart</th>
                    <th>Year</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Result preview</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.event_timeline_jobs || []).length === 0 ? (
                    <tr><td colSpan={6}>No rows in range.</td></tr>
                  ) : (
                    data.event_timeline_jobs.map((row) => (
                      <tr key={row.job_id}>
                        <td className="mono">{row.job_id}</td>
                        <td>{row.birth_chart_id ?? '—'}</td>
                        <td>{row.selected_year ?? '—'}{row.selected_month != null ? ` / ${row.selected_month}` : ''}</td>
                        <td>{row.status || '—'}</td>
                        <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                        <td className="preview">{row.result_preview || row.error_message || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`Credit transactions (${data.credit_transactions?.length || 0})`}>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Balance after</th>
                    <th>Source</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.credit_transactions || []).length === 0 ? (
                    <tr><td colSpan={6}>No rows in range.</td></tr>
                  ) : (
                    data.credit_transactions.map((row) => (
                      <tr key={row.id}>
                        <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                        <td>{row.transaction_type || '—'}</td>
                        <td>{row.amount ?? '—'}</td>
                        <td>{row.balance_after ?? '—'}</td>
                        <td>{row.source || '—'}</td>
                        <td>{row.description || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`Trading daily cache (${data.trading?.daily?.length || 0})`}>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>Created</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.trading?.daily || []).length === 0 ? (
                    <tr><td colSpan={4}>No rows in range.</td></tr>
                  ) : (
                    data.trading.daily.map((row) => (
                      <tr key={row.id}>
                        <td>{row.id}</td>
                        <td>{row.target_date || '—'}</td>
                        <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                        <td className="preview">{row.analysis_preview || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title={`Trading monthly cache (${data.trading?.monthly?.length || 0})`}>
            <div className="admin-user-profile-table-wrap">
              <table className="admin-user-profile-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Year / month</th>
                    <th>Created</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.trading?.monthly || []).length === 0 ? (
                    <tr><td colSpan={4}>No rows in range.</td></tr>
                  ) : (
                    data.trading.monthly.map((row) => (
                      <tr key={row.id}>
                        <td>{row.id}</td>
                        <td>{row.year ?? '—'} / {row.month ?? '—'}</td>
                        <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                        <td className="preview">{row.analysis_preview || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}
