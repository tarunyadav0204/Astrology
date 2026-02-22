import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Line,
  Area,
  ComposedChart,
} from 'recharts';

const ACTIVITY_LABELS = {
  chat_question: 'Chat',
  marriage_analysis: 'Marriage',
  wealth_analysis: 'Wealth',
  health_analysis: 'Health',
  education_analysis: 'Education',
  career_analysis: 'Career',
  progeny_analysis: 'Progeny',
  trading_daily: 'Trading Daily',
  trading_calendar: 'Trading Calendar',
  childbirth_planner: 'Childbirth',
  vehicle_purchase: 'Vehicle Muhurat',
  griha_pravesh: 'Griha Pravesh',
  gold_purchase: 'Gold Purchase',
  business_opening: 'Business Opening',
  event_timeline: 'Event Timeline',
  partnership_analysis: 'Partnership',
  karma_analysis: 'Karma',
  mundane_chat: 'Mundane Chat',
  other: 'Other',
};

function getActivityLabel(activity) {
  return ACTIVITY_LABELS[activity] || activity || 'Other';
}

function getDateRange(preset) {
  const today = new Date();
  const y = today.getFullYear();
  const m = today.getMonth();
  const d = today.getDate();
  const to = new Date(y, m, d);
  let from;

  switch (preset) {
    case 'this_month':
      from = new Date(y, m, 1);
      break;
    case 'past_3_months':
      from = new Date(y, m - 2, 1);
      break;
    case 'this_week': {
      const day = today.getDay();
      const sun = day === 0 ? 0 : -day;
      from = new Date(today);
      from.setDate(today.getDate() + sun);
      from.setHours(0, 0, 0, 0);
      break;
    }
    case 'last_week': {
      const day = today.getDay();
      const sun = day === 0 ? -7 : -day - 7;
      from = new Date(today);
      from.setDate(today.getDate() + sun);
      from.setHours(0, 0, 0, 0);
      to.setDate(today.getDate() + (day === 0 ? -1 : -day));
      to.setHours(23, 59, 59, 999);
      break;
    }
    case 'ytd':
      from = new Date(y, 0, 1);
      break;
    default:
      from = new Date(y, m, 1);
  }

  return {
    from_date: from.toISOString().slice(0, 10),
    to_date: to.toISOString().slice(0, 10),
  };
}

const PRESET_LABELS = {
  this_month: 'This month',
  past_3_months: 'Past 3 months',
  this_week: 'This week',
  last_week: 'Last week',
  ytd: 'YTD',
  custom: 'Custom',
};

const COLORS = ['#ff6b35', '#f7931e', '#ffd700', '#4CAF50', '#2196F3', '#9C27B0', '#00BCD4', '#795548', '#607D8B', '#E91E63'];

export default function AdminCreditsDashboard() {
  const [preset, setPreset] = useState('this_month');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const { from_date, to_date } = preset === 'custom'
      ? { from_date: fromDate, to_date: toDate }
      : getDateRange(preset);
    if (preset === 'custom' && (!from_date || !to_date)) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ from_date, to_date });
    fetch(`/api/credits/admin/dashboard?${params}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    })
      .then((res) => res.json())
      .then((body) => {
        setData(body);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load dashboard');
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [preset, fromDate, toDate]);

  // Sync custom dates when switching to custom
  useEffect(() => {
    if (preset === 'custom' && !fromDate) {
      const r = getDateRange('this_month');
      setFromDate(r.from_date);
      setToDate(r.to_date);
    }
  }, [preset]);

  if (loading && !data) {
    return <div className="credits-dashboard-loading">Loading dashboard…</div>;
  }
  if (error) {
    return <div className="credits-dashboard-error">{error}</div>;
  }

  const summary = data?.summary || {};
  const topUsers = data?.top_users_by_activity || [];
  const distribution = (data?.distribution_by_activity || []).map((item) => ({
    ...item,
    name: getActivityLabel(item.activity),
  }));
  const timeSeries = data?.time_series || [];

  const topUsersChart = topUsers.map((u) => ({
    name: u.user_name || u.user_phone || `User ${u.userid}`,
    count: u.transaction_count,
  }));

  return (
    <div className="credits-dashboard">
      <h2>Credits dashboard</h2>

      <div className="dashboard-controls">
        <div className="preset-buttons">
          {['this_month', 'past_3_months', 'this_week', 'last_week', 'ytd', 'custom'].map((key) => (
            <button
              key={key}
              type="button"
              className={`preset-btn ${preset === key ? 'active' : ''}`}
              onClick={() => setPreset(key)}
            >
              {PRESET_LABELS[key]}
            </button>
          ))}
        </div>
        {preset === 'custom' && (
          <div className="custom-dates">
            <label>
              From <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </label>
            <label>
              To <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </label>
          </div>
        )}
        {data && (
          <div className="dashboard-period">
            {data.from_date} → {data.to_date}
          </div>
        )}
      </div>

      {data && (
        <>
          <div className="dashboard-summary">
            <div className="summary-card earned">
              <span className="label">Credits bought</span>
              <span className="value">{summary.total_earned ?? 0}</span>
            </div>
            <div className="summary-card spent">
              <span className="label">Credits spent</span>
              <span className="value">{summary.total_spent ?? 0}</span>
            </div>
            <div className="summary-card count">
              <span className="label">Transactions</span>
              <span className="value">{summary.transaction_count ?? 0}</span>
            </div>
          </div>

          <div className="dashboard-charts">
            <div className="chart-card">
              <h3>Top 10 users by activity count</h3>
              {topUsersChart.length ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={topUsersChart} layout="vertical" margin={{ left: 80, right: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={78} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#ff6b35" name="Activities" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No activity in this period.</p>
              )}
            </div>

            <div className="chart-card">
              <h3>Credit use by activity</h3>
              {distribution.length ? (
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={distribution}
                      dataKey="total_credits"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {distribution.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => [v, 'Credits']} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No spend in this period.</p>
              )}
            </div>

            <div className="chart-card chart-card-wide">
              <h3>Credits bought vs spent over time</h3>
              {timeSeries.length ? (
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={timeSeries}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="credits" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="count" orientation="right" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Area yAxisId="credits" type="monotone" dataKey="earned" fill="#4CAF50" stroke="#2E7D32" name="Bought" />
                    <Bar yAxisId="credits" dataKey="spent" fill="#ff6b35" name="Spent" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="count" type="monotone" dataKey="transaction_count" stroke="#2196F3" strokeWidth={2} name="Transactions" dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No data in this period.</p>
              )}
            </div>

            <div className="chart-card">
              <h3>Spend by activity (credits)</h3>
              {distribution.length ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={distribution} margin={{ bottom: 80 }} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="total_credits" fill="#f7931e" name="Credits" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No spend in this period.</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
