import React, { useState, useEffect } from 'react';
import './ConsultationHistory.css';

const ConsultationHistory = ({ user }) => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/api/chat-v2/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions);
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8001/api/chat-v2/session/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedSession(data);
      }
    } catch (error) {
      console.error('Error fetching session details:', error);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatMessageContent = (content) => {
    // Decode HTML entities
    const decoded = content
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
    
    // Format markdown-style content
    return decoded
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
      .replace(/### (.*?)\n/g, '<h3>$1</h3>') // Headers
      .replace(/\n\* /g, '<br/>• ') // Bullet points
      .replace(/\n/g, '<br/>') // Line breaks
      .replace(/• \*\*(.*?)\*\*/g, '• <strong>$1</strong>'); // Bold bullets
  };

  if (loading) {
    return (
      <div className="consultation-history">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading consultation history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="consultation-history">
      {sessions.length === 0 ? (
        <div className="no-history">
          <div className="no-history-icon">💬</div>
          <h3>No Consultations Yet</h3>
          <p>Start your first astrology consultation to see your history here.</p>
        </div>
      ) : (
        <div className="history-content">
          <div className="sessions-list">
            {sessions.map((session) => (
              <div 
                key={session.session_id}
                className={`session-card ${selectedSession?.session_id === session.session_id ? 'active' : ''}`}
                onClick={() => fetchSessionDetails(session.session_id)}
              >
                <div className="session-date">
                  {formatDate(session.created_at)}
                </div>
                <div className="session-preview">
                  {session.preview || 'Consultation session'}
                </div>
              </div>
            ))}
          </div>

          {selectedSession && (
            <div className="session-details">
              <div className="session-header">
                <h3>Consultation Details</h3>
                <button 
                  className="close-btn"
                  onClick={() => setSelectedSession(null)}
                >
                  ×
                </button>
              </div>
              
              <div className="messages-container">
                {selectedSession.messages.map((message, index) => (
                  <div 
                    key={index}
                    className={`message ${message.sender}`}
                  >
                    <div 
                      className="message-content"
                      dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}
                    />
                    <div className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConsultationHistory;