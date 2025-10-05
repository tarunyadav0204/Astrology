# Transit and Astrological Configuration

# Planet movement speeds (degrees per month)
PLANET_SPEEDS = {
    'Sun': 12, 'Moon': 1, 'Mars': 6, 'Mercury': 12, 
    'Jupiter': 1, 'Venus': 12, 'Saturn': 0.4, 'Rahu': -0.05, 'Ketu': -0.05
}

# Swiss Ephemeris planet numbers
PLANET_NUMBERS = {
    'Sun': 0, 'Moon': 1, 'Mars': 4, 'Mercury': 2, 
    'Jupiter': 5, 'Venus': 3, 'Saturn': 6
}

# Transit planets list
TRANSIT_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

# Conjunction strengths by planet
CONJUNCTION_STRENGTHS = {
    'Jupiter': 85, 'Saturn': 80, 'Mars': 75, 'Sun': 70, 'Venus': 75, 
    'Mercury': 65, 'Moon': 60, 'Rahu': 70, 'Ketu': 70
}

# Opposition strengths by planet
OPPOSITION_STRENGTHS = {
    'Jupiter': 75, 'Saturn': 75, 'Mars': 70, 'Sun': 65, 'Venus': 60, 
    'Mercury': 55, 'Moon': 50, 'Rahu': 65, 'Ketu': 65
}

# Special aspect strengths
SPECIAL_ASPECT_STRENGTHS = {
    'Mars': {'4th_aspect': 65, '8th_aspect': 65},
    'Jupiter': {'5th_aspect': 75, '9th_aspect': 75},
    'Saturn': {'3rd_aspect': 70, '10th_aspect': 70},
    'Rahu': {'3rd_aspect': 60, '11th_aspect': 60},
    'Ketu': {'3rd_aspect': 60, '11th_aspect': 60}
}

# Vimshottari Dasha periods (in years)
DASHA_PERIODS = {
    'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
    'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17
}

# Nakshatra ruling planets (27 nakshatras)
NAKSHATRA_LORDS = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
]

# Planet order for Dasha sequence
PLANET_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']

# Panchang names
TITHI_NAMES = [
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi',
    'Saptami', 'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi',
    'Trayodashi', 'Chaturdashi', 'Purnima/Amavasya'
]

VARA_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

NAKSHATRA_NAMES = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]

YOGA_NAMES = [
    'Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda',
    'Sukarman', 'Dhriti', 'Shula', 'Ganda', 'Vriddhi', 'Dhruva',
    'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyan',
    'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla',
    'Brahma', 'Indra', 'Vaidhriti'
]

KARANA_NAMES = [
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija',
    'Vishti', 'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna'
]

# Sign names
SIGN_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
              'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# Natural friendship
NATURAL_FRIENDS = {
    'Sun': ['Moon', 'Mars', 'Jupiter'],
    'Moon': ['Sun', 'Mercury'],
    'Mars': ['Sun', 'Moon', 'Jupiter'],
    'Mercury': ['Sun', 'Venus'],
    'Jupiter': ['Sun', 'Moon', 'Mars'],
    'Venus': ['Mercury', 'Saturn'],
    'Saturn': ['Mercury', 'Venus'],
    'Rahu': [],
    'Ketu': []
}

NATURAL_ENEMIES = {
    'Sun': ['Venus', 'Saturn'],
    'Moon': ['None'],
    'Mars': ['Mercury'],
    'Mercury': ['Moon'],
    'Jupiter': ['Mercury', 'Venus'],
    'Venus': ['Sun', 'Moon'],
    'Saturn': ['Sun', 'Moon', 'Mars'],
    'Rahu': ['Sun', 'Moon', 'Mars'],
    'Ketu': ['Sun', 'Moon', 'Mars']
}