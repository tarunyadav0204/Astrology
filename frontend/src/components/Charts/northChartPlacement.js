// Pack planet labels inside one North Indian house so names, status marks
// such as (R) and (c), and degree lines stay off the diamond borders and
// off each other.

const FRAME = 400;
const FRAME_PAD = 4;
const EDGE = 3.5;

export const HOUSE_POLYGONS = {
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

export const textHalfWidth = (text, fontSize, factor = 0.36) => {
  let units = 0;
  for (const char of String(text || '')) {
    units += (char === '(' || char === ')' || char === '↑' || char === '↓' || char === "'" || char === '°')
      ? 0.55
      : 1;
  }
  return Math.max(4, units * fontSize * factor);
};

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

const boxInside = (box, polygon) => {
  const inset = {
    left: box.left - EDGE,
    right: box.right + EDGE,
    top: box.top - EDGE,
    bottom: box.bottom + EDGE,
  };
  return [
    [inset.left, inset.top],
    [inset.right, inset.top],
    [inset.left, inset.bottom],
    [inset.right, inset.bottom],
    [(box.left + box.right) / 2, (box.top + box.bottom) / 2],
  ].every(([x, y]) => pointInPolygon(x, y, polygon));
};

const fitsFrame = (box) => (
  box.left >= FRAME_PAD
  && box.right <= FRAME - FRAME_PAD
  && box.top >= FRAME_PAD
  && box.bottom <= FRAME - FRAME_PAD
);

export const signOccupied = (sign, label, font = 15) => {
  const half = textHalfWidth(String(label), font, 0.5);
  const pad = 3;
  const halfH = font * 0.55;
  return {
    left: sign.x - half - pad,
    right: sign.x + half + pad,
    top: sign.y - halfH - pad,
    bottom: sign.y + halfH + pad,
  };
};

const polygonCentroid = (polygon) => {
  const count = polygon.length || 1;
  return {
    x: polygon.reduce((sum, point) => sum + point[0], 0) / count,
    y: polygon.reduce((sum, point) => sum + point[1], 0) / count,
  };
};

const boundsOf = (polygon) => {
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  };
};

const isWideHouse = (polygon) => {
  const bounds = boundsOf(polygon);
  return (bounds.maxX - bounds.minX) > (bounds.maxY - bounds.minY) * 1.25;
};

const fontSchedules = (planets, hasAsc, showDegree, wide) => {
  const count = planets.length + (hasAsc ? 1 : 0);
  const longest = planets.reduce((max, planet) => Math.max(max, String(planet.symbol || '').length), hasAsc ? 3 : 0);
  let start = 16;
  if (longest >= 9 || count >= 6) start = 13;
  else if (longest >= 7 || count >= 5) start = 14;
  else if (count >= 4) start = 15;
  const schedules = [];
  if (showDegree) {
    const short = [];
    const largeStack = [];
    const smallStack = [];
    // Wide triangles cannot hold three full two-line labels. A larger symbol
    // with the degree under it is tried before any stacked layout. Other
    // houses still try a full stack first, then this large degree-only size
    // before the type is allowed to collapse.
    if (count <= 4) {
      for (let symbolFont = 17; symbolFont >= 12; symbolFont -= 1) {
        short.push({ symbolFont, detailFont: 7, mode: 'short' });
      }
    }
    for (let symbolFont = start; symbolFont >= 15; symbolFont -= 1) {
      largeStack.push({ symbolFont, detailFont: Math.max(7, symbolFont - 6), mode: 'stack' });
    }
    for (let symbolFont = 14; symbolFont >= 13; symbolFont -= 1) {
      smallStack.push({ symbolFont, detailFont: Math.max(7, symbolFont - 6), mode: 'stack' });
    }
    for (let symbolFont = 12; symbolFont >= 10; symbolFont -= 1) {
      smallStack.push({ symbolFont, detailFont: Math.max(6.5, symbolFont - 6), mode: 'stack' });
    }
    schedules.push(...(wide ? [...short, ...largeStack, ...smallStack] : [...largeStack, ...short, ...smallStack]));
    for (let symbolFont = 12; symbolFont >= 8; symbolFont -= 2) {
      schedules.push({ symbolFont, detailFont: Math.max(6.5, symbolFont - 5), mode: 'line' });
      schedules.push({ symbolFont, detailFont: Math.max(6.5, symbolFont - 4), mode: 'short' });
    }
    schedules.push({ symbolFont: 10, detailFont: 7, mode: 'inline' });
    schedules.push({ symbolFont: 8, detailFont: 6.5, mode: 'inline' });
  } else {
    // No degree line, so the name can stay as large as the house allows.
    for (let symbolFont = 17; symbolFont >= 13; symbolFont -= 1) {
      schedules.push({ symbolFont, detailFont: 0, mode: 'none' });
    }
  }
  schedules.push({ symbolFont: Math.min(start, 12), detailFont: 0, mode: 'none' });
  schedules.push({ symbolFont: 8, detailFont: 0, mode: 'none' });
  return schedules;
};

