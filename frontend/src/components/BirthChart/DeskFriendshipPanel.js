import React, { useMemo, useState } from 'react';
import './DeskFriendshipPanel.css';

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa',
};

/** BPHS natural (naisargika) friendships — matches FriendshipCalculator */
const NATURAL_FRIENDS = {
  Sun: ['Moon', 'Mars', 'Jupiter'],
  Moon: ['Sun', 'Mercury'],
  Mars: ['Sun', 'Moon', 'Jupiter'],
  Mercury: ['Sun', 'Venus'],
  Jupiter: ['Sun', 'Moon', 'Mars'],
  Venus: ['Mercury', 'Saturn'],
  Saturn: ['Mercury', 'Venus'],
};

const NATURAL_ENEMIES = {
  Sun: ['Venus', 'Saturn'],
  Moon: [],
  Mars: ['Mercury'],
  Mercury: ['Moon'],
  Jupiter: ['Mercury', 'Venus'],
  Venus: ['Sun', 'Moon'],
  Saturn: ['Sun', 'Moon', 'Mars'],
};

const TEMPORAL_FRIEND_DIFFS = new Set([1, 2, 3, 9, 10, 11]); // houses 2,3,4,10,11,12

function naturalOf(a, b) {
  if (NATURAL_FRIENDS[a]?.includes(b)) return 'F';
  if (NATURAL_ENEMIES[a]?.includes(b)) return 'E';
  return 'N';
}

function temporalOf(signA, signB) {
  if (typeof signA !== 'number' || typeof signB !== 'number') return 'N';
  const diff = ((signB - signA) % 12 + 12) % 12;
  return TEMPORAL_FRIEND_DIFFS.has(diff) ? 'F' : 'E';
}

function compoundOf(perm, temp) {
  if (perm === 'F' && temp === 'F') return 'BF';
  if (perm === 'F' && temp === 'E') return 'N';
  if (perm === 'E' && temp === 'F') return 'N';
  if (perm === 'E' && temp === 'E') return 'GE';
  if (perm === 'N' && temp === 'F') return 'F';
  if (perm === 'N' && temp === 'E') return 'E';
  return 'N';
}

const LABELS = {
  BF: 'Best friend',
  F: 'Friend',
  N: 'Neutral',
  E: 'Enemy',
  GE: 'Great enemy',
  '·': 'Self',
};

const MODES = [
  { id: 'fiveFold', label: '5-Fold' },
  { id: 'permanent', label: 'Natural' },
  { id: 'temporal', label: 'Temporal' },
];

/**
 * Compact Panchadha Maitri matrix for the Parashari desk.
 */
export default function DeskFriendshipPanel({ chartData }) {
  const [mode, setMode] = useState('fiveFold');

  const matrices = useMemo(() => {
    if (!chartData?.planets) return null;
    const permanent = {};
    const temporal = {};
    const fiveFold = {};

    PLANETS.forEach((p1) => {
      permanent[p1] = {};
      temporal[p1] = {};
      fiveFold[p1] = {};
      const sign1 = chartData.planets[p1]?.sign;
      PLANETS.forEach((p2) => {
                if (p1 === p2) {
          permanent[p1][p2] = '·';
          temporal[p1][p2] = '·';
          fiveFold[p1][p2] = '·';
          return;
        }
        const perm = naturalOf(p1, p2);
        const temp = temporalOf(sign1, chartData.planets[p2]?.sign);
        permanent[p1][p2] = perm;
        temporal[p1][p2] = temp;
        fiveFold[p1][p2] = compoundOf(perm, temp);
      });
    });

    return { permanent, temporal, fiveFold };
  }, [chartData]);

  if (!matrices) {
    return <div className="desk-friend desk-friend--status">No chart data</div>;
  }

  const matrix = matrices[mode];
  const legendKeys = mode === 'fiveFold' ? ['BF', 'F', 'N', 'E', 'GE'] : ['F', 'N', 'E'];

  return (
    <div className="desk-friend" aria-label="Five-fold friendship">
      <div className="desk-friend__modes" role="tablist" aria-label="Friendship type">
        {MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={mode === m.id}
            className={mode === m.id ? 'is-active' : ''}
            onClick={() => setMode(m.id)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="desk-friend__scroll">
        <table className="desk-friend__table">
          <thead>
            <tr>
              <th scope="col" className="desk-friend__corner" />
              {PLANETS.map((p) => (
                <th key={p} scope="col" title={p}>{ABBR[p]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PLANETS.map((p1) => (
              <tr key={p1}>
                <th scope="row" title={p1}>{ABBR[p1]}</th>
                {PLANETS.map((p2) => {
                  const rel = matrix[p1]?.[p2] || 'N';
                  const tone = rel === '·' ? 'self' : rel.toLowerCase();
                  return (
                    <td
                      key={p2}
                      className={`desk-friend__cell desk-friend__cell--${tone}`}
                      title={p1 === p2 ? 'Self' : `${p1} → ${p2}: ${LABELS[rel] || rel}`}
                    >
                      {rel}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="desk-friend__legend" aria-hidden="true">
        {legendKeys.map((k) => (
          <span key={k} className={`desk-friend__cell--${k.toLowerCase()}`}>
            {k} · {LABELS[k]}
          </span>
        ))}
      </div>
      <p className="desk-friend__note">Row → column · Temporal: houses 2–4 & 10–12</p>
    </div>
  );
}
