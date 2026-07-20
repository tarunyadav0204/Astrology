import React, { useCallback, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminAudienceBuilder.css';

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      ...getAdminAuthHeaders(),
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return body;
}

function formatDate(value) {
  if (!value) return '—';
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleString();
  } catch (_) {
    return String(value);
  }
}

function formatPurchaseAmount(row) {
  if (row.last_purchase_amount != null && row.last_purchase_amount !== '') {
    const n = Number(row.last_purchase_amount);
    if (Number.isFinite(n)) {
      return n === Math.floor(n) ? `₹${n.toLocaleString()}` : `₹${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    }
  }
  if (row.last_purchase_credits) {
    return `${row.last_purchase_credits} credits`;
  }
  return '—';
}

const EXAMPLE =
  'Users who bought credits in the last 60 days, still have a credit balance, and have not asked a chat question in 14 days.';
const ANALYTICS_EXAMPLE = 'What was the total credit purchase this month?';

function humanizeColumn(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatAnalyticsValue(column, value, row) {
  if (value == null || value === '') return '—';
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  const formatted = number.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (String(column).includes('amount')) {
    return String(row.currency || '').toUpperCase() === 'INR' ? `₹${formatted}` : formatted;
  }
  return formatted;
}

export default function AdminAudienceBuilder({ onCreateCampaign = null }) {
  const [mode, setMode] = useState('audience');
  const [prompt, setPrompt] = useState(EXAMPLE);
  const [explanation, setExplanation] = useState('');
  const [sql, setSql] = useState('');
  const [showSql, setShowSql] = useState(false);
  const [rows, setRows] = useState([]);
  const [allUserIds, setAllUserIds] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [truncated, setTruncated] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [selected, setSelected] = useState(() => new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [analyticsColumns, setAnalyticsColumns] = useState([]);
  const [analyticsRows, setAnalyticsRows] = useState([]);

  const pageIds = useMemo(() => rows.map((r) => Number(r.userid)).filter(Boolean), [rows]);
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));

  const applyResult = useCallback((body, { keepSelection = false } = {}) => {
    setExplanation(body.explanation || '');
    setSql(body.sql || '');
    setRows(Array.isArray(body.rows) ? body.rows : []);
    setAllUserIds(Array.isArray(body.user_ids) ? body.user_ids.map(Number) : []);
    setTotal(Number(body.total) || 0);
    setPage(Number(body.page) || 1);
    setTruncated(Boolean(body.truncated));
    setWarnings(Array.isArray(body.warnings) ? body.warnings : []);
    if (!keepSelection) {
      setSelected(new Set());
    }
  }, []);

  const applyAnalyticsResult = useCallback((body) => {
    setExplanation(body.explanation || '');
    setSql(body.sql || '');
    setAnalyticsColumns(Array.isArray(body.columns) ? body.columns : []);
    setAnalyticsRows(Array.isArray(body.rows) ? body.rows : []);
    setWarnings(Array.isArray(body.warnings) ? body.warnings : []);
  }, []);

  const changeMode = (nextMode) => {
    if (nextMode === mode || busy) return;
    setMode(nextMode);
    setPrompt(nextMode === 'analytics' ? ANALYTICS_EXAMPLE : EXAMPLE);
    setExplanation('');
    setSql('');
    setShowSql(false);
    setWarnings([]);
    setError('');
    setStatus('');
    setRows([]);
    setAllUserIds([]);
    setTotal(0);
    setSelected(new Set());
    setAnalyticsColumns([]);
    setAnalyticsRows([]);
  };

  const runGenerateAndRun = async () => {
    setBusy(true);
    setError('');
    setStatus(mode === 'analytics' ? 'Generating analytics and running query…' : 'Generating audience and running query…');
    try {
      const endpoint =
        mode === 'analytics'
          ? '/api/nudge/admin/analytics-nl/generate-and-run'
          : '/api/nudge/admin/audience-nl/generate-and-run';
      const body = await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(
          mode === 'analytics' ? { prompt } : { prompt, page: 1, page_size: pageSize }
        ),
      });
      if (mode === 'analytics') {
        applyAnalyticsResult(body);
        setStatus(body.row_count ? `Returned ${body.row_count} result row${body.row_count === 1 ? '' : 's'}` : 'No data matched');
      } else {
        applyResult(body);
        setStatus(`Found ${body.total || 0} users`);
      }
      setShowSql(false);
    } catch (err) {
      setError(err.message || 'Failed');
      setStatus('');
    } finally {
      setBusy(false);
    }
  };

  const runExecute = async (nextPage = page) => {
    if (!sql.trim()) {
      setError('Generate or paste SQL first');
      return;
    }
    setBusy(true);
    setError('');
    setStatus('Running query…');
    try {
      const endpoint =
        mode === 'analytics' ? '/api/nudge/admin/analytics-nl/execute' : '/api/nudge/admin/audience-nl/execute';
      const body = await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(
          mode === 'analytics' ? { sql } : { sql, page: nextPage, page_size: pageSize }
        ),
      });
      if (mode === 'analytics') {
        applyAnalyticsResult(body);
        setStatus(body.row_count ? `Returned ${body.row_count} result row${body.row_count === 1 ? '' : 's'}` : 'No data matched');
      } else {
        applyResult(body, { keepSelection: true });
        setPage(nextPage);
        setStatus(`Found ${body.total || 0} users`);
      }
    } catch (err) {
      setError(err.message || 'Failed');
      setStatus('');
    } finally {
      setBusy(false);
    }
  };

  const toggleRow = (userid) => {
    const id = Number(userid);
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const togglePage = () => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allPageSelected) {
        pageIds.forEach((id) => next.delete(id));
      } else {
        pageIds.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  const selectAllMatching = () => {
    setSelected(new Set(allUserIds));
  };

  const clearSelection = () => setSelected(new Set());

  const createCampaign = () => {
    if (typeof onCreateCampaign !== 'function') return;
    const ids = Array.from(selected);
    if (!ids.length) {
      setError('Select at least one user');
      return;
    }
    onCreateCampaign({
      name: 'NL audience campaign',
      title_template: '',
      body_template: '',
      question_template: '',
      landing_screen: 'chat',
      audience_type: 'user_ids',
      audience_user_ids: ids.join(', '),
      audience_nl_prompt: prompt,
      audience_nl_sql: sql,
    });
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  return (
    <div className="audience-builder">
      <div className="audience-builder__header">
        <div>
          <h2>Audience & analytics builder</h2>
          <p className="audience-builder__hint">
            Ask for a campaign audience or a purchase metric in plain English. Queries run only against
            curated admin data.
          </p>
        </div>
      </div>

      <div className="audience-builder__mode-tabs" role="tablist" aria-label="Builder mode">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'audience'}
          className={mode === 'audience' ? 'is-active' : ''}
          onClick={() => changeMode('audience')}
          disabled={busy}
        >
          Audience
          <span>User lists for campaigns</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'analytics'}
          className={mode === 'analytics' ? 'is-active' : ''}
          onClick={() => changeMode('analytics')}
          disabled={busy}
        >
          Analytics
          <span>Totals, counts, and trends</span>
        </button>
      </div>

      <div className="audience-builder__prompt-block">
        <label htmlFor="audience-nl-prompt">
          {mode === 'analytics' ? 'Analytics question' : 'Audience description'}
        </label>
        <textarea
          id="audience-nl-prompt"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={busy}
          placeholder={mode === 'analytics' ? ANALYTICS_EXAMPLE : EXAMPLE}
        />
        <div className="audience-builder__actions">
          <button type="button" className="audience-builder__primary" onClick={runGenerateAndRun} disabled={busy}>
            {busy ? 'Working…' : mode === 'analytics' ? 'Ask & run' : 'Generate & run'}
          </button>
          <button type="button" className="audience-builder__secondary" onClick={() => runExecute(1)} disabled={busy || !sql}>
            Re-run SQL
          </button>
          <button
            type="button"
            className="audience-builder__secondary"
            onClick={() => setShowSql((v) => !v)}
            disabled={!sql}
          >
            {showSql ? 'Hide SQL' : 'Show SQL'}
          </button>
        </div>
      </div>

      {explanation ? (
        <div className="audience-builder__explanation">
          <strong>Interpretation</strong>
          <p>{explanation}</p>
        </div>
      ) : null}

      {showSql ? (
        <div className="audience-builder__sql-block">
          <label htmlFor="audience-nl-sql">SQL (editable)</label>
          <textarea
            id="audience-nl-sql"
            rows={8}
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            disabled={busy}
            spellCheck={false}
          />
        </div>
      ) : null}

      {warnings.length > 0 ? (
        <div className="audience-builder__warnings">
          {warnings.map((w) => (
            <div key={w}>{w}</div>
          ))}
        </div>
      ) : null}

      {error ? <div className="audience-builder__error">{error}</div> : null}
      {status ? <div className="audience-builder__status">{status}</div> : null}

      {truncated ? (
        <div className="audience-builder__warnings">
          Result capped at the server limit. Narrow the description if you need a smaller, more precise set.
        </div>
      ) : null}

      {mode === 'analytics' && analyticsRows.length > 0 ? (
        <div className="audience-builder__analytics-results">
          {analyticsRows.map((row, rowIndex) => (
            <div className="audience-builder__analytics-group" key={`analytics-${rowIndex}`}>
              {analyticsRows.length > 1 ? (
                <div className="audience-builder__analytics-group-title">
                  Result {rowIndex + 1}
                  {row.currency ? ` · ${row.currency}` : ''}
                  {row.provider ? ` · ${humanizeColumn(row.provider)}` : ''}
                </div>
              ) : null}
              <div className="audience-builder__metric-grid">
                {analyticsColumns
                  .filter((column) => !['currency', 'provider'].includes(column))
                  .map((column) => (
                    <div className="audience-builder__metric-card" key={`${rowIndex}-${column}`}>
                      <span>{humanizeColumn(column)}</span>
                      <strong>{formatAnalyticsValue(column, row[column], row)}</strong>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {mode === 'audience' ? (
      <div className="audience-builder__table-toolbar">
        <div>
          <strong>{total}</strong> matching · <strong>{selected.size}</strong> selected
        </div>
        <div className="audience-builder__actions">
          <button type="button" className="audience-builder__secondary" onClick={togglePage} disabled={!rows.length}>
            {allPageSelected ? 'Unselect page' : 'Select page'}
          </button>
          <button
            type="button"
            className="audience-builder__secondary"
            onClick={selectAllMatching}
            disabled={!allUserIds.length}
          >
            Select all matching
          </button>
          <button type="button" className="audience-builder__secondary" onClick={clearSelection} disabled={!selected.size}>
            Clear
          </button>
          <button
            type="button"
            className="audience-builder__primary"
            onClick={createCampaign}
            disabled={!selected.size}
          >
            Create campaign with selected
          </button>
        </div>
      </div>
      ) : null}

      {mode === 'audience' ? (
      <div className="audience-builder__table-wrap">
        <table className="audience-builder__table">
          <thead>
            <tr>
              <th />
              <th>User ID</th>
              <th>Name</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Balance</th>
              <th>Lifetime purchased</th>
              <th>Last purchase</th>
              <th>Last purchase amt</th>
              <th>Last chat</th>
              <th>Days since chat</th>
              <th>Push</th>
              <th>WhatsApp</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={13} className="audience-builder__empty">
                  No rows yet. Generate an audience to preview users.
                </td>
              </tr>
            ) : (
              rows.map((row) => {
                const id = Number(row.userid);
                return (
                  <tr key={id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(id)}
                        onChange={() => toggleRow(id)}
                        aria-label={`Select user ${id}`}
                      />
                    </td>
                    <td>{id}</td>
                    <td>{row.name || '—'}</td>
                    <td>{row.phone || '—'}</td>
                    <td>{row.email || '—'}</td>
                    <td>{row.credits_balance ?? 0}</td>
                    <td>{row.lifetime_purchased_credits ?? 0}</td>
                    <td>{formatDate(row.last_purchase_at)}</td>
                    <td>{formatPurchaseAmount(row)}</td>
                    <td>{formatDate(row.last_user_chat_at)}</td>
                    <td>{row.days_since_last_chat == null ? '—' : row.days_since_last_chat}</td>
                    <td>{row.has_device_token ? 'Yes' : '—'}</td>
                    <td>{row.has_whatsapp ? 'Yes' : '—'}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
      ) : analyticsRows.length === 0 && !busy ? (
        <div className="audience-builder__analytics-empty">
          Ask a purchase question to see totals, counts, or grouped results.
        </div>
      ) : null}

      {mode === 'audience' && total > pageSize ? (
        <div className="audience-builder__pager">
          <button
            type="button"
            className="audience-builder__secondary"
            disabled={busy || page <= 1}
            onClick={() => runExecute(page - 1)}
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            className="audience-builder__secondary"
            disabled={busy || page >= totalPages}
            onClick={() => runExecute(page + 1)}
          >
            Next
          </button>
        </div>
      ) : null}
    </div>
  );
}
