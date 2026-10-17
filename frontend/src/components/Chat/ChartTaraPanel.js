import React, { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useCredits } from '../../context/CreditContext';
import './ChartTaraPanel.css';

const ChatPage = lazy(() => import('./ChatPage'));

export const clampPanelPosition = (position, viewport, size) => ({
  x: Math.max(8, Math.min(position.x, Math.max(8, viewport.width - size.width - 8))),
  y: Math.max(8, Math.min(position.y, Math.max(8, viewport.height - size.height - 8))),
});

export default function ChartTaraPanel({ birthData, onLogin }) {
  const { verifiedChatCost, features } = useCredits();
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState(null);
  const panel = useRef(null);
  const drag = useRef(null);
  const enabled = features?.verified_chat_enabled === true;

  const constrain = (next) => {
    const bounds = panel.current?.getBoundingClientRect();
    return clampPanelPosition(next, { width: window.innerWidth, height: window.innerHeight },
      { width: bounds?.width || Math.min(440, window.innerWidth - 16), height: bounds?.height || Math.min(740, window.innerHeight - 24) });
  };
  useEffect(() => {
    const resize = () => setPosition(previous => previous ? constrain(previous) : previous);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);
  useEffect(() => {
    if (!open) return undefined;
    panel.current?.querySelector('.chart-tara-panel__drag')?.focus({ preventScroll: true });
    const escape = event => { if (event.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', escape);
    return () => window.removeEventListener('keydown', escape);
  }, [open]);
  const beginDrag = event => {
    if (event.button !== 0) return;
    const bounds = panel.current.getBoundingClientRect();
    drag.current = { pointer: event.pointerId, x: event.clientX, y: event.clientY, left: bounds.left, top: bounds.top };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const move = event => {
    if (!drag.current || drag.current.pointer !== event.pointerId) return;
    setPosition(constrain({ x: drag.current.left + event.clientX - drag.current.x, y: drag.current.top + event.clientY - drag.current.y }));
  };
  const finishDrag = () => { drag.current = null; };
  const launch = () => { setMounted(true); setOpen(true); };
  const chartKey = [birthData?.id, birthData?.name, birthData?.date, birthData?.time, birthData?.latitude, birthData?.longitude, birthData?.timezone].join('|');

  return <>
    <button type="button" className="chart-tara-launcher" onClick={launch} disabled={!enabled} aria-expanded={open} title={!enabled ? 'Verified chat is currently unavailable' : 'Ask about the selected chart'}>✦ Ask Tara</button>
    {mounted && createPortal(<section ref={panel} className="chart-tara-panel" role="region" aria-label="Ask Tara about this chart" hidden={!open}
      style={position ? { left: position.x, top: position.y, right: 'auto', bottom: 'auto' } : undefined}>
      <header className="chart-tara-panel__header">
        <div className="chart-tara-panel__drag" role="button" tabIndex={0} aria-label="Move chat panel. Drag or use arrow keys."
          onPointerDown={beginDrag} onPointerMove={move} onPointerUp={finishDrag} onPointerCancel={finishDrag} onLostPointerCapture={finishDrag}
          onKeyDown={event => {
            const delta = { ArrowLeft: [-24, 0], ArrowRight: [24, 0], ArrowUp: [0, -24], ArrowDown: [0, 24] }[event.key];
            if (!delta) return;
            event.preventDefault();
            const bounds = panel.current.getBoundingClientRect();
            setPosition(constrain({ x: bounds.left + delta[0], y: bounds.top + delta[1] }));
          }}>
          <strong>✦ Ask Tara <span>Verified</span></strong>
          <small>{birthData?.name || 'Selected chart'} · {verifiedChatCost} credits/question</small>
        </div>
        <button type="button" className="chart-tara-panel__close" aria-label="Minimize chat" onClick={() => setOpen(false)}>−</button>
      </header>
      <div className="chart-tara-panel__body">
        <Suspense fallback={<p role="status">Opening Tara…</p>}>
          <ChatPage key={chartKey} embeddedVerified onLogin={onLogin} />
        </Suspense>
      </div>
    </section>, document.body)}
  </>;
}
