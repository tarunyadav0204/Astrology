# KP Sub/Sub-Sub Lord calculator - Exact working code
from math import floor

# ---- Configuration ----
NK_RULER_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
TOTAL_DASHA = sum(VIMSHOTTARI_YEARS)
PROPORTIONS = [y / TOTAL_DASHA for y in VIMSHOTTARI_YEARS]
NAKSPAN_DEG = 13 + 1/3  # 13°20′

def normalize_long(long_deg):
    long = float(long_deg) % 360.0
    return long

def find_sublord(long_deg):
    long = normalize_long(long_deg)
    nak_idx = int(long // NAKSPAN_DEG)
    if nak_idx >= 27:
        nak_idx = 26
    nak_start = nak_idx * NAKSPAN_DEG
    offset = long - nak_start
    bounds = []
    cum = 0.0
    for p in PROPORTIONS:
        span = p * NAKSPAN_DEG
        bounds.append((cum, cum + span))
        cum += span
    for i, (bstart, bend) in enumerate(bounds):
        if offset >= bstart and offset < bend or (i == len(bounds) - 1 and offset <= bend):
            sub_ruler = NK_RULER_SEQUENCE[i]
            sub_start = nak_start + bstart
            sub_end = nak_start + bend
            sub_span = bend - bstart
            return i, sub_ruler, sub_start, sub_end, sub_span

def find_sub_sublord(long_deg):
    long = normalize_long(long_deg)
    sub_index, sub_lord, sub_start, sub_end, sub_span = find_sublord(long)
    cum = 0.0
    for p in PROPORTIONS:
        span = p * sub_span
        start = sub_start + cum
        end = start + span
        if long >= start and long < end or end >= long:
            subsub_lord = NK_RULER_SEQUENCE[PROPORTIONS.index(p)]
            return subsub_lord
        cum += span
    return NK_RULER_SEQUENCE[0]