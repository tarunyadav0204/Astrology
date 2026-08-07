import React, { useMemo } from 'react';
import './DeskAspectsPanel.css';

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
const ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

/** Parashari house aspects from planet's occupied sign (1 = occupied). */
const GRAHA_HOUSE_ASPECTS = {
  Sun: [7],
  Moon: [7],
  Mars: [4, 7, 8],
  Mercury: [7],
  Jupiter: [5, 7, 9],
  Venus: [7],
  Saturn: [3, 7, 10],
  Rahu: [5, 7, 9],
  Ketu: [5, 7, 9],
};

const SPECIAL = new Set(['Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu']);

function nth(n) {
  if (n === 3) return '3';
  if (n === 4) return '4';
  if (n === 5) return '5';
  if (n === 7) return '7';
  if (n === 8) return '8';
  if (n === 9) return '9';
  if (n === 10) return '10';
  return String(n);
}

function aspectsFromTo(fromSign, fromName, toSign) {
  if (typeof fromSign !== 'number' || typeof toSign !== 'number') return [];
  if (fromSign === toSign) return []; // conjunction / co-tenant, not drishti cell
  const aspects = GRAHA_HOUSE_ASPECTS[fromName] || [7];
  return aspects.filter((n) => (fromSign + n - 1) % 12 === toSign);
}

/**
 * Compact Parashari drishti matrix (row aspects column).
 */
export default function DeskAspectsPanel({ chartData }) {
  const { matrix, hasAny } = useMemo(() => {
    if (!chartData?.planets) return { matrix: null, hasAny: false };
    let any = false;
    const grid = {};
    PLANETS.forEach((p1) => {
      grid[p1] = {};
      const s1 = chartData.planets[p1]?.sign;
      PLANETS.forEach((p2) => {
        if (p1 === p2) {
          grid[p1][p2] = { label: '·', hits: [], special: false };
          return;
        }
        const s2 = chartData.planets[p2]?.sign;
        const hits = aspectsFromTo(s1, p1, s2);
        if (hits.length) any = true;
        const specialHit = SPECIAL.has(p1) && hits.some((h) => h !== 7);
        grid[p1][p2] = {
          label: hits.length ? hits.map(nth).join(',') : '',
          hits,
          special: specialHit,
        };
      });
    });
    return { matrix: grid, hasAny: any };
  }, [chartData]);

  if (!matrix) {
    return <div className="desk-asp desk-asp--status">No chart data</div>;
  }

  if (!hasAny) {
    return <div className="desk-asp desk-asp--status">No drishti links found</div>;
  }

  return (
    <div className="desk-asp" aria-label="Graha drishti matrix">
      <p className="desk-asp__note">Row → column · house aspects (7th + special)</p>
      <div className="desk-asp__scroll">
        <table className="desk-asp__table">
          <thead>
            <tr>
              <th className="desk-asp__corner" />
              {PLANETS.map((p) => (
                <th key={p} title={p}>{ABBR[p]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PLANETS.map((p1) => (
              <tr key={p1}>
                <th scope="row" title={p1}>{ABBR[p1]}</th>
                {PLANETS.map((p2) => {
                  const cell = matrix[p1][p2];
                  if (p1 === p2) {
                    return <td key={p2} className="desk-asp__self">·</td>;
                  }
                  if (!cell.label) {
                    return <td key={p2} className="desk-asp__empty" />;
                  }
                  return (
                    <td
                      key={p2}
                      className={`desk-asp__hit${cell.special ? ' is-special' : ''}`}
                      title={`${p1} aspects ${p2}: ${cell.hits.map((h) => `${h}th`).join(', ')}`}
                    >
                      {cell.label}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="desk-asp__legend" aria-hidden="true">
        <span>7 = full aspect</span>
        <span className="is-special">4/8 Ma · 5/9 Ju/Ra/Ke · 3/10 Sa</span>
      </div>
    </div>
  );
}
