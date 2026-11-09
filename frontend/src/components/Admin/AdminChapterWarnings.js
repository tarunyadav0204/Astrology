import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';

export default function AdminChapterWarnings() {
  const [runs, setRuns] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const load = async () => {
    setLoading(true); setError('');
    try {
      const response = await fetch('/api/next-chapter/admin/validation-warnings', { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error(`Could not load diagnostics (${response.status})`);
      setRuns((await response.json()).runs || []);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  return <div className="credits-dashboard">
    <h2>Next Chapter validation warnings</h2>
    <p>Editorial warnings do not block usable reports. Review diagnostics from the latest 100 runs, including earlier validation failures.</p>
    <button onClick={load} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button>
    {error && <p role="alert">{error}</p>}
    {!loading && !error && !runs.length && <p>No recorded validation warnings in recent runs.</p>}
    {runs.map(run => <section key={run.id}>
      <h3>{run.id}</h3><p>{run.status} · {run.created_at}</p>
      {run.warnings.map((warning, index) => <details key={index}>
        <summary>{warning.stage}: {warning.message}</summary>
        <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(warning, null, 2)}</pre>
      </details>)}
    </section>)}
  </div>;
}
