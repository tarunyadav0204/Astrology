import React, { useState, useEffect, useMemo } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import { formatChatMessageHtml as formatMessageContent } from '../../utils/markdown';
import './AdminChatHistory.css';

const AdminChatHistory = () => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessionQuery, setSessionQuery] = useState('');

  useEffect(() => {
    fetchAllChatHistory();
  }, []);

  const fetchAllChatHistory = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/chat/all-history', {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Error fetching all chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId) => {
    try {
      const response = await fetch(`/api/admin/chat/session/${sessionId}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedSession(data);
      }
    } catch (error) {
      console.error('Error fetching session details:', error);
    }
  };

  const IST = 'Asia/Kolkata';

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: IST
    }) + ' IST';
  };

  const formatTimeIST = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: IST
    }) + ' IST';
  };

  const filteredSessions = useMemo(() => {
    const q = sessionQuery.trim().toLowerCase();
    if (!q) return sessions;
    return sessions.filter((s) => {
      const hay = [
        s.user_name,
        s.user_phone,
        s.native_name,
        s.preview,
        s.session_id,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return hay.includes(q);
    });
  }, [sessions, sessionQuery]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape' && selectedSession) setSelectedSession(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selectedSession]);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 900px), (max-height: 700px)');
    const lock = () => {
      if (selectedSession && mq.matches) {
        document.body.classList.add('admin-chat-mobile-thread-active');
      } else {
        document.body.classList.remove('admin-chat-mobile-thread-active');
      }
    };
    lock();
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', lock);
      return () => {
        mq.removeEventListener('change', lock);
        document.body.classList.remove('admin-chat-mobile-thread-active');
      };
    }
    mq.addListener(lock);
    return () => {
      mq.removeListener(lock);
      document.body.classList.remove('admin-chat-mobile-thread-active');
    };
  }, [selectedSession]);

  const msgCount = selectedSession?.messages?.length ?? 0;

  return (
    <div
      className={`admin-chat-history${
        selectedSession ? ' admin-chat-history--thread-open' : ''
      }`}
    >
      <div className="admin-chat-history-intro">
        <h2>Chat history</h2>
        <p className="admin-chat-history-hint admin-chat-history-hint--desktop">
          Open a session for a full-width transcript. Press <kbd>Esc</kbd> to close the
          conversation.
        </p>
        <p className="admin-chat-history-hint admin-chat-history-hint--mobile">
          Tap a session to open it full screen. Use <strong>Back</strong> or the close control to
          return here.
        </p>
      </div>

      <div className={`admin-chat-content ${selectedSession ? 'has-selection' : ''}`}>
        <aside className="sessions-sidebar" aria-label="Chat sessions">
          <div className="sessions-list-header">
            <h3>Sessions</h3>
            {!loading && sessions.length > 0 && (
              <span className="sessions-count">{sessions.length}</span>
            )}
          </div>
          {sessions.length > 0 && (
            <div className="sessions-search-wrap">
              <label className="sessions-search-label" htmlFor="admin-chat-session-filter">
                Filter
              </label>
              <input
                id="admin-chat-session-filter"
                type="search"
                className="sessions-search-input"
                placeholder="Name, phone, chart, preview…"
                value={sessionQuery}
                onChange={(e) => setSessionQuery(e.target.value)}
                autoComplete="off"
              />
            </div>
          )}
          <div className="sessions-list">
            {loading ? (
              <div className="loading">Loading sessions…</div>
            ) : sessions.length === 0 ? (
              <div className="no-sessions">No chat sessions found.</div>
            ) : filteredSessions.length === 0 ? (
              <div className="no-sessions">No sessions match your filter.</div>
            ) : (
              filteredSessions.map((session) => (
                <div
                  key={session.session_id}
                  role="button"
                  tabIndex={0}
                  className={`session-card ${
                    selectedSession?.session_id === session.session_id ? 'active' : ''
                  }`}
                  onClick={() => fetchSessionDetails(session.session_id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      fetchSessionDetails(session.session_id);
                    }
                  }}
                >
                  <div className="session-user">
                    <strong>{session.user_name || 'Unknown'}</strong>
                    <span className="session-phone"> {session.user_phone}</span>
                  </div>
                  {session.native_name && (
                    <div className="session-card-native">Chart: {session.native_name}</div>
                  )}
                  <div className="session-date">{formatDate(session.created_at)}</div>
                  <div className="session-preview">{session.preview || 'Chat session'}</div>
                </div>
              ))
            )}
          </div>
        </aside>

        <div className="session-detail-pane">
          {selectedSession ? (
            <div className="session-details">
              <div className="session-header">
                <button
                  type="button"
                  className="session-back"
                  onClick={() => setSelectedSession(null)}
                  aria-label="Back to sessions list"
                >
                  <span className="session-back-icon" aria-hidden="true">
                    ←
                  </span>
                  <span className="session-back-label">Sessions</span>
                </button>
                <div className="session-header-center">
                  <h3 className="session-header-title">
                    <span className="session-header-title-text">Conversation</span>
                    {selectedSession.native_name && (
                      <span className="session-native-name">{selectedSession.native_name}</span>
                    )}
                  </h3>
                  {msgCount > 0 && (
                    <span className="session-msg-count">
                      {msgCount} message{msgCount === 1 ? '' : 's'}
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  className="session-close"
                  onClick={() => setSelectedSession(null)}
                  aria-label="Close conversation"
                >
                  <span aria-hidden="true">×</span>
                </button>
              </div>

              <div className="messages-container">
                {selectedSession.messages.map((message, index) => {
                  const role =
                    message.sender === 'user'
                      ? 'user'
                      : message.sender === 'assistant'
                        ? 'assistant'
                        : 'assistant';
                  const label =
                    message.sender === 'user'
                      ? 'User'
                      : message.sender === 'assistant'
                        ? 'Assistant'
                        : String(message.sender || 'Message').replace(/^\w/, (c) => c.toUpperCase());
                  return (
                <div key={index} className={`message message--${role}`}>
                    <div className="message-label">
                      {label}
                    </div>
                    <div
                      className="message-content"
                      dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}
                    />
                    <div className="message-meta">
                      {message.native_name && (
                        <span
                          className="message-native-badge"
                          title="Birth chart / Native"
                        >
                          {message.native_name}
                        </span>
                      )}
                      <span className="message-time">{formatTimeIST(message.timestamp)}</span>
                    </div>
                  </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="session-detail-empty">
              <div className="session-detail-empty-inner">
                <span className="session-detail-empty-icon" aria-hidden="true">
                  💬
                </span>
                <p className="session-detail-empty-title">Select a session</p>
                <p className="session-detail-empty-text">
                  Choose a conversation from the list to read the full thread. Assistant replies use
                  the full width for easier reading.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminChatHistory;