import React, { useState, useEffect, useCallback } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminActivity.css';

const COLUMNS = [
  'event_id', 'user_id', 'user_phone', 'user_name', 'action', 'path',
  'method', 'status_code', 'duration_ms', 'resource_type', 'resource_id',
  'metadata',
  'error_type', 'error_message', 'stack_trace',
  'ip', 'user_agent', 'created_at',
];

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

/** Sum of request duration_ms from activity logs (server-side handling time, not “time in app”). */
function formatTotalDurationMs(ms) {
  if (ms == null || Number.isNaN(Number(ms))) return '—';
  const n = Number(ms);
  if (n < 1000) return `${Math.round(n)} ms`;
  const s = n / 1000;
  const digits = s >= 100 ? 0 : s >= 10 ? 1 : 2;
  return `${s.toFixed(digits)} s`;
}

/** Returns positive integer user id or null if missing / invalid. */
function parseActivityUserId(row) {
  const v = row?.user_id;
  if (v == null || v === '') return null;
  const n = parseInt(String(v).trim(), 10);
  if (!n || Number.isNaN(n) || n <= 0) return null;
  return n;
}

export default function AdminActivity({ onOpenUserProfile }) {
  const [activity, setActivity] = useState([]);
  const [distinctUsers, setDistinctUsers] = useState([]);
  const [distinctUserCount, setDistinctUserCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateFrom, setDateFrom] = useState(todayStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [filterUserName, setFilterUserName] = useState('');
  const [filterPhone, setFilterPhone] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterResourceId, setFilterResourceId] = useState('');
  const [onlyErrors, setOnlyErrors] = useState(false);
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
      if (onlyErrors) {
        params.set('errors_only', 'true');
      } else if (filterAction.trim()) {
        params.set('action', filterAction.trim());
      }
      if (filterResourceId.trim()) params.set('resource_id', filterResourceId.trim());
      const res = await fetch(`/api/admin/activity?${params.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setActivity(data.activity || []);
      setDistinctUsers(data.distinct_users || []);
      setDistinctUserCount(
        typeof data.distinct_user_count === 'number'
          ? data.distinct_user_count
          : (data.distinct_users || []).length,
      );
    } catch (e) {
      setError(e.message || 'Failed to load activity');
      setActivity([]);
      setDistinctUsers([]);
      setDistinctUserCount(0);
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, filterUserName, filterPhone, filterAction, filterResourceId, onlyErrors, sortBy, sortOrder]);

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
    if (col === 'stack_trace' && typeof v === 'string') {
      // Keep admin table readable; stack traces are huge.
      return v.length > 250 ? `${v.slice(0, 250)}…` : v;
    }
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
      error_type: 'Error Type',
      error_message: 'Error Message',
      stack_trace: 'Stack Trace',
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
        The username filter matches logged display name and also resolves <strong>name or email</strong> from the users database (so rows with empty logged name but matching user id/phone still appear).
        Filter by <strong>Phone</strong> when User ID is missing (e.g. older activity).
        <strong>Only errors</strong> includes unhandled server exceptions (<code>api_error</code>) and any
        <code>api_request</code> with an HTTP status outside 2xx (4xx/5xx). The <strong>Users in date range</strong>{' '}
        table lists distinct users (name and phone) who had any matching activity between the selected dates
        (same filters as below).
        <strong> Total API time</strong> is the sum of request <code>duration_ms</code> (server processing
        time per logged call), not a measure of how long someone stayed in the app.
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
            <span>Name or email</span>
            <input
              type="text"
              placeholder="Name, email, or logged username"
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
                disabled={onlyErrors}
              onChange={(e) => setFilterAction(e.target.value)}
            />
          </label>
          <label>
            <span>Resource ID</span>
            <input
              type="text"
              placeholder="e.g. GPA.3349-2483-3207-52951"
              value={filterResourceId}
              onChange={(e) => setFilterResourceId(e.target.value)}
            />
          </label>
            <label style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 18 }}>
              <input
                type="checkbox"
                checked={onlyErrors}
                onChange={(e) => setOnlyErrors(e.target.checked)}
              />
              <span>Only errors</span>
            </label>
          <button type="button" className="admin-activity-refresh-btn" onClick={fetchActivity}>
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="admin-activity-error">{error}</div>}
      {loading && <div className="admin-activity-loading">Loading activity…</div>}

      {!loading && !error && (
        <>
          <div className="admin-activity-distinct-section">
            <h3 className="admin-activity-distinct-heading">
              Users in date range
              <span className="admin-activity-distinct-count">
                ({distinctUserCount} distinct {distinctUserCount === 1 ? 'user' : 'users'})
              </span>
            </h3>
            <div className="admin-activity-table-wrap admin-activity-distinct-wrap">
              <table className="admin-activity-table admin-activity-distinct-table">
                <thead>
                  <tr>
                    <th className="admin-activity-th">Name</th>
                    <th className="admin-activity-th">Phone</th>
                    <th className="admin-activity-th">User ID</th>
                    <th className="admin-activity-th">API calls</th>
                    <th className="admin-activity-th">Total API time</th>
                  </tr>
                </thead>
                <tbody>
                  {distinctUsers.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="admin-activity-empty">
                        No users with activity for the selected date range and filters.
                      </td>
                    </tr>
                  ) : (
                    distinctUsers.map((row, idx) => {
                      const uid = parseActivityUserId(row);
                      const openProfile = () => {
                        if (uid != null && typeof onOpenUserProfile === 'function') {
                          onOpenUserProfile(uid);
                        }
                      };
                      return (
                      <tr
                        key={`${row.user_id ?? ''}-${row.user_phone ?? ''}-${idx}`}
                        className={uid != null ? 'admin-activity-tr-clickable' : 'admin-activity-tr-no-user'}
                        onClick={uid != null ? openProfile : undefined}
                        title={uid != null ? 'Open user profile (today’s date range)' : 'No user ID — open profile from User management after lookup'}
                      >
                        <td className="admin-activity-td" title={row.user_name || ''}>
                          {row.user_name != null && String(row.user_name).trim() !== ''
                            ? String(row.user_name)
                            : '—'}
                        </td>
                        <td className="admin-activity-td" title={row.user_phone || ''}>
                          {row.user_phone != null && String(row.user_phone).trim() !== ''
                            ? String(row.user_phone)
                            : '—'}
                        </td>
                        <td className="admin-activity-td">
                          {row.user_id != null && row.user_id !== '' ? String(row.user_id) : '—'}
                        </td>
                        <td className="admin-activity-td">{row.api_calls != null ? row.api_calls : '—'}</td>
                        <td
                          className="admin-activity-td"
                          title={
                            row.total_duration_ms != null
                              ? `${row.total_duration_ms} ms summed`
                              : ''
                          }
                        >
                          {formatTotalDurationMs(row.total_duration_ms)}
                        </td>
                      </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

        <div className="admin-activity-table-wrap">
          <table className="admin-activity-table">
            <thead>
              <tr>
                {COLUMNS.map((col) => (
                  <th
                    key={col}
                    className="admin-activity-th admin-activity-sortable"
                    onClick={() => (col === 'stack_trace' ? null : handleSort(col))}
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
                activity.map((row, idx) => {
                  const uid = parseActivityUserId(row);
                  const openProfile = () => {
                    if (uid != null && typeof onOpenUserProfile === 'function') {
                      onOpenUserProfile(uid);
                    }
                  };
                  return (
                  <tr
                    key={row.event_id || idx}
                    className={uid != null ? 'admin-activity-tr-clickable' : 'admin-activity-tr-no-user'}
                    onClick={uid != null ? openProfile : undefined}
                    title={uid != null ? 'Open user profile (today’s date range)' : 'No user ID on this row'}
                  >
                    {COLUMNS.map((col) => (
                      <td key={col} className="admin-activity-td" title={renderCell(row, col)}>
                        {renderCell(row, col)}
                      </td>
                    ))}
                  </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}
