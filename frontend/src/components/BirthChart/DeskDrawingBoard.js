import React, { useCallback, useEffect, useRef, useState } from 'react';
import './DeskDrawingBoard.css';

const PALETTE = [
  { id: 'gold', label: 'Gold', value: '#b8892f' },
  { id: 'red', label: 'Red', value: '#c0392b' },
  { id: 'green', label: 'Green', value: '#1e7a46' },
  { id: 'blue', label: 'Blue', value: '#1d4e89' },
];

const clamp01 = (value) => Math.min(1, Math.max(0, value));

export const deskDrawingPoint = (clientX, clientY, rect) => ([
  clamp01((clientX - rect.left) / Math.max(1, rect.width)),
  clamp01((clientY - rect.top) / Math.max(1, rect.height)),
]);

const strokePath = (points, width, height) => points
  .map(([x, y], index) => `${index ? 'L' : 'M'} ${x * width} ${y * height}`)
  .join(' ');

const arrowHead = (points, width, height) => {
  if (points.length < 2) return '';
  const [startX, startY] = points[0];
  const [endX, endY] = points[points.length - 1];
  const x1 = startX * width;
  const y1 = startY * height;
  const x2 = endX * width;
  const y2 = endY * height;
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const length = 14;
  const spread = Math.PI / 7;
  return [
    `M ${x2} ${y2}`,
    `L ${x2 - length * Math.cos(angle - spread)} ${y2 - length * Math.sin(angle - spread)}`,
    `L ${x2 - length * Math.cos(angle + spread)} ${y2 - length * Math.sin(angle + spread)}`,
    'Z',
  ].join(' ');
};

