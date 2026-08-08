import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import { getCombustionConditions, getPlanetDignity } from '../../utils/planetAnalyzer';
import './DeskConditionStrip.css';

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
const ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};
const WAR_PLANETS = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];

function normLon(lon) {
  return ((Number(lon) % 360) + 360) % 360;
}

function nakshatraOf(lonOrName) {
  if (typeof lonOrName === 'string' && lonOrName.trim()) return lonOrName.trim();
  if (typeof lonOrName !== 'number' || Number.isNaN(lonOrName)) return null;
  return NAKSHATRAS[Math.floor(normLon(lonOrName) / 13.333333)] || null;
}

function nakshatraShort(name) {
  if (!name) return null;
  // Keep first word for compound names (Purva Phalguni → Purva)
  const first = String(name).split(/\s+/)[0];
  return first.length > 7 ? first.slice(0, 6) : first;
}

function planetNakshatra(planetData, fallbackLon) {
  if (!planetData && typeof fallbackLon !== 'number') return null;
  return nakshatraOf(
    planetData?.nakshatra
    || planetData?.nakshatra_name
    || (typeof planetData?.longitude === 'number' ? planetData.longitude : fallbackLon)
  );
}

function baladiShort(degree, sign) {
  if (typeof degree !== 'number' || typeof sign !== 'number') return null;
  const odd = (sign + 1) % 2 !== 0;
  if (degree < 6) return odd ? 'Bal' : 'Mrit';
  if (degree < 12) return odd ? 'Kumar' : 'Vriddha';
  if (degree < 18) return 'Yuva';
  if (degree < 24) return odd ? 'Vriddha' : 'Kumar';
  return odd ? 'Mrit' : 'Bal';
}

function angDist(a, b) {
  let d = Math.abs(Number(a) - Number(b));
  if (d > 180) d = 360 - d;
  return d;
}

function findWars(planets) {
  const wars = [];
  for (let i = 0; i < WAR_PLANETS.length; i += 1) {
    for (let j = i + 1; j < WAR_PLANETS.length; j += 1) {
      const a = WAR_PLANETS[i];
      const b = WAR_PLANETS[j];
      const lonA = planets[a]?.longitude;
      const lonB = planets[b]?.longitude;
      if (typeof lonA !== 'number' || typeof lonB !== 'number') continue;
      const d = angDist(lonA, lonB);
      if (d <= 1) {
        const winner = lonA >= lonB ? a : b;
        wars.push({ a, b, winner, dist: d.toFixed(2) });
      }
    }
  }
  return wars;
}

function parseGandanta(payload) {
  const analysis = payload?.gandanta_analysis || payload?.data?.gandanta_analysis || payload || null;
  if (!analysis) return { byPlanet: {}, lagna: null };
  const byPlanet = {};
  const rows = analysis.planets_in_gandanta || analysis.planetary_gandanta || [];
  rows.forEach((row) => {
    const name = typeof row.planet === 'string' ? row.planet : (row.planet?.name || row.name);
    const info = row.gandanta_info || (row.is_gandanta ? row : null);
    if (!name || !info?.is_gandanta) return;
    byPlanet[name] = info;
  });
  const lagna = analysis.lagna_gandanta?.is_gandanta
    ? (analysis.lagna_gandanta.gandanta_info || analysis.lagna_gandanta)
    : null;
  return { byPlanet, lagna };
}

/**
 * Compact planetary-condition strip: combust, R, VG, yuddha, baladi, Gandanta.
 */
