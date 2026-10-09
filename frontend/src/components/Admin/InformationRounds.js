import React, { useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './InformationRounds.css';

export default function InformationRounds({ messageId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const load = async () => {
    if (loading) return;
    setLoading(true); setError('');
    try {
      const response = await fetch(`/api/admin/chat/information-rounds/${messageId}`, { headers: getAdminAuthHeaders() });
      if (!response.ok) throw new Error('Unable to load');
      setData(await response.json());
    } catch (_) { setError('Unable to load information rounds. Please try again.'); }
    finally { setLoading(false); }
  };
  const rounds = new Map();
  (data?.audit?.events || []).forEach(event => {
    const number = Number(event.round || 0);
    if (!rounds.has(number)) rounds.set(number, []);
    rounds.get(number).push(event);
  });
  return <details className="information-rounds" onToggle={event => { if (event.currentTarget.open && !data && !loading) load(); }}>
    <summary>Information rounds</summary>
    {loading && <p role="status">Loading round details…</p>}
    {error && <p role="alert">{error} <button type="button" onClick={load}>Retry</button></p>}
    {data && !data.available && <p>Detailed round information was not recorded for this answer.</p>}
    {data?.available && <p>Maximum information rounds: {data.audit.max_rounds}. Initial chart context is shown separately.</p>}
    {[...rounds.entries()].sort(([a], [b]) => a - b).map(([number, events]) => <section key={number}>
      <h4>{number === 0 ? 'Initial chart context' : `Round ${number}`}</h4>
      {events.map((event, index) => <div key={index} className="information-rounds-event">
        {event.calculator && <p><strong>Calculator:</strong> {event.calculator} {event.success === true ? '· Completed' : event.success === false ? '· Unavailable' : ''}</p>}
        {event.kind === 'progress_update' && <p><strong>Progress update:</strong> The model summarized calculations already received; no additional information was requested.</p>}
        {event.kind === 'question' && <p><strong>Asked the user:</strong> {event.text}</p>}
        {event.kind === 'user_reply' && <p><strong>User provided:</strong> {event.text}</p>}
        {(event.requested || event.requests) && <details><summary>Information requested</summary><pre>{JSON.stringify(event.requested || event.requests, null, 2)}</pre></details>}
        {event.provided !== undefined && <details><summary>Information provided</summary><pre>{JSON.stringify(event.provided, null, 2)}</pre></details>}
      </div>)}
    </section>)}
  </details>;
}