const DeskDrawingBoard = ({ active, onActiveChange, drawingKey, showLauncher = false }) => {
  const layerRef = useRef(null);
  const toolbarRef = useRef(null);
  const activeStrokeRef = useRef(null);
  const toolbarDragRef = useRef(null);
  const drawingsRef = useRef(new Map());
  const [strokes, setStrokes] = useState([]);
  const [tool, setTool] = useState('pen');
  const [color, setColor] = useState(PALETTE[0].value);
  const [boardSize, setBoardSize] = useState({ width: 1, height: 1 });
  const [toolbarPosition, setToolbarPosition] = useState(null);

  const updateStrokes = useCallback((updater) => {
    setStrokes((current) => {
      const next = typeof updater === 'function' ? updater(current) : updater;
      drawingsRef.current.set(drawingKey, next);
      return next;
    });
  }, [drawingKey]);

  useEffect(() => {
    setStrokes(drawingsRef.current.get(drawingKey) || []);
    activeStrokeRef.current = null;
  }, [drawingKey]);

  useEffect(() => {
    const layer = layerRef.current;
    if (!layer) return undefined;
    const measure = () => {
      const rect = layer.getBoundingClientRect();
      const next = {
        width: Math.max(1, Math.round(rect.width)),
        height: Math.max(1, Math.round(rect.height)),
      };
      setBoardSize((current) => (
        current.width === next.width && current.height === next.height ? current : next
      ));
    };
    measure();
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(measure);
    observer?.observe(layer);
    window.addEventListener('resize', measure);
    return () => {
      observer?.disconnect();
      window.removeEventListener('resize', measure);
    };
  }, [active, showLauncher]);

  useEffect(() => {
    if (!active) return undefined;
    const previousUserSelect = document.body.style.userSelect;
    const previousOverscroll = document.body.style.overscrollBehavior;
    document.body.style.userSelect = 'none';
    document.body.style.overscrollBehavior = 'none';
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onActiveChange(false);
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'z') {
        event.preventDefault();
        updateStrokes((current) => current.slice(0, -1));
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.userSelect = previousUserSelect;
      document.body.style.overscrollBehavior = previousOverscroll;
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [active, onActiveChange, updateStrokes]);

  const pointForEvent = (event) => {
    const rect = layerRef.current?.getBoundingClientRect();
    return rect ? deskDrawingPoint(event.clientX, event.clientY, rect) : [0, 0];
  };

  const beginStroke = (event) => {
    if (!active || event.button > 0) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    const stroke = { color, tool, points: [pointForEvent(event)] };
    activeStrokeRef.current = stroke;
    updateStrokes((current) => [...current, stroke]);
  };

  const extendStroke = (event) => {
    const current = activeStrokeRef.current;
    if (!active || !current) return;
    event.preventDefault();
    const point = pointForEvent(event);
    current.points = current.tool === 'arrow'
      ? [current.points[0], point]
      : [...current.points, point];
    const replacement = { ...current, points: [...current.points] };
    updateStrokes((items) => [...items.slice(0, -1), replacement]);
  };

  const finishStroke = (event) => {
    if (event?.currentTarget?.hasPointerCapture?.(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    activeStrokeRef.current = null;
  };

  const clampToolbarPosition = useCallback((left, top, width, height) => ({
    left: Math.max(8, Math.min(left, window.innerWidth - width - 8)),
    top: Math.max(8, Math.min(top, window.innerHeight - height - 8)),
  }), []);

  const beginToolbarDrag = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const toolbar = toolbarRef.current;
    if (!toolbar) return;
    const rect = toolbar.getBoundingClientRect();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    toolbarDragRef.current = {
      pointerId: event.pointerId,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top,
      width: rect.width,
      height: rect.height,
    };
    setToolbarPosition({ left: rect.left, top: rect.top });
  };

  const moveToolbar = (event) => {
    const drag = toolbarDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    event.preventDefault();
    setToolbarPosition(clampToolbarPosition(
      event.clientX - drag.offsetX,
      event.clientY - drag.offsetY,
      drag.width,
      drag.height,
    ));
  };

  const finishToolbarDrag = (event) => {
    if (event.currentTarget.hasPointerCapture?.(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    toolbarDragRef.current = null;
  };

  useEffect(() => {
    if (!toolbarPosition) return undefined;
    const keepToolbarVisible = () => {
      const rect = toolbarRef.current?.getBoundingClientRect();
      if (!rect) return;
      setToolbarPosition((current) => current && clampToolbarPosition(
        current.left, current.top, rect.width, rect.height,
      ));
    };
    window.addEventListener('resize', keepToolbarVisible);
    return () => window.removeEventListener('resize', keepToolbarVisible);
  }, [clampToolbarPosition, toolbarPosition]);

  if (!active && !strokes.length && !showLauncher) return null;

  return (
    <>
      <div
        ref={layerRef}
        className={`desk-drawing-board${active ? ' is-active' : ''}`}
        onPointerDown={beginStroke}
        onPointerMove={extendStroke}
        onPointerUp={finishStroke}
        onPointerCancel={finishStroke}
        aria-hidden="true"
      >
        <svg viewBox={`0 0 ${boardSize.width} ${boardSize.height}`} preserveAspectRatio="none">
          {strokes.map((stroke, index) => {
            const path = strokePath(stroke.points, boardSize.width, boardSize.height);
            if (!path) return null;
            return (
              <g key={`desk-stroke-${index}`}>
                <path d={path} stroke={stroke.color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                {stroke.tool === 'arrow' && stroke.points.length > 1
                  ? <path d={arrowHead(stroke.points, boardSize.width, boardSize.height)} fill={stroke.color} />
                  : null}
              </g>
            );
          })}
        </svg>
      </div>

      {active ? (
        <div
          ref={toolbarRef}
          className="desk-drawing-toolbar"
          role="toolbar"
          aria-label="Drawing tools"
          style={toolbarPosition ? {
            left: `${toolbarPosition.left}px`,
            top: `${toolbarPosition.top}px`,
            bottom: 'auto',
            transform: 'none',
          } : undefined}
        >
          <button
            type="button"
            className="desk-drawing-toolbar__drag"
            onPointerDown={beginToolbarDrag}
            onPointerMove={moveToolbar}
            onPointerUp={finishToolbarDrag}
            onPointerCancel={finishToolbarDrag}
            onDoubleClick={() => setToolbarPosition(null)}
            aria-label="Move drawing toolbar"
            title="Drag to move · Double-click to reset"
          >
            <span aria-hidden="true">⠿</span>
          </button>
          <span className="desk-drawing-toolbar__mode">Drawing on the full desk</span>
          <div className="desk-drawing-toolbar__group" aria-label="Drawing tool">
            <button type="button" className={tool === 'pen' ? 'is-active' : ''} onClick={() => setTool('pen')} aria-pressed={tool === 'pen'} title="Freehand pen">✎ <span>Pen</span></button>
            <button type="button" className={tool === 'arrow' ? 'is-active' : ''} onClick={() => setTool('arrow')} aria-pressed={tool === 'arrow'} title="Arrow">→ <span>Arrow</span></button>
          </div>
          <div className="desk-drawing-toolbar__colors" aria-label="Drawing color">
            {PALETTE.map((swatch) => (
              <button
                type="button"
                key={swatch.id}
                className={color === swatch.value ? 'is-active' : ''}
                style={{ '--drawing-swatch': swatch.value }}
                onClick={() => setColor(swatch.value)}
                aria-label={swatch.label}
                aria-pressed={color === swatch.value}
              />
            ))}
          </div>
          <button type="button" onClick={() => updateStrokes((current) => current.slice(0, -1))} disabled={!strokes.length} title="Undo last stroke">↶ <span>Undo</span></button>
          <button type="button" onClick={() => updateStrokes([])} disabled={!strokes.length} title="Clear all drawing">⌫ <span>Clear</span></button>
          <button type="button" className="desk-drawing-toolbar__done" onClick={() => onActiveChange(false)}>Done</button>
        </div>
      ) : showLauncher ? (
        <button type="button" className="desk-drawing-launcher" onClick={() => onActiveChange(true)} aria-label="Draw on the desk" title="Draw on the full desk">✎</button>
      ) : null}
    </>
  );
};

export default DeskDrawingBoard;
