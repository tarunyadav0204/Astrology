import React, { useEffect, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminEvidenceErrors.css';

const initial = { username: '', start_date: '', end_date: '', chat_type: '' };
const labels = { mismatches: 'Confirmed mismatches', unverified: 'Unverified claims', failures: 'Audit failures' };
const unverified = ['unsupported', 'ambiguous', 'invalid_extraction', 'calculation_failed'];
const displayStatus = status => ({ unsupported: 'Not verified (coverage)', ambiguous: 'Needs context', invalid_extraction: 'Extraction issue', calculation_failed: 'Calculator error' })[status] || status;
async function get(url, signal) {
  const response = await fetch(url, { headers: getAdminAuthHeaders(), signal });
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Could not load evidence audits.');
  return body;
}

export default function AdminEvidenceErrors() {
  const [draft, setDraft] = useState(initial);
  const [filters, setFilters] = useState(initial);
  const [view, setView] = useState('mismatches');
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState({ items: [], total: 0, total_pages: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailError, setDetailError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(''); setSelected(null); setDetail(null);
    const params = new URLSearchParams({ view, page: String(page), limit: '25' });
    Object.entries(filters).forEach(([key,value]) => { if (value.trim()) params.set(key,value.trim()); });
    get(`/api/admin/chat/evidence-errors?${params}`,controller.signal)
      .then(body => { if (!controller.signal.aborted) setData(body); })
      .catch(e => { if (!controller.signal.aborted) setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [filters, view, page, revision]);
  useEffect(() => {
    if (!selected) return undefined;
    const controller = new AbortController();
    setDetail(null); setDetailError('');
    get(`/api/admin/chat/evidence-audit/${selected.message_id}`,controller.signal)
      .then(body => { if (!controller.signal.aborted) setDetail(body); })
      .catch(e => { if (!controller.signal.aborted) setDetailError(e.message); });
    return () => controller.abort();
  }, [selected]);
  const findings = (detail?.evaluator_result?.fact_checks || []).filter(row => view === 'mismatches' ? row.status === 'mismatch' : view === 'unverified' ? unverified.includes(row.status) : false);
  return <section className="admin-evidence-errors">
    <h2>Evidence Errors</h2>
    <div role="tablist" aria-label="Evidence audit views">
      {Object.entries(labels).map(([key,label]) => <button key={key} role="tab" aria-selected={view === key} onClick={() => { setView(key); setPage(1); }}>{label}</button>)}
    </div>
    <p>{view === 'mismatches' ? 'Only answers with calculator-confirmed mismatches. Model opinions and unverified claims are excluded.' : view === 'unverified' ? 'Claims that could not be checked. These are not confirmed factual errors. An answer may also have separate mismatches.' : 'Audits that failed to finish. Customer answers were not rejected.'}</p>
    <form onSubmit={e => { e.preventDefault(); setFilters({ ...draft }); setPage(1); }}>
      <label>Username<input value={draft.username} onChange={e => setDraft({ ...draft, username: e.target.value })} /></label>
      <label>Start date (IST)<input type="date" value={draft.start_date} max={draft.end_date || undefined} onChange={e => setDraft({ ...draft, start_date: e.target.value })} /></label>
      <label>End date (IST)<input type="date" value={draft.end_date} min={draft.start_date || undefined} onChange={e => setDraft({ ...draft, end_date: e.target.value })} /></label>
      <label>Chat type<select value={draft.chat_type} onChange={e => setDraft({ ...draft, chat_type: e.target.value })}>
        <option value="">All types</option>{['standard','premium','instant','speech','verified'].map(type => <option key={type} value={type}>{type[0].toUpperCase()+type.slice(1)}</option>)}
      </select></label>
      <button type="submit">Apply filters</button>
      <button type="button" onClick={() => { setDraft(initial); setFilters(initial); setPage(1); }}>Reset</button>
      <button type="button" onClick={() => setRevision(value => value+1)}>Refresh</button>
    </form>
    {error && <p role="alert">{error}</p>}
    {loading ? <p role="status">Loading evidence audits…</p> : !error && <>
      <p>{data.total} matching answers · Dates use answer time in Asia/Kolkata.</p>
      {!data.items.length ? <p>No {labels[view].toLowerCase()} found for these filters.</p> : <div className="evidence-table-scroll"><table>
        <thead><tr><th>Date (IST)</th><th>User</th><th>Chat type</th><th>Question</th><th>{view === 'failures' ? 'Failure' : 'Findings'}</th><th>Details</th></tr></thead>
        <tbody>{data.items.map(item => <tr key={item.message_id}>
          <td>{item.answer_at ? new Date(item.answer_at).toLocaleString('en-IN',{ timeZone: 'Asia/Kolkata' }) : '—'}</td>
          <td>{item.username}<small>User #{item.user_id}</small></td><td>{item.chat_type}</td>
          <td>{item.question || 'Question not captured'}<small>Answer #{item.message_id}</small></td>
          <td>{view === 'failures' ? item.error_message || 'Audit failed' : view === 'mismatches' ? `${item.mismatch_count} mismatches` : `${item.unverified_count} unverified`}</td>
          <td><button onClick={() => setSelected(item)}>View findings</button></td>
        </tr>)}</tbody></table></div>}
      <nav aria-label="Evidence errors pagination"><button disabled={page <= 1} onClick={() => setPage(value => value-1)}>Previous</button> Page {page} of {data.total_pages} <button disabled={page >= data.total_pages} onClick={() => setPage(value => value+1)}>Next</button></nav>
    </>}
    {selected && <div className="evidence-detail" aria-label="Evidence finding details">
      <button onClick={() => setSelected(null)}>Close details</button>
      <h3>Answer #{selected.message_id} · {selected.username}</h3><p>{selected.question}</p>
      {detailError ? <p role="alert">{detailError}</p> : !detail ? <p>Loading findings…</p> : <>
        {!detail.found ? <p>Audit no longer available.</p> : <>
          {detail.status === 'failed' && <p role="alert">{detail.error_message}</p>}
          {findings.map((finding,index) => <article key={index}>
            <strong>{displayStatus(finding.status)}</strong><blockquote>{finding.quote || finding.claim?.quote}</blockquote>
            {finding.status === 'mismatch' && <p>Claimed: {JSON.stringify(finding.asserted_value)} · Calculated: {JSON.stringify(finding.calculated_value)}</p>}
            <p>{finding.reason || finding.evidence_path}</p>
          </article>)}
          <details><summary>Original answer</summary><pre>{detail.evidence_brief?.answer}</pre></details>
          <details><summary>Full audit and replay evidence</summary><pre>{JSON.stringify(detail, null, 2)}</pre></details>
        </>}
      </>}
    </div>}
  </section>;
}
