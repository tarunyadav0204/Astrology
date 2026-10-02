// Development-only real-provider QA. The companion server only uses a fictional chart.
import React, { useEffect, useRef, useState } from 'react';
import { CreditProvider } from '../context/CreditContext';
import MessageBubble from '../components/Chat/MessageBubble';
import { applyInstantProgress, buildImmediateChartPreview, mergeChartContext } from '../utils/instantProgress';
import '../components/Chat/ChatPage.css';

export default function InstantChatTimingProbe() {
    const [fixture, setFixture] = useState(null);
    const [question, setQuestion] = useState('How is my career looking over the next six months?');
    const [message, setMessage] = useState(null);
    const [measurements, setMeasurements] = useState([]);
    const surface = useRef(null);
    const started = useRef(0);
    const source = useRef(null);
    const observed = useRef(new Set());
    useEffect(() => {
        fetch('http://127.0.0.1:8767/fixture').then(r => r.json()).then(setFixture);
        return () => source.current?.close();
    }, []);
    useEffect(() => {
        if (!surface.current) return undefined;
        const readVisible = () => {
            if (!started.current) return;
            const nodes = surface.current.querySelectorAll('[data-context-row], [data-source="llm"] p');
            nodes.forEach(node => {
                const key = node.dataset.contextRow || 'first-llm-text';
                if (observed.current.has(key) || !node.textContent.trim()) return;
                observed.current.add(key);
                requestAnimationFrame(() => {
                    const measurement = { event: key, ms: Math.round(performance.now() - started.current), text: node.textContent };
                    console.info('[InstantTimingPaint]', JSON.stringify(measurement));
                    setMeasurements(prev => [...prev, measurement]);
                });
            });
        };
        const observer = new MutationObserver(readVisible);
        observer.observe(surface.current, { childList: true, subtree: true, characterData: true });
        return () => observer.disconnect();
    }, []);
    const run = () => {
        source.current?.close();
        observed.current.clear();
        setMeasurements([]);
        started.current = performance.now();
        const pending = { role:'assistant', chatTier:'instant', content:'', isTyping:true, timestamp:new Date().toISOString() };
        setMessage(applyInstantProgress(pending, { preview:buildImmediateChartPreview(fixture.chart) }));
        const eventSource = new EventSource(`http://127.0.0.1:8767/stream?question=${encodeURIComponent(question)}`);
        source.current = eventSource;
        eventSource.onmessage = event => {
            const payload = JSON.parse(event.data);
            if (payload.type === 'completed') {
                setMessage(previous => ({ ...previous, content:payload.content, instantPreview:mergeChartContext(previous.instantPreview,payload.preview), isTyping:false, instantStreaming:false }));
                setMeasurements(prev => [...prev, { event:'complete', ms:Math.round(performance.now()-started.current) }]);
                eventSource.close();
            } else if (payload.type === 'error') {
                setMeasurements(prev => [...prev, { event:'error', error:payload.error }]);
                eventSource.close();
            } else if (payload.type === 'content_delta' || payload.type === 'preview') {
                setMessage(previous => applyInstantProgress(previous, payload));
            }
        };
    };
    return <CreditProvider><main style={{ maxWidth:760, margin:'40px auto', padding:24, color:'#292329' }}>
        <h1>Instant Chat timing probe</h1>
        <p>Fictional profile · real calculations, intent router and LLM · actual chat bubble</p>
        <textarea aria-label="Test question" value={question} onChange={e=>setQuestion(e.target.value)} style={{ width:'100%', minHeight:75 }} />
        <button onClick={run} disabled={!fixture}>Send real question</button>
        <section ref={surface} style={{ marginTop:24 }}>{message ? <MessageBubble key={started.current} message={message} forceInstantPresentation /> : null}</section>
        <h2>Browser paint timings</h2>
        <pre aria-label="Timing results" style={{ whiteSpace:'pre-wrap',fontSize:12 }}>{JSON.stringify(measurements,null,2)}</pre>
    </main></CreditProvider>;
}
