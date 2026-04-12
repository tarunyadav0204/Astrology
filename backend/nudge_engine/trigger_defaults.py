"""
Built-in defaults for admin-configurable nudge triggers (layer A: copy, layer B: config).

Each trigger_key registered here can be loaded from DB with merge; unknown keys are rejected
at the admin API until registered.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple


@dataclass(frozen=True)
class TriggerDefaultSpec:
    """Static metadata and factory defaults for one trigger."""

    trigger_key: str
    title_template: str
    body_template: str
    question_template: str
    default_config: Dict[str, Any]
    allowed_placeholders: FrozenSet[str]
    default_priority: int = 75
    # Human-readable config keys for admin UI / validation
    config_schema: Dict[str, str] = field(default_factory=dict)


# Placeholders shared by natal return triggers
_NATAL_DATE_PLACEHOLDERS = frozenset(
    {
        "planet",
        "date_range",
        "window_start",
        "window_end",
    }
)

DEFAULT_SPECS: Tuple[TriggerDefaultSpec, ...] = (
    TriggerDefaultSpec(
        trigger_key="natal_planet_return",
        title_template="{planet} returns to your natal {planet}",
        body_template=(
            "Only {date_range}: transiting {planet} meets where it sat in your birth chart. "
            "A short personal window—easy to miss. Open chat and ask what to watch for before it passes."
        ),
        question_template=(
            "What should I focus on while transiting {planet} is conjunct my natal "
            "{planet} from {window_start} to {window_end}, and what shifts "
            "after that window closes?"
        ),
        default_config={
            "orb_deg": 1.0,
            "advance_notice_days": 30,
            "horizon_days": 800,
            "planets": [
                "Sun",
                "Moon",
                "Mercury",
                "Venus",
                "Mars",
                "Jupiter",
                "Saturn",
            ],
        },
        allowed_placeholders=_NATAL_DATE_PLACEHOLDERS,
        config_schema={
            "orb_deg": "float, conjunction orb in degrees (0.25–5)",
            "advance_notice_days": "int, notify when window starts within this many days (1–90)",
            "horizon_days": "int, ephemeris lookahead in days (30–2500)",
            "planets": "list[str], subset of Sun Moon Mercury Venus Mars Jupiter Saturn",
        },
    ),
    TriggerDefaultSpec(
        trigger_key="natal_whole_sign_return",
        title_template="{planet} returns to {sign}",
        body_template=(
            "{date_range}: transiting {planet} moves back through {sign}—the whole-sign house "
            "it occupied in your birth chart. You only get this pass for a while; ask in chat what "
            "this stretch tends to unlock for you before it moves on."
        ),
        question_template=(
            "What themes should I watch while transiting {planet} is in {sign} "
            "(my natal sign for {planet}) from {window_start} to {window_end}, "
            "and how is that different from the exact conjunction to my natal degree?"
        ),
        default_config={
            "advance_notice_days": 30,
            "horizon_days": 800,
            "planets": [
                "Sun",
                "Moon",
                "Mercury",
                "Venus",
                "Mars",
                "Jupiter",
                "Saturn",
            ],
        },
        allowed_placeholders=frozenset(
            _NATAL_DATE_PLACEHOLDERS | {"sign"},
        ),
        config_schema={
            "advance_notice_days": "int, notify when window starts within this many days (1–90)",
            "horizon_days": "int, ephemeris lookahead in days (30–2500)",
            "planets": "list[str], subset of Sun Moon Mercury Venus Mars Jupiter Saturn",
        },
    ),
    TriggerDefaultSpec(
        trigger_key="vimshottari_dasha_change",
        title_template="{level_label}: {to_planet} period begins {change_date_display}",
        body_template=(
            "Your chart moves from {from_planet} to {to_planet} at the {level_short} level on "
            "{change_date_display}. This is personal to your Vimshottari timeline—worth a focused "
            "check-in before it lands. Ask in chat what to emphasize as this phase opens."
        ),
        question_template=(
            "How does the shift from {from_planet} to {to_planet} ({level_label}) on {change_start} "
            "affect me, and what should I prioritize in the first weeks of this new period?"
        ),
        default_config={
            "md_lead_days": 90,
            "ad_lead_days": 30,
            "pd_lead_days": 2,
        },
        allowed_placeholders=frozenset(
            {
                "level_label",
                "level_short",
                "from_planet",
                "to_planet",
                "change_start",
                "change_date_display",
            }
        ),
        default_priority=72,
        config_schema={
            "md_lead_days": "int, notify when Mahadasha change is within this many days (1–120); default 90 (~3 months)",
            "ad_lead_days": "int, Antardasha (1–90); default 30 (~1 month)",
            "pd_lead_days": "int, Pratyantardasha (1–14); default 2 days",
        },
    ),
)

DEFAULTS_BY_KEY: Dict[str, TriggerDefaultSpec] = {s.trigger_key: s for s in DEFAULT_SPECS}

ALLOWED_PLANET_NAMES = frozenset(
    {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
)


def get_spec(trigger_key: str) -> Optional[TriggerDefaultSpec]:
    return DEFAULTS_BY_KEY.get(trigger_key)


def list_registered_trigger_keys() -> List[str]:
    return sorted(DEFAULTS_BY_KEY.keys())
