import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminAppPulse.css';

function todayIST() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function number(value) {
  return new Intl.NumberFormat('en-IN').format(Number(value) || 0);
}

function duration(value) {
  if (value === null || value === undefined) return '—';
  const ms = Number(value) || 0;
  return ms >= 1000 ? `${(ms / 1000).toFixed(ms >= 10_000 ? 0 : 1)} sec` : `${ms} ms`;
}

function readablePath(path) {
  const value = String(path || '').replace(/^\/api\//, '').replace(/\?.*$/, '');
  if (value.includes('nakshatra-blueprint')) return 'Nakshatra Blueprint';
  if (value.includes('partner-portrait')) return 'Partner Portrait';
  if (value.includes('instant') || value.includes('chat')) return 'Chat';
  if (value.includes('credit') || value.includes('purchase')) return 'Credits & payments';
  if (value.includes('chart')) return 'Charts';
  return value || 'App activity';
}

function readableScreen(screen) {
  const value = String(screen || '').trim();
  if (/^chart(screen)?$/i.test(value) || value === 'birth_chart') return 'Chart screen';
  if (!value) return 'Unknown screen';
  return value.replace(/([a-z])([A-Z])/g, '$1 $2');
}

function localTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata', hour: 'numeric', minute: '2-digit', hour12: true,
  }).format(date);
}

