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

const PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

const STHANA_ROWS = [
  ['Uccha Bala', 'uccha_bala'],
  ['Sapta-vargaja Bala', 'saptavargaja_bala'],
  ['Ojhayugma Bala', 'ojha_yugma_bala'],
  ['Kendradi Bala', 'kendradi_bala'],
  ['Drekkana Bala', 'drekkana_bala'],
];

const KALA_ROWS = [
  ['Nata-Unnata Bala', 'nathonniya_bala'],
  ['Paksha Bala', 'paksha_bala'],
  ['Tri-Bhaga Bala', 'tribhaga_bala'],
  ['Varsha Bala', 'varsha_bala'],
  ['Maasa Bala', 'maasa_bala'],
  ['Vaara Bala', 'dina_bala'],
  ['Hora Bala', 'hora_bala'],
  ['Ayana Bala', 'ayana_bala'],
  ['Yuddha Bala', 'yuddha_bala'],
];

function requirementClass(data) {
  return data?.meets_minimum ? 'meets-requirement' : 'below-requirement';
}

function formatValue(value, digits = 2) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits).replace(/\.00$/, '') : '—';
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
      <em className={`shadbala-grade shadbala-grade--${requirementClass(data)}`}>{formatValue(data.required_ratio)}× required</em>
    </article>
  );
}

