import { useCallback, useEffect, useRef, useState } from 'react';

const requestId = () => typeof globalThis.crypto?.randomUUID === 'function' ? globalThis.crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.floor(Math.random() * 16); return (c === 'x' ? r : ((r & 3) | 8)).toString(16); });

export default function useConflictResolution({ apiBase, getToken }) {
  const [state, setState] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [progress, setProgress] = useState('');
  const socket = useRef(null), stateRef = useRef(null), timeout = useRef(null), creationId = useRef(null), mounted = useRef(true), tokenRef = useRef(getToken);
  tokenRef.current = getToken;
  const clearTimer = () => { clearTimeout(timeout.current); timeout.current = null; };
  const request = useCallback(async (path, options = {}) => {
    try {
    const token = await tokenRef.current();
    const response = await fetch(`${apiBase}/chat/conflicts${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...(options.headers || {}) } });
    const data = await response.json();
    if (!response.ok) throw new Error(response.status === 401 ? 'Please sign in again to continue.' : 'Unable to load this comparison. Please try again.');
    return data;
    } catch (_) { throw new Error('Unable to load this comparison. Please try again.'); }
  }, [apiBase]);
  const connect = async run => {
    socket.current?.close(); clearTimer();
    const token = await tokenRef.current();
    if (!mounted.current) return;
    const origin = /^https?:/.test(apiBase) ? apiBase : `${window.location.origin}${apiBase}`;
    const ws = new WebSocket(`${origin.replace(/^http/, 'ws')}/chat/conflicts/ws/${run.id}?token=${encodeURIComponent(token)}`);
    socket.current = ws;
    timeout.current = setTimeout(() => { if (socket.current === ws) { setError('Connection timed out. Reconnect to continue.'); setBusy(false); ws.close(); } }, 20000);
    ws.onmessage = event => {
      if (!mounted.current || socket.current !== ws) return;
      try {
        const data = JSON.parse(event.data);
        clearTimer();
        if (data.type === 'error') { setError('We couldn’t complete this comparison. Please reconnect to try again.'); setBusy(false); return; }
        if (data.type === 'progress') { setProgress(data.text); setBusy(true); }
        if (data.type === 'state') {
          stateRef.current = data; setState(data);
          setBusy(data.phase === 'running');
          if (data.phase === 'ready' || data.phase === 'running') {
            setBusy(true); ws.send(JSON.stringify({ type: 'start', revision: data.revision }));
          }
          if (data.phase === 'completed' || data.phase === 'waiting') setProgress('');
        }
        if (data.type === 'progress') timeout.current = setTimeout(() => { setError('The comparison is taking longer than expected. Reconnect to check its status.'); setBusy(false); ws.close(); }, 240000);
      } catch (_) { setError('Unable to read the comparison response.'); setBusy(false); }
    };
    ws.onerror = () => { if (mounted.current && socket.current === ws) { clearTimer(); setError('Connection failed. Reconnect to continue.'); setBusy(false); } };
    ws.onclose = () => { if (mounted.current && socket.current === ws) { clearTimer(); if (stateRef.current?.phase !== 'completed') { setError(previous => previous || 'Connection closed. Reconnect to continue.'); setBusy(false); } } };
  };
  const start = async (ids, concern, language) => {
    setError(''); setBusy(true);
    const signature = JSON.stringify([ids, concern, language]);
    if (creationId.current?.signature !== signature) creationId.current = { signature, id: requestId() };
    try {
      const data = await request('', { method: 'POST', body: JSON.stringify({ message_ids: ids, concern, language, request_id: creationId.current.id }) });
      if (!mounted.current) return;
      stateRef.current = data; setState(data);
      if (data.phase === 'completed') { setBusy(false); return; }
      await connect(data);
    } catch (err) { if (mounted.current) { setError('Unable to continue this comparison. Please try again.'); setBusy(false); } }
  };
  const resume = async id => {
    setError(''); setBusy(true);
    try { const data = await request(`/${id}`); if (!mounted.current) return; stateRef.current = data; setState(data); if (data.phase === 'completed') setBusy(false); else await connect(data); }
    catch (err) { setError('Unable to continue this comparison. Please try again.'); setBusy(false); }
  };
  const send = (type, text = '') => {
    if (socket.current?.readyState !== WebSocket.OPEN) { setError('Reconnect before continuing.'); return; }
    setError(''); setBusy(true);
    socket.current.send(JSON.stringify({ type, text, revision: stateRef.current.revision }));
    clearTimer(); timeout.current = setTimeout(() => { setError('Reconnect to check the comparison status.'); setBusy(false); socket.current?.close(); }, 240000);
  };
  const reset = () => { socket.current?.close(); socket.current = null; clearTimer(); creationId.current = null; stateRef.current = null; setState(null); setError(''); setProgress(''); setBusy(false); };
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; socket.current?.close(); socket.current = null; clearTimer(); }; }, []);
  return { state, busy, error, progress, request, start, resume, send, reset };
}

export function appendConflictResolution(messages, result) {
  if (!result.message_id || messages.some(message => Number(message.messageId || message.message_id) === result.message_id)) return messages;
  const timestamp = result.completed_at || new Date().toISOString();
  const common = { status: 'completed', message_type: 'answer', timestamp, responseStyle: 'simple', response_style: 'simple', chatTier: 'verified', chat_tier: 'verified' };
  const additions = [];
  if (result.question_message_id) additions.push({ ...common, id: `${result.question_message_id}_${timestamp}`, messageId: result.question_message_id, message_id: result.question_message_id, role: 'user', sender: 'user', content: result.question_text });
  additions.push({ ...common, id: `${result.message_id}_${timestamp}`, messageId: result.message_id, message_id: result.message_id, role: 'assistant', sender: 'assistant', content: result.content });
  return [...messages, ...additions];
}
