import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import { downloadEventTimelinePdf } from '../../utils/eventTimelinePdf';
import './AdminEventTimelineHistory.css';

const AdminEventTimelineHistory = () => {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [pdfJobId, setPdfJobId] = useState(null);
  const [error, setError] = useState('');
  const [userNameFilter, setUserNameFilter] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [timelineType, setTimelineType] = useState('yearly');

  const fetchRows = async (nextPage, overrides = null) => {
    setLoading(true);
    setError('');
    try {
      const filters = overrides || {
        userName: userNameFilter,
        startDate: startDateFilter,
        endDate: endDateFilter,
        timelineType,
      };
      const params = new URLSearchParams();
      params.set('page', String(nextPage));
      params.set('limit', '50');
      params.set('timeline_type', String(filters.timelineType || 'yearly'));
      if (filters.userName.trim()) params.set('user_name', filters.userName.trim());
      if (filters.startDate) params.set('start_date', filters.startDate);
      if (filters.endDate) params.set('end_date', filters.endDate);
      const response = await fetch(`/api/admin/event-timeline/history?${params.toString()}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch timeline history (${response.status})`);
      }
      const data = await response.json();
      setItems(data.items || []);
      setPage(Number(data.page || nextPage || 1));
      setTotalPages(Math.max(1, Number(data.total_pages || 1)));
    } catch (e) {
      setError(e?.message || 'Failed to load timeline history');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (row) => {
    if (!row?.job_id || (row.status || '').toLowerCase() !== 'completed') return;
    setPdfJobId(row.job_id);
    setError('');
    try {
      const response = await fetch(`/api/admin/event-timeline/job/${encodeURIComponent(row.job_id)}/result`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || data.message || `Load failed (${response.status})`);
      }
      const year = Number(data.selected_year) || new Date().getFullYear();
      const monthlyData = data.monthly_data;
      if (!monthlyData || typeof monthlyData !== 'object') {
        throw new Error('No timeline payload in response');
      }
      const logoSrc =
        typeof window !== 'undefined' && window.location?.origin
          ? `${window.location.origin}/images/astroroshni-icon-96.png`
          : null;
      const native = data.native_name || row.native_name || '';
      const fileNameBase = `event_timeline_${year}_${native || 'user'}_${String(row.job_id).slice(0, 8)}`;
      await downloadEventTimelinePdf({
        year,
        nativeName: native,
        monthlyData,
        fileNameBase,
        logoSrc,
      });
    } catch (e) {
      setError(e?.message || 'PDF download failed');
    } finally {
      setPdfJobId(null);
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

  return (
    <div className="admin-event-timeline-history">
      <div className="admin-event-timeline-history__header">
        <h2>Event timeline usage</h2>
        <button
          type="button"
          className="admin-event-timeline-history__refresh"
          onClick={() => fetchRows(page)}
          disabled={loading}
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      <div className="admin-event-timeline-history__filters">
        <select value={timelineType} onChange={(e) => setTimelineType(e.target.value)}>
          <option value="yearly">Yearly</option>
          <option value="monthly">Monthly</option>
          <option value="all">All</option>
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
            fetchRows(1, { userName: '', startDate: '', endDate: '', timelineType });
          }}
          disabled={loading}
        >
          Clear
        </button>
      </div>

      {error ? <div className="admin-event-timeline-history__error">{error}</div> : null}

      <div className="admin-event-timeline-history__table-wrap">
        <table className="admin-event-timeline-history__table">
          <thead>
            <tr>
              <th>When</th>
              <th>User</th>
              <th>Year</th>
              <th>Month</th>
              <th>Status</th>
              <th>Model</th>
              <th>Input</th>
              <th>Cached In</th>
              <th>Non-cached In</th>
              <th>Cache Setup In</th>
              <th>Output</th>
              <th>Total</th>
              <th>Cost (INR)</th>
              <th>PDF</th>
            </tr>
          </thead>
          <tbody>
            {!loading && items.length === 0 ? (
              <tr>
                <td colSpan={14} className="admin-event-timeline-history__empty">
                  No timeline runs match the current filters.
                </td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.job_id}>
                  <td title={row.job_id}>{formatDate(row.completed_at || row.created_at)}</td>
                  <td>
                    <div>{row.user_name || 'Unknown'}</div>
                    <div className="admin-event-timeline-history__sub">
                      {row.user_phone || '—'}
                      {row.native_name ? ` · ${row.native_name}` : ''}
                    </div>
                  </td>
                  <td>{row.selected_year}</td>
                  <td>{row.selected_month || '—'}</td>
                  <td>{row.status}</td>
                  <td className="admin-event-timeline-history__model">{row.llm_model || '—'}</td>
                  <td>{Number(row.llm_input_tokens || 0).toLocaleString()}</td>
                  <td>{Number(row.llm_cached_input_tokens || 0).toLocaleString()}</td>
                  <td>{Number(row.llm_non_cached_input_tokens || 0).toLocaleString()}</td>
                  <td>{Number(row.llm_cache_setup_input_tokens || 0).toLocaleString()}</td>
                  <td>{Number(row.llm_output_tokens || 0).toLocaleString()}</td>
                  <td>{Number(row.llm_total_tokens || 0).toLocaleString()}</td>
                  <td title={row.cost_summary?.note || ''}>
                    <div>{Number(row.cost_summary?.total_cost_inr_estimate || 0).toFixed(4)}</div>
                    <div className="admin-event-timeline-history__sub">
                      NC In: {Number(row.cost_summary?.input_cost_non_cached_inr_estimate || 0).toFixed(4)}
                    </div>
                    <div className="admin-event-timeline-history__sub">
                      C In: {Number(row.cost_summary?.input_cost_cached_inr_estimate || 0).toFixed(4)}
                    </div>
                    <div className="admin-event-timeline-history__sub">
                      Cache setup: {Number(row.cost_summary?.cache_setup_cost_inr_estimate || 0).toFixed(4)}
                    </div>
                    <div className="admin-event-timeline-history__sub">
                      Out: {Number(row.cost_summary?.output_cost_inr_estimate || 0).toFixed(4)}
                    </div>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="admin-event-timeline-history__pdf-btn"
                      disabled={
                        pdfJobId === row.job_id ||
                        (row.status || '').toLowerCase() !== 'completed'
                      }
                      title={
                        (row.status || '').toLowerCase() !== 'completed'
                          ? 'Only completed jobs have a PDF'
                          : 'Download PDF (same layout as app export)'
                      }
                      onClick={() => handleDownloadPdf(row)}
                    >
                      {pdfJobId === row.job_id ? '…' : 'PDF'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="admin-event-timeline-history__pager">
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

export default AdminEventTimelineHistory;