function ShadbalaWorksheet({ data }) {
  const availablePlanets = PLANET_ORDER.filter((planet) => data?.[planet]);
  if (!availablePlanets.length) return null;

  const valueFor = (planet, path) => path.reduce((value, key) => value?.[key], data[planet]);
  const rows = [
    ...STHANA_ROWS.map(([label, key]) => ({ label, path: ['detailed_breakdown', 'sthana_components', key] })),
    { label: '1. Sthana Bala', path: ['components', 'sthana_bala'], major: true },
    { label: '2. Dig Bala', path: ['components', 'dig_bala'], major: true },
    ...KALA_ROWS.map(([label, key]) => ({ label, path: ['detailed_breakdown', 'kala_components', key] })),
    { label: '3. Kala Bala', path: ['components', 'kala_bala'], major: true },
    { label: '4. Chesta Bala', path: ['components', 'chesta_bala'], major: true },
    { label: '5. Naisargika Bala', path: ['components', 'naisargika_bala'], major: true },
    { label: '6. Drik Bala', path: ['components', 'drik_bala'], major: true },
    { label: 'Total Shadbala', path: ['total_points'], total: true },
    { label: 'Shadbala in Rupas', path: ['total_rupas'], total: true },
    { label: 'Minimum requirement', path: ['minimum_required_points'], standard: true },
    { label: 'Ratio of required', path: ['required_ratio'], standard: true, suffix: '×' },
    { label: 'Relative rank', path: ['relative_rank'], standard: true, integer: true },
    { label: 'Ishta Phala', path: ['ishta_phala'], phala: true },
    { label: 'Kashta Phala', path: ['kashta_phala'], phala: true },
  ];

  return (
    <section className="shadbala-worksheet" aria-label="Complete Shadbala worksheet">
      <header>
        <div><span>Parashara-style worksheet</span><h3>Complete Shadbala table</h3></div>
        <small>Values are Virupas unless a row says Rupas or ratio.</small>
      </header>
      <div className="shadbala-worksheet__scroll">
        <table>
          <thead><tr><th scope="col">Bala</th>{availablePlanets.map((planet) => <th scope="col" key={planet}>{planet}</th>)}</tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className={`${row.major ? 'is-major' : ''}${row.total ? ' is-total' : ''}${row.standard ? ' is-standard' : ''}${row.phala ? ' is-phala' : ''}`}>
                <th scope="row">{row.label}</th>
                {availablePlanets.map((planet) => {
                  const value = valueFor(planet, row.path);
                  return <td key={planet}>{row.integer ? formatValue(value, 0) : formatValue(value)}{row.suffix || ''}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function BhavaBalaWorksheet({ data }) {
  const houses = Array.from({ length: 12 }, (_, index) => data?.[String(index + 1)])
    .filter(Boolean);
  if (!houses.length) return null;
  const rows = [
    ['Sign', 'sign_name', 'text'],
    ['Lord', 'lord', 'text'],
    ['From lord', 'from_lord'],
    ['Bhava Dig Bala', 'dig_bala'],
    ['Bhava Drishti Bala', 'drishti_bala'],
    ['Planets in Bhava', 'planets_in_bala'],
    ['Day / twilight / night', 'day_night_bala'],
    ['Bhava Bala total', 'total_points', 'total'],
    ['Bhava Bala in Rupas', 'total_rupas', 'total'],
    ['Relative rank', 'relative_rank', 'rank'],
  ];
  return (
    <section className="shadbala-worksheet bhava-bala-worksheet" aria-label="Classical Bhava Bala worksheet">
      <header>
        <div><span>BPHS 27.26–31</span><h3>Classical Bhava Bala</h3></div>
        <small>House strength in Virupas; this is separate from the app’s weighted house score.</small>
      </header>
      <div className="shadbala-worksheet__scroll">
        <table>
          <thead><tr><th scope="col">Bala</th>{houses.map((house) => <th scope="col" key={house.house}>H{house.house}</th>)}</tr></thead>
          <tbody>
            {rows.map(([label, key, kind]) => (
              <tr key={key} className={kind === 'total' ? 'is-total' : ''}>
                <th scope="row">{label}</th>
                {houses.map((house) => (
                  <td key={house.house}>{kind === 'text' ? house[key] : formatValue(house[key], kind === 'rank' ? 0 : 2)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="bhava-bala-worksheet__note">
        Total = lord’s Shadbala + directional strength + net degree-based aspects + classical occupation and birth-phase adjustments. A stronger house is more capable of expressing its topics; it is not automatically more benefic.
      </p>
    </section>
  );
}

function SupplementaryHouseScore({ data }) {
  const houses = Array.from({ length: 12 }, (_, index) => data?.[String(index + 1)]).filter(Boolean);
  if (!houses.length) return <div className="shadbala-empty-tab">No supplementary house score is available for this chart.</div>;
  return (
    <section className="shadbala-results shadbala-house-score">
      <header>
        <div><span>Supplementary diagnostic</span><h3>App house-strength score</h3></div>
        <small>This weighted score is not classical Bhava Bala.</small>
      </header>
      <div className="shadbala-house-score__grid">
        {houses.map((house, index) => (
          <article key={index + 1}>
            <span>House {index + 1}</span>
            <strong>{formatValue(house.total_strength, 0)}<small>/100</small></strong>
            <em>{house.grade || '—'}</em>
          </article>
        ))}
      </div>
      <p className="bhava-bala-worksheet__note">Uses the app’s separate lord, resident-planet, aspect, sign and positional weighting. Use the Classical Bhava Bala tab for the BPHS worksheet.</p>
    </section>
  );
}

const ShadbalaModal = ({ chartData, birthData, onClose }) => {
  const [shadbalaData, setShadbalaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedPlanet, setExpandedPlanet] = useState(null);
  const [activeTab, setActiveTab] = useState('planetary');

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
      .sort(([, first], [, second]) => Number(first.relative_rank || 99) - Number(second.relative_rank || 99))
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
              <nav className="shadbala-tabs" role="tablist" aria-label="Strength worksheets">
                {[
                  ['planetary', 'Planetary Shadbala'],
                  ['bhava', 'Classical Bhava Bala'],
                  ['supplementary', 'App house score'],
                ].map(([key, label]) => (
                  <button type="button" role="tab" key={key} className={activeTab === key ? 'is-active' : ''} onClick={() => setActiveTab(key)} aria-selected={activeTab === key}>{label}</button>
                ))}
              </nav>

              {activeTab === 'planetary' ? (
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
                  <small>Ranked against each planet’s own classical minimum</small>
                </header>
                <div className="shadbala-results__head" aria-hidden="true">
                  <span>Planet</span><span>Strength</span><span>Assessment</span><span />
                </div>
                <div className="shadbala-planet-list">
                  {planetEntries.map(([planet, data]) => {
                    const expanded = expandedPlanet === planet;
                    const benchmark = Math.min(100, Math.max(4, Number(data.required_percent || 0)));
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
                            <span><strong>{formatValue(data.total_rupas)}</strong> Rupas <small>{formatValue(data.required_ratio)}× required · rank {formatValue(data.relative_rank, 0)}</small></span>
                            <i><em style={{ width: `${benchmark}%` }} /></i>
                          </span>
                          <em className={`shadbala-grade shadbala-grade--${requirementClass(data)}`}>{data.classical_status || 'Unrated'}</em>
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
                            <div className="shadbala-standard">
                              <div><span>Classical minimum</span><strong>{formatValue(data.minimum_required_points, 0)} Virupas</strong><small>{formatValue(data.minimum_required_rupas)} Rupas</small></div>
                              <div><span>Requirement reached</span><strong>{formatValue(data.required_percent, 1)}%</strong><small>{formatValue(data.required_ratio)}× minimum</small></div>
                              <div><span>Relative rank</span><strong>#{formatValue(data.relative_rank, 0)}</strong><small>Ranked by required ratio</small></div>
                              <div><span>Ishta Phala</span><strong>{formatValue(data.ishta_phala)}</strong><small>Capacity for agreeable results</small></div>
                              <div><span>Kashta Phala</span><strong>{formatValue(data.kashta_phala)}</strong><small>Capacity for difficult results</small></div>
                            </div>
                            <div className="shadbala-subtables">
                              <section><h4>Sthana Bala components</h4>{STHANA_ROWS.map(([label, key]) => <div key={key}><span>{label}</span><b>{formatValue(data.detailed_breakdown?.sthana_components?.[key])}</b></div>)}</section>
                              <section><h4>Kala Bala components</h4>{KALA_ROWS.map(([label, key]) => <div key={key}><span>{label}</span><b>{formatValue(data.detailed_breakdown?.kala_components?.[key])}</b></div>)}</section>
                            </div>
                          </div>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>

              <ShadbalaWorksheet data={shadbalaData.shadbala} />

              <details className="shadbala-guide">
                <summary>Method, limits and interpretation</summary>
                <div className="shadbala-method-grid">
                  <span><strong>Classical standard</strong><em>Each planet is compared with its own BPHS minimum; 1.00× means the minimum is reached.</em></span>
                  <span><strong>Relative rank</strong><em>Rank is based on the required-strength ratio, not the largest raw total.</em></span>
                  <span><strong>Phala</strong><em>Ishta and Kashta describe agreeable and difficult result-giving capacity; they are not probabilities.</em></span>
                  <span><strong>Scope</strong><em>Strength is not beneficence and must be read with lordship, dignity, placement and aspects.</em></span>
                </div>
                <p>{shadbalaData.validation?.note || 'Shadbala is a classical strength measure, not a health, lifespan or event-probability score.'}</p>
                {shadbalaData.validation ? <p><strong>Validation:</strong> exact rows: {shadbalaData.validation.exact_rows?.join(', ')}; bounded row: {shadbalaData.validation.bounded_rows?.join(', ')}; convention-dependent: {shadbalaData.validation.convention_dependent_rows?.join(', ')}.</p> : null}
              </details>
                </>
              ) : null}

              {activeTab === 'bhava' ? (
                <>
                  <BhavaBalaWorksheet data={shadbalaData.bhava_bala} />
                  <details className="shadbala-guide">
                    <summary>Bhava Bala method and limits</summary>
                    <p>{shadbalaData.validation?.bhava_bala_note || 'Bhava Bala measures a house’s capacity to express its topics; strength is not automatically beneficence.'}</p>
                  </details>
                </>
              ) : null}

              {activeTab === 'supplementary' ? <SupplementaryHouseScore data={shadbalaData.supplementary_house_strength} /> : null}
            </>
          ) : null}
        </div>
      </section>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default ShadbalaModal;
