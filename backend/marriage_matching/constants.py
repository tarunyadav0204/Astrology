"""Shared constants for kundli matching."""

SIGN_NAMES = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

SIGN_LORDS = {
    1: "Mars",
    2: "Venus",
    3: "Mercury",
    4: "Moon",
    5: "Sun",
    6: "Mercury",
    7: "Venus",
    8: "Mars",
    9: "Jupiter",
    10: "Saturn",
    11: "Saturn",
    12: "Jupiter",
}

SIGN_ELEMENTS = {
    1: "Fire",
    2: "Earth",
    3: "Air",
    4: "Water",
    5: "Fire",
    6: "Earth",
    7: "Air",
    8: "Water",
    9: "Fire",
    10: "Earth",
    11: "Air",
    12: "Water",
}

NAKSHATRA_GANA = {
    1: "Deva",
    2: "Manushya",
    3: "Rakshasa",
    4: "Manushya",
    5: "Deva",
    6: "Manushya",
    7: "Deva",
    8: "Deva",
    9: "Rakshasa",
    10: "Rakshasa",
    11: "Manushya",
    12: "Manushya",
    13: "Deva",
    14: "Rakshasa",
    15: "Deva",
    16: "Rakshasa",
    17: "Deva",
    18: "Rakshasa",
    19: "Rakshasa",
    20: "Manushya",
    21: "Manushya",
    22: "Deva",
    23: "Rakshasa",
    24: "Rakshasa",
    25: "Manushya",
    26: "Manushya",
    27: "Deva",
}

NAKSHATRA_NADI = {
    idx: ("Adya" if (idx - 1) % 3 == 0 else "Madhya" if (idx - 1) % 3 == 1 else "Antya")
    for idx in range(1, 28)
}

NAKSHATRA_YONI = {
    1: "Horse",
    2: "Elephant",
    3: "Sheep",
    4: "Serpent",
    5: "Serpent",
    6: "Dog",
    7: "Cat",
    8: "Sheep",
    9: "Cat",
    10: "Rat",
    11: "Rat",
    12: "Cow",
    13: "Buffalo",
    14: "Tiger",
    15: "Buffalo",
    16: "Tiger",
    17: "Deer",
    18: "Deer",
    19: "Dog",
    20: "Monkey",
    21: "Mongoose",
    22: "Monkey",
    23: "Lion",
    24: "Horse",
    25: "Lion",
    26: "Cow",
    27: "Elephant",
}

PLANET_FRIENDSHIPS = {
    "Sun": {"friends": {"Moon", "Mars", "Jupiter"}, "enemies": {"Venus", "Saturn"}},
    "Moon": {"friends": {"Sun", "Mercury"}, "enemies": set()},
    "Mars": {"friends": {"Sun", "Moon", "Jupiter"}, "enemies": {"Mercury"}},
    "Mercury": {"friends": {"Sun", "Venus"}, "enemies": {"Moon"}},
    "Jupiter": {"friends": {"Sun", "Moon", "Mars"}, "enemies": {"Mercury", "Venus"}},
    "Venus": {"friends": {"Mercury", "Saturn"}, "enemies": {"Sun", "Moon"}},
    "Saturn": {"friends": {"Mercury", "Venus"}, "enemies": {"Sun", "Moon", "Mars"}},
}

PLANET_EXALTATION_SIGNS = {
    "Sun": 1,
    "Moon": 2,
    "Mars": 10,
    "Mercury": 6,
    "Jupiter": 4,
    "Venus": 12,
    "Saturn": 7,
}

PLANET_DEBILITATION_SIGNS = {
    "Sun": 7,
    "Moon": 8,
    "Mars": 4,
    "Mercury": 12,
    "Jupiter": 10,
    "Venus": 6,
    "Saturn": 1,
}

PLANET_OWN_SIGNS = {
    "Sun": {5},
    "Moon": {4},
    "Mars": {1, 8},
    "Mercury": {3, 6},
    "Jupiter": {9, 12},
    "Venus": {2, 7},
    "Saturn": {10, 11},
}

BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
