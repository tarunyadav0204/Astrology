"""Canonical Mrityu Bhaga tables and degree-span evaluation.

The traditional values are ordinal degrees: the 20th degree is the arc from
19°00′ up to (but not including) 20°00′.  Textual tables are kept named rather
than blended.  The application default is the Jataka Parijata / Sarvartha
Chintamani table; Phaladeepika's differing Moon and Ascendant rows are
available explicitly.
"""
from typing import Any, Dict, Mapping, Tuple


JATAKA_PARIJATA_SARVARTHA: Dict[str, Tuple[int, ...]] = {
    'Sun': (20, 9, 12, 6, 8, 24, 16, 17, 22, 2, 3, 23),
    'Moon': (8, 25, 22, 22, 21, 1, 4, 23, 18, 20, 20, 10),
    'Mars': (19, 28, 25, 23, 29, 28, 14, 21, 2, 15, 11, 6),
    'Mercury': (15, 14, 13, 12, 8, 18, 20, 10, 21, 22, 7, 5),
    'Jupiter': (19, 29, 12, 27, 6, 4, 13, 10, 17, 11, 15, 28),
    'Venus': (28, 15, 11, 17, 10, 13, 4, 6, 27, 12, 29, 19),
    'Saturn': (10, 4, 7, 9, 12, 16, 3, 18, 28, 14, 13, 15),
    'Rahu': (14, 13, 12, 11, 24, 23, 22, 21, 10, 20, 18, 8),
    'Ketu': (8, 18, 20, 10, 21, 22, 23, 24, 11, 12, 13, 14),
    'Mandi': (23, 24, 11, 12, 13, 14, 8, 18, 20, 10, 21, 22),
    'Ascendant': (1, 9, 22, 22, 25, 2, 4, 23, 18, 20, 24, 10),
}

PHALADEEPIKA_MOON: Tuple[int, ...] = (26, 12, 13, 25, 24, 11, 26, 14, 13, 25, 5, 12)
PHALADEEPIKA_ASCENDANT: Tuple[int, ...] = (8, 9, 22, 22, 25, 14, 4, 23, 18, 20, 21, 10)

TABLES: Dict[str, Dict[str, Tuple[int, ...]]] = {
    'jataka_parijata_sarvartha_chintamani': JATAKA_PARIJATA_SARVARTHA,
    'phaladeepika': {
        **JATAKA_PARIJATA_SARVARTHA,
        'Moon': PHALADEEPIKA_MOON,
        'Ascendant': PHALADEEPIKA_ASCENDANT,
    },
}

TABLE_REFERENCES = {
    'jataka_parijata_sarvartha_chintamani': 'Jataka Parijata and Sarvartha Chintamani traditional table',
    'phaladeepika': 'Phaladeepika, chapter 13, verse 11 (Moon and Lagna variants are preserved)',
}


def evaluate_mrityu_bhaga(
    point_name: str,
    longitude: float,
    *,
    table_key: str = 'jataka_parijata_sarvartha_chintamani',
) -> Dict[str, Any]:
    table: Mapping[str, Tuple[int, ...]] = TABLES[table_key]
    if point_name not in table:
        return {'is_mrityu_bhaga': False, 'applicable': False, 'point': point_name}
    lon = float(longitude) % 360.0
    sign = int(lon / 30.0)
    degree = lon % 30.0
    ordinal = table[point_name][sign]
    start = float(ordinal - 1)
    end = float(ordinal)
    qualifies = start <= degree < end
    distance = 0.0 if qualifies else min(abs(degree - start), abs(degree - end))
    return {
        'point': point_name,
        'applicable': True,
        'is_mrityu_bhaga': qualifies,
        'sign': sign,
        'degree_in_sign': round(degree, 6),
        'traditional_degree': ordinal,
        'degree_span_start': start,
        'degree_span_end': end,
        'distance_from_span': round(distance, 6),
        'table_key': table_key,
        'source': TABLE_REFERENCES[table_key],
        'interpretation_scope': 'A sensitive natal degree; it is not a standalone prediction of death or disease.',
    }
