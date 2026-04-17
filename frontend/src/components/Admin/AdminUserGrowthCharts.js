import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { format, parseISO, subDays } from 'date-fns';
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
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminUserGrowthCharts.css';

const COL_MALE = '#3498db';
const COL_FEMALE = '#e91e63';
const COL_UNKNOWN = '#95a5a6';

function defaultEndDate() {
  const t = new Date();
  return format(t, 'yyyy-MM-dd');
}

function defaultStartDate() {
  return format(subDays(new Date(), 29), 'yyyy-MM-dd');
}

function formatPeriodLabel(periodIso, bucket) {
  const d = parseISO(periodIso);
  if (bucket === 'month') return format(d, 'MMM yyyy');
  if (bucket === 'week') return format(d, "MMM d ''yy");
  return format(d, 'MMM d');
}

export default function AdminUserGrowthCharts() {
  const [dateFrom, setDateFrom] = useState(defaultStartDate);
  const [dateTo, setDateTo] = useState(defaultEndDate);
  const [bucket, setBucket] = useState('day');
  const [gender, setGender] = useState('all');
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const chartData = useMemo(() => {
    return (series || []).map((row) => ({
      ...row,
      label: formatPeriodLabel(row.period, bucket),
    }));
  }, [series, bucket]);

  const fetchSeries = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        date_from: dateFrom,
        date_to: dateTo,
        bucket,
        gender,
      });
      const res = await fetch(`/api/admin/user-analytics-timeseries?${params}`, {
        headers: getAdminAuthHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.detail || data.message || `Request failed (${res.status})`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
      setSeries(data.series || []);
    } catch (e) {
      setError(e.message || 'Failed to load');
      setSeries([]);
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, bucket, gender]);

  useEffect(() => {
    fetchSeries();
  }, [fetchSeries]);

  const showStacks = gender === 'all';

  return (
    <div className="admin-user-growth">
      <h2>User charts</h2>
      <p className="admin-user-growth-desc">
        New users are signups per period (gender: if the user has one birth chart, that chart; otherwise the latest self chart).
        Active users are distinct people who sent at least one chat message in that period.
      </p>

      <div className="admin-user-growth-filters">
        <label>
          <span>From</span>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label>
          <span>To</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
        <label>
          <span>Bar size</span>
          <select value={bucket} onChange={(e) => setBucket(e.target.value)}>
            <option value="day">Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </select>
        </label>
        <label>
          <span>Gender</span>
          <select value={gender} onChange={(e) => setGender(e.target.value)}>
            <option value="all">All</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        <button type="button" onClick={fetchSeries} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && <div className="admin-user-growth-error">{error}</div>}
      {loading && !chartData.length ? (
        <div className="admin-user-growth-loading">Loading chart data…</div>
      ) : (
        <div className="admin-user-growth-grid">
          <div className="admin-user-growth-chart-card">
            <h3>New users</h3>
            <div className="admin-user-growth-chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 48 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" angle={-35} textAnchor="end" height={60} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={40} />
                  <Tooltip />
                  {showStacks ? <Legend /> : null}
                  {showStacks ? (
                    <>
                      <Bar dataKey="new_male" name="Male" stackId="n" fill={COL_MALE} />
                      <Bar dataKey="new_female" name="Female" stackId="n" fill={COL_FEMALE} />
                      <Bar dataKey="new_unknown" name="Unknown" stackId="n" fill={COL_UNKNOWN} />
                    </>
                  ) : (
                    <Bar
                      dataKey={gender === 'male' ? 'new_male' : gender === 'female' ? 'new_female' : 'new_unknown'}
                      name="New users"
                      fill={gender === 'male' ? COL_MALE : gender === 'female' ? COL_FEMALE : COL_UNKNOWN}
                    />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="admin-user-growth-chart-card">
            <h3>Active users</h3>
            <div className="admin-user-growth-chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 48 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" angle={-35} textAnchor="end" height={60} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={40} />
                  <Tooltip />
                  {showStacks ? <Legend /> : null}
                  {showStacks ? (
                    <>
                      <Bar dataKey="active_male" name="Male" stackId="a" fill={COL_MALE} />
                      <Bar dataKey="active_female" name="Female" stackId="a" fill={COL_FEMALE} />
                      <Bar dataKey="active_unknown" name="Unknown" stackId="a" fill={COL_UNKNOWN} />
                    </>
                  ) : (
                    <Bar
                      dataKey={gender === 'male' ? 'active_male' : gender === 'female' ? 'active_female' : 'active_unknown'}
                      name="Active users"
                      fill={gender === 'male' ? COL_MALE : gender === 'female' ? COL_FEMALE : COL_UNKNOWN}
                    />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
