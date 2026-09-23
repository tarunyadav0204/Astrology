import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Animated, Easing, Platform } from 'react-native';
import Svg, { Rect, Polygon, Line, Text as SvgText, G, Defs, LinearGradient, Stop, Circle, Path, ClipPath } from 'react-native-svg';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

// Create animated versions of SVG components
const AnimatedLine = Animated.createAnimatedComponent(Line);
const AnimatedPolygon = Animated.createAnimatedComponent(Polygon);
const AnimatedRect = Animated.createAnimatedComponent(Rect);
const AnimatedG = Animated.createAnimatedComponent(G);
const HOUSE_DOT_POINTS = {
  // Keep markers in the open outer part of each house, away from sign
  // numbers and the central planet-label area.
  1: { x: 250, y: 55 }, 2: { x: 150, y: 20 }, 3: { x: 25, y: 70 },
  4: { x: 70, y: 190 }, 5: { x: 25, y: 330 }, 6: { x: 150, y: 380 },
  7: { x: 250, y: 345 }, 8: { x: 350, y: 380 }, 9: { x: 375, y: 330 },
  10: { x: 350, y: 190 }, 11: { x: 375, y: 70 }, 12: { x: 350, y: 20 },
};
const SAV_RADIUS = 12;

const circleInsidePolygon = (x, y, radius, polygon) => {
  if (!pointInPolygon(x, y, polygon)) return false;
  for (let step = 0; step < 8; step += 1) {
    const angle = (Math.PI * 2 * step) / 8;
    if (!pointInPolygon(x + Math.cos(angle) * radius, y + Math.sin(angle) * radius, polygon)) {
      return false;
    }
  }
  return true;
};

export const placeCircleClear = (polygon, occupied, radius) => {
  if (!polygon) return null;
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const radii = [radius, Math.max(8, radius - 4)];
  let fallback = null;
  for (const nextRadius of radii) {
    let best = null;
    for (let x = minX + nextRadius; x <= maxX - nextRadius; x += 4) {
      for (let y = minY + nextRadius; y <= maxY - nextRadius; y += 4) {
        if (!circleInsidePolygon(x, y, nextRadius + 1, polygon)) continue;
        const box = labelBox(x, y, nextRadius, nextRadius, nextRadius);
        const gap = occupied.reduce((min, rect) => Math.min(min, boxGap(box, rect)), Infinity);
        const spot = { x, y, gap, radius: nextRadius, box };
        if (!best || gap > best.gap) best = spot;
      }
    }
    if (best && best.gap >= 2) return best;
    if (best && (!fallback || best.gap > fallback.gap)) fallback = best;
  }
  return fallback;
};

const HOUSE_DOT_POINTS_ALT = {
  1: { x: 180, y: 145 }, 2: { x: 75, y: 67 }, 3: { x: 50, y: 97 },
  4: { x: 125, y: 197 }, 5: { x: 50, y: 302 }, 6: { x: 75, y: 332 },
  7: { x: 180, y: 252 }, 8: { x: 300, y: 332 }, 9: { x: 375, y: 282 },
  10: { x: 250, y: 197 }, 11: { x: 375, y: 97 }, 12: { x: 300, y: 62 },
};
const HOUSE_POLYGONS = {
  1: [[200, 0], [300, 100], [200, 200], [100, 100]],
  2: [[0, 0], [200, 0], [100, 100]],
  3: [[0, 0], [100, 100], [0, 200]],
  4: [[0, 200], [100, 100], [200, 200], [100, 300]],
  5: [[0, 200], [100, 300], [0, 400]],
  6: [[0, 400], [100, 300], [200, 400]],
  7: [[200, 200], [300, 300], [200, 400], [100, 300]],
  8: [[200, 400], [300, 300], [400, 400]],
  9: [[300, 300], [400, 200], [400, 400]],
  10: [[200, 200], [300, 100], [400, 200], [300, 300]],
  11: [[300, 100], [400, 0], [400, 200]],
  12: [[200, 0], [400, 0], [300, 100]],
};

const pointInPolygon = (x, y, polygon) => {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    const crosses = (yi > y) !== (yj > y)
      && x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-9) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
};

export const labelBox = (x, y, halfW, above, below) => ({
  left: x - halfW,
  right: x + halfW,
  top: y - above,
  bottom: y + below,
});

const boxInsidePolygon = (box, polygon) => (
  [
    [box.left, box.top],
    [box.right, box.top],
    [box.left, box.bottom],
    [box.right, box.bottom],
    [(box.left + box.right) / 2, (box.top + box.bottom) / 2],
  ].every(([x, y]) => pointInPolygon(x, y, polygon))
);

const boxGap = (a, b) => {
  const dx = Math.max(b.left - a.right, a.left - b.right, 0);
  const dy = Math.max(b.top - a.bottom, a.top - b.bottom, 0);
  if (dx === 0 && dy === 0) {
    const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    return -Math.min(overlapX, overlapY);
  }
  return Math.hypot(dx, dy);
};

export const textHalfWidth = (text, fontSize) => Math.max(4, String(text || '').length * fontSize * 0.34);

