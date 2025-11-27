import React, { useState, useEffect } from 'react';
import './CreditLedger.css';

const CreditLedger = ({ user }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTransactionHistory();
  }, []);

  const fetchTransactionHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/api/credits/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTransactions(data.transactions);
      }
    } catch (error) {
      console.error('Error fetching transaction history:', error);
    } finally {
      setLoading(false);
    }
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
    if (source === 'promo_code') return `Promo Code`;
    if (source === 'admin_adjustment') return 'Admin Adjustment';
    if (source === 'feature_usage') {
      if (referenceId === 'chat') return 'Chat Question';
      if (referenceId === 'marriage_analysis') return 'Marriage Analysis';
      if (referenceId === 'wealth_analysis') return 'Wealth Analysis';
      return referenceId;
    }
    return source;
  };

  if (loading) {
    return (
      <div className="credit-ledger">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading credit history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="credit-ledger">
      {transactions.length === 0 ? (
        <div className="no-transactions">
          <div className="no-transactions-icon">📊</div>
          <h3>No Transactions Yet</h3>
          <p>Your credit transactions will appear here.</p>
        </div>
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
    </div>
  );
};

export default CreditLedger;
