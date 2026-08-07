import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskStrengthStrip.css';

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa',
};

const DIG_SHORT = {
  exalted: 'Ex',
  debilitated: 'Db',
  moolatrikona: 'MT',
  own_sign: 'Own',
  favorable: '+',
  unfavorable: '−',
  neutral: '·',
};

function digTone(key) {
  if (key === 'exalted' || key === 'moolatrikona' || key === 'own_sign') return 'good';
  if (key === 'debilitated' || key === 'unfavorable') return 'warn';
  return 'neutral';
}

function sbTone(grade) {
  const g = String(grade || '').toLowerCase();
  if (g.includes('excellent') || g.includes('good')) return 'good';
  if (g.includes('weak') || g.includes('poor')) return 'warn';
  return 'neutral';
}

/**
 * Compact Dig + SB glance strip for the analysis dock.
 * Click Dig/SB labels to open full tool modals.
 */
export default function DeskStrengthStrip({
  birthData,
  chartData,
  onOpenTool,
}) {
  const [dig, setDig] = useState(null);
  const [sb, setSb] = useState(null);

  useEffect(() => {
    if (!birthData || !chartData) {
      setDig(null);
      setSb(null);
      return undefined;
    }
    let cancelled = false;
    Promise.all([
      apiService.calculatePlanetaryDignities(chartData, birthData).catch(() => null),
      apiService.calculateShadbala(chartData, birthData).catch(() => null),
    ]).then(([d, s]) => {
      if (cancelled) return;
      setDig(d);
      setSb(s);
    });
    return () => { cancelled = true; };
  }, [birthData, chartData]);

  const digChips = PLANETS.map((name) => {
    const row = dig?.dignities?.[name];
    const key = String(row?.dignity || 'neutral').toLowerCase().replace(/\s+/g, '_');
    return {
      name,
      label: ABBR[name],
      value: DIG_SHORT[key] || (row?.dignity ? String(row.dignity).slice(0, 2) : '·'),
      title: row ? `${name}: ${row.dignity}${row.combustion_status && row.combustion_status !== 'normal' ? ` · ${row.combustion_status}` : ''}` : name,
      tone: digTone(key),
      combust: row?.combustion_status === 'combust',
    };
  });

  const sbChips = PLANETS.map((name) => {
    const row = sb?.shadbala?.[name];
    const rupas = row?.total_rupas != null ? Number(row.total_rupas).toFixed(1) : '—';
    return {
      name,
      label: ABBR[name],
      value: rupas,
      title: row ? `${name}: ${rupas} rupas · ${row.grade || ''}` : name,
      tone: sbTone(row?.grade),
    };
  });

  const digSummary = dig?.summary;
  const sbStrong = sb?.summary?.strongest?.[0];
  const sbWeak = sb?.summary?.weakest?.[0];

  return (
    <div className="desk-str" aria-label="Dignity and Shadbala summary">
      <div className="desk-str__row">
        <button
          type="button"
          className="desk-str__label"
          onClick={() => onOpenTool?.('dignities')}
          title="Open planetary dignities"
        >
          Dig
        </button>
        <div className="desk-str__chips">
          {digChips.map((c) => (
            <span
              key={`d-${c.name}`}
              className={`desk-str__chip desk-str__chip--${c.tone}${c.combust ? ' is-combust' : ''}`}
              title={c.title}
            >
              <em>{c.label}</em>
              <strong>{c.value}</strong>
            </span>
          ))}
        </div>
        {digSummary?.exalted_planets?.length || digSummary?.debilitated_planets?.length ? (
          <span className="desk-str__meta" title="Exalted / Debilitated">
            {digSummary.exalted_planets?.length ? `Ex ${digSummary.exalted_planets.length}` : null}
            {digSummary.exalted_planets?.length && digSummary.debilitated_planets?.length ? ' · ' : null}
            {digSummary.debilitated_planets?.length ? `Db ${digSummary.debilitated_planets.length}` : null}
          </span>
        ) : null}
      </div>

      <div className="desk-str__row">
        <button
          type="button"
          className="desk-str__label"
          onClick={() => onOpenTool?.('shadbala')}
          title="Open Shadbala"
        >
          SB
        </button>
        <div className="desk-str__chips">
          {sbChips.map((c) => (
            <span
              key={`s-${c.name}`}
              className={`desk-str__chip desk-str__chip--${c.tone}`}
              title={c.title}
            >
              <em>{c.label}</em>
              <strong>{c.value}</strong>
            </span>
          ))}
        </div>
        {sbStrong || sbWeak ? (
          <span className="desk-str__meta" title="Strongest / weakest">
            {sbStrong ? `↑${ABBR[sbStrong] || sbStrong}` : null}
            {sbStrong && sbWeak ? ' ' : null}
            {sbWeak ? `↓${ABBR[sbWeak] || sbWeak}` : null}
          </span>
        ) : null}
      </div>
    </div>
  );
}
