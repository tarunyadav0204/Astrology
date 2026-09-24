import React from 'react';
import { G, Line, Polygon, Text as SvgText } from 'react-native-svg';

export const SPECIAL_ASPECTS = {
  Mars: [4, 8],
  Jupiter: [5, 9],
  Saturn: [3, 10],
};

export const NADI_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
const NADI_PLANET_SET = new Set(NADI_PLANETS);
const NADI_ASPECTS = [5, 7, 9];

export const planetAspectCounts = (mode, planetName) => {
  if (mode === 'nadi') return NADI_PLANET_SET.has(planetName) ? NADI_ASPECTS : null;
  if (mode === 'parashari') return SPECIAL_ASPECTS[planetName] || null;
  return null;
};

const SIGN_LORDS = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];

export const lagnaRoleLords = (lagnaSign) => {
  if (!Number.isInteger(lagnaSign)) return { badhaka: null, maraka: [] };
  const lord = (house) => SIGN_LORDS[(lagnaSign + house - 1) % 12];
  const badhakaHouse = [0, 3, 6, 9].includes(lagnaSign) ? 11 : [1, 4, 7, 10].includes(lagnaSign) ? 9 : 7;
  return {
    badhaka: lord(badhakaHouse),
    maraka: [...new Set([lord(2), lord(7)])],
  };
};

export const jaiminiTargetSigns = (sign) => {
  const movable = [0, 3, 6, 9];
  const fixed = [1, 4, 7, 10];
  const dual = [2, 5, 8, 11];
  if (movable.includes(sign)) return fixed.filter((item) => item !== (sign + 1) % 12);
  if (fixed.includes(sign)) return movable.filter((item) => item !== (sign + 11) % 12);
  if (dual.includes(sign)) return dual.filter((item) => item !== sign);
  return [];
};

export const aspectHouse = (fromHouse, count) => ((fromHouse - 1 + (count - 1)) % 12) + 1;

const segmentHit = (x1, y1, x2, y2, x3, y3, x4, y4) => {
  const d1x = x2 - x1;
  const d1y = y2 - y1;
  const d2x = x4 - x3;
  const d2y = y4 - y3;
  const den = d1x * d2y - d1y * d2x;
  if (Math.abs(den) < 1e-8) return null;
  const t = ((x3 - x1) * d2y - (y3 - y1) * d2x) / den;
  const u = ((x3 - x1) * d1y - (y3 - y1) * d1x) / den;
  if (t <= 0.02 || t >= 1 || u < 0 || u > 1) return null;
  return { x: x1 + t * d1x, y: y1 + t * d1y, t };
};

export const aspectArrow = (from, center, polygon, aspect, key) => {
  if (!from || !center || !polygon?.length) return null;
  let entry = null;
  for (let i = 0; i < polygon.length; i += 1) {
    const [x3, y3] = polygon[i];
    const [x4, y4] = polygon[(i + 1) % polygon.length];
    const hit = segmentHit(from.x, from.y, center.x, center.y, x3, y3, x4, y4);
    if (hit && (!entry || hit.t < entry.t)) entry = hit;
  }
  if (!entry) return null;
  const dx = entry.x - from.x;
  const dy = entry.y - from.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const startPad = Math.min(16, len * 0.28);
  const x1 = from.x + ux * startPad;
  const y1 = from.y + uy * startPad;
  const room = Math.hypot(center.x - entry.x, center.y - entry.y);
  const inset = Math.min(18, room * 0.42);
  const x2 = entry.x + ux * inset;
  const y2 = entry.y + uy * inset;
  if (Math.hypot(x2 - x1, y2 - y1) < 10) return null;
  const head = 6.5;
  const baseX = x2 - ux * head;
  const baseY = y2 - uy * head;
  const px = -uy * 2.6;
  const py = ux * 2.6;
  return {
    key,
    aspect,
    x1,
    y1,
    x2,
    y2,
    head: `${x2},${y2} ${baseX + px},${baseY + py} ${baseX - px},${baseY - py}`,
    labelX: entry.x + ux * (inset + 11),
    labelY: entry.y + uy * (inset + 11) + 3,
  };
};

export function ChartAspectArrows({ arrows, color }) {
  if (!arrows?.length) return null;
  return (
    <G pointerEvents="none">
      {arrows.map((arrow) => (
        <G key={arrow.key}>
          <Line
            x1={arrow.x1}
            y1={arrow.y1}
            x2={arrow.x2}
            y2={arrow.y2}
            stroke={color}
            strokeOpacity={0.28}
            strokeWidth={1.1}
            strokeLinecap="round"
          />
          <Polygon points={arrow.head} fill={color} fillOpacity={0.28} />
          {arrow.aspect ? (
            <SvgText
              x={arrow.labelX}
              y={arrow.labelY}
              fontSize="8"
              fill={color}
              fillOpacity={0.42}
              fontWeight="600"
              textAnchor="middle"
            >
              {arrow.aspect}
            </SvgText>
          ) : null}
        </G>
      ))}
    </G>
  );
}

export default ChartAspectArrows;
