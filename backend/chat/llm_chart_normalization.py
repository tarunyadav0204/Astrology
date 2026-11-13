"""Copy-only chart normalization at LLM serialization boundaries.

Calculators and agent builders keep their native schemas. Raw sign/sign_id fields
are zero-based; compact s/z and explicit sign_number fields are already one-based.
Named values make this transform idempotent, including cache/fallback paths.
"""
import json
import math

SIGNS = ('Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces')
INDEXING_INSTRUCTION = (
    'CHART COORDINATES: Signs are named; explicit sign_number and compact sign '
    's/z values use 1=Aries through 12=Pisces. Houses use 1–12 in the stated '
    'chart/reference frame. Never shift a house or sign by one. Use each divisional '
    'chart\'s own ascendant, not the D1 ascendant. SAV/BAV sign maps use sign names; '
    'use Ho/Ho9 for house bindus. Missing/zero house values mean unavailable, not house 1.'
)
# These are user statements, not calculated chart coordinates.
_OPAQUE = {'user_facts', 'history', 'conversation_history', 'recent_conversation',
           'birth_data', 'birth_details', 'user_context', 'extracted_context'}
_SIGN_FIELDS = set("""sign a_sign activated_sign antardasha_sign arudha_lagna_sign asc_sign
ascendant_sign b_sign base_sign contributor_sign current_ad_sign current_md_sign
current_sign cusp_sign d10_sign d1_sign d3_ascendant_sign d7_fifth_house_sign
d7_ninth_house_sign d7_second_house_sign d9_reference_sign d9_sign danger_sign
debilitation_sign deha_sign derived_ascendant_sign fourth_sign from_sign house_sign
indu_lagna_sign jeeva_sign jupiter_sign karkamsa_sign karma_bhava_sign lagna_sign
lord_sign maha_sign mahadasha_sign mars_sign moon_d9_sign moon_sign muntha_sign
natal_moon_sign natal_sign native_sign navamsa_sign ninth_from_ascendant_sign
ninth_from_moon_sign own_sign partner_sign placement_sign planet_sign position_sign
reference_sign saturn_sign sensitive_sign seventh_house_sign source_sign start_sign
strongest_sign swamsa_sign target_ascendant_sign target_sign to_sign transit_sign
ul_sign venus_sign weakest_sign""".split())
_SIGN_MAPS = {'bindus', 'sarvashtakavarga', 'sign_totals', 'rashi_aspects',
              'sign_aspects', 'sign_strengths'}


def _index(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(value) and value == int(value) and 0 <= value < 12:
        return int(value)
    return None


def normalize_chart_evidence(value, *, _key='', _base=0):
    """Normalize known raw coordinate fields, never mutate calculator evidence."""
    if isinstance(value, (list, tuple)):
        return [normalize_chart_evidence(v, _key=_key, _base=_base) for v in value]
    if not isinstance(value, dict):
        return value
    if str(value.get('sign_numbering', '')).startswith('1=Aries'):
        _base = 1
    out = {}
    compact_av = ('S' in value and 'B' in value) or 'S9' in value or 'B9' in value
    for key, child in value.items():
        if key == 'sarvashtakavarga_key_legend':
            out[key] = 'Keys are zodiac sign names Aries through Pisces, not houses from lagna.'
            continue
        if key in _OPAQUE:
            out[key] = child
            continue
        # Compact AV vectors are zodiac rows, not houses. Make their labels explicit.
        if compact_av and key in {'S', 'S9'} and isinstance(child, list) and len(child) == 12:
            out[key] = dict(zip(SIGNS, child))
            continue
        if compact_av and key in {'B', 'B9'} and isinstance(child, dict):
            out[key] = {p: dict(zip(SIGNS, row)) if isinstance(row, list) and len(row) == 12
                        else normalize_chart_evidence(row) for p, row in child.items()}
            continue
        if _key in _SIGN_MAPS and str(key).isdigit() and 0 <= int(key) < 12:
            key = SIGNS[int(key)]
        if _key in {'sign_aspects', 'rashi_aspects'} and isinstance(child, list):
            out[key] = [SIGNS[i] if (i := _index(v)) is not None else v for v in child]
            continue
        if _key == 'raw_sign_order' and key == 'sav' and isinstance(child, list) and len(child) == 12:
            out[key] = dict(zip(SIGNS, child))
            continue
        idx = _index(child)
        if key == 'sign' and isinstance(child, (int, float)) and not isinstance(child, bool):
            lon = value.get('longitude')
            if isinstance(lon, (int, float)) and math.isfinite(lon) and 0 <= lon < 360:
                idx = int(lon // 30)
            elif (_base == 1 or _key == 'muntha') and 1 <= child <= 12:
                idx = int(child) - 1
        if idx is not None and key in _SIGN_FIELDS:
            # Explicit names can also accompany a one-based external tool result.
            named = value.get(key + '_name') if key != 'sign' else value.get('sign_name')
            out[key] = named if named in SIGNS else SIGNS[idx]
            continue
        if idx is not None and (key in {'sign_id', 'sign_index'} or key.endswith(('_sign_id', '_sign_index'))):
            stem = key.rsplit('_', 1)[0]
            out[stem + '_number'] = idx + 1
            out.setdefault(stem + '_name', SIGNS[idx])
            continue
        out[key] = normalize_chart_evidence(child, _key=str(key), _base=_base)
    # Raw chart ascendants are absolute longitudes, including D9/D10/recast charts.
    asc = value.get('ascendant')
    if isinstance(asc, (int, float)) and not isinstance(asc, bool) and math.isfinite(asc) and 0 <= asc < 360:
        idx = int(asc // 30)
        out['ascendant_sign_name'] = SIGNS[idx]
        out['ascendant_sign_number'] = idx + 1
    return out


def llm_json_dumps(value, **kwargs):
    normalized = normalize_chart_evidence(value)
    if isinstance(normalized, dict):
        normalized = {'chart_coordinate_convention': INDEXING_INSTRUCTION, **normalized}
    return json.dumps(normalized, **kwargs)
