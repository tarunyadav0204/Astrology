import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import { getPlanetDignity, houseLords } from '../../utils/planetAnalyzer';
import { getHouseAspects } from '../../utils/grahaDrishti';
import './DeskHouseInsight.css';

const SIGN_ABBR = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'];
const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};
const DIG_SHORT = { Exalted: 'Ex', Debilitated: 'Db', Own: 'Own', Neutral: '—' };
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

/**
 * Docked house judgment: lord · seat · dig · tenants · AV · drishti · verdict.
 * Fed by chart house clicks on the Parashari desk.
 */
export default function DeskHouseInsight({
  birthData,
  chartData,
  selection,
  asOfDate,
  chartId = 'lagna',
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
    const lord = houseLords[sign];
    const lordData = chartData.planets?.[lord];
    const lordHouse = houseOfPlanet(lordData, lagnaSign);
    const dig = lordData && typeof lordData.sign === 'number'
      ? getPlanetDignity(lord, lordData.sign)
      : 'Neutral';
    const tenants = TENANTS.filter((name) => {
      const h = houseOfPlanet(chartData.planets?.[name], lagnaSign);
      return h === houseNumber;
    }).map((name) => {
      const retro = chartData.planets[name]?.retrograde && name !== 'Rahu' && name !== 'Ketu';
      return `${PLANET_ABBR[name] || name}${retro ? '(R)' : ''}`;
    });
    const aspects = getHouseAspects(chartData, houseNumber, sign);
    return {
      sign,
      signAbbr: SIGN_ABBR[sign] || '—',
      lord,
      lordAbbr: PLANET_ABBR[lord] || lord,
      lordHouse,
      dig,
      digShort: DIG_SHORT[dig] || '—',
      tenants,
      aspects,
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
    apiService
      .getHouseInsight({
        birthData,
        houseNum: houseNumber,
        chartId: activeChartId,
        transitDate: formatAsOfDate(asOfDate),
      })
      .then((data) => {
        if (!cancelled) setInsight(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setInsight(null);
          setError(err?.response?.data?.detail || err.message || 'Failed');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [birthData, houseNumber, activeChartId, asOfDate]);

  if (!houseNumber) {
    return (
      <div className="desk-hi desk-hi--empty">
        <p>Click a house on D1 / D9 / Dx / Transit</p>
        <span>Lord · tenants · AV · drishti · verdict for that bhāva</span>
      </div>
    );
  }

  const av = insight?.raw?.ashtakavarga;
  const support = (insight?.support_factors || []).slice(0, 3);
  const stress = (insight?.stress_factors || []).slice(0, 3);

  return (
    <div className="desk-hi" aria-label={`House ${houseNumber} insight`}>
      <header className="desk-hi__head">
        <strong className="desk-hi__badge">H{houseNumber}</strong>
        <div className="desk-hi__titles">
          <h3>{signName || local?.signAbbr || '—'}</h3>
          <span>{activeChartId === 'lagna' ? 'D1' : activeChartId}</span>
        </div>
        {insight?.verdict ? (
          <em className={`desk-hi__verdict desk-hi__verdict--${insight.verdict.key || 'quiet'}`}>
            {insight.verdict.label}
          </em>
        ) : null}
      </header>

      {local ? (
        <table className="desk-hi__table" aria-label="House map">
          <thead>
            <tr>
              <th>Sign</th>
              <th>Lord</th>
              <th>In</th>
              <th>Dig</th>
              <th>Tenants</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{local.signAbbr}</td>
              <td>{local.lordAbbr}</td>
              <td>{local.lordHouse != null ? `H${local.lordHouse}` : '—'}</td>
              <td title={local.dig}>{local.digShort}</td>
              <td className="desk-hi__tenants">{local.tenants.length ? local.tenants.join(' ') : '—'}</td>
            </tr>
          </tbody>
        </table>
      ) : null}

      {av ? (
        <div className="desk-hi__av">
          <span title="Sarvashtakavarga">
            SAV <strong>{av.sav?.house_points ?? '—'}</strong>
            {av.sav?.classification ? <i>{av.sav.classification}</i> : null}
          </span>
          <span title="Lord Bhinna Ashtakavarga">
            BAV {av.lord_bav?.planet ? PLANET_ABBR[av.lord_bav.planet] || av.lord_bav.planet : ''}
            {' '}
            <strong>{av.lord_bav?.house_points ?? '—'}</strong>
            {av.lord_bav?.classification ? <i>{av.lord_bav.classification}</i> : null}
          </span>
        </div>
      ) : null}

      {local?.aspects?.length ? (
        <div className="desk-hi__aspects">
          <em>Drishti</em>
          <div className="desk-hi__chips">
            {local.aspects.map((a) => (
              <span key={`${a.planetName}-${a.aspectKinds}`} title={`${a.planetName} · ${a.aspectKinds}`}>
                {PLANET_ABBR[a.planetName] || a.planetName}
                {a.aspectKinds ? ` ${a.aspectKinds.replace(/th/g, '')}` : ''}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {loading ? <p className="desk-hi__status">Loading…</p> : null}
      {error ? <p className="desk-hi__status desk-hi__status--err">{error}</p> : null}

      {insight?.interpretation ? (
        <p className="desk-hi__read">{insight.interpretation}</p>
      ) : null}

      {(support.length || stress.length) ? (
        <div className="desk-hi__factors">
          {support.map((f) => (
            <span key={`s-${f.label}`} className="is-good">{f.label}</span>
          ))}
          {stress.map((f) => (
            <span key={`w-${f.label}`} className="is-warn">{f.label}</span>
          ))}
        </div>
      ) : null}

      {insight?.timing_verdict ? (
        <p className="desk-hi__timing" title="Relative to as-of date">
          Timing · {insight.timing_verdict.label}
        </p>
      ) : null}
    </div>
  );
}
