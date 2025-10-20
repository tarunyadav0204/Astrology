# Functional Benefic/Malefic Configuration by Ascendant

# Functional Benefics for each Ascendant (0=Aries, 1=Taurus, etc.)
FUNCTIONAL_BENEFICS = {
    0: ['Sun', 'Mars', 'Jupiter'],           # Aries: 1st, 5th, 9th lords
    1: ['Saturn', 'Mercury', 'Venus'],       # Taurus: 9th, 10th, 1st lords  
    2: ['Venus', 'Mercury', 'Saturn'],       # Gemini: 5th, 1st, 9th lords
    3: ['Mars', 'Jupiter', 'Moon'],          # Cancer: 5th, 9th, 1st lords
    4: ['Mars', 'Jupiter', 'Sun'],           # Leo: 9th, 5th, 1st lords
    5: ['Venus', 'Saturn', 'Mercury'],       # Virgo: 9th, 5th, 1st lords
    6: ['Saturn', 'Mercury', 'Venus'],       # Libra: 5th, 9th, 1st lords
    7: ['Jupiter', 'Moon', 'Mars'],          # Scorpio: 5th, 9th, 1st lords
    8: ['Mars', 'Sun', 'Jupiter'],           # Sagittarius: 5th, 9th, 1st lords
    9: ['Venus', 'Mercury', 'Saturn'],       # Capricorn: 5th, 9th, 1st lords
    10: ['Venus', 'Mercury', 'Saturn'],      # Aquarius: 5th, 9th, 1st lords
    11: ['Mars', 'Moon', 'Jupiter']          # Pisces: 5th, 9th, 1st lords
}

# Functional Malefics for each Ascendant
FUNCTIONAL_MALEFICS = {
    0: ['Mercury', 'Venus', 'Saturn'],       # Aries: 3rd, 6th, 8th, 11th lords
    1: ['Mars', 'Jupiter', 'Sun'],           # Taurus: 7th, 8th, 12th lords
    2: ['Mars', 'Jupiter', 'Sun'],           # Gemini: 6th, 7th, 8th lords  
    3: ['Saturn', 'Venus', 'Mercury'],       # Cancer: 7th, 8th, 11th lords
    4: ['Mercury', 'Venus', 'Saturn'],       # Leo: 2nd, 6th, 11th lords
    5: ['Mars', 'Jupiter', 'Sun'],           # Virgo: 3rd, 8th, 12th lords
    6: ['Mars', 'Jupiter', 'Sun'],           # Libra: 2nd, 7th, 8th lords
    7: ['Mercury', 'Venus', 'Saturn'],       # Scorpio: 8th, 11th, 12th lords
    8: ['Mercury', 'Venus', 'Saturn'],       # Sagittarius: 7th, 10th, 11th lords
    9: ['Mars', 'Jupiter', 'Sun'],           # Capricorn: 3rd, 4th, 12th lords
    10: ['Mars', 'Jupiter', 'Sun'],          # Aquarius: 3rd, 4th, 12th lords
    11: ['Mercury', 'Venus', 'Saturn']       # Pisces: 4th, 6th, 10th lords
}

# Neutral planets (neither strongly benefic nor malefic)
FUNCTIONAL_NEUTRALS = {
    0: ['Moon'],      # Aries: 4th lord
    1: ['Moon'],      # Taurus: 3rd lord
    2: ['Moon'],      # Gemini: 2nd lord
    3: ['Sun'],       # Cancer: 2nd lord
    4: ['Moon'],      # Leo: 12th lord
    5: ['Moon'],      # Virgo: 11th lord
    6: ['Moon'],      # Libra: 10th lord
    7: ['Sun'],       # Scorpio: 10th lord
    8: ['Moon'],      # Sagittarius: 8th lord
    9: ['Moon'],      # Capricorn: 7th lord
    10: ['Sun'],      # Aquarius: 7th lord
    11: ['Sun']       # Pisces: 6th lord
}

# Functional nature multipliers for prediction intensity
FUNCTIONAL_MULTIPLIERS = {
    'benefic': 1.2,      # Functional benefics enhance positive effects
    'malefic': 0.8,      # Functional malefics reduce positive effects
    'neutral': 1.0       # Neutral planets have standard effects
}