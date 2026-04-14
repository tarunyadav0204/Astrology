"""
Strip ChatContextBuilder output for event timeline (yearly + monthly deep) only.

Chart math runs unchanged in ChatContextBuilder; pruning happens on a deep copy
of the merged dict before json.dumps — chat caches and other callers are unaffected.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, FrozenSet

# Divisionals referenced in event_predictor prompts (varga audit + sniper + disambiguation).
_EVENT_TIMELINE_DIVISIONAL_KEYS: FrozenSet[str] = frozenset(
    {
        "d3_drekkana",
        "d4_chaturthamsa",
        "d7_saptamsa",
        "d9_navamsa",
        "d10_dasamsa",
        "d12_dwadasamsa",
        "d16_shodasamsa",
        "d24_chaturvimsamsa",
        "d30_trimsamsa",
        # Jaimini-derived charts if ever injected by intent filtering
        "karkamsa",
        "swamsa",
    }
)

# Top-level keys not used by event timeline prompts (chat / short-period only).
_EVENT_TIMELINE_DROP_KEYS: FrozenSet[str] = frozenset(
    {
        "kp_analysis",
        "friendship_analysis",
        "kalchakra_dasha",
        "shoola_dasha",
        "yogini_dasha",
        "kota_chakra",
        "dasha_conflicts",
        "transit_data_availability",
        "birth_panchang",
        "pushkara_navamsa",
        "nakshatra_remedies",
        "nadi_links",
        "jaimini_full_analysis",
        "relationships",
        "advanced_analysis",
        "special_lagnas",
        "special_points",
        "prediction_matrix",
        "transit_optimization",
        "comprehensive_transit_analysis",
        "transit_activations",
        "unified_dasha_timeline",
        "requested_dasha_summary",
        "period_dasha_activations",
        "selected_period_focus",
        "bhavat_bhavam",
        # Large overlap with divisional D9 + D1 planetary_analysis
        "d9_planetary_analysis",
    }
)


def prune_for_event_timeline(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deep copy of context with event-timeline-only reductions applied."""
    out = copy.deepcopy(context)

    for key in _EVENT_TIMELINE_DROP_KEYS:
        out.pop(key, None)

    divs = out.get("divisional_charts")
    if isinstance(divs, dict):
        out["divisional_charts"] = {
            k: v for k, v in divs.items() if k in _EVENT_TIMELINE_DIVISIONAL_KEYS
        }

    av = out.get("ashtakavarga")
    if isinstance(av, dict) and isinstance(av.get("d9_navamsa"), dict):
        av = copy.deepcopy(av)
        av.pop("d9_navamsa", None)
        out["ashtakavarga"] = av

    cd = out.get("current_dashas")
    if isinstance(cd, dict) and "maraka_analysis" in cd:
        cd = copy.deepcopy(cd)
        cd.pop("maraka_analysis", None)
        out["current_dashas"] = cd

    return out
