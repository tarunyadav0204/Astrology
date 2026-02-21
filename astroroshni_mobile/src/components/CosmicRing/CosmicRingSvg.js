import React from 'react';
import { View } from 'react-native';
import Svg, { Circle, Line, Text as SvgText, G, Path } from 'react-native-svg';

const CX = 400;
const CY = 400;
const R_OUTER = 380;
const R_NAK = 280;
const R_MID = 200;
const R_INNER = 100;
const R_CENTER = 70;
const R_RASHI_LABEL = 240;
const R_NAK_LABEL = 330;
const R_PLANET = 140;

/** Deterministic star positions for cosmic background (angle in deg, radius from center, size, opacity) */
function getStarPoints() {
  const points = [];
  const goldenAngle = 137.5;
  for (let i = 0; i < 55; i++) {
    const angle = (i * goldenAngle) % 360;
    const r = R_INNER + 30 + ((i * 47) % 230);
    const size = 0.4 + ((i * 13) % 7) / 5;
    const opacity = 0.25 + ((i * 11) % 10) / 18;
    points.push({ angle, r, size, opacity });
  }
  return points;
}

const STAR_POINTS = getStarPoints();

/** 4-point star path (cross sparkle) centered at cx,cy with radius r */
function star4Path(cx, cy, r) {
  const r2 = r * 0.45;
  return `M ${cx} ${cy - r} L ${cx} ${cy + r} M ${cx - r} ${cy} L ${cx + r} ${cy} M ${cx - r2} ${cy - r2} L ${cx + r2} ${cy + r2} M ${cx + r2} ${cy - r2} L ${cx - r2} ${cy + r2}`;
}

const RASHI_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

const NAKSHATRA_LABELS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
  'Pushya', 'Ashlesha', 'Magha', 'P. Phalguni', 'U. Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'P. Ashadha', 'U. Ashadha',
  'Shravana', 'Dhanishta', 'Shatabhisha', 'P. Bhadrapada', 'U. Bhadrapada', 'Revati'
];

const THEME_COLORS = {
  dark: {
    bg: '#0f172a',
    strokeOuter: '#1e293b',
    strokeMid: '#334155',
    strokeInner: '#475569',
    centerFill: '#0f172a',
    rashiText: '#e2e8f0',
    nakText: '#fde047',
    centerTitle: '#f8fafc',
    centerSub: '#94a3b8',
    centerMuted: '#64748b',
    textStroke: '#0f172a',
    starFill: '#fef9c3',
    sparkleStroke: 'rgba(254,249,195,0.9)',
  },
  light: {
    bg: '#fffbf7',
    strokeOuter: '#e7e5e4',
    strokeMid: '#d6d3d1',
    strokeInner: '#a8a29e',
    centerFill: '#fffbf7',
    rashiText: '#1c1917',
    nakText: '#92400e',
    centerTitle: '#1c1917',
    centerSub: '#78716c',
    centerMuted: '#a8a29e',
    textStroke: '#fffbf7',
    starFill: '#fef08a',
    sparkleStroke: 'rgba(254,240,138,0.85)',
  },
};

/** Convert sign (0-11) + degree to x,y on ring. 0° Aries = top, clockwise. */
function positionOnRing(sign, degree, r = R_PLANET) {
  const totalDeg = (sign ?? 0) * 30 + (parseFloat(degree) || 0);
  const angleRad = ((totalDeg - 90) * Math.PI) / 180;
  return {
    x: CX + r * Math.cos(angleRad),
    y: CY + r * Math.sin(angleRad),
  };
}

