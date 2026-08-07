import React from 'react';
import './ChartOverlayActions.css';

/**
 * Floating chart actions (reset ASC, clear highlight/aspects).
 * In deskMode, sits below the N / maximize mini-bar.
 */
export default function ChartOverlayActions({
  deskMode = false,
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

  return (
    <div
      className={`chart-overlay-actions${deskMode ? ' chart-overlay-actions--desk' : ''}`}
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
}
