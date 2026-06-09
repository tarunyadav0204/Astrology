import React, { useCallback, useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';

function formatDateTimeIST(value) {
  if (!value) return '—';
  const raw = String(value).trim();
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw);
  const normalized = hasTimezone ? raw : `${raw.replace(' ', 'T')}Z`;
  const d = new Date(normalized);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZone: 'Asia/Kolkata',
  });
}

function formatReferrerPreview(value) {
  const raw = String(value || '').trim();
  if (!raw) return '—';

  const decodeSafely = (text) => {
    try {
      return decodeURIComponent(String(text || '').replace(/\+/g, ' '));
    } catch (_) {
      return String(text || '');
    }
  };

  const lines = raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const formatted = (lines.length ? lines : [raw])
    .map((line) => {
      const eq = line.indexOf('=');
      if (eq <= 0) return decodeSafely(line);
      const key = line.slice(0, eq).trim();
      const valuePart = decodeSafely(line.slice(eq + 1).trim());
      return `${key}: ${valuePart.replace(/&/g, ' & ')}`;
    })
    .join('\n');

  return formatted.length > 500 ? `${formatted.slice(0, 500)}…` : formatted;
}

function getTodayISTDateInputValue() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const get = (type) => parts.find((part) => part.type === type)?.value || '';
  return `${get('year')}-${get('month')}-${get('day')}`;
}