export default function AdminAppPulse({ onOpenUserProfile }) {
  const [date, setDate] = useState(todayIST);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAllScreens, setShowAllScreens] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/admin/activity/dashboard?date=${encodeURIComponent(date)}`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || 'Could not load App Pulse');
      setData(body);
    } catch (err) {
      setError(err.message || 'Could not load App Pulse');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [date]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const id = window.setInterval(load, 60_000);
    return () => window.clearInterval(id);
  }, [load]);

  const hourly = useMemo(() => {
    const byHour = new Map((data?.chat_hourly || []).map((item) => [item.hour, item]));
    return Array.from({ length: 24 }, (_, hour) => {
      const label = `${String(hour).padStart(2, '0')}:00`;
      return { hour: label, questions: Number(byHour.get(label)?.questions) || 0, answers: Number(byHour.get(label)?.answers) || 0 };
    });
  }, [data]);
  const maxHourly = Math.max(1, ...hourly.map((item) => Math.max(item.questions, item.answers)));
  const summary = data?.summary || {};
  const api = data?.api || {};
  const apiSummary = api.summary || {};
  const errorRate = apiSummary.api_calls ? ((apiSummary.error_count / apiSummary.api_calls) * 100).toFixed(1) : '0.0';
  const chartScreen = (api.screens || []).find((row) => /^chart(screen)?$/i.test(String(row.screen || '')) || row.screen === 'birth_chart');

  return (
    <section className="admin-app-pulse">
      <header className="app-pulse-header">
        <div>
          <p className="app-pulse-kicker">LIVE PRODUCT OVERVIEW</p>
          <h2>App Pulse</h2>
          <p>How AstroRoshni is being used today. All dates and times are in IST.</p>
        </div>
        <div className="app-pulse-actions">
          <label>
            <span>Date</span>
            <input type="date" value={date} max={todayIST()} onChange={(event) => setDate(event.target.value)} />
          </label>
          <button type="button" onClick={load} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button>
        </div>
      </header>

      {data && <p className="app-pulse-updated">Updated {localTime(data.generated_at)}{data.cached ? ' · cached for up to one minute' : ''}</p>}
      {error && <div className="app-pulse-error">{error}</div>}
      {loading && !data && <div className="app-pulse-loading">Loading today’s activity…</div>}

      {data && <>
        <div className="app-pulse-cards">
          <article><span>Active users</span><strong>{number(summary.active_users)}</strong><small>API or chat activity</small></article>
          <article><span>Questions</span><strong>{number(summary.questions)}</strong><small>{number(summary.chat_users)} chat users</small></article>
          <article><span>Answers delivered</span><strong>{number(summary.answers_delivered)}</strong><small>{summary.questions ? `${Math.min(100, Math.round((summary.answers_delivered / summary.questions) * 100))}% of questions` : 'No questions yet'}</small></article>
          <article><span>Paid purchases</span><strong>{number(summary.paid_purchases)}</strong><small>{number(summary.paid_buyers)} buyers · {number(summary.paid_credits)} credits</small></article>
          <article><span>Chart screen</span><strong>{api.available ? number(chartScreen?.users) : '—'}</strong><small>{api.available ? `${number(chartScreen?.opens)} mobile opens` : api.reason}</small></article>
          <article className={Number(apiSummary.error_count) ? 'app-pulse-card-warn' : ''}><span>API errors</span><strong>{api.available ? `${errorRate}%` : '—'}</strong><small>{api.available ? `${number(apiSummary.error_count)} errors · p95 ${duration(apiSummary.p95_duration_ms)}` : api.reason}</small></article>
        </div>

        <div className="app-pulse-grid app-pulse-grid-main">
          <article className="app-pulse-panel app-pulse-chart-panel">
            <div className="app-pulse-panel-heading"><div><h3>Questions through the day</h3><p>Question and completed-answer volume by IST hour</p></div><span className="app-pulse-legend"><i /> Questions <b /> Answers</span></div>
            <div className="app-pulse-bars" role="img" aria-label="Hourly questions and answers">
              {hourly.map((item) => <div className="app-pulse-hour" key={item.hour} title={`${item.hour}: ${item.questions} questions, ${item.answers} answers`}>
                <div className="app-pulse-bar-track"><i style={{ height: `${Math.max(item.questions ? 5 : 0, (item.questions / maxHourly) * 100)}%` }} /><b style={{ height: `${Math.max(item.answers ? 5 : 0, (item.answers / maxHourly) * 100)}%` }} /></div>
                {(item.hour === '00:00' || Number(item.hour.slice(0, 2)) % 4 === 0) && <small>{item.hour.slice(0, 2)}</small>}
              </div>)}
            </div>
          </article>

          <article className="app-pulse-panel">
            <div className="app-pulse-panel-heading"><div><h3>Chat usage</h3><p>Questions by answer mode</p></div></div>
            <div className="app-pulse-list">
              {(data.chat_by_tier || []).length ? data.chat_by_tier.map((item) => <div className="app-pulse-list-row" key={item.name}><span>{String(item.name).replace(/^./, (x) => x.toUpperCase())}</span><strong>{number(item.count)}</strong></div>) : <p className="app-pulse-empty">No chat activity yet.</p>}
            </div>
            <div className="app-pulse-spend"><span>Credits spent</span><strong>{number(summary.credits_spent)}</strong><small>by {number(summary.spending_users)} users</small></div>
            <div className="app-pulse-screen-usage">
              <div className="app-pulse-screen-heading"><strong>Mobile screen usage</strong><small>Native Android and iOS app opens</small></div>
              {(api.screens || []).length ? (api.screens || []).slice(0, showAllScreens ? undefined : 5).map((row) => <div className="app-pulse-list-row" key={`${row.screen}-${row.content_type}`}><span>{readableScreen(row.screen)}</span><strong>{number(row.users)} <small>{number(row.opens)} opens · median {duration(row.median_duration_ms)}</small></strong></div>) : <p className="app-pulse-empty">No mobile screen opens yet.</p>}
              {(api.screens || []).length > 5 && <button type="button" className="app-pulse-show-more" onClick={() => setShowAllScreens((current) => !current)}>{showAllScreens ? 'Show fewer screens' : `Show all ${(api.screens || []).length} screens`}</button>}
            </div>
          </article>
        </div>

        <div className="app-pulse-grid">
          <article className="app-pulse-panel">
            <div className="app-pulse-panel-heading"><div><h3>Paid reports</h3><p>Started, completed, and failed today</p></div></div>
            <div className="app-pulse-table-wrap"><table className="app-pulse-table"><thead><tr><th>Feature</th><th>Users</th><th>Started</th><th>Done</th><th>Failed</th></tr></thead><tbody>
              {(data.reports || []).length ? data.reports.map((row) => <tr key={row.feature}><td>{row.feature}</td><td>{number(row.users)}</td><td>{number(row.started)}</td><td>{number(row.completed)}</td><td className={row.failed ? 'app-pulse-bad' : ''}>{number(row.failed)}</td></tr>) : <tr><td colSpan="5" className="app-pulse-empty">No report activity yet.</td></tr>}
            </tbody></table></div>
          </article>

          <article className="app-pulse-panel">
            <div className="app-pulse-panel-heading"><div><h3>API health</h3><p>{api.available ? `${number(apiSummary.api_calls)} calls today` : 'BigQuery unavailable'}</p></div></div>
            <div className="app-pulse-list">
              {(api.endpoints || []).map((row) => <div className="app-pulse-endpoint" key={row.path}><div><strong>{readablePath(row.path)}</strong><small>{number(row.calls)} calls · p95 {duration(row.p95_duration_ms)}</small></div><em className={Number(row.errors) ? 'app-pulse-bad' : ''}>{Number(row.errors) ? `${number(row.errors)} errors` : 'Healthy'}</em></div>)}
              {!api.available && <p className="app-pulse-empty">{api.reason}</p>}
            </div>
          </article>
        </div>

        <div className="app-pulse-grid">
          <article className="app-pulse-panel">
            <div className="app-pulse-panel-heading"><div><h3>Needs attention</h3><p>Users with failed delivered answers today</p></div></div>
            <div className="app-pulse-list">
              {(data.attention || []).length ? data.attention.map((row) => <button type="button" className="app-pulse-user" key={row.user_id} onClick={() => onOpenUserProfile?.(row.user_id)}><span><strong>{row.name}</strong><small>#{row.user_id} · {number(row.questions)} questions · last active {localTime(row.last_activity)}</small></span><em>{number(row.failed_answers)} failed</em></button>) : <p className="app-pulse-empty">No failed chat answers today.</p>}
            </div>
          </article>
          <article className="app-pulse-panel">
            <div className="app-pulse-panel-heading"><div><h3>Live API activity</h3><p>Most recent server activity; technical detail remains in Activity</p></div></div>
            <div className="app-pulse-list app-pulse-live-list">
              {(api.recent || []).slice(0, 10).map((row, index) => <div className="app-pulse-live" key={`${row.created_at}-${index}`}><span><strong>{row.user_name || (row.user_id ? `User #${row.user_id}` : 'Anonymous')}</strong> · {readablePath(row.path)}</span><small>{localTime(row.created_at)} · {row.status_code || '—'} · {duration(row.duration_ms)}</small></div>)}
              {api.available && !(api.recent || []).length && <p className="app-pulse-empty">No API activity yet.</p>}
            </div>
          </article>
        </div>
      </>}
    </section>
  );
}
