import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import { sanitizeSupportBody } from '../../utils/supportText';

const STATUSES = ['open', 'pending_user', 'resolved', 'closed'];
const COMPACT_MQ = '(max-width: 767px)';

async function parseError(res) {
  try {
    const data = await res.json();
    const d = data.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) return d.map((x) => x.msg || String(x)).join(' ');
    return data.message || `HTTP ${res.status}`;
  } catch {
    return `HTTP ${res.status}`;
  }
}

function UserContactLines({ name, phone, email, compact }) {
  const lineStyle = {
    fontSize: compact ? 13 : 12,
    color: '#444',
    marginTop: compact ? 4 : 2,
    lineHeight: 1.35,
    wordBreak: 'break-word',
  };
  return (
    <>
      {name ? (
        <div style={lineStyle}>
          <span style={{ color: '#666', fontWeight: 600 }}>Name </span>
          {name}
        </div>
      ) : null}
      {phone ? (
        <div style={lineStyle}>
          <span style={{ color: '#666', fontWeight: 600 }}>Mobile </span>
          <a href={`tel:${String(phone).replace(/\s/g, '')}`} style={{ color: '#1565c0' }}>
            {phone}
          </a>
        </div>
      ) : null}
      {email ? (
        <div style={lineStyle}>
          <span style={{ color: '#666', fontWeight: 600 }}>Email </span>
          <a href={`mailto:${String(email).trim()}`} style={{ color: '#1565c0', wordBreak: 'break-all' }}>
            {email}
          </a>
        </div>
      ) : null}
    </>
  );
}

