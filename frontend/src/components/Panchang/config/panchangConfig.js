export const TITHI_NAMES = [
  'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
  'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
  'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
  'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'
];

export const VARA_NAMES = [
  'Ravivaar', 'Somvaar', 'Mangalvaar', 'Budhvaar', 
  'Guruvaar', 'Shukravaar', 'Shanivaar'
];

export const VARA_ENGLISH = [
  'Sunday', 'Monday', 'Tuesday', 'Wednesday', 
  'Thursday', 'Friday', 'Saturday'
];

export const VARA_LORDS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 
  'Jupiter', 'Venus', 'Saturn'
];

export const NAKSHATRA_NAMES = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira',
  'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha',
  'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
  'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
  'Uttara Bhadrapada', 'Revati'
];

export const NAKSHATRA_LORDS = [
  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
  'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu',
  'Venus', 'Sun', 'Moon', 'Mars', 'Rahu',
  'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus',
  'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
  'Saturn', 'Mercury'
];

export const YOGA_NAMES = [
  'Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana',
  'Atiganda', 'Sukarma', 'Dhriti', 'Shula', 'Ganda',
  'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra',
  'Siddhi', 'Vyatipata', 'Variyan', 'Parigha', 'Shiva',
  'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma',
  'Indra', 'Vaidhriti'
];

export const KARANA_NAMES = [
  'Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara',
  'Vanija', 'Vishti', 'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna'
];

export const RAHU_KAAL_TIMINGS = {
  0: { start: 16.5, duration: 1.5 }, // Sunday
  1: { start: 7.5, duration: 1.5 },  // Monday
  2: { start: 15, duration: 1.5 },   // Tuesday
  3: { start: 12, duration: 1.5 },   // Wednesday
  4: { start: 13.5, duration: 1.5 }, // Thursday
  5: { start: 10.5, duration: 1.5 }, // Friday
  6: { start: 9, duration: 1.5 }     // Saturday
};

export const YAMAGANDA_TIMINGS = {
  0: { start: 12, duration: 1.5 },   // Sunday
  1: { start: 10.5, duration: 1.5 }, // Monday
  2: { start: 9, duration: 1.5 },    // Tuesday
  3: { start: 7.5, duration: 1.5 },  // Wednesday
  4: { start: 6, duration: 1.5 },    // Thursday
  5: { start: 15, duration: 1.5 },   // Friday
  6: { start: 13.5, duration: 1.5 }  // Saturday
};

export const GULIKA_TIMINGS = {
  0: { start: 15, duration: 1.5 },   // Sunday
  1: { start: 13.5, duration: 1.5 }, // Monday
  2: { start: 12, duration: 1.5 },   // Tuesday
  3: { start: 10.5, duration: 1.5 }, // Wednesday
  4: { start: 9, duration: 1.5 },    // Thursday
  5: { start: 7.5, duration: 1.5 },  // Friday
  6: { start: 6, duration: 1.5 }     // Saturday
};

export const CHOGHADIYA_NAMES = [
  'Udveg', 'Char', 'Labh', 'Amrit', 'Kaal', 'Shubh', 'Rog', 'Udveg'
];

export const CHOGHADIYA_QUALITY = {
  'Udveg': 'Inauspicious',
  'Char': 'Good for travel',
  'Labh': 'Profitable',
  'Amrit': 'Excellent',
  'Kaal': 'Inauspicious',
  'Shubh': 'Auspicious',
  'Rog': 'Inauspicious'
};

export const HORA_SEQUENCE = [
  'Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars'
];

export const CALENDAR_SYSTEMS = {
  GREGORIAN: 'gregorian',
  VIKRAM_SAMVAT: 'vikram_samvat',
  SAKA_SAMVAT: 'saka_samvat',
  BENGALI: 'bengali',
  TAMIL: 'tamil'
};

export const PAKSHA_TYPES = {
  SHUKLA: 'Shukla Paksha',
  KRISHNA: 'Krishna Paksha'
};

export const MOON_PHASES = {
  NEW_MOON: 'New Moon',
  WAXING_CRESCENT: 'Waxing Crescent',
  FIRST_QUARTER: 'First Quarter',
  WAXING_GIBBOUS: 'Waxing Gibbous',
  FULL_MOON: 'Full Moon',
  WANING_GIBBOUS: 'Waning Gibbous',
  LAST_QUARTER: 'Last Quarter',
  WANING_CRESCENT: 'Waning Crescent'
};

export const ACTIVITY_CATEGORIES = {
  SPIRITUAL: 'Spiritual',
  BUSINESS: 'Business',
  PERSONAL: 'Personal',
  CEREMONIES: 'Ceremonies',
  HEALTH: 'Health',
  EDUCATION: 'Education',
  TRAVEL: 'Travel',
  CONSTRUCTION: 'Construction'
};

export const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
];

export const PLANET_NAMES = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'
];