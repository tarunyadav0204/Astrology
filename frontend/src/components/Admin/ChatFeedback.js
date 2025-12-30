import React, { useState, useEffect } from 'react';
import './ChatFeedback.css';

const ChatFeedback = () => {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});
  const [pagination, setPagination] = useState({ page: 1, limit: 10, total: 0, pages: 0 });
  const [searchUsername, setSearchUsername] = useState('');
  const [searchRating, setSearchRating] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ username: '', rating: '' });

  useEffect(() => {
    // Check if user is admin
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.role !== 'admin') {
      setError('Admin access required');
      setLoading(false);
      return;
    }
    
    fetchFeedbacks();
  }, [pagination.page, appliedFilters]);

  const fetchFeedbacks = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        limit: pagination.limit.toString()
      });
      
      if (appliedFilters.username.trim()) {
        params.append('username', appliedFilters.username.trim());
      }
      
      if (appliedFilters.rating) {
        params.append('rating', appliedFilters.rating);
      }
      
      const response = await fetch(`/api/chat/feedback/stats?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFeedbacks(data.feedback || []);
        setStats({
          total_feedback: data.total_feedback,
          average_rating: data.average_rating,
          rating_distribution: data.rating_distribution
        });
        setPagination(prev => ({
          ...prev,
          total: data.pagination.total,
          pages: data.pagination.pages
        }));
      } else {
        setError(`Failed to fetch feedback data: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      setError('Error loading feedback data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  };

  const handleSearch = () => {
    setAppliedFilters({ username: searchUsername, rating: searchRating });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const clearFilters = () => {
    setSearchUsername('');
    setSearchRating('');
    setAppliedFilters({ username: '', rating: '' });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const renderStars = (rating) => {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && pagination.page === 1) return <div className="loading">Loading feedback data...</div>;
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

      <div className="feedback-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search by username..."
            value={searchUsername}
            onChange={(e) => setSearchUsername(e.target.value)}
            className="search-input"
          />
          <select
            value={searchRating}
            onChange={(e) => setSearchRating(e.target.value)}
            className="rating-filter"
          >
            <option value="">All Ratings</option>
            <option value="5">5 Stars</option>
            <option value="4">4 Stars</option>
            <option value="3">3 Stars</option>
            <option value="2">2 Stars</option>
            <option value="1">1 Star</option>
          </select>
          <button onClick={handleSearch} className="search-btn">Search</button>
          <button onClick={clearFilters} className="clear-btn">Clear</button>
        </div>
      </div>

      <div className="feedback-table-container">
        <div className="table-header">
          <h3>Feedback Results</h3>
          <div className="pagination-info">
            Showing {((pagination.page - 1) * pagination.limit) + 1}-{Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total}
          </div>
        </div>
        
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

        {pagination.pages > 1 && (
          <div className="pagination">
            <button 
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
              className="page-btn"
            >
              Previous
            </button>
            
            {[...Array(pagination.pages)].map((_, i) => {
              const page = i + 1;
              if (page === 1 || page === pagination.pages || (page >= pagination.page - 2 && page <= pagination.page + 2)) {
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`page-btn ${page === pagination.page ? 'active' : ''}`}
                  >
                    {page}
                  </button>
                );
              } else if (page === pagination.page - 3 || page === pagination.page + 3) {
                return <span key={page} className="page-ellipsis">...</span>;
              }
              return null;
            })}
            
            <button 
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page === pagination.pages}
              className="page-btn"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatFeedback;