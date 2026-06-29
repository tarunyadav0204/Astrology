const GANDANTA_RANGES = {
  pisces_aries: {
    start: 356.666667,
    end: 3.333333,
    name: 'Revati-Ashwini Gandanta',
  },
  cancer_leo: {
    start: 116.666667,
    end: 123.333333,
    name: 'Ashlesha-Magha Gandanta',
  },
  scorpio_sagittarius: {
    start: 236.666667,
    end: 243.333333,
    name: 'Jyeshtha-Mula Gandanta',
  },
};

const RASHI_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

function normalizeLongitude(longitude) {
  const lon = Number(longitude) || 0;
  return ((lon % 360) + 360) % 360;
}

function isInGandantaRange(longitude, range) {
  const lon = normalizeLongitude(longitude);
  const { start, end } = range;
  if (start > end) {
    return lon >= start || lon <= end;
  }
  return lon >= start && lon <= end;
}

function calculateDistanceFromJunction(longitude, range) {
  const lon = normalizeLongitude(longitude);
  if (range.start > range.end) {
    return lon >= 356.666667 ? round2(360 - lon) : round2(lon);
  }
  return round2(Math.abs(lon - (range.start + 4)));
}

function calculateIntensity(distance) {
  if (distance <= 1.0) return 'Extreme';
  if (distance <= 2.0) return 'High';
  if (distance <= 3.0) return 'Medium';
  return 'Low';
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

function checkLongitude(longitude) {
  for (const [gandantaType, gandantaRange] of Object.entries(GANDANTA_RANGES)) {
    if (isInGandantaRange(longitude, gandantaRange)) {
      const distance = calculateDistanceFromJunction(longitude, gandantaRange);
      return {
        is_gandanta: true,
        gandanta_type: gandantaType,
        gandanta_name: gandantaRange.name,
        longitude: normalizeLongitude(longitude),
        distance_from_junction: distance,
        intensity: calculateIntensity(distance),
      };
    }
  }
  return { is_gandanta: false };
}

export function calculateGandantaLocal(chartData = {}) {
  const planets = chartData?.planets && typeof chartData.planets === 'object' ? chartData.planets : {};
  const ascendant = chartData?.ascendant;

  const planets_in_gandanta = Object.entries(planets)
    .map(([planet, planetData]) => {
      const gandanta_info = checkLongitude(planetData?.longitude);
      return gandanta_info.is_gandanta ? { planet, gandanta_info } : null;
    })
    .filter(Boolean);

  const lagna_gandanta = ascendant == null ? { is_gandanta: false } : checkLongitude(ascendant);
  const moon_gandanta = planets.Moon?.longitude == null ? { is_gandanta: false } : checkLongitude(planets.Moon.longitude);

  return {
    planets_in_gandanta,
    lagna_gandanta: lagna_gandanta.is_gandanta ? { is_gandanta: true, gandanta_info: lagna_gandanta } : { is_gandanta: false },
    moon_gandanta: moon_gandanta.is_gandanta ? { is_gandanta: true, gandanta_info: moon_gandanta } : { is_gandanta: false },
  };
}

export function getGandantaHouseMatches(chartData = {}, planetsInHouse = []) {
  const gandanta = calculateGandantaLocal(chartData);
  const matchingPlanets = planetsInHouse
    .map((planet) => {
      const gandantaInfo = checkLongitude(planet?.longitude);
      return gandantaInfo.is_gandanta ? { planet, gandanta_info: gandantaInfo } : null;
    })
    .filter(Boolean);

  return {
    planets: matchingPlanets,
    lagna: gandanta.lagna_gandanta,
    moon: gandanta.moon_gandanta,
  };
}

export function getGandantaSignName(longitude) {
  const lon = normalizeLongitude(longitude);
  return RASHI_NAMES[Math.floor(lon / 30)] || 'Unknown';
}