export default function AdminSupportInbox() {
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [q, setQ] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);
  const [statusBusy, setStatusBusy] = useState(false);
  const [err, setErr] = useState('');
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const mq = window.matchMedia(COMPACT_MQ);
    const apply = () => setCompact(mq.matches);
    apply();
    mq.addEventListener('change', apply);
    return () => mq.removeEventListener('change', apply);
  }, []);

  const loadList = useCallback(async () => {
    setLoading(true);
    setErr('');
    try {
      const sp = new URLSearchParams();
      sp.set('limit', '100');
      sp.set('offset', '0');
      if (statusFilter) sp.set('status', statusFilter);
      if (q.trim()) sp.set('q', q.trim());
      const res = await fetch(`/api/admin/support/tickets?${sp.toString()}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!res.ok) throw new Error(await parseError(res));
      const data = await res.json();
      setTickets(data.tickets || []);
      setTotal(data.total ?? 0);
    } catch (e) {
      setErr(e.message || 'Failed to load tickets');
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, q]);

  useEffect(() => {
    const delay = q.trim() ? 400 : 0;
    const t = setTimeout(() => loadList(), delay);
    return () => clearTimeout(t);
  }, [statusFilter, q, loadList]);

  const loadDetail = async (id) => {
    setDetailLoading(true);
    setErr('');
    setReplyText('');
    try {
      const res = await fetch(`/api/admin/support/tickets/${id}`, {
        headers: getAdminAuthHeaders(),
      });
      if (!res.ok) throw new Error(await parseError(res));
      const data = await res.json();
      setDetail(data);
      setSelectedId(id);
    } catch (e) {
      setErr(e.message || 'Failed to load thread');
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const selectTicket = (id) => {
    loadDetail(id);
  };

  const backToList = () => {
    setSelectedId(null);
    setDetail(null);
  };

  const sendReply = async () => {
    if (!selectedId) return;
    const body = sanitizeSupportBody(replyText);
    if (!body) {
      setErr('Enter a non-empty message.');
      return;
    }
    setSending(true);
    setErr('');
    try {
      const res = await fetch(`/api/admin/support/tickets/${selectedId}/messages`, {
        method: 'POST',
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: body }),
      });
      if (!res.ok) throw new Error(await parseError(res));
      setReplyText('');
      await loadDetail(selectedId);
      await loadList();
    } catch (e) {
      setErr(e.message || 'Send failed');
    } finally {
      setSending(false);
    }
  };

  const patchStatus = async (next) => {
    if (!selectedId) return;
    setStatusBusy(true);
    setErr('');
    try {
      const res = await fetch(`/api/admin/support/tickets/${selectedId}`, {
        method: 'PATCH',
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: next }),
      });
      if (!res.ok) throw new Error(await parseError(res));
      await loadDetail(selectedId);
      await loadList();
    } catch (e) {
      setErr(e.message || 'Update failed');
    } finally {
      setStatusBusy(false);
    }
  };

  const ticket = detail?.ticket;
  const messages = detail?.messages || [];

  const showListPanel = !compact || !selectedId;
  const showThreadPanel = !compact || !!selectedId;
  /** On narrow screens in thread view, list UI (title, filters, total) is hidden to maximize space */
  const showListChrome = !compact || !selectedId;

  return (
    <div className="admin-support-inbox">
      {showListChrome ? (
        <>
          <h2>Support tickets</h2>
          <p className="settings-hint admin-support-inbox-hint" style={{ marginBottom: compact ? 8 : 16 }}>
            View and reply to user support threads. Messages are stored as plain text.
          </p>
        </>
      ) : null}
      {err ? (
        <div
          style={{
            padding: compact ? '8px 10px' : 12,
            background: '#fff0f0',
            borderRadius: 8,
            marginBottom: compact ? 8 : 12,
            color: '#a00',
            fontSize: compact ? 14 : undefined,
          }}
        >
          {err}
        </div>
      ) : null}

      {showListChrome ? (
        <>
          <div
            className="admin-support-filters"
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: compact ? 8 : 12,
              marginBottom: compact ? 8 : 16,
              alignItems: compact ? 'stretch' : 'flex-end',
              flexDirection: compact ? 'column' : 'row',
            }}
          >
            <div className="form-field" style={{ width: compact ? '100%' : 'auto', minWidth: compact ? 0 : 140 }}>
              <label>Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: compact ? '10px 12px' : '8px 12px',
                  minWidth: compact ? '100%' : 140,
                  width: compact ? '100%' : 'auto',
                  fontSize: 16,
                  boxSizing: 'border-box',
                }}
              >
                <option value="">All</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div
              className="form-field"
              style={{
                flex: compact ? 'none' : '1 1 200px',
                width: compact ? '100%' : 'auto',
                minWidth: compact ? 0 : 200,
              }}
            >
              <label>Search subject</label>
              <input
                type="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                maxLength={100}
                placeholder="Keyword"
                style={{
                  padding: compact ? '10px 12px' : '8px 12px',
                  width: '100%',
                  maxWidth: compact ? 'none' : 320,
                  fontSize: 16,
                  boxSizing: 'border-box',
                }}
              />
            </div>
            <button
              type="button"
              className="create-btn"
              onClick={() => loadList()}
              disabled={loading}
              style={{
                padding: compact ? '10px 16px' : undefined,
                alignSelf: compact ? 'stretch' : 'auto',
                minHeight: compact ? 44 : undefined,
              }}
            >
              {loading ? 'Loading…' : 'Refresh'}
            </button>
          </div>

          <p style={{ fontSize: 13, color: '#666', marginBottom: compact ? 8 : 12 }}>
            Total: {total}
          </p>
        </>
      ) : null}

      <div
        className="support-inbox-grid"
        style={{
          display: compact ? 'block' : 'grid',
          gridTemplateColumns: compact ? undefined : 'minmax(260px, 1fr) minmax(320px, 2fr)',
          gap: compact ? 0 : 20,
          alignItems: 'start',
        }}
      >
        {showListPanel && (
          <div
            className="admin-support-list-wrap"
            style={{
              border: '1px solid #ddd',
              borderRadius: 8,
              maxHeight: compact ? 'none' : '70vh',
              overflow: 'auto',
              background: '#fafafa',
              marginBottom: compact && selectedId ? 0 : compact ? 8 : 0,
              WebkitOverflowScrolling: 'touch',
            }}
          >
            {loading && tickets.length === 0 ? (
              <p style={{ padding: compact ? '12px 10px' : 16 }}>Loading…</p>
            ) : tickets.length === 0 ? (
              <p style={{ padding: compact ? '12px 10px' : 16 }}>No tickets.</p>
            ) : (
              tickets.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => selectTicket(t.id)}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: compact ? '10px 12px' : '12px 14px',
                    border: 'none',
                    borderBottom: '1px solid #eee',
                    background: selectedId === t.id ? '#e3f2fd' : 'transparent',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: compact ? 15 : 14, lineHeight: 1.3 }}>
                    #{t.id} — {t.subject}
                  </div>
                  <UserContactLines
                    name={t.user_name}
                    phone={t.user_phone}
                    email={t.user_email}
                    compact={compact}
                  />
                  <div style={{ fontSize: 12, color: '#555', marginTop: 6 }}>
                    {t.status} · {t.source}
                  </div>
                  {t.last_message_preview ? (
                    <div
                      style={{
                        fontSize: 12,
                        color: '#777',
                        marginTop: 6,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {t.last_message_preview}
                    </div>
                  ) : null}
                </button>
              ))
            )}
          </div>
        )}

        {showThreadPanel && (
          <div
            className="admin-support-thread"
            style={{
              border: '1px solid #ddd',
              borderRadius: compact ? 6 : 8,
              padding: compact ? 8 : 16,
              background: '#fff',
              minHeight: compact ? 'auto' : 200,
              position: compact ? 'relative' : 'static',
            }}
          >
            {compact && selectedId ? (
              <button
                type="button"
                onClick={backToList}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 8,
                  padding: '6px 0',
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  fontSize: 16,
                  fontWeight: 600,
                  color: '#1565c0',
                  minHeight: 40,
                }}
              >
                ← All tickets
              </button>
            ) : null}

            {!selectedId ? (
              <p style={{ color: '#666', fontSize: compact ? 15 : undefined }}>
                {compact ? 'Tap a ticket to open the thread.' : 'Select a ticket to view the thread.'}
              </p>
            ) : detailLoading ? (
              <p>Loading thread…</p>
            ) : ticket ? (
              <>
                <div style={{ marginBottom: compact ? 10 : 16 }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: compact ? 17 : 20, lineHeight: 1.25 }}>
                    {ticket.subject}
                  </h3>
                  <div
                    style={{
                      fontSize: compact ? 13 : 13,
                      color: '#555',
                      marginBottom: compact ? 8 : 10,
                      padding: compact ? '8px 10px' : '10px 12px',
                      background: '#f5f7fa',
                      borderRadius: 8,
                      border: '1px solid #e8ecf1',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: compact ? 6 : 8, color: '#333' }}>User</div>
                    <div style={{ marginBottom: compact ? 4 : 6 }}>
                      <span style={{ color: '#666' }}>User ID </span>
                      {ticket.userid}
                    </div>
                    <UserContactLines
                      name={ticket.user_name}
                      phone={ticket.user_phone}
                      email={ticket.user_email}
                      compact
                    />
                  </div>
                  <div
                    style={{
                      marginTop: 8,
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: compact ? 10 : 8,
                      alignItems: compact ? 'stretch' : 'center',
                      flexDirection: compact ? 'column' : 'row',
                    }}
                  >
                    <span style={{ fontSize: compact ? 15 : 13 }}>Status: {ticket.status}</span>
                    <select
                      value={ticket.status}
                      onChange={(e) => patchStatus(e.target.value)}
                      disabled={statusBusy}
                      style={{
                        padding: compact ? '12px 10px' : '6px 10px',
                        fontSize: 16,
                        width: compact ? '100%' : 'auto',
                        maxWidth: compact ? '100%' : 280,
                      }}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div
                  style={{
                    maxHeight: compact ? 'min(58vh, 560px)' : '45vh',
                    overflow: 'auto',
                    marginBottom: compact ? 10 : 16,
                    WebkitOverflowScrolling: 'touch',
                  }}
                >
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      style={{
                        marginBottom: compact ? 8 : 12,
                        padding: compact ? 8 : 10,
                        borderRadius: 6,
                        background: m.author_role === 'admin' ? '#e8f5e9' : '#f5f5f5',
                      }}
                    >
                      <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                        {m.author_role === 'admin' ? 'Admin' : 'User'} · {m.created_at || ''}
                      </div>
                      <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: compact ? 15 : 14 }}>
                        {m.body}
                      </div>
                    </div>
                  ))}
                </div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: 4, fontSize: compact ? 14 : undefined }}>
                  Reply
                </label>
                <textarea
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  rows={compact ? 4 : 5}
                  maxLength={9000}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    padding: compact ? 10 : 12,
                    borderRadius: 4,
                    border: '1px solid #ccc',
                    fontSize: 16,
                    minHeight: compact ? 96 : undefined,
                  }}
                  placeholder="Plain text only"
                />
                <div style={{ marginTop: compact ? 8 : 12 }}>
                  <button
                    type="button"
                    className="create-btn"
                    onClick={sendReply}
                    disabled={sending}
                    style={{
                      width: compact ? '100%' : 'auto',
                      padding: compact ? '12px 18px' : undefined,
                      minHeight: compact ? 44 : undefined,
                    }}
                  >
                    {sending ? 'Sending…' : 'Send reply'}
                  </button>
                </div>
              </>
            ) : (
              <p>Could not load ticket.</p>
            )}
          </div>
        )}
      </div>
      <style>{`
        @media (max-width: 767px) {
          .admin-support-inbox .support-inbox-grid {
            display: block;
          }
        }
      `}</style>
    </div>
  );
}
