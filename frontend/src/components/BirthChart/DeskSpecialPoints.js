import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskSpecialPoints.css';

const SIGN_ABBR = {
  Aries: 'Ar', Taurus: 'Ta', Gemini: 'Ge', Cancer: 'Cn',
  Leo: 'Le', Virgo: 'Vi', Libra: 'Li', Scorpio: 'Sc',
  Sagittarius: 'Sg', Capricorn: 'Cp', Aquarius: 'Aq', Pisces: 'Pi',
};

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

function signAbbr(name) {
  if (!name && name !== 0) return '—';
  if (typeof name === 'number') return signAbbr(SIGN_NAMES[name]);
  return SIGN_ABBR[name] || String(name).slice(0, 2);
}

function planetAbbr(name) {
  if (!name) return '—';
  return PLANET_ABBR[name] || String(name).slice(0, 2);
}

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];

function nakshatraOfLon(lon) {
  if (typeof lon !== 'number' || Number.isNaN(lon)) return null;
  const n = ((lon % 360) + 360) % 360;
  return NAKSHATRAS[Math.floor(n / 13.333333)] || null;
}

function nakshatraShort(name) {
  if (!name) return null;
  const first = String(name).split(/\s+/)[0];
  return first.length > 7 ? first.slice(0, 6) : first;
}

function planetNakshatra(chartData, planetName) {
  const data = chartData?.planets?.[planetName];
  if (!data) return null;
  if (typeof data.nakshatra === 'string' && data.nakshatra.trim()) return data.nakshatra.trim();
  if (typeof data.nakshatra_name === 'string' && data.nakshatra_name.trim()) {
    return data.nakshatra_name.trim();
  }
  return nakshatraOfLon(data.longitude);
}

function fmtPoint(point) {
  if (!point) return '—';
  const deg = point.degree != null ? `${Number(point.degree).toFixed(1)}°` : '';
  return `${signAbbr(point.sign_name || point.sign)} ${deg}`.trim();
}

/**
 * Compact special-points readout for the Parashari desk.
 * variant: "strip" (toolbar) | "panel" (fills leftover dasha width)
 */
