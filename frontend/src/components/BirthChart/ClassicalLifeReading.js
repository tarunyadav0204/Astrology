import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/apiService';
import './ClassicalLifeReading.css';

const CONDITION_LABELS = {
  supported: 'Supported',
  mixed: 'Support and pressure',
  under_pressure: 'Under pressure',
  unqualified: 'No strong modifier',
};

const requestCache = new Map();

function chartFingerprint(chartData, birthData) {
  const planets = Object.entries(chartData?.planets || {}).map(([name, row]) => [
    name, row?.longitude, row?.sign, row?.house, Boolean(row?.retrograde),
  ]);
  return JSON.stringify([
    birthData?.id || birthData?.birthchart_id,
    birthData?.date, birthData?.time, birthData?.latitude, birthData?.longitude,
    chartData?.ascendant, planets,
  ]);
}

function loadReading(chartData, birthData) {
  const key = chartFingerprint(chartData, birthData);
  if (!requestCache.has(key)) {
    const request = apiService.calculateClassicalReading(chartData, birthData)
      .then((response) => response?.classical_reading)
      .catch((error) => {
        requestCache.delete(key);
        throw error;
      });
    requestCache.set(key, request);
  }
  return requestCache.get(key);
}

function sentence(text) {
  const value = String(text || '').trim();
  if (!value) return '';
  return `${value.charAt(0).toUpperCase()}${value.slice(1).replace(/[.!?]+$/, '')}.`;
}

function unique(rows, key) {
  const seen = new Set();
  return (rows || []).filter((row) => {
    const identity = key(row);
    if (seen.has(identity)) return false;
    seen.add(identity);
    return true;
  });
}

function Evidence({ insight }) {
  const facts = unique(
    (insight.contributions || []).flatMap((row) => row?.evidence?.facts || []),
    (row) => `${row.key}:${row.value}`,
  );
  const summaries = unique(
    (insight.contributions || []).map((row) => row?.evidence?.summary).filter(Boolean),
    (row) => `${row.key}:${row.text}`,
  );
  const sources = unique(insight.sources, (row) => `${row.rule_key}:${row.reference}`);
  return (
    <details className="clr-evidence">
      <summary>Why this is shown <span>Rules and references</span></summary>
      <div className="clr-evidence__body">
        {summaries.map((row) => <p key={`${row.key}:${row.text}`}>{row.text}</p>)}
        {facts.length ? <div className="clr-facts">{facts.map((fact) => (
          <div className={`clr-fact is-${fact.state || 'neutral'}`} key={`${fact.key}:${fact.value}`}>
            <strong>{fact.label}</strong><span>{fact.value}</span>
          </div>
        ))}</div> : null}
        {sources.length ? <div className="clr-sources"><strong>Classical sources</strong>{sources.map((source) => (
          <a key={`${source.rule_key}:${source.reference}`} href={source.witness_url} target="_blank" rel="noopener noreferrer">
            <span>{source.reference}</span><small>{source.rule_key}</small>
          </a>
        ))}</div> : null}
        {(insight.controls || []).map((control) => <p className="clr-control" key={control.key}>{control.text}</p>)}
      </div>
    </details>
  );
}

