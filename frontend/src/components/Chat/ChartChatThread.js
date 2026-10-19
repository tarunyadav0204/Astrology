import React, { useEffect, useRef, useState } from 'react';
import { useCredits } from '../../context/CreditContext';
import { buildQueryContext } from '../../utils/queryContext';
import { chartTaraRequest } from '../../utils/chartTaraConversation';
import { askOverConversation, takeConversationStream, closeConversationSession } from '../../utils/instantConversation';
import MessageBubble from './MessageBubble';
import './ChatPage.css';

const wsUrl = path => `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api${path}`;
const detail = data => typeof data?.detail === 'string' ? data.detail : data?.detail?.message || data?.error_message || data?.error || 'Could not complete this question. Please retry.';

export default function ChartChatThread({ birthData, chartType, onLogin, onFocus, draftRequest }) {
    const { chartChatCost = 2, credits, fetchBalance } = useCredits();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [busy, setBusy] = useState(false);
    const [activity, setActivity] = useState('');
    const [activityRows, setActivityRows] = useState([]);
    const [error, setError] = useState('');
    const session = useRef(null);
    const pending = useRef(null);
    const lock = useRef(false);
    const alive = useRef(true);
    const socket = useRef(null);
    const timer = useRef(null);
    const list = useRef(null);
    const inputRef = useRef(null);
    useEffect(() => { if (draftRequest?.text) setInput(draftRequest.text); }, [draftRequest]);
    const stick = useRef(true);
    useEffect(() => {
        if (!inputRef.current) return;
        inputRef.current.style.height = 'auto';
        inputRef.current.style.height = `${Math.max(46, Math.min(130, inputRef.current.scrollHeight))}px`;
    }, [input]);
    const stop = () => {
        clearTimeout(timer.current);
        const previous = socket.current;
        socket.current = null;
        previous?.close();
    };
    useEffect(() => {
        alive.current = true;
        return () => { alive.current = false; stop(); closeConversationSession(session.current); };
    }, []);
    useEffect(() => { if (stick.current) list.current?.scrollTo?.({ top: list.current.scrollHeight }); }, [messages, activity, error]);
    const api = async (path, token, body) => {
        const response = await fetch(`/api${path}`, { method: body ? 'POST' : 'GET', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}) });
        const data = await response.json();
        if (!response.ok) throw new Error(detail(data));
        return data;
    };
    const update = (id, content, extra = {}) => setMessages(previous => previous.map(message => (message.clientId === id || message.messageId === id) ? { ...message, ...(content != null ? { content } : {}), ...extra } : message));
    const applyActivity = rows => {
        const visible = (Array.isArray(rows) ? rows : []).filter(row => row?.detail || row?.text || row?.title);
        if (visible.length) {
            setActivityRows(visible.slice(-3));
            setActivity('');
        }
    };
    const observe = (mid, answerId, token) => {
        const current = () => alive.current && pending.current?.messageId === mid;
        let partial = pending.current?.partialContent || '';
        const receiveText = (text, replace = false) => {
            if (!current() || typeof text !== 'string' || !text) return;
            // A slower status request must not roll back a newer socket chunk.
            if (!replace && partial.startsWith(text) && text.length < partial.length) return;
            partial = text;
            pending.current.partialContent = text;
            update(answerId, text, { instantStreaming: true });
        };
        const finish = data => {
            if (!current()) return;
            stop();
            update(answerId, data.content || data.response || partial, { instantStreaming: false, isTyping: false, isProcessing: false, terms: data.terms || [], glossary: data.glossary || {} });
            pending.current = null; setBusy(false); setActivity(''); fetchBalance();
        };
        const poll = async () => {
            if (!current()) return;
            try {
                const data = await api(`/chat-v2/status/${mid}`, token);
                if (!current()) return;
                if (data.status === 'completed') { finish(data); return; }
                if (['failed', 'error'].includes(data.status)) throw new Error(detail(data));
                if (data.partial_content) receiveText(data.partial_content);
                applyActivity(data.engagement_updates);
                timer.current = setTimeout(poll, 1500);
            } catch (err) {
                if (!current()) return;
                if (socket.current) { timer.current = setTimeout(poll, 3000); return; }
                stop(); setBusy(false); setError(err.message);
            }
        };
        let stream;
        try { stream = takeConversationStream(mid) || new WebSocket(`${wsUrl(`/chat-v2/stream/${mid}`)}?token=${encodeURIComponent(token)}`); }
        catch (_) { poll(); return; }
        socket.current = stream;
        const recover = () => { if (socket.current === stream) { stop(); poll(); } };
        stream.onmessage = event => {
            if (!current()) return;
            let data;
            try { data = JSON.parse(event.data); } catch (_) { return; }
            if (data.type === 'content_delta') receiveText(typeof data.content === 'string' ? data.content : (data.replace ? data.delta : partial + (data.delta || '')), Boolean(data.replace));
            if (data.type === 'progress') applyActivity(data.engagement_updates);
            if (data.type === 'completed') finish(data.payload || {});
            if (data.type === 'error') recover();
        };
        stream.onclose = recover; stream.onerror = recover;
        // Recover missed progress even while a socket still appears connected.
        timer.current = setTimeout(poll, 1500);
    };
    const send = async event => {
        event?.preventDefault();
        if (lock.current || busy || (!input.trim() && !pending.current)) return;
        const token = localStorage.getItem('token');
        if (!token) { onLogin?.(); return; }
        lock.current = true; setBusy(true); setError(''); setActivityRows([]); setActivity('Reading your question…');
        try {
            const birthId = birthData?.chart_id ?? birthData?.birth_chart_id ?? birthData?.id ?? null;
            if (!session.current) {
                const result = await api('/chat-v2/session', token, { birth_chart_id: birthId, query_context: buildQueryContext() });
                if (!alive.current) return;
                session.current = result.session_id;
            }
            if (!pending.current) {
                const id = `chart-${Date.now()}-${Math.random().toString(36).slice(2)}`;
                pending.current = { id, question: input.trim(), chartType, answerId: `${id}-answer` };
                setMessages(previous => [...previous, { messageId: id, role: 'user', content: input.trim(), timestamp: new Date().toISOString() }, { clientId: `${id}-answer`, messageId: `${id}-answer`, role: 'assistant', content: '', chatTier: 'instant', timestamp: new Date().toISOString() }]);
                setInput(''); stick.current = true;
            }
            const turn = pending.current;
            if (turn.messageId) { observe(turn.messageId, turn.answerId, token); return; }
            const body = chartTaraRequest({ sessionId: session.current, pending: turn, birthData, queryContext: buildQueryContext(), language: document.documentElement.lang || navigator.language || 'english' });
            const response = await askOverConversation(wsUrl('/chat-v2/conversation'), token, body, () => fetch('/api/chat-v2/ask', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }));
            const data = await response.json();
            if (!alive.current) return;
            if (!response.ok) throw new Error(detail(data));
            if (!data.message_id) throw new Error('The question could not be queued. Please retry.');
            turn.messageId = data.message_id;
            update(turn.answerId, null, { messageId: data.message_id });
            observe(data.message_id, turn.answerId, token);
        } catch (err) { if (alive.current) { setBusy(false); setActivity(''); setError(err.message); } }
        finally { lock.current = false; }
    };
    return <div className="chart-chat-thread">
        <div className="chart-chat-thread__messages chat-page" ref={list} onScroll={event => { const el = event.currentTarget; stick.current = el.scrollHeight - el.clientHeight - el.scrollTop < 80; }}>
            {!messages.length && <p className="chart-chat-thread__welcome">Ask about this chart. Drag this sheet down whenever you want to inspect the chart.</p>}
            {messages.map(message => message.content ? message.instantStreaming
                ? <div key={message.messageId} className="chart-chat-thread__stream" aria-label="Tara is typing"><div>{message.content}</div><span className="chart-chat-thread__cursor" aria-hidden="true">▍</span></div>
                : <MessageBubble key={message.messageId} message={message} sessionId={session.current} forceInstantPresentation onFollowUpClick={setInput} /> : null)}
            {error && <div role="alert"><p>{error}</p>{pending.current && !busy && <button type="button" onClick={send}>Retry question</button>}</div>}
        </div>
        {busy && <div className="chart-chat-thread__activity" role="status" aria-live="polite">
            <span className="chart-chat-thread__spinner" aria-hidden="true" />
            <div><strong>Tara’s activity</strong>{activityRows.length
                ? <ul>{activityRows.map((row, index) => <li key={row.id || index}>{row.detail || row.text || row.title}</li>)}</ul>
                : <p>{activity || 'Preparing your answer…'}</p>}</div>
        </div>}
        <form className="chart-chat-thread__composer" onSubmit={send}>
            <small>{chartChatCost === 0 ? 'Free' : `${chartChatCost} credits / question`} · Answers saved to chat history</small>
            <div><textarea ref={inputRef} aria-label="Question for Tara" placeholder="Ask about this chart…" value={input} onChange={event => setInput(event.target.value)} onFocus={onFocus} rows={1} disabled={busy || !!pending.current} />
            <button aria-label="Send question" type="submit" disabled={busy || !input.trim() || !!pending.current || credits < chartChatCost}>↑</button></div>
            {credits < chartChatCost && <small>Insufficient credits. Add credits to ask a question.</small>}
        </form>
    </div>;
}
