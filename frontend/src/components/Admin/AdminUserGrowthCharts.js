import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { format, parseISO, subDays } from 'date-fns';
import {
  BarChart,
  Bar,
  LabelList,
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
const DEFAULT_BAR_LIMIT = 10;
const MOBILE_BAR_LIMIT = 6;

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
  const [todaySummary, setTodaySummary] = useState({
    total: 0,
    male: 0,
    female: 0,
    unknown: 0,
  });
  const [todaySummaryLoading, setTodaySummaryLoading] = useState(false);
  const [isMobile, setIsMobile] = useState(() => (
    typeof window !== 'undefined' ? window.innerWidth <= 768 : false
  ));

  const chartData = useMemo(() => {
    return (series || []).map((row) => {
      const newMale = Number(row.new_male || 0);
      const newFemale = Number(row.new_female || 0);
      const newUnknown = Number(row.new_unknown || 0);
      const activeMale = Number(row.active_male || 0);
      const activeFemale = Number(row.active_female || 0);
      const activeUnknown = Number(row.active_unknown || 0);
      return {
      ...row,
      label: formatPeriodLabel(row.period, bucket),
      new_total: newMale + newFemale + newUnknown,
      active_total: activeMale + activeFemale + activeUnknown,
    };
    });
  }, [series, bucket]);

  const barLimit = isMobile ? MOBILE_BAR_LIMIT : DEFAULT_BAR_LIMIT;
  const visibleChartData = useMemo(() => chartData.slice(-barLimit), [chartData, barLimit]);
  const showStacks = gender === 'all';
  const showLegend = showStacks && !isMobile;
  const axisAngle = isMobile ? -30 : -35;
  const axisHeight = isMobile ? 52 : 60;
  const axisFontSize = isMobile ? 9 : 11;
  const chartMargins = isMobile
    ? { top: 10, right: 2, left: -14, bottom: 24 }
    : { top: 18, right: 12, left: 4, bottom: 48 };
  const hasNewUsersData = visibleChartData.some((row) => Number(row.new_total || 0) > 0);
  const hasActiveUsersData = visibleChartData.some((row) => Number(row.active_total || 0) > 0);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const onResize = () => setIsMobile(window.innerWidth <= 768);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

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

  const fetchTodaySummary = useCallback(async () => {
    setTodaySummaryLoading(true);
    try {
      const today = defaultEndDate();
      const params = new URLSearchParams({
        date_from: today,
        date_to: today,
        bucket: 'day',
        gender: 'all',
      });
      const res = await fetch(`/api/admin/user-analytics-timeseries?${params}`, {
        headers: getAdminAuthHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.detail || data.message || `Request failed (${res.status})`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
      const todayRow = (data.series || [])[0] || {};
      const male = Number(todayRow.new_male || 0);
      const female = Number(todayRow.new_female || 0);
      const unknown = Number(todayRow.new_unknown || 0);
      setTodaySummary({
        total: male + female + unknown,
        male,
        female,
        unknown,
      });
    } catch (_) {
      setTodaySummary({ total: 0, male: 0, female: 0, unknown: 0 });
    } finally {
      setTodaySummaryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSeries();
  }, [fetchSeries]);

  useEffect(() => {
    fetchTodaySummary();
  }, [fetchTodaySummary]);

  return (
    <div className="admin-user-growth">
      <h2>User charts</h2>
      <p className="admin-user-growth-desc admin-user-growth-desc--mobile-hide">
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
      <div className="admin-user-growth-today-summary">
        <div className="admin-user-growth-summary-card">
          <span>Today - Total Users</span>
          <strong>{todaySummaryLoading ? '...' : todaySummary.total}</strong>
        </div>
        <div className="admin-user-growth-summary-card">
          <span>Males</span>
          <strong>{todaySummaryLoading ? '...' : todaySummary.male}</strong>
        </div>
        <div className="admin-user-growth-summary-card">
          <span>Females</span>
          <strong>{todaySummaryLoading ? '...' : todaySummary.female}</strong>
        </div>
        <div className="admin-user-growth-summary-card">
          <span>Unknowns</span>
          <strong>{todaySummaryLoading ? '...' : todaySummary.unknown}</strong>
        </div>
      </div>

      {error && <div className="admin-user-growth-error">{error}</div>}
      {loading && !visibleChartData.length ? (
        <div className="admin-user-growth-loading">Loading chart data…</div>
      ) : (
        <div className="admin-user-growth-grid">
          <div className="admin-user-growth-chart-card">
            <h3>New users (last {barLimit} bars)</h3>
            <div className="admin-user-growth-chart-wrap">
              {!hasNewUsersData ? (
                <div className="admin-user-growth-no-data">No new users in this range.</div>
              ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={visibleChartData} margin={chartMargins}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="label" tick={{ fontSize: axisFontSize }} interval="preserveStartEnd" angle={axisAngle} textAnchor="end" height={axisHeight} />
                  <YAxis allowDecimals={false} tick={{ fontSize: axisFontSize }} width={40} />
                  <Tooltip />
                  {showLegend ? <Legend /> : null}
                  {showStacks ? (
                    <>
                      <Bar dataKey="new_male" name="Male" stackId="n" fill={COL_MALE} />
                      <Bar dataKey="new_female" name="Female" stackId="n" fill={COL_FEMALE} />
                      <Bar dataKey="new_unknown" name="Unknown" stackId="n" fill={COL_UNKNOWN}>
                        <LabelList dataKey="new_total" position="top" className="admin-user-growth-bar-label" />
                      </Bar>
                    </>
                  ) : (
                    <Bar
                      dataKey={gender === 'male' ? 'new_male' : gender === 'female' ? 'new_female' : 'new_unknown'}
                      name="New users"
                      fill={gender === 'male' ? COL_MALE : gender === 'female' ? COL_FEMALE : COL_UNKNOWN}
                    >
                      <LabelList
                        dataKey={gender === 'male' ? 'new_male' : gender === 'female' ? 'new_female' : 'new_unknown'}
                        position="top"
                        className="admin-user-growth-bar-label"
                      />
                    </Bar>
                  )}
                </BarChart>
              </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="admin-user-growth-chart-card">
            <h3>Active users (last {barLimit} bars)</h3>
            <div className="admin-user-growth-chart-wrap">
              {!hasActiveUsersData ? (
                <div className="admin-user-growth-no-data">No active users in this range.</div>
              ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={visibleChartData} margin={chartMargins}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="label" tick={{ fontSize: axisFontSize }} interval="preserveStartEnd" angle={axisAngle} textAnchor="end" height={axisHeight} />
                  <YAxis allowDecimals={false} tick={{ fontSize: axisFontSize }} width={40} />
                  <Tooltip />
                  {showLegend ? <Legend /> : null}
                  {showStacks ? (
                    <>
                      <Bar dataKey="active_male" name="Male" stackId="a" fill={COL_MALE} />
                      <Bar dataKey="active_female" name="Female" stackId="a" fill={COL_FEMALE} />
                      <Bar dataKey="active_unknown" name="Unknown" stackId="a" fill={COL_UNKNOWN}>
                        <LabelList dataKey="active_total" position="top" className="admin-user-growth-bar-label" />
                      </Bar>
                    </>
                  ) : (
                    <Bar
                      dataKey={gender === 'male' ? 'active_male' : gender === 'female' ? 'active_female' : 'active_unknown'}
                      name="Active users"
                      fill={gender === 'male' ? COL_MALE : gender === 'female' ? COL_FEMALE : COL_UNKNOWN}
                    >
                      <LabelList
                        dataKey={gender === 'male' ? 'active_male' : gender === 'female' ? 'active_female' : 'active_unknown'}
                        position="top"
                        className="admin-user-growth-bar-label"
                      />
                    </Bar>
                  )}
                </BarChart>
              </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