const DeskSpecialPoints = ({ birthData, chartData, variant = 'strip' }) => {
  const [yogi, setYogi] = useState(null);
  const [badhaka, setBadhaka] = useState(null);
  const [sniper, setSniper] = useState(null);
  const [pushkara, setPushkara] = useState(null);
  const [gandanta, setGandanta] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!birthData?.date || !chartData) {
      setYogi(null);
      setBadhaka(null);
      setSniper(null);
      setPushkara(null);
      setGandanta(null);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const [yogiRes, badhakaRes, sniperRes, d9Res, ganRes] = await Promise.all([
          apiService.calculateYogi(birthData),
          apiService.calculateBadhakaMaraka(chartData).catch(() => null),
          apiService.calculateSniperPoints(chartData).catch(() => null),
          apiService.calculateDivisionalChart(birthData, 9).catch(() => null),
          apiService.calculateGandantaAnalysis(chartData).catch(() => null),
        ]);
        let push = null;
        if (d9Res?.divisional_chart) {
          push = await apiService.calculatePushkaraAnalysis(chartData, d9Res.divisional_chart).catch(() => null);
        }
        if (cancelled) return;
        setYogi(yogiRes);
        setBadhaka(badhakaRes);
        setSniper(sniperRes?.sniper_points || sniperRes || null);
        setPushkara(push?.pushkara_analysis || push || null);
        setGandanta(ganRes?.gandanta_analysis || ganRes?.data?.gandanta_analysis || ganRes || null);
        setError(null);
      } catch (err) {
        if (!cancelled) setError(err?.message || 'Failed to load special points');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [birthData, chartData]);

  const items = useMemo(() => {
    const list = [];
    if (yogi?.yogi) list.push({ key: 'yogi', label: 'Yogi', value: fmtPoint(yogi.yogi), tone: 'yogi' });
    if (yogi?.avayogi) list.push({ key: 'avayogi', label: 'Avayogi', value: fmtPoint(yogi.avayogi), tone: 'ava' });
    if (yogi?.dagdha_rashi) list.push({ key: 'dagdha', label: 'Dagdha', value: fmtPoint(yogi.dagdha_rashi), tone: 'dagdha' });
    if (yogi?.tithi_shunya_rashi) {
      list.push({ key: 'shunya', label: 'Tithi Śūnya', value: fmtPoint(yogi.tithi_shunya_rashi), tone: 'shunya' });
    }

    const analysis = badhaka?.chart_analysis;
    if (analysis?.badhaka) {
      list.push({
        key: 'badhaka',
        label: 'Badhaka',
        value: `H${analysis.badhaka.house} ${planetAbbr(analysis.badhaka.lord)}`,
        tone: 'badhaka',
        title: analysis.badhaka.effects?.description || undefined,
      });
    }
    if (analysis?.maraka?.lords?.length) {
      const lords = analysis.maraka.lords.map((l) => {
        if (typeof l === 'string') return planetAbbr(l);
        return planetAbbr(l.planet || l.lord || l.name);
      });
      list.push({
        key: 'maraka',
        label: 'Maraka',
        value: lords.filter(Boolean).join(' · '),
        tone: 'maraka',
      });
    }
    if (analysis?.rasi_type) {
      list.push({ key: 'rasi', label: 'Rasi', value: analysis.rasi_type, tone: 'rasi' });
    }

    const bb = sniper?.bhrigu_bindu;
    if (bb && !bb.error) {
      list.push({
        key: 'bb',
        label: 'Bhrigu',
        value: fmtPoint(bb) || `${signAbbr(bb.sign)} ${bb.degree != null ? `${Number(bb.degree).toFixed(1)}°` : ''}`.trim(),
        tone: 'bb',
        title: bb.significance || 'Bhrigu Bindu',
      });
    }
    const mb = sniper?.mrityu_bhaga;
    if (mb?.afflicted_points?.length) {
      const names = mb.afflicted_points
        .map((p) => planetAbbr(p.planet || p.point || p.name))
        .filter(Boolean)
        .slice(0, 3);
      if (names.length) {
        list.push({
          key: 'mb',
          label: 'Mṛtyu',
          value: names.join(' · '),
          tone: 'mb',
          title: 'Mrityu Bhaga afflictions',
        });
      }
    }

    const pushPlanets = pushkara?.pushkara_planets || pushkara?.planets_in_pushkara || [];
    if (pushkara?.has_pushkara || pushPlanets.length) {
      const names = (Array.isArray(pushPlanets) ? pushPlanets : [])
        .map((p) => planetAbbr(typeof p === 'string' ? p : (p.planet || p.name)))
        .filter(Boolean)
        .slice(0, 4);
      list.push({
        key: 'push',
        label: 'Pushkara',
        value: names.length ? names.join(' · ') : 'Yes',
        tone: 'push',
        title: 'Planets in Pushkara navamsa/degrees',
      });
    }

    const ganRows = gandanta?.planets_in_gandanta || gandanta?.planetary_gandanta || [];
    const ganEntries = ganRows
      .map((row) => {
        const name = typeof row.planet === 'string' ? row.planet : (row.planet?.name || row.name);
        const info = row.gandanta_info || row;
        if (!name || !(info?.is_gandanta || row.is_gandanta)) return null;
        const nak = planetNakshatra(chartData, name);
        return {
          abbr: planetAbbr(name),
          name,
          nak,
          info,
          label: [planetAbbr(name), nakshatraShort(nak)].filter(Boolean).join(' '),
        };
      })
      .filter(Boolean)
      .slice(0, 5);
    const lagnaGan = gandanta?.lagna_gandanta?.is_gandanta
      ? (gandanta.lagna_gandanta.gandanta_info || gandanta.lagna_gandanta)
      : null;
    if (ganEntries.length || lagnaGan) {
      const valueParts = [];
      let lagnaNak = null;
      if (lagnaGan) {
        const ascLon = typeof chartData?.ascendant === 'number'
          ? chartData.ascendant
          : chartData?.houses?.[0]?.longitude;
        lagnaNak = nakshatraOfLon(ascLon);
        valueParts.push(['Asc', nakshatraShort(lagnaNak)].filter(Boolean).join(' '));
      }
      valueParts.push(...ganEntries.map((row) => row.label));
      const titles = ganEntries.map((row) => ([
        row.name,
        row.nak ? `nakṣatra ${row.nak}` : null,
        row.info.gandanta_name || 'Gandanta',
        row.info.intensity || null,
        row.info.distance_from_junction != null ? `${row.info.distance_from_junction}°` : null,
      ].filter(Boolean).join(' · ')));
      if (lagnaGan) {
        titles.unshift([
          'Lagna',
          lagnaNak ? `nakṣatra ${lagnaNak}` : null,
          lagnaGan.gandanta_name || 'Gandanta',
          lagnaGan.intensity || null,
        ].filter(Boolean).join(' · '));
      }
      list.push({
        key: 'gandanta',
        label: 'Gandanta',
        value: valueParts.join(' · ') || 'Yes',
        tone: 'gandanta',
        title: titles.length
          ? `Gandamoola (Gandanta): ${titles.join('; ')}`
          : 'Gandamoola (Gandanta) junction affliction',
      });
    }

    return list;
  }, [yogi, badhaka, sniper, pushkara, gandanta, chartData]);

  if (error) {
    return <div className={`desk-sp desk-sp--${variant} desk-sp--error`}>{error}</div>;
  }

  if (!items.length) {
    return (
      <div className={`desk-sp desk-sp--${variant} desk-sp--empty`}>
        {variant === 'panel' ? 'Loading special points…' : null}
      </div>
    );
  }

  if (variant === 'panel') {
    return (
      <aside className="desk-sp desk-sp--panel" aria-label="Special points">
        <header className="desk-sp__head">
          <span>SP</span>
          <strong>Special points</strong>
        </header>
        <ul className="desk-sp__list">
          {items.map((item) => (
            <li key={item.key} className={`desk-sp__item desk-sp__item--${item.tone}`} title={item.title}>
              <em>{item.label}</em>
              <strong>{item.value}</strong>
            </li>
          ))}
        </ul>
      </aside>
    );
  }

  return (
    <div className="desk-sp desk-sp--strip" aria-label="Special points">
      <span className="desk-sp__strip-label">Points</span>
      <div className="desk-sp__chips">
        {items.map((item) => (
          <span
            key={item.key}
            className={`desk-sp__chip desk-sp__chip--${item.tone}`}
            title={item.title || `${item.label}: ${item.value}`}
          >
            <em>{item.label}</em>
            <strong>{item.value}</strong>
          </span>
        ))}
      </div>
    </div>
  );
};

export default DeskSpecialPoints;
