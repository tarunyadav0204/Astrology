import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import { getPlanetDignity } from '../../utils/planetAnalyzer';
import './DeskPositionsTable.css';

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

const SIGN_LORDS = [
  'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
  'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter',
];

const PLANET_ORDER = [
  'Ascendant', 'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn',
  'Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna',
];

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];

const KARAKA_ABBR = {
  Atmakaraka: 'AK',
  Amatyakaraka: 'AmK',
  Bhratrukaraka: 'BK',
  Matrukaraka: 'MK',
  Pitrikaraka: 'PiK',
  Putrakaraka: 'PK',
  Gnatikaraka: 'GK',
  Darakaraka: 'DK',
};

function normLon(lon) {
  return ((Number(lon) % 360) + 360) % 360;
}

function nakshatraOf(lon) {
  return NAKSHATRAS[Math.floor(normLon(lon) / 13.333333)] || '—';
}

function padaOf(lon) {
  return Math.floor((normLon(lon) % 13.333333) / 3.333333) + 1;
}

function fmtDeg(deg) {
  const d = Math.floor(deg);
  const m = Math.floor((deg - d) * 60);
  return `${d}°${String(m).padStart(2, '0')}'`;
}

function houseOf(sign, lagnaSign) {
  if (typeof sign !== 'number' || typeof lagnaSign !== 'number') return '—';
  return ((sign - lagnaSign + 12) % 12) + 1;
}

function dignityOf(name, sign, degree) {
  const label = getPlanetDignity(name, sign, degree);
  if (label === 'Exalted') return { key: 'ex', label };
  if (label === 'Debilitated') return { key: 'db', label };
  if (label === 'Moolatrikona') return { key: 'mt', label };
  if (label === 'Own') return { key: 'own', label };
  return null;
}

/**
 * Dense planetary positions table for the Parashari desk.
 */
export default function DeskPositionsTable({ chartData, birthData }) {
  const [karakaByPlanet, setKarakaByPlanet] = useState({});

  useEffect(() => {
    if (!birthData?.date || !chartData?.planets) {
      setKarakaByPlanet({});
      return undefined;
    }
    let cancelled = false;
    apiService.calculateCharaKarakas(chartData, birthData)
      .then((data) => {
        if (cancelled) return;
        const rows = data?.chara_karakas && typeof data.chara_karakas === 'object'
          ? data.chara_karakas
          : {};
        const map = {};
        Object.entries(rows).forEach(([karaka, info]) => {
          if (info?.planet) map[info.planet] = KARAKA_ABBR[karaka] || karaka;
        });
        setKarakaByPlanet(map);
      })
      .catch(() => {
        if (!cancelled) setKarakaByPlanet({});
      });
    return () => {
      cancelled = true;
    };
  }, [birthData, chartData]);

  const rows = useMemo(() => {
    if (!chartData?.planets) return [];
    const lagnaSign = chartData.houses?.[0]?.sign
      ?? (typeof chartData.ascendant === 'number' ? Math.floor(normLon(chartData.ascendant) / 30) : 0);

    const out = [];
    const ascLon = typeof chartData.ascendant === 'number'
      ? chartData.ascendant
      : chartData.houses?.[0]?.longitude;
    if (typeof ascLon === 'number') {
      const sign = Math.floor(normLon(ascLon) / 30) % 12;
      out.push({
        name: 'Lagna',
        abbr: 'Asc',
        sign,
        signName: SIGN_NAMES[sign],
        lord: SIGN_LORDS[sign],
        house: 1,
        degree: fmtDeg(normLon(ascLon) % 30),
        nakshatra: nakshatraOf(ascLon),
        pada: padaOf(ascLon),
        retro: false,
        dignity: null,
      });
    }

    PLANET_ORDER.forEach((name) => {
      if (name === 'Ascendant') return;
      const data = chartData.planets[name];
      if (!data || typeof data.sign !== 'number') return;
      const lon = typeof data.longitude === 'number' ? data.longitude : (data.sign * 30 + (data.degree || 0));
      const degree = typeof data.degree === 'number' ? data.degree : (normLon(lon) % 30);
      const dig = dignityOf(name, data.sign, degree);
      out.push({
        name,
        abbr: name === 'InduLagna' ? 'IL' : name.slice(0, 2),
        sign: data.sign,
        signName: SIGN_NAMES[data.sign] || '—',
        lord: SIGN_LORDS[data.sign] || '—',
        house: houseOf(data.sign, lagnaSign),
        degree: fmtDeg(typeof data.degree === 'number' ? data.degree : (normLon(lon) % 30)),
        nakshatra: nakshatraOf(lon),
        pada: padaOf(lon),
        retro: !!data.retrograde && name !== 'Rahu' && name !== 'Ketu',
        dignity: dig,
      });
    });
    return out;
  }, [chartData]);

  if (!rows.length) {
    return <div className="desk-pos desk-pos--empty">No planetary data</div>;
  }

  return (
    <div className="desk-pos" aria-label="Planetary positions">
      <table className="desk-pos__table">
        <thead>
          <tr>
            <th>Pl</th>
            <th>CK</th>
            <th>Sign</th>
            <th>H</th>
            <th>Deg</th>
            <th>Nak · Pda</th>
            <th>Lord</th>
            <th>Note</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name} className={row.dignity ? `is-${row.dignity.key}` : undefined}>
              <td>
                <strong>{row.abbr}</strong>
                {row.retro ? <i title="Retrograde">R</i> : null}
              </td>
              <td className="desk-pos__ck">{karakaByPlanet[row.name] || '—'}</td>
              <td>{row.signName.slice(0, 3)}</td>
              <td>{row.house}</td>
              <td>{row.degree}</td>
              <td>{row.nakshatra.slice(0, 6)} · {row.pada}</td>
              <td>{String(row.lord).slice(0, 2)}</td>
              <td>{row.dignity?.label || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
