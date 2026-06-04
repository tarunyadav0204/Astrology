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

const AdminAcquisition = () => {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [registered, setRegistered] = useState('all');
  const [utmCampaignInput, setUtmCampaignInput] = useState('');
  const [utmCampaignFilter, setUtmCampaignFilter] = useState('');
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

  const applyUtmAndSearch = useCallback(() => {
    setUtmCampaignFilter(utmCampaignInput.trim());
    setPage(1);
  }, [utmCampaignInput]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const dateParams = {};
      if (dateFrom) dateParams.date_from = dateFrom;
      if (dateTo) dateParams.date_to = dateTo;

      const [listRes, sumRes] = await Promise.all([
        adminService.getAcquisitionInstallations({
          ...dateParams,
          registered,
          utm_campaign: utmCampaignFilter || undefined,
          page,
          limit,
        }),
        adminService.getAcquisitionInstallationsSummary(dateParams),
      ]);

      setItems(listRes.items || []);
      setTotal(Number(listRes.total) || 0);
      setSummary({
        installs: sumRes.installs ?? 0,
        registered: sumRes.registered ?? 0,
        not_registered: sumRes.not_registered ?? 0,
        registration_rate: sumRes.registration_rate ?? 0,
      });
    } catch (e) {
      setError(e?.message || 'Failed to load');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, registered, utmCampaignFilter, page, limit]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="users-management">
      <h2 style={{ marginBottom: 8 }}>Mobile install funnel</h2>
      <p style={{ color: '#555', marginBottom: 16, fontSize: 14 }}>
        First app opens from the mobile client (anonymous), then rows link to a user after successful login or
        registration. Dates filter on <strong>first open</strong> (UTC stored; use date range conservatively).
      </p>

      <div className="users-summary-grid" style={{ marginBottom: 20 }}>
        <div className="users-summary-card">
          <h4>First opens</h4>
          <p>
            <strong>{loading ? '…' : summary.installs}</strong>
          </p>
        </div>
        <div className="users-summary-card">
          <h4>Linked (registered)</h4>
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

      <div className="users-management-filters">
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
        <button
          type="button"
          className="users-search-btn"
          onClick={() => {
            applyUtmAndSearch();
          }}
        >
          Apply filters
        </button>
      </div>

      {error ? (
        <p style={{ color: '#c2185b' }}>{error}</p>
      ) : loading ? (
        <div className="loading">Loading…</div>
      ) : (
        <>
          <div className="users-table">
            <table>
              <thead>
                <tr>
                  <th>First open (IST)</th>
                  <th>Platform</th>
                  <th>App version</th>
                  <th>UTM source / medium / campaign</th>
                  <th>Opens</th>
                  <th>User</th>
                  <th>Linked at (IST)</th>
                  <th>Referrer preview</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="users-table-empty">
                      No rows for this filter.
                    </td>
                  </tr>
                ) : (
                  items.map((row) => (
                    <tr key={row.installation_id}>
                      <td>{formatDateTimeIST(row.first_open_at)}</td>
                      <td>{row.platform || '—'}</td>
                      <td>{row.app_version || '—'}</td>
                      <td>
                        {[row.utm_source, row.utm_medium, row.utm_campaign].filter(Boolean).join(' · ') || '—'}
                      </td>
                      <td>{row.open_count ?? '—'}</td>
                      <td>
                        {row.userid != null ? (
                          <>
                            <div>{row.user_phone || '—'}</div>
                            <div style={{ fontSize: 12, color: '#666' }}>{row.user_name || ''}</div>
                            <div style={{ fontSize: 11, color: '#999' }}>id {row.userid}</div>
                          </>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td>{formatDateTimeIST(row.registered_at)}</td>
                      <td title={row.referrer_preview || ''} style={{ maxWidth: 220, wordBreak: 'break-all' }}>
                        {(row.referrer_preview || '').slice(0, 120)}
                        {(row.referrer_preview || '').length > 120 ? '…' : ''}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

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
