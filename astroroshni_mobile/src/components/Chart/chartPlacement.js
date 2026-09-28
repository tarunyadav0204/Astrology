// Pack natal labels inside one North Indian house so the sign number,
// ascendant, and planet names do not sit on each other.

const FRAME = 400;
const FRAME_PAD = 5;

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

const textHalfWidth = (text, fontSize) => Math.max(4, String(text || '').length * fontSize * 0.36);

const boxInside = (box, polygon) => (
  [
    [box.left, box.top],
    [box.right, box.top],
    [box.left, box.bottom],
    [box.right, box.bottom],
    [(box.left + box.right) / 2, (box.top + box.bottom) / 2],
  ].every(([x, y]) => pointInPolygon(x, y, polygon))
);

const fitsFrame = (box) => (
  box.left >= FRAME_PAD
  && box.right <= FRAME - FRAME_PAD
  && box.top >= FRAME_PAD
  && box.bottom <= FRAME - FRAME_PAD
);

export const signOccupied = (sign, label, font = 18) => {
  const width = textHalfWidth(String(label), font) * 2;
  const pad = 2;
  return {
    left: sign.x - pad,
    right: sign.x + width + pad,
    top: sign.y - font * 0.82 - pad,
    bottom: sign.y + font * 0.28 + pad,
  };
};

const fontSchedules = (count) => {
  const stacked = (count >= 5
    ? [[11, 8, 11], [10, 7, 10], [9, 7, 9]]
    : count >= 3
      ? [[12, 9, 12], [11, 8, 10], [10, 7, 10]]
      : [[14, 10, 12], [12, 9, 11], [11, 8, 10]]
  ).map(([symbolFont, degreeFont, ascFont]) => ({ symbolFont, degreeFont, ascFont, inline: false, short: false }));
  if (count < 3) return stacked;
  return stacked.concat([
    { symbolFont: 9, degreeFont: 7, ascFont: 9, inline: true, short: false },
    { symbolFont: 8, degreeFont: 7, ascFont: 8, inline: true, short: true },
  ]);
};

const blockMetrics = (symbol, degreeText, extras, symbolFont, degreeFont, showDegree, inline) => {
  const tagFont = Math.max(6, Math.round(symbolFont * 0.42));
  const symbolHalf = textHalfWidth(symbol, symbolFont);
  const extra = Math.max(
    0,
    ...extras.filter(Boolean).map((text) => textHalfWidth(text, tagFont) * 2 + 2),
  );
  const degree = showDegree && degreeText ? String(degreeText) : '';
  const degreeHalf = degree ? textHalfWidth(degree, degreeFont) : 0;
  const tagRise = Math.round(symbolFont * 0.55);
  const above = Math.max(symbolFont * 0.86, extras.some(Boolean) ? tagRise + tagFont * 0.86 : 0) + 1;
  if (inline && degree) {
    return {
      leftW: symbolHalf + 2,
      rightW: Math.max(symbolHalf + extra, symbolHalf + degreeHalf * 2 + 4) + 2,
      above,
      below: Math.ceil(symbolFont * 0.3) + 1,
      symbolFont,
      degreeFont,
      degreeGap: 0,
      inline: true,
      tagFont,
      tagRise,
    };
  }
  const degreeGap = degree ? Math.ceil(symbolFont * 0.22 + 2 + degreeFont * 0.78) : 0;
  const half = Math.max(symbolHalf + extra, degreeHalf) + 2;
  return {
    leftW: half,
    rightW: half,
    above,
    below: degree ? degreeGap + Math.ceil(degreeFont * 0.28) : 3,
    symbolFont,
    degreeFont: degree ? degreeFont : 0,
    degreeGap,
    inline: false,
    tagFont,
    tagRise,
  };
};

const candidatesFor = (polygon) => {
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  const minX = Math.max(FRAME_PAD, Math.min(...xs));
  const maxX = Math.min(FRAME - FRAME_PAD, Math.max(...xs));
  const minY = Math.max(FRAME_PAD, Math.min(...ys));
  const maxY = Math.min(FRAME - FRAME_PAD, Math.max(...ys));
  const points = [];
  for (let x = minX; x <= maxX; x += 4) {
    for (let y = minY; y <= maxY; y += 4) {
      if (pointInPolygon(x, y, polygon)) points.push({ x, y });
    }
  }
  return points;
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

const ascPrefer = (polygon, center, sign) => {
  let far = polygon[0];
  let best = -1;
  polygon.forEach((point) => {
    const dist = Math.hypot(point[0] - sign.x, point[1] - sign.y);
    if (dist > best) {
      best = dist;
      far = point;
    }
  });
  const dx = center.x - far[0];
  const dy = center.y - far[1];
  const len = Math.hypot(dx, dy) || 1;
  const shift = Math.min(46, len * 0.5);
  return { x: far[0] + (dx / len) * shift, y: far[1] + (dy / len) * shift };
};

const tryLayout = (opts, fonts, minGap) => {
  const { polygon, center, sign, planets, showDegree } = opts;
  const candidates = candidatesFor(polygon);
  const blocked = [signOccupied(sign, opts.signLabel)];
  let asc = null;
  if (opts.asc) {
    const degree = showDegree ? (fonts.short ? opts.asc.shortDegree : opts.asc.degreeText) : '';
    const spec = blockMetrics(opts.asc.label || 'ASC', degree, [], fonts.ascFont, Math.max(7, fonts.degreeFont - 1), !!degree, fonts.inline);
    const spot = packOne(candidates, polygon, blocked, spec, ascPrefer(polygon, center, sign), minGap);
    if (!spot) return null;
    asc = spot;
    blocked.push(spot.box);
  }
  const placed = [];
  const rowGap = fonts.symbolFont + fonts.degreeFont + 10;
  planets.forEach((planet, index) => {
    const spec = blockMetrics(
      planet.symbol,
      fonts.short ? planet.shortDegree : planet.degreeText,
      [planet.tag, planet.role, planet.neecha],
      fonts.symbolFont,
      fonts.degreeFont,
      showDegree,
      fonts.inline,
    );
    const prefer = planets.length === 1
      ? center
      : {
        x: center.x + (index % 2 ? 34 : -34),
        y: center.y - rowGap * 0.35 + Math.floor(index / 2) * rowGap,
      };
    const spot = packOne(candidates, polygon, blocked, spec, prefer, minGap);
    if (!spot) return;
    placed.push(spot);
    blocked.push(spot.box);
  });
  if (placed.length !== planets.length) return null;
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

export const layoutNatalHouse = (opts) => {
  const schedules = fontSchedules(opts.planets.length);
  let fallback = null;
  for (const fonts of schedules) {
    const placed = tryLayout(opts, fonts, 2);
    if (placed) return placed;
    fallback = tryLayout(opts, fonts, -999);
  }
  return fallback || { planets: [], asc: null, occupied: [signOccupied(opts.sign, opts.signLabel)], minGap: 8, fonts: schedules[0] };
};

export const boxesOverlap = (boxes) => {
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      if (boxGap(boxes[i], boxes[j]) < 2) return true;
    }
  }
  return false;
};
