import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import { houseLords } from '../../utils/planetAnalyzer';
import { getHouseAspects } from '../../utils/grahaDrishti';
import './DeskHouseInsight.css';

const SIGN_ABBR = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'];
const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju',
  Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke', Lagna: 'Lg',
};
const TENANTS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

function formatAsOfDate(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return null;
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function houseOfPlanet(data, lagnaSign) {
  if (typeof data?.house === 'number') return data.house;
  if (typeof data?.sign !== 'number' || typeof lagnaSign !== 'number') return null;
  return ((data.sign - lagnaSign + 12) % 12) + 1;
}

function titleCase(value) {
  return String(value || '—').replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function fixed(value, digits = 2) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(digits) : '—';
}

function ordinal(value) {
  const numberValue = Number(value);
  const mod100 = numberValue % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${numberValue}th`;
  if (numberValue % 10 === 1) return `${numberValue}st`;
  if (numberValue % 10 === 2) return `${numberValue}nd`;
  if (numberValue % 10 === 3) return `${numberValue}rd`;
  return `${numberValue}th`;
}

function strength(points, kind) {
  if (!Number.isFinite(points)) return 'moderate';
  if (kind === 'sav') return points >= 30 ? 'strong' : points <= 25 ? 'weak' : 'moderate';
  return points >= 5 ? 'strong' : points <= 3 ? 'weak' : 'moderate';
}

function buildAshtakavargaSummary(payload, houseNumber, rashiIndex, lord) {
  const houses = payload?.chart_ashtakavarga || {};
  const individuals = payload?.ashtakavarga?.individual_charts || {};
  const savPoints = houses?.[String(houseNumber)]?.bindus;
  if (!Number.isFinite(savPoints)) return null;
  const savValues = Object.values(houses).map((row) => row?.bindus).filter(Number.isFinite);
  const summary = {
    sav: {
      house_points: savPoints,
      classification: strength(savPoints, 'sav'),
      max_points: savValues.length ? Math.max(...savValues) : null,
      min_points: savValues.length ? Math.min(...savValues) : null,
    },
  };
  const entries = Object.entries(individuals?.[lord]?.bindus || {})
    .map(([sign, value]) => [Number(sign), Number(value)])
    .filter(([sign, value]) => Number.isInteger(sign) && Number.isFinite(value));
  const housePoints = entries.find(([sign]) => sign === rashiIndex)?.[1];
  if (!Number.isFinite(housePoints)) return summary;
  const signToHouse = Object.entries(houses).reduce((result, [house, row]) => {
    if (Number.isInteger(row?.sign)) result[row.sign] = Number(house);
    return result;
  }, {});
  const values = entries.map(([, value]) => value);
  const maximum = Math.max(...values);
  const minimum = Math.min(...values);
  summary.lord_bav = {
    planet: lord,
    house_points: housePoints,
    classification: strength(housePoints, 'bav'),
    max_points: maximum,
    min_points: minimum,
    strongest_houses: entries.filter(([, value]) => value === maximum).map(([sign]) => signToHouse[sign]).filter(Number.isInteger),
    weakest_houses: entries.filter(([, value]) => value === minimum).map(([sign]) => signToHouse[sign]).filter(Number.isInteger),
  };
  return summary;
}

function EvidenceList({ title, items, tone }) {
  if (!items?.length) return null;
  return (
    <section className={`desk-hi__section desk-hi__evidence desk-hi__evidence--${tone}`}>
      <h3>{title}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={`${item?.evidence_key || item?.label || title}-${index}`}>{item?.label || item}</li>
        ))}
      </ul>
    </section>
  );
}

function MiniRow({ mark, title, detail, tone = '' }) {
  return (
    <div className={`desk-hi__mini-row ${tone ? `desk-hi__mini-row--${tone}` : ''}`}>
      {mark ? <span className="desk-hi__mini-mark">{mark}</span> : null}
      <div><strong>{title}</strong>{detail ? <span>{detail}</span> : null}</div>
    </div>
  );
}

/** Shared-backend house judgment used by the compact desk and expanded professional view. */
export default function DeskHouseInsight({
  birthData,
  chartData,
  selection,
  asOfDate,
  chartId = 'lagna',
  expanded = false,
  emptyTitle = 'Click a house on D1 / D9 / Dx / Transit',
  emptyHint = 'Lord · occupants · Ashtakavarga · drishti · verdict',
  emptyAction = null,
}) {
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const houseNumber = selection?.houseNumber || null;
  const rashiIndex = selection?.rashiIndex;
  const signName = selection?.signName;
  const activeChartId = selection?.chartId || chartId;

  const local = useMemo(() => {
    if (!houseNumber || !chartData) return null;
    const lagnaSign = chartData.houses?.[0]?.sign
      ?? (typeof chartData.ascendant === 'number'
        ? Math.floor((((chartData.ascendant % 360) + 360) % 360) / 30)
        : 0);
    const sign = typeof rashiIndex === 'number'
      ? rashiIndex
      : (chartData.houses?.[houseNumber - 1]?.sign ?? ((lagnaSign + houseNumber - 1) % 12));
    return {
      sign,
      signAbbr: SIGN_ABBR[sign] || '—',
      lord: houseLords[sign],
      tenants: TENANTS
        .filter((name) => houseOfPlanet(chartData.planets?.[name], lagnaSign) === houseNumber)
        .map((name) => ({ name, ...(chartData.planets?.[name] || {}) })),
      aspects: getHouseAspects(chartData, houseNumber, sign),
    };
  }, [houseNumber, rashiIndex, chartData]);

  useEffect(() => {
    if (!birthData || !houseNumber) {
      setInsight(null);
      setError('');
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError('');
    const transitDate = formatAsOfDate(asOfDate);
    const requests = [apiService.getHouseInsight({ birthData, houseNum: houseNumber, chartId: activeChartId, transitDate })];
    if (activeChartId === 'lagna' || activeChartId === 'transit') {
      requests.push(apiService.getChartAshtakavarga({ birthData, chartType: activeChartId, transitDate }).catch(() => null));
    }
    Promise.all(requests).then(([data, ashtakavarga]) => {
      if (!cancelled) {
        const canonicalAv = buildAshtakavargaSummary(
          ashtakavarga,
          houseNumber,
          rashiIndex,
          data?.house_lord || local?.lord,
        );
        if (canonicalAv) {
          data.raw = { ...(data.raw || {}), ashtakavarga: { ...canonicalAv, givers: data?.sav_givers?.givers || [] } };
        }
        setInsight(data);
      }
    }).catch((err) => {
      if (!cancelled) {
        setInsight(null);
        setError(err?.response?.data?.detail || err.message || 'Failed');
      }
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [birthData, houseNumber, activeChartId, asOfDate, rashiIndex, local?.lord]);

  if (!houseNumber) {
    return <div className="desk-hi desk-hi--empty"><p>{emptyTitle}</p><span>{emptyHint}</span>{emptyAction}</div>;
  }

  const av = insight?.raw?.ashtakavarga;
  const lord = insight?.lord_worksheet;
  const support = insight?.support_factors || [];
  const stress = insight?.stress_factors || [];
  const activation = insight?.activation_factors || [];

  if (!expanded) {
    return (
      <div className="desk-hi" aria-label={`House ${houseNumber} insight`}>
        <header className="desk-hi__head">
          <strong className="desk-hi__badge">H{houseNumber}</strong>
          <div className="desk-hi__titles"><h3>{signName || local?.signAbbr || '—'}</h3><span>{activeChartId === 'lagna' ? 'D1' : activeChartId}</span></div>
          {insight?.verdict ? <em className={`desk-hi__verdict desk-hi__verdict--${insight.verdict.key || 'quiet'}`}>{insight.verdict.label}</em> : null}
        </header>
        <div className="desk-hi__compact-facts">
          <span>Lord <strong>{insight?.house_lord || local?.lord || '—'}</strong></span>
          <span>In <strong>{lord?.house ? `H${lord.house}` : '—'}</strong></span>
          <span>Occupants <strong>{local?.tenants?.length ? local.tenants.map((row) => PLANET_ABBR[row.name]).join(' ') : '—'}</strong></span>
        </div>
        {av ? <div className="desk-hi__av"><span>SAV <strong>{av.sav?.house_points ?? '—'}</strong></span><span>{av.lord_bav?.planet || 'Lord'} BAV <strong>{av.lord_bav?.house_points ?? '—'}</strong></span></div> : null}
        {loading ? <p className="desk-hi__status">Loading…</p> : null}
        {error ? <p className="desk-hi__status desk-hi__status--err">{error}</p> : null}
        {insight?.interpretation ? <p className="desk-hi__read">{insight.interpretation}</p> : null}
        {(support.length || stress.length) ? <div className="desk-hi__factor-counts"><span>{support.length} supporting factors</span><span>{stress.length} pressure factors</span></div> : null}
        {insight?.timing_verdict ? <p className="desk-hi__timing">Current activation · {insight.timing_verdict.label}</p> : null}
      </div>
    );
  }

  const lordCombustion = lord?.combustion;
  const timingRows = insight?.timing?.windows || [];
  const currentTransits = insight?.timing?.current_transits || [];
  const argalaSupport = insight?.argala?.support || [];
  const argalaObstruction = insight?.argala?.obstruction || [];
  const points = [...(insight?.points_in_house || []), ...(insight?.chara_karakas_here || [])];
  const givers = insight?.sav_givers?.givers || av?.givers || [];

  return (
    <div className="desk-hi desk-hi--expanded" aria-label={`House ${houseNumber} professional insight`}>
      <header className="desk-hi__hero">
        <div className="desk-hi__hero-badge">H{houseNumber}</div>
        <div>
          <p>House insight · {activeChartId === 'lagna' ? 'D1 natal chart' : insight?.chart_name || activeChartId}</p>
          <h2>{ordinal(houseNumber)} House</h2>
          {insight?.significance ? <div className="desk-hi__hero-themes">{insight.significance.replace(/,\s*/g, ' · ')}</div> : null}
          {(insight?.sign_body_parts?.length || insight?.body_parts?.length) ? (
            <div className="desk-hi__hero-body">
              <strong>{insight?.sign_name || signName || 'Sign'} body focus</strong>
              <span>{(insight.sign_body_parts || insight.body_parts).map(titleCase).join(' · ')}</span>
            </div>
          ) : null}
          {insight?.house_body_parts?.length ? (
            <div className="desk-hi__hero-body desk-hi__hero-body--secondary">
              <strong>Bhava body area</strong>
              <span>{insight.house_body_parts.map(titleCase).join(' · ')}</span>
            </div>
          ) : null}
          <span>{insight?.sign_name || signName || '—'} · ruled by {insight?.house_lord || local?.lord || '—'}</span>
        </div>
      </header>
      {loading ? <p className="desk-hi__status desk-hi__status--large">Reading the house from the shared chart engine…</p> : null}
      {error ? <p className="desk-hi__status desk-hi__status--err desk-hi__status--large">{error}</p> : null}
      {insight ? (
        <>
          <div className="desk-hi__top-grid">
            <section className="desk-hi__condition">
              <div className="desk-hi__section-head"><h3>Natal house condition</h3><em className={`desk-hi__verdict desk-hi__verdict--${insight.verdict?.key || 'quiet'}`}>{insight.verdict?.label}</em></div>
              <p>{insight.interpretation}</p>
              <div className="desk-hi__counts"><span><b>{insight?.natal_assessment?.support_count ?? support.length}</b> supporting {Number(insight?.natal_assessment?.support_count ?? support.length) === 1 ? 'testimony' : 'testimonies'}</span><span><b>{insight?.natal_assessment?.pressure_count ?? stress.length}</b> pressure {Number(insight?.natal_assessment?.pressure_count ?? stress.length) === 1 ? 'testimony' : 'testimonies'}</span></div>
            </section>
            <section className="desk-hi__section desk-hi__activation">
              <div className="desk-hi__section-head"><h3>Current activation</h3><em className={`desk-hi__verdict desk-hi__verdict--${insight.timing_verdict?.key || 'quiet'}`}>{insight.timing_verdict?.label}</em></div>
              <p>{activation.length ? 'Dasha or transit factors are currently emphasizing this natal house.' : 'No distinct Dasha or transit emphasis is active for this house.'}</p>
              {activation.length ? <ul>{activation.map((row, index) => <li key={`${row.label}-${index}`}>{row.label}</li>)}</ul> : null}
            </section>
          </div>

          <div className="desk-hi__evidence-grid">
            <EvidenceList title="What supports this house" items={support} tone="good" />
            <EvidenceList title="What adds pressure" items={stress} tone="warn" />
          </div>

          <div className="desk-hi__detail-grid">
            <section className="desk-hi__section">
              <h3>Occupant planets</h3>
              {local?.tenants?.length ? local.tenants.map((planet) => {
                const condition = insight.planet_conditions?.[planet.name];
                const combustion = condition?.combustion;
                const roles = insight.raw?.occupant_roles?.[planet.name] || [];
                return <MiniRow key={planet.name} mark={PLANET_ABBR[planet.name]} title={planet.name} detail={[
                  planet.retrograde && !['Rahu', 'Ketu'].includes(planet.name) ? 'Retrograde' : null,
                  combustion?.is_combust ? `${combustion.source_chart === 'D1' && activeChartId !== 'lagna' ? 'Natal combustion (D1)' : 'Combust'} · ${fixed(combustion.angular_distance)}° from Sun` : null,
                  condition?.neecha_bhanga ? 'Neecha Bhanga' : null,
                  ...roles,
                ].filter(Boolean).join(' · ') || 'Occupies this house'} />;
              }) : <p className="desk-hi__muted">No planets occupy this house.</p>}
            </section>

            <section className="desk-hi__section">
              <h3>Graha drishti</h3>
              {local?.aspects?.length ? local.aspects.map((row, index) => <MiniRow key={`${row.planetName}-${index}`} mark="◉" title={`${row.planetName}${row.planetHouse ? ` · H${row.planetHouse}` : ''}`} detail={`${row.aspectKinds} aspect`} />) : <p className="desk-hi__muted">No graha drishti from other houses.</p>}
            </section>

            {lord ? (
              <section className="desk-hi__section desk-hi__lord">
                <div className="desk-hi__section-head"><h3>House lord</h3><strong>{lord.planet}</strong></div>
                <p>{lord.sign_name || '—'} · H{lord.house || '—'}{lord.nakshatra ? ` · ${lord.nakshatra}` : ''}</p>
                <div className="desk-hi__tags">
                  {lord.dignity ? <span>{titleCase(lord.dignity)}</span> : null}<span>{lord.retrograde ? 'Retrograde' : 'Direct'}</span>
                  {lord.combust ? <span className="is-warn">{lordCombustion?.source_chart === 'D1' && activeChartId !== 'lagna' ? 'Natal combustion (D1)' : 'Combust'}</span> : null}
                  {lord.neecha_bhanga ? <span className="is-good">Neecha Bhanga</span> : null}
                  {lord.meets_minimum != null ? <span className={lord.meets_minimum ? 'is-good' : 'is-warn'}>Shadbala {lord.meets_minimum ? 'above' : 'below'} minimum</span> : null}
                </div>
                {lord.combust && lordCombustion?.angular_distance != null ? <p className="desk-hi__note">{fixed(lordCombustion.angular_distance)}° from Sun · {fixed(lordCombustion.threshold, 0)}° limit · {titleCase(lordCombustion.motion)} · calculated from {lordCombustion.source_chart || 'D1'}</p> : null}
                {lord.shadbala_rupas != null ? <div className="desk-hi__stat"><span>Shadbala</span><strong>{lord.shadbala_rupas} / {lord.required_rupas ?? '—'} rupas</strong></div> : null}
                {lord.neecha_bhanga ? <div className="desk-hi__callout"><strong>Neecha Bhanga</strong><span>{lord.planet}'s debilitation is classically cancelled or mitigated.</span><small>{lord.neecha_bhanga_source?.reference_label || 'Phaladeepika 7.26–30'}</small></div> : null}
                {lord.other_lordships?.length ? <p className="desk-hi__note">Also rules H{lord.other_lordships.join(', H')}</p> : null}
              </section>
            ) : null}

            {av?.sav ? (
              <section className="desk-hi__section desk-hi__ashtakavarga">
                <h3>Ashtakavarga</h3>
                <div className="desk-hi__av-cards"><div><span>SAV</span><strong>{av.sav.house_points ?? '—'}</strong><small>{titleCase(av.sav.classification)}</small></div>{av.lord_bav ? <div><span>{av.lord_bav.planet} BAV</span><strong>{av.lord_bav.house_points ?? '—'}</strong><small>{titleCase(av.lord_bav.classification)}</small></div> : null}</div>
                <p className="desk-hi__muted">SAV shows the house's total support. BAV shows how strongly the house lord contributes to this house.</p>
                {av.lord_bav?.strongest_houses?.length ? <p><b>Strongest {av.lord_bav.planet} BAV houses:</b> {av.lord_bav.strongest_houses.join(', ')}</p> : null}
                {av.lord_bav?.weakest_houses?.length ? <p><b>Weakest {av.lord_bav.planet} BAV houses:</b> {av.lord_bav.weakest_houses.join(', ')}</p> : null}
                {givers.length ? <div className="desk-hi__giver-row">{givers.map((row) => <span key={row.planet}>{PLANET_ABBR[row.planet] || row.planet} <b>{row.bindus}</b></span>)}</div> : null}
              </section>
            ) : null}

            {(argalaSupport.length || argalaObstruction.length) ? (
              <section className="desk-hi__section">
                <div className="desk-hi__section-head"><h3>Argala</h3><em className={`desk-hi__verdict desk-hi__verdict--${insight.argala?.grade === 'Support' ? 'strong' : insight.argala?.grade === 'Obstruction' ? 'mixed' : 'quiet'}`}>{insight.argala?.grade}</em></div>
                {argalaSupport.map((row) => <MiniRow key={`a-${row.planet}-${row.from_house}`} mark="+" title={row.planet} detail={`Support from H${row.from_house}${row.label ? ` · ${row.label}` : ''}`} tone="good" />)}
                {argalaObstruction.map((row) => <MiniRow key={`v-${row.planet}-${row.from_house}`} mark="−" title={row.planet} detail={`Virodha from H${row.from_house}${row.label ? ` · ${row.label}` : ''}`} tone="warn" />)}
              </section>
            ) : null}

            {points.length ? <section className="desk-hi__section"><h3>Points in this house</h3>{points.map((row, index) => <MiniRow key={`${row.key || row.karaka}-${index}`} mark={row.abbr || String(row.label || '').slice(0, 1)} title={row.label || row.planet} detail={[row.title, row.sign_name, row.detail].filter(Boolean).join(' · ')} />)}</section> : null}
          </div>

          {(timingRows.length || currentTransits.length || insight.natural_karakas?.length || insight.related_varga) ? (
            <section className="desk-hi__section desk-hi__timing-card">
              <h3>Timing, Karaka and related Varga</h3>
              {currentTransits.length ? <MiniRow mark="Now" title="Current transits through this house" detail={currentTransits.join(', ')} /> : null}
              {timingRows.map((row, index) => <MiniRow key={`${row.mahadasha}-${row.antardasha}-${row.start}-${index}`} mark={row.current ? 'Now' : 'Next'} title={[row.mahadasha, row.antardasha].filter(Boolean).join(' / ')} detail={[row.start && row.end ? `${row.start} – ${row.end}` : row.start || row.end, row.why].filter(Boolean).join(' · ')} />)}
              {insight.natural_karakas?.map((row) => <MiniRow key={row.planet} mark="★" title={`${row.planet} · natural Karaka`} detail={[row.sign_name, row.house != null ? `H${row.house}` : null].filter(Boolean).join(' · ')} />)}
              {insight.related_varga ? <MiniRow mark="Dx" title={insight.related_varga.name} detail={[insight.related_varga.sign_name, insight.related_varga.lord ? `Lord ${insight.related_varga.lord}` : null, insight.related_varga.lord_house != null ? `in H${insight.related_varga.lord_house}` : null, insight.related_varga.occupants?.length ? `Occupants: ${insight.related_varga.occupants.join(', ')}` : 'Empty'].filter(Boolean).join(' · ')} /> : null}
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
