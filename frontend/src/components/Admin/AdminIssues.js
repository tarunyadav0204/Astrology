import React, { useCallback, useEffect, useState } from 'react';
import { adminService, getAdminAuthHeaders } from '../../services/adminService';

const STATUS_OPTIONS = ['all', 'open', 'fixed', 'closed'];

function formatDateTimeIST(value) {
  if (!value) return '—';
  const raw = String(value).trim();
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw);
  const normalized = hasTimezone ? raw : `${raw.replace(' ', 'T')}Z`;
  const d = new Date(normalized);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    timeZone: 'Asia/Kolkata',
  });
}

function statusBadgeStyle(status) {
  if (status === 'fixed') return { background: '#dcfce7', color: '#166534' };
  if (status === 'closed') return { background: '#f1f5f9', color: '#475569' };
  return { background: '#ffedd5', color: '#c2410c' };
}

export default function AdminIssues() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [screenshotFile, setScreenshotFile] = useState(null);
  const [creating, setCreating] = useState(false);

  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [commentSaving, setCommentSaving] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);
  const [dueSaving, setDueSaving] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const loadList = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getAdminIssues({
        page,
        limit,
        status: statusFilter === 'all' ? undefined : statusFilter,
      });
      setItems(data.items || []);
      setTotal(Number(data.total) || 0);
    } catch (e) {
      setError(e?.message || 'Failed to load issues');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, limit, statusFilter]);

  const loadDetail = useCallback(async (issueId) => {
    if (!issueId) {
      setDetail(null);
      return;
    }
    setDetailLoading(true);
    try {
      const data = await adminService.getAdminIssue(issueId);
      setDetail(data);
    } catch (e) {
      setError(e?.message || 'Failed to load issue');
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  useEffect(() => {
    loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setCreating(true);
    setError('');
    try {
      const form = new FormData();
      form.append('title', title.trim());
      form.append('description', description.trim());
      if (dueDate) form.append('due_date', dueDate);
      if (screenshotFile) form.append('screenshot', screenshotFile);
      const res = await adminService.createAdminIssue(form);
      setTitle('');
      setDescription('');
      setDueDate('');
      setScreenshotFile(null);
      setPage(1);
      await loadList();
      if (res?.id) setSelectedId(res.id);
    } catch (err) {
      setError(err?.message || 'Failed to create issue');
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    if (!selectedId || !detail?.issue) return;
    setStatusSaving(true);
    try {
      await adminService.updateAdminIssue(selectedId, { status: newStatus });
      await Promise.all([loadList(), loadDetail(selectedId)]);
    } catch (e) {
      setError(e?.message || 'Failed to update status');
    } finally {
      setStatusSaving(false);
    }
  };

  const handleDueDateChange = async (newDue) => {
    if (!selectedId) return;
    setDueSaving(true);
    try {
      await adminService.updateAdminIssue(selectedId, { due_date: newDue || '' });
      await Promise.all([loadList(), loadDetail(selectedId)]);
    } catch (e) {
      setError(e?.message || 'Failed to update due date');
    } finally {
      setDueSaving(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!selectedId || !commentText.trim()) return;
    setCommentSaving(true);
    try {
      await adminService.addAdminIssueComment(selectedId, commentText.trim());
      setCommentText('');
      await Promise.all([loadList(), loadDetail(selectedId)]);
    } catch (err) {
      setError(err?.message || 'Failed to add comment');
    } finally {
      setCommentSaving(false);
    }
  };

  const openScreenshot = async (issueId) => {
    try {
      const url = adminService.getAdminIssueScreenshotUrl(issueId);
      const res = await fetch(url, { headers: getAdminAuthHeaders() });
      if (!res.ok) throw new Error('Could not load screenshot');
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      window.open(objectUrl, '_blank', 'noopener,noreferrer');
      setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
    } catch (e) {
      setError(e?.message || 'Failed to open screenshot');
    }
  };

  const issue = detail?.issue;
  const comments = detail?.comments || [];

  return (
    <div className="users-management admin-issues">
      <h2 style={{ marginBottom: 8 }}>Issues / enhancements</h2>
      <p style={{ color: '#555', marginBottom: 16, fontSize: 14 }}>
        Track bugs and product improvements. Screenshots use the same private storage bucket as expense invoices.
      </p>

      <form className="admin-issues-create" onSubmit={handleCreate}>
        <h3 style={{ margin: '0 0 12px', fontSize: 15 }}>New issue</h3>
        <div className="users-management-filters" style={{ marginBottom: 12 }}>
          <label style={{ flex: '1 1 220px' }}>
            <span>Title</span>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={500} />
          </label>
          <label>
            <span>Due date</span>
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </label>
          <label>
            <span>Screenshot (optional)</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setScreenshotFile(e.target.files?.[0] || null)}
            />
          </label>
        </div>
        <label style={{ display: 'block', marginBottom: 12 }}>
          <span style={{ display: 'block', fontSize: 12, color: '#666', marginBottom: 4 }}>Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            style={{ width: '100%', maxWidth: 720, padding: 8, borderRadius: 6, border: '1px solid #ddd' }}
          />
        </label>
        <button type="submit" className="users-search-btn" disabled={creating}>
          {creating ? 'Creating…' : 'Create issue'}
        </button>
      </form>

      <div className="users-management-filters" style={{ margin: '20px 0' }}>
        <label>
          <span>Status</span>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="users-search-btn" onClick={loadList} disabled={loading}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

      <div className="admin-issues-layout">
        <div className="users-table">
          {loading ? (
            <div className="loading">Loading issues…</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Opened (IST)</th>
                  <th>Due</th>
                  <th>Comments</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="users-table-empty">No issues yet.</td>
                  </tr>
                ) : (
                  items.map((row) => (
                    <tr
                      key={row.id}
                      onClick={() => setSelectedId(row.id)}
                      style={{
                        cursor: 'pointer',
                        background: selectedId === row.id ? '#eff6ff' : undefined,
                      }}
                    >
                      <td>
                        <strong>{row.title}</strong>
                        {row.has_screenshot ? (
                          <span style={{ marginLeft: 8, fontSize: 11, color: '#64748b' }}>📷</span>
                        ) : null}
                      </td>
                      <td>
                        <span
                          style={{
                            ...statusBadgeStyle(row.status),
                            fontSize: 12,
                            padding: '2px 8px',
                            borderRadius: 999,
                            fontWeight: 600,
                          }}
                        >
                          {row.status}
                        </span>
                      </td>
                      <td>{formatDateTimeIST(row.opened_at)}</td>
                      <td>{row.due_date || '—'}</td>
                      <td>{row.comment_count ?? 0}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        <div className="admin-issues-detail">
          {!selectedId ? (
            <p style={{ color: '#888', fontSize: 14 }}>Select an issue to view details and comments.</p>
          ) : detailLoading ? (
            <div className="loading">Loading…</div>
          ) : issue ? (
            <>
              <h3 style={{ marginTop: 0 }}>{issue.title}</h3>
              <p style={{ fontSize: 13, color: '#666' }}>
                Opened {formatDateTimeIST(issue.opened_at)}
                {issue.created_by_name ? ` · ${issue.created_by_name}` : ''}
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
                <label style={{ fontSize: 13 }}>
                  Status{' '}
                  <select
                    value={issue.status}
                    disabled={statusSaving}
                    onChange={(e) => handleStatusChange(e.target.value)}
                  >
                    <option value="open">Open</option>
                    <option value="fixed">Fixed</option>
                    <option value="closed">Closed</option>
                  </select>
                </label>
                <label style={{ fontSize: 13 }}>
                  Due date{' '}
                  <input
                    type="date"
                    value={issue.due_date || ''}
                    disabled={dueSaving}
                    onChange={(e) => handleDueDateChange(e.target.value)}
                  />
                </label>
              </div>
              <div
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  padding: 12,
                  marginBottom: 12,
                  whiteSpace: 'pre-wrap',
                  fontSize: 14,
                }}
              >
                {issue.description || '—'}
              </div>
              {issue.has_screenshot ? (
                <button type="button" className="users-search-btn" onClick={() => openScreenshot(issue.id)}>
                  View screenshot
                </button>
              ) : null}

              <h4 style={{ margin: '20px 0 10px' }}>Comments</h4>
              <div className="admin-issues-comments">
                {comments.length === 0 ? (
                  <p style={{ fontSize: 13, color: '#888' }}>No comments yet.</p>
                ) : (
                  comments.map((c) => (
                    <div key={c.id} className="admin-issues-comment">
                      <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                        {c.author || 'Admin'} · {formatDateTimeIST(c.created_at)}
                      </div>
                      <div style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>{c.body}</div>
                    </div>
                  ))
                )}
              </div>
              <form onSubmit={handleAddComment} style={{ marginTop: 12 }}>
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={2}
                  placeholder="Add a comment…"
                  style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #ddd' }}
                />
                <button type="submit" className="users-search-btn" disabled={commentSaving || !commentText.trim()}>
                  {commentSaving ? 'Saving…' : 'Add comment'}
                </button>
              </form>
            </>
          ) : null}
        </div>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16 }}>
          <button
            type="button"
            className="users-pagination-btn"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </button>
          <span className="users-pagination-info">
            Page {page} of {totalPages} · {total} total
          </span>
          <button
            type="button"
            className="users-pagination-btn"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
