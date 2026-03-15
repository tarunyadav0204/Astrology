import React, { useState, useEffect, useCallback } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminActivity.css';

const COLUMNS = [
  'event_id', 'user_id', 'user_phone', 'user_name', 'action', 'path',
  'method', 'status_code', 'duration_ms', 'resource_type', 'resource_id',
  'metadata', 'ip', 'user_agent', 'created_at',
];

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function AdminActivity() {
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateFrom, setDateFrom] = useState(todayStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [filterUserName, setFilterUserName] = useState('');
  const [filterPhone, setFilterPhone] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchActivity = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        date_from: dateFrom,
        date_to: dateTo,
        sort_by: sortBy,
        order: sortOrder,
        limit: '500',
        offset: '0',
      });
      if (filterUserName.trim()) params.set('user_name', filterUserName.trim());
      if (filterPhone.trim()) params.set('user_phone', filterPhone.trim());
      if (filterAction.trim()) params.set('action', filterAction.trim());
      const res = await fetch(`/api/admin/activity?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setActivity(data.activity || []);
    } catch (e) {
      setError(e.message || 'Failed to load activity');
      setActivity([]);
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, filterUserName, filterPhone, filterAction, sortBy, sortOrder]);

  useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  const handleSort = (col) => {
    if (sortBy === col) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
  };

  const renderCell = (row, col) => {
    let v = row[col];
    if (v === null || v === undefined) return '—';
    if (col === 'created_at' && typeof v === 'string') {
      try {
        return new Date(v).toLocaleString();
      } catch (_) {
        return v;
      }
    }
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
  };

  const columnLabel = (col) => {
    const labels = {
      event_id: 'Event ID',
      user_id: 'User ID',
      user_phone: 'Phone',
      user_name: 'Username',
      action: 'Action',
      path: 'Path',
      method: 'Method',
      status_code: 'Status',
      duration_ms: 'Duration (ms)',
      resource_type: 'Resource Type',
      resource_id: 'Resource ID',
      metadata: 'Metadata',
      ip: 'IP',
      user_agent: 'User Agent',
      created_at: 'Created At',
    };
    return labels[col] || col;
  };

  return (
    <div className="admin-activity">
      <h2>Activity</h2>
      <p className="admin-activity-description">
        Today&apos;s activity by default. Use filters and column headers to sort.
        Filter by <strong>Phone</strong> when User ID is missing (e.g. older activity).
      </p>

      <div className="admin-activity-filters">
        <div className="admin-activity-filter-row">
          <label>
            <span>From date</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label>
            <span>To date</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
          <label>
            <span>Username</span>
            <input
              type="text"
              placeholder="Filter by username"
              value={filterUserName}
              onChange={(e) => setFilterUserName(e.target.value)}
            />
          </label>
          <label>
            <span>Phone</span>
            <input
              type="text"
              placeholder="Filter by phone"
              value={filterPhone}
              onChange={(e) => setFilterPhone(e.target.value)}
            />
          </label>
          <label>
            <span>Action</span>
            <input
              type="text"
              placeholder="e.g. api_request, podcast_generated"
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
            />
          </label>
          <button type="button" className="admin-activity-refresh-btn" onClick={fetchActivity}>
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="admin-activity-error">{error}</div>}
      {loading && <div className="admin-activity-loading">Loading activity…</div>}

      {!loading && !error && (
        <div className="admin-activity-table-wrap">
          <table className="admin-activity-table">
            <thead>
              <tr>
                {COLUMNS.map((col) => (
                  <th
                    key={col}
                    className="admin-activity-th admin-activity-sortable"
                    onClick={() => handleSort(col)}
                    title={`Sort by ${columnLabel(col)}`}
                  >
                    {columnLabel(col)}
                    {sortBy === col && (
                      <span className="admin-activity-sort-icon" aria-hidden>
                        {sortOrder === 'asc' ? ' ↑' : ' ↓'}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activity.length === 0 ? (
                <tr>
                  <td colSpan={COLUMNS.length} className="admin-activity-empty">
                    No activity for the selected date range and filters.
                  </td>
                </tr>
              ) : (
                activity.map((row, idx) => (
                  <tr key={row.event_id || idx}>
                    {COLUMNS.map((col) => (
                      <td key={col} className="admin-activity-td" title={renderCell(row, col)}>
                        {renderCell(row, col)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