export default function CosmicRingSvg({
  theme = 'dark',
  dateLabel = '—',
  subLabel = 'SIDEREAL LAHIRI',
  planets = [],
  planetColors = {},
  width = 800,
  height = 800,
}) {
  const c = THEME_COLORS[theme] || THEME_COLORS.dark;

  return (
    <View style={{ width, height }}>
      <Svg width="100%" height="100%" viewBox="0 0 800 800" preserveAspectRatio="xMidYMid meet" style={{ backgroundColor: 'transparent' }}>
        {/* Cosmic background: stars */}
        {STAR_POINTS.map((s, i) => {
          const rad = (s.angle * Math.PI) / 180;
          const x = CX + s.r * Math.sin(rad);
          const y = CY - s.r * Math.cos(rad);
          return (
            <Circle
              key={`star-${i}`}
              cx={x}
              cy={y}
              r={s.size}
              fill={c.starFill}
              opacity={s.opacity}
            />
          );
        })}
        {/* Sparkle stars (4-point) */}
        {[
          { angle: 22, r: 155 },
          { angle: 178, r: 310 },
          { angle: 265, r: 245 },
          { angle: 340, r: 195 },
        ].map((s, i) => {
          const rad = (s.angle * Math.PI) / 180;
          const x = CX + s.r * Math.sin(rad);
          const y = CY - s.r * Math.cos(rad);
          return (
            <Path
              key={`sparkle-${i}`}
              d={star4Path(x, y, 4)}
              fill="none"
              stroke={c.sparkleStroke}
              strokeWidth={1}
              opacity={0.85}
            />
          );
        })}
        {/* Small crescent / celestial accent (optional dot cluster) */}
        {[120, 280].map((angle, i) => {
          const rad = (angle * Math.PI) / 180;
          const x = CX + 350 * Math.sin(rad);
          const y = CY - 350 * Math.cos(rad);
          return (
            <G key={`dot-${i}`}>
              <Circle cx={x} cy={y} r={1.5} fill={c.starFill} opacity={0.5} />
              <Circle cx={x + 8} cy={y - 4} r={0.8} fill={c.starFill} opacity={0.4} />
              <Circle cx={x - 5} cy={y + 6} r={1} fill={c.starFill} opacity={0.35} />
            </G>
          );
        })}
        {/* Rings */}
        <Circle cx={CX} cy={CY} r={R_OUTER} fill="none" stroke={c.strokeOuter} strokeWidth={2} />
        <Circle cx={CX} cy={CY} r={R_NAK} fill="none" stroke={c.strokeMid} strokeWidth={2} />
        <Circle cx={CX} cy={CY} r={R_MID} fill="none" stroke={c.strokeInner} strokeWidth={2} />
        <Circle cx={CX} cy={CY} r={R_INNER} fill="none" stroke={c.strokeMid} strokeWidth={1} />
        <Circle cx={CX} cy={CY} r={R_CENTER} fill="none" stroke={c.strokeMid} strokeWidth={1} />

        {/* Center text */}
        <SvgText x={CX} y={CY - 10} fill={c.centerTitle} fontSize={16} fontWeight="bold" textAnchor="middle" letterSpacing={1}>
          AstroRoshni
        </SvgText>
        <SvgText x={CX} y={CY + 10} fill={c.centerSub} fontSize={10} textAnchor="middle" letterSpacing={1}>
          {dateLabel}
        </SvgText>
        <SvgText x={CX} y={CY + 25} fill={c.centerMuted} fontSize={9} textAnchor="middle" letterSpacing={0.5}>
          {subLabel}
        </SvgText>

        {/* Rashi divider lines (12) - at boundaries 0°, 30°, ... */}
        {RASHI_NAMES.map((_, i) => {
          const deg = i * 30;
          const rad = (deg * Math.PI) / 180;
          const x1 = CX + R_INNER * Math.sin(rad);
          const y1 = CY - R_INNER * Math.cos(rad);
          const x2 = CX + R_OUTER * Math.sin(rad);
          const y2 = CY - R_OUTER * Math.cos(rad);
          return <Line key={`rashi-line-${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke={c.strokeInner} strokeWidth={1.5} />;
        })}
        {/* Rashi labels (12) - at centre of each section, rotated with the circle */}
        {RASHI_NAMES.map((name, i) => {
          const deg = 15 + i * 30;
          const rad = (deg * Math.PI) / 180;
          const tx = CX + R_RASHI_LABEL * Math.sin(rad);
          const ty = CY - R_RASHI_LABEL * Math.cos(rad);
          return (
            <G key={name} transform={`rotate(${deg}, ${tx}, ${ty})`}>
              <SvgText x={tx} y={ty} fill={c.rashiText} fontSize={18} fontWeight="bold" textAnchor="middle" dominantBaseline="middle">
                {name}
              </SvgText>
            </G>
          );
        })}

        {/* Nakshatra divider lines (27) - at boundaries */}
        {NAKSHATRA_LABELS.map((_, i) => {
          const deg = (i * 360) / 27;
          const rad = (deg * Math.PI) / 180;
          const x1 = CX + R_NAK * Math.sin(rad);
          const y1 = CY - R_NAK * Math.cos(rad);
          const x2 = CX + R_OUTER * Math.sin(rad);
          const y2 = CY - R_OUTER * Math.cos(rad);
          return <Line key={`nak-line-${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke={c.strokeMid} strokeWidth={1} />;
        })}
        {/* Nakshatra labels (27) - 8 chars first line, rest on second line so it fits */}
        {NAKSHATRA_LABELS.map((name, i) => {
          const deg = ((i + 0.5) * 360) / 27;
          const rad = (deg * Math.PI) / 180;
          const tx = CX + R_NAK_LABEL * Math.sin(rad);
          const ty = CY - R_NAK_LABEL * Math.cos(rad);
          const nakFontSize = 16;
          const lineHeight = 16;
          const maxFirstLine = 8;
          const firstLine = name.length <= maxFirstLine ? name : name.slice(0, maxFirstLine);
          const secondLine = name.length > maxFirstLine ? name.slice(maxFirstLine).trim() : null;
          const offsetY = secondLine ? -lineHeight / 2 : 0;
          return (
            <G key={`${name}-${i}`} transform={`rotate(${deg}, ${tx}, ${ty})`}>
              <SvgText x={tx} y={ty + offsetY} fill={c.nakText} fontSize={nakFontSize} fontWeight="600" textAnchor="middle" dominantBaseline="middle">
                {firstLine}
              </SvgText>
              {secondLine ? (
                <SvgText x={tx} y={ty + offsetY + lineHeight} fill={c.nakText} fontSize={nakFontSize} fontWeight="600" textAnchor="middle" dominantBaseline="middle">
                  {secondLine}
                </SvgText>
              ) : null}
            </G>
          );
        })}

        {/* Planets */}
        {planets.map((p) => {
          if (p.sign === undefined || p.sign === null) return null;
          const { x, y } = positionOnRing(p.sign, p.degree ?? 0);
          const color = planetColors[p.name] || '#f8fafc';
          const lineStart = positionOnRing(p.sign, p.degree ?? 0, R_INNER + 10);
          const dy = y > CY ? 14 : -6;
          return (
            <G key={p.name}>
              <Line
                x1={lineStart.x}
                y1={lineStart.y}
                x2={x}
                y2={y}
                stroke={color}
                strokeWidth={1}
                strokeDasharray="3 3"
                opacity={0.6}
              />
              <Circle cx={x} cy={y} r={4} fill={color} />
              <SvgText
                x={x}
                y={y + dy}
                fill={color}
                fontSize={11}
                fontWeight="700"
                textAnchor="middle"
              >
                {p.name}
              </SvgText>
            </G>
          );
        })}
      </Svg>
    </View>
  );
}

export { positionOnRing, THEME_COLORS, RASHI_NAMES, NAKSHATRA_LABELS };
