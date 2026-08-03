import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

const MIN_SCALE = 1;
const MAX_SCALE = 6;

/**
 * Fullscreen image viewer with wheel / pinch zoom and drag pan.
 */
export default function ZoomableImageLightbox({ src, alt = 'Map', onClose }) {
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragRef = useRef(null);
  const pinchRef = useRef(null);
  const frameRef = useRef(null);

  const clampScale = useCallback((value) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value)), []);

  const resetView = useCallback(() => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
      if (e.key === '0') resetView();
      if (e.key === '+' || e.key === '=') setScale((s) => clampScale(s * 1.2));
      if (e.key === '-' || e.key === '_') setScale((s) => clampScale(s / 1.2));
    };
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener('keydown', onKey);
    };
  }, [onClose, resetView, clampScale]);

  const zoomAt = useCallback(
    (nextScale, clientX, clientY) => {
      const frame = frameRef.current;
      if (!frame) {
        setScale(clampScale(nextScale));
        return;
      }
      const rect = frame.getBoundingClientRect();
      const cx = clientX - rect.left - rect.width / 2;
      const cy = clientY - rect.top - rect.height / 2;
      setScale((prev) => {
        const clamped = clampScale(nextScale);
        const ratio = clamped / prev;
        setOffset((off) => ({
          x: cx - (cx - off.x) * ratio,
          y: cy - (cy - off.y) * ratio,
        }));
        return clamped;
      });
    },
    [clampScale],
  );

  const onWheel = useCallback(
    (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      zoomAt(scale * factor, e.clientX, e.clientY);
    },
    [scale, zoomAt],
  );

  const onPointerDown = useCallback(
    (e) => {
      if (e.pointerType === 'touch' && e.isPrimary === false) return;
      // Pinch: track two touches via native touch events below.
      if (scale <= 1 && e.pointerType !== 'touch') {
        // At 1x, allow drag only after zoom; click backdrop still closes.
      }
      e.currentTarget.setPointerCapture?.(e.pointerId);
      dragRef.current = {
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        origX: offset.x,
        origY: offset.y,
        moved: false,
      };
    },
    [offset.x, offset.y, scale],
  );

  const onPointerMove = useCallback((e) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    const dx = e.clientX - drag.startX;
    const dy = e.clientY - drag.startY;
    if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
    setOffset({ x: drag.origX + dx, y: drag.origY + dy });
  }, []);

  const onPointerUp = useCallback(
    (e) => {
      const drag = dragRef.current;
      if (!drag || drag.pointerId !== e.pointerId) return;
      const wasTap = !drag.moved;
      dragRef.current = null;
      if (wasTap && scale <= 1.02) {
        // Tap empty / image at fit zoom closes — unless they used zoom buttons.
        // Keep open on image tap; backdrop handles close.
      }
    },
    [scale],
  );

  const onDoubleClick = useCallback(
    (e) => {
      e.stopPropagation();
      if (scale > 1.05) {
        resetView();
        return;
      }
      zoomAt(2.5, e.clientX, e.clientY);
    },
    [scale, resetView, zoomAt],
  );

  const onTouchStart = useCallback(
    (e) => {
      if (e.touches.length === 2) {
        const [a, b] = e.touches;
        const dist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
        pinchRef.current = {
          startDist: dist,
          startScale: scale,
          midX: (a.clientX + b.clientX) / 2,
          midY: (a.clientY + b.clientY) / 2,
        };
        dragRef.current = null;
      }
    },
    [scale],
  );

  const onTouchMove = useCallback(
    (e) => {
      const pinch = pinchRef.current;
      if (!pinch || e.touches.length !== 2) return;
      e.preventDefault();
      const [a, b] = e.touches;
      const dist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      const next = pinch.startScale * (dist / Math.max(pinch.startDist, 1));
      zoomAt(next, pinch.midX, pinch.midY);
    },
    [zoomAt],
  );

  const onTouchEnd = useCallback(() => {
    if (!pinchRef.current) return;
    pinchRef.current = null;
  }, []);

  if (!src) return null;

  return createPortal(
    <div
      className="zoomable-lightbox"
      role="dialog"
      aria-modal="true"
      aria-label={alt}
      onClick={onClose}
    >
      <div className="zoomable-lightbox__toolbar" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="zoomable-lightbox__btn" onClick={() => setScale((s) => clampScale(s / 1.25))} aria-label="Zoom out">
          −
        </button>
        <button type="button" className="zoomable-lightbox__btn" onClick={resetView} aria-label="Reset zoom">
          {Math.round(scale * 100)}%
        </button>
        <button type="button" className="zoomable-lightbox__btn" onClick={() => setScale((s) => clampScale(s * 1.25))} aria-label="Zoom in">
          +
        </button>
        <button type="button" className="zoomable-lightbox__btn zoomable-lightbox__btn--close" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>
      <div
        className="zoomable-lightbox__hint"
        onClick={(e) => e.stopPropagation()}
      >
        Scroll or pinch to zoom · drag to pan · double-click to toggle · Esc to close
      </div>
      <div
        ref={frameRef}
        className="zoomable-lightbox__stage"
        onClick={(e) => e.stopPropagation()}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={onDoubleClick}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <img
          src={src}
          alt={alt}
          className="zoomable-lightbox__img"
          draggable={false}
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
            cursor: scale > 1 ? 'grab' : 'zoom-in',
          }}
        />
      </div>
    </div>,
    document.body,
  );
}

export function resolveSummaryImageSrc(summaryImage) {
  if (!summaryImage || typeof summaryImage !== 'string') return null;
  if (
    summaryImage.startsWith('data:') ||
    summaryImage.startsWith('http://') ||
    summaryImage.startsWith('https://')
  ) {
    return summaryImage;
  }
  return `data:image/png;base64,${summaryImage}`;
}