const detailLinesFor = (item, mode, showDegree) => {
  if (!showDegree || mode === 'none') return [];
  const degree = item.degree || '';
  const nakshatra = item.nakshatra || '';
  if (mode === 'inline' || mode === 'short') return degree ? [degree] : [];
  if (mode === 'line') {
    const text = [degree, nakshatra].filter(Boolean).join(' ');
    return text ? [text] : [];
  }
  return [degree, nakshatra].filter(Boolean);
};

const blockMetrics = (symbol, lines, symbolFont, detailFont, inline) => {
  const symbolHalf = textHalfWidth(symbol, symbolFont);
  const above = Math.ceil(symbolFont * 0.72) + 1;
  const symbolBelow = Math.ceil(symbolFont * 0.22);
  if (inline && lines[0]) {
    const degreeWidth = textHalfWidth(lines[0], detailFont, 0.33) * 2;
    return {
      leftW: symbolHalf + 2,
      rightW: symbolHalf + degreeWidth + 6,
      above: Math.max(above, Math.ceil(detailFont * 0.8) + 1),
      below: Math.max(symbolBelow, Math.ceil(detailFont * 0.28)),
      symbolFont,
      detailFont,
      mode: 'inline',
      lines,
      line1: 0,
      line2: 0,
    };
  }
  if (!lines.length) {
    return {
      leftW: symbolHalf + 2,
      rightW: symbolHalf + 2,
      above,
      below: symbolBelow + 1,
      symbolFont,
      detailFont: 0,
      mode: 'none',
      lines: [],
      line1: 0,
      line2: 0,
    };
  }
  const line1 = Math.ceil(symbolBelow + detailFont * 0.8 + 2);
  const line2 = lines[1] ? line1 + Math.ceil(detailFont + 1) : 0;
  const last = line2 || line1;
  const half = Math.max(
    symbolHalf,
    ...lines.map((line) => textHalfWidth(line, detailFont, 0.33)),
  ) + 2;
  return {
    leftW: half,
    rightW: half,
    above,
    below: last + Math.ceil(detailFont * 0.28),
    symbolFont,
    detailFont,
    mode: lines.length > 1 ? 'stack' : 'short',
    lines,
    line1,
    line2,
  };
};

const candidatesFor = (polygon, step) => {
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  const minX = Math.max(FRAME_PAD, Math.min(...xs));
  const maxX = Math.min(FRAME - FRAME_PAD, Math.max(...xs));
  const minY = Math.max(FRAME_PAD, Math.min(...ys));
  const maxY = Math.min(FRAME - FRAME_PAD, Math.max(...ys));
  const points = [];
  for (let x = minX; x <= maxX; x += step) {
    for (let y = minY; y <= maxY; y += step) {
      if (pointInPolygon(x, y, polygon)) points.push({ x, y });
    }
  }
  return points;
};

const candidateCache = new Map();
const cachedCandidates = (polygon, step) => {
  const key = `${step}:${polygon.map((point) => point.join(',')).join(';')}`;
  if (!candidateCache.has(key)) candidateCache.set(key, candidatesFor(polygon, step));
  return candidateCache.get(key);
};

const boxAt = (x, y, spec) => ({
  left: x - spec.leftW,
  right: x + spec.rightW,
  top: y - spec.above,
  bottom: y + spec.below,
});

const packOne = (candidates, polygon, blocked, spec, prefer, minGap) => {
  let best = null;
  candidates.forEach((candidate) => {
    const box = boxAt(candidate.x, candidate.y, spec);
    if (!fitsFrame(box) || !boxInside(box, polygon)) return;
    const gap = blocked.length
      ? blocked.reduce((min, rect) => Math.min(min, boxGap(box, rect)), Infinity)
      : 8;
    if (gap < minGap) return;
    const dist = Math.hypot(candidate.x - prefer.x, candidate.y - prefer.y);
    if (!best || dist < best.dist - 0.1 || (Math.abs(dist - best.dist) <= 0.1 && gap > best.gap)) {
      best = { x: candidate.x, y: candidate.y, gap, dist, box, ...spec };
    }
  });
  return best;
};

