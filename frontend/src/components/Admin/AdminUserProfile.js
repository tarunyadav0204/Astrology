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
              <span>credits {user.credits_balance ?? '—'}</span>
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
              <div className="admin-user-profile-summary-credits">
                <span className="admin-user-profile-summary-credits-label">Credits purchase (earned + refunds)</span>
                <strong>{summary?.credits_received ?? 0}</strong>
                <span className="admin-user-profile-summary-credits-sub">
                  earned {summary?.credits_purchased_earned ?? 0}, refunds {summary?.credits_refunds ?? 0}
                </span>
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
