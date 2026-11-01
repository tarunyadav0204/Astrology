import { dashaLensThemes } from './dashaLens';

const TRANSIT_ASPECT_STEPS = {
  Jupiter: [5, 7, 9],
  Saturn: [3, 7, 10],
  Rahu: [5, 7, 9],
  Ketu: [5, 7, 9],
};

const houseForSign = (sign, ascendantSign) => {
  const numericSign = Number(sign);
  const numericAscendant = Number(ascendantSign);
  return Number.isFinite(numericSign) && Number.isFinite(numericAscendant)
    ? ((numericSign - numericAscendant + 12) % 12) + 1
    : null;
};

export const buildTransitLens = (natalChart, transitChart, planetName) => {
  const ascendantSign = natalChart?.houses?.[0]?.sign;
  const transitPlanet = transitChart?.planets?.[planetName];
  const sourceHouse = houseForSign(transitPlanet?.sign, ascendantSign);
  if (!sourceHouse || !planetName) return null;

  const byHouse = new Map();
  const add = (house, kind, label) => {
    if (!house || byHouse.has(house)) return;
    byHouse.set(house, { house, kind, kinds: [kind], label });
  };
  add(sourceHouse, 'transit', 'Transits here');
  (TRANSIT_ASPECT_STEPS[planetName] || [7]).forEach((step) => {
    add(((sourceHouse + step - 2) % 12) + 1, 'aspect', 'Aspects this house');
  });
  const lens = {
    type: 'transit',
    planet: planetName,
    sourceHouse,
    houses: [...byHouse.values()].sort((a, b) => a.house - b.house),
  };
  return { ...lens, themes: dashaLensThemes(lens) };
};

// A dasha lord can be any graha, so the timing lens must let the reader
// compare that very same planet's current transit, not only slow planets.
export const TRANSIT_LENS_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
