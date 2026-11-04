import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

const money = (value) => `₹${Number(value || 0).toFixed(2)}`;

export default function AdminReelCosts() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const load = async () => {
    setLoading(true); setError('');
    try {
      const response = await fetch('/api/reel-studio/admin/runs?limit=100', { headers: getAdminAuthHeaders() });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
      setData(body);
    } catch (e) { setError(e.message || 'Could not load reel costs'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const runs = data?.runs || [];
  const total = runs.reduce((sum, run) => sum + Number(run.actual_total_inr || 0), 0);
  return <div className="credits-dashboard">
    <h2>Reel Generation Costs</h2>
    <p className="credit-settings-hint">Actual recorded provider cost in INR for every Reel Studio run. Each row includes image, Omni video, podcast TTS, and render charges recorded by the worker.</p>
    <div className="dashboard-controls"><button type="button" className="preset-btn active" onClick={load} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button></div>
    {error ? <div className="credits-dashboard-error">{error}</div> : null}
    {data ? <>
      <div className="metrics-grid question-cost-metrics-grid"><div className="metric-card"><h4>Recorded runs</h4><p>{runs.length}</p></div><div className="metric-card"><h4>Actual provider cost</h4><p>{money(total)}</p><small>Last {runs.length} runs</small></div></div>
      <div className="transactions-table wrap question-cost-table-wrap"><table><thead><tr><th>Run</th><th>Status</th><th>Actual cost</th><th>Charges</th></tr></thead><tbody>
        {runs.map((run) => <tr key={run.job_id}><td><code>{run.job_id}</code><br /><small>{run.created_at ? new Date(run.created_at).toLocaleString() : '—'}</small></td><td>{run.status}</td><td><strong>{money(run.actual_total_inr)}</strong></td><td>{run.charges.length ? run.charges.map((charge, index) => <div key={`${charge.provider}-${index}`}><small>{charge.stage} · {charge.provider} · {money(charge.total_inr)}{charge.recovered_from_usage ? ' · recovered from provider usage' : ''}</small></div>) : <small>No measured charges recorded.</small>}</td></tr>)}
        {!runs.length ? <tr><td colSpan="4">No reel runs yet.</td></tr> : null}
      </tbody></table></div>
    </> : null}
  </div>;
}
