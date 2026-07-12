import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminReportHistory.css';

const AdminReportHistory = () => {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userNameFilter, setUserNameFilter] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [reportType, setReportType] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchRows = async (nextPage, overrides = null) => {
    setLoading(true);
    setError('');
    try {
      const filters = overrides || {
        userName: userNameFilter,
        startDate: startDateFilter,
        endDate: endDateFilter,
        reportType,
        status: statusFilter,
      };
      const params = new URLSearchParams();
      params.set('page', String(nextPage));
      params.set('limit', '50');
      if (filters.reportType && filters.reportType !== 'all') {
        params.set('report_type', filters.reportType);
      }
      if (filters.status && filters.status !== 'all') {
        params.set('status', filters.status);
      }
      if (filters.userName.trim()) params.set('user_name', filters.userName.trim());
      if (filters.startDate) params.set('start_date', filters.startDate);
      if (filters.endDate) params.set('end_date', filters.endDate);

      const response = await fetch(`/api/admin/reports/history?${params.toString()}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch report history (${response.status})`);
      }
      const data = await response.json();
      setItems(data.items || []);
      setPage(Number(data.page || nextPage || 1));
      setTotalPages(Math.max(1, Number(data.total_pages || 1)));
      setTotal(Number(data.total || 0));
    } catch (e) {
      setError(e?.message || 'Failed to load report history');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows(1);
  }, []);

  const formatDate = (v) => {
    if (!v) return '—';
    try {
      return new Date(v).toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata',
      });
    } catch {
      return String(v);
    }
  };

  const formatDuration = (seconds) => {
    if (seconds == null || Number.isNaN(Number(seconds))) return '—';
    const s = Math.max(0, Number(seconds));
    if (s < 60) return `${s}s`;
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}m ${rem}s`;
  };

  const openPdf = (row) => {
    if (!row?.pdf_url) return;
    window.open(row.pdf_url, '_blank', 'noopener,noreferrer');
  };

  const hasUsage = (row) => row?.cost_summary != null || row?.llm_total_tokens != null;

  return (
    <div className="admin-report-history">
      <div className="admin-report-history__header">
        <div>
          <h2>Report generation</h2>
          <p className="admin-report-history__hint">
            Who generated premium reports, credits charged, and estimated AI cost (INR) with cache savings —
            Gemini context-cache discount, chapter DB hits, and full document reopen. Same pricing model as chat /
            event timeline. Older jobs may show empty cost until a new generate runs.
          </p>
        </div>
        <button
          type="button"
          className="admin-report-history__refresh"
          onClick={() => fetchRows(page)}
          disabled={loading}
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      <div className="admin-report-history__filters">
        <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
          <option value="all">All types</option>
          <option value="partnership">Partnership</option>
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="processing">Processing</option>
          <option value="pending">Pending</option>
        </select>
        <input
          type="text"
          value={userNameFilter}
          onChange={(e) => setUserNameFilter(e.target.value)}
          placeholder="Filter by user name"
        />
        <input type="date" value={startDateFilter} onChange={(e) => setStartDateFilter(e.target.value)} />
        <input type="date" value={endDateFilter} onChange={(e) => setEndDateFilter(e.target.value)} />
        <button type="button" onClick={() => fetchRows(1)} disabled={loading}>
          Apply
        </button>
        <button
          type="button"
          onClick={() => {
            setUserNameFilter('');
            setStartDateFilter('');
            setEndDateFilter('');
            setReportType('all');
            setStatusFilter('all');
            fetchRows(1, {
              userName: '',
              startDate: '',
              endDate: '',
              reportType: 'all',
              status: 'all',
            });
          }}
          disabled={loading}
        >
          Clear
        </button>
      </div>

      {error ? <div className="admin-report-history__error">{error}</div> : null}

      <div className="admin-report-history__meta">
        {loading ? 'Loading…' : `${total.toLocaleString()} job${total === 1 ? '' : 's'}`}
      </div>

      <div className="admin-report-history__table-wrap">
        <table className="admin-report-history__table">
          <thead>
            <tr>
              <th>When</th>
              <th>User</th>
              <th>Type</th>
              <th>Subjects</th>
              <th>Language</th>
              <th>Status</th>
              <th>Cached</th>
              <th>Credits</th>
              <th>Model</th>
              <th>In</th>
              <th>Cached In</th>
              <th>NC In</th>
              <th>Cache Setup</th>
              <th>Out</th>
              <th>Cost (INR)</th>
              <th>Saved (INR)</th>
              <th>Duration</th>
              <th>PDF</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {!loading && items.length === 0 ? (
              <tr>
                <td colSpan={19} className="admin-report-history__empty">
                  No report jobs match the current filters.
                </td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.report_id}>
                  <td title={row.report_id}>{formatDate(row.completed_at || row.created_at)}</td>
                  <td>
                    <div>{row.user_name || 'Unknown'}</div>
                    <div className="admin-report-history__sub">
                      {row.user_phone || '—'}
                      {row.userid != null ? ` · #${row.userid}` : ''}
                    </div>
                  </td>
                  <td>{row.report_type || '—'}</td>
                  <td>
                    <div>{row.person_a_name || '—'}</div>
                    <div className="admin-report-history__sub">{row.person_b_name || '—'}</div>
                  </td>
                  <td>{row.language || '—'}</td>
                  <td>
                    <span className={`admin-report-history__status admin-report-history__status--${String(row.status || '').toLowerCase()}`}>
                      {row.status || '—'}
                    </span>
                  </td>
                  <td>
                    {row.cached ? 'Yes' : 'No'}
                    {row.document_cache_hit ? (
                      <div className="admin-report-history__sub">doc reopen</div>
                    ) : null}
                    {row.chapters_from_db_cache ? (
                      <div className="admin-report-history__sub">
                        ch {row.chapters_from_db_cache} cached
                        {row.chapters_generated != null ? ` / ${row.chapters_generated} gen` : ''}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    {row.credits_charged == null ? '—' : Number(row.credits_charged).toLocaleString()}
                  </td>
                  <td className="admin-report-history__model">{row.llm_model || '—'}</td>
                  <td>{hasUsage(row) ? Number(row.llm_input_tokens || 0).toLocaleString() : '—'}</td>
                  <td>{hasUsage(row) ? Number(row.llm_cached_input_tokens || 0).toLocaleString() : '—'}</td>
                  <td>{hasUsage(row) ? Number(row.llm_non_cached_input_tokens || 0).toLocaleString() : '—'}</td>
                  <td>{hasUsage(row) ? Number(row.llm_cache_setup_input_tokens || 0).toLocaleString() : '—'}</td>
                  <td>{hasUsage(row) ? Number(row.llm_output_tokens || 0).toLocaleString() : '—'}</td>
                  <td title={row.cost_summary?.note || ''}>
                    {row.cost_summary ? (
                      <>
                        <div>{Number(row.cost_summary.total_cost_inr_estimate || 0).toFixed(4)}</div>
                        <div className="admin-report-history__sub">
                          NC: {Number(row.cost_summary.input_cost_non_cached_inr_estimate || 0).toFixed(4)}
                        </div>
                        <div className="admin-report-history__sub">
                          C: {Number(row.cost_summary.input_cost_cached_inr_estimate || 0).toFixed(4)}
                        </div>
                        <div className="admin-report-history__sub">
                          Setup: {Number(row.cost_summary.cache_setup_cost_inr_estimate || 0).toFixed(4)}
                        </div>
                        <div className="admin-report-history__sub">
                          Out: {Number(row.cost_summary.output_cost_inr_estimate || 0).toFixed(4)}
                        </div>
                      </>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td title={row.cost_summary?.note || ''}>
                    {row.cost_summary ? (
                      <>
                        <div>{Number(row.cost_summary.cache_savings_inr_estimate || 0).toFixed(4)}</div>
                        <div className="admin-report-history__sub">
                          Gemini: {Number(row.cost_summary.gemini_context_cache_savings_inr_estimate || 0).toFixed(4)}
                        </div>
                        <div className="admin-report-history__sub">
                          Chapter: {Number(row.cost_summary.chapter_db_cache_savings_inr_estimate || 0).toFixed(4)}
                        </div>
                        <div className="admin-report-history__sub">
                          Doc: {Number(row.cost_summary.document_cache_savings_inr_estimate || 0).toFixed(4)}
                        </div>
                      </>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>{formatDuration(row.duration_seconds)}</td>
                  <td>
                    <button
                      type="button"
                      className="admin-report-history__pdf-btn"
                      disabled={!row.has_pdf || !row.pdf_url}
                      title={row.has_pdf ? 'Open signed PDF URL' : 'No PDF'}
                      onClick={() => openPdf(row)}
                    >
                      PDF
                    </button>
                  </td>
                  <td className="admin-report-history__error-cell" title={row.error_message || ''}>
                    {row.error_message || '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="admin-report-history__pager">
        <button type="button" onClick={() => fetchRows(Math.max(1, page - 1))} disabled={loading || page <= 1}>
          Previous
        </button>
        <span>
          Page {page} / {totalPages}
        </span>
        <button
          type="button"
          onClick={() => fetchRows(Math.min(totalPages, page + 1))}
          disabled={loading || page >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default AdminReportHistory;
