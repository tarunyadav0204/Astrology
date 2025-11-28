import React, { useState, useEffect } from 'react';
import './AdminCreditLedger.css';

const AdminCreditLedger = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

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
    if (source === 'feature_usage') {
      if (referenceId === 'chat') return 'Chat Question';
      if (referenceId === 'marriage_analysis') return 'Marriage Analysis';
      if (referenceId === 'wealth_analysis') return 'Wealth Analysis';
      return referenceId;
    }
    return source;
  };

  return (
    <div className="admin-credit-ledger">
      <div className="users-panel">
        <h3>Users</h3>
        <div className="users-list">
          {users.map(user => (
            <div
              key={user.userid}
              className={`user-item ${selectedUser?.userid === user.userid ? 'active' : ''}`}
              onClick={() => handleUserSelect(user)}
            >
              <div className="user-name">{user.name}</div>
              <div className="user-phone">{user.phone}</div>
              <div className="user-credits">💳 {user.credits}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="ledger-panel">
        {!selectedUser ? (
          <div className="no-selection">
            <p>Select a user to view their credit ledger</p>
          </div>
        ) : (
          <>
            <div className="ledger-header">
              <h3>{selectedUser.name}'s Credit Ledger</h3>
              <div className="current-balance">Current Balance: {selectedUser.credits} credits</div>
            </div>

            {loading ? (
              <div className="loading">Loading transactions...</div>
            ) : transactions.length === 0 ? (
              <div className="no-transactions">No transactions found</div>
            ) : (
              <div className="transactions-table">
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
                            {transaction.type === 'earned' ? '↑ Earned' : '↓ Spent'}
                          </span>
                        </td>
                        <td className="feature-cell">
                          {transaction.description || getFeatureName(transaction.source, transaction.source)}
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
          </>
        )}
      </div>
    </div>
  );
};

export default AdminCreditLedger;
