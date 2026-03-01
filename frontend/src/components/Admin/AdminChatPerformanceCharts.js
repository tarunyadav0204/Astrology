import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import './AdminChatPerformanceCharts.css';

const COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#d35400'];

const BUCKET_ORDER = ['<30s', '30-60s', '60-90s', '90-120s', '2-3 min', '3-4 min', '4-5 min', '>5 min'];

function getPeriodDates(period, customStart, customEnd) {
  const today = new Date();
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, '0');
  const d = String(today.getDate()).padStart(2, '0');
  const todayStr = `${y}-${m}-${d}`;
  if (period === 'today') return { start_date: todayStr, end_date: todayStr };
  if (period === 'custom') {
    if (!customStart || !customEnd) return { start_date: '', end_date: '' };
    return { start_date: customStart, end_date: customEnd };
  }
  const start = new Date(today);
  if (period === 'week') start.setDate(today.getDate() - 6);
  if (period === 'month') start.setDate(1);
  if (period === 'ytd') start.setMonth(0), start.setDate(1);
  const sy = start.getFullYear();
  const sm = String(start.getMonth() + 1).padStart(2, '0');
  const sd = String(start.getDate()).padStart(2, '0');
  return { start_date: `${sy}-${sm}-${sd}`, end_date: todayStr };
}

export default function AdminChatPerformanceCharts() {
  const [buckets, setBuckets] = useState([]);
  const [byUser, setByUser] = useState([]);
  const [slowByHour, setSlowByHour] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('month');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const { start_date, end_date } = useMemo(
    () => getPeriodDates(period, customStart, customEnd),
    [period, customStart, customEnd]
  );

  useEffect(() => {
    fetchStats();
  }, [start_date, end_date]);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: '5000' });
      if (start_date && end_date) params.set('start_date', start_date), params.set('end_date', end_date);
      const response = await fetch(`/api/admin/chat-performance/stats?${params.toString()}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setBuckets(data.buckets || []);
      setByUser(data.by_user || []);
      setSlowByHour(data.slow_by_hour || []);
    } catch (e) {
      setError(e.message);
      setBuckets([]);
      setByUser([]);
      setSlowByHour([]);
    } finally {
      setLoading(false);
    }
  };

  // Build stacked data for graph 2: one row per bucket, one key per user (top 10 by total)
  const topUsers = [...byUser]
    .map((u) => ({
      ...u,
      total: (u.buckets || []).reduce((s, b) => s + (b.count || 0), 0),
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);

  const stackedData = BUCKET_ORDER.map((bucketName) => {
    const row = { name: bucketName };
    topUsers.forEach((u, i) => {
      const b = (u.buckets || []).find((x) => x.name === bucketName);
      const key = `user_${i}`;
      row[key] = b ? b.count : 0;
    });
    return row;
  });

  if (loading) {
    return (
      <div className="chat-performance-charts">
        <div className="charts-header">
          <h2>📊 Chat Performance – Duration</h2>
          <button onClick={fetchStats} className="refresh-btn" disabled>Loading…</button>
        </div>
        <div className="loading">Loading stats…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chat-performance-charts">
        <div className="charts-header">
          <h2>📊 Chat Performance – Duration</h2>
          <button onClick={fetchStats} className="refresh-btn">🔄 Refresh</button>
        </div>
        <div className="charts-error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="chat-performance-charts">
      <div className="charts-header">
        <h2>📊 Chat Performance – Duration</h2>
        <button onClick={fetchStats} className="refresh-btn">🔄 Refresh</button>
      </div>
      <div className="performance-filters performance-filters-period charts-period">
        <span className="filter-label">Period:</span>
        <div className="period-buttons">
          {['today', 'week', 'month', 'ytd', 'custom'].map((p) => (
            <button
              key={p}
              type="button"
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {p === 'today' && 'Today'}
              {p === 'week' && 'This week'}
              {p === 'month' && 'This month'}
              {p === 'ytd' && 'YTD'}
              {p === 'custom' && 'Custom'}
            </button>
          ))}
        </div>
        {period === 'custom' && (
          <div className="custom-date-row">
            <label>
              From
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="date-input"
              />
            </label>
            <label>
              To
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="date-input"
              />
            </label>
          </div>
        )}
      </div>

      <div className="chart-card">
        <h3>Slow responses (&gt;2 min) by time of day</h3>
        <p className="chart-subtitle">When did responses take more than 2 minutes? (by hour when response completed)</p>
        {slowByHour.length ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={slowByHour}
              margin={{ top: 16, right: 24, left: 24, bottom: 24 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour_label" tick={{ fontSize: 11 }} interval={1} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" name="Slow responses (>2 min)" fill="#e74c3c" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No slow responses in this sample.</p>
        )}
      </div>

      <div className="chart-card">
        <h3>Response count by duration (all users)</h3>
        {buckets.length ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={buckets} margin={{ top: 16, right: 24, left: 24, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" name="Count" fill="#3498db" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No duration data available.</p>
        )}
      </div>

      <div className="chart-card">
        <h3>Response count by duration (by user, top 10)</h3>
        {stackedData.length && topUsers.length ? (
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={stackedData} margin={{ top: 16, right: 24, left: 24, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              {topUsers.map((u, i) => (
                <Bar
                  key={u.user_name + (u.user_phone || '')}
                  stackId="stack"
                  dataKey={`user_${i}`}
                  name={u.user_phone ? `${u.user_name} (${u.user_phone})` : u.user_name}
                  fill={COLORS[i % COLORS.length]}
                  radius={i === topUsers.length - 1 ? [0, 4, 4, 0] : [0, 0, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No per-user duration data available.</p>
        )}
      </div>
    </div>
  );
}