const AdminAcquisition = () => {
  const todayIST = getTodayISTDateInputValue();
  const [dateFrom, setDateFrom] = useState(todayIST);
  const [dateTo, setDateTo] = useState(todayIST);
  const [registered, setRegistered] = useState('all');
  const [utmSourceInput, setUtmSourceInput] = useState('');
  const [utmSourceFilter, setUtmSourceFilter] = useState('');
  const [utmMediumInput, setUtmMediumInput] = useState('');
  const [utmMediumFilter, setUtmMediumFilter] = useState('');
  const [utmCampaignInput, setUtmCampaignInput] = useState('');
  const [utmCampaignFilter, setUtmCampaignFilter] = useState('');
  const [appBuildInput, setAppBuildInput] = useState('');
  const [appBuildFilter, setAppBuildFilter] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [total, setTotal] = useState(0);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState({
    installs: 0,
    registered: 0,
    not_registered: 0,
    registration_rate: 0,
  });
  const [analytics, setAnalytics] = useState({
    funnel: [],
    dropoff: [],
    installs: 0,
    linked: 0,
    unlinked: 0,
    existing_user_installs: 0,
    new_user_candidate_installs: 0,
    registration_flow_installs: 0,
    unknown_anonymous_installs: 0,
  });
  const [referrerModal, setReferrerModal] = useState({ visible: false, text: '' });
  const [timelineModal, setTimelineModal] = useState({ visible: false, loading: false, error: '', data: null });

  const applyUtmAndSearch = useCallback(() => {
    setUtmSourceFilter(utmSourceInput.trim());
    setUtmMediumFilter(utmMediumInput.trim());
    setUtmCampaignFilter(utmCampaignInput.trim());
    setAppBuildFilter(appBuildInput.trim());
    setPage(1);
  }, [appBuildInput, utmCampaignInput, utmMediumInput, utmSourceInput]);

  const activeFilterParams = useCallback(() => {
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (utmSourceFilter) params.utm_source = utmSourceFilter;
    if (utmMediumFilter) params.utm_medium = utmMediumFilter;
    if (utmCampaignFilter) params.utm_campaign = utmCampaignFilter;
    if (appBuildFilter) params.app_build = appBuildFilter;
    return params;
  }, [appBuildFilter, dateFrom, dateTo, utmCampaignFilter, utmMediumFilter, utmSourceFilter]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const filterParams = activeFilterParams();

      const [listRes, sumRes, analyticsRes] = await Promise.all([
        adminService.getAcquisitionInstallations({
          ...filterParams,
          registered,
          page,
          limit,
        }),
        adminService.getAcquisitionInstallationsSummary(filterParams),
        adminService.getAcquisitionInstallationsAnalytics(filterParams),
      ]);

      setItems(listRes.items || []);
      setTotal(Number(listRes.total) || 0);
      setSummary({
        installs: sumRes.installs ?? 0,
        registered: sumRes.registered ?? 0,
        not_registered: sumRes.not_registered ?? 0,
        registration_rate: sumRes.registration_rate ?? 0,
      });
      setAnalytics({
        funnel: analyticsRes.funnel || [],
        dropoff: analyticsRes.dropoff || [],
        installs: analyticsRes.installs || 0,
        linked: analyticsRes.linked || 0,
        unlinked: analyticsRes.unlinked || 0,
        existing_user_installs: analyticsRes.existing_user_installs || 0,
        new_user_candidate_installs: analyticsRes.new_user_candidate_installs || 0,
        registration_flow_installs: analyticsRes.registration_flow_installs || 0,
        unknown_anonymous_installs: analyticsRes.unknown_anonymous_installs || 0,
      });
    } catch (e) {
      setError(e?.message || 'Failed to load');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [activeFilterParams, registered, page, limit]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / limit));
  const dropoffTotal = (analytics.dropoff || []).reduce((sum, row) => sum + Number(row.installs || 0), 0);
  const openTimeline = async (installationId) => {
    if (!installationId) return;
    setTimelineModal({ visible: true, loading: true, error: '', data: null });
    try {
      const data = await adminService.getAcquisitionInstallationEvents(installationId);
      setTimelineModal({ visible: true, loading: false, error: '', data });
    } catch (e) {
      setTimelineModal({ visible: true, loading: false, error: e?.message || 'Failed to load timeline', data: null });
    }
  };

  const dropoffSeverity = (eventName, status) => {
    if (status === 'failed') return '#fee2e2';
    if (String(eventName || '').includes('otp')) return '#ffedd5';
    if (eventName === 'first_open_only' || eventName === 'auth_welcome_viewed') return '#fef9c3';
    return '#f8fafc';
  };

  return (
    <div className="users-management">
      <h2 style={{ marginBottom: 8 }}>Mobile install funnel</h2>
      <p style={{ color: '#555', marginBottom: 16, fontSize: 14 }}>
        First app opens from the mobile client (anonymous), then rows link to a user after successful login or
        registration. Dates filter on <strong>first open</strong> (UTC stored; use date range conservatively).
      </p>

      <div className="users-management-filters" style={{ marginBottom: 20 }}>
        <label>
          <span>First open from</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setPage(1);
              setDateFrom(e.target.value);
            }}
          />
        </label>
        <label>
          <span>First open to</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setPage(1);
              setDateTo(e.target.value);
            }}
          />
        </label>
        <label>
          <span>Linked user</span>
          <select
            value={registered}
            onChange={(e) => {
              setPage(1);
              setRegistered(e.target.value);
            }}
          >
            <option value="all">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </label>
        <label>
          <span>UTM source contains</span>
          <input
            type="text"
            placeholder="google-play, meta"
            value={utmSourceInput}
            onChange={(e) => setUtmSourceInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') applyUtmAndSearch();
            }}
          />
        </label>
        <label>
          <span>UTM campaign contains</span>
          <input
            type="text"
            placeholder="e.g. summer_sale"
            value={utmCampaignInput}
            onChange={(e) => setUtmCampaignInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') applyUtmAndSearch();
            }}
          />
        </label>
        <label>
          <span>UTM medium contains</span>
          <input
            type="text"
            placeholder="organic, paid_social"
            value={utmMediumInput}
            onChange={(e) => setUtmMediumInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') applyUtmAndSearch();
            }}
          />
        </label>
        <label>
          <span>App build</span>
          <input
            type="text"
            placeholder="178"
            value={appBuildInput}
            onChange={(e) => setAppBuildInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') applyUtmAndSearch();
            }}
          />
        </label>
        <button
          type="button"
          className="users-search-btn"
          onClick={() => {
            const today = getTodayISTDateInputValue();
            setDateFrom(today);
            setDateTo(today);
            setPage(1);
          }}
        >
          Today
        </button>
        <button
          type="button"
          className="users-search-btn"
          onClick={() => {
            setDateFrom('');
            setDateTo('');
            setRegistered('all');
            setUtmSourceInput('');
            setUtmSourceFilter('');
            setUtmMediumInput('');
            setUtmMediumFilter('');
            setUtmCampaignInput('');
            setUtmCampaignFilter('');
            setAppBuildInput('');
            setAppBuildFilter('');
            setPage(1);
          }}
        >
          Clear
        </button>
        <button
          type="button"
          className="users-search-btn"
          onClick={() => {
            applyUtmAndSearch();
          }}
        >
          Apply filters
        </button>
        <button
          type="button"
          className="users-search-btn"
          onClick={() => {
            load();
          }}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      <div className="users-summary-grid" style={{ marginBottom: 20 }}>
        <div className="users-summary-card">
          <h4>First opens</h4>
          <p>
            <strong>{loading ? '…' : summary.installs}</strong>
          </p>
        </div>
        <div className="users-summary-card">
          <h4>Linked user</h4>
          <p>
            <strong>{loading ? '…' : summary.registered}</strong>
          </p>
        </div>
        <div className="users-summary-card">
          <h4>Not linked</h4>
          <p>
            <strong>{loading ? '…' : summary.not_registered}</strong>
          </p>
        </div>
        <div className="users-summary-card">
          <h4>Registration rate</h4>
          <p>
            <strong>{loading ? '…' : `${(Number(summary.registration_rate) * 100).toFixed(1)}%`}</strong>
          </p>
        </div>
      </div>

      {!loading && !error ? (
        <>
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ margin: '0 0 10px' }}>New-user funnel summary</h3>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
              <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '8px 10px', background: '#f8fafc' }}>
                <div style={{ fontSize: 11, color: '#64748b' }}>All first opens</div>
                <div style={{ fontWeight: 800 }}>{analytics.installs || 0}</div>
              </div>
              <div style={{ border: '1px solid #bfdbfe', borderRadius: 8, padding: '8px 10px', background: '#eff6ff' }}>
                <div style={{ fontSize: 11, color: 'var(--admin-accent-hover)' }}>Existing/login users separated</div>
                <div style={{ fontWeight: 800 }}>{analytics.existing_user_installs || 0}</div>
              </div>
              <div style={{ border: '1px solid #bbf7d0', borderRadius: 8, padding: '8px 10px', background: '#f0fdf4' }}>
                <div style={{ fontSize: 11, color: '#15803d' }}>New-user funnel base</div>
                <div style={{ fontWeight: 800 }}>{analytics.new_user_candidate_installs || 0}</div>
              </div>
              <div style={{ border: '1px solid #fde68a', borderRadius: 8, padding: '8px 10px', background: '#fffbeb' }}>
                <div style={{ fontSize: 11, color: '#92400e' }}>No mode yet</div>
                <div style={{ fontWeight: 800 }}>{analytics.unknown_anonymous_installs || 0}</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 8 }}>
              {(analytics.funnel || []).map((step, index) => {
                const prevPct = index === 0 ? 1 : Number(step.conversion_from_previous || 0);
                const color =
                  index === 0 || prevPct >= 0.75 ? '#dcfce7' : prevPct >= 0.45 ? '#fef9c3' : '#fee2e2';
                return (
                  <div
                    key={step.event_name}
                    style={{
                      minWidth: 150,
                      border: '1px solid #e2e8f0',
                      background: color,
                      borderRadius: 8,
                      padding: 12,
                    }}
                  >
                    <div style={{ fontSize: 12, color: '#475569', marginBottom: 6 }}>{step.label}</div>
                    <div style={{ fontSize: 24, fontWeight: 800 }}>{step.count}</div>
                    <div style={{ fontSize: 12, color: '#475569' }}>
                      {index === 0
                        ? 'Start'
                        : `${(Number(step.conversion_from_previous || 0) * 100).toFixed(1)}% from previous`}
                    </div>
                    {index > 0 ? (
                      <div style={{ fontSize: 11, color: '#991b1b' }}>
                        drop {step.drop_from_previous || 0}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <h3 style={{ margin: '0 0 10px' }}>Unconverted drop-off</h3>
            <div className="users-table">
              <table>
                <thead>
                  <tr>
                    <th>Last event</th>
                    <th>Status / screen</th>
                    <th>Installs</th>
                    <th>% of unlinked</th>
                  </tr>
                </thead>
                <tbody>
                  {(analytics.dropoff || []).length === 0 ? (
                    <tr>
                      <td colSpan={4} className="users-table-empty">
                        No unconverted drop-off for this filter.
                      </td>
                    </tr>
                  ) : (
                    analytics.dropoff.map((row) => (
                      <tr
                        key={`${row.event_name}-${row.event_status}-${row.screen_name}`}
                        style={{ background: dropoffSeverity(row.event_name, row.event_status) }}
                      >
                        <td style={{ fontWeight: 700 }}>{row.event_name}</td>
                        <td>
                          {[row.event_status, row.screen_name].filter(Boolean).join(' · ') || '—'}
                        </td>
                        <td>{row.installs}</td>
                        <td>{(Number(row.share_of_unlinked || 0) * 100).toFixed(1)}%</td>
                      </tr>
                    ))
                  )}
                  {(analytics.dropoff || []).length > 0 ? (
                    <tr style={{ background: '#e0f2fe', fontWeight: 800 }}>
                      <td>Total unlinked</td>
                      <td>—</td>
                      <td>{dropoffTotal}</td>
                      <td>{analytics.unlinked ? `${((dropoffTotal / analytics.unlinked) * 100).toFixed(1)}%` : '0.0%'}</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}

      {error ? (
        <p style={{ color: '#b91c1c' }}>{error}</p>
      ) : loading ? (
        <div className="loading">Loading…</div>
      ) : (
        <>
          <div className="users-table">
            <table>
              <thead>
                <tr>
                  <th>Install ID</th>
                  <th>First open (IST)</th>
                  <th>Platform</th>
                  <th>App version / build</th>
                  <th>UTM source / medium / campaign</th>
                  <th>Opens</th>
                  <th>Last funnel event</th>
                  <th>User / lead</th>
                  <th>Linked at (IST)</th>
                  <th>Referrer preview</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="users-table-empty">
                      No rows for this filter.
                    </td>
                  </tr>
                ) : (
                  items.map((row) => {
                    const referrerPreview = formatReferrerPreview(row.referrer_preview);
                    const isUnconverted = row.userid == null;
                    const isFailed = row.last_event_status === 'failed';
                    const rowBg = isFailed ? '#fef2f2' : isUnconverted ? '#fff7ed' : undefined;
                    return (
                      <tr key={row.installation_id} style={{ background: rowBg }}>
                        <td
                          title="Open event timeline"
                          style={{
                            fontFamily: 'monospace',
                            fontSize: 12,
                            cursor: 'pointer',
                            color: 'var(--admin-accent)',
                          }}
                          onClick={() => openTimeline(row.installation_id)}
                        >
                          {row.installation_id
                            ? `${String(row.installation_id).slice(0, 8)}…${String(row.installation_id).slice(-6)}`
                            : '—'}
                        </td>
                        <td>{formatDateTimeIST(row.first_open_at)}</td>
                        <td>{row.platform || '—'}</td>
                        <td>
                          <div>{row.app_version || '—'}</div>
                          <div style={{ fontSize: 11, color: '#999' }}>
                            {row.app_build ? `build ${row.app_build}` : '—'}
                          </div>
                        </td>
                        <td>
                          {[row.utm_source, row.utm_medium, row.utm_campaign].filter(Boolean).join(' · ') || '—'}
                        </td>
                        <td>{row.open_count ?? '—'}</td>
                        <td
                          style={{ cursor: row.installation_id ? 'pointer' : 'default' }}
                          onClick={() => openTimeline(row.installation_id)}
                        >
                          {row.last_event_name ? (
                            <>
                              <div style={{ fontWeight: 600, color: isFailed ? '#b91c1c' : isUnconverted ? '#c2410c' : 'inherit' }}>
                                {row.last_event_name}
                              </div>
                              <div style={{ fontSize: 12, color: '#666' }}>
                                {[row.last_event_status, row.last_event_screen].filter(Boolean).join(' · ') || '—'}
                              </div>
                              <div style={{ fontSize: 11, color: '#999' }}>{formatDateTimeIST(row.last_event_at)}</div>
                            </>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td>
                          {row.userid != null ? (
                            <>
                              <div>{row.user_phone || '—'}</div>
                              <div style={{ fontSize: 12, color: '#666' }}>{row.user_name || ''}</div>
                              <div style={{ fontSize: 11, color: '#999' }}>id {row.userid}</div>
                            </>
                          ) : row.lead_phone || row.lead_email ? (
                            <>
                              <div style={{ color: '#c2410c', fontWeight: 700 }}>{row.lead_phone || '—'}</div>
                              <div style={{ fontSize: 12, color: '#9a3412' }}>{row.lead_email || ''}</div>
                              <div style={{ fontSize: 11, color: '#999' }}>lead contact</div>
                            </>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td>{formatDateTimeIST(row.registered_at)}</td>
                        <td
                          title={referrerPreview}
                          style={{
                            maxWidth: 280,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            cursor: referrerPreview === '—' ? 'default' : 'pointer',
                            color: referrerPreview === '—' ? 'inherit' : 'var(--admin-accent)',
                          }}
                          onClick={() => {
                            if (referrerPreview !== '—') {
                              setReferrerModal({ visible: true, text: referrerPreview });
                            }
                          }}
                        >
                          {referrerPreview}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {referrerModal.visible ? (
            <div
              role="dialog"
              aria-modal="true"
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(15, 23, 42, 0.45)',
                zIndex: 1000,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 20,
              }}
              onClick={() => setReferrerModal({ visible: false, text: '' })}
            >
              <div
                style={{
                  width: 'min(720px, 100%)',
                  maxHeight: '80vh',
                  background: '#fff',
                  borderRadius: 8,
                  boxShadow: '0 20px 45px rgba(15, 23, 42, 0.25)',
                  padding: 20,
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
                  <h3 style={{ margin: 0 }}>Referrer</h3>
                  <button
                    type="button"
                    className="users-pagination-btn"
                    onClick={() => setReferrerModal({ visible: false, text: '' })}
                  >
                    Close
                  </button>
                </div>
                <pre
                  style={{
                    marginTop: 16,
                    padding: 14,
                    borderRadius: 8,
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    maxHeight: '50vh',
                    overflow: 'auto',
                  }}
                >
                  {referrerModal.text}
                </pre>
                <button
                  type="button"
                  className="users-search-btn"
                  onClick={() => navigator.clipboard?.writeText(referrerModal.text)}
                >
                  Copy
                </button>
              </div>
            </div>
          ) : null}

          {timelineModal.visible ? (
            <div
              role="dialog"
              aria-modal="true"
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(15, 23, 42, 0.45)',
                zIndex: 1000,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 20,
              }}
              onClick={() => setTimelineModal({ visible: false, loading: false, error: '', data: null })}
            >
              <div
                style={{
                  width: 'min(820px, 100%)',
                  maxHeight: '84vh',
                  background: '#fff',
                  borderRadius: 8,
                  boxShadow: '0 20px 45px rgba(15, 23, 42, 0.25)',
                  padding: 20,
                  overflow: 'auto',
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
                  <h3 style={{ margin: 0 }}>Install event timeline</h3>
                  <button
                    type="button"
                    className="users-pagination-btn"
                    onClick={() => setTimelineModal({ visible: false, loading: false, error: '', data: null })}
                  >
                    Close
                  </button>
                </div>

                {timelineModal.loading ? (
                  <div className="loading" style={{ marginTop: 20 }}>Loading…</div>
                ) : timelineModal.error ? (
                  <p style={{ color: '#b91c1c' }}>{timelineModal.error}</p>
                ) : timelineModal.data ? (
                  <>
                    <div style={{ marginTop: 14, padding: 12, background: '#f8fafc', borderRadius: 8 }}>
                      <div style={{ fontFamily: 'monospace', fontSize: 12 }}>
                        {timelineModal.data.installation?.installation_id}
                      </div>
                      <div style={{ fontSize: 13, color: '#475569', marginTop: 6 }}>
                        First open: {formatDateTimeIST(timelineModal.data.installation?.first_open_at)}
                      </div>
                      <div style={{ fontSize: 13, color: '#475569' }}>
                        Build: {timelineModal.data.installation?.app_version || '—'} / {timelineModal.data.installation?.app_build || '—'}
                      </div>
                      <div style={{ fontSize: 13, color: '#475569' }}>
                        Attribution: {[timelineModal.data.installation?.utm_source, timelineModal.data.installation?.utm_medium, timelineModal.data.installation?.utm_campaign].filter(Boolean).join(' · ') || '—'}
                      </div>
                      <div style={{ fontSize: 13, color: timelineModal.data.installation?.userid ? '#166534' : '#c2410c' }}>
                        User: {timelineModal.data.installation?.userid
                          ? `${timelineModal.data.installation.user_phone || '—'} · ${timelineModal.data.installation.user_name || ''} · id ${timelineModal.data.installation.userid}`
                          : `Not converted${timelineModal.data.installation?.lead_phone || timelineModal.data.installation?.lead_email ? ` · lead ${[timelineModal.data.installation?.lead_phone, timelineModal.data.installation?.lead_email].filter(Boolean).join(' · ')}` : ''}`}
                      </div>
                    </div>

                    <div className="users-table" style={{ marginTop: 16 }}>
                      <table>
                        <thead>
                          <tr>
                            <th>Time</th>
                            <th>Event</th>
                            <th>Status / screen</th>
                            <th>Metadata</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(timelineModal.data.events || []).length === 0 ? (
                            <tr>
                              <td colSpan={4} className="users-table-empty">No event rows yet.</td>
                            </tr>
                          ) : (
                            timelineModal.data.events.map((event, idx) => (
                              <tr
                                key={`${event.event_name}-${event.created_at}-${idx}`}
                                style={{ background: event.event_status === 'failed' ? '#fef2f2' : undefined }}
                              >
                                <td>{formatDateTimeIST(event.created_at)}</td>
                                <td style={{ fontWeight: 700 }}>{event.event_name}</td>
                                <td>{[event.event_status, event.screen_name].filter(Boolean).join(' · ') || '—'}</td>
                                <td style={{ maxWidth: 300, wordBreak: 'break-word', fontSize: 12 }}>
                                  {event.metadata && Object.keys(event.metadata).length
                                    ? JSON.stringify(event.metadata)
                                    : '—'}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : null}
              </div>
            </div>
          ) : null}

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
            <span className="users-pagination-info">
              Page {page} of {totalPages} · {total} total
            </span>
            <button
              type="button"
              className="users-pagination-btn"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <button
              type="button"
              className="users-pagination-btn"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminAcquisition;
