# KP Sub/Sub-Sub Lord calculator - Rotational KP Logic
from math import floor

# ---- Configuration ----
NK_RULER_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
TOTAL_DASHA = 120.0
PROPORTIONS = [y / TOTAL_DASHA for y in VIMSHOTTARI_YEARS]
NAKSPAN_DEG = 360.0 / 27.0  # Exactly 13°20'

def normalize_long(long_deg):
    """Normalize longitude to 0-360 range."""
    return float(long_deg) % 360.0

def _get_rotated_sequences(start_lord):
    """Helper to rotate ruler and proportion sequences to start with a specific lord."""
    try:
        start_idx = NK_RULER_SEQUENCE.index(start_lord)
    except ValueError:
        start_idx = 0  # Fallback
    
    rotated_rulers = NK_RULER_SEQUENCE[start_idx:] + NK_RULER_SEQUENCE[:start_idx]
    rotated_proportions = PROPORTIONS[start_idx:] + PROPORTIONS[:start_idx]
    
    return rotated_rulers, rotated_proportions

def find_sublord(long_deg):
    """Calculate sub-lord using the standard KP method."""
    long = normalize_long(long_deg)
    nak_idx = int(long // NAKSPAN_DEG)
    
    # The sequence starts with the Nakshatra's lord
    nak_lord = NK_RULER_SEQUENCE[nak_idx % 9]
    rotated_rulers, rotated_proportions = _get_rotated_sequences(nak_lord)

    nak_start = nak_idx * NAKSPAN_DEG
    offset = long - nak_start
    
    cum = 0.0
    for i, p in enumerate(rotated_proportions):
        span = p * NAKSPAN_DEG
        bstart = cum
        bend = cum + span
        
        # Check if offset is within the sub-lord's span
        if (offset >= bstart and offset < bend) or (i == len(rotated_proportions) - 1 and abs(offset - bend) < 1e-12):
            sub_ruler = rotated_rulers[i]
            sub_start = nak_start + bstart
            sub_end = nak_start + bend
            sub_span = bend - bstart
            
            original_ruler_index = NK_RULER_SEQUENCE.index(sub_ruler)
            return original_ruler_index, sub_ruler, sub_start, sub_end, sub_span
            
        cum += span
    
    return 0, NK_RULER_SEQUENCE[0], nak_start, nak_start + (PROPORTIONS[0] * NAKSPAN_DEG), (PROPORTIONS[0] * NAKSPAN_DEG)

def find_sub_sublord(long_deg):
    """Calculate sub-sub-lord using the 'Straight' KP method (Standard)."""
    long = normalize_long(long_deg)
    # Get the sub-lord details first
    _, sub_lord, sub_start, sub_end, sub_span = find_sublord(long_deg)
    
    # Standard 'Straight' method for SSL: 
    # The sequence of Sub-Sub Lords within a Sub-Lord always starts with the Sub-Lord itself.
    # We rotate the sequence to start with the sub_lord.
    rotated_rulers, rotated_proportions = _get_rotated_sequences(sub_lord)
    
    offset_in_sub = long - sub_start

    cum_prop = 0.0
    for i, p in enumerate(rotated_proportions):
        # The SSL span is (Planet's Proportion) * (Sub-Lord's Span)
        # Sub-Lord's Span is (Sub-Lord's Proportion) * (Nakshatra Span)
        prop_span = p * sub_span
        
        # Use a slightly more robust comparison for floating point
        if offset_in_sub < cum_prop + prop_span - 1e-12:
            return rotated_rulers[i]
            
        cum_prop += prop_span
        
    return rotated_rulers[-1]
