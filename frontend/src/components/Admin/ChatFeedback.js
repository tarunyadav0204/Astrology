import React, { useState, useEffect } from 'react';
import './ChatFeedback.css';

const ChatFeedback = () => {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});

  useEffect(() => {
    // Check if user is admin
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.role !== 'admin') {
      setError('Admin access required');
      setLoading(false);
      return;
    }
    
    fetchFeedbacks();
    fetchStats();
  }, []);

  const fetchFeedbacks = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Fetching feedback with token:', token ? 'Present' : 'Missing');
      
      const response = await fetch('/api/chat/feedback/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Feedback response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Feedback data received:', data);
        setFeedbacks(data.recent_feedback || []);
      } else {
        const errorText = await response.text();
        console.error('Feedback fetch failed:', response.status, errorText);
        setError(`Failed to fetch feedback data: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error fetching feedback data:', err);
      if (err.response) {
        console.error('Response status:', err.response.status);
        console.error('Response data:', err.response.data);
        setError(`Failed to fetch feedback data: ${err.response.status} ${err.response.statusText}`);
      } else {
        setError('Error loading feedback data: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/chat/feedback/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const renderStars = (rating) => {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) return <div className="loading">Loading feedback data...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="chat-feedback-container">
      <div className="feedback-header">
        <h2>Chat Feedback Analysis</h2>
        <div className="feedback-stats">
          <div className="stat-card">
            <h3>Total Feedback</h3>
            <p className="stat-number">{stats.total_feedback || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Average Rating</h3>
            <p className="stat-number">{stats.average_rating || 0}/5</p>
          </div>
          <div className="stat-card">
            <h3>Rating Distribution</h3>
            <div className="rating-dist">
              {Object.entries(stats.rating_distribution || {}).map(([rating, count]) => (
                <div key={rating} className="rating-item">
                  {rating}★: {count}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="feedback-table-container">
        <h3>Recent Feedback</h3>
        <table className="feedback-table">
          <thead>
            <tr>
              <th>User Name</th>
              <th>Rating</th>
              <th>Comment</th>
              <th>Created Time</th>
            </tr>
          </thead>
          <tbody>
            {feedbacks.length > 0 ? (
              feedbacks.map((feedback, index) => (
                <tr key={index}>
                  <td>{feedback.user_name || 'Anonymous'}</td>
                  <td className="rating-cell">
                    <span className="stars">{renderStars(feedback.rating)}</span>
                    <span className="rating-number">({feedback.rating}/5)</span>
                  </td>
                  <td className="comment-cell">
                    {feedback.comment || 'No comment'}
                  </td>
                  <td>{formatDate(feedback.created_at)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="no-data">No feedback data available</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ChatFeedback;