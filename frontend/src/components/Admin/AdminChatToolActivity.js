import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminChatToolActivity.css';

const emptyFilters = { tool: '', user_id: '', user_name: '', start_date: '', end_date: '' };
const money = value => value == null ? 'Not recorded' : `₹${Number(value).toFixed(4)}`;
const date = value => value ? new Date(value).toLocaleString() : '—';
const label = tool => tool === 'summary' ? 'Summary' : 'Resolve conflicts';

export default function AdminChatToolActivity() {
  const [draft, setDraft] = useState(emptyFilters);
  const [filters, setFilters] = useState(emptyFilters);
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState({ items: [], total: 0, total_pages: 1 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    const params = new URLSearchParams({ page: String(page), limit: '30' });
    Object.entries(filters).forEach(([key, value]) => { if (String(value).trim()) params.set(key, String(value).trim()); });
    fetch(`/api/admin/chat/tool-activity?${params}`, { headers: getAdminAuthHeaders(), signal: controller.signal })
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Could not load chat tools activity.');
        return body;
      }).then(body => { if (!controller.signal.aborted) setData(body); })
      .catch(err => { if (!controller.signal.aborted) { setError(err.message); setData({ items: [], total: 0, total_pages: 1 }); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [filters, page, revision]);
  const field = (key, value) => setDraft(previous => ({ ...previous, [key]: value }));
  return <section className="chat-tool-activity">
    <h2>Chat Tools Activity</h2>
    <p>See who summarized answers or resolved conflicts, the messages they selected, and the model usage for each request.</p>
    <form className="chat-tool-filters" onSubmit={event => { event.preventDefault(); setFilters({ ...draft }); setPage(1); }}>
      <label>Tool<select value={draft.tool} onChange={event => field('tool', event.target.value)}><option value="">All tools</option><option value="summary">Summary</option><option value="conflict_resolution">Resolve conflicts</option></select></label>
      <label>User ID<input type="number" min="1" value={draft.user_id} onChange={event => field('user_id', event.target.value)} /></label>
      <label>Username<input value={draft.user_name} onChange={event => field('user_name', event.target.value)} placeholder="Search name" /></label>
      <label>From (UTC)<input type="date" value={draft.start_date} onChange={event => field('start_date', event.target.value)} /></label>
      <label>To (UTC)<input type="date" value={draft.end_date} onChange={event => field('end_date', event.target.value)} /></label>
      <button type="submit" disabled={loading}>Apply filters</button>
      <button type="button" disabled={loading} onClick={() => { setDraft(emptyFilters); setFilters(emptyFilters); setPage(1); setRevision(value => value + 1); }}>Reset</button>
      <button type="button" disabled={loading} onClick={() => setRevision(value => value + 1)}>Refresh</button>
    </form>
    {error && <p role="alert" className="chat-tool-error">{error}</p>}
    <p aria-live="polite">{loading ? 'Loading activity…' : `${data.total} requests`}</p>
    <div className="chat-tool-table-wrap"><table><thead><tr><th>Time / User</th><th>Tool / Status</th><th>Model / Tokens</th><th>Model cost</th><th>Messages and result</th></tr></thead><tbody>
      {!loading && !data.items.length && !error && <tr><td colSpan="5">No activity matches these filters.</td></tr>}
      {data.items.map(item => <tr key={`${item.tool}:${item.id}`}>
        <td><strong>{item.user_name}</strong><small>User ID: {item.user_id}</small><small>{date(item.created_at)}</small><small>Updated: {date(item.updated_at)}</small></td>
        <td><strong>{label(item.tool)}</strong><small>{item.status}{item.cached ? ' · Cached result' : ''}{item.legacy ? ' · Historical record' : ''}</small>{item.rounds != null && <small>{item.rounds} model rounds</small>}{item.error_type && <small className="chat-tool-error">{item.error_type}</small>}</td>
        <td><strong>{item.model || 'Model not recorded'}</strong>{item.provider_model && item.provider_model !== item.model && <small>API model: {item.provider_model}</small>}{item.usage ? <><small>Input: {item.usage.input_tokens.toLocaleString()}</small><small>Cached input: {item.usage.cached_tokens.toLocaleString()}</small><small>Output: {item.usage.output_tokens.toLocaleString()}</small></> : <small>Tokens not recorded</small>}</td>
        <td><strong>{money(item.cost_inr)}</strong>{item.cost_usd != null && <small>${Number(item.cost_usd).toFixed(6)} USD</small>}<small>{item.cached ? 'No new model call' : item.cost_basis === 'measured_tokens_estimate' ? 'Estimate from measured tokens' : item.cost_basis === 'model_rate_unavailable' ? 'Model rate unavailable' : item.cost_basis === 'no_model_usage' ? 'No measured model usage yet' : 'Usage unavailable'}</small></td>
        <td><details><summary>View {item.sources.length || 'source'} messages and result</summary>
          <small>Activity ID: {item.id}</small>{item.session_id && <small>Conversation: {item.session_id}</small>}
          {item.legacy && <p>This historical summary predates source and usage tracking. Those details cannot be reconstructed.</p>}
          {item.concern && <><h4>User concern</h4><pre>{item.concern}</pre></>}
          {item.sources.map((source, index) => <article className="chat-tool-source" key={`${source.answer_id}:${index}`}><h4>Answer #{source.answer_id}</h4><small>Conversation: {source.session_id || item.session_id || 'Not recorded'}</small><h5>Question</h5><pre>{source.question || 'Not recorded'}</pre><h5>Answer</h5><pre>{source.answer || 'Not recorded'}</pre></article>)}
          <h4>{item.tool === 'summary' ? 'Summary result' : 'Resolution result'}</h4><pre>{item.result || (item.resolution ? JSON.stringify(item.resolution, null, 2) : 'No completed result yet.')}</pre>
          {item.question && <><h4>Clarification requested</h4><pre>{item.question}</pre></>}
          {!!item.events.length && <details><summary>Resolution progress</summary><pre>{JSON.stringify(item.events, null, 2)}</pre></details>}
        </details></td>
      </tr>)}
    </tbody></table></div>
    <div className="chat-tool-pagination"><button disabled={loading || page <= 1} onClick={() => setPage(value => value - 1)}>Previous</button><span>Page {page} of {data.total_pages}</span><button disabled={loading || page >= data.total_pages} onClick={() => setPage(value => value + 1)}>Next</button></div>
    <p className="chat-tool-note">{data.cost_note} Exchange rate: ₹{data.usd_to_inr || '—'} per USD. Costs shown are provider cost estimates, not user credit charges.</p>
  </section>;
}
