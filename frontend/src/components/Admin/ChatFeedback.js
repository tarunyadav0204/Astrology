import React, { useState, useEffect, useCallback } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './ChatFeedback.css';

const PAGE_LIMIT = 10;
const RATING_ORDER = ['5', '4', '3', '2', '1'];

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
    const n = Math.max(0, Math.min(5, Number(rating) || 0));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && page === 1 && feedbacks.length === 0) {
    return <div className="chat-feedback-standalone-loading">Loading feedback data…</div>;
  }
  if (error) return <div className="chat-feedback-standalone-error">{error}</div>;

  const distribution = stats.rating_distribution || {};
  const avg = Number(stats.average_rating);
  const avgDisplay = Number.isFinite(avg) ? avg.toFixed(2) : '—';

  return (
    <div className="chat-feedback-container">
      <div className="feedback-toolbar">
        <div className="feedback-meta">
          <strong>{stats.total_feedback || 0}</strong> feedback
          <span className="feedback-meta-sep">·</span>
          avg <strong>{avgDisplay}</strong>
        </div>
        <div className="feedback-rating-row" aria-label="Rating distribution">
          {RATING_ORDER.map((rating) => {
            const count = Number(distribution[rating] || 0);
            return (
              <div key={rating} className="feedback-rating-chip">
                <span className="cf-rating-stars" aria-hidden="true">
                  {renderStars(Number(rating))}
                </span>
                <span className="cf-rating-count">{count}</span>
              </div>
            );
          })}
        </div>
        <div className="filter-group">
          <input
            type="text"
            placeholder="Username…"
            value={searchUsername}
            onChange={(e) => setSearchUsername(e.target.value)}
            className="search-input"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
          />
          <select
            value={searchRating}
            onChange={(e) => setSearchRating(e.target.value)}
            className="rating-filter"
          >
            <option value="">All ratings</option>
            <option value="5">5 stars</option>
            <option value="4">4 stars</option>
            <option value="3">3 stars</option>
            <option value="2">2 stars</option>
            <option value="1">1 star</option>
          </select>
          <button type="button" onClick={handleSearch} className="search-btn">Search</button>
          <button type="button" onClick={clearFilters} className="clear-btn">Clear</button>
        </div>
      </div>

      <div className="feedback-table-container">
        {loading && page > 1 ? (
          <div className="loading">Loading page…</div>
        ) : (
          <table className="feedback-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Phone</th>
                <th>Question</th>
                <th>Rating</th>
                <th>Comment</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {feedbacks.length > 0 ? (
                feedbacks.map((feedback, index) => (
                  <tr key={feedback.id || `${feedback.created_at}-${index}`}>
                    <td>{feedback.user_name || 'Anonymous'}</td>
                    <td>{feedback.user_phone || '—'}</td>
                    <td className="question-cell">
                      {feedback.question || 'Question not found'}
                    </td>
                    <td className="rating-cell">
                      <span className="cf-rating-stars" aria-hidden="true">
                        {renderStars(feedback.rating)}
                      </span>
                      <span className="rating-number">{feedback.rating}/5</span>
                    </td>
                    <td className="comment-cell">
                      {feedback.comment || '—'}
                    </td>
                    <td>{formatDate(feedback.created_at)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="no-data">No feedback data available</td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {totalPages > 1 && (
          <div className="chat-feedback-pagination" role="navigation" aria-label="Chat feedback pages">
            <button
              type="button"
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1 || loading}
              className="chat-feedback-page-btn"
            >
              Previous
            </button>

            {[...Array(totalPages)].map((_, i) => {
              const pageNum = i + 1;
              if (pageNum === 1 || pageNum === totalPages || (pageNum >= page - 2 && pageNum <= page + 2)) {
                return (
                  <button
                    type="button"
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    disabled={loading}
                    className={`chat-feedback-page-btn ${pageNum === page ? 'active' : ''}`}
                  >
                    {pageNum}
                  </button>
                );
              }
              if (pageNum === page - 3 || pageNum === page + 3) {
                return <span key={pageNum} className="chat-feedback-page-ellipsis">…</span>;
              }
              return null;
            })}

            <button
              type="button"
              onClick={() => handlePageChange(page + 1)}
              disabled={page === totalPages || loading}
              className="chat-feedback-page-btn"
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
