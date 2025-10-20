# Natural Benefic/Malefic Configuration

# Natural Benefics (inherently positive planets)
NATURAL_BENEFICS = ['Jupiter', 'Venus', 'Mercury', 'Moon']

# Natural Malefics (inherently challenging planets)
NATURAL_MALEFICS = ['Mars', 'Saturn', 'Rahu', 'Ketu']

# Natural Neutral (depends on other factors)
NATURAL_NEUTRALS = ['Sun']  # Sun can be benefic or malefic based on context

# Temporal Benefic/Malefic based on current Dasha Lord
# When a planet is the current dasha lord, it becomes temporally benefic
TEMPORAL_BENEFIC_MULTIPLIER = 1.3  # Dasha lord gets enhanced power
TEMPORAL_NEUTRAL_MULTIPLIER = 1.0  # Non-dasha planets remain normal

# Combined analysis priorities (most important to least)
BENEFIC_MALEFIC_PRIORITY = [
    'temporal',      # Current dasha lord status (highest priority)
    'functional',    # Functional nature for ascendant
    'natural'        # Natural benefic/malefic nature
]