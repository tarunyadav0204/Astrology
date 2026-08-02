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
    hour12: true,
    timeZone: 'Asia/Kolkata',
  });
}

export default function AdminPandits() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [pincode, setPincode] = useState('');
  const [pincodeInput, setPincodeInput] = useState('');
  const [verifiedFilter, setVerifiedFilter] = useState('all');
  const [q, setQ] = useState('');
  const [qInput, setQInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [togglingUserId, setTogglingUserId] = useState(null);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const loadList = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getAdminPandits({
        page,
        limit,
        pincode: pincode || undefined,
        q: q || undefined,
        verified_jobs:
          verifiedFilter === 'all' ? undefined : verifiedFilter === 'yes',
      });
      setItems(data.items || []);
      setTotal(Number(data.total) || 0);
    } catch (e) {
      setError(e?.message || 'Failed to load pandits');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, limit, pincode, q, verifiedFilter]);

  useEffect(() => {
    loadList();
  }, [loadList]);

  const applyFilters = (e) => {
    e?.preventDefault?.();
    setPage(1);
    setPincode(String(pincodeInput || '').replace(/\D/g, '').slice(0, 10));
    setQ(String(qInput || '').trim());
  };

  const toggleVerified = async (item) => {
    const userid = item.userid;
    setTogglingUserId(userid);
    setError('');
    try {
      const next = !item.verified_jobs;
      await adminService.patchAdminPandit(userid, { verified_jobs: next });
      setItems((prev) =>
        prev.map((row) =>
          row.userid === userid ? { ...row, verified_jobs: next } : row
        )
      );
    } catch (e) {
      setError(e?.message || 'Failed to update verified_jobs');
    } finally {
      setTogglingUserId(null);
    }
  };

  return (
    <div className="admin-section" style={{ padding: 16 }}>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: '0 0 4px', fontSize: 20 }}>Pandits</h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: 13 }}>
          Practice profiles for Pandit Desk. Mark verified_jobs candidates for future puja routing.
        </p>
      </div>

      <form
        onSubmit={applyFilters}
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 10,
          alignItems: 'flex-end',
          marginBottom: 16,
          padding: 12,
          background: '#f8fafc',
          borderRadius: 8,
          border: '1px solid #e2e8f0',
        }}
      >
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, color: '#475569' }}>
          Pincode prefix
          <input
            value={pincodeInput}
            onChange={(e) => setPincodeInput(e.target.value.replace(/\D/g, '').slice(0, 10))}
            placeholder="e.g. 1100"
            style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', minWidth: 120 }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, color: '#475569' }}>
          Search
          <input
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            placeholder="Name, city, phone"
            style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', minWidth: 180 }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, color: '#475569' }}>
          Jobs verified
          <select
            value={verifiedFilter}
            onChange={(e) => {
              setVerifiedFilter(e.target.value);
              setPage(1);
            }}
            style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1' }}
          >
            <option value="all">All</option>
            <option value="yes">Verified only</option>
            <option value="no">Not verified</option>
          </select>
        </label>
        <button
          type="submit"
          style={{
            padding: '8px 14px',
            borderRadius: 6,
            border: 'none',
            background: '#0f172a',
            color: '#fff',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Apply
        </button>
      </form>

      {error ? (
        <div style={{ marginBottom: 12, padding: 10, background: '#fef2f2', color: '#b91c1c', borderRadius: 6 }}>
          {error}
        </div>
      ) : null}

      <div style={{ marginBottom: 8, fontSize: 13, color: '#64748b' }}>
        {loading ? 'Loading…' : `${total} pandit${total === 1 ? '' : 's'}`}
      </div>

      <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
              <th style={{ padding: 10 }}>Practice</th>
              <th style={{ padding: 10 }}>City / Pincode</th>
              <th style={{ padding: 10 }}>User</th>
              <th style={{ padding: 10 }}>Puja types</th>
              <th style={{ padding: 10 }}>Joined</th>
              <th style={{ padding: 10 }}>verified_jobs</th>
            </tr>
          </thead>
          <tbody>
            {!loading && items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: 20, color: '#94a3b8', textAlign: 'center' }}>
                  No pandit profiles match these filters.
                </td>
              </tr>
            ) : null}
            {items.map((item) => (
              <tr key={item.userid} style={{ borderTop: '1px solid #e2e8f0' }}>
                <td style={{ padding: 10 }}>
                  <div style={{ fontWeight: 600 }}>{item.display_name || '—'}</div>
                  <div style={{ color: '#64748b', fontSize: 12 }}>
                    #{item.userid}
                    {item.setup_complete ? '' : ' · setup incomplete'}
                  </div>
                </td>
                <td style={{ padding: 10 }}>
                  <div>{item.city || '—'}</div>
                  <div style={{ fontFamily: 'monospace', color: '#0f172a' }}>{item.pincode || '—'}</div>
                </td>
                <td style={{ padding: 10 }}>
                  <div>{item.user_name || '—'}</div>
                  <div style={{ color: '#64748b', fontSize: 12 }}>
                    {item.user_phone || item.phone || '—'}
                  </div>
                </td>
                <td style={{ padding: 10, maxWidth: 180 }}>
                  {(item.puja_types || []).length
                    ? item.puja_types.join(', ')
                    : '—'}
                </td>
                <td style={{ padding: 10, whiteSpace: 'nowrap' }}>
                  {formatDateTimeIST(item.created_at)}
                </td>
                <td style={{ padding: 10 }}>
                  <label
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      cursor: togglingUserId === item.userid ? 'wait' : 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={!!item.verified_jobs}
                      disabled={togglingUserId === item.userid}
                      onChange={() => toggleVerified(item)}
                    />
                    <span
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        color: item.verified_jobs ? '#166534' : '#64748b',
                      }}
                    >
                      {item.verified_jobs ? 'Candidate' : 'Not yet'}
                    </span>
                  </label>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 12 }}>
        <button
          type="button"
          disabled={page <= 1 || loading}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1', background: '#fff' }}
        >
          Prev
        </button>
        <span style={{ fontSize: 13, color: '#475569' }}>
          Page {page} / {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages || loading}
          onClick={() => setPage((p) => p + 1)}
          style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1', background: '#fff' }}
        >
          Next
        </button>
      </div>
    </div>
  );
}
