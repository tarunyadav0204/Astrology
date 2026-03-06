import React, { useState, useEffect, useCallback } from 'react';
import './AdminUserCreditManagement.css';

const PAGE_SIZE = 50;

const AdminUserCreditManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [withCreditsOnly, setWithCreditsOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [adjustModal, setAdjustModal] = useState(null); // { user, type: 'add'|'remove', amount: '', description: '' }
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set('search', search.trim());
      if (withCreditsOnly) params.set('with_credits_only', 'true');
      params.set('page', String(page));
      params.set('limit', String(PAGE_SIZE));
      const response = await fetch(`/api/credits/admin/users?${params.toString()}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data.users || []);
      setTotal(data.total ?? 0);
    } catch (err) {
      console.error(err);
      setUsers([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [search, withCreditsOnly, page]);

  useEffect(() => {
    setPage(1);
  }, [search, withCreditsOnly]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const openAdd = (user) => setAdjustModal({ user, type: 'add', amount: '', description: '' });
  const openRemove = (user) => setAdjustModal({ user, type: 'remove', amount: '', description: '' });
  const closeModal = () => {
    setAdjustModal(null);
    setMessage(null);
  };

  const handleAdjust = async () => {
    if (!adjustModal) return;
    const amount = parseInt(adjustModal.amount, 10);
    if (!Number.isInteger(amount) || amount <= 0) {
      setMessage('Please enter a positive number for amount.');
      return;
    }
    if (adjustModal.type === 'remove' && amount > (adjustModal.user.credits || 0)) {
      setMessage(`User only has ${adjustModal.user.credits} credits. Cannot remove more.`);
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const body = {
        userid: adjustModal.user.userid,
        amount: adjustModal.type === 'add' ? amount : -amount,
        description: adjustModal.description.trim() || 'Admin adjustment',
      };
      const response = await fetch('/api/credits/admin/adjust-credits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Adjustment failed');
      setMessage(data.message || 'Done.');
      setTimeout(() => {
        closeModal();
        fetchUsers();
      }, 800);
    } catch (err) {
      setMessage(err.message || 'Failed to adjust credits.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="admin-user-credit-management">
      <h2>User Credit Management</h2>
      <p className="section-hint">Search users and add or remove credits. Changes are recorded in the ledger.</p>

      <div className="filters-row">
        <div className="form-field search-field">
          <label>Search by name or phone</label>
          <input
            type="text"
            placeholder="Type to filter..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <label className="toggle-with-credits">
          <input
            type="checkbox"
            checked={withCreditsOnly}
            onChange={(e) => setWithCreditsOnly(e.target.checked)}
          />
          Only show users with credits
        </label>
        <button type="button" className="create-btn" onClick={() => fetchUsers()} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {loading && <div className="loading-row">Loading users…</div>}
      {!loading && (
        <div className="users-table-wrap">
          <table className="users-credits-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Credits</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={4}>No users match the filters.</td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.userid}>
                    <td>{user.name || '—'}</td>
                    <td>{user.phone || '—'}</td>
                    <td className="credits-cell">{user.credits ?? 0}</td>
                    <td className="actions-cell">
                      <button type="button" className="btn-add" onClick={() => openAdd(user)}>
                        Add
                      </button>
                      <button
                        type="button"
                        className="btn-remove"
                        onClick={() => openRemove(user)}
                        disabled={!(user.credits > 0)}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          {total > 0 && (
            <div className="pagination-row">
              <span className="pagination-info">
                Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total}
              </span>
              <div className="pagination-buttons">
                <button
                  type="button"
                  className="pagination-btn"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || loading}
                >
                  Previous
                </button>
                <span className="pagination-page">Page {page} of {Math.ceil(total / PAGE_SIZE) || 1}</span>
                <button
                  type="button"
                  className="pagination-btn"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * PAGE_SIZE >= total || loading}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {adjustModal && (
        <div className="adjust-modal-overlay" onClick={closeModal}>
          <div className="adjust-modal" onClick={(e) => e.stopPropagation()}>
            <h3>
              {adjustModal.type === 'add' ? 'Add' : 'Remove'} credits — {adjustModal.user.name || adjustModal.user.phone}
            </h3>
            <p className="current-balance">Current balance: {adjustModal.user.credits ?? 0} credits</p>
            <div className="form-field">
              <label>Amount (positive number)</label>
              <input
                type="number"
                min="1"
                step="1"
                placeholder={adjustModal.type === 'remove' ? `Max ${adjustModal.user.credits ?? 0}` : 'e.g. 50'}
                value={adjustModal.amount}
                onChange={(e) => setAdjustModal((m) => ({ ...m, amount: e.target.value }))}
              />
            </div>
            <div className="form-field">
              <label>Reason (optional)</label>
              <input
                type="text"
                placeholder="Admin adjustment"
                value={adjustModal.description}
                onChange={(e) => setAdjustModal((m) => ({ ...m, description: e.target.value }))}
              />
            </div>
            {message && <div className={`modal-message ${message.includes('Successfully') ? 'success' : 'error'}`}>{message}</div>}
            <div className="modal-actions">
              <button type="button" className="create-btn" onClick={handleAdjust} disabled={submitting}>
                {submitting ? 'Saving…' : adjustModal.type === 'add' ? 'Add credits' : 'Remove credits'}
              </button>
              <button type="button" className="cancel-btn" onClick={closeModal}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUserCreditManagement;
