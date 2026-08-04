import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getAdminAuthHeaders, getAdminEndpoint } from '../../services/adminService';
import './AdminBuyerAnalysis.css';

function formatLocalDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 83);
  return { from: formatLocalDate(from), to: formatLocalDate(to) };
}

function formatInt(value) {
  return Number(value || 0).toLocaleString('en-IN');
}

function formatInr(value) {
  return Number(value || 0).toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  });
}

function weekLabel(weekStart) {
  if (!weekStart) return '—';
  const d = new Date(`${weekStart}T00:00:00+05:30`);
  if (Number.isNaN(d.getTime())) return weekStart;
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    timeZone: 'Asia/Kolkata',
  }).format(d);
}

export default function AdminBuyerAnalysis() {
  const initial = defaultRange();
  const [fromDate, setFromDate] = useState(initial.from);
  const [toDate, setToDate] = useState(initial.to);
  const [groupBy, setGroupBy] = useState('source');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const requestIdRef = useRef(0);

  const load = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      if (fromDate) qs.set('from_date', fromDate);
      if (toDate) qs.set('to_date', toDate);
      qs.set('group_by', groupBy);
      qs.set('_ts', String(Date.now()));
      const res = await fetch(`${getAdminEndpoint('/credits/admin/buyer-analysis')}?${qs}`, {
        headers: {
          ...getAdminAuthHeaders(),
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
        cache: 'no-store',
      });
      const body = await res.json().catch(() => ({}));
      if (requestId !== requestIdRef.current) return;
      if (!res.ok) {
        throw new Error(body.detail || body.message || 'Failed to load buyer analysis');
      }
      setData(body);
    } catch (e) {
      if (requestId !== requestIdRef.current) return;
      setError(e.message || 'Failed to load');
      setData(null);
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, [fromDate, toDate, groupBy]);

  useEffect(() => {
    load();
  }, [load]);

  const kpis = data?.kpis || {};
  const weeklyNr = data?.weekly_new_vs_repeat || [];
  const weeklyCh = data?.weekly_by_channel || [];
  const leaderboard = data?.channel_leaderboard || [];
  const cohorts = data?.cohorts || [];
  const billing = data?.by_billing || [];

  const channelPivot = useMemo(() => {
    const weeks = [...new Set(weeklyCh.map((r) => r.week_start))].sort();
    const channels = [...new Set(weeklyCh.map((r) => r.channel))];
    const topChannels = channels
      .map((ch) => ({
        channel: ch,
        buyers: weeklyCh.filter((r) => r.channel === ch).reduce((s, r) => s + (r.buyers || 0), 0),
      }))
      .sort((a, b) => b.buyers - a.buyers)
      .slice(0, 8)
      .map((x) => x.channel);
    const map = new Map();
    weeklyCh.forEach((r) => {
      map.set(`${r.week_start}|${r.channel}`, r);
    });
    return { weeks, topChannels, map };
  }, [weeklyCh]);

  const maxCohortLag = 8;

  return (
    <div className="admin-buyer-analysis">
      <div className="aba-header">
        <div>
          <h3>Buyer analysis</h3>
          <p>
            Week-by-week credit purchases by UTM (first-touch install), new vs repeat buyers, and
            return cohorts. Queries use a pooled connection with a 15s statement timeout and a short
            server cache so admin refreshes do not starve chat traffic.
          </p>
        </div>
        <div className="aba-filters">
          <label>
            From
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </label>
          <label>
            To
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </label>
          <label>
            Channel
            <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
              <option value="source">utm_source</option>
              <option value="medium">utm_medium</option>
              <option value="campaign">utm_campaign</option>
              <option value="source_medium">source / medium</option>
            </select>
          </label>
          <button type="button" onClick={load} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="aba-meta">
        Applied IST range: <strong>{data?.from_date || fromDate}</strong> →{' '}
        <strong>{data?.to_date || toDate}</strong>
        {data?.query_ms != null ? ` · ${data.query_ms} ms` : ''}
        {data?.cached ? ' · cached' : ''}
        {data?.attribution ? ` · attribution: ${data.attribution}` : ''}
      </div>

      {error && <div className="aba-error">{error}</div>}

      <div className="aba-kpis">
        <div className="aba-kpi">
          <div className="aba-kpi-label">Revenue (est.)</div>
          <div className="aba-kpi-value">{formatInr(kpis.estimated_revenue_inr)}</div>
        </div>
        <div className="aba-kpi">
          <div className="aba-kpi-label">Paying users</div>
          <div className="aba-kpi-value">{formatInt(kpis.unique_buyers)}</div>
        </div>
        <div className="aba-kpi">
          <div className="aba-kpi-label">Purchases</div>
          <div className="aba-kpi-value">{formatInt(kpis.purchase_count)}</div>
        </div>
        <div className="aba-kpi">
          <div className="aba-kpi-label">Repeat buyers</div>
          <div className="aba-kpi-value">
            {formatInt(kpis.repeat_buyers)}
            {kpis.repeat_buyer_pct != null ? (
              <span className="aba-kpi-sub"> {kpis.repeat_buyer_pct}%</span>
            ) : null}
          </div>
        </div>
        <div className="aba-kpi">
          <div className="aba-kpi-label">Credits bought</div>
          <div className="aba-kpi-value">{formatInt(kpis.credits_purchased)}</div>
        </div>
      </div>

      <section className="aba-section">
        <h4>Week × new vs repeat buyers</h4>
        <div className="aba-table-wrap">
          <table className="aba-table">
            <thead>
              <tr>
                <th>Week</th>
                <th>Buyers</th>
                <th>New</th>
                <th>Repeat</th>
                <th>Purchases</th>
                <th>Credits</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {weeklyNr.map((row) => (
                <tr key={row.week_start}>
                  <td>{weekLabel(row.week_start)}</td>
                  <td>{formatInt(row.buyers)}</td>
                  <td>{formatInt(row.new_buyers)}</td>
                  <td>{formatInt(row.repeat_buyers)}</td>
                  <td>{formatInt(row.purchase_count)}</td>
                  <td>{formatInt(row.credits)}</td>
                  <td>{formatInr(row.revenue_inr)}</td>
                </tr>
              ))}
              {!weeklyNr.length && !loading && (
                <tr>
                  <td colSpan={7}>No purchases in this range.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="aba-section">
        <h4>Week × UTM channel (top 8 by buyers)</h4>
        <div className="aba-table-wrap">
          <table className="aba-table aba-pivot">
            <thead>
              <tr>
                <th>Week</th>
                {channelPivot.topChannels.map((ch) => (
                  <th key={ch} title={ch}>
                    {ch.length > 18 ? `${ch.slice(0, 16)}…` : ch}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {channelPivot.weeks.map((week) => (
                <tr key={week}>
                  <td>{weekLabel(week)}</td>
                  {channelPivot.topChannels.map((ch) => {
                    const cell = channelPivot.map.get(`${week}|${ch}`);
                    return (
                      <td key={ch}>
                        {cell ? (
                          <>
                            <div>{formatInt(cell.buyers)} buyers</div>
                            <div className="aba-cell-sub">{formatInr(cell.revenue_inr)}</div>
                          </>
                        ) : (
                          '—'
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
              {!channelPivot.weeks.length && !loading && (
                <tr>
                  <td colSpan={Math.max(1, channelPivot.topChannels.length) + 1}>No channel data.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="aba-section">
        <h4>Channel leaderboard</h4>
        <div className="aba-table-wrap">
          <table className="aba-table">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Buyers</th>
                <th>Purchases</th>
                <th>Credits</th>
                <th>Revenue</th>
                <th>New in range</th>
                <th>Median days install→buy</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((row) => (
                <tr key={row.channel}>
                  <td>{row.channel}</td>
                  <td>{formatInt(row.buyers)}</td>
                  <td>{formatInt(row.purchase_count)}</td>
                  <td>{formatInt(row.credits)}</td>
                  <td>{formatInr(row.revenue_inr)}</td>
                  <td>{formatInt(row.new_buyers_in_range)}</td>
                  <td>
                    {row.median_days_install_to_first_buy != null
                      ? row.median_days_install_to_first_buy
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="aba-section">
        <h4>Return cohort (first-buy week → later weeks)</h4>
        <div className="aba-table-wrap">
          <table className="aba-table aba-cohort">
            <thead>
              <tr>
                <th>Cohort week</th>
                <th>Size</th>
                {[...Array(maxCohortLag + 1)].map((_, i) => (
                  <th key={i}>W+{i}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cohorts.map((c) => (
                <tr key={c.cohort_week}>
                  <td>{weekLabel(c.cohort_week)}</td>
                  <td>{formatInt(c.cohort_size)}</td>
                  {[...Array(maxCohortLag + 1)].map((_, i) => {
                    const n = Number(c.returns?.[String(i)] || 0);
                    const pct = c.cohort_size ? Math.round((100 * n) / c.cohort_size) : 0;
                    return (
                      <td key={i} title={`${n} buyers`}>
                        {c.cohort_size ? `${pct}%` : '—'}
                      </td>
                    );
                  })}
                </tr>
              ))}
              {!cohorts.length && !loading && (
                <tr>
                  <td colSpan={maxCohortLag + 3}>No cohort data.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="aba-section">
        <h4>Billing split</h4>
        <div className="aba-billing">
          {billing.map((row) => (
            <div className="aba-billing-card" key={row.source}>
              <div className="aba-billing-title">{row.source}</div>
              <div>{formatInt(row.buyers)} buyers · {formatInt(row.purchase_count)} purchases</div>
              <div>{formatInr(row.revenue_inr)} · {formatInt(row.credits)} credits</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
