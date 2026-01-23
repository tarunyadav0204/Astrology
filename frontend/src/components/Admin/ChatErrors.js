import React, { useState, useEffect } from 'react';
import './ChatErrors.css';

const ChatErrors = () => {
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, last24h: 0, uniqueUsers: 0 });
  const [sourceFilter, setSourceFilter] = useState('all');
  const [expandedError, setExpandedError] = useState(null);

  useEffect(() => {
    fetchErrors();
  }, [sourceFilter]);

  const fetchErrors = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/admin/chat-errors?limit=100&source=${sourceFilter}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      console.log('Chat errors API response:', data);
      const errorList = data.errors || [];
      setErrors(errorList);

      // Calculate stats
      const now = new Date();
      const last24h = errorList.filter(e => {
        const errorTime = new Date(e.created_at);
        return (now - errorTime) < 24 * 60 * 60 * 1000;
      }).length;

      const uniqueUsers = new Set(errorList.map(e => e.username)).size;

      setStats({
        total: errorList.length,
        last24h,
        uniqueUsers
      });
    } catch (error) {
      console.error('Error fetching chat errors:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-errors-container">
      <div className="chat-errors-header">
        <h2>🚨 Chat Error Logs</h2>
        <button onClick={fetchErrors} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      <div className="error-stats">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Errors</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.last24h}</div>
          <div className="stat-label">Last 24 Hours</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.uniqueUsers}</div>
          <div className="stat-label">Affected Users</div>
        </div>
      </div>

      <div className="filter-section">
        <label>Filter by Source:</label>
        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
          <option value="all">All Errors</option>
          <option value="mobile">Mobile Errors</option>
          <option value="backend">Backend Errors</option>
        </select>
      </div>

      {loading ? (
        <div className="loading">Loading errors...</div>
      ) : errors.length === 0 ? (
        <div className="no-errors">✅ No errors found</div>
      ) : (
        <div className="errors-list">
          {errors.map(error => (
            <div key={error.id} className="error-card">
              <div className="error-header">
                <span className="error-user">👤 {error.username} ({error.phone})</span>
                <span className="error-time">⏰ {new Date(error.created_at).toLocaleString()}</span>
              </div>
              <div className="error-meta">
                <span className="error-type">{error.error_type}</span>
                <span className="error-source">{error.error_source === 'backend' ? '🔧 Backend' : '📱 Mobile'}</span>
                <span className="error-platform">📱 {error.platform}</span>
              </div>
              <div className="error-message">❌ {error.error_message}</div>
              {error.user_question && (
                <div className="user-question">💬 User asked: "{error.user_question}"</div>
              )}
              {error.birth_data_context && (
                <div className="birth-context">🔮 Birth Data: {JSON.parse(error.birth_data_context).name} ({JSON.parse(error.birth_data_context).date} {JSON.parse(error.birth_data_context).time})</div>
              )}
              {error.stack_trace && (
                <div className="stack-trace-section">
                  <button 
                    className="toggle-stack-btn"
                    onClick={() => setExpandedError(expandedError === error.id ? null : error.id)}
                  >
                    {expandedError === error.id ? '▼ Hide' : '▶ Show'} Stack Trace
                  </button>
                  {expandedError === error.id && (
                    <pre className="stack-trace">{error.stack_trace}</pre>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatErrors;
