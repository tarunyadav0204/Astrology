import React, { useState, useEffect } from 'react';
import { formatChatMessageHtml } from '../../utils/markdown';
import './ConsultationHistory.css';

const ConsultationHistory = ({ user, onStartConsultation }) => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    fetchChatHistory();
  }, [user?.userid]);

  const fetchChatHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }
      // Same-origin /api path so CRA dev proxy forwards auth (matches ChatModal, CreditContext)
      const response = await fetch('/api/chat-v2/history', {
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
      const response = await fetch(`/api/chat-v2/session/${sessionId}`, {
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
      <header className="consultation-history__heading">
        <div><span>Private archive</span><h3>Past consultations</h3></div>
        <button type="button" onClick={onStartConsultation}>New consultation <span aria-hidden>↗</span></button>
      </header>
      {sessions.length === 0 ? (
        <div className="no-history">
          <div className="no-history-icon" aria-hidden>त</div>
          <h3>No Consultations Yet</h3>
          <p>Start your first astrology consultation to see your history here.</p>
          <button type="button" onClick={onStartConsultation}>Ask Tara</button>
        </div>
      ) : (
        <div className="history-content">
          <div className="sessions-list">
            {sessions.map((session) => (
              <button
                type="button"
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
                <span className="session-card__arrow" aria-hidden>→</span>
              </button>
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
                      dangerouslySetInnerHTML={{ __html: formatChatMessageHtml(message.content) }}
                    />
                    <div className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {!selectedSession && (
            <div className="session-placeholder">
              <span aria-hidden>AR</span>
              <h3>Select a consultation</h3>
              <p>Choose a dated conversation to reopen its complete question and Tara’s synthesis.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConsultationHistory;
