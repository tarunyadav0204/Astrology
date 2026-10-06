import React from 'react';
import './ChartActivationKey.css';

export default function ChartActivationKey({
  enabled,
  onToggle,
  loading = false,
  compact = false,
  locked = false,
  onLocked,
}) {
  return (
    <div className={`chart-act-key${compact ? ' chart-act-key--compact' : ''}${enabled && !locked ? ' is-enabled' : ''}`}>
      <button
        type="button"
        aria-pressed={locked ? false : enabled}
        title={locked ? 'Chart marks require an Astrologer License.' : 'Color the houses that are active now'}
        onClick={() => (locked ? onLocked?.() : onToggle?.(!enabled))}
      >
        <i aria-hidden />
        <span>{loading && !locked ? 'Updating…' : 'Chart marks'}</span>
        {locked ? <em>License</em> : null}
      </button>
      {enabled && !locked ? (
        <div className="chart-act-key__legend" aria-label="House activation colors">
          <span><i className="is-strong" />Strong</span>
          <span><i className="is-active" />Active</span>
          <span><i className="is-period" />Period</span>
        </div>
      ) : null}
    </div>
  );
}
