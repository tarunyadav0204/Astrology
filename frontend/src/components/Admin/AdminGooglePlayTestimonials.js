import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const STATUS_OPTIONS = ['all', 'pending', 'approved', 'hidden'];

const getJsonOrThrow = async (response, fallbackMessage) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || fallbackMessage);
  }
  return data;
};

function Stars({ rating }) {
  return <span className="admin-testimonial-stars">{'★'.repeat(Number(rating) || 0)}</span>;
}

export default function AdminGooglePlayTestimonials() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('all');
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMode, setSyncMode] = useState('');
  const [message, setMessage] = useState('');
  const [drafts, setDrafts] = useState({});
  const [nextPageToken, setNextPageToken] = useState('');
  const [minRating, setMinRating] = useState(4);

  const counts = useMemo(() => {
    return items.reduce(
      (acc, item) => {
        acc[item.status] = (acc[item.status] || 0) + 1;
        acc.all += 1;
        return acc;
      },
      { all: 0, pending: 0, approved: 0, hidden: 0 }
    );
  }, [items]);

  const visibleItems = useMemo(() => {
    if (status === 'all') return items;
    return items.filter((item) => item.status === status);
  }, [items, status]);

  const loadTestimonials = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch('/api/admin/testimonials?status=all', {
        headers: getAdminAuthHeaders(),
      });
      const data = await getJsonOrThrow(response, 'Failed to load testimonials');
      setItems(data.testimonials || []);
      setDrafts(
        (data.testimonials || []).reduce((acc, item) => {
          acc[item.id] = {
            display_name: item.display_name || '',
            display_location: item.display_location || '',
            display_order: item.display_order || 0,
          };
          return acc;
        }, {})
      );
    } catch (error) {
      setMessage(error.message || 'Failed to load testimonials');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTestimonials();
  }, [loadTestimonials]);

  const syncReviews = async ({ mode, pageToken = '', pages = 1 }) => {
    setSyncing(true);
    setSyncMode(mode);
    setMessage('');
    try {
      const response = await fetch('/api/admin/testimonials/sync', {
        method: 'POST',
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_results: 100,
          min_rating: Number(minRating) || 4,
          page_token: pageToken || null,
          pages,
        }),
      });
      const data = await getJsonOrThrow(response, 'Failed to fetch Google Play reviews');
      setNextPageToken(data.next_page_token || '');
      setMessage(
        `Fetched ${data.fetched} reviews across ${data.pages_fetched || 1} page(s): ${data.inserted} new, ${data.updated} updated, ${data.skipped} skipped.${data.next_page_token ? ' More reviews are available.' : ''}`
      );
      await loadTestimonials();
    } catch (error) {
      setMessage(error.message || 'Failed to fetch Google Play reviews');
    } finally {
      setSyncing(false);
      setSyncMode('');
    }
  };

  const patchItem = async (id, patch) => {
    const response = await fetch(`/api/admin/testimonials/${id}`, {
      method: 'PATCH',
      headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    const data = await getJsonOrThrow(response, 'Failed to update testimonial');
    setItems((prev) => prev.map((item) => (item.id === id ? data.testimonial : item)));
    setDrafts((prev) => ({
      ...prev,
      [id]: {
        display_name: data.testimonial.display_name || '',
        display_location: data.testimonial.display_location || '',
        display_order: data.testimonial.display_order || 0,
      },
    }));
    return data.testimonial;
  };

  const updateDraft = (id, key, value) => {
    setDrafts((prev) => ({ ...prev, [id]: { ...(prev[id] || {}), [key]: value } }));
  };

  const saveDisplay = async (item) => {
    const draft = drafts[item.id] || {};
    setMessage('');
    try {
      await patchItem(item.id, {
        display_name: draft.display_name || null,
        display_location: draft.display_location || null,
        display_order: Number(draft.display_order) || 0,
      });
      setMessage('Display fields saved.');
    } catch (error) {
      setMessage(error.message || 'Failed to save display fields');
    }
  };

  const setItemStatus = async (item, nextStatus) => {
    setMessage('');
    try {
      await patchItem(item.id, { status: nextStatus });
      setMessage(nextStatus === 'approved' ? 'Testimonial approved for homepage.' : 'Testimonial updated.');
    } catch (error) {
      setMessage(error.message || 'Failed to update testimonial');
    }
  };

  return (
    <div className="admin-testimonials">
      <div className="admin-testimonials-header">
        <div>
          <h2>Google Play Testimonials</h2>
          <p>Fetch latest Google Play reviews, approve selected ones, and control how they appear on the homepage.</p>
        </div>
        <div className="admin-testimonials-fetch-actions">
          <label className="admin-testimonials-min-rating">
            Min rating
            <select value={minRating} onChange={(e) => setMinRating(Number(e.target.value))} disabled={syncing}>
              <option value={5}>5★</option>
              <option value={4}>4★+</option>
              <option value={3}>3★+</option>
              <option value={2}>2★+</option>
              <option value={1}>1★+</option>
            </select>
          </label>
          <button
            type="button"
            className="admin-testimonials-sync-btn"
            onClick={() => syncReviews({ mode: 'latest', pages: 1 })}
            disabled={syncing}
          >
            {syncing && syncMode === 'latest' ? 'Fetching...' : 'Fetch latest reviews'}
          </button>
          <button
            type="button"
            className="admin-testimonials-sync-btn secondary"
            onClick={() => syncReviews({ mode: 'more', pageToken: nextPageToken, pages: 1 })}
            disabled={syncing || !nextPageToken}
            title={nextPageToken ? 'Fetch the next Google Play reviews page' : 'Fetch latest reviews first'}
          >
            {syncing && syncMode === 'more' ? 'Fetching...' : 'Fetch more reviews'}
          </button>
          <button
            type="button"
            className="admin-testimonials-sync-btn secondary"
            onClick={() => syncReviews({ mode: 'all', pageToken: nextPageToken, pages: 10 })}
            disabled={syncing}
            title="Fetch up to 10 Google Play pages from the current position"
          >
            {syncing && syncMode === 'all' ? 'Fetching...' : 'Fetch all available'}
          </button>
        </div>
      </div>

      <div className="admin-testimonials-toolbar">
        {STATUS_OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            className={`admin-testimonials-filter ${status === option ? 'active' : ''}`}
            onClick={() => setStatus(option)}
          >
            {option} <span>{counts[option] || 0}</span>
          </button>
        ))}
      </div>

      {message && <div className="admin-testimonials-message">{message}</div>}
      {loading ? (
        <div className="loading">Loading testimonials...</div>
      ) : (
        <div className="admin-testimonials-list">
          {visibleItems.length === 0 ? (
            <div className="users-table-empty">No testimonials in this view.</div>
          ) : (
            visibleItems.map((item) => {
              const draft = drafts[item.id] || {};
              return (
                <article key={item.id} className={`admin-testimonial-row status-${item.status}`}>
                  <div className="admin-testimonial-main">
                    <div className="admin-testimonial-meta">
                      <strong>{item.author_name || 'Google Play user'}</strong>
                      <Stars rating={item.rating} />
                      <span className={`admin-testimonial-status ${item.status}`}>{item.status}</span>
                      {item.app_version_name && <span>v{item.app_version_name}</span>}
                    </div>
                    <p>{item.review_text}</p>
                    <small>
                      Review ID: {item.external_review_id}
                      {item.review_updated_at ? ` • Updated ${new Date(item.review_updated_at).toLocaleDateString()}` : ''}
                    </small>
                  </div>

                  <div className="admin-testimonial-display">
                    <label>
                      Display name
                      <input
                        value={draft.display_name || ''}
                        placeholder={item.author_name || 'Google Play user'}
                        onChange={(e) => updateDraft(item.id, 'display_name', e.target.value)}
                      />
                    </label>
                    <label>
                      Display location
                      <input
                        value={draft.display_location || ''}
                        placeholder="Google Play review"
                        onChange={(e) => updateDraft(item.id, 'display_location', e.target.value)}
                      />
                    </label>
                    <label>
                      Order
                      <input
                        type="number"
                        value={draft.display_order ?? 0}
                        onChange={(e) => updateDraft(item.id, 'display_order', e.target.value)}
                      />
                    </label>
                  </div>

                  <div className="admin-testimonial-actions">
                    <button type="button" className="save-btn" onClick={() => saveDisplay(item)}>
                      Save
                    </button>
                    {item.status !== 'approved' && (
                      <button type="button" className="approve-btn" onClick={() => setItemStatus(item, 'approved')}>
                        Approve
                      </button>
                    )}
                    {item.status !== 'hidden' && (
                      <button type="button" className="delete-btn" onClick={() => setItemStatus(item, 'hidden')}>
                        Hide
                      </button>
                    )}
                    {item.status !== 'pending' && (
                      <button type="button" className="cancel-btn" onClick={() => setItemStatus(item, 'pending')}>
                        Pending
                      </button>
                    )}
                  </div>
                </article>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
