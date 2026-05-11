const SIGN_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

const EXALTATION_SIGNS = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6 };
const DEBILITATION_SIGNS = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0 };
const HOUSE_LORDS = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
const BENEFIC_PLANETS = new Set(['Jupiter', 'Venus', 'Moon']);
const CHALLENGING_PLANETS = new Set(['Saturn', 'Mars', 'Rahu', 'Ketu']);

const RELATED_CHARTS = {
  2: { id: 'hora', name: 'Hora (D2)' },
  4: { id: 'chaturthamsa', name: 'Chaturthamsa (D4)' },
  5: { id: 'saptamsa', name: 'Saptamsa (D7)' },
  7: { id: 'navamsa', name: 'Navamsa (D9)' },
  9: { id: 'vimsamsa', name: 'Vimsamsa (D20)' },
  10: { id: 'dashamsa', name: 'Dasamsa (D10)' },
  12: { id: 'dwadashamsa', name: 'Dwadashamsa (D12)' },
};

function getPlanetDignity(planetName, signIndex) {
  if (EXALTATION_SIGNS[planetName] === signIndex) return 'exalted';
  if (DEBILITATION_SIGNS[planetName] === signIndex) return 'debilitated';
  return 'ordinary';
}

function getHouseLordForSign(signIndex) {
  return HOUSE_LORDS[signIndex] || 'Unknown';
}

function getHouseOfPlanet(chartData, planetName) {
  const sign = chartData?.planets?.[planetName]?.sign;
  if (typeof sign !== 'number' || !Array.isArray(chartData?.houses)) return null;
  const idx = chartData.houses.findIndex((house) => house?.sign === sign);
  return idx >= 0 ? idx + 1 : null;
}

function getPlanetsInHouseByNumber(chartData, houseNum) {
  const house = chartData?.houses?.[houseNum - 1];
  if (!house || typeof house.sign !== 'number') return [];
  const targetSign = house.sign;
  return Object.entries(chartData?.planets || {})
    .filter(([planetName, data]) => data?.sign === targetSign && planetName !== 'ascendant_longitude')
    .map(([planetName, data]) => ({
      name: planetName,
      sign: data.sign,
      degree: data.degree,
      retrograde: !!data.retrograde,
    }));
}

function getTransitActivators(transitChartData, natalTargetSign) {
  if (!transitChartData?.planets) return [];
  return Object.entries(transitChartData.planets)
    .filter(([planetName, data]) => {
      if (planetName === 'ascendant_longitude' || !data || typeof data.sign !== 'number') return false;
      if (data.sign === natalTargetSign) return true;

      const offsets = {
        Sun: [7],
        Moon: [7],
        Mars: [4, 7, 8],
        Mercury: [7],
        Jupiter: [5, 7, 9],
        Venus: [7],
        Saturn: [3, 7, 10],
        Rahu: [5, 7, 9],
        Ketu: [5, 7, 9],
      }[planetName] || [7];

      return offsets.some((offset) => ((data.sign + offset - 1) % 12) === natalTargetSign);
    })
    .map(([planetName, data]) => ({ name: planetName, sign: data.sign }));
}

function summarizeVerdict(score, activationCount) {
  if (score >= 5) return { key: 'strong', label: 'Strongly activated' };
  if (score >= 2) return { key: 'mixed', label: 'Supportive but mixed' };
  if (activationCount > 0) return { key: 'active', label: 'Active but sensitive' };
  return { key: 'quiet', label: 'Quiet right now' };
}

function buildInterpretation(houseNum, verdict, chartTypeName, signName) {
  const area = {
    1: 'self-expression and direction',
    2: 'money, family, and speech',
    3: 'effort, courage, and communication',
    4: 'home, emotional steadiness, and comforts',
    5: 'creativity, children, and intelligence',
    6: 'work stress, health, and conflict management',
    7: 'relationships and agreements',
    8: 'transformation, vulnerability, and hidden shifts',
    9: 'fortune, mentors, and meaning',
    10: 'career, visibility, and responsibility',
    11: 'gains, networks, and fulfillment',
    12: 'losses, rest, withdrawal, and spiritual release',
  }[houseNum] || 'this area of life';

  if (verdict.key === 'strong') {
    return `This ${chartTypeName} chart gives extra weight to ${area}. ${signName} themes here are likely to show up clearly in lived experience.`;
  }
  if (verdict.key === 'mixed') {
    return `This house matters in your ${chartTypeName} chart, but it carries both support and pressure. ${area} may grow through effort, timing, and better choices.`;
  }
  if (verdict.key === 'active') {
    return `This house is not weak, but it is more reactive than settled right now. ${area} may feel event-driven rather than steady.`;
  }
  return `This house is comparatively quiet in the ${chartTypeName} chart. ${area} may still matter, but it is not the loudest pattern at the moment.`;
}

export function getRelatedChartForHouse(houseNum) {
  return RELATED_CHARTS[houseNum] || null;
}

