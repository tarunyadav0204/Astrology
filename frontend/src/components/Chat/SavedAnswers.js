import React, { useEffect, useState } from 'react';
import './SavedAnswers.css';
import { showToast } from '../../utils/toast';

const request = async (path = '', method = 'GET', signal) => {
  const res = await fetch(`/api/chat/bookmarks${path}`, { method, signal, headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
  if (!res.ok) throw new Error('Unable to access saved answers. Please try again.');
  return res.json();
};
const icon = <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M6 3h12v18l-6-4-6 4V3Z" /></svg>;
const plain = value => String(value || '').replace(/<[^>]*>/g, '').replace(/(?:【|\[)(?:POS|NEG)_(?:START|END)(?:】|\])/gi, '').replace(/\*\*/g, '').replace(/^#{1,6}\s*/gm, '');

export function SaveAnswerButton({ message }) {
  const id = Number(message.messageId || message.message_id);
  const eligible = Number.isInteger(id) && id > 0 && message.role === 'assistant' && !message.isTyping && !message.isProcessing && !message.instantStreaming && !message.isWelcome && (!message.message_type || message.message_type === 'answer') && Boolean(message.content);
  const [saved, setSaved] = useState(false), [busy, setBusy] = useState(false);
  useEffect(() => { if (!eligible) return; const controller = new AbortController(); request(`/${id}`, 'GET', controller.signal).then(data => setSaved(data.saved)).catch(() => {}); return () => controller.abort(); }, [id, eligible]);
  if (!eligible) return null;
  return <><button type="button" className="action-btn save-answer-button" disabled={busy} aria-pressed={saved} aria-label={saved ? 'Remove saved answer' : 'Save answer'} title={saved ? 'Remove saved answer' : 'Save answer'} onClick={async () => { setBusy(true); try { const data = await request(`/${id}`, saved ? 'DELETE' : 'PUT'); setSaved(data.saved); } catch (err) { showToast(err.message, 'error', 4000); } finally { setBusy(false); } }}>{icon}</button></>;
}

export default function SavedAnswers({ onOpenConversation }) {
  const open = true;
  const [query, setQuery] = useState(''), [answers, setAnswers] = useState([]), [page, setPage] = useState(1), [more, setMore] = useState(false), [loading, setLoading] = useState(false), [error, setError] = useState(''), [revision, setRevision] = useState(0);
  useEffect(() => { if (!open) return; const controller = new AbortController(); setLoading(true); setError(''); const timer = setTimeout(() => { request(`?q=${encodeURIComponent(query)}&page=${page}`, 'GET', controller.signal).then(data => { setAnswers(prev => page === 1 ? data.answers : [...prev, ...data.answers]); setMore(data.has_more); }).catch(err => { if (err.name !== 'AbortError') setError(err.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); }); }, 200); return () => { clearTimeout(timer); controller.abort(); }; }, [open, query, page, revision]);
  return <section className="saved-answers" aria-label="Saved answers">
      <label>Search saved answers<input autoFocus type="search" value={query} placeholder="Search a question, answer or person" onChange={event => { setQuery(event.target.value); setPage(1); }} style={{ width: '100%', padding: 10, boxSizing: 'border-box', marginTop: 8 }} /></label>
      {error && <p role="alert">{error} <button onClick={() => setRevision(value => value + 1)}>Retry</button></p>}
      {loading && <p role="status">Loading…</p>}
      {!loading && !error && !answers.length && <p>{query ? 'No saved answers match your search.' : 'Save an answer using the bookmark icon beneath it. Your saved answers will appear here.'}</p>}
      {answers.map(answer => <article className="saved-answer-card" key={answer.message_id}><small>{answer.name} · {new Date(answer.saved_at).toLocaleDateString()}</small><h3>{plain(answer.question) || 'Saved answer'}</h3><details><summary>Read answer</summary><p style={{ whiteSpace: 'pre-wrap' }}>{plain(answer.content)}</p></details><button type="button" onClick={() => onOpenConversation(answer.session_id)}>Open conversation</button><button type="button" onClick={async () => { try { await request(`/${answer.message_id}`, 'DELETE'); setPage(1); setRevision(value => value + 1); } catch (err) { setError(err.message); } }}>Remove bookmark</button></article>)}
      {more && <button disabled={loading} onClick={() => setPage(value => value + 1)}>Load more</button>}
    </section>;
}
