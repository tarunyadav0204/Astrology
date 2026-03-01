import React, { useState, useEffect, useMemo } from 'react';
import './AdminChatPerformance.css';

const DURATION_OPTIONS = [
  { value: 'all', label: 'All durations' },
  { value: '<30s', label: 'Less than 30 sec' },
  { value: '30-60s', label: '30–60 sec' },
  { value: '60-90s', label: '60–90 sec' },
  { value: '90-120s', label: '90–120 sec' },
  { value: '2-3min', label: '2–3 min' },
  { value: '3-4min', label: '3–4 min' },
  { value: '4-5min', label: '4–5 min' },
  { value: '>5min', label: 'Greater than 5 min' },
];

function getPeriodDates(period, customStart, customEnd) {
  const today = new Date();
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, '0');
  const d = String(today.getDate()).padStart(2, '0');
  const todayStr = `${y}-${m}-${d}`;
  if (period === 'today') return { start_date: todayStr, end_date: todayStr };
  if (period === 'custom') {
    if (!customStart || !customEnd) return { start_date: '', end_date: '' };
    return { start_date: customStart, end_date: customEnd };
  }
  const start = new Date(today);
  if (period === 'week') start.setDate(today.getDate() - 6);
  if (period === 'month') start.setDate(1);
  if (period === 'ytd') start.setMonth(0), start.setDate(1);
  const sy = start.getFullYear();
  const sm = String(start.getMonth() + 1).padStart(2, '0');
  const sd = String(start.getDate()).padStart(2, '0');
  const startStr = `${sy}-${sm}-${sd}`;
  return { start_date: startStr, end_date: todayStr };
}

const AdminChatPerformance = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [durationBucket, setDurationBucket] = useState('all');
  const [period, setPeriod] = useState('month');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const { start_date, end_date } = useMemo(
    () => getPeriodDates(period, customStart, customEnd),
    [period, customStart, customEnd]
  );

  useEffect(() => {
    fetchPage();
  }, [page, durationBucket, start_date, end_date]);

  const fetchPage = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
      if (durationBucket && durationBucket !== 'all') params.set('duration_bucket', durationBucket);
      if (start_date && end_date) params.set('start_date', start_date), params.set('end_date', end_date);
      const response = await fetch(
        `/api/admin/chat-performance?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setItems(data.items || []);
      setTotal(data.total ?? 0);
      setTotalPages(data.total_pages ?? 0);
    } catch (error) {
      console.error('Error fetching chat performance:', error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (seconds == null) return '—';
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return s ? `${m}m ${s}s` : `${m}m`;
  };

  const formatIntent = (ms) => {
    if (ms == null) return '—';
    return `${Number(ms).toFixed(0)} ms`;
  };

  const onDurationChange = (e) => {
    setDurationBucket(e.target.value);
    setPage(1);
  };

  const onPeriodChange = (p) => {
    setPeriod(p);
    setPage(1);
  };

  return (
    <div className="chat-performance-container">
      <div className="chat-performance-header">
        <h2>📊 Chat Performance</h2>
        <button onClick={fetchPage} className="refresh-btn" disabled={loading}>
          🔄 Refresh
        </button>
      </div>
      <div className="performance-filters performance-filters-period">
        <span className="filter-label">Period:</span>
        <div className="period-buttons">
          {['today', 'week', 'month', 'ytd', 'custom'].map((p) => (
            <button
              key={p}
              type="button"
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => onPeriodChange(p)}
            >
              {p === 'today' && 'Today'}
              {p === 'week' && 'This week'}
              {p === 'month' && 'This month'}
              {p === 'ytd' && 'YTD'}
              {p === 'custom' && 'Custom'}
            </button>
          ))}
        </div>
        {period === 'custom' && (
          <div className="custom-date-row">
            <label>
              From
              <input
                type="date"
                value={customStart}
                onChange={(e) => { setCustomStart(e.target.value); setPage(1); }}
                className="date-input"
              />
            </label>
            <label>
              To
              <input
                type="date"
                value={customEnd}
                onChange={(e) => { setCustomEnd(e.target.value); setPage(1); }}
                className="date-input"
              />
            </label>
          </div>
        )}
      </div>
      <div className="performance-filters">
        <label htmlFor="duration-filter">Duration:</label>
        <select
          id="duration-filter"
          value={durationBucket}
          onChange={onDurationChange}
          className="duration-select"
        >
          {DURATION_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="loading">Loading…</div>
      ) : items.length === 0 ? (
        <div className="no-data">No assistant messages found.</div>
      ) : (
        <>
          <div className="performance-table-wrap">
            <table className="performance-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>User question</th>
                  <th>Response preview</th>
                  <th>Native</th>
                  <th>Intent (ms)</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.message_id}>
                    <td className="cell-user">
                      <span className="user-name">{row.user_name}</span>
                      {row.user_phone && row.user_phone !== '—' && (
                        <span className="user-phone">{row.user_phone}</span>
                      )}
                    </td>
                    <td className="cell-question" title={row.user_question}>
                      {row.user_question || '—'}
                    </td>
                    <td className="cell-preview" title={row.response_preview}>
                      {row.response_preview || '—'}
                    </td>
                    <td className="cell-native">{row.native_name || '—'}</td>
                    <td className="cell-intent">{formatIntent(row.intent_router_ms)}</td>
                    <td className="cell-duration">{formatDuration(row.duration_seconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Prev
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages} ({total} total)
              </span>
              <button
                className="pagination-btn"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AdminChatPerformance;
