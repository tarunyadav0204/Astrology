import React, { useState, useEffect } from 'react';

export default function AdminChatAnalysis() {
  const [byCategory, setByCategory] = useState([]);
  const [byFaq, setByFaq] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('/api/admin/chat/analysis-stats', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Failed to load');
        return res.json();
      })
      .then((data) => {
        setByCategory(data.by_category || []);
        setByFaq(data.by_faq || []);
      })
      .catch((err) => setError(err.message || 'Failed to load chat analysis'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="admin-chat-analysis-loading">Loading chat analysis…</div>;
  if (error) return <div className="admin-chat-analysis-error">{error}</div>;

  return (
    <div className="admin-chat-analysis">
      <h2>Chat analysis</h2>

      <div className="admin-chat-analysis-section">
        <h3>By category</h3>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {byCategory.length === 0 ? (
              <tr><td colSpan={2}>No categorized questions yet.</td></tr>
            ) : (
              byCategory.map((row) => (
                <tr key={row.category}>
                  <td>{row.category}</td>
                  <td>{row.count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="admin-chat-analysis-section">
        <h3>By FAQ (frequently asked)</h3>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Canonical question</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {byFaq.length === 0 ? (
              <tr><td colSpan={2}>No FAQ data yet.</td></tr>
            ) : (
              byFaq.map((row, i) => (
                <tr key={row.canonical_question || i}>
                  <td>{row.canonical_question}</td>
                  <td>{row.count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
