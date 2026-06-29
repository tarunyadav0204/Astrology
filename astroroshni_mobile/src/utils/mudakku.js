const NAKSHATRA_NAMES = [
  'Ashwini',
  'Bharani',
  'Krittika',
  'Rohini',
  'Mrigashira',
  'Ardra',
  'Punarvasu',
  'Pushya',
  'Ashlesha',
  'Magha',
  'Purva Phalguni',
  'Uttara Phalguni',
  'Hasta',
  'Chitra',
  'Swati',
  'Vishakha',
  'Anuradha',
  'Jyeshtha',
  'Mula',
  'Purva Ashadha',
  'Uttara Ashadha',
  'Shravana',
  'Dhanishta',
  'Shatabhisha',
  'Purva Bhadrapada',
  'Uttara Bhadrapada',
  'Revati',
];

const NAKSHATRA_LORDS = [
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
];

const NAKSHATRA_BASE_SIGNS = [
  0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8, 9, 9, 10, 10, 11, 11, 11,
];

const SPLIT_NAKSHATRAS = new Set([
  'Krittika',
  'Mrigashira',
  'Uttara Phalguni',
  'Chitra',
  'Vishakha',
  'Uttara Ashadha',
  'Dhanishta',
  'Purva Bhadrapada',
]);

const RASHI_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
const RASHI_LORDS = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
const MULA_INDEX = 18;
const PURVASHADA_INDEX = 19;

function normalizeIndex(index) {
  return ((index % 27) + 27) % 27;
}

function longitudeToNakshatra(longitude) {
  const span = 360 / 27;
  const lon = Number(longitude) || 0;
  const idx = Math.min(Math.max(Math.floor(((lon % 360) + 360) % 360 / span), 0), 26);
  const degreeInNakshatra = ((lon % 360) + 360) % 360 % span;
  const pada = Math.min(4, Math.floor(degreeInNakshatra / (span / 4)) + 1);
  return {
    index: idx,
    name: NAKSHATRA_NAMES[idx],
    lord: NAKSHATRA_LORDS[idx],
    degree_in_nakshatra: Number(degreeInNakshatra.toFixed(4)),
    pada,
  };
}

function countExclusiveStart(startIndex, endIndex) {
  // Counts inclusively from the start nakshatra to the end nakshatra.
  return ((endIndex - startIndex + 27) % 27) + 1;
}

function countForwardFrom(startIndex, steps) {
  return normalizeIndex(startIndex + steps - 1);
}

export function calculateMudakkuLocal(chartData = {}) {
  const sunLongitude = chartData?.planets?.Sun?.longitude;
  if (sunLongitude == null) {
    return null;
  }

  const sunNak = longitudeToNakshatra(sunLongitude);
  const countToMula = countExclusiveStart(sunNak.index, MULA_INDEX);
  const mudakkuIndex = countForwardFrom(PURVASHADA_INDEX, countToMula);
  const mudakkuLongitude = mudakkuIndex * (360 / 27);
  const mudakkuNak = longitudeToNakshatra(mudakkuLongitude);
  const mudakkuSignIndex = NAKSHATRA_BASE_SIGNS[mudakkuIndex];
  const mudakkuRashi = RASHI_NAMES[mudakkuSignIndex];

  return {
    sun_nakshatra: sunNak,
    count_to_mula: countToMula,
    mudakku_nakshatra: {
      index: mudakkuNak.index + 1,
      name: mudakkuNak.name,
      lord: mudakkuNak.lord,
      pada: mudakkuNak.pada,
      degree_in_nakshatra: mudakkuNak.degree_in_nakshatra,
    },
    mudakku_point: {
      longitude: mudakkuSignIndex * 30 + 15,
      sign: mudakkuSignIndex,
      degree: 15,
      sign_name: mudakkuRashi,
      nakshatra: mudakkuNak.name,
    },
    mudakku_rashi: mudakkuRashi,
    mudakku_rashi_lord: RASHI_LORDS[mudakkuSignIndex] || 'Unknown',
    is_split_nakshatra: SPLIT_NAKSHATRAS.has(mudakkuNak.name),
    method: {
      count_from: sunNak.name,
      count_to: 'Mula',
      restart_from: 'Purvashada',
      special_rashi_rule: 'Use first pada / first sign when the landing nakshatra spans two signs.',
    },
  };
}
