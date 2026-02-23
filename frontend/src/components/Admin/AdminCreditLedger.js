import React, { useState, useEffect } from 'react';
import './AdminCreditLedger.css';

const AdminCreditLedger = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchFromDate, setSearchFromDate] = useState('');
  const [searchToDate, setSearchToDate] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [searchRange, setSearchRange] = useState({ from_date: null, to_date: null });

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async (fromDate = '', toDate = '', query = '') => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (query.trim()) params.append('query', query.trim());
      const response = await fetch(`/api/credits/admin/search?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error(`Search failed with status ${response.status}`);
      const data = await response.json();
      setSearchResults(data.transactions || []);
      setSearchRange({ from_date: data.from_date || null, to_date: data.to_date || null });
    } catch (err) {
      console.error('Error loading transactions:', err);
      setSearchError('Failed to load transactions. Please try again.');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearch = () => {
    loadTransactions(searchFromDate, searchToDate, searchQuery);
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/credits/admin/users', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchUserTransactions = async (userid) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/credits/admin/user-history/${userid}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = (user) => {
    setSelectedUser(user);
    fetchUserTransactions(user.userid);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFeatureName = (source, referenceId) => {
    if (source === 'promo_code') return 'Promo Code';
    if (source === 'admin_adjustment') return 'Admin Adjustment';
    if (source === 'credit_request_approval') return 'Credit Request Approved';
    if (source === 'feature_usage') {
      const names = {
        chat_question: 'Chat Question',
        marriage_analysis: 'Marriage Analysis',
        wealth_analysis: 'Wealth Analysis',
        health_analysis: 'Health Analysis',
        education_analysis: 'Education Analysis',
        career_analysis: 'Career Analysis',
        progeny_analysis: 'Progeny Analysis',
        trading_daily: 'Trading Daily',
        trading_calendar: 'Trading Calendar',
        childbirth_planner: 'Childbirth Planner',
        vehicle_purchase: 'Vehicle Purchase Muhurat',
        griha_pravesh: 'Griha Pravesh',
        gold_purchase: 'Gold Purchase Muhurat',
        business_opening: 'Business Opening Muhurat',
        event_timeline: 'Event Timeline',
        partnership_analysis: 'Partnership Analysis',
        karma_analysis: 'Karma Analysis',
        mundane_chat: 'Mundane Chat',
      };
      return names[referenceId] || referenceId || 'Feature';
    }
    return source;
  };

  const showUserLedger = selectedUser;

  return (
    <div className="admin-credit-ledger">
      <aside className="users-panel">
        <h3>View ledger</h3>
        <p className="users-hint">Click a user to see their transaction history below.</p>
        <div className="users-list">
          {users.map(user => (
            <button
              type="button"
              key={user.userid}
              className={`user-item ${selectedUser?.userid === user.userid ? 'active' : ''}`}
              onClick={() => handleUserSelect(user)}
            >
              <span className="user-name">{user.name}</span>
              <span className="user-meta">{user.phone} · {user.credits} cr</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="ledger-main">
        <section className="search-bar">
          <div className="search-row">
            <label>
              <span className="label-text">From</span>
              <input
                type="date"
                value={searchFromDate}
                onChange={(e) => setSearchFromDate(e.target.value)}
              />
            </label>
            <label>
              <span className="label-text">To</span>
              <input
                type="date"
                value={searchToDate}
                onChange={(e) => setSearchToDate(e.target.value)}
              />
            </label>
            <label>
              <span className="label-text">Name / Phone</span>
              <input
                type="text"
                placeholder="Optional filter..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </label>
            <button className="search-btn" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? 'Searching…' : 'Search'}
            </button>
          </div>
          <p className="search-hint">Default: last 30 days when dates are empty.</p>
          {searchError && <div className="search-error">{searchError}</div>}
        </section>

        <section className="ledger-content">
          {searchLoading && (
            <div className="loading">Loading transactions…</div>
          )}
          {!searchLoading && (
            <div className="results-block">
              <h2 className="results-title">
                Transactions ({searchResults.length})
                {searchRange.from_date && searchRange.to_date && (
                  <span className="results-range">
                    {' '}· {formatDate(searchRange.from_date)} – {formatDate(searchRange.to_date)}
                  </span>
                )}
                {searchQuery.trim() && (
                  <span className="results-filter"> · matching &quot;{searchQuery.trim()}&quot;</span>
                )}
              </h2>
              {searchResults.length > 0 ? (
              <div className="transactions-table wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>User</th>
                      <th>Phone</th>
                      <th>Type</th>
                      <th>Feature</th>
                      <th>Amount</th>
                      <th>Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((tx) => (
                      <tr key={tx.id} className={tx.type}>
                        <td className="date-cell">{formatDate(tx.created_at)}</td>
                        <td>{tx.user_name}</td>
                        <td>{tx.user_phone}</td>
                        <td className="type-cell">
                          <span className={`type-badge ${tx.type}`}>
                            {tx.type === 'earned' || tx.type === 'refund' ? '↑ Earned' : '↓ Spent'}
                          </span>
                        </td>
                        <td className="feature-cell">
                          {tx.description || getFeatureName(tx.source, tx.reference_id)}
                        </td>
                        <td className={`amount-cell ${tx.type}`}>
                          {tx.amount > 0 ? `+${tx.amount}` : tx.amount}
                        </td>
                        <td className="balance-cell">{tx.balance_after}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              ) : (
                <p className="no-results-msg">No transactions for this period. Adjust dates or name/phone and click Search.</p>
              )}
            </div>
          )}

          {showUserLedger && (
            <div className="user-ledger-block">
              <div className="user-ledger-header">
                <h2 className="user-ledger-title">{selectedUser.name}'s ledger</h2>
                <button type="button" className="clear-selection" onClick={() => setSelectedUser(null)}>
                  Clear selection
                </button>
                <span className="current-balance">{selectedUser.credits} credits</span>
              </div>
              {loading ? (
                <div className="loading">Loading…</div>
              ) : transactions.length === 0 ? (
                <div className="no-transactions">No transactions for this user.</div>
              ) : (
                <div className="transactions-table wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Feature</th>
                        <th>Amount</th>
                        <th>Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((transaction, index) => (
                        <tr key={index} className={transaction.type}>
                          <td className="date-cell">{formatDate(transaction.date)}</td>
                          <td className="type-cell">
<span className={`type-badge ${transaction.type}`}>
                            {transaction.type === 'earned' || transaction.type === 'refund' ? '↑ Earned' : '↓ Spent'}
                          </span>
                          </td>
                          <td className="feature-cell">
                            {transaction.description || getFeatureName(transaction.source, transaction.reference_id)}
                          </td>
                          <td className={`amount-cell ${transaction.type}`}>
                            {transaction.type === 'earned' ? '+' : ''}{transaction.amount}
                          </td>
                          <td className="balance-cell">{transaction.balance_after}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

        </section>
      </main>
    </div>
  );
};

export default AdminCreditLedger;
