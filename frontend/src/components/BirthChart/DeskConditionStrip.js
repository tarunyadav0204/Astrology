import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../../services/apiService';
import { getCombustionConditions, getPlanetDignity } from '../../utils/planetAnalyzer';
import './DeskConditionStrip.css';

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa',
};
const WAR_PLANETS = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

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

/**
 * Compact planetary-condition strip: combust, R, VG, yuddha, baladi avasthā.
 */
export default function DeskConditionStrip({ birthData, chartData }) {
  const [d9, setD9] = useState(null);

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

  const chips = useMemo(() => {
    if (!chartData?.planets) return [];
    const combustSet = new Set(getCombustionConditions(chartData).map((c) => c.planet));
    const wars = findWars(chartData.planets);
    const out = [];

    PLANETS.forEach((name) => {
      const data = chartData.planets[name];
      if (!data || typeof data.sign !== 'number') return;
      const tags = [];
      if (data.retrograde && name !== 'Rahu' && name !== 'Ketu') tags.push('R');
      if (combustSet.has(name)) tags.push('Combust');
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
      out.push({
        key: name,
        label: ABBR[name],
        value: tags.join(' · '),
        title: `${name}: ${tags.join(', ')}`,
        tone: combustSet.has(name) || dig === 'Debilitated' || av === 'Mrit'
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
  }, [chartData, d9]);

  if (!chips.length) {
    return (
      <div className="desk-cond desk-cond--strip desk-cond--empty" aria-hidden="true">
        <span className="desk-cond__label">Cond</span>
      </div>
    );
  }

  return (
    <div className="desk-cond desk-cond--strip" aria-label="Planetary conditions">
      <span className="desk-cond__label">Cond</span>
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