const preferFor = (index, count, center, wide, rowGap) => {
  if (count <= 1) return center;
  if (wide || count >= 4) {
    return {
      x: center.x,
      y: center.y - ((count - 1) * rowGap) / 2 + index * rowGap,
    };
  }
  return {
    x: center.x + (index % 2 ? 24 : -24),
    y: center.y - rowGap * 0.35 + Math.floor(index / 2) * rowGap,
  };
};

const centerRange = (polygon, y, spec, blocked, minGap) => {
  const bounds = boundsOf(polygon);
  let min = null;
  let max = null;
  for (let x = bounds.minX; x <= bounds.maxX; x += 2) {
    const box = boxAt(x, y, spec);
    if (!fitsFrame(box) || !boxInside(box, polygon)) continue;
    const gap = blocked.length
      ? blocked.reduce((smallest, rect) => Math.min(smallest, boxGap(box, rect)), Infinity)
      : 8;
    if (gap < minGap) continue;
    if (min == null) min = x;
    max = x;
  }
  return min == null ? null : { min, max };
};

const placeCenters = (specs, y, polygon, blocked, minGap) => {
  const ranges = specs.map((spec) => centerRange(polygon, y, spec, blocked, minGap));
  if (ranges.some((range) => !range)) return null;
  if (specs.length === 1) {
    const x = (ranges[0].min + ranges[0].max) / 2;
    const box = boxAt(x, y, specs[0]);
    if (!fitsFrame(box) || !boxInside(box, polygon)) return null;
    return [{ x, y, gap: minGap, box, ...specs[0] }];
  }
  const centers = [];
  for (let index = 0; index < specs.length; index += 1) {
    const needed = index === 0
      ? ranges[index].min
      : centers[index - 1] + specs[index - 1].rightW + specs[index].leftW + minGap;
    const x = Math.max(ranges[index].min, needed);
    const box = boxAt(x, y, specs[index]);
    if (x > ranges[index].max || !fitsFrame(box) || !boxInside(box, polygon)) return null;
    centers.push(x);
  }
  const last = centers.length - 1;
  const slack = ranges[last].max - centers[last];
  const extra = slack / Math.max(last, 1);
  const spread = centers.map((x, index) => x + extra * index);
  const spots = spread.map((x, index) => {
    const box = boxAt(x, y, specs[index]);
    return { x, y, gap: minGap, box, ...specs[index] };
  });
  if (spots.some((spot) => !fitsFrame(spot.box) || !boxInside(spot.box, polygon))) {
    return centers.map((x, index) => {
      const box = boxAt(x, y, specs[index]);
      return { x, y, gap: minGap, box, ...specs[index] };
    });
  }
  return spots;
};

// A single row of long status marks, such as Sa(R)(c), only fits at a tiny
// size. Two bands use the empty part of the triangle and keep the names large.
const tryTwoRows = (specs, polygon, signBox, signLow, bounds, center, minGap) => {
  if (specs.length !== 3) return null;
  const widths = specs.map((spec) => spec.leftW + spec.rightW);
  const widest = widths.indexOf(Math.max(...widths));
  const others = [0, 1, 2].filter((index) => index !== widest);
  const plans = [
    { edge: others, inner: [widest] },
    { edge: [widest], inner: others },
  ];
  const yStart = signLow ? bounds.minY + 4 : bounds.maxY - 4;
  const yLimit = signLow ? center.y + 18 : center.y - 18;
  const yStep = signLow ? 2 : -2;
  const towardSign = (y) => (signLow ? y <= yLimit : y >= yLimit);

  for (const plan of plans) {
    for (let y1 = yStart; towardSign(y1); y1 += yStep) {
      const edgeSpots = placeCenters(plan.edge.map((index) => specs[index]), y1, polygon, [signBox], minGap);
      if (!edgeSpots) continue;
      const blocked = [signBox, ...edgeSpots.map((spot) => spot.box)];
      for (let y2 = y1 + yStep; towardSign(y2); y2 += yStep) {
        const innerSpots = placeCenters(plan.inner.map((index) => specs[index]), y2, polygon, blocked, minGap);
        if (!innerSpots) continue;
        const placed = new Array(specs.length);
        plan.edge.forEach((index, spotIndex) => { placed[index] = edgeSpots[spotIndex]; });
        plan.inner.forEach((index, spotIndex) => { placed[index] = innerSpots[spotIndex]; });
        return placed;
      }
    }
  }
  return null;
};