export default function ClassicalLifeReading({
  birthData,
  chartData,
  variant = 'compact',
  onOpenFull,
  initialAreaKey = '',
}) {
  const navigate = useNavigate();
  const [reading, setReading] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedAreaKey, setSelectedAreaKey] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [retryNonce, setRetryNonce] = useState(0);
  const fingerprint = useMemo(() => chartFingerprint(chartData, birthData), [chartData, birthData]);

  useEffect(() => {
    let cancelled = false;
    if (!chartData?.planets || chartData?.ascendant == null) {
      setReading(null);
      return undefined;
    }
    setLoading(true);
    setError('');
    loadReading(chartData, birthData)
      .then((payload) => {
        if (cancelled) return;
        if (!payload?.areas?.length) throw new Error('No published classical readings are available for this chart.');
        setReading(payload);
        setSelectedAreaKey((current) => {
          if (payload.areas.some((row) => row.key === initialAreaKey)) return initialAreaKey;
          if (payload.areas.some((row) => row.key === current)) return current;
          return payload.areas[0].key;
        });
      })
      .catch((reason) => {
        if (!cancelled) setError(reason?.response?.data?.detail?.message || reason?.message || 'The classical reading could not be loaded.');
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [fingerprint, chartData, birthData, initialAreaKey, retryNonce]);

  const areas = reading?.areas || [];
  const selected = areas.find((row) => row.key === selectedAreaKey) || areas[0];
  const subjects = selected?.subjects || [];
  const subjectIsValid = selectedSubject === 'all' || subjects.some((row) => row.key === selectedSubject);
  const activeSubject = subjectIsValid ? selectedSubject : 'all';
  const filteredInsights = (selected?.insights || []).filter((row) => activeSubject === 'all' || row.subject?.key === activeSubject);
  const insights = variant === 'compact' ? filteredInsights.slice(0, 2) : filteredInsights;
  const openFull = onOpenFull || (() => navigate(`/life-reading${selected ? `?area=${encodeURIComponent(selected.key)}` : ''}`));

  if (!chartData?.planets) return <div className="clr-state"><strong>Select a birth chart</strong><p>Choose a native to open the classical Life reading.</p></div>;
  if (loading) return <div className="clr-state clr-state--loading"><i aria-hidden></i><strong>Reading the published classical rules…</strong><p>Bringing the matching indications together by life area.</p></div>;
  if (error) return <div className="clr-state clr-state--error"><strong>Life reading unavailable</strong><p>{error}</p><button type="button" onClick={() => { requestCache.delete(fingerprint); setReading(null); setError(''); setRetryNonce((value) => value + 1); }}>Try again</button></div>;
  if (!selected) return null;

  const supports = unique(filteredInsights.flatMap((row) => row.supports || []), (row) => row);
  const pressures = unique(filteredInsights.flatMap((row) => row.pressures || []), (row) => row);
  const condition = supports.length && pressures.length ? 'mixed' : supports.length ? 'supported' : pressures.length ? 'under_pressure' : 'unqualified';

  return (
    <div className={`clr clr--${variant}`}>
      <div className="clr-intro">
        <span>Classical natal reading</span>
        <p>This describes the birth-chart promise. Dashas and transits are evaluated separately for timing.</p>
      </div>
      <div className="clr-layout">
        <aside className="clr-areas" aria-label="Life areas">
          <label htmlFor={`clr-area-${variant}`}>Life area</label>
          <select id={`clr-area-${variant}`} value={selected.key} onChange={(event) => { setSelectedAreaKey(event.target.value); setSelectedSubject('all'); }}>
            {areas.map((area) => <option value={area.key} key={area.key}>H{area.house} · {area.label}</option>)}
          </select>
          <div className="clr-area-list" role="tablist" aria-label="Choose life area">
            {areas.map((area) => <button type="button" role="tab" aria-selected={area.key === selected.key} className={area.key === selected.key ? 'is-active' : ''} onClick={() => { setSelectedAreaKey(area.key); setSelectedSubject('all'); }} key={area.key}><b>H{area.house}</b><span>{area.label}</span><small>{area.insight_count} indication{area.insight_count === 1 ? '' : 's'}</small></button>)}
          </div>
        </aside>
        <main className="clr-reading">
          <header className="clr-reading__head">
            <div><span>House {selected.house}</span><h2>{selected.label}</h2></div>
            <strong className={`clr-condition is-${condition}`}>{CONDITION_LABELS[condition]}</strong>
          </header>
          {subjects.length > 1 ? <div className="clr-subjects" role="tablist" aria-label="Topics"><button type="button" className={activeSubject === 'all' ? 'is-active' : ''} onClick={() => setSelectedSubject('all')}>All indications</button>{subjects.map((subject) => <button type="button" className={activeSubject === subject.key ? 'is-active' : ''} onClick={() => setSelectedSubject(subject.key)} key={subject.key}>{subject.label}</button>)}</div> : null}
          <div className="clr-insights">
            {insights.map((insight) => <article className="clr-insight" key={insight.dedupe_key || insight.insight_id}>
              <header><div><span>{insight.subject?.label}</span><h3>{insight.title}</h3></div><em className={`is-${insight.condition}`}>{CONDITION_LABELS[insight.condition] || insight.condition}</em></header>
              <div className="clr-statements">{(insight.statements || []).map((statement) => <p key={statement.key}>{sentence(statement.text)}</p>)}</div>
              {variant !== 'compact' ? <><div className="clr-testimony">{insight.supports?.length ? <section><strong>What supports this</strong>{insight.supports.map((row) => <p key={row}>{row}</p>)}</section> : null}{insight.pressures?.length ? <section><strong>What adds pressure</strong>{insight.pressures.map((row) => <p key={row}>{row}</p>)}</section> : null}</div><Evidence insight={insight} /></> : null}
            </article>)}
          </div>
          {variant === 'compact' ? <div className="clr-compact-actions"><p>{filteredInsights.length > insights.length ? `${filteredInsights.length - insights.length} more indications in this area.` : 'Open the complete reading with rules and source references.'}</p><button type="button" onClick={openFull}>Open full Life reading <span aria-hidden>→</span></button></div> : null}
        </main>
      </div>
    </div>
  );
}