const colorLuminance = (hex) => {
  const raw = String(hex || '').replace('#', '');
  if (raw.length < 6) return 0;
  const channel = (index) => {
    const value = parseInt(raw.slice(index, index + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(0) + 0.7152 * channel(2) + 0.0722 * channel(4);
};

const colorContrast = (a, b) => {
  const lighter = Math.max(colorLuminance(a), colorLuminance(b));
  const darker = Math.min(colorLuminance(a), colorLuminance(b));
  return (lighter + 0.05) / (darker + 0.05);
};

const readableHex = (value) => (
  /^#[0-9A-Fa-f]{6}$/.test(String(value || '').trim()) ? String(value).trim() : null
);

// Letter color for the period planets. Theme color when it stays readable on the
// chart surface and apart from the other planets; otherwise a strong mark color.
export const dashaPaint = (colors) => {
  const primary = readableHex(colors?.primary) || '#701d3f';
  const accent = readableHex(colors?.accent) || primary;
  const ink = readableHex(colors?.chartText) || '#210b17';
  const surface = readableHex(colors?.chartSurface) || '#fffaf2';
  const marks = colorLuminance(surface) >= 0.4
    ? ['#9f1239', '#1d4ed8', '#b45309', '#0f766e']
    : ['#fb7185', '#38bdf8', '#fbbf24', '#4ade80'];
  const pool = [];
  [primary, accent, ...marks].forEach((hex) => {
    if (!pool.includes(hex)) pool.push(hex);
  });
  const scored = pool.map((hex) => ({
    hex,
    theme: hex === primary || hex === accent,
    surface: colorContrast(hex, surface),
    ink: colorContrast(hex, ink),
  }));
  const themeOk = scored.find((item) => item.theme && item.surface >= 4.5 && item.ink >= 1.7);
  const distinct = scored
    .filter((item) => item.surface >= 4.5 && item.ink >= 2)
    .sort((a, b) => (b.surface + Math.min(b.ink, 4)) - (a.surface + Math.min(a.ink, 4)));
  const readable = scored
    .filter((item) => item.surface >= 4.5)
    .sort((a, b) => b.surface - a.surface);
  const brightest = scored.slice().sort((a, b) => b.surface - a.surface)[0];
  const chosen = themeOk || distinct[0] || readable[0] || brightest;
  return { fill: chosen.hex, glow: chosen.hex };
};

export const dashaLevelSuffix = (planetName, highlight) => {
  if (!highlight || !planetName) return '';
  const tags = [];
  if (highlight.mahadasha === planetName) tags.push('MD');
  if (highlight.antardasha === planetName) tags.push('AD');
  if (highlight.pratyantardasha === planetName) tags.push('PD');
  return tags.length ? tags.join('·') : '';
};

// Same anchors the natal labels already use. Transit placement reads these
// so it can sit in the leftover space without shifting a birth planet.
const natalPlanetAnchor = (houseNumber, center, totalPlanets, pIndex) => {
  let planetX;
  let planetY;

  if (totalPlanets === 1) {
    if (houseNumber === 1) {
      planetX = center.x;
      planetY = center.y - 15;
    } else if ([3, 4, 5].includes(houseNumber)) {
      planetX = center.x - (houseNumber === 3 ? 10 : 15);
      planetY = center.y + 10;
    } else if ([6, 7, 8].includes(houseNumber)) {
      planetX = center.x;
      planetY = center.y + 30;
    } else if (houseNumber === 9) {
      planetX = center.x + 10;
      planetY = center.y - 10;
    } else if (houseNumber === 10) {
      planetX = center.x + 15;
      planetY = center.y - 20;
    } else if (houseNumber === 11) {
      planetX = center.x + 5;
      planetY = center.y - 5;
    } else if (houseNumber === 12) {
      planetX = center.x;
      planetY = center.y - 25;
    } else if (houseNumber === 2) {
      planetX = center.x;
      planetY = center.y - 20;
    } else {
      planetX = center.x;
      planetY = center.y - 10;
    }
  } else if (totalPlanets <= 4) {
    if ([3, 5, 9, 11].includes(houseNumber)) {
      const rowSpacing = 35;
      if (houseNumber === 3) {
        planetX = center.x - 25;
        planetY = center.y - 30 + (pIndex * rowSpacing);
      } else if (houseNumber === 5) {
        planetX = center.x - 25;
        planetY = center.y - 38 + (pIndex * rowSpacing);
      } else if (houseNumber === 9) {
        planetX = center.x + 30;
        planetY = center.y - 30 + (pIndex * rowSpacing);
      } else if (houseNumber === 11) {
        planetX = center.x + 25;
        planetY = center.y - 45 + (pIndex * rowSpacing);
      }
    } else {
      const row = Math.floor(pIndex / 2);
      const col = pIndex % 2;
      const spacing = 25;
      const rowSpacing = 32;

      if (houseNumber === 1) {
        planetX = center.x + (col === 0 ? -spacing : spacing);
        planetY = center.y - 20 + (row * rowSpacing);
      } else if (houseNumber === 4) {
        planetX = center.x - 25 + (col === 0 ? -spacing : spacing);
        planetY = center.y + 5 + (row * rowSpacing);
      } else if ([6, 7, 8].includes(houseNumber)) {
        planetX = center.x + (col === 0 ? -spacing : spacing);
        planetY = center.y + 25 + (row * rowSpacing);
      } else if (houseNumber === 10) {
        planetX = center.x + 15 + (col === 0 ? -spacing : spacing);
        planetY = center.y - 25 + (row * rowSpacing);
      } else if (houseNumber === 12) {
        planetX = center.x + (col === 0 ? -spacing : spacing);
        planetY = center.y - 15 + (row * rowSpacing);
      } else if (houseNumber === 2) {
        planetX = center.x + (col === 0 ? -spacing : spacing);
        planetY = center.y - 25 + (row * rowSpacing);
      } else {
        planetX = center.x + (col === 0 ? -spacing : spacing);
        planetY = center.y - 25 + (row * rowSpacing);
      }
    }
  } else {
    const rowSpacing = 26;

    if (houseNumber === 1) {
      planetX = center.x;
      planetY = center.y - 25 + (pIndex * rowSpacing);
    } else if ([3, 4, 5].includes(houseNumber)) {
      planetX = center.x - (houseNumber === 3 ? 20 : 25);
      planetY = center.y + 0 + (pIndex * rowSpacing);
    } else if ([6, 7, 8].includes(houseNumber)) {
      planetX = center.x;
      planetY = center.y + 20 + (pIndex * rowSpacing);
    } else if (houseNumber === 9) {
      planetX = center.x + 20;
      planetY = center.y - 20 + (pIndex * rowSpacing);
    } else if (houseNumber === 10) {
      planetX = center.x + 15;
      planetY = center.y - 30 + (pIndex * rowSpacing);
    } else if (houseNumber === 11) {
      planetX = center.x + 15;
      planetY = center.y - 15 + (pIndex * rowSpacing);
    } else if (houseNumber === 12) {
      planetX = center.x;
      planetY = center.y - 5 + (pIndex * rowSpacing);
    } else if (houseNumber === 2) {
      planetX = center.x;
      planetY = center.y - 35 + (pIndex * rowSpacing);
    } else {
      planetX = center.x;
      planetY = center.y - 30 + (pIndex * rowSpacing);
    }
  }

  if ([6, 8].includes(houseNumber) && totalPlanets > 1) {
    // Bottom triangles are short. A second row lands on the sign number and
    // then on the frame, so keep every planet on one row in the wide base.
    const y = 372;
    const edgeLeft = houseNumber === 8 ? 600 - y : 400 - y;
    const edgeRight = houseNumber === 8 ? y : y - 200;
    const inset = 26;
    const innerLeft = edgeLeft + inset;
    const innerRight = edgeRight - inset;
    const slot = (innerRight - innerLeft) / Math.max(totalPlanets - 1, 1);
    planetX = innerLeft + pIndex * slot;
    planetY = y;
  } else if (houseNumber === 7 && totalPlanets > 1) {
    const packed = totalPlanets > 4;
    const rowSpacingUsed = packed ? 28 : 32;
    const rowCount = packed ? totalPlanets : Math.ceil(totalPlanets / 2);
    const rowIndex = packed ? pIndex : Math.floor(pIndex / 2);
    const bottomLimit = 368;
    let start = planetY - rowIndex * rowSpacingUsed;
    const lastY = start + (rowCount - 1) * rowSpacingUsed;
    if (lastY > bottomLimit) start -= lastY - bottomLimit;
    planetY = start + rowIndex * rowSpacingUsed;
  }

  return { x: planetX, y: planetY };
};

const signAnchor = (houseNumber, center) => ({
  x: houseNumber === 1 ? center.x - 5
    : houseNumber === 2 ? center.x - 10
    : houseNumber === 3 ? center.x + 10
    : houseNumber === 4 ? center.x + 40
    : houseNumber === 5 ? center.x + 10
    : houseNumber === 6 ? center.x - 15
    : houseNumber === 7 ? center.x - 5
    : houseNumber === 8 ? center.x - 5
    : houseNumber === 9 ? center.x - 20
    : houseNumber === 10 ? center.x - 50
    : houseNumber === 11 ? center.x - 25
    : center.x - 5,
  y: houseNumber === 1 ? center.y + 55
    : houseNumber === 2 ? center.y + 25
    : houseNumber === 6 ? center.y - 10
    : houseNumber === 7 ? center.y - 40
    : houseNumber === 8 ? center.y - 10
    : houseNumber === 12 ? center.y + 20
    : houseNumber === 5 ? center.y + 10
    : center.y + 5,
});

const polygonCentroid = (polygon) => {
  const count = polygon.length || 1;
  return {
    x: polygon.reduce((sum, point) => sum + point[0], 0) / count,
    y: polygon.reduce((sum, point) => sum + point[1], 0) / count,
  };
};

// Pick baselines whose glyphs stay inside the house and clear of occupied boxes.
// Clearance wins over sitting near the house center, which is where natal labels are.
export const placeClearLabels = (polygon, occupied, specs, minGap = 3) => {
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const centroid = polygonCentroid(polygon);
  const candidates = [];
  for (let x = minX + 2; x <= maxX - 2; x += 2) {
    for (let y = minY + 2; y <= maxY - 2; y += 2) {
      candidates.push({ x, y });
    }
  }

  const blocked = occupied.slice();
  const placed = [];
  for (const spec of specs) {
    let best = null;
    candidates.forEach((candidate) => {
      const box = labelBox(candidate.x, candidate.y, spec.halfW, spec.above, spec.below);
      let inside;
      if (spec.lineOffsets) {
        const samples = [candidate.x - spec.halfW, candidate.x, candidate.x + spec.halfW];
        inside = spec.lineOffsets.every((offset) => (
          samples.every((x) => pointInPolygon(x, candidate.y + offset, polygon))
        )) && pointInPolygon(candidate.x, candidate.y - Math.max(3, spec.above - 1), polygon);
      } else {
        inside = boxInsidePolygon(labelBox(
          candidate.x,
          candidate.y,
          spec.halfW + 1,
          spec.above + 1,
          spec.below + 1,
        ), polygon);
      }
      if (!inside) return;
      const gap = blocked.reduce((min, rect) => Math.min(min, boxGap(box, rect)), Infinity);
      if (gap < (spec.lineOffsets ? 1 : minGap)) return;
      const dist = Math.hypot(candidate.x - centroid.x, candidate.y - centroid.y);
      const score = gap - dist * 0.02;
      if (!best || score > best.score) best = { ...candidate, score, box };
    });
    if (!best) {
      placed.push(null);
      return placed;
    }
    placed.push(best);
    blocked.push(best.box);
  }
  return placed;
};

const TRANSIT_MARK = '\u1D40';

const bavSuffix = (label) => (Number.isInteger(label.bav) ? ` ${label.bav}` : '');

export const signPointAt = (signPoints, signIndex) => {
  if (!Array.isArray(signPoints) || signIndex < 0 || signIndex > 11) return null;
  const value = signPoints[signIndex];
  return Number.isFinite(value) ? value : null;
};

export const transitBav = (bavBySign, planetName, signIndex) => {
  if (!bavBySign || signIndex == null || signIndex < 0) return null;
  const value = bavBySign[planetName]?.[signIndex];
  return Number.isInteger(value) ? value : null;
};

// Try roomy labels first, then shorter ones. Never overlap a natal box.
export const placeTransitLabels = (polygon, occupied, labels, showDegree) => {
  if (!labels.length) return null;
  const fullText = (label) => `${label.symbol}${label.retrograde ? '(R)' : ''}${TRANSIT_MARK}${bavSuffix(label)}`;
  const shortText = (label) => `${label.symbol}${TRANSIT_MARK}${bavSuffix(label)}`;
  const detailText = (label) => `${label.degree || ''} ${label.nakshatra || ''}`.trim();
  const detailSpec = (label, fontSize, detailSize) => {
    const text = fullText(label);
    const detail = detailText(label);
    const detailOffset = detailSize + 2;
    return {
      halfW: Math.max(textHalfWidth(text, fontSize), textHalfWidth(detail, detailSize)),
      above: Math.ceil(fontSize * 0.8),
      below: detailOffset + Math.ceil(detailSize * 0.4),
      text,
      detail,
      fontSize,
      detailSize,
      detailOffset,
      name: label.name,
      lineOffsets: [0, detailOffset],
    };
  };
  const nameSpec = (label, fontSize, textOf) => {
    const text = textOf(label);
    return {
      halfW: textHalfWidth(text, fontSize),
      above: fontSize,
      below: 2,
      text,
      fontSize,
      name: label.name,
    };
  };

  const blocked = occupied.slice();
  const placed = [];
  const specs = [];
  labels.forEach((label) => {
    const tries = [];
    if (showDegree && detailText(label)) {
      tries.push(detailSpec(label, 9, 7), detailSpec(label, 8, 6));
    }
    tries.push(nameSpec(label, 9, fullText), nameSpec(label, 8, shortText), nameSpec(label, 7, shortText));
    for (const spec of tries) {
      const slot = placeClearLabels(polygon, blocked, [spec], 2)[0];
      if (!slot) continue;
      placed.push(slot);
      specs.push(spec);
      blocked.push(slot.box);
      return;
    }
  });
  if (placed.length) return { placed, specs };

  if (labels.length > 1) {
    for (const fontSize of [8, 7]) {
      const text = labels.map(shortText).join(' ');
      const spec = {
        halfW: textHalfWidth(text, fontSize),
        above: fontSize,
        below: 2,
        text,
        fontSize,
        joined: true,
      };
      const slot = placeClearLabels(polygon, occupied, [spec], 2)[0];
      if (slot) return { placed: [slot], specs: [spec] };
    }
  }
  return null;
};
// House polygons and grid lines must share the same 400×400 frame so
// active-house fills align with the diagonal/diamond dividers.
const CHART_SIZE = 400;
const CHART_MID = CHART_SIZE / 2;
const CHART_DIAMOND_POINTS = `${CHART_MID},0 ${CHART_SIZE},${CHART_MID} ${CHART_MID},${CHART_SIZE} 0,${CHART_MID}`;

const NorthIndianChart = ({
  chartData,
  chartType,
  birthData,
  showDegreeNakshatra = true,
  cosmicTheme = false,
  rotatedAscendant = null,
  onRotate,
  showKarakas = false,
  karakas = null,
  highlightHouse = null,
  highlightColor = null,
  highlightFill = null,
  glowAnimation = null,
  hideInstructions = false,
  onHousePress, // New prop for drawer
  houseActivation = null,
  size = null, // PWA/web: explicit pixel square (avoids % SVG collapse)
  onDarkSurface = false,
  gridLineColor = null,
  gridLineWidth = null,
  transitOverlay = null,
  dashaHighlight = null,
  signPoints = null,
  bavBySign = null,
  onTransitPlanetPress = null,
}) => {
  const { theme, colors } = useTheme();
  const { t } = useTranslation();
  const themedChartText = onDarkSurface ? colors.textInverse : colors.chartText;
  const themedChartTextMuted = onDarkSurface ? colors.textInverseMuted : colors.chartTextMuted;
  const themedChartLine = onDarkSurface ? colors.cosmicLine : colors.chartLine;
  const resolvedGridLine = gridLineColor || themedChartLine;
  const resolvedGridLineWidth = gridLineWidth || (cosmicTheme ? 1 : 2);

  const [tooltip, setTooltip] = useState({ show: false, text: '' });

  // Animation refs
  const drawAnim = useRef(new Animated.Value(0)).current;
  const lastDataRef = useRef(null);
  const drawAnimHandleRef = useRef(null);
  const mountedRef = useRef(true);
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      drawAnimHandleRef.current?.stop?.();
      drawAnim.stopAnimation();
    };
  }, [drawAnim]);

  useEffect(() => {
    if (!chartData) return;

    // Deep compare chartData to prevent unnecessary animation resets
    const dataString = JSON.stringify({
      planets: chartData.planets,
      houses: chartData.houses,
      chartType,
      rotatedAscendant
    });

    if (lastDataRef.current === dataString) {
      return;
    }
    lastDataRef.current = dataString;

    drawAnimHandleRef.current?.stop?.();
    drawAnim.setValue(0);
    if (!mountedRef.current) return;
    setIsAnimating(true);

    const anim = Animated.timing(drawAnim, {
      toValue: 1,
      duration: 800,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    });
    drawAnimHandleRef.current = anim;
    anim.start(({ finished }) => {
      if (mountedRef.current && finished) {
        setIsAnimating(false);
      }
    });
  }, [chartData, chartType, rotatedAscendant, drawAnim]);

  const handlePlanetPress = (planet) => {
    if (chartType === 'transit' && onTransitPlanetPress && bavBySign?.[planet.name]) {
      onTransitPlanetPress(planet.name);
      return;
    }
    const tooltipText = `${planet.name}: ${planet.formattedDegree} in ${planet.nakshatra} · Pada ${planet.pada}`;
    setTooltip({ show: true, text: tooltipText });
    setTimeout(() => setTooltip({ show: false, text: '' }), 2000);
  };

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  const handleHousePressInternal = (houseNum) => {
    const houseIndex = houseNum - 1;
    const rashiIndex = getRashiForHouse(houseIndex);
    const planetsInHouse = getPlanetsInHouse(houseIndex);

    if (onHousePress) {
      onHousePress({
        houseNum,
        rashiIndex,
        signName: rashiNames[rashiIndex],
        planets: planetsInHouse,
        chartData
      });
    }
  };

  const getHouseGlowColor = (houseNum) => {
    if (highlightHouse !== houseNum) return null;
    return cosmicTheme ? 'rgba(255, 215, 0, 0.6)' : 'rgba(255, 107, 53, 0.6)';
  };

  const getHouseData = (houseNum) => {
    // Perfectly symmetrical coordinates for a 400x400 SVG
    const houseData = {
      1: { center: { x: 200, y: 100 }, path: "M200,0 L300,100 L200,200 L100,100 Z" },
      2: { center: { x: 100, y: 50 }, path: "M0,0 L200,0 L100,100 Z" },
      3: { center: { x: 50, y: 100 }, path: "M0,0 L100,100 L0,200 Z" },
      4: { center: { x: 100, y: 200 }, path: "M0,200 L100,100 L200,200 L100,300 Z" },
      5: { center: { x: 50, y: 300 }, path: "M0,200 L100,300 L0,400 Z" },
      6: { center: { x: 100, y: 350 }, path: "M0,400 L100,300 L200,400 Z" },
      7: { center: { x: 200, y: 300 }, path: "M200,200 L300,300 L200,400 L100,300 Z" },
      8: { center: { x: 300, y: 350 }, path: "M200,400 L300,300 L400,400 Z" },
      9: { center: { x: 350, y: 300 }, path: "M300,300 L400,200 L400,400 Z" },
      10: { center: { x: 300, y: 200 }, path: "M200,200 L300,100 L400,200 L300,300 Z" },
      11: { center: { x: 350, y: 100 }, path: "M300,100 L400,0 L400,200 Z" },
      12: { center: { x: 300, y: 50 }, path: "M200,0 L400,0 L300,100 Z" }
    };
    return houseData[houseNum];
  };

  const getRashiForHouse = (houseIndex) => {
    if (!chartData || !chartData.houses || !chartData.houses[houseIndex]) return houseIndex;
    if (rotatedAscendant !== null) {
      return (rotatedAscendant + houseIndex) % 12;
    }
    return chartData.houses[houseIndex].sign;
  };

  const getPlanetStatus = (planet) => {
    if (!chartData) return 'normal';
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna'].includes(planet.name)) return 'normal';
    const planets = chartData.planets || chartData;
    const planetData = planets[planet.name];
    if (!planetData) return 'normal';
    const planetSign = planetData.sign;
    const exaltationSigns = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6 };
    const debilitationSigns = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0 };
    if (exaltationSigns[planet.name] === planetSign) return 'exalted';
    if (debilitationSigns[planet.name] === planetSign) return 'debilitated';
    return 'normal';
  };

  const getPlanetColor = (planet, houseNumber) => {
    if (planet.name === 'InduLagna') return '#9c27b0';
    const status = getPlanetStatus(planet);
    if (status === 'exalted') return '#22c55e';
    if (status === 'debilitated') return '#ef4444';
    if (houseActivation?.[houseNumber]?.text) return houseActivation[houseNumber].text;
    return cosmicTheme
      ? themedChartText
      : (theme === 'dark' ? '#fff' : '#2d3436');
  };

  const getPlanetSymbolWithStatus = (planet) => {
    const status = getPlanetStatus(planet);
    if (!chartData) {
      let symbol = planet.symbol;
      if (status === 'exalted') symbol += '↑';
      if (status === 'debilitated') symbol += '↓';
      return symbol;
    }
    const planets = chartData.planets || chartData;
    const planetData = planets[planet.name];
    const isRetrograde = planetData?.retrograde;
    let symbol = planet.symbol;
    if (isRetrograde && planet.name !== 'Rahu' && planet.name !== 'Ketu') symbol += '(R)';
    if (status === 'exalted') symbol += '↑';
    if (status === 'debilitated') symbol += '↓';
    if (showKarakas && karakas && typeof karakas === 'object') {
      const karaka = Object.entries(karakas).find(([_, data]) => data?.planet === planet.name);
      if (karaka) {
        const karakaAbbr = { 'Atmakaraka': 'AK', 'Amatyakaraka': 'AmK', 'Bhratrukaraka': 'BK', 'Matrukaraka': 'MK', 'Putrakaraka': 'PK', 'Gnatikaraka': 'GK', 'Darakaraka': 'DK' }[karaka[0]];
        if (karakaAbbr) symbol += `(${karakaAbbr})`;
      }
    }
    return symbol;
  };

  const getNakshatra = (longitude) => {
    const nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return nakshatras[nakshatraIndex] || 'Unknown';
  };

  const getShortNakshatra = (longitude) => {
    const shortNakshatras = ['Ash', 'Bha', 'Kri', 'Roh', 'Mri', 'Ard', 'Pun', 'Pus', 'Asl', 'Mag', 'PPh', 'UPh', 'Has', 'Chi', 'Swa', 'Vis', 'Anu', 'Jye', 'Mul', 'PAs', 'UAs', 'Shr', 'Dha', 'Sha', 'PBh', 'UBh', 'Rev'];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return shortNakshatras[nakshatraIndex] || 'Unk';
  };

  const getNakshatraPada = (longitude) => {
    const lon = typeof longitude === 'number' && !Number.isNaN(longitude) ? longitude : 0;
    const degreeInNakshatra = lon % 13.333333;
    return Math.floor(degreeInNakshatra / 3.333333) + 1;
  };

  const formatDegree = (degree) => {
    if (typeof degree !== 'number' || Number.isNaN(degree)) return '0°';
    return `${Math.round(degree)}°`;
  };

  const formatDegreeFull = (degree) => {
    if (typeof degree !== 'number' || Number.isNaN(degree)) return '0.0000°';
    return degree.toFixed(4) + '°';
  };

  const getPlanetsInHouse = (houseIndex) => {
    if (!chartData) return [];
    const planets = chartData.planets || chartData;
    if (!planets || typeof planets !== 'object') return [];
    const rashiForThisHouse = getRashiForHouse(houseIndex);
    const houseNumber = houseIndex + 1;
    const useHousePlacement = chartData?._place_by_house === true;
    const planetsInHouse = [];
    const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi'];
    planetNames.forEach(name => {
      const data = planets[name];
      if (
        data
        && typeof data === 'object'
        && (useHousePlacement && typeof data.house === 'number'
          ? data.house === houseNumber
          : data.sign === rashiForThisHouse)
      ) {
        planetsInHouse.push({
          symbol: t(`planets.${name}`, name.substring(0, 2)),
          name: name,
          degree: typeof data.degree === 'number' ? data.degree : 0,
          longitude: data.longitude || 0,
          retrograde: !!data.retrograde,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          pada: getNakshatraPada(data.longitude || 0),
          formattedDegree: formatDegree(data.degree ?? 0),
          formattedDegreeFull: formatDegreeFull(data.degree ?? 0)
        });
      }
    });
    if (
      planets.InduLagna
      && (useHousePlacement && typeof planets.InduLagna.house === 'number'
        ? planets.InduLagna.house === houseNumber
        : planets.InduLagna.sign === rashiForThisHouse)
    ) {
      planetsInHouse.push({
        symbol: t('planets.InduLagna', 'IL'),
        name: 'InduLagna',
        degree: typeof planets.InduLagna.degree === 'number' ? planets.InduLagna.degree : 0,
        longitude: planets.InduLagna.longitude || 0,
        retrograde: !!planets.InduLagna.retrograde,
        nakshatra: getNakshatra(planets.InduLagna.longitude || 0),
        shortNakshatra: getShortNakshatra(planets.InduLagna.longitude || 0),
        pada: getNakshatraPada(planets.InduLagna.longitude || 0),
        formattedDegree: formatDegree(planets.InduLagna.degree ?? 0),
        formattedDegreeFull: formatDegreeFull(planets.InduLagna.degree ?? 0)
      });
    }
    return planetsInHouse;
  };

  const getTransitPlanetsInHouse = (houseIndex) => {
    const planets = transitOverlay?.planets;
    if (!planets || typeof planets !== 'object') return [];
    const rashiForThisHouse = getRashiForHouse(houseIndex);
    const names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
    return names.flatMap((name) => {
      const data = planets[name];
      if (!data || data.sign !== rashiForThisHouse) return [];
      const retrograde = !!data.retrograde && name !== 'Rahu' && name !== 'Ketu';
      return [{
        symbol: t(`planets.${name}`, name.substring(0, 2)),
        name,
        retrograde,
        sign: data.sign,
        bav: transitBav(bavBySign, name, data.sign),
        nakshatra: getNakshatra(data.longitude || 0),
        shortNakshatra: getShortNakshatra(data.longitude || 0),
        pada: getNakshatraPada(data.longitude || 0),
        formattedDegree: formatDegree(data.degree ?? 0),
      }];
    });
  };

  const collectNatalBoxes = (houseNumber, houseData, planetsInHouse) => {
    const occupied = planetsInHouse.map((planet, pIndex) => {
      const anchor = natalPlanetAnchor(houseNumber, houseData.center, planetsInHouse.length, pIndex);
      const dashaTag = dashaLevelSuffix(planet.name, dashaHighlight);
      const symbolFont = (planetsInHouse.length > 4 ? 10 : planetsInHouse.length > 2 ? 12 : 14) + (dashaTag ? 4 : 0);
      const degreeFont = planetsInHouse.length > 4 ? 7 : planetsInHouse.length > 2 ? 9 : 10;
      const symbol = getPlanetSymbolWithStatus(planet);
      const symbolY = anchor.y - 8;
      const tagFont = Math.max(6, Math.round(symbolFont * 0.42));
      const symbolHalf = textHalfWidth(symbol, symbolFont);
      const tagExtra = dashaTag ? textHalfWidth(dashaTag, tagFont) + 2 : 0;
      const degreeHalf = showDegreeNakshatra
        ? textHalfWidth(`${planet.formattedDegree} ${planet.shortNakshatra}`, degreeFont)
        : 0;
      const half = Math.max(symbolHalf + tagExtra, degreeHalf) + 6;
      const above = Math.ceil(symbolFont * 0.95) + (dashaTag ? tagFont + 1 : 2) + 2;
      const below = (showDegreeNakshatra ? 16 + Math.ceil(degreeFont * 0.5) + 2 : 4) + 2;
      return labelBox(anchor.x, symbolY, half, above, below);
    });
    const sign = signAnchor(houseNumber, houseData.center);
    const signLabel = String(getRashiForHouse(houseNumber - 1) + 1);
    const signHalf = textHalfWidth(signLabel, 18) + 4;
    occupied.push(labelBox(sign.x + signHalf, sign.y - 2, signHalf, 16, 8));
    if (houseNumber === 1) {
      const ascX = houseData.center.x + 25;
      const ascY = houseData.center.y + 35;
      occupied.push(labelBox(ascX, ascY, 28, 16, showDegreeNakshatra ? 26 : 8));
    }
    return occupied;
  };

  const savSpotFor = (houseNumber, houseData, planetsInHouse) => {
    if (signPointAt(signPoints, getRashiForHouse(houseNumber - 1)) == null) return null;
    return placeCircleClear(
      HOUSE_POLYGONS[houseNumber],
      collectNatalBoxes(houseNumber, houseData, planetsInHouse),
      SAV_RADIUS,
    );
  };

  const renderTransitOverlay = (houseNumber, houseData, planetsInHouse) => {
    const list = getTransitPlanetsInHouse(houseNumber - 1);
    const polygon = HOUSE_POLYGONS[houseNumber];
    if (!list.length || !polygon) return null;
    const occupied = collectNatalBoxes(houseNumber, houseData, planetsInHouse);
    const savSpot = savSpotFor(houseNumber, houseData, planetsInHouse);
    if (savSpot?.box) occupied.push(savSpot.box);

    const layout = placeTransitLabels(polygon, occupied, list.map((planet) => ({
      symbol: planet.symbol,
      retrograde: planet.retrograde,
      degree: planet.formattedDegree,
      nakshatra: planet.shortNakshatra,
      name: planet.name,
      bav: planet.bav,
    })), showDegreeNakshatra);
    if (!layout) return null;

    const transitColor = colors.accent || colors.primary;
    return (
      <>
        <ClipPath id={`transit-house-${houseNumber}`}>
          <Path d={houseData.path} />
        </ClipPath>
        <G pointerEvents="box-none" clipPath={`url(#transit-house-${houseNumber})`}>
          {layout.specs.map((spec, index) => {
            const slot = layout.placed[index];
            if (!slot) return null;
            return (
              <G key={`transit-${spec.text}-${index}`}>
                <SvgText
                  x={slot.x}
                  y={slot.y}
                  fontSize={spec.fontSize}
                  fill={transitColor}
                  fontWeight="800"
                  textAnchor="middle"
                  onPress={spec.name && onTransitPlanetPress ? () => onTransitPlanetPress(spec.name) : undefined}
                >
                  {spec.text}
                </SvgText>
                {spec.detail ? (
                  <SvgText
                    x={slot.x}
                    y={slot.y + (spec.detailOffset || 10)}
                    fontSize={spec.detailSize || 8}
                    fill={transitColor}
                    fontWeight="600"
                    textAnchor="middle"
                  >
                    {spec.detail}
                  </SvgText>
                ) : null}
              </G>
            );
          })}
        </G>
      </>
    );
  };

  const gridStrokeDash = hideInstructions && cosmicTheme
    ? 0
    : drawAnim.interpolate({
        inputRange: [0, 1],
        outputRange: [1000, 0],
      });
  const useStaticGrid = hideInstructions && cosmicTheme;
  const GridLine = useStaticGrid ? Line : AnimatedLine;
  const GridPolygon = useStaticGrid ? Polygon : AnimatedPolygon;
  const gridDashProps = useStaticGrid
    ? {}
    : { strokeDasharray: '600', strokeDashoffset: gridStrokeDash };
  const diamondDashProps = useStaticGrid
    ? {}
    : { strokeDasharray: '1200', strokeDashoffset: gridStrokeDash };

  return (
    <View
      style={[
        styles.container,
        size ? { width: size, height: size, alignSelf: 'center' } : null,
      ]}
    >
      <Svg
        viewBox="0 0 400 400"
        width={size || '100%'}
        height={size || '100%'}
        overflow="visible"
        preserveAspectRatio="xMidYMid meet"
        style={[styles.svg, size ? { width: size, height: size } : null]}
      >
        <Defs>
          <LinearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            {cosmicTheme ? (
              theme === 'dark' ? [
                <Stop key="0" offset="0%" stopColor="rgba(255, 255, 255, 0.15)" />,
                <Stop key="50" offset="50%" stopColor="rgba(255, 255, 255, 0.08)" />,
                <Stop key="100" offset="100%" stopColor="rgba(255, 255, 255, 0.12)" />
              ] : [
                <Stop key="0" offset="0%" stopColor="rgba(249, 115, 22, 0.15)" />,
                <Stop key="50" offset="50%" stopColor="rgba(249, 115, 22, 0.08)" />,
                <Stop key="100" offset="100%" stopColor="rgba(249, 115, 22, 0.12)" />
              ]
            ) : [
                <Stop key="0" offset="0%" stopColor="rgba(255, 255, 255, 0.9)" />,
                <Stop key="50" offset="50%" stopColor="rgba(248, 250, 252, 0.95)" />,
                <Stop key="100" offset="100%" stopColor="rgba(241, 245, 249, 0.9)" />
              ]}
          </LinearGradient>
        </Defs>

        {/* Outer square. Inset so the stroke stays inside the SVG and is not clipped. */}
        <Rect
          x="1.5"
          y="1.5"
          width={CHART_SIZE - 3}
          height={CHART_SIZE - 3}
          fill="none"
          stroke={cosmicTheme ? (colors.chartLineStrong || resolvedGridLine) : '#e91e63'}
          strokeWidth={cosmicTheme ? 2.5 : 3}
          pointerEvents="none"
        />

        {/* Inner diamond border */}
        <GridPolygon
          points={CHART_DIAMOND_POINTS}
          fill="none"
          stroke={cosmicTheme ? resolvedGridLine : "#ff6f00"}
          strokeWidth={cosmicTheme ? resolvedGridLineWidth : "3"}
          {...diamondDashProps}
          pointerEvents="none"
        />

        {/* Diagonal lines */}
        <G>
          <GridLine
            x1="0" y1="0" x2={CHART_SIZE} y2={CHART_SIZE}
            stroke={cosmicTheme ? resolvedGridLine : "#ff8a65"}
            strokeWidth={resolvedGridLineWidth}
            {...gridDashProps}
            pointerEvents="none"
          />
          <GridLine
            x1={CHART_SIZE} y1="0" x2="0" y2={CHART_SIZE}
            stroke={cosmicTheme ? resolvedGridLine : "#ff8a65"}
            strokeWidth={resolvedGridLineWidth}
            {...gridDashProps}
            pointerEvents="none"
          />
        </G>

        {/* Houses */}
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const houseIndex = houseNumber - 1;
          const rashiIndex = getRashiForHouse(houseIndex);
          const planetsInHouse = getPlanetsInHouse(houseIndex);
          const houseData = getHouseData(houseNumber);
          const activatedHouseText = houseActivation?.[houseNumber]?.text;

          return (
            <G key={houseNumber}>
              {highlightHouse === houseNumber ? (
                <Path
                  d={houseData.path}
                  fill={highlightFill || "rgba(255,215,0,0.18)"}
                  stroke={highlightColor || "#ffd700"}
                  strokeWidth="2"
                  strokeLinejoin="miter"
                  pointerEvents="none"
                />
              ) : null}
              {houseActivation?.[houseNumber] ? (
                <Path
                  d={houseData.path}
                  fill={houseActivation[houseNumber].fill}
                  opacity={houseActivation[houseNumber].state === 'dormant' ? 0 : 0.42}
                  pointerEvents="none"
                />
              ) : null}
              {houseActivation?.[houseNumber] ? (
                <Circle
                  cx={HOUSE_DOT_POINTS[houseNumber].x}
                  cy={HOUSE_DOT_POINTS[houseNumber].y}
                  r="6"
                  fill={houseActivation[houseNumber].dot}
                  stroke="#ffffff"
                  strokeWidth="1.5"
                  pointerEvents="none"
                />
              ) : null}
              {highlightHouse === houseNumber && glowAnimation && (
                <Circle cx={houseData.center.x} cy={houseData.center.y} r="60" fill={getHouseGlowColor(houseNumber)} opacity={glowAnimation} />
              )}

              <SvgText
                x={signAnchor(houseNumber, houseData.center).x}
                y={signAnchor(houseNumber, houseData.center).y}
                fontSize="18"
                fill={activatedHouseText || (cosmicTheme ?
                  (rashiIndex === (chartData?.houses?.[0]?.sign ?? 0) ? colors.primary : themedChartTextMuted) :
                  (rashiIndex === (chartData?.houses?.[0]?.sign ?? 0) ? "#e91e63" : (theme === 'dark' ? "#fff" : "#333")))}
                fontWeight={rashiIndex === (chartData?.houses?.[0]?.sign ?? 0) ? "900" : "bold"}>
                {rashiIndex + 1}
              </SvgText>

              {(() => {
                const savSpot = savSpotFor(houseNumber, houseData, planetsInHouse);
                if (!savSpot) return null;
                return (
                  <G pointerEvents="none">
                    <Circle
                      cx={savSpot.x}
                      cy={savSpot.y}
                      r={savSpot.radius}
                      fill={cosmicTheme ? colors.chartSurface : (theme === 'dark' ? '#111827' : '#ffffff')}
                      stroke={cosmicTheme ? (colors.chartLineStrong || colors.chartLine) : (theme === 'dark' ? '#94a3b8' : '#e91e63')}
                      strokeWidth="1.25"
                    />
                    <SvgText
                      x={savSpot.x}
                      y={savSpot.y + 4}
                      fontSize="11"
                      fill={themedChartText}
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {signPointAt(signPoints, rashiIndex)}
                    </SvgText>
                  </G>
                );
              })()}

              {houseNumber === 1 && (
                <G>
                  <SvgText x={houseData.center.x + 25} y={houseData.center.y + 35} fontSize="12" fill={activatedHouseText || (cosmicTheme ? colors.primary : "#e91e63")} fontWeight="900" textAnchor="middle">ASC</SvgText>
                  {(chartData?.ascendant ?? null) != null && (
                    <SvgText x={houseData.center.x + 25} y={houseData.center.y + 50} fontSize="8" fill={activatedHouseText || (cosmicTheme ? themedChartTextMuted : (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "#666"))} fontWeight="500" textAnchor="middle">
                      {formatDegree(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                    </SvgText>
                  )}
                </G>
              )}

              {planetsInHouse.map((planet, pIndex) => {
                const totalPlanets = planetsInHouse.length;
                const { x: planetX, y: planetY } = natalPlanetAnchor(
                  houseNumber,
                  houseData.center,
                  totalPlanets,
                  pIndex,
                );

                const dashaTag = dashaLevelSuffix(planet.name, dashaHighlight);
                const planetFont = (showKarakas
                  ? (totalPlanets > 4 ? 8 : totalPlanets > 2 ? 10 : 11)
                  : (totalPlanets > 4 ? 10 : totalPlanets > 2 ? 12 : 14)) + (dashaTag ? 4 : 0);
                const symbol = getPlanetSymbolWithStatus(planet);
                const paint = dashaTag ? dashaPaint(colors) : null;
                return (
                  <G key={pIndex}>
                    <SvgText
                      x={planetX}
                      y={planetY - 8}
                      fontSize={planetFont}
                      fill={paint ? paint.fill : getPlanetColor(planet, houseNumber)}
                      fontWeight="900"
                      textAnchor="middle"
                      onPress={() => handlePlanetPress(planet)}>
                      {symbol}
                    </SvgText>
                    {dashaTag ? (
                      <SvgText
                        x={planetX + textHalfWidth(symbol, planetFont)}
                        y={planetY - 8 - Math.round(planetFont * 0.55)}
                        fontSize={Math.max(6, Math.round(planetFont * 0.42))}
                        fill={paint.glow}
                        fontWeight="700"
                        textAnchor="start"
                        pointerEvents="none"
                      >
                        {dashaTag}
                      </SvgText>
                    ) : null}
                    {chartType === 'transit' && transitBav(bavBySign, planet.name, rashiIndex) != null ? (
                      <SvgText
                        x={planetX + textHalfWidth(symbol, planetFont) + 2}
                        y={planetY - 8}
                        fontSize={Math.max(7, Math.round(planetFont * 0.62))}
                        fill={themedChartTextMuted}
                        fontWeight="700"
                        textAnchor="start"
                        pointerEvents="none"
                      >
                        {transitBav(bavBySign, planet.name, rashiIndex)}
                      </SvgText>
                    ) : null}
                    {showDegreeNakshatra && (
                      <SvgText
                        x={planetX}
                        y={planetY + 8}
                        fontSize={totalPlanets > 4 ? "7" : totalPlanets > 2 ? "9" : "10"}
                        fill={paint ? paint.fill : (activatedHouseText || (cosmicTheme ? themedChartTextMuted : "#666"))}
                        fontWeight="500"
                        textAnchor="middle"
                        onPress={() => handlePlanetPress(planet)}>
                        {planet.formattedDegree} {planet.shortNakshatra}
                      </SvgText>
                    )}
                  </G>
                );
              })}
              {renderTransitOverlay(houseNumber, houseData, planetsInHouse)}
            </G>
          );
        })}

        {/* House Hit Areas - Moved to end to be on top */}
        <G pointerEvents="auto">
          {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNum) => (
            <Path
              key={`hit-${houseNum}`}
              d={getHouseData(houseNum).path}
              fill="transparent"
              onPress={() => handleHousePressInternal(houseNum)}
            />
          ))}
        </G>
      </Svg>

      {tooltip.show && (
        <View style={[styles.tooltip, { backgroundColor: theme === 'dark' ? 'rgba(233, 30, 99, 0.9)' : 'rgba(249, 115, 22, 0.9)' }]}>
          <Text style={styles.tooltipText}>{tooltip.text}</Text>
        </View>
      )}

      {!hideInstructions && (
        <Text style={[
          styles.instructionText,
          cosmicTheme && styles.instructionTextCosmic,
          Platform.OS === 'web' && styles.instructionTextWeb,
          cosmicTheme && Platform.OS === 'web' && styles.instructionTextCosmicWeb,
          { color: theme === 'dark' ? (cosmicTheme ? 'rgba(255, 255, 255, 0.7)' : '#666') : (cosmicTheme ? 'rgba(0, 0, 0, 0.6)' : '#666') },
        ]}>
          Touch any house for deep insights
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: Platform.select({
    // Prefer aspectRatio over height:% so the chart stays visible before size is measured.
    web: { width: '100%', aspectRatio: 1, alignSelf: 'stretch', position: 'relative' },
    default: { flex: 1, width: '100%', aspectRatio: 1 },
  }),
  svg: Platform.select({
    web: { width: '100%', aspectRatio: 1, display: 'block' },
    default: { width: '100%', height: '100%', aspectRatio: 1 },
  }),
  tooltip: { position: 'absolute', top: 20, left: 20, right: 20, padding: 12, borderRadius: 12, alignItems: 'center', zIndex: 100 },
  tooltipText: { color: 'white', fontSize: 14, fontWeight: 'bold', textAlign: 'center' },
  instructionText: { textAlign: 'center', fontSize: 12, fontStyle: 'italic', marginTop: 12, marginBottom: 18 },
  // Keep the hint outside the square chart instead of letting the fixed-size
  // SVG container overlap it when the chart is rendered in the cosmic layout.
  instructionTextCosmic: { position: 'absolute', left: 0, right: 0, bottom: -24, marginTop: 0, marginBottom: 0 },
  instructionTextWeb: { position: 'absolute', left: 0, right: 0, bottom: 8, marginTop: 0, marginBottom: 0 },
  instructionTextCosmicWeb: { bottom: -24 },
});

export default NorthIndianChart;