// Top and bottom triangles are wide and short. A vertical stack leaves the
// wings empty and then shrinks the type. Lay the planets across the wide edge.
const tryWideRow = (opts, fonts, minGap) => {
  const { polygon, planets, showDegree } = opts;
  if (!isWideHouse(polygon) || planets.length < 2) return null;
  const specs = planets.map((planet) => {
    const lines = detailLinesFor(planet, fonts.mode, showDegree);
    return blockMetrics(planet.symbol, lines, fonts.symbolFont, fonts.detailFont, fonts.mode === 'inline');
  });
  const signBox = signOccupied(opts.sign, opts.signLabel);
  const bounds = boundsOf(polygon);
  const center = polygonCentroid(polygon);
  const signLow = opts.sign.y >= center.y;
  const yStart = signLow ? bounds.minY + 4 : bounds.maxY - 4;
  const yEnd = signLow ? center.y + 8 : center.y - 8;
  const yStep = signLow ? 2 : -2;

  for (let y = yStart; signLow ? y <= yEnd : y >= yEnd; y += yStep) {
    const placed = placeCenters(specs, y, polygon, [signBox], minGap);
    if (!placed) continue;
    return {
      planets: placed,
      asc: null,
      occupied: [signBox, ...placed.map((spot) => spot.box)],
      minGap,
      fonts,
    };
  }
  const stacked = tryTwoRows(specs, polygon, signBox, signLow, bounds, center, minGap);
  if (!stacked) return null;
  return {
    planets: stacked,
    asc: null,
    occupied: [signBox, ...stacked.map((spot) => spot.box)],
    minGap,
    fonts,
  };
};

const tryLayout = (opts, fonts, candidates, minGap) => {
  const { polygon, planets, showDegree } = opts;
  if (isWideHouse(polygon) && planets.length >= 2 && !opts.asc) {
    return tryWideRow(opts, fonts, minGap);
  }
  const center = polygonCentroid(polygon);
  const blocked = [signOccupied(opts.sign, opts.signLabel)];
  let asc = null;
  if (opts.asc) {
    const lines = detailLinesFor(opts.asc, fonts.mode, showDegree);
    const spec = blockMetrics(opts.asc.label || 'ASC', lines, fonts.symbolFont, fonts.detailFont, fonts.mode === 'inline');
    const bias = opts.asc.bias || { x: 0, y: 0 };
    const spot = packOne(
      candidates,
      polygon,
      blocked,
      spec,
      { x: center.x + bias.x, y: center.y + bias.y },
      minGap,
    );
    if (!spot) return null;
    asc = spot;
    blocked.push(spot.box);
  }
  const wide = planets.some((planet) => String(planet.symbol || '').length >= 7);
  const rowGap = fonts.symbolFont + (fonts.mode === 'stack' ? fonts.detailFont * 2 + 8 : fonts.mode === 'none' || fonts.mode === 'inline' ? 6 : fonts.detailFont + 8);
  const placed = [];
  for (let index = 0; index < planets.length; index += 1) {
    const planet = planets[index];
    const lines = detailLinesFor(planet, fonts.mode, showDegree);
    const spec = blockMetrics(planet.symbol, lines, fonts.symbolFont, fonts.detailFont, fonts.mode === 'inline');
    const spot = packOne(
      candidates,
      polygon,
      blocked,
      spec,
      preferFor(index, planets.length, center, wide, rowGap),
      minGap,
    );
    if (!spot) return null;
    placed.push(spot);
    blocked.push(spot.box);
  }
  const gaps = placed.map((spot) => spot.gap);
  if (asc) gaps.push(asc.gap);
  return {
    planets: placed,
    asc,
    occupied: blocked,
    minGap: gaps.length ? Math.min(...gaps) : 8,
    fonts,
  };
};

export const layoutWebHouse = (opts) => {
  const schedules = fontSchedules(opts.planets, !!opts.asc, !!opts.showDegree, isWideHouse(opts.polygon));
  let best = null;
  for (const fonts of schedules) {
    for (const minGap of [3, 1]) {
      for (const step of [4, 2]) {
        const placed = tryLayout(opts, fonts, cachedCandidates(opts.polygon, step), minGap);
        if (!placed) continue;
        if (minGap >= 3) return placed;
        if (!best || placed.fonts.symbolFont > best.fonts.symbolFont) best = placed;
        break;
      }
      if (best && best.fonts === fonts) break;
    }
    if (best) return best;
  }
  const tiny = { symbolFont: 8, detailFont: 0, mode: 'none' };
  const forced = tryLayout(opts, tiny, cachedCandidates(opts.polygon, 2), -999);
  return forced || {
    planets: [],
    asc: null,
    occupied: [signOccupied(opts.sign, opts.signLabel)],
    minGap: 8,
    fonts: tiny,
  };
};

export const boxesOverlap = (boxes, minGap = 1) => {
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      if (boxGap(boxes[i], boxes[j]) < minGap) return true;
    }
  }
  return false;
};
