import React, { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useCredits } from '../../context/CreditContext';
import './ChartTaraPanel.css';
const ChartChatThread = lazy(() => import('./ChartChatThread'));
export const sheetSnapHeight = (height, viewportHeight) => {
  const points = [72, viewportHeight * 0.52, viewportHeight - 90];
  return points.reduce((best, next) => Math.abs(next - height) < Math.abs(best - height) ? next : best);
};

export default function ChartTaraPanel({ birthData, chartType = 'lagna', onLogin, draftRequest }) {
  const { chartChatCost = 2, features, fetchCosts } = useCredits();
  const [mounted, setMounted] = useState(false);
  const [visible, setVisible] = useState(false);
  const launcher = useRef(null);
  const [collapsed, setCollapsed] = useState(false);
  const [height, setHeight] = useState(() => window.innerHeight * 0.52);
  const panel = useRef(null);
  const drag = useRef(null);
  const enabled = features?.instant_chat_enabled === true;
  useEffect(() => {
    const resize = () => setHeight(previous => Math.min(previous, window.innerHeight - 90));
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);
  useEffect(() => {
    if (!visible) return undefined;
    const escape = event => { if (event.key === 'Escape') {
      if (collapsed) { setVisible(false); launcher.current?.focus(); }
      else setCollapsed(true);
    } };
    window.addEventListener('keydown', escape);
    return () => window.removeEventListener('keydown', escape);
  }, [visible, collapsed]);
  const launch = () => { setMounted(true); setVisible(true); setCollapsed(false); setHeight(window.innerHeight * 0.52); fetchCosts?.(); };
  useEffect(() => { if (draftRequest?.text) launch(); }, [draftRequest]);
  const beginDrag = event => {
    if (event.button !== 0) return;
    drag.current = { pointer: event.pointerId, y: event.clientY, height: panel.current.getBoundingClientRect().height };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const move = event => {
    if (!drag.current || drag.current.pointer !== event.pointerId) return;
    setCollapsed(false);
    setHeight(Math.max(72, Math.min(window.innerHeight - 90, drag.current.height + drag.current.y - event.clientY)));
  };
  const finish = event => {
    if (!drag.current || drag.current.pointer !== event.pointerId) return;
    const next = sheetSnapHeight(drag.current.height + drag.current.y - event.clientY, window.innerHeight);
    setHeight(next); setCollapsed(next === 72); drag.current = null;
  };
  const chartKey = JSON.stringify([birthData?.chart_id ?? birthData?.birth_chart_id ?? birthData?.id, birthData?.name, birthData?.date, birthData?.time, birthData?.latitude, birthData?.longitude, birthData?.calculation_profile]);
  return <>
    <button ref={launcher} type="button" className="chart-tara-launcher" onClick={launch} disabled={!enabled} aria-expanded={visible && !collapsed} title={enabled ? 'Ask about the selected chart' : 'Chart Chat is currently unavailable'}>✦ Ask Tara</button>
    {mounted && createPortal(<section ref={panel} className={`chart-tara-panel${collapsed ? ' chart-tara-panel--collapsed' : ''}`} role="region" aria-label="Ask Tara about this chart" hidden={!visible} style={{ height: collapsed ? 72 : height }}>
      <header className="chart-tara-panel__header">
        <div className="chart-tara-panel__drag" role="button" tabIndex={0} aria-label="Resize Chart Chat. Drag or use arrow keys."
          onPointerDown={beginDrag} onPointerMove={move} onPointerUp={finish} onPointerCancel={() => { drag.current = null; }} onLostPointerCapture={() => { drag.current = null; }}
          onKeyDown={event => {
            if (!['ArrowUp', 'ArrowDown', 'Enter', ' '].includes(event.key)) return;
            event.preventDefault();
            if (event.key === 'ArrowUp') { setCollapsed(false); setHeight(window.innerHeight - 90); }
            else if (event.key === 'ArrowDown') setCollapsed(true);
            else setCollapsed(previous => !previous);
          }}>
          <i aria-hidden="true" />
          <strong>✦ Ask Tara <span>Chart Chat</span></strong>
          <small>{birthData?.name || 'Selected chart'} · {chartType} · {chartChatCost === 0 ? 'Free' : `${chartChatCost} credits/question`}</small>
        </div>
        <button type="button" className="chart-tara-panel__close" aria-label={collapsed ? 'Expand chat' : 'Minimize chat'} onClick={() => setCollapsed(previous => !previous)}><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={collapsed ? 'M6 15l6-6 6 6' : 'M6 9l6 6 6-6'} /></svg></button>
        <button type="button" className="chart-tara-panel__close" aria-label="Close Chart Chat" title="Close chat — your conversation is kept" onClick={() => { setVisible(false); launcher.current?.focus(); }}><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg></button>
      </header>
      <div className="chart-tara-panel__body" hidden={collapsed}>
        <Suspense fallback={<p role="status">Opening Tara…</p>}>
          <ChartChatThread key={chartKey} birthData={birthData} chartType={chartType} onLogin={onLogin} draftRequest={draftRequest} onFocus={() => { setCollapsed(false); setHeight(window.innerHeight - 90); }} />
        </Suspense>
      </div>
    </section>, document.body)}
  </>;
}
