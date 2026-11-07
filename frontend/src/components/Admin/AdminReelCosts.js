import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const money = value => value == null ? 'Unknown' : `₹${Number(value).toFixed(2)}`;
const fields = {
  usd_to_inr: 'USD to INR exchange rate', tax_percent: 'Effective tax %',
  payment_fee_percent: 'Payment / FX fee % (after tax)',
  worker_inr_per_second: 'Allocated worker cost ₹ / second',
  storage_inr_per_gib_month: 'Storage ₹ / GiB / month',
  storage_months: 'Storage months to budget', upload_inr_per_gib: 'Upload transfer ₹ / GiB',
  storage_write_inr_per_1000: 'Storage writes ₹ / 1,000 operations',
};
async function api(path, options = {}) {
  const response = await fetch(`/api/reel-studio${path}`, {
    ...options, headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status})`);
  return body;
}
export default function AdminReelCosts() {
  const [data, setData] = useState(null);
  const [settings, setSettings] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reconcile, setReconcile] = useState(null);
  const load = async () => {
    setLoading(true); setError('');
    try {
      const [runs, config] = await Promise.all([api('/admin/runs?limit=100'), api('/admin/cost-settings')]);
      setData(runs); setSettings(config);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const save = async event => {
    event.preventDefault(); setSaving(true); setError(''); setNotice('');
    try {
      await api('/admin/cost-settings', { method: 'PUT', body: JSON.stringify(settings) });
      setNotice('Saved. New runs use these rates; existing runs retain their original rate snapshot.');
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };
  const confirmInvoice = async event => {
    event.preventDefault(); setSaving(true); setError('');
    try {
      await api(`/admin/runs/${encodeURIComponent(reconcile.run_id)}/reconcile`, {
        method: 'POST', body: JSON.stringify({ total_inr: Number(reconcile.total), reference: reconcile.reference }),
      });
      setReconcile(null); await load();
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };
  const runs = data?.runs || [];
  const total = runs.reduce((sum, run) => sum + Number(run.estimated_total_inr || 0), 0);
  const incomplete = runs.filter(run => !run.cost_complete).length;
  return <div className="credits-dashboard">
    <h2>Reel Generation Costs</h2>
    <p className="credit-settings-hint">Planning, repairs, images (including input images), narration, presenter videos, compute and storage. Includes unsuccessful attempts. Usage estimates are separate from invoice-confirmed costs.</p>
    <button type="button" className="preset-btn active" onClick={load} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button>
    {error && <div role="alert" className="credits-dashboard-error">{error}</div>}
    {notice && <p role="status">{notice}</p>}
    {settings && <details style={{ margin: '20px 0' }}><summary>Cost assumptions and additional charges</summary>
      <p>Leave unknown charges blank. Enter 0 only when confirmed free or included elsewhere. Worker cost allocates shared server capacity per active job, including time waiting for providers. Tax applies to the subtotal; payment fees apply after tax.</p>
      <form onSubmit={save}><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 16 }}>
        {Object.entries(fields).map(([key, label]) => <label key={key}>{label}<input aria-label={label} type="number" min="0" step="any"
          required={key === 'usd_to_inr' || key === 'storage_months'} value={settings[key] ?? ''}
          style={{ display: 'block', width: '100%', padding: 8 }}
          onChange={e => setSettings({ ...settings, [key]: e.target.value === '' ? null : Number(e.target.value) })} /></label>)}
      </div><button disabled={saving} type="submit">Save assumptions</button></form>
    </details>}
    {data && <>
      <div className="metrics-grid question-cost-metrics-grid">
        <div className="metric-card"><h4>Recorded runs</h4><p>{runs.length}</p></div>
        <div className="metric-card"><h4>Known cost estimate</h4><p>{money(total)}</p><small>{incomplete} runs have missing costs</small></div>
      </div><p className="credit-settings-hint">{data.note}</p>
      <div className="transactions-table wrap question-cost-table-wrap"><table><thead><tr><th>Run</th><th>Status</th><th>Cost in INR</th><th>Breakdown</th></tr></thead><tbody>
        {runs.map(run => <tr key={run.run_id}>
          <td><code>{run.job_id || run.run_id}</code><br /><small>{run.created_at ? new Date(run.created_at).toLocaleString() : '—'}</small></td>
          <td>{run.status}</td>
          <td><strong>{money(run.estimated_total_inr)}</strong><br /><small>{run.cost_complete ? 'Complete estimate' : 'Partial estimate — costs missing'}</small>
            <div>Subtotal: {money(run.known_subtotal_inr)}<br />Tax: {money(run.tax_inr)}<br />Fees: {money(run.payment_fee_inr)}</div>
            <small>FX: ₹{run.pricing_config?.usd_to_inr} / USD</small>
            {run.actual_total_inr != null && <p><strong>Invoice confirmed: {money(run.actual_total_inr)}</strong><br />{run.invoice_reference}</p>}
            <button type="button" disabled={!run.charges.length} onClick={() => setReconcile({ run_id: run.run_id, total: '', reference: '' })}>Reconcile invoice</button>
          </td><td>{run.missing_costs?.length > 0 && <p style={{ color: '#944100' }}>{run.missing_costs.join('; ')}</p>}
            {run.charges.map((charge, index) => <details key={index} style={{ marginBottom: 6 }}>
              <summary>{charge.stage} · {charge.provider} · {money(charge.total_inr)}</summary>
              <small>{charge.basis} · {charge.metadata?.state || 'Legacy record'}</small>
              <pre style={{ whiteSpace: 'pre-wrap', maxWidth: 480 }}>{JSON.stringify({ usage: charge.metadata?.usage, components: charge.metadata?.components, request_id: charge.metadata?.request_id }, null, 2)}</pre>
            </details>)}{!run.charges.length && <small>No usage recorded yet.</small>}
          </td></tr>)}
        {!runs.length && <tr><td colSpan="4">No reel runs yet.</td></tr>}
      </tbody></table></div>
    </>}
    {reconcile && <form onSubmit={confirmInvoice} style={{ padding: 20, border: '1px solid #ccc', marginTop: 20 }}>
      <h3>Reconcile {reconcile.run_id}</h3>
      <p>Enter the allocated invoice total including tax, fees, infrastructure and credits. This records an audited adjustment without replacing usage records.</p>
      <label>Invoice total in INR <input type="number" min="0" step="any" required value={reconcile.total} onChange={e => setReconcile({ ...reconcile, total: e.target.value })} /></label>
      <label>Invoice reference / allocation note <input required minLength={3} maxLength={500} value={reconcile.reference} onChange={e => setReconcile({ ...reconcile, reference: e.target.value })} /></label>
      <button type="submit" disabled={saving}>Record confirmed total</button><button type="button" onClick={() => setReconcile(null)}>Cancel</button>
    </form>}
  </div>;
}
