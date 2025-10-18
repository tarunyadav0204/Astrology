// Planet Analysis Utilities
// Handles planet status, dignity, lordships, friendships, and aspects
export const getHouseLordship = (planet, ascendantSign = 0) => {
  const signLordships = {
    'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5], 
    'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
  };
  const planetSigns = signLordships[planet] || [];
  return planetSigns.map(sign => ((sign - ascendantSign + 12) % 12) + 1);
};

export const getFriendship = (planet1, planet2) => {
  const friends = {
    'Sun': ['Moon', 'Mars', 'Jupiter'], 'Moon': ['Sun', 'Mercury'], 'Mars': ['Sun', 'Moon', 'Jupiter'],
    'Mercury': ['Sun', 'Venus'], 'Jupiter': ['Sun', 'Moon', 'Mars'], 'Venus': ['Mercury', 'Saturn'], 'Saturn': ['Mercury', 'Venus']
  };
  const enemies = {
    'Sun': ['Venus', 'Saturn'], 'Moon': [], 'Mars': ['Mercury'], 'Mercury': ['Moon'],
    'Jupiter': ['Mercury', 'Venus'], 'Venus': ['Sun', 'Moon'], 'Saturn': ['Sun', 'Moon', 'Mars']
  };
  if (friends[planet1]?.includes(planet2)) return 'Friend';
  if (enemies[planet1]?.includes(planet2)) return 'Enemy';
  return 'Neutral';
};

export const ownSigns = { 
  'Mars': [0, 7], 'Venus': [1, 6], 'Mercury': [2, 5], 'Moon': [3], 
  'Sun': [4], 'Jupiter': [8, 11], 'Saturn': [9, 10] 
};

export const exaltationSigns = { 
  'Mars': 9, 'Venus': 11, 'Mercury': 5, 'Moon': 1, 
  'Sun': 0, 'Jupiter': 3, 'Saturn': 6 
};

export const debilitationSigns = { 
  'Mars': 3, 'Venus': 5, 'Mercury': 11, 'Moon': 7, 
  'Sun': 6, 'Jupiter': 9, 'Saturn': 0 
};

export const houseLords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];

export const getPlanetStatus = (planet, rashiIndex, lordships) => {
  const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet);
  const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet);
  const isInOwnSign = ownSigns[planet]?.includes(rashiIndex);
  
  const hasTrikonaLordship = lordships.some(h => [1, 5, 9].includes(h));
  const hasKendraLordship = lordships.some(h => [1, 4, 7, 10].includes(h));
  
  // Rahu/Ketu special handling - they don't have lordships but are natural malefics
  if (['Rahu', 'Ketu'].includes(planet)) {
    return 'Negative (natural malefic)';
  }
  
  if (lordships.includes(6)) {
    return 'Negative';
  } else if (lordships.includes(8)) {
    return hasTrikonaLordship ? 'Mixed (8th lord negative dominates)' : 'Negative';
  } else if (lordships.includes(12)) {
    return hasTrikonaLordship || hasKendraLordship ? 'Mixed' : 'Negative';
  } else if (isNaturalBenefic && (hasTrikonaLordship || hasKendraLordship)) {
    return 'Positive';
  } else if (isNaturalMalefic && isInOwnSign) {
    return 'Positive';
  } else if (isNaturalMalefic && hasKendraLordship) {
    return 'Mixed (natural malefic in kendra)';
  } else if (isNaturalMalefic) {
    return 'Negative';
  } else {
    return 'Neutral';
  }
};

export const getPlanetDignity = (planet, sign) => {
  if (sign === exaltationSigns[planet]) return 'Exalted';
  if (sign === debilitationSigns[planet]) return 'Debilitated';
  if (ownSigns[planet]?.includes(sign)) return 'Own';
  return 'Neutral';
};

export const getStatusColor = (status) => {
  if (status === 'Positive') return '#4caf50';
  if (status === 'Negative') return '#f44336';
  return '#ff9800';
};

