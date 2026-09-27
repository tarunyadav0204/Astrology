"""Compatibility exports backed by the canonical BPHS Chapter 34 calculator."""

from calculators.classical_functional_nature import (
    calculate_functional_nature,
    compatibility_lists,
    functional_nature_table,
)


FUNCTIONAL_BENEFICS, FUNCTIONAL_MALEFICS, FUNCTIONAL_NEUTRALS = compatibility_lists()


def get_functional_nature(ascendant_sign, planet):
    """Return the complete classical result; old list exports remain stable."""
    return calculate_functional_nature(ascendant_sign, planet)


def get_functional_nature_table(ascendant_sign):
    return functional_nature_table(ascendant_sign)

# Functional nature multipliers for prediction intensity
FUNCTIONAL_MULTIPLIERS = {
    'benefic': 1.2,      # Functional benefics enhance positive effects
    'malefic': 0.8,      # Functional malefics reduce positive effects
    'neutral': 1.0       # Neutral planets have standard effects
}
