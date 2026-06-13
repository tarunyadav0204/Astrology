import React, { useState, useEffect, useCallback } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './ChatFeedback.css';

const PAGE_LIMIT = 10;

const ChatFeedback = () => {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [searchUsername, setSearchUsername] = useState('');
  const [searchRating, setSearchRating] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ username: '', rating: '' });

  const fetchFeedbacks = useCallback(async (signal) => {
    try {
      setLoading(true);

      const params = new URLSearchParams({
        page: String(page),
        limit: String(PAGE_LIMIT),
      });

      if (appliedFilters.username.trim()) {
        params.append('username', appliedFilters.username.trim());
      }

      if (appliedFilters.rating) {
        params.append('rating', appliedFilters.rating);
      }

      const response = await fetch(`/api/chat/feedback/stats?${params}`, {
        headers: getAdminAuthHeaders(),
        signal,
      });

      if (!response.ok) {
        setError(`Failed to fetch feedback data: ${response.status} ${response.statusText}`);
        return;
      }

      const data = await response.json();
      if (signal.aborted) return;

      setFeedbacks(data.feedback || []);
      setStats({
        total_feedback: data.total_feedback,
        average_rating: data.average_rating,
        rating_distribution: data.rating_distribution,
      });

      const rowTotal = Number(data.pagination?.total) || 0;
      const pages = Number(data.pagination?.pages) || (rowTotal > 0 ? Math.ceil(rowTotal / PAGE_LIMIT) : 0);
      setTotal(rowTotal);
      setTotalPages(pages);
      setError(null);
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError('Error loading feedback data: ' + err.message);
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [page, appliedFilters]);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.role !== 'admin') {
      setError('Admin access required');
      setLoading(false);
      return undefined;
    }

    const controller = new AbortController();
    fetchFeedbacks(controller.signal);
    return () => controller.abort();
  }, [fetchFeedbacks]);

  const handlePageChange = (newPage) => {
    if (newPage < 1 || (totalPages > 0 && newPage > totalPages)) return;
    setPage(newPage);
  };

  const handleSearch = () => {
    setAppliedFilters({ username: searchUsername, rating: searchRating });
    setPage(1);
  };

  const clearFilters = () => {
    setSearchUsername('');
    setSearchRating('');
    setAppliedFilters({ username: '', rating: '' });
    setPage(1);
  };

  const renderStars = (rating) => {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && page === 1 && feedbacks.length === 0) {
    return <div className="loading">Loading feedback data...</div>;
  }
  if (error) return <div className="error">{error}</div>;

  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_LIMIT + 1;
  const rangeEnd = Math.min(page * PAGE_LIMIT, total);

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
            Showing {rangeStart}-{rangeEnd} of {total}
          </div>
        </div>

        {loading && page > 1 ? (
          <div className="loading">Loading page…</div>
        ) : (
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
        )}

        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1 || loading}
              className="page-btn"
            >
              Previous
            </button>

            {[...Array(totalPages)].map((_, i) => {
              const pageNum = i + 1;
              if (pageNum === 1 || pageNum === totalPages || (pageNum >= page - 2 && pageNum <= page + 2)) {
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    disabled={loading}
                    className={`page-btn ${pageNum === page ? 'active' : ''}`}
                  >
                    {pageNum}
                  </button>
                );
              }
              if (pageNum === page - 3 || pageNum === page + 3) {
                return <span key={pageNum} className="page-ellipsis">...</span>;
              }
              return null;
            })}

            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === totalPages || loading}
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
