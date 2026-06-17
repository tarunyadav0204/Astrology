import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
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
const COL_FEMALE = '#7c3aed';
const COL_UNKNOWN = '#95a5a6';
const COL_TOTAL = '#2c5282';
const DEFAULT_RANGE_DAYS = 5;

const DEFAULT_CHART_OPTS = { bucket: 'day', showGender: false, gender: 'all' };

function defaultEndDate() {
  return format(new Date(), 'yyyy-MM-dd');
}

function defaultStartDate() {
  return format(subDays(new Date(), DEFAULT_RANGE_DAYS - 1), 'yyyy-MM-dd');
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
  const [bucket, setBucket] = useState(DEFAULT_CHART_OPTS.bucket);
  const [showGender, setShowGender] = useState(DEFAULT_CHART_OPTS.showGender);
  const [gender, setGender] = useState(DEFAULT_CHART_OPTS.gender);
  const [appliedChart, setAppliedChart] = useState(DEFAULT_CHART_OPTS);
  const appliedChartRef = useRef(DEFAULT_CHART_OPTS);
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isMobile, setIsMobile] = useState(() => (
    typeof window !== 'undefined' ? window.innerWidth <= 768 : false
  ));

  const chartData = useMemo(() => {
    const b = appliedChart.bucket;
    return (series || []).map((row) => {
      const newMale = Number(row.new_male || 0);
      const newFemale = Number(row.new_female || 0);
      const newUnknown = Number(row.new_unknown || 0);
      return {
        ...row,
        label: formatPeriodLabel(row.period, b),
        new_total: newMale + newFemale + newUnknown,
      };
    });
  }, [series, appliedChart.bucket]);

  const todaySummary = useMemo(() => {
    const today = defaultEndDate();
    const row = chartData.find((r) => r.period === today);
    if (!row) {
      return { total: null, male: null, female: null, unknown: null };
    }
    const male = Number(row.new_male || 0);
    const female = Number(row.new_female || 0);
    const unknown = Number(row.new_unknown || 0);
    return {
      total: male + female + unknown,
      male,
      female,
      unknown,
    };
  }, [chartData]);

  const showStacks = appliedChart.showGender && appliedChart.gender === 'all';
  const showLegend = showStacks && !isMobile;
  const axisAngle = isMobile ? -30 : -35;
  const axisHeight = isMobile ? 52 : 60;
  const axisFontSize = isMobile ? 9 : 11;
  const chartMargins = isMobile
    ? { top: 10, right: 2, left: -14, bottom: 24 }
    : { top: 18, right: 12, left: 4, bottom: 48 };
  const hasNewUsersData = chartData.some((row) => Number(row.new_total || 0) > 0);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const onResize = () => setIsMobile(window.innerWidth <= 768);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const fetchSeries = useCallback(async (from, to, opts) => {
    const { bucket: b, showGender: withGender, gender: g } = opts;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        date_from: from,
        date_to: to,
        bucket: b,
        gender: g,
        include_gender: withGender ? 'true' : 'false',
      });
      const res = await fetch(`/api/admin/user-analytics-timeseries?${params}`, {
        headers: getAdminAuthHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.detail || data.message || `Request failed (${res.status})`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
      appliedChartRef.current = opts;
      setAppliedChart(opts);
      setSeries(data.series || []);
    } catch (e) {
      setError(e.message || 'Failed to load');
      setSeries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSeries(dateFrom, dateTo, appliedChartRef.current);
  }, [dateFrom, dateTo, fetchSeries]);

  const handleApplyChartOptions = () => {
    const opts = { bucket, showGender, gender };
    fetchSeries(dateFrom, dateTo, opts);
  };

  const summaryValue = (n) => (loading ? '…' : n == null ? '—' : n);

  return (
    <div className="admin-user-growth">
      <h2>User charts</h2>
      <p className="admin-user-growth-desc admin-user-growth-desc--mobile-hide">
        New user signups per period. Default view is the last {DEFAULT_RANGE_DAYS} days; change the date range for a longer history.
        Enable gender breakdown only when you need it (slower — uses birth chart data).
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
        <label className="admin-user-growth-checkbox">
          <input
            type="checkbox"
            checked={showGender}
            onChange={(e) => setShowGender(e.target.checked)}
          />
          <span>Gender breakdown</span>
        </label>
        {showGender ? (
          <label>
            <span>Gender</span>
            <select value={gender} onChange={(e) => setGender(e.target.value)}>
              <option value="all">All (stacked)</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="unknown">Unknown</option>
            </select>
          </label>
        ) : null}
        <button type="button" onClick={handleApplyChartOptions} disabled={loading}>
          {loading ? 'Loading…' : 'Apply bar size / gender'}
        </button>
      </div>

      <div className="admin-user-growth-today-summary">
        <div className="admin-user-growth-summary-card">
          <span>Today — new signups</span>
          <strong>{summaryValue(todaySummary.total)}</strong>
        </div>
        {appliedChart.showGender ? (
          <>
            <div className="admin-user-growth-summary-card">
              <span>Males</span>
              <strong>{summaryValue(todaySummary.male)}</strong>
            </div>
            <div className="admin-user-growth-summary-card">
              <span>Females</span>
              <strong>{summaryValue(todaySummary.female)}</strong>
            </div>
            <div className="admin-user-growth-summary-card">
              <span>Unknown</span>
              <strong>{summaryValue(todaySummary.unknown)}</strong>
            </div>
          </>
        ) : null}
      </div>

      {error && <div className="admin-user-growth-error">{error}</div>}
      {loading && !chartData.length ? (
        <div className="admin-user-growth-loading">Loading chart data…</div>
      ) : (
        <div className="admin-user-growth-grid">
          <div className="admin-user-growth-chart-card">
            <h3>New users</h3>
            <div className="admin-user-growth-chart-wrap">
              {!hasNewUsersData ? (
                <div className="admin-user-growth-no-data">No new users in this range.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={chartMargins}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: axisFontSize }}
                      interval="preserveStartEnd"
                      angle={axisAngle}
                      textAnchor="end"
                      height={axisHeight}
                    />
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
                    ) : appliedChart.showGender ? (
                      <Bar
                        dataKey={
                          appliedChart.gender === 'male'
                            ? 'new_male'
                            : appliedChart.gender === 'female'
                              ? 'new_female'
                              : 'new_unknown'
                        }
                        name="New users"
                        fill={
                          appliedChart.gender === 'male'
                            ? COL_MALE
                            : appliedChart.gender === 'female'
                              ? COL_FEMALE
                              : COL_UNKNOWN
                        }
                      >
                        <LabelList
                          dataKey={
                            appliedChart.gender === 'male'
                              ? 'new_male'
                              : appliedChart.gender === 'female'
                                ? 'new_female'
                                : 'new_unknown'
                          }
                          position="top"
                          className="admin-user-growth-bar-label"
                        />
                      </Bar>
                    ) : (
                      <Bar dataKey="new_total" name="New users" fill={COL_TOTAL}>
                        <LabelList dataKey="new_total" position="top" className="admin-user-growth-bar-label" />
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
