import React, { useCallback, useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const isoDaysAgo = (days) => {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
};
const todayIso = () => new Date().toISOString().slice(0, 10);

function fmtDuration(seconds) {
  if (seconds == null) return '—';
  const s = Math.round(Number(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  if (s < 86400) return `${(s / 3600).toFixed(1)}h`;
  return `${(s / 86400).toFixed(1)}d`;
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

  const loadCampaignStats = async (campaignId) => {
    setCampaignLoadingId(campaignId);
    try {
      const res = await fetch(`/api/nudge/admin/campaigns/${campaignId}/stats`, {
        headers: getAdminAuthHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || 'Failed to load campaign stats');
      setCampaignStats(body);
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
            <button type="button" className="notif-search-btn" onClick={() => setCampaignStats(null)}>
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
        </div>
      )}
    </div>
  );
}
