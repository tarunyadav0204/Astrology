import React, { useState, useEffect } from 'react';
import './AdminChatHistory.css';

const AdminChatHistory = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/api/admin/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserChatHistory = async (userId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8001/api/admin/chat/history/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
        setSelectedUser(userId);
        setSelectedSession(null);
      }
    } catch (error) {
      console.error('Error fetching user chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8001/api/admin/chat/session/${sessionId}`, {
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
    const decoded = content
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
    
    return decoded
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/### (.*?)\n/g, '<h3>$1</h3>')
      .replace(/\n\* /g, '<br/>• ')
      .replace(/\n/g, '<br/>')
      .replace(/• \*\*(.*?)\*\*/g, '• <strong>$1</strong>');
  };

  return (
    <div className="admin-chat-history">
      <h2>User Chat History</h2>
      
      <div className="admin-chat-content">
        <div className="users-list">
          <h3>Users</h3>
          {loading && !selectedUser ? (
            <div className="loading">Loading users...</div>
          ) : (
            users.map(user => (
              <div 
                key={user.userid}
                className={`user-card ${selectedUser === user.userid ? 'active' : ''}`}
                onClick={() => fetchUserChatHistory(user.userid)}
              >
                <div className="user-name">{user.name || user.phone}</div>
                <div className="user-phone">{user.phone}</div>
              </div>
            ))
          )}
        </div>

        {selectedUser && (
          <div className="sessions-list">
            <h3>Chat Sessions</h3>
            {loading ? (
              <div className="loading">Loading sessions...</div>
            ) : sessions.length === 0 ? (
              <div className="no-sessions">No chat sessions found</div>
            ) : (
              sessions.map(session => (
                <div 
                  key={session.session_id}
                  className={`session-card ${selectedSession?.session_id === session.session_id ? 'active' : ''}`}
                  onClick={() => fetchSessionDetails(session.session_id)}
                >
                  <div className="session-date">{formatDate(session.created_at)}</div>
                  <div className="session-preview">{session.preview || 'Chat session'}</div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedSession && (
          <div className="session-details">
            <div className="session-header">
              <h3>Session Details</h3>
              <button onClick={() => setSelectedSession(null)}>×</button>
            </div>
            
            <div className="messages-container">
              {selectedSession.messages.map((message, index) => (
                <div key={index} className={`message ${message.sender}`}>
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
    </div>
  );
};

export default AdminChatHistory;