"""Source-reviewed value aliases used while compiling extracted rules.

Aliases are exact and edition-specific.  This module deliberately performs no
case folding, transliteration guessing, OCR repair or fuzzy matching.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from .nadiamsa import load_nadiamsa_table


@dataclass(frozen=True)
class ReviewedValueAlias:
    supplied_value: str
    canonical_value: str
    canonical_ordinal: int
    source_reference: str
    review_note: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


_PRABHAA_REFERENCE = (
    "Deva Keralam, Book I, PDF pages 32–36, verses 54–96; "
    "section note identifying Abala with Prabha according to C. G. Rajan"
)

NADIAMSA_NAME_ALIASES = {
    "Abala": ReviewedValueAlias(
        "Abala", "Prabhaa", 16, _PRABHAA_REFERENCE,
        "Reviewed section-name alias; Table 1 remains authoritative for the canonical spelling and ordinal.",
    ),
    "Prabha": ReviewedValueAlias(
        "Prabha", "Prabhaa", 16, _PRABHAA_REFERENCE,
        "Reviewed spelling alias; Table 1 uses Prabhaa at ordinal 16.",
    ),
}


class UnknownReviewedValue(ValueError):
    """A draft value is neither canonical source data nor a reviewed alias."""


def resolve_nadiamsa_name(value: Any, *, expected_ordinal: Optional[int] = None) -> tuple[str, Optional[ReviewedValueAlias]]:
    supplied = str(value or "").strip()
    alias = NADIAMSA_NAME_ALIASES.get(supplied)
    if alias is not None:
        if expected_ordinal is not None and int(expected_ordinal) != alias.canonical_ordinal:
            raise UnknownReviewedValue(
                f"Reviewed alias {supplied!r} belongs to ordinal {alias.canonical_ordinal}, not {expected_ordinal}"
            )
        return alias.canonical_value, alias

    table = load_nadiamsa_table()
    canonical_ordinals = {name: ordinal for ordinal, name in table.names_by_ordinal.items()}
    ordinal = canonical_ordinals.get(supplied)
    if ordinal is None:
        raise UnknownReviewedValue(f"No reviewed Nadiamsa value mapping for: {supplied!r}")
    if expected_ordinal is not None and int(expected_ordinal) != ordinal:
        raise UnknownReviewedValue(
            f"Canonical Nadiamsa {supplied!r} belongs to ordinal {ordinal}, not {expected_ordinal}"
        )
    return supplied, None
