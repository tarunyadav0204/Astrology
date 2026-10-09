import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import './ChatMemory.css';

const CATEGORIES = ['personal', 'family', 'career', 'health', 'education', 'finance', 'relationship', 'other'];

export default function ChatMemory({ chartId, name }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(null);
  const [more, setMore] = useState(false);
  const [searching, setSearching] = useState(false);
  const [open, setOpen] = useState(false);
  const [facts, setFacts] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(null);
  const [text, setText] = useState('');
  const [category, setCategory] = useState('personal');
  const [notice, setNotice] = useState('');
  const trigger = useRef(null);
  const dialog = useRef(null);
  const request = useCallback(async (path, method = 'GET', body) => {
    const response = await fetch(`/api/facts${path}`, {
      method,
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    if (!response.ok) throw new Error('Unable to update memory. Please try again.');
    return response.json();
  }, []);
  const load = useCallback(async () => {
    const data = await request(`/${chartId}?q=${encodeURIComponent(query)}&page=${page}`);
    setFacts(data.facts || []); setTotal(data.total ?? data.facts.length); setMore(Boolean(data.has_more));
  }, [chartId, request, query, page]);
  useEffect(() => { let active = true; request(`/${chartId}?limit=1`).then(data => { if (active) setTotal(data.total ?? data.facts.length); }).catch(() => {}); return () => { active = false; }; }, [chartId, request]);
  useEffect(() => { if (!open) return; let active = true; setSearching(true); const timer = setTimeout(() => { request(`/${chartId}?q=${encodeURIComponent(query)}&page=${page}`).then(data => { if (active) { setFacts(data.facts || []); setTotal(data.total ?? (data.facts || []).length); setMore(Boolean(data.has_more)); setError(''); } }).catch(err => { if (active) setError(err.message); }).finally(() => { if (active) setSearching(false); }); }, 250); return () => { active = false; clearTimeout(timer); }; }, [open, chartId, query, page, request]);
  useEffect(() => {
    if (!open) return;
    dialog.current?.focus();
    const keydown = event => {
      if (event.key === 'Escape' && !busy) setOpen(false);
      if (event.key === 'Tab') {
        const items = [...dialog.current.querySelectorAll('button:not(:disabled), input, textarea, select')];
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', keydown);
    return () => { document.removeEventListener('keydown', keydown); trigger.current?.focus(); };
  }, [open, busy]);
  const mutate = async (path, method, body) => {
    setBusy(true); setError(''); setNotice('');
    try { await request(path, method, body); await load(); setEditing(null); setNotice('Memory updated. Future answers can use your saved details.'); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const startEdit = fact => { setEditing(fact || { id: null }); setText(fact?.fact || ''); setCategory(fact?.category || 'personal'); setNotice(''); };
  return <>
    <button ref={trigger} type="button" className="chat-memory-trigger" title="Review remembered details" aria-label={`Memory for ${name || 'this person'}${total !== null ? `, ${total} saved details` : ''}`} aria-haspopup="dialog" onClick={() => { setOpen(true); setError(''); load().catch(() => setError('Unable to load memory. Please try again.')); }}>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M6 4h10v17l-5-3-5 3V4Z" /><path d="M10 1h10v17" /></svg>{facts !== null && <span aria-hidden="true">{facts.length}</span>}
    </button>
    {open && createPortal(<div className="chat-memory-overlay">
      <section ref={dialog} tabIndex={-1} className="chat-memory-panel" role="dialog" aria-modal="true" aria-labelledby="chat-memory-title">
        <header><h2 id="chat-memory-title">Remembered about {name || 'this person'}</h2><button type="button" disabled={busy} onClick={() => setOpen(false)} aria-label="Close memory">✕</button></header>
        <p>These details help personalize future answers. You can correct or remove them anytime.</p>
        <p className="chat-memory-help">Editing memory does not change your conversation history.</p>
        <label>Search memory<input type="search" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} placeholder="Search facts, e.g. career or studying abroad" /></label>
        {searching && <p role="status">Searching…</p>}
        {error && <p role="alert">{error} <button type="button" onClick={() => load().then(() => setError('')).catch(() => {})}>Retry</button></p>}
        {notice && <p role="status">{notice}</p>}
        {facts === null && !error && <p role="status">Loading memory…</p>}
        {facts?.length === 0 && <p>{query ? 'No facts match your search.' : 'No remembered details yet. Add something you want this chat to know.'}</p>}
        {facts?.map(fact => <article key={fact.id} className="chat-memory-fact"><small>{fact.category.replace(/_/g, ' ')}</small><p>{fact.fact}</p><button type="button" disabled={busy} onClick={() => startEdit(fact)} aria-label={`Edit: ${fact.fact}`}>Edit</button><button type="button" disabled={busy} onClick={() => { if (window.confirm('Remove this detail from saved memory? Conversation history will remain.')) mutate(`/${fact.id}`, 'DELETE'); }} aria-label={`Remove: ${fact.fact}`}>Remove</button></article>)}
        <div>{page > 1 && <button disabled={searching} onClick={() => setPage(value => value - 1)}>Previous</button>}{more && <button disabled={searching} onClick={() => setPage(value => value + 1)}>Next</button>}</div>
        {editing ? <form onSubmit={event => { event.preventDefault(); if (text.trim()) mutate(editing.id ? `/${editing.id}` : '', editing.id ? 'PUT' : 'POST', { fact: text.trim(), category, ...(editing.id ? {} : { birth_chart_id: chartId }) }); }}>
          <label>Category<select value={category} onChange={event => setCategory(event.target.value)}>{[...new Set([...CATEGORIES, category])].map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}</select></label>
          <label>Remembered detail<textarea autoFocus value={text} onChange={event => setText(event.target.value)} placeholder="For example: Considering a master's abroad" required /></label>
          <button disabled={busy || !text.trim()} type="submit">{busy ? 'Saving…' : 'Save'}</button><button type="button" disabled={busy} onClick={() => setEditing(null)}>Cancel</button>
        </form> : <button type="button" disabled={busy || facts === null} onClick={() => startEdit(null)}>+ Add a fact</button>}
      </section>
    </div>, document.body)}
  </>;
}
