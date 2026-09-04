"""Shared Avayogi interpretation rules for every chat calculation path."""

from __future__ import annotations

from typing import Any, Iterable


AVAYOGI_REVERSAL_HOUSES = frozenset({3, 6, 8, 12})

AVAYOGI_CHAT_DOCTRINE = """
[AVAYOGI-EFFECT-POLICY]
- Judge the Avayogi contribution separately from dignity, combustion, Gandanta, Dagdha, functional lordship and other independent conditions.
- If the Avayogi planet is also the Tithi Shunya lord/Adhipati, its ordinary Avayogi obstruction is cancelled. Do not call that Avayogi contribution negative or mixed; treat it as neutral unless a reversal rule below makes it supportive.
- If the Avayogi planet is placed in House 3, 6, 8 or 12, its Avayogi contribution reverses and is supportive rather than obstructive.
- If the Avayogi planet aspects House 3, 6, 8 or 12, its Avayogi contribution to that aspected house is supportive rather than obstructive.
- These rules modify only the Avayogi contribution. Do not erase a separate Dagdha, Gandanta, debilitation, combustion or other independently calculated condition.
""".strip()


def normalize_house(value: Any) -> int | None:
    try:
        house = int(value)
    except (TypeError, ValueError):
        return None
    return ((house - 1) % 12) + 1


def avayogi_effect(
    *,
    placement_house: Any,
    tithi_shunya_overlap: bool = False,
    target_house: Any = None,
    relation: str | Iterable[str] | None = None,
) -> dict[str, Any]:
    """Resolve only the Avayogi contribution under the declared precedence."""
    placement = normalize_house(placement_house)
    target = normalize_house(target_house)
    relations = (
        {str(item).strip().lower() for item in relation}
        if isinstance(relation, (list, tuple, set, frozenset))
        else {str(relation or "").strip().lower()}
    )
    placed_in_reversal_house = placement in AVAYOGI_REVERSAL_HOUSES
    aspects_reversal_house = "aspector" in relations and target in AVAYOGI_REVERSAL_HOUSES

    if placed_in_reversal_house:
        polarity, rule = "supportive", "avayogi_placement_reversal"
    elif aspects_reversal_house:
        polarity, rule = "supportive", "avayogi_aspect_reversal"
    elif tithi_shunya_overlap:
        polarity, rule = "neutral", "avayogi_tithi_shunya_cancellation"
    else:
        polarity, rule = "challenging", "ordinary_avayogi_obstruction"

    return {
        "polarity": polarity,
        "rule": rule,
        "placement_house": placement,
        "target_house": target,
        "relation": tuple(sorted(value for value in relations if value)),
        "tithi_shunya_overlap": bool(tithi_shunya_overlap),
        "placed_in_reversal_house": placed_in_reversal_house,
        "aspects_reversal_house": aspects_reversal_house,
        "reversal_houses": tuple(sorted(AVAYOGI_REVERSAL_HOUSES)),
    }