export const getNakshatraLord = (longitude) => {
  const nakshatraLords = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
  ];
  const nakshatraIndex = Math.floor(longitude / 13.333333);
  return nakshatraLords[nakshatraIndex];
};

export const getAspectingPlanets = (houseIndex, chartData) => {
  const aspectingPlanets = [];
  const targetHouseSign = chartData.houses?.[houseIndex]?.sign;
  
  Object.entries(chartData.planets || {}).forEach(([planetName, planetData]) => {
    // 7th aspect (opposition)
    const aspectSign = (planetData.sign + 6) % 12;
    if (aspectSign === targetHouseSign) {
      aspectingPlanets.push(planetName);
    }
    
    // Special aspects
    if (planetName === 'Mars') {
      // Mars 4th and 8th aspects
      const fourthAspect = (planetData.sign + 3) % 12;
      const eighthAspect = (planetData.sign + 7) % 12;
      if (fourthAspect === targetHouseSign || eighthAspect === targetHouseSign) {
        aspectingPlanets.push(planetName);
      }
    } else if (planetName === 'Jupiter') {
      // Jupiter 5th and 9th aspects
      const fifthAspect = (planetData.sign + 4) % 12;
      const ninthAspect = (planetData.sign + 8) % 12;
      if (fifthAspect === targetHouseSign || ninthAspect === targetHouseSign) {
        aspectingPlanets.push(planetName);
      }
    } else if (planetName === 'Saturn') {
      // Saturn 3rd and 10th aspects
      const thirdAspect = (planetData.sign + 2) % 12;
      const tenthAspect = (planetData.sign + 9) % 12;
      if (thirdAspect === targetHouseSign || tenthAspect === targetHouseSign) {
        aspectingPlanets.push(planetName);
      }
    }
  });
  
  return [...new Set(aspectingPlanets)]; // Remove duplicates
};

// Special Conditions Analysis
export const getYogiAvayogi = (birthDetails) => {
  if (!birthDetails?.date_of_birth) return { yogi: null, avayogi: null };
  
  const date = new Date(birthDetails.date_of_birth);
  const weekday = date.getDay(); // 0=Sunday, 1=Monday, etc.
  const nakshatra = Math.floor((birthDetails.moon_longitude || 0) / 13.333333);
  
  // Yogi calculation: Weekday + Nakshatra number
  const yogiIndex = (weekday + nakshatra) % 27;
  const avayogiIndex = (yogiIndex + 12) % 27;
  
  const nakshatraLords = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
  ];
  
  return {
    yogi: nakshatraLords[yogiIndex],
    avayogi: nakshatraLords[avayogiIndex]
  };
};

export const getDagdhaConditions = (chartData) => {
  const dagdhaConditions = [];
  
  // Dagdha combinations (Planet + Sign combinations that are considered burnt/inauspicious)
  const dagdhaCombinations = {
    'Sun': [10], // Sun in Aquarius
    'Moon': [7], // Moon in Scorpio  
    'Mars': [6], // Mars in Libra
    'Mercury': [11], // Mercury in Pisces
    'Jupiter': [9], // Jupiter in Capricorn
    'Venus': [5], // Venus in Virgo
    'Saturn': [0] // Saturn in Aries
  };
  
  Object.entries(chartData.planets || {}).forEach(([planet, data]) => {
    if (dagdhaCombinations[planet]?.includes(data.sign)) {
      dagdhaConditions.push({
        planet,
        condition: 'Dagdha',
        effect: 'Weakened results, obstacles in significations'
      });
    }
  });
  
  return dagdhaConditions;
};

