import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { adminService } from '../../services/adminService';

function when(value) {
  if (!value) return 'Never';
  return new Date(value).toLocaleString('en-IN');
}

const cardStyle = {
  border: '1px solid #e5e7eb',
  borderRadius: 8,
  padding: 14,
  background: '#fff',
};

const AdminGcpExpenseImport = ({ vendors, paidByList, onSynced }) => {
  const [status, setStatus] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [savingId, setSavingId] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const activeVendors = useMemo(() => vendors.filter((row) => row.is_active), [vendors]);
  const activePaidBy = useMemo(() => paidByList.filter((row) => row.is_active), [paidByList]);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getGcpExpenseIntegrationStatus();
      setStatus(data);
    } catch (e) {
      setError(e?.message || 'Failed to load GCP integration');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const discover = async () => {
    setDiscovering(true);
    setError('');
    setMessage('');
    try {
      const data = await adminService.discoverGcpBillingAccounts();
      const found = data.items || [];
      setAccounts(found);
      const nextDrafts = {};
      found.forEach((account) => {
        const config = account.configuration || {};
        nextDrafts[account.billing_account_id] = {
          display_name: config.display_name || `GCP ${account.billing_account_id}`,
          vendor_id: config.vendor_id ? String(config.vendor_id) : '',
          paid_by_id: config.paid_by_id ? String(config.paid_by_id) : '',
          category: config.category || 'Cloud infrastructure',
          is_active: config.is_active !== false,
        };
      });
      setDrafts(nextDrafts);
      setMessage(`Found ${found.length} billing account${found.length === 1 ? '' : 's'}.`);
    } catch (e) {
      setError(e?.message || 'Account discovery failed');
    } finally {
      setDiscovering(false);
    }
  };

  const setDraft = (accountId, patch) => {
    setDrafts((current) => ({
      ...current,
      [accountId]: { ...(current[accountId] || {}), ...patch },
    }));
  };

  const saveAccount = async (account) => {
    const accountId = account.billing_account_id;
    const draft = drafts[accountId] || {};
    if (!draft.vendor_id || !draft.paid_by_id) {
      setError('Select a vendor and paid-by entry before enabling this account.');
      return;
    }
    setSavingId(accountId);
    setError('');
    setMessage('');
    try {
      await adminService.configureGcpBillingAccount(accountId, {
        billing_account_id: accountId,
        display_name: (draft.display_name || '').trim(),
        vendor_id: Number(draft.vendor_id),
        paid_by_id: Number(draft.paid_by_id),
        category: (draft.category || '').trim(),
        is_active: Boolean(draft.is_active),
      });
      setMessage(`Saved GCP billing account ${accountId}.`);
      await Promise.all([loadStatus(), discover()]);
    } catch (e) {
      setError(e?.message || 'Could not save billing account');
    } finally {
      setSavingId('');
    }
  };

  const syncAll = async () => {
    setSyncing(true);
    setError('');
    setMessage('');
    try {
      const result = await adminService.syncGcpExpenses();
      setMessage(
        `Sync complete: ${result.expenses_created} created, ${result.expenses_updated} updated from ${result.rows_fetched} cost lines.`,
      );
      await loadStatus();
      if (onSynced) await onSynced();
    } catch (e) {
      setError(e?.message || 'GCP sync failed');
      await loadStatus();
    } finally {
      setSyncing(false);
    }
  };

  if (loading && !status) return <div className="loading">Loading GCP billing integration…</div>;

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ ...cardStyle, marginBottom: 16 }}>
        <h3 style={{ margin: '0 0 8px', fontSize: 17 }}>Google Cloud Billing</h3>
        <p style={{ color: '#555', fontSize: 14, margin: '0 0 12px' }}>
          Imports net Cloud Billing cost after credits from BigQuery. Each billing account produces one expense per
          invoice month and currency; the current month is marked provisional.
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span
            style={{
              padding: '4px 9px',
              borderRadius: 999,
              fontSize: 12,
              color: status?.table_configured ? '#166534' : '#92400e',
              background: status?.table_configured ? '#dcfce7' : '#fef3c7',
            }}
          >
            {status?.table_configured ? 'BigQuery table configured' : 'BigQuery table not configured'}
          </span>
          {status?.table_ref ? <code style={{ fontSize: 12 }}>{status.table_ref}</code> : null}
        </div>
        {!status?.table_configured ? (
          <p style={{ color: '#92400e', fontSize: 13, marginBottom: 0 }}>
            Set <code>GCP_BILLING_EXPORT_TABLE</code> on the backend to the fully qualified Cloud Billing export table.
          </p>
        ) : null}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <button
          type="button"
          className="users-search-btn"
          onClick={discover}
          disabled={!status?.table_configured || discovering}
        >
          {discovering ? 'Discovering…' : 'Discover billing accounts'}
        </button>
        <button
          type="button"
          className="users-search-btn"
          style={{ background: '#1a73e8' }}
          onClick={syncAll}
          disabled={syncing || !(status?.accounts || []).some((row) => row.is_active)}
        >
          {syncing ? 'Syncing GCP…' : 'Sync all active accounts'}
        </button>
      </div>

      {message ? <p style={{ color: '#166534' }}>{message}</p> : null}
      {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

      {accounts.length > 0 ? (
        <div style={{ display: 'grid', gap: 14, marginBottom: 20 }}>
          {accounts.map((account) => {
            const draft = drafts[account.billing_account_id] || {};
            return (
              <div key={account.billing_account_id} style={cardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div>
                    <strong>{account.billing_account_id}</strong>
                    <div style={{ color: '#666', fontSize: 12 }}>
                      Latest invoice month: {account.latest_invoice_month || '—'} · Currency: {account.currency || '—'}
                    </div>
                  </div>
                  <label style={{ display: 'inline-flex', flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <input
                      type="checkbox"
                      checked={draft.is_active !== false}
                      onChange={(e) => setDraft(account.billing_account_id, { is_active: e.target.checked })}
                    />
                    Active
                  </label>
                </div>
                <div className="users-management-filters" style={{ marginTop: 12 }}>
                  <label>
                    <span>Display name</span>
                    <input
                      value={draft.display_name || ''}
                      onChange={(e) => setDraft(account.billing_account_id, { display_name: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Vendor</span>
                    <select
                      value={draft.vendor_id || ''}
                      onChange={(e) => setDraft(account.billing_account_id, { vendor_id: e.target.value })}
                    >
                      <option value="">Select vendor…</option>
                      {activeVendors.map((row) => (
                        <option key={row.id} value={String(row.id)}>{row.label}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Paid by</span>
                    <select
                      value={draft.paid_by_id || ''}
                      onChange={(e) => setDraft(account.billing_account_id, { paid_by_id: e.target.value })}
                    >
                      <option value="">Select paid by…</option>
                      {activePaidBy.map((row) => (
                        <option key={row.id} value={String(row.id)}>{row.label}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Category</span>
                    <input
                      value={draft.category || ''}
                      onChange={(e) => setDraft(account.billing_account_id, { category: e.target.value })}
                    />
                  </label>
                  <button
                    type="button"
                    className="users-search-btn"
                    onClick={() => saveAccount(account)}
                    disabled={savingId === account.billing_account_id}
                  >
                    {savingId === account.billing_account_id ? 'Saving…' : 'Save account'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {(status?.accounts || []).length > 0 ? (
        <div style={{ ...cardStyle, marginBottom: 16 }}>
          <h3 style={{ marginTop: 0, fontSize: 16 }}>Configured accounts</h3>
          <div className="users-table">
            <table>
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Vendor</th>
                  <th>Paid by</th>
                  <th>Status</th>
                  <th>Last sync</th>
                </tr>
              </thead>
              <tbody>
                {status.accounts.map((row) => (
                  <tr key={row.billing_account_id}>
                    <td>{row.display_name || row.billing_account_id}<br /><small>{row.billing_account_id}</small></td>
                    <td>{row.vendor}</td>
                    <td>{row.paid_by}</td>
                    <td>{row.is_active ? row.last_sync_status || 'Ready' : 'Inactive'}</td>
                    <td>{when(row.last_sync_completed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {(status?.recent_runs || []).length > 0 ? (
        <details style={cardStyle}>
          <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Recent sync runs</summary>
          <div className="users-table" style={{ marginTop: 12 }}>
            <table>
              <thead>
                <tr>
                  <th>Started</th>
                  <th>Status</th>
                  <th>Cost lines</th>
                  <th>Created</th>
                  <th>Updated</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {status.recent_runs.map((run) => (
                  <tr key={run.id}>
                    <td>{when(run.started_at)}</td>
                    <td>{run.status}</td>
                    <td>{run.rows_fetched}</td>
                    <td>{run.expenses_created}</td>
                    <td>{run.expenses_updated}</td>
                    <td style={{ maxWidth: 280, wordBreak: 'break-word' }}>{run.error || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </div>
  );
};

export default AdminGcpExpenseImport;
