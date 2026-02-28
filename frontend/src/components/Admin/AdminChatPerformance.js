import React, { useState, useEffect } from 'react';
import './AdminChatPerformance.css';

const AdminChatPerformance = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    fetchPage();
  }, [page]);

  const fetchPage = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/admin/chat-performance?page=${page}&per_page=${perPage}`,
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

  return (
    <div className="chat-performance-container">
      <div className="chat-performance-header">
        <h2>📊 Chat Performance</h2>
        <button onClick={fetchPage} className="refresh-btn" disabled={loading}>
          🔄 Refresh
        </button>
      </div>
      <p className="chat-performance-description">
        One row per assistant answer: user, question, response preview, native (birth chart), intent router time, total duration.
      </p>

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
