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
} from 'recharts';
import './AdminChatPerformanceCharts.css';

const COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#d35400'];

const BUCKET_ORDER = ['<30s', '30-60s', '60-90s', '90-120s', '2-3 min', '3-4 min', '4-5 min', '>5 min'];

export default function AdminChatPerformanceCharts() {
  const [buckets, setBuckets] = useState([]);
  const [byUser, setByUser] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/admin/chat-performance/stats?limit=5000', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setBuckets(data.buckets || []);
      setByUser(data.by_user || []);
    } catch (e) {
      setError(e.message);
      setBuckets([]);
      setByUser([]);
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
