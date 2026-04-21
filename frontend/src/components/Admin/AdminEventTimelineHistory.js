import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminEventTimelineHistory.css';

const AdminEventTimelineHistory = () => {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
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
        <h2>Yearly Event Timeline Usage</h2>
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
            </tr>
          </thead>
          <tbody>
            {!loading && items.length === 0 ? (
              <tr>
                <td colSpan={13} className="admin-event-timeline-history__empty">
                  No yearly timeline runs found.
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
