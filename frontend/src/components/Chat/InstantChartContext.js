import React from 'react';
import { useInstantChartRows } from '../../utils/useInstantChartRows';
import './InstantChartContext.css';

export default function InstantChartContext({ preview, active }) {
    const rows = useInstantChartRows(preview, active);
    if (!rows.length) return null;
    return (
        <aside className="instant-chart-context" data-source="calculation" dir={preview?.direction || 'auto'}>
            <div className="instant-chart-context-title">◇ {preview.title}</div>
            {rows.map(row => <div className="instant-chart-context-row" data-context-row={row.key} key={row.key}>{row.text}</div>)}
            {preview.as_of ? <time className="instant-chart-context-date" dateTime={preview.as_of}>{preview.as_of}</time> : null}
        </aside>
    );
}
