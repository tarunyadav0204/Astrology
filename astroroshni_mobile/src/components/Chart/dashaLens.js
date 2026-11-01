// The dasha lens deliberately starts with the most legible classical links:
// where the selected lord sits and the houses it owns.  Aspect connections are
// exposed as supporting links, so the chart remains readable on a phone.
const SIGN_LORDS = {
  0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
  6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter',
};

const ASPECT_STEPS = {
  Sun: [7], Moon: [7], Mercury: [7], Venus: [7],
  Mars: [4, 7, 8], Jupiter: [5, 7, 9], Saturn: [3, 7, 10],
  Rahu: [5, 7, 9], Ketu: [5, 7, 9],
};

const HOUSE_THEMES = {
  1: 'self, body, identity, vitality and personal direction',
  2: 'savings, income, family, speech, food and values',
  3: 'courage, effort, skills, writing, communication, siblings and short travel',
  4: 'home, property, vehicles, mother, education, comfort and emotional foundations',
  5: 'creativity, intelligence, learning, romance, children, speculation and self-expression',
  6: 'work, service, health, healing, routines, competition, disputes and debts',
  7: 'marriage, partnerships, contracts, clients, public dealings and travel',
  8: 'research, hidden matters, occult study, transformation, inheritance, insurance and shared resources',
  9: 'higher learning, fortune, mentors, father, dharma, publishing, long journeys and foreign travel',
  10: 'career, profession, reputation, authority, responsibility and public contribution',
  11: 'gains, income, networks, friends, community, elder siblings and aspirations',
  12: 'expenses, sleep, hospitals, isolation, foreign residence, retreats, release and spirituality',
};

const HOUSE_THEME_CHIPS = {
  1: 'Self · Vitality',
  2: 'Savings · Family',
  3: 'Skills · Communication',
  4: 'Home · Property',
  5: 'Creativity · Children',
  6: 'Work · Health',
  7: 'Partnerships · Marriage',
  8: 'Research · Change',
  9: 'Learning · Fortune',
  10: 'Career · Status',
  11: 'Gains · Networks',
  12: 'Hospitals · Foreign',
};

const houseForPlanet = (planet, ascendantSign) => {
  if (Number.isFinite(planet?.house)) return planet.house;
  if (!Number.isFinite(planet?.sign) || !Number.isFinite(ascendantSign)) return null;
  return ((planet.sign - ascendantSign + 12) % 12) + 1;
};

export const buildDashaLens = (chartData, planetName) => {
  const planets = chartData?.planets || chartData || {};
  const ascendantSign = chartData?.houses?.[0]?.sign;
  if (!planetName || !planets?.[planetName] || !Number.isFinite(ascendantSign)) return null;

  const selectedPlanet = planets[planetName];
  const placementHouse = houseForPlanet(selectedPlanet, ascendantSign);
  const ownedHouses = [];
  Object.entries(SIGN_LORDS).forEach(([sign, lord]) => {
    if (lord === planetName) ownedHouses.push(((Number(sign) - ascendantSign + 12) % 12) + 1);
  });
  const aspectHouses = (ASPECT_STEPS[planetName] || [])
    .map((step) => (placementHouse ? ((placementHouse + step - 2) % 12) + 1 : null))
    .filter(Boolean);

  const byHouse = new Map();
  const add = (house, kind, label) => {
    if (!house) return;
    const existing = byHouse.get(house);
    if (existing) {
      existing.kinds.push(kind);
      return;
    }
    byHouse.set(house, { house, kind, kinds: [kind], label });
  };
  add(placementHouse, 'placement', 'Placed here');
  ownedHouses.forEach((house) => add(house, 'lordship', 'Rules this house'));
  aspectHouses.forEach((house) => add(house, 'aspect', 'Aspects this house'));

  return {
    planet: planetName,
    sourceHouse: placementHouse,
    houses: [...byHouse.values()].sort((a, b) => a.house - b.house),
  };
};

export const dashaLensThemes = (lens) => (
  (lens?.houses || []).map(({ house }) => ({
    house,
    label: `${house}${house === 1 ? 'st' : house === 2 ? 'nd' : house === 3 ? 'rd' : 'th'}`,
    theme: HOUSE_THEMES[house],
    chip: HOUSE_THEME_CHIPS[house],
  })).filter(({ theme }) => theme)
);
