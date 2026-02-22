import React, { useState, useEffect } from 'react';
import './AdminCreditLedger.css';

const FEATURE_NAMES = {
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

function getActivityLabel(source, referenceId, description) {
  if (source === 'promo_code') return 'Promo Code';
  if (source === 'admin_adjustment') return 'Admin Adjustment';
  if (source === 'credit_request_approval') return 'Credit Request Approved';
  if (source === 'feature_usage') {
    return FEATURE_NAMES[referenceId] || referenceId || 'Feature';
  }
  return description || source;
}

export default function AdminDailyActivity() {
  const [date, setDate] = useState(() => {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  });
  const [data, setData] = useState({ date: '', transactions: [], summary: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/credits/admin/daily-activity?date=${date}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
      .then((res) => res.json())
      .then((body) => {
        if (!cancelled) {
          setData({
            date: body.date || date,
            transactions: body.transactions || [],
            summary: body.summary || {},
          });
        }
      })
      .catch(() => {
        if (!cancelled) setData({ date, transactions: [], summary: {} });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [date]);

  const formatTime = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const { transactions, summary } = data;

  return (
    <div className="admin-credit-ledger admin-daily-activity">
      <div className="ledger-panel" style={{ width: '100%' }}>
        <h2>Daily credit activity</h2>
        <div className="daily-activity-controls">
          <label>
            Date:{' '}
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              max={new Date().toISOString().slice(0, 10)}
            />
          </label>
        </div>
        {summary && (summary.total_earned > 0 || summary.total_spent > 0 || summary.count > 0) && (
          <div className="daily-summary">
            <span className="summary-earned">↑ Earned: {summary.total_earned || 0} credits</span>
            <span className="summary-spent">↓ Spent: {summary.total_spent || 0} credits</span>
            <span className="summary-count">{summary.count || 0} transactions</span>
          </div>
        )}
        {loading ? (
          <div className="loading">Loading…</div>
        ) : transactions.length === 0 ? (
          <div className="no-transactions">No transactions on this date.</div>
        ) : (
          <div className="transactions-table">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>User</th>
                  <th>Activity</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Balance after</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => (
                  <tr key={t.id} className={t.type}>
                    <td className="date-cell">{formatTime(t.created_at)}</td>
                    <td className="user-cell">
                      <div className="user-name">{t.user_name || '—'}</div>
                      <div className="user-phone">{t.user_phone || '—'}</div>
                    </td>
                    <td className="feature-cell">
                      {getActivityLabel(t.source, t.reference_id, t.description)}
                    </td>
                    <td className="type-cell">
                      <span className={`type-badge ${t.type}`}>
                        {t.type === 'earned' || t.type === 'refund' ? '↑ Earned' : '↓ Spent'}
                      </span>
                    </td>
                    <td className="amount-cell">{t.amount > 0 ? `+${t.amount}` : t.amount}</td>
                    <td className="balance-cell">{t.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
