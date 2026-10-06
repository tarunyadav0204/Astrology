import React from 'react';
import { createPortal } from 'react-dom';
import './ChartOverlayActions.css';

/**
 * Chart actions (reset ASC, clear highlight/aspects).
 * On the desk these sit in the chart header; elsewhere they float on the chart.
 */
export default function ChartOverlayActions({
  deskMode = false,
  host = null,
  highlightedPlanet,
  onClearHighlight,
  customAscendant,
  onResetAscendant,
  aspectsHighlight,
  onClearAspects,
}) {
  const showReset = customAscendant !== null && customAscendant !== undefined;
  const showAspects = Boolean(aspectsHighlight?.show);
  if (!highlightedPlanet && !showReset && !showAspects) return null;
  if (deskMode && !host) return null;

  const actions = (
    <div
      className={`chart-overlay-actions${deskMode ? ' chart-overlay-actions--header' : ''}`}
      role="toolbar"
      aria-label="Chart actions"
    >
      {highlightedPlanet ? (
        <button type="button" className="chart-overlay-actions__btn" onClick={onClearHighlight}>
          Clear
        </button>
      ) : null}
      {showReset ? (
        <button
          type="button"
          className="chart-overlay-actions__btn chart-overlay-actions__btn--reset"
          onClick={onResetAscendant}
          title="Restore birth ascendant"
        >
          Reset ASC
        </button>
      ) : null}
      {showAspects ? (
        <button type="button" className="chart-overlay-actions__btn" onClick={onClearAspects}>
          Clear aspects
        </button>
      ) : null}
    </div>
  );

  return host ? createPortal(actions, host) : actions;
}