export const getTithiShunyaConditions = (birthDetails, chartData) => {
  const tithiShunyaConditions = [];
  
  if (!birthDetails?.tithi) return tithiShunyaConditions;
  
  // Tithi Shunya combinations (certain planets are weak on certain tithis)
  const tithiShunyaCombinations = {
    4: ['Sun'], // Chaturthi - Sun is Tithi Shunya
    6: ['Moon'], // Shashthi - Moon is Tithi Shunya
    7: ['Mars'], // Saptami - Mars is Tithi Shunya
    8: ['Rahu'], // Ashtami - Rahu is Tithi Shunya
    9: ['Jupiter'], // Navami - Jupiter is Tithi Shunya
    12: ['Venus'], // Dwadashi - Venus is Tithi Shunya
    14: ['Saturn'] // Chaturdashi - Saturn is Tithi Shunya
  };
  
  const affectedPlanets = tithiShunyaCombinations[birthDetails.tithi] || [];
  
  affectedPlanets.forEach(planet => {
    if (chartData.planets?.[planet]) {
      tithiShunyaConditions.push({
        planet,
        condition: 'Tithi Shunya',
        effect: 'Reduced strength and auspiciousness'
      });
    }
  });
  
  return tithiShunyaConditions;
};

export const getCombustionConditions = (chartData) => {
  const combustionConditions = [];
  const sunData = chartData.planets?.Sun;
  
  if (!sunData) return combustionConditions;
  
  // Combustion distances (degrees)
  const combustionDistances = {
    'Moon': 12,
    'Mars': 17,
    'Mercury': 14, // 14 degrees when retrograde, 12 when direct
    'Jupiter': 11,
    'Venus': 10, // 10 degrees when retrograde, 8 when direct
    'Saturn': 15
  };
  
  Object.entries(chartData.planets || {}).forEach(([planet, data]) => {
    if (planet === 'Sun' || !combustionDistances[planet]) return;
    
    // Calculate angular distance
    let distance = Math.abs(data.longitude - sunData.longitude);
    if (distance > 180) distance = 360 - distance;
    
    if (distance <= combustionDistances[planet]) {
      combustionConditions.push({
        planet,
        condition: 'Combust',
        distance: distance.toFixed(1),
        effect: 'Weakened, overshadowed by Sun\'s energy'
      });
    }
  });
  
  return combustionConditions;
};

export const analyzeSpecialConditions = (birthDetails, chartData) => {
  const yogiAvayogi = getYogiAvayogi(birthDetails);
  const dagdhaConditions = getDagdhaConditions(chartData);
  const tithiShunyaConditions = getTithiShunyaConditions(birthDetails, chartData);
  const combustionConditions = getCombustionConditions(chartData);
  
  return {
    yogiAvayogi,
    dagdhaConditions,
    tithiShunyaConditions,
    combustionConditions,
    hasSpecialConditions: dagdhaConditions.length > 0 || tithiShunyaConditions.length > 0 || combustionConditions.length > 0
  };
};

// Calculate D9 House Strength considering planet dignities
export const calculateD9HouseStrength = (houseSign, planetsInHouse, d9ChartData) => {
  let strength = 5; // Base strength
  
  // House lord strength
  const houseLord = houseLords[houseSign];
  const houseLordData = d9ChartData?.planets?.[houseLord];
  if (houseLordData) {
    const lordDignity = getPlanetDignity(houseLord, houseLordData.sign);
    if (lordDignity === 'Exalted') strength += 2;
    else if (lordDignity === 'Own') strength += 1.5;
    else if (lordDignity === 'Debilitated') strength -= 2;
    else if (lordDignity === 'Neutral') strength += 0;
  }
  
  // Planets in house strength
  planetsInHouse.forEach(planetName => {
    const planetData = d9ChartData?.planets?.[planetName];
    if (!planetData) return;
    
    const dignity = getPlanetDignity(planetName, planetData.sign);
    const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
    const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planetName);
    
    if (dignity === 'Exalted') {
      strength += isNaturalBenefic ? 2 : 1.5;
    } else if (dignity === 'Own') {
      strength += isNaturalBenefic ? 1.5 : 1;
    } else if (dignity === 'Debilitated') {
      strength -= isNaturalBenefic ? 1.5 : 2; // Debilitated planets reduce strength more
    } else {
      strength += isNaturalBenefic ? 0.5 : (isNaturalMalefic ? -0.5 : 0);
    }
  });
  
  // Cap between 1-10
  return Math.max(1, Math.min(10, Math.round(strength)));
};