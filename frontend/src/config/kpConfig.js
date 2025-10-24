// KP System Configuration Constants
export const KP_CONFIG = {
  // Ayanamsa
  AYANAMSA: {
    KP: 'krishnamurti',
    BASE_VALUE: 23.25, // Base value for 1900
    ANNUAL_PRECESSION: 50.27 // arcseconds per year
  },

  // House System
  HOUSE_SYSTEM: 'placidus',

  // Nakshatra Configuration
  NAKSHATRAS: {
    COUNT: 27,
    PADAS_PER_NAKSHATRA: 4,
    TOTAL_SUBDIVISIONS: 249, // 27 * 9 + 6 extra
    DEGREES_PER_NAKSHATRA: 13.333333 // 360/27
  },

  // Sub-Lord Divisions
  SUB_LORDS: {
    KETU: 7,
    VENUS: 20,
    SUN: 6,
    MOON: 10,
    MARS: 7,
    RAHU: 18,
    JUPITER: 16,
    SATURN: 19,
    MERCURY: 17
  },

  // Ruling Planets Types
  RULING_PLANETS: {
    ASCENDANT_SUB_LORD: 'ascendant_sub_lord',
    MOON_SIGN_SUB_LORD: 'moon_sign_sub_lord',
    MOON_STAR_SUB_LORD: 'moon_star_sub_lord',
    DAY_LORD: 'day_lord'
  },

  // Significator Types
  SIGNIFICATOR_TYPES: {
    OWNER: 'owner',
    OCCUPANT: 'occupant',
    ASPECT: 'aspect',
    SUB_LORD: 'sub_lord'
  },

  // House Significations for Events
  EVENT_HOUSES: {
    MARRIAGE: [2, 7, 11],
    CAREER: [2, 6, 10],
    HEALTH: [1, 6, 8, 12],
    EDUCATION: [2, 4, 9, 11],
    CHILDREN: [2, 5, 11],
    TRAVEL: [3, 9, 12],
    PROPERTY: [4, 11, 12],
    LITIGATION: [6, 8, 12]
  },

  // Colors for UI
  COLORS: {
    SUB_LORD: '#2196f3',
    SIGNIFICATOR: '#4caf50',
    RULING_PLANET: '#ff9800',
    CUSP: '#9c27b0',
    PLANET: '#e91e63'
  },

  // Horary Number Range
  HORARY: {
    MIN_NUMBER: 1,
    MAX_NUMBER: 249
  }
};

// Nakshatra Names and Lords
export const NAKSHATRA_DATA = [
  { name: 'Ashwini', lord: 'Ketu', startDegree: 0 },
  { name: 'Bharani', lord: 'Venus', startDegree: 13.333333 },
  { name: 'Krittika', lord: 'Sun', startDegree: 26.666667 },
  { name: 'Rohini', lord: 'Moon', startDegree: 40 },
  { name: 'Mrigashira', lord: 'Mars', startDegree: 53.333333 },
  { name: 'Ardra', lord: 'Rahu', startDegree: 66.666667 },
  { name: 'Punarvasu', lord: 'Jupiter', startDegree: 80 },
  { name: 'Pushya', lord: 'Saturn', startDegree: 93.333333 },
  { name: 'Ashlesha', lord: 'Mercury', startDegree: 106.666667 },
  { name: 'Magha', lord: 'Ketu', startDegree: 120 },
  { name: 'P.Phalguni', lord: 'Venus', startDegree: 133.333333 },
  { name: 'U.Phalguni', lord: 'Sun', startDegree: 146.666667 },
  { name: 'Hasta', lord: 'Moon', startDegree: 160 },
  { name: 'Chitra', lord: 'Mars', startDegree: 173.333333 },
  { name: 'Swati', lord: 'Rahu', startDegree: 186.666667 },
  { name: 'Vishakha', lord: 'Jupiter', startDegree: 200 },
  { name: 'Anuradha', lord: 'Saturn', startDegree: 213.333333 },
  { name: 'Jyeshtha', lord: 'Mercury', startDegree: 226.666667 },
  { name: 'Mula', lord: 'Ketu', startDegree: 240 },
  { name: 'P.Ashadha', lord: 'Venus', startDegree: 253.333333 },
  { name: 'U.Ashadha', lord: 'Sun', startDegree: 266.666667 },
  { name: 'Shravana', lord: 'Moon', startDegree: 280 },
  { name: 'Dhanishtha', lord: 'Mars', startDegree: 293.333333 },
  { name: 'Shatabhisha', lord: 'Rahu', startDegree: 306.666667 },
  { name: 'P.Bhadrapada', lord: 'Jupiter', startDegree: 320 },
  { name: 'U.Bhadrapada', lord: 'Saturn', startDegree: 333.333333 },
  { name: 'Revati', lord: 'Mercury', startDegree: 346.666667 }
];

// Day Lords (Weekday Rulers)
export const DAY_LORDS = {
  0: 'Sun',    // Sunday
  1: 'Moon',   // Monday
  2: 'Mars',   // Tuesday
  3: 'Mercury', // Wednesday
  4: 'Jupiter', // Thursday
  5: 'Venus',  // Friday
  6: 'Saturn'  // Saturday
};