import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import './ChatMemory.css';
import ConflictResolution from './ConflictResolution';
import PrashnaSetup from './PrashnaSetup';

export default function ChatSummary({ messages = [], onResolved, language = 'english', onPrashna }) {
  const [tool, setTool] = useState('summary');
  const [open, setOpen] = useState(false), [ids, setIds] = useState([]), [summary, setSummary] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const answers = messages.filter(message => (message.role || message.sender) === 'assistant' && (message.messageId || message.message_id) && message.content && !message.isProcessing && !message.isTyping && !message.instantStreaming && (!message.status || message.status === 'completed') && (!message.message_type || message.message_type === 'answer'));
  const toggle = id => { setSummary(''); setError(''); setIds(previous => previous.includes(id) ? previous.filter(value => value !== id) : previous.length < 3 ? [...previous, id] : previous); };
  const generate = async () => {
    setBusy(true); setError('');
    try {
      const response = await fetch('/api/chat/summaries', { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ message_ids: ids, language }) });
      const data = await response.json();
      if (!response.ok) throw new Error('Unable to summarize these answers.');
      setSummary(data.summary);
    } catch (err) { setError('Unable to summarize these answers. Please try again.'); }
    finally { setBusy(false); }
  };
  return <><button type="button" className="chat-memory-trigger chat-tools-trigger" title="Chat tools" aria-label="Chat tools" onClick={() => setOpen(true)}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M14.7 6.3a5 5 0 0 0-6.4 6.4l-5.6 5.6a2.1 2.1 0 0 0 3 3l5.6-5.6a5 5 0 0 0 6.4-6.4l-3 3-3-3 3-3Z" /></svg></button>
    {open && createPortal(<div className="chat-memory-overlay"><section className="chat-memory-panel" role="dialog" aria-modal="true" aria-label="Chat tools"><header><h2>{tool === 'prashna' ? 'Ask with Prashna' : tool === 'summary' ? 'Summarize chat' : 'Resolve conflicting answers'}</h2><button disabled={busy} onClick={() => setOpen(false)} aria-label="Close summary">✕</button></header>
      <div className="conflict-actions"><button aria-pressed={tool === 'summary'} disabled={busy} onClick={() => setTool('summary')}>Summarize</button><button aria-pressed={tool === 'conflict'} disabled={busy} onClick={() => setTool('conflict')}>Resolve conflicts</button>{onPrashna && <button disabled={busy} onClick={() => setTool('prashna')}>Ask with Prashna</button>}</div>
      {tool === 'prashna' ? <PrashnaSetup onSelect={place => { onPrashna(place); setOpen(false); }} /> : tool === 'conflict' ? <ConflictResolution onResolved={onResolved} messages={messages} language={language} /> : <>
      <p>Select 1–3 answers. Their original questions will be included.</p>
      <div style={{ maxHeight: '40vh', overflow: 'auto' }}>{answers.map(answer => { const id = Number(answer.messageId || answer.message_id); const index = messages.indexOf(answer); const question = [...messages.slice(0, index)].reverse().find(message => (message.role || message.sender) === 'user'); return <label className="chat-memory-fact" key={id}><input type="checkbox" style={{ width: 'auto', display: 'inline' }} checked={ids.includes(id)} disabled={busy || (!ids.includes(id) && ids.length >= 3)} onChange={() => toggle(id)} /> {question?.content || String(answer.content).replace(/<[^>]*>/g, '').slice(0, 150)}</label>; })}</div>
      <button disabled={!ids.length || busy} onClick={generate}>{busy ? 'Summarizing…' : `Summarize selected (${ids.length})`}</button>
      {error && <p role="alert">{error}</p>}
      {summary && <><h3>Summary of {ids.length} selected {ids.length === 1 ? 'answer' : 'answers'}</h3><div>{summary.split('\n').map((line, index) => <p key={index} style={{ margin: '8px 0', fontWeight: /^#{1,6} /.test(line) ? 600 : 400 }}>{line.replace(/^#{1,6} /, '').split(/(\*\*[^*]+\*\*)/g).map((part, i) => part.startsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part)}</p>)}</div><button onClick={async () => { try { await navigator.clipboard.writeText(summary); } catch (_) { setError('Could not copy the summary.'); } }}>Copy summary</button></>}
      </>}
    </section></div>, document.body)}
  </>;
}
