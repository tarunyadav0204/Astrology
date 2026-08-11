import React, { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import './ShadbalaModal.css';

const COMPONENT_META = {
  sthana_bala: { name: 'Sthana Bala', note: 'Positional strength' },
  dig_bala: { name: 'Dig Bala', note: 'Directional strength' },
  kala_bala: { name: 'Kala Bala', note: 'Temporal strength' },
  chesta_bala: { name: 'Chesta Bala', note: 'Motional strength' },
  naisargika_bala: { name: 'Naisargika Bala', note: 'Natural strength' },
  drik_bala: { name: 'Drik Bala', note: 'Aspectual strength' },
};

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa',
};

const GRADE_GUIDE = [
  { grade: 'Excellent', range: '6+ Rupas', note: 'Very strong' },
  { grade: 'Good', range: '5–6 Rupas', note: 'Strong' },
  { grade: 'Average', range: '4–5 Rupas', note: 'Moderate' },
  { grade: 'Weak', range: 'Below 4 Rupas', note: 'Low strength' },
];

function gradeClass(grade) {
  return String(grade || 'unrated').toLowerCase().replace(/[^a-z0-9]+/g, '-');
}

function formatValue(value, digits = 2) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits).replace(/\.00$/, '') : '—';
}

function FormulaDetails({ formulas }) {
  if (!formulas || !Object.keys(formulas).length) return null;
  return (
    <details className="shadbala-formulas">
      <summary>View classical calculation notes</summary>
      <div className="shadbala-formulas__list">
        {Object.entries(formulas).map(([formulaType, formulaData]) => (
          <article key={formulaType}>
            <h5>{formulaType.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())}</h5>
            {typeof formulaData === 'object' && formulaData !== null ? (
              <div>
                {formulaData.formula ? <p><strong>Formula</strong><code>{formulaData.formula}</code></p> : null}
                {formulaData.explanation ? <p><strong>Meaning</strong><span>{formulaData.explanation}</span></p> : null}
                {formulaData.calculation ? <p><strong>Calculation</strong><span>{formulaData.calculation}</span></p> : null}
                {formulaData.components ? (
                  <div className="shadbala-formulas__components">
                    {Object.entries(formulaData.components).map(([key, value]) => (
                      <section key={key}>
                        <b>{key.replaceAll('_', ' ')}</b>
                        {typeof value === 'object' && value !== null ? (
                          <>
                            {value.formula ? <code>{value.formula}</code> : null}
                            {value.explanation ? <span>{value.explanation}</span> : null}
                          </>
                        ) : <span>{String(value)}</span>}
                      </section>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : <p>{String(formulaData)}</p>}
          </article>
        ))}
      </div>
    </details>
  );
}

function SummaryCard({ label, entry, tone }) {
  if (!entry) return null;
  const [planet, data] = entry;
  return (
    <article className={`shadbala-summary-card shadbala-summary-card--${tone}`}>
      <span className="shadbala-summary-card__label">{label}</span>
      <div className="shadbala-summary-card__planet">
        <b>{PLANET_ABBR[planet] || planet.slice(0, 2)}</b>
        <div><strong>{planet}</strong><span>{formatValue(data.total_rupas)} Rupas</span></div>
      </div>
      <em className={`shadbala-grade shadbala-grade--${gradeClass(data.grade)}`}>{data.grade || 'Unrated'}</em>
    </article>
  );
}

const ShadbalaModal = ({ chartData, birthData, onClose }) => {
  const [shadbalaData, setShadbalaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedPlanet, setExpandedPlanet] = useState(null);

  useEffect(() => {
    let active = true;
    const fetchShadbala = async () => {
      try {
        setLoading(true);
        const response = await apiService.calculateShadbala(chartData, birthData);
        if (active) setShadbalaData(response);
      } catch (err) {
        if (active) setError(err.message || 'Failed to calculate Shadbala');
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchShadbala();
    return () => { active = false; };
  }, [chartData, birthData]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose?.();
    };
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const planetEntries = useMemo(() => (
    Object.entries(shadbalaData?.shadbala || {})
      .sort(([, first], [, second]) => Number(second.total_rupas || 0) - Number(first.total_rupas || 0))
  ), [shadbalaData]);

  const strongest = shadbalaData?.summary?.strongest || planetEntries[0];
  const weakest = shadbalaData?.summary?.weakest || planetEntries[planetEntries.length - 1];

  const modalContent = (
    <div className="shadbala-modal-overlay" onMouseDown={onClose}>
      <section
        className="shadbala-modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shadbala-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="shadbala-modal-header">
          <div>
            <span>Classical planetary strength</span>
            <h2 id="shadbala-title">Shadbala</h2>
            <p>Six complementary measures of each planet’s capacity to deliver results.</p>
          </div>
          <button type="button" className="shadbala-close-btn" onClick={onClose} aria-label="Close Shadbala">×</button>
        </header>

        <div className="shadbala-modal-body">
          {loading ? (
            <div className="shadbala-loading">
              <div className="shadbala-spinner" />
              <strong>Calculating planetary strengths</strong>
              <span>Combining all six classical strength measures…</span>
            </div>
          ) : null}

          {error ? (
            <div className="shadbala-error">
              <strong>Shadbala could not be calculated</strong>
              <span>{error}</span>
            </div>
          ) : null}

          {shadbalaData && !loading ? (
            <>
              <section className="shadbala-overview" aria-label="Shadbala overview">
                <SummaryCard label="Leading strength" entry={strongest} tone="strong" />
                <SummaryCard label="Lowest relative strength" entry={weakest} tone="weak" />
                <div className="shadbala-overview__note">
                  <strong>{planetEntries.length} planets assessed</strong>
                  <span>Rupas combine positional, directional, temporal, motional, natural and aspectual strength.</span>
                </div>
              </section>

              <section className="shadbala-results">
                <header>
                  <div><span>Planet comparison</span><h3>Strength profile</h3></div>
                  <small>Select a planet to inspect its six components</small>
                </header>
                <div className="shadbala-results__head" aria-hidden="true">
                  <span>Planet</span><span>Strength</span><span>Assessment</span><span />
                </div>
                <div className="shadbala-planet-list">
                  {planetEntries.map(([planet, data]) => {
                    const expanded = expandedPlanet === planet;
                    const benchmark = Math.min(100, Math.max(4, (Number(data.total_rupas || 0) / 6) * 100));
                    return (
                      <article key={planet} className={`shadbala-planet${expanded ? ' is-expanded' : ''}`}>
                        <button
                          type="button"
                          className="shadbala-planet__summary"
                          onClick={() => setExpandedPlanet(expanded ? null : planet)}
                          aria-expanded={expanded}
                        >
                          <span className="shadbala-planet__identity">
                            <b>{PLANET_ABBR[planet] || planet.slice(0, 2)}</b><strong>{planet}</strong>
                          </span>
                          <span className="shadbala-planet__strength">
                            <span><strong>{formatValue(data.total_rupas)}</strong> Rupas <small>{formatValue(data.total_points, 0)} points</small></span>
                            <i><em style={{ width: `${benchmark}%` }} /></i>
                          </span>
                          <em className={`shadbala-grade shadbala-grade--${gradeClass(data.grade)}`}>{data.grade || 'Unrated'}</em>
                          <span className="shadbala-planet__chevron" aria-hidden="true">⌄</span>
                        </button>

                        {expanded ? (
                          <div className="shadbala-planet__details">
                            <header><strong>Six-fold breakdown</strong><span>Component values in Shadbala points</span></header>
                            <div className="shadbala-components">
                              {Object.entries(data.components || {}).map(([component, value]) => {
                                const meta = COMPONENT_META[component] || { name: component.replaceAll('_', ' '), note: 'Classical component' };
                                return (
                                  <div key={component}>
                                    <span><strong>{meta.name}</strong><small>{meta.note}</small></span>
                                    <b>{formatValue(value)}</b>
                                  </div>
                                );
                              })}
                            </div>
                            <FormulaDetails formulas={data.formulas} />
                          </div>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>

              <details className="shadbala-guide">
                <summary>How to read the strength grades</summary>
                <div>
                  {GRADE_GUIDE.map((item) => (
                    <span key={item.grade}>
                      <i className={`shadbala-grade-dot shadbala-grade-dot--${gradeClass(item.grade)}`} />
                      <strong>{item.grade}</strong><b>{item.range}</b><em>{item.note}</em>
                    </span>
                  ))}
                </div>
                <p>Shadbala measures capacity, not whether a planet’s results are inherently favourable. Interpret strength together with lordship, dignity, placement and aspects.</p>
              </details>
            </>
          ) : null}
        </div>
      </section>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default ShadbalaModal;
