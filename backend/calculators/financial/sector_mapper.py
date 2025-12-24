# calculators/financial/sector_mapper.py

SECTOR_RULES = {
    "Banking & Finance": {
        "ruler": "Jupiter",
        "benefics": ["Mercury", "Venus"],
        "malefics": ["Rahu", "Ketu"],
        "bullish_signs": [8, 11, 3],  # Sagittarius, Pisces, Cancer (0-indexed)
        "bearish_signs": [9],  # Capricorn
        "nakshatras": ["Punarvasu", "Pushya", "Vishakha", "Purva Bhadrapada"]
    },
    "Technology & AI": {
        "ruler": "Mercury",
        "benefics": ["Rahu", "Venus"],
        "malefics": ["Mars", "Ketu"],
        "bullish_signs": [2, 5, 10],  # Gemini, Virgo, Aquarius
        "bearish_signs": [11],  # Pisces
        "nakshatras": ["Ardra", "Shatabhisha", "Hastha", "Swati"]
    },
    "Real Estate & Infrastructure": {
        "ruler": "Mars",
        "benefics": ["Saturn", "Venus"],
        "malefics": ["Mercury", "Rahu"],
        "bullish_signs": [0, 7, 9],  # Aries, Scorpio, Capricorn
        "bearish_signs": [3],  # Cancer
        "nakshatras": ["Dhanishta", "Chitra", "Mrigashira"]
    },
    "Pharma & Healthcare": {
        "ruler": "Sun",
        "benefics": ["Jupiter", "Mars"],
        "malefics": ["Saturn", "Rahu"],
        "bullish_signs": [4, 0],  # Leo, Aries
        "bearish_signs": [6],  # Libra
        "nakshatras": ["Ashwini", "Shatabhisha", "Mula"]
    },
    "Auto & Luxury": {
        "ruler": "Venus",
        "benefics": ["Mercury", "Saturn"],
        "malefics": ["Sun", "Mars"],
        "bullish_signs": [1, 6, 11],  # Taurus, Libra, Pisces
        "bearish_signs": [5],  # Virgo
        "nakshatras": ["Rohini", "Bharani", "Purva Phalguni"]
    },
    "Metals & Heavy Industry": {
        "ruler": "Saturn",
        "benefics": ["Mars"],
        "malefics": ["Sun"],
        "bullish_signs": [9, 10, 6],  # Capricorn, Aquarius, Libra
        "bearish_signs": [0],  # Aries
        "nakshatras": ["Pushya", "Anuradha", "Uttara Bhadrapada"]
    },
    "Energy & Oil": {
        "ruler": "Sun",
        "benefics": ["Mars", "Jupiter"],
        "malefics": ["Saturn", "Ketu"],
        "bullish_signs": [4, 0, 7],  # Leo, Aries, Scorpio
        "bearish_signs": [6],  # Libra
        "nakshatras": ["Krittika", "Uttara Phalguni", "Uttara Ashadha"]
    },
    "FMCG & Consumer": {
        "ruler": "Moon",
        "benefics": ["Venus", "Jupiter"],
        "malefics": ["Saturn", "Rahu"],
        "bullish_signs": [3, 1],  # Cancer, Taurus
        "bearish_signs": [7],  # Scorpio
        "nakshatras": ["Rohini", "Hasta", "Shravana"]
    },
    "Gold": {
        "ruler": "Sun",
        "benefics": ["Jupiter", "Mars"],
        "malefics": ["Saturn", "Rahu"],
        "bullish_signs": [4, 0],  # Leo, Aries
        "bearish_signs": [6, 10],  # Libra, Aquarius
        "nakshatras": ["Krittika", "Uttara Phalguni", "Uttara Ashadha"]
    },
    "Silver": {
        "ruler": "Moon",
        "benefics": ["Venus", "Mercury"],
        "malefics": ["Mars", "Ketu"],
        "bullish_signs": [3, 1],  # Cancer, Taurus
        "bearish_signs": [7, 9],  # Scorpio, Capricorn
        "nakshatras": ["Rohini", "Hasta", "Shravana"]
    },
    "Copper": {
        "ruler": "Mars",
        "benefics": ["Sun", "Jupiter"],
        "malefics": ["Saturn", "Mercury"],
        "bullish_signs": [0, 7],  # Aries, Scorpio
        "bearish_signs": [3, 6],  # Cancer, Libra
        "nakshatras": ["Mrigashira", "Chitra", "Dhanishta"]
    },
    "Iron & Steel": {
        "ruler": "Saturn",
        "benefics": ["Mars", "Venus"],
        "malefics": ["Sun", "Moon"],
        "bullish_signs": [9, 10],  # Capricorn, Aquarius
        "bearish_signs": [3, 4],  # Cancer, Leo
        "nakshatras": ["Pushya", "Anuradha", "Uttara Bhadrapada"]
    }
}