export function buildHouseInsight({
  houseNum,
  signName,
  chartData,
  chartTypeId = 'lagna',
  chartTypeName = 'chart',
  grahaDrishti = [],
  relatedChartData = null,
  transitChartData = null,
}) {
  const house = chartData?.houses?.[houseNum - 1];
  const targetSign = house?.sign;
  const occupants = getPlanetsInHouseByNumber(chartData, houseNum);
  const houseLord = typeof targetSign === 'number' ? getHouseLordForSign(targetSign) : 'Unknown';
  const lordSign = chartData?.planets?.[houseLord]?.sign;
  const lordHouse = getHouseOfPlanet(chartData, houseLord);
  const lordDignity = typeof lordSign === 'number' ? getPlanetDignity(houseLord, lordSign) : 'ordinary';
  const transitActivators = typeof targetSign === 'number' ? getTransitActivators(transitChartData, targetSign) : [];
  const relatedChart = getRelatedChartForHouse(houseNum);

  let score = 0;
  const reasons = [];
  const chips = [];

  if (occupants.length) {
    score += Math.min(3, occupants.length);
    reasons.push(
      occupants.length === 1
        ? `Occupied by ${occupants[0].name}, so this house speaks directly in the chart.`
        : `Occupied by ${occupants.map((planet) => planet.name).join(', ')}, making this house one of the more active zones.`
    );
    chips.push({ label: `Occupants ${occupants.length}`, tone: 'neutral' });
  } else {
    reasons.push('No natal occupants here, so the house depends more on its lord and incoming aspects.');
  }

  if (lordHouse != null) {
    const lordHouseLabel = `${houseLord} rules this house and sits in house ${lordHouse}.`;
    reasons.push(lordHouseLabel);
    chips.push({ label: `${houseLord} in H${lordHouse}`, tone: 'neutral' });

    if ([1, 4, 5, 7, 9, 10].includes(lordHouse)) {
      score += 2;
      reasons.push(`Its lord is placed in a prominent house, which helps this area show up more clearly.`);
      chips.push({ label: 'Prominent lord placement', tone: 'good' });
    } else if ([6, 8, 12].includes(lordHouse)) {
      score -= 1;
      reasons.push(`Its lord is placed in a demanding house, so results here may come with more friction or delay.`);
      chips.push({ label: 'Demanding lord placement', tone: 'warn' });
    }
  }

  if (lordDignity === 'exalted') {
    score += 2;
    reasons.push(`${houseLord} is exalted, which supports cleaner expression of this house.`);
    chips.push({ label: `${houseLord} exalted`, tone: 'good' });
  } else if (lordDignity === 'debilitated') {
    score -= 2;
    reasons.push(`${houseLord} is debilitated, so this house may need maturity and better timing to deliver fully.`);
    chips.push({ label: `${houseLord} debilitated`, tone: 'warn' });
  }

  if (grahaDrishti.length) {
    const supportive = grahaDrishti.filter((row) => BENEFIC_PLANETS.has(row.planetName)).map((row) => row.planetName);
    const challenging = grahaDrishti.filter((row) => CHALLENGING_PLANETS.has(row.planetName)).map((row) => row.planetName);

    if (supportive.length) {
      score += 1;
      reasons.push(`Supportive graha drishti from ${supportive.join(', ')} adds help to this house.`);
      chips.push({ label: `Supportive drishti ${supportive.length}`, tone: 'good' });
    }
    if (challenging.length) {
      score -= 1;
      reasons.push(`Challenging graha drishti from ${challenging.join(', ')} can add pressure, delay, or intensity here.`);
      chips.push({ label: `Pressure drishti ${challenging.length}`, tone: 'warn' });
    }
    if (!supportive.length && !challenging.length) {
      reasons.push(`This house receives graha drishti, but the influence is more neutral than strongly helpful or difficult.`);
    }
  }

  if (relatedChart && relatedChartData) {
    const relatedOccupants = getPlanetsInHouseByNumber(relatedChartData, houseNum);
    const relatedLordHouse = getHouseOfPlanet(relatedChartData, houseLord);
    if (relatedOccupants.length || relatedLordHouse === houseNum) {
      score += 1;
      reasons.push(`${relatedChart.name} repeats this theme, which strengthens confidence in the reading.`);
      chips.push({ label: `${relatedChart.name} confirms`, tone: 'good' });
    } else {
      reasons.push(`${relatedChart.name} is quieter on this house, so the signal is stronger in the current chart than in the support chart.`);
    }
  }

  if (transitActivators.length) {
    score += 1;
    reasons.push(`Current transit activity from ${transitActivators.slice(0, 3).map((row) => row.name).join(', ')} is touching this house now.`);
    chips.push({ label: 'Transit active', tone: 'good' });
  }

  const verdict = summarizeVerdict(score, occupants.length + grahaDrishti.length + transitActivators.length);

  return {
    verdict,
    score,
    houseLord,
    lordHouse,
    lordDignity,
    occupants,
    reasons: reasons.slice(0, 6),
    chips,
    interpretation: buildInterpretation(houseNum, verdict, chartTypeName, signName || SIGN_NAMES[targetSign] || 'this sign'),
    relatedChart,
    transitActivators,
  };
}
