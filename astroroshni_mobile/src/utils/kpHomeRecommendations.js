const AREA_RULES = [
  { id: 'career', analysisType: 'career', required: [6, 10], weights: { 10: 5, 6: 3, 2: 1.5, 11: 2 } },
  { id: 'relationships', analysisType: 'marriage', required: [7], weights: { 7: 5, 2: 1.5, 5: 1.5, 11: 1 } },
  { id: 'wealth', analysisType: 'wealth', required: [2, 11], weights: { 2: 4, 11: 4, 5: 1, 6: 1, 10: 1 } },
  { id: 'education', analysisType: 'education', required: [4, 5, 9], weights: { 4: 3, 5: 4, 9: 4, 11: 1 } },
  { id: 'family', analysisType: 'progeny', required: [5], weights: { 5: 5, 2: 1.5, 11: 1.5 } },
  { id: 'wellbeing', analysisType: 'health', required: [1, 6], weights: { 1: 3, 6: 4, 8: 0.75, 12: 0.75 } },
  { id: 'innerGrowth', analysisType: 'karma', required: [8, 9, 12], weights: { 8: 4, 9: 2, 12: 3, 1: 1 } },
];

const normalizeHouse = (value) => {
  const house = Number(value);
  return Number.isInteger(house) && house >= 1 && house <= 12 ? house : null;
};

const moonRolePlanets = (roleMap = {}) => new Set([
  roleMap.moon_sign_lord,
  roleMap.moon_star_lord,
  roleMap.moon_sub_lord,
].filter(Boolean).map(String));

export function rankKpHomeAreas(kpPayload) {
  const todayBlock = kpPayload?.today || kpPayload;
  const rows = Array.isArray(todayBlock?.houses_giving_results)
    ? todayBlock.houses_giving_results
    : [];
  // Today's KP block uses day + Moon sign/star lords. The selected-hour block
  // also exposes Moon sub lord; use it as an extra relevance boost without
  // letting it replace the stronger, full activated-house synthesis.
  const moonPlanets = new Set([
    ...moonRolePlanets(todayBlock?.ruling_planets_used),
    ...moonRolePlanets(kpPayload?.hour?.ruling_planets_used),
  ]);
  const moonSubLord = kpPayload?.hour?.ruling_planets_used?.moon_sub_lord;
  const significatorStep = (todayBlock?.calculation?.steps || []).find(
    (step) => step?.planet_significators,
  );
  const moonSubHouses = new Set(
    (significatorStep?.planet_significators?.[moonSubLord] || [])
      .map(normalizeHouse)
      .filter(Boolean),
  );
  const houseSignals = new Map();

  rows.forEach((row) => {
    const house = normalizeHouse(row?.house);
    if (!house) return;
    const activation = Math.max(0, Number(row?.activation_score) || 0);
    const activating = Array.isArray(row?.activating_rps) ? row.activating_rps.map(String) : [];
    const moonConfirmed = activating.some((planet) => moonPlanets.has(planet))
      || moonSubHouses.has(house);
    houseSignals.set(house, {
      activation,
      moonConfirmed,
      tone: row?.tone || 'neutral',
    });
  });

  return AREA_RULES.map((area) => {
    const matchedHouses = Object.keys(area.weights)
      .map(Number)
      .filter((house) => houseSignals.has(house));
    const requiredMatched = area.required.some((house) => houseSignals.has(house));
    if (!requiredMatched) return null;

    let score = 0;
    let moonBoost = false;
    matchedHouses.forEach((house) => {
      const signal = houseSignals.get(house);
      const strength = Math.min(1.6, Math.max(0.7, signal.activation / 3));
      score += area.weights[house] * strength;
      if (signal.moonConfirmed) {
        score += area.weights[house] * 0.22;
        moonBoost = true;
      }
    });

    return {
      ...area,
      score,
      moonBoost,
      houses: matchedHouses.sort((a, b) => a - b),
    };
  })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
}

export function buildKpHomeRecommendations(kpPayload, t) {
  const ranked = rankKpHomeAreas(kpPayload);
  if (!ranked.length) return [];

  const primary = ranked[0];
  const secondary = ranked.find((item) => item.id !== primary.id);
  const houseText = primary.houses.join(', ');
  const recommendations = [
    {
      id: `analysis-${primary.id}`,
      kind: 'analysis',
      area: primary.id,
      analysisType: primary.analysisType,
      houses: primary.houses,
      title: t(`premiumUi.homeRecommendations.areas.${primary.id}.title`),
      body: t(
        primary.moonBoost
          ? 'premiumUi.homeRecommendations.moonBody'
          : 'premiumUi.homeRecommendations.activationBody',
        { houses: houseText },
      ),
    },
    {
      id: `ask-${primary.id}`,
      kind: 'ask',
      area: primary.id,
      houses: primary.houses,
      title: t('premiumUi.homeRecommendations.askTitle', {
        area: t(`premiumUi.homeRecommendations.areas.${primary.id}.short`),
      }),
      body: t('premiumUi.homeRecommendations.askBody'),
      question: t(`premiumUi.homeRecommendations.areas.${primary.id}.question`),
    },
  ];

  if (secondary) {
    recommendations.push({
      id: `analysis-${secondary.id}`,
      kind: 'analysis',
      area: secondary.id,
      analysisType: secondary.analysisType,
      houses: secondary.houses,
      title: t(`premiumUi.homeRecommendations.areas.${secondary.id}.title`),
      body: t('premiumUi.homeRecommendations.secondaryBody', {
        houses: secondary.houses.join(', '),
      }),
    });
  }

  return recommendations;
}
