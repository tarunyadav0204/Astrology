/**
 * Client-side fallback for graha drishti when chart payload has no graha_drishti_by_house
 * (e.g. cached old API). Mirrors backend calculators/vedic_graha_drishti.py.
 */

const PLANET_ORDER = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn',
  'Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi', 'InduLagna',
];

const GRAHA_HOUSE_ASPECTS = {
  Sun: [1, 7],
  Moon: [1, 7],
  Mars: [1, 4, 7, 8],
  Mercury: [1, 7],
  Jupiter: [1, 5, 7, 9],
  Venus: [1, 7],
  Saturn: [1, 3, 7, 10],
  Rahu: [1, 5, 7, 9],
  Ketu: [1, 5, 7, 9],
  Uranus: [1, 7],
  Neptune: [1, 7],
  Pluto: [1, 7],
  Gulika: [1, 7],
  Mandi: [1, 7],
  InduLagna: [1, 7],
};

const DEFAULT_ASPECTS = [1, 7];

function nthLabel(n) {
  if (n === 1) return '1st';
  if (n === 2) return '2nd';
  if (n === 3) return '3rd';
  return `${n}th`;
}

function aspectLabelsFromHits(hits) {
  return [...new Set(hits)]
    .sort((a, b) => a - b)
    .map(nthLabel)
    .join(', ');
}

function houseNumberForSign(chartData, signIndex) {
  if (!chartData?.houses?.length) return null;
  const idx = chartData.houses.findIndex((h) => h.sign === signIndex);
  return idx >= 0 ? idx + 1 : null;
}

export function getGrahaDrishtiToHouseSign(chartData, targetSign) {
  if (typeof targetSign !== 'number' || targetSign < 0 || targetSign > 11) return [];
  const planets = chartData?.planets;
  if (!planets || typeof planets !== 'object') return [];

  const out = [];
  for (const name of PLANET_ORDER) {
    const data = planets[name];
    if (!data || typeof data !== 'object' || typeof data.sign !== 'number') continue;
    const pSign = data.sign;
    if (pSign === targetSign) continue;

    const aspects = GRAHA_HOUSE_ASPECTS[name] || DEFAULT_ASPECTS;
    const hits = aspects.filter((n) => (pSign + n - 1) % 12 === targetSign);
    if (!hits.length) continue;

    out.push({
      planetName: name,
      planetHouse: houseNumberForSign(chartData, pSign),
      aspectKinds: aspectLabelsFromHits(hits),
    });
  }
  return out;
}
