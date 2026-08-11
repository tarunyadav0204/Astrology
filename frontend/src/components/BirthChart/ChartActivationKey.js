import React from 'react';
import './ChartActivationKey.css';

export default function ChartActivationKey({ enabled, onToggle, loading = false, compact = false }) {
  return (
    <div className={`chart-act-key${compact ? ' chart-act-key--compact' : ''}${enabled ? ' is-enabled' : ''}`}>
      <button type="button" aria-pressed={enabled} onClick={() => onToggle?.(!enabled)}>
        <i aria-hidden />
        <span>{loading ? 'Updating…' : 'Activations'}</span>
      </button>
      {enabled ? (
        <div className="chart-act-key__legend" aria-label="House activation colors">
          <span><i className="is-strong" />Strong</span>
          <span><i className="is-active" />Active</span>
          <span><i className="is-period" />Period</span>
        </div>
      ) : null}
    </div>
  );
}