export default function DeskConditionStrip({ birthData, chartData, label = 'Cond' }) {
  const [d9, setD9] = useState(null);
  const [gandanta, setGandanta] = useState({ byPlanet: {}, lagna: null });

  useEffect(() => {
    if (!birthData?.date || !chartData) {
      setD9(null);
      return undefined;
    }
    let cancelled = false;
    apiService.calculateDivisionalChart(birthData, 9)
      .then((res) => {
        if (!cancelled) setD9(res?.divisional_chart || res || null);
      })
      .catch(() => {
        if (!cancelled) setD9(null);
      });
    return () => { cancelled = true; };
  }, [birthData, chartData]);

  useEffect(() => {
    if (!chartData?.planets) {
      setGandanta({ byPlanet: {}, lagna: null });
      return undefined;
    }
    let cancelled = false;
    apiService.calculateGandantaAnalysis(chartData)
      .then((res) => {
        if (!cancelled) setGandanta(parseGandanta(res));
      })
      .catch(() => {
        if (!cancelled) setGandanta({ byPlanet: {}, lagna: null });
      });
    return () => { cancelled = true; };
  }, [chartData]);

  const chips = useMemo(() => {
    if (!chartData?.planets) return [];
    const combustSet = new Set(getCombustionConditions(chartData).map((c) => c.planet));
    const wars = findWars(chartData.planets);
    const out = [];

    if (gandanta.lagna) {
      const info = gandanta.lagna;
      const ascLon = typeof chartData.ascendant === 'number'
        ? chartData.ascendant
        : chartData.houses?.[0]?.longitude;
      const nak = nakshatraOf(ascLon);
      out.push({
        key: 'lagna-gan',
        label: 'Asc',
        value: ['Gan', nakshatraShort(nak)].filter(Boolean).join(' · '),
        title: [
          'Lagna in Gandamoola (Gandanta)',
          nak ? `nakṣatra ${nak}` : null,
          info.gandanta_name || 'Gandanta',
          info.intensity ? `${info.intensity} intensity` : null,
          info.distance_from_junction != null ? `${info.distance_from_junction}° from junction` : null,
        ].filter(Boolean).join(' · '),
        tone: 'warn',
      });
    }

    PLANETS.forEach((name) => {
      const data = chartData.planets[name];
      if (!data || typeof data.sign !== 'number') return;
      const gan = gandanta.byPlanet[name];
      const ganNak = gan ? planetNakshatra(data) : null;
      const tags = [];
      if (data.retrograde && name !== 'Rahu' && name !== 'Ketu') tags.push('R');
      if (combustSet.has(name)) tags.push('Combust');
      if (gan) tags.push(ganNak ? `Gan · ${nakshatraShort(ganNak)}` : 'Gan');
      const d9Sign = d9?.planets?.[name]?.sign;
      if (typeof d9Sign === 'number' && d9Sign === data.sign) tags.push('VG');
      const dig = getPlanetDignity(name, data.sign);
      if (dig === 'Exalted') tags.push('Ex');
      if (dig === 'Debilitated') tags.push('Deb');
      const av = baladiShort(
        typeof data.degree === 'number' ? data.degree : (Number(data.longitude) % 30),
        data.sign
      );
      // Extreme / aged avasthās always; Yuva/Kumar only when other flags exist
      if (av === 'Mrit' || av === 'Bal' || av === 'Vriddha') tags.push(av);
      else if (av && tags.length) tags.push(av);
      if (!tags.length) return;
      const titleParts = [`${name}: ${tags.join(', ')}`];
      if (gan) {
        titleParts.push(
          ganNak ? `nakṣatra ${ganNak}` : null,
          gan.gandanta_name || 'Gandanta',
          gan.intensity ? `${gan.intensity} intensity` : null,
          gan.distance_from_junction != null ? `${gan.distance_from_junction}° from junction` : null,
        );
      }
      out.push({
        key: name,
        label: ABBR[name],
        value: tags.join(' · '),
        title: titleParts.filter(Boolean).join(' · '),
        tone: combustSet.has(name) || dig === 'Debilitated' || av === 'Mrit' || gan
          ? 'warn'
          : dig === 'Exalted' || tags.includes('VG')
            ? 'good'
            : 'neutral',
      });
    });

    wars.forEach((w) => {
      out.push({
        key: `war-${w.a}-${w.b}`,
        label: 'Yuddha',
        value: `${ABBR[w.a]}–${ABBR[w.b]} (${ABBR[w.winner]}↑)`,
        title: `Graha yuddha ${w.a}–${w.b} · ${w.dist}° · winner ${w.winner}`,
        tone: 'war',
      });
    });

    return out;
  }, [chartData, d9, gandanta]);

  if (!chips.length) {
    return (
      <div className="desk-cond desk-cond--strip desk-cond--empty" aria-hidden="true">
        <span className="desk-cond__label">{label}</span>
      </div>
    );
  }

  return (
    <div className="desk-cond desk-cond--strip" aria-label="Planetary conditions">
      <span className="desk-cond__label">{label}</span>
      <div className="desk-cond__chips">
        {chips.map((c) => (
          <span key={c.key} className={`desk-cond__chip desk-cond__chip--${c.tone}`} title={c.title}>
            <em>{c.label}</em>
            <strong>{c.value}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}
