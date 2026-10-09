import React, { useEffect, useRef, useState } from 'react';
import useConflictResolution from '../../hooks/useConflictResolution';
import './ConflictResolution.css';

const plain = text => String(text || '').replace(/<[^>]*>/g, '');
const BoldText = ({ text }) => <>{String(text || '').split(/(\*\*[^*]+\*\*)/g).map((part, index) => part.startsWith('**') ? <strong key={index}>{part.slice(2, -2)}</strong> : part)}</>;

export default function ConflictResolution({ messages = [], onResolved, language = 'english' }) {
  const flow = useConflictResolution({ apiBase: '/api', getToken: () => localStorage.getItem('token') });
  const [selected, setSelected] = useState([]), [concern, setConcern] = useState(''), [reply, setReply] = useState('');
  const [history, setHistory] = useState(false), [query, setQuery] = useState(''), [page, setPage] = useState(1), [answers, setAnswers] = useState([]), [hasMore, setHasMore] = useState(false), [loading, setLoading] = useState(false), [searchError, setSearchError] = useState(''), [recent, setRecent] = useState([]), [expanded, setExpanded] = useState({});
  useEffect(() => { let active = true; flow.request('/recent').then(data => { if (active) setRecent(data.comparisons); }).catch(() => {}); return () => { active = false; }; }, [flow.request]);
  useEffect(() => {
    if (!history) return undefined;
    let active = true; setLoading(true); setSearchError('');
    const timer = setTimeout(() => { flow.request(`/answers?q=${encodeURIComponent(query)}&page=${page}`).then(data => { if (active) { setAnswers(data.answers); setHasMore(data.has_more); } }).catch(err => { if (active) setSearchError(err.message); }).finally(() => { if (active) setLoading(false); }); }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [history, query, page, flow.request]);
  const current = messages.filter(m => (m.role || m.sender) === 'assistant' && (m.messageId || m.message_id) && m.content && !m.isProcessing && !m.isTyping && !m.instantStreaming && (!m.status || m.status === 'completed') && (!m.message_type || m.message_type === 'answer')).map(m => { const index = messages.indexOf(m); return { answer_id: Number(m.messageId || m.message_id), answer: plain(m.content), question: plain([...messages.slice(0, index)].reverse().find(q => (q.role || q.sender) === 'user')?.content), answered_at: m.timestamp }; });
  const filteredCurrent = current.filter(source => !query.trim() || `${source.question} ${source.answer}`.toLowerCase().includes(query.trim().toLowerCase()));
  const visibleAnswers = history ? answers : filteredCurrent.slice((page - 1) * 30, page * 30);
  const more = history ? hasMore : page * 30 < filteredCurrent.length;
  const toggle = source => setSelected(previous => previous.some(s => s.answer_id === source.answer_id) ? previous.filter(s => s.answer_id !== source.answer_id) : previous.length < 2 ? [...previous, source] : previous);
  const reset = () => { flow.reset(); setSelected([]); setConcern(''); setReply(''); };
  const notified = useRef(null);
  useEffect(() => {
    if (flow.state?.phase === 'completed' && notified.current !== flow.state.id) {
      notified.current = flow.state.id;
      onResolved?.(flow.state);
    }
  }, [flow.state, onResolved]);
  const result = flow.state?.resolution;
  return <div className="conflict-resolution">
    {!flow.state && <>
      <p>Select exactly two answers. You can compare different chat modes or conversations.</p>
      <div className="conflict-actions"><button aria-pressed={!history} onClick={() => { setHistory(false); setPage(1); }}>This conversation</button><button aria-pressed={history} onClick={() => { setHistory(true); setPage(1); }}>All conversations</button></div>
      {<input aria-label="Search past answers" placeholder="Search questions or answers across conversations" value={query} onChange={e => { setQuery(e.target.value); setPage(1); }} />}
      {selected.length > 0 && <div className="conflict-selected">{selected.map((source, index) => <div key={source.answer_id}>Answer {index + 1}: {source.question || 'Selected answer'} <button onClick={() => toggle(source)} aria-label={`Remove answer ${index + 1}`}>✕</button></div>)}</div>}
      {loading && <p role="status">Loading answers…</p>}{searchError && <p role="alert">{searchError}</p>}
      <div className="conflict-answer-list">{visibleAnswers.map(source => <section key={source.answer_id}><label><input type="checkbox" checked={selected.some(s => s.answer_id === source.answer_id)} disabled={flow.busy || (!selected.some(s => s.answer_id === source.answer_id) && selected.length === 2)} onChange={() => toggle(source)} /><strong>{source.question || 'Answer'}</strong></label>
        {source.answered_at && <small>{new Date(source.answered_at).toLocaleString()}</small>}<p>{plain(source.answer).slice(0, 220)}</p>
        <button onClick={async () => { if (expanded[source.answer_id]) { setExpanded(prev => ({ ...prev, [source.answer_id]: null })); return; } try { const data = await flow.request(`/answers/${source.answer_id}`); setExpanded(prev => ({ ...prev, [source.answer_id]: data.answer })); } catch (err) { setSearchError(err.message); } }}> {expanded[source.answer_id] ? 'Hide answer' : 'Read answer'}</button>
        {expanded[source.answer_id] && <div className="conflict-source-text"><BoldText text={expanded[source.answer_id]} /></div>}
      </section>)}</div>
      {!loading && !visibleAnswers.length && <p>No answers found.</p>}
      {<div className="conflict-actions"><button disabled={page === 1 || loading} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page}</span><button disabled={!more || loading} onClick={() => setPage(page + 1)}>Next</button></div>}
      <label>What seems contradictory? <span>(optional)</span><textarea maxLength={2000} placeholder="For example: one answer recommends a field, while the other advises against it." value={concern} disabled={flow.busy} onChange={e => setConcern(e.target.value)} /></label>
      <button className="conflict-primary" disabled={selected.length !== 2 || flow.busy} onClick={() => flow.start(selected.map(s => s.answer_id), concern, language)}>Resolve selected answers ({selected.length}/2)</button>
      {recent.length > 0 && <details><summary>Recent comparisons</summary>{recent.map(run => <button className="conflict-recent" key={run.id} onClick={() => flow.resume(run.id)}>{run.sources.map(s => s.question || `#${s.answer_id}`).join(' / ')} · {run.phase === 'completed' ? 'Read resolution' : 'Resume'}</button>)}</details>}
    </>}
    {flow.state && <><p><strong>Comparing two answers</strong> · Information rounds {flow.state.rounds}/{flow.state.max_rounds || 8}</p><div className="conflict-selected">{flow.state.sources.map((source, index) => <div key={source.answer_id}><strong>Answer {index + 1}:</strong> {source.question}</div>)}</div>
      {flow.state.events.filter(e => e.kind === 'question' || e.kind === 'user_reply').map((event, index) => <p key={index}><strong>{event.kind === 'question' ? 'Clarification' : 'Your reply'}:</strong> {event.text}</p>)}
      {flow.state.phase === 'waiting' && <div className="conflict-clarification"><label>{flow.state.question}<textarea aria-label="Your clarification" placeholder="Provide the detail requested above" maxLength={3000} disabled={flow.busy} value={reply} onChange={e => setReply(e.target.value)} /></label><div className="conflict-actions"><button className="conflict-primary" disabled={!reply.trim() || flow.busy} onClick={() => { flow.send('reply', reply); setReply(''); }}>Send clarification</button><button disabled={flow.busy} onClick={() => flow.send('finish')}>Resolve with available information</button></div></div>}
    </>}
    {flow.busy && <p role="status">{flow.progress || 'Checking the comparison…'}</p>}
    {flow.error && <div role="alert"><p>{flow.error}</p>{flow.state && <button disabled={flow.busy} onClick={() => flow.resume(flow.state.id)}>Reconnect</button>}</div>}
    {result && <article><h3>Your answer</h3><div className="conflict-source-text"><BoldText text={result.corrected_answer} /></div><h3>Why the guidance differed</h3><p><BoldText text={result.explanation} /></p>{result.evidence.length > 0 && <><h3>Why this is most likely</h3>{result.evidence.map((evidence, index) => <p key={index}><BoldText text={evidence.finding} /></p>)}</>}{result.uncertainty.length > 0 && <><h3>Keep in mind</h3><p><BoldText text={result.uncertainty[0]} /></p></>}<p>Saved in your chat history.</p></article>}
    {flow.state && !flow.busy && <button onClick={reset}>Compare another pair</button>}
  </div>;
}
