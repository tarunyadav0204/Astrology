export const CAREER_CONFIG = {
  // Career analysis endpoints
  endpoints: {
    tenthHouseAnalysis: '/api/career/tenth-house-analysis',
    careerSignificators: '/api/career/career-significators',
    suitableFields: '/api/career/suitable-fields',
    timingAnalysis: '/api/career/timing-analysis',
    foreignOpportunities: '/api/career/foreign-opportunities',
    financialProspects: '/api/career/financial-prospects',
    d10Analysis: '/api/career/d10-analysis',
    careerChallenges: '/api/career/challenges-remedies'
  },

  // Career significator planets
  significators: {
    Sun: { fields: ['Government', 'Leadership', 'Authority', 'Politics', 'Administration'], strength: 'high' },
    Mercury: { fields: ['Communication', 'Business', 'Writing', 'IT', 'Media', 'Trading'], strength: 'high' },
    Mars: { fields: ['Engineering', 'Military', 'Sports', 'Real Estate', 'Surgery'], strength: 'medium' },
    Jupiter: { fields: ['Teaching', 'Law', 'Finance', 'Spirituality', 'Consulting'], strength: 'high' },
    Venus: { fields: ['Arts', 'Entertainment', 'Beauty', 'Luxury Goods', 'Fashion'], strength: 'medium' },
    Saturn: { fields: ['Manufacturing', 'Service', 'Oil & Gas', 'Mining', 'Agriculture'], strength: 'medium' }
  },

  // House significance for career
  houses: {
    1: { significance: 'Personality & Approach', weight: 0.15 },
    2: { significance: 'Earned Wealth & Resources', weight: 0.20 },
    6: { significance: 'Service & Daily Work', weight: 0.15 },
    10: { significance: 'Career & Profession', weight: 0.35 },
    11: { significance: 'Gains & Income', weight: 0.15 }
  },

  // Career timing factors
  timing: {
    majorTransits: ['Jupiter', 'Saturn'],
    careerPlanets: ['Sun', 'Mercury', 'Mars', 'Jupiter', 'Venus', 'Saturn'],
    significantAges: [21, 28, 35, 42, 49, 56],
    dashaImportance: {
      mahadasha: 0.50,
      antardasha: 0.30,
      pratyantardasha: 0.20
    }
  },

  // D10 chart analysis
  d10: {
    name: 'Dasamsa',
    division: 10,
    significance: 'Career & Professional Life',
    keyFactors: ['10th Lord', 'Planets in 10th', 'Ascendant Lord', 'Arudha Pada']
  },

  // Career strength calculation weights
  strengthWeights: {
    tenthHouse: 0.25,
    tenthLord: 0.20,
    careerSignificators: 0.20,
    d10Chart: 0.15,
    dashaLords: 0.10,
    transits: 0.10
  }
};

// Zodiac signs array for reuse
export const ZODIAC_SIGNS = [
  { name: 'aries', symbol: '♈', displayName: 'Aries' },
  { name: 'taurus', symbol: '♉', displayName: 'Taurus' },
  { name: 'gemini', symbol: '♊', displayName: 'Gemini' },
  { name: 'cancer', symbol: '♋', displayName: 'Cancer' },
  { name: 'leo', symbol: '♌', displayName: 'Leo' },
  { name: 'virgo', symbol: '♍', displayName: 'Virgo' },
  { name: 'libra', symbol: '♎', displayName: 'Libra' },
  { name: 'scorpio', symbol: '♏', displayName: 'Scorpio' },
  { name: 'sagittarius', symbol: '♐', displayName: 'Sagittarius' },
  { name: 'capricorn', symbol: '♑', displayName: 'Capricorn' },
  { name: 'aquarius', symbol: '♒', displayName: 'Aquarius' },
  { name: 'pisces', symbol: '♓', displayName: 'Pisces' }
];