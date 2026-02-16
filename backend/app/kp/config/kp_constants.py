from enum import Enum

# KP Ayanamsa
KP_AYANAMSA = 23.85  # Approximate value, should be calculated dynamically

# Nakshatra data with lords and sub-divisions
NAKSHATRAS = [
    {"name": "Ashwini", "lord": "Ketu", "start": 0.0, "end": 13.333333333333334},
    {"name": "Bharani", "lord": "Venus", "start": 13.333333333333334, "end": 26.666666666666668},
    {"name": "Krittika", "lord": "Sun", "start": 26.666666666666668, "end": 40.0},
    {"name": "Rohini", "lord": "Moon", "start": 40.0, "end": 53.333333333333336},
    {"name": "Mrigashira", "lord": "Mars", "start": 53.333333333333336, "end": 66.66666666666667},
    {"name": "Ardra", "lord": "Rahu", "start": 66.66666666666667, "end": 80.0},
    {"name": "Punarvasu", "lord": "Jupiter", "start": 80.0, "end": 93.33333333333334},
    {"name": "Pushya", "lord": "Saturn", "start": 93.33333333333334, "end": 106.66666666666667},
    {"name": "Ashlesha", "lord": "Mercury", "start": 106.66666666666667, "end": 120.0},
    {"name": "Magha", "lord": "Ketu", "start": 120.0, "end": 133.33333333333334},
    {"name": "Purva Phalguni", "lord": "Venus", "start": 133.33333333333334, "end": 146.66666666666669},
    {"name": "Uttara Phalguni", "lord": "Sun", "start": 146.66666666666669, "end": 160.0},
    {"name": "Hasta", "lord": "Moon", "start": 160.0, "end": 173.33333333333334},
    {"name": "Chitra", "lord": "Mars", "start": 173.33333333333334, "end": 186.66666666666669},
    {"name": "Swati", "lord": "Rahu", "start": 186.66666666666669, "end": 200.0},
    {"name": "Vishakha", "lord": "Jupiter", "start": 200.0, "end": 213.33333333333334},
    {"name": "Anuradha", "lord": "Saturn", "start": 213.33333333333334, "end": 226.66666666666669},
    {"name": "Jyeshtha", "lord": "Mercury", "start": 226.66666666666669, "end": 240.0},
    {"name": "Mula", "lord": "Ketu", "start": 240.0, "end": 253.33333333333334},
    {"name": "Purva Ashadha", "lord": "Venus", "start": 253.33333333333334, "end": 266.6666666666667},
    {"name": "Uttara Ashadha", "lord": "Sun", "start": 266.6666666666667, "end": 280.0},
    {"name": "Shravana", "lord": "Moon", "start": 280.0, "end": 293.33333333333337},
    {"name": "Dhanishtha", "lord": "Mars", "start": 293.33333333333337, "end": 306.6666666666667},
    {"name": "Shatabhisha", "lord": "Rahu", "start": 306.6666666666667, "end": 320.0},
    {"name": "Purva Bhadrapada", "lord": "Jupiter", "start": 320.0, "end": 333.33333333333337},
    {"name": "Uttara Bhadrapada", "lord": "Saturn", "start": 333.33333333333337, "end": 346.6666666666667},
    {"name": "Revati", "lord": "Mercury", "start": 346.6666666666667, "end": 360.0}
]

# Removed destructive normalization loop that caused precision errors


# Sub-lord divisions (Original Vimshottari periods in years)
SUB_LORD_DIVISIONS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17
}

# Planet order for sub-lord calculations
PLANET_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# Event houses mapping
EVENT_HOUSES = {
    "marriage": [2, 7, 11],
    "career": [2, 6, 10, 11],
    "health": [1, 6, 8, 12],
    "education": [2, 4, 5, 9, 11],
    "children": [2, 5, 11],
    "property": [2, 4, 11, 12],
    "travel": [3, 9, 12],
    "litigation": [6, 8, 12],
    "spirituality": [1, 5, 8, 9, 12],
    "wealth": [2, 11]
}

class KPPlanet(Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"

class KPHouse(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    SIXTH = 6
    SEVENTH = 7
    EIGHTH = 8
    NINTH = 9
    TENTH = 10
    ELEVENTH = 11
    TWELFTH = 12