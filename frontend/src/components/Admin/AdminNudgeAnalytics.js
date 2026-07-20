import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const dateIsoInIST = (date) => {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date);
  const get = (type) => parts.find((part) => part.type === type)?.value;
  return `${get('year')}-${get('month')}-${get('day')}`;
};
const isoDaysAgo = (days) => dateIsoInIST(new Date(Date.now() - days * 86400000));
const todayIso = () => dateIsoInIST(new Date());

function fmtDuration(seconds) {
  if (seconds == null) return '—';
  const s = Math.round(Number(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  if (s < 86400) return `${(s / 3600).toFixed(1)}h`;
  return `${(s / 86400).toFixed(1)}d`;
}

function fmtDateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  });
}

function fmtHours(hours) {
  if (hours == null) return '—';
  return fmtDuration(Number(hours) * 3600);
}

function StatCard({ label, value, sub }) {
  return (
    <div
      style={{
        flex: '1 1 130px',
        minWidth: 130,
        background: '#fff',
        border: '1px solid #e3e3ee',
        borderRadius: 10,
        padding: '14px 16px',
      }}
    >
      <div style={{ fontSize: 12, color: '#777', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: '#1c1c28' }}>{value}</div>
      {sub ? <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>{sub}</div> : null}
    </div>
  );
}

function BucketBar({ buckets }) {
  const entries = [
    ['< 5 min', buckets?.under_5m || 0],
    ['5m – 1h', buckets?.under_1h || 0],
    ['1h – 6h', buckets?.under_6h || 0],
    ['6h – 24h', buckets?.under_24h || 0],
    ['> 24h', buckets?.over_24h || 0],
  ];
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {entries.map(([label, value]) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 80, fontSize: 12, color: '#666' }}>{label}</span>
          <div style={{ flex: 1, background: '#f0f0f6', borderRadius: 4, height: 16 }}>
            <div
              style={{
                width: `${(value / max) * 100}%`,
                background: '#6c4bd8',
                height: '100%',
                borderRadius: 4,
                minWidth: value > 0 ? 4 : 0,
              }}
            />
          </div>
          <span style={{ width: 40, fontSize: 12, textAlign: 'right' }}>{value}</span>
        </div>
      ))}
    </div>
  );
}

export default function AdminNudgeAnalytics() {
  const [startDate, setStartDate] = useState(isoDaysAgo(7));
  const [endDate, setEndDate] = useState(todayIso());
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [campaignStats, setCampaignStats] = useState(null);
  const [campaignLoadingId, setCampaignLoadingId] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [funnelDays, setFunnelDays] = useState(7);
  const [funnelAsked, setFunnelAsked] = useState('all');
  const [funnelLoading, setFunnelLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
      const res = await fetch(`/api/nudge/admin/stats/overview?${params}`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || 'Failed to load nudge analytics');
      setOverview(body);
    } catch (e) {
      setError(e.message || 'Failed to load nudge analytics');
      setOverview(null);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    load();
  }, [load]);

  const loadCampaignFunnel = async (
    campaignId,
    days = funnelDays,
    askedFilter = funnelAsked,
    page = 1
  ) => {
    setFunnelLoading(true);
    try {
      const params = new URLSearchParams({
        window_days: String(days),
        page: String(page),
        page_size: '50',
      });
      if (askedFilter !== 'all') params.set('asked', askedFilter === 'asked' ? 'true' : 'false');
      const res = await fetch(
        `/api/nudge/admin/campaigns/${campaignId}/question-funnel?${params}`,
        { headers: getAdminAuthHeaders() }
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || 'Failed to load campaign question funnel');
      setFunnel(body);
    } catch (e) {
      setError(e.message || 'Failed to load campaign question funnel');
      setFunnel(null);
    } finally {
      setFunnelLoading(false);
    }
  };

  const loadCampaignStats = async (campaignId) => {
    setCampaignLoadingId(campaignId);
    setError('');
    setFunnel(null);
    try {
      const [statsRes] = await Promise.all([
        fetch(`/api/nudge/admin/campaigns/${campaignId}/stats`, {
          headers: getAdminAuthHeaders(),
        }),
        loadCampaignFunnel(campaignId, funnelDays, funnelAsked, 1),
      ]);
      const statsBody = await statsRes.json().catch(() => ({}));
      if (!statsRes.ok) throw new Error(statsBody.detail || 'Failed to load campaign stats');
      setCampaignStats(statsBody);
    } catch (e) {
      setError(e.message || 'Failed to load campaign stats');
    } finally {
      setCampaignLoadingId(null);
    }
  };

  const sends = overview?.sends || {};
  const buckets = overview?.time_buckets || {};

  return (
    <div className="nudge-analytics-admin">
      <p className="notifications-description">
        How many nudges were sent per channel, how many users asked a question afterwards, and how
        long they took. Conversions are attributed via nudge tap (push/inbox/email link); the
        “window” count adds users who asked within 24h without a tracked tap.
      </p>

      <div className="nudge-scheduler-filter">
        <div className="form-field">
          <label>From</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div className="form-field">
          <label>To</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
        <button type="button" className="notif-search-btn" onClick={load}>
          Refresh
        </button>
      </div>

      {loading && <p className="notifications-description">Loading analytics…</p>}
      {error && (
        <div className="notif-result error">
          <strong>Error.</strong> {error}
        </div>
      )}

      {!loading && overview && (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 16 }}>
            <StatCard label="Nudges sent" value={sends.targeted || 0} />
            <StatCard label="Push" value={sends.push || 0} />
            <StatCard label="WhatsApp" value={sends.whatsapp || 0} />
            <StatCard label="Email" value={sends.email || 0} />
            <StatCard label="Inbox only" value={sends.stored_only || 0} sub="no channel reached" />
            <StatCard label="Failed attempts" value={sends.failed_attempts || 0} />
            <StatCard label="Email clicks" value={sends.clicked || 0} />
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 16 }}>
            <StatCard
              label="Questions asked (tap)"
              value={overview.conversions || 0}
              sub={`conversion rate ${(100 * (overview.conversion_rate || 0)).toFixed(1)}%`}
            />
            <StatCard
              label="Median time to question"
              value={fmtDuration(overview.median_seconds_to_question)}
            />
            {Object.entries(overview.conversions_by_channel || {}).map(([ch, n]) => (
              <StatCard key={ch} label={`Conversions via ${ch}`} value={n} />
            ))}
          </div>

          <div
            style={{
              background: '#fff',
              border: '1px solid #e3e3ee',
              borderRadius: 10,
              padding: 16,
              marginBottom: 16,
              maxWidth: 520,
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>
              Time from nudge to question
            </div>
            <BucketBar buckets={buckets} />
          </div>

          <div className="notif-user-list nudge-scheduler-list">
            <table className="notif-user-table">
              <thead>
                <tr>
                  <th>Source (trigger / campaign)</th>
                  <th style={{ width: 80 }}>Sent</th>
                  <th style={{ width: 70 }}>Push</th>
                  <th style={{ width: 90 }}>WhatsApp</th>
                  <th style={{ width: 70 }}>Email</th>
                  <th style={{ width: 100 }}>Conversions</th>
                  <th style={{ width: 80 }}>Rate</th>
                  <th style={{ width: 110 }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {(overview.by_source || []).length === 0 ? (
                  <tr>
                    <td colSpan={8} className="notif-td-name">No nudges sent in this range.</td>
                  </tr>
                ) : (
                  (overview.by_source || []).map((row) => (
                    <tr key={`${row.trigger_id}-${row.campaign_id || ''}`}>
                      <td>
                        <strong>{row.trigger_id || '(unknown)'}</strong>
                        {row.campaign_id ? <div className="notif-td-phone">campaign #{row.campaign_id}</div> : null}
                      </td>
                      <td>{row.targeted}</td>
                      <td>{row.push}</td>
                      <td>{row.whatsapp}</td>
                      <td>{row.email}</td>
                      <td>{row.conversions}</td>
                      <td>{row.targeted ? `${((100 * row.conversions) / row.targeted).toFixed(1)}%` : '—'}</td>
                      <td>
                        {row.campaign_id ? (
                          <button
                            type="button"
                            className="notif-search-btn"
                            style={{ padding: '2px 8px' }}
                            disabled={campaignLoadingId === row.campaign_id}
                            onClick={() => loadCampaignStats(row.campaign_id)}
                          >
                            {campaignLoadingId === row.campaign_id ? 'Loading…' : 'Campaign stats'}
                          </button>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {campaignStats && (
        <div
          style={{
            background: '#fff',
            border: '1px solid #e3e3ee',
            borderRadius: 10,
            padding: 16,
            marginTop: 16,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: 14, fontWeight: 700 }}>
              Campaign #{campaignStats.campaign?.id} — {campaignStats.campaign?.name}
            </div>
            <button
              type="button"
              className="notif-search-btn"
              onClick={() => {
                setCampaignStats(null);
                setFunnel(null);
              }}
            >
              Close
            </button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, margin: '12px 0' }}>
            <StatCard label="Targeted" value={campaignStats.stats?.sends?.targeted || 0} />
            <StatCard label="Push" value={campaignStats.stats?.sends?.push || 0} />
            <StatCard label="WhatsApp" value={campaignStats.stats?.sends?.whatsapp || 0} />
            <StatCard label="Email" value={campaignStats.stats?.sends?.email || 0} />
            <StatCard label="Email clicks" value={campaignStats.stats?.sends?.clicked || 0} />
            <StatCard
              label="Conversions (tap)"
              value={campaignStats.stats?.conversions || 0}
              sub={`rate ${(100 * (campaignStats.stats?.conversion_rate || 0)).toFixed(1)}%`}
            />
            <StatCard label="Conversions (24h window)" value={campaignStats.stats?.window_conversions || 0} />
            <StatCard
              label="Median time to question"
              value={fmtDuration(campaignStats.stats?.median_seconds_to_question)}
            />
          </div>
          <div style={{ maxWidth: 520 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>
              Time from nudge to question
            </div>
            <BucketBar buckets={campaignStats.stats?.time_buckets || {}} />
          </div>

          <div style={{ borderTop: '1px solid #ececf3', marginTop: 18, paddingTop: 16 }}>
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'end',
                justifyContent: 'space-between',
                gap: 12,
                marginBottom: 12,
              }}
            >
              <div>
                <div style={{ fontSize: 14, fontWeight: 700 }}>Question funnel</div>
                <div style={{ fontSize: 12, color: '#777', marginTop: 3 }}>
                  Users who asked a chat question after this campaign was delivered.
                </div>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'end', gap: 8 }}>
                <div className="form-field" style={{ margin: 0 }}>
                  <label>Window</label>
                  <select
                    value={funnelDays}
                    onChange={(e) => {
                      const days = Number(e.target.value);
                      setFunnelDays(days);
                      loadCampaignFunnel(campaignStats.campaign.id, days, funnelAsked, 1);
                    }}
                  >
                    {[1, 3, 7, 14, 30].map((days) => (
                      <option key={days} value={days}>
                        {days} day{days === 1 ? '' : 's'}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-field" style={{ margin: 0 }}>
                  <label>Recipients</label>
                  <select
                    value={funnelAsked}
                    onChange={(e) => {
                      const filter = e.target.value;
                      setFunnelAsked(filter);
                      loadCampaignFunnel(campaignStats.campaign.id, funnelDays, filter, 1);
                    }}
                  >
                    <option value="all">All</option>
                    <option value="asked">Asked</option>
                    <option value="not_asked">Did not ask</option>
                  </select>
                </div>
                <button
                  type="button"
                  className="notif-search-btn"
                  disabled={funnelLoading}
                  onClick={() =>
                    loadCampaignFunnel(
                      campaignStats.campaign.id,
                      funnelDays,
                      funnelAsked,
                      funnel?.page || 1
                    )
                  }
                >
                  {funnelLoading ? 'Loading…' : 'Refresh funnel'}
                </button>
              </div>
            </div>

            {funnel && (
              <>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
                  <StatCard label="Targeted users" value={funnel.summary?.targeted || 0} />
                  <StatCard label="Channel delivered" value={funnel.summary?.delivered || 0} />
                  <StatCard
                    label={`Asked within ${funnel.window_days}d`}
                    value={funnel.summary?.asked || 0}
                    sub={`${(100 * (funnel.summary?.asked_rate || 0)).toFixed(1)}% of targeted`}
                  />
                  <StatCard label="Did not ask" value={funnel.summary?.not_asked || 0} />
                  <StatCard label="Clicked" value={funnel.summary?.clicked || 0} />
                  <StatCard
                    label="Directly attributed"
                    value={funnel.summary?.tap_attributed || 0}
                    sub="question carried nudge ID"
                  />
                </div>
                <div
                  style={{
                    background: '#faf9ff',
                    border: '1px solid #e7e1ff',
                    borderRadius: 8,
                    color: '#625a78',
                    fontSize: 12,
                    padding: '8px 10px',
                    marginBottom: 12,
                  }}
                >
                  “Asked within the window” shows observed activity after delivery. “Directly
                  attributed” is stronger evidence: the user entered chat through the nudge link.
                </div>

                <div className="notif-user-list nudge-scheduler-list">
                  <table className="notif-user-table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Delivery</th>
                        <th>First question</th>
                        <th style={{ width: 100 }}>Time to ask</th>
                        <th style={{ width: 90 }}>Questions</th>
                        <th style={{ width: 110 }}>Attribution</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(funnel.items || []).length === 0 ? (
                        <tr>
                          <td colSpan={6} className="notif-td-name">
                            No recipients match this filter.
                          </td>
                        </tr>
                      ) : (
                        funnel.items.map((item) => (
                          <tr key={item.user_id}>
                            <td>
                              <strong>{item.name || `User #${item.user_id}`}</strong>
                              <div className="notif-td-phone">
                                {item.phone || 'No phone'} · ID {item.user_id}
                              </div>
                            </td>
                            <td>
                              {fmtDateTime(item.delivered_at)}
                              <div className="notif-td-phone">
                                {item.channel}
                                {item.channel_delivered ? ' · sent' : ' · inbox only'}
                                {item.clicked ? ' · clicked' : ''}
                              </div>
                            </td>
                            <td>{fmtDateTime(item.first_question_at)}</td>
                            <td>{fmtHours(item.hours_to_first_question)}</td>
                            <td>{item.questions_in_window || 0}</td>
                            <td>{item.tap_attributed ? 'Nudge tap' : item.first_question_at ? 'Observed' : '—'}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {funnel.filtered_total > funnel.page_size && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: 8,
                      marginTop: 10,
                    }}
                  >
                    <button
                      type="button"
                      className="notif-search-btn"
                      disabled={funnelLoading || funnel.page <= 1}
                      onClick={() =>
                        loadCampaignFunnel(
                          campaignStats.campaign.id,
                          funnelDays,
                          funnelAsked,
                          funnel.page - 1
                        )
                      }
                    >
                      Previous
                    </button>
                    <span style={{ fontSize: 12, color: '#666' }}>
                      Page {funnel.page} of{' '}
                      {Math.ceil(funnel.filtered_total / funnel.page_size)}
                    </span>
                    <button
                      type="button"
                      className="notif-search-btn"
                      disabled={
                        funnelLoading ||
                        funnel.page * funnel.page_size >= funnel.filtered_total
                      }
                      onClick={() =>
                        loadCampaignFunnel(
                          campaignStats.campaign.id,
                          funnelDays,
                          funnelAsked,
                          funnel.page + 1
                        )
                      }
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
