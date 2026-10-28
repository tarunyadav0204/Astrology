"""Curated interpretive layers used only by Nakshatra Blueprint.

This is deliberately not a collection of generic Sun-sign adjectives.  The
classical identifiers (deity, ruler and symbol) are retained alongside a
carefully bounded modern interpretive layer so the writer can connect a star's
mythic action to a graha, its house, and recurring patterns in one chart.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from vedic_predictions.config.nakshatra_data import NAKSHATRA_DATA


# Each entry is an editorially reviewed *interpretive direction*, not a claim
# that every native will exhibit every trait.  It is intentionally compact: the
# chart supplies the specificity, while this library supplies the star's depth.
_LAYERS = {
    "Ashwini": ("swift restoration and first movement", "initiate, repair, open a route", "impatience or leaving before integration", "beginnings, healing, transport, decisive intervention"),
    "Bharani": ("the capacity to contain, bear and transform", "hold consequence with creative strength", "pressure, control or carrying too much alone", "desire, stewardship, endings and ethical responsibility"),
    "Krittika": ("discerning fire that separates what nourishes from what does not", "clarify, refine and protect standards", "cutting speech, dissatisfaction or over-correction", "craft, leadership, nourishment and principled choices"),
    "Rohini": ("cultivation, embodiment and the desire to make life flourish", "grow, beautify and sustain", "attachment to comfort, attention or possession", "resources, sensuality, fertility, art and continuity"),
    "Mrigashira": ("the searching mind following a subtle trail", "inquire, experiment and notice what others miss", "restlessness, scattered desire or perpetual seeking", "research, learning, travel, courtship and curiosity"),
    "Ardra": ("the storm that exposes what must be grieved and understood", "name complexity and rebuild honestly", "overwhelm, harshness or identifying with rupture", "research, weathering change, truth-telling and renewal"),
    "Punarvasu": ("return, replenishment and a wider shelter", "restore faith and make a second beginning", "repeating a cycle without changing its cause", "homecoming, teaching, generosity and recovery"),
    "Pushya": ("nourishment through disciplined guardianship", "protect, mentor and steadily develop", "duty becoming emotional dependency or rigidity", "care, education, institutions, food and spiritual practice"),
    "Ashlesha": ("subtle perception, binding intelligence and hidden currents", "read motives and work with complexity", "entanglement, suspicion or indirect control", "psychology, strategy, healing, secrecy and emotional bonds"),
    "Magha": ("lineage, inherited authority and rightful seat", "honour ancestry while carrying responsibility with dignity", "status anxiety, entitlement or performing an inherited role", "legacy, ceremony, leadership, family memory and stewardship"),
    "Purva Phalguni": ("creative release, enjoyment and the renewal of affection", "create pleasure, intimacy and generosity", "excess, avoidance or needing constant affirmation", "art, romance, hospitality, recreation and charisma"),
    "Uttara Phalguni": ("enduring agreements and the ethics of mutual support", "organise, serve and make bonds reliable", "over-functioning or turning care into obligation", "contracts, mentoring, partnership and social duty"),
    "Hasta": ("skill held in the hand: shaping, arranging and making workable", "apply intelligence with dexterity and timing", "manipulation, anxiety or trying to control every outcome", "craft, communication, service, trade and practical healing"),
    "Chitra": ("design, luminosity and the urge to give form to an inner vision", "build, refine and make the invisible visible", "image-consciousness or dissatisfaction with the unfinished", "design, architecture, aesthetics, presentation and innovation"),
    "Swati": ("self-directed movement carried by wind", "adapt, trade and preserve inner independence", "drift, detachment or avoiding rooted commitment", "enterprise, negotiation, travel, language and autonomy"),
    "Vishakha": ("focused striving toward a chosen aim", "concentrate desire and sustain a path to fruition", "single-mindedness, comparison or inability to stop", "ambition, ritual effort, competition and achievement"),
    "Anuradha": ("devotion, friendship and the discipline of reciprocity", "build trust through loyalty and shared rhythm", "self-abandonment for loyalty or fear of exclusion", "alliances, devotion, travel, networks and emotional commitment"),
    "Jyeshtha": ("seniority, protection and the burden of discernment", "take mature responsibility and safeguard what matters", "hypervigilance, superiority or carrying power alone", "crisis management, research, guardianship and authority"),
    "Mula": ("the root beneath appearances and the courage to uproot", "investigate causes and clear what is no longer true", "needless destruction, nihilism or abrupt severing", "research, transformation, philosophy, recovery and radical honesty"),
    "Purva Ashadha": ("purification, conviction and the force of renewal", "advocate, inspire and cleanse a stagnant current", "dogmatism, pride or mistaking conviction for proof", "persuasion, art, advocacy, water and public ideals"),
    "Uttara Ashadha": ("principled victory and responsibility to the collective", "make values durable through sustained leadership", "moral rigidity or defining worth by achievement", "governance, ethics, long projects, institutions and legacy"),
    "Shravana": ("receptive learning, transmission and the art of listening", "hear deeply, connect knowledge and carry a teaching onward", "absorbing others' expectations or living through borrowed voices", "education, language, memory, mediation and attentive service"),
    "Dhanishtha": ("rhythm, resource circulation and coordinated contribution", "create momentum and share capability within a group", "status competition or giving to be recognised", "music, finance, teams, timing and public contribution"),
    "Shatabhisha": ("the veiled circle: inquiry, healing and truth beneath appearances", "research, diagnose and restore through clear observation", "isolation, contrarianism or concealing distress", "science, systems, medicine, reform, privacy and contemplative depth"),
    "Purva Bhadrapada": ("intense idealism at the threshold of transformation", "commit to a truth with courage and sacrifice", "extremes, severity or romanticising suffering", "philosophy, activism, austerity, depth and radical change"),
    "Uttara Bhadrapada": ("the deep foundation: patience, containment and inner steadiness", "hold complexity without haste and make compassion durable", "inertia, emotional heaviness or hidden resentment", "counselling, stewardship, contemplation, water and long-term care"),
    "Revati": ("safe passage, guidance and compassionate completion", "protect a transition and help people find their way", "rescuer patterns, porous boundaries or difficulty ending", "guidance, travel, music, care, closure and restoration"),
}

_ALIASES = {"Satabhisha": "Shatabhisha", "Shatabhisa": "Shatabhisha", "Purva Bhadra": "Purva Bhadrapada", "Uttara Bhadra": "Uttara Bhadrapada"}
_PADA_FOCUS = {
    1: "initiating and self-directed; it asks how this impulse begins",
    2: "grounding and value-building; it asks what can be made dependable",
    3: "relational and expressive; it asks how this pattern is communicated or exchanged",
    4: "inner and integrating; it asks how this pattern is emotionally absorbed and completed",
}

# These are editorial contracts for the reader-facing result. They make every
# life area useful without turning astrology into deterministic prediction.
LIFE_AREA_READER_QUESTIONS = {
    "identity": "State the kind of self-direction, leadership or personal choices that help this native become more fully themselves.",
    "mind": "State the emotional rhythm, mental hygiene and decision conditions that help this native stay clear rather than overwhelmed.",
    "family": "State the practical pattern around earning, saving, family obligations and speech that the native can consciously manage.",
    "home": "State what kind of home, family boundary and emotional environment supports the native.",
    "creativity": "State the creative mediums, learning style or approach to children and projects that best uses this pattern.",
    "work": "State the work rhythm, service style and sustainable routines that fit this native; do not give medical advice.",
    "partnership": "State the partnership qualities, agreements and relational habits that support a durable connection.",
    "transformation": "State the approach to intimacy, shared money, endings and research that helps the native act wisely.",
    "dharma": "State the learning path, mentor qualities, travel or worldview practices that give this native genuine meaning.",
    "career": "Name 3–5 plausible role families or work domains, the environment where they thrive, and the contribution they are equipped to make. Frame these as directions to explore, never guarantees.",
    "gains": "State the kind of communities, collaborators, audience-building and long-term gains strategy that fits this native.",
    "spirituality": "State a realistic restorative or contemplative practice, and how solitude, release or foreign links can be approached constructively.",
}


def _canonical(raw: Any) -> str:
    name = str(raw or "").strip()
    return _ALIASES.get(name, name)


def _record(name: Any, pada: Any = None) -> dict[str, Any]:
    canonical = _canonical(name)
    row = next((value for value in NAKSHATRA_DATA.values() if value["name"] == canonical), {})
    core, action, shadow, motifs = _LAYERS.get(canonical, ("a distinctive Nakshatra pattern", "express its central quality", "an unintegrated expression", "life direction"))
    try:
        pada_number = int(pada)
    except (TypeError, ValueError):
        pada_number = None
    return {
        "name": canonical, "deity": row.get("deity"), "nakshatra_lord": row.get("lord"),
        "symbol": row.get("symbol"), "yoni": row.get("animal"), "guna": row.get("guna"),
        "core_pattern": core, "mature_action": action, "shadow_expression": shadow,
        "life_motifs": motifs, "pada": pada_number,
        "pada_refinement": _PADA_FOCUS.get(pada_number) if pada_number else None,
    }


def build_nakshatra_blueprint_brief(facts: dict[str, Any]) -> dict[str, Any]:
    """Return only active-star dossiers and chart-level motifs for the writer."""
    rows = [row for row in (facts.get("planet_matrix") or []) if isinstance(row, dict) and row.get("nakshatra")]
    active: dict[str, dict[str, Any]] = {}
    placements: list[dict[str, Any]] = []
    by_star: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        dossier = _record(row.get("nakshatra"), row.get("pada"))
        name = dossier["name"]
        active.setdefault(name, _record(name))
        planet = str(row.get("planet") or "")
        by_star[name].append(planet)
        placements.append({
            "planet": planet, "house": row.get("house"), "sign": row.get("sign_name"),
            "dignity": row.get("dignity"), "aspects": row.get("aspects"), **dossier,
        })

    patterns = []
    for star, planets in by_star.items():
        if len(planets) >= 2:
            layer = active[star]
            patterns.append({"kind": "repeated_nakshatra", "star": star, "planets": planets, "meaning": layer["core_pattern"], "writing_direction": f"Show how {star}'s pattern repeats across {', '.join(planets)} rather than describing each occurrence in isolation."})
    asc = facts.get("ascendant") or {}
    moon = facts.get("moon") or {}
    if asc.get("nakshatra") and moon.get("nakshatra"):
        asc_star, moon_star = _canonical(asc.get("nakshatra")), _canonical(moon.get("nakshatra"))
        if asc_star != moon_star:
            patterns.append({"kind": "ascendant_moon_dialogue", "stars": [asc_star, moon_star], "meaning": f"Outer approach is shaped by {_record(asc_star)['core_pattern']}; emotional rhythm is shaped by {_record(moon_star)['core_pattern']}.", "writing_direction": "Use this contrast or alliance as a recurring personal tension, not as two separate labels."})
    for node in ("Rahu", "Ketu"):
        hit = next((placement for placement in placements if placement["planet"] == node), None)
        if hit:
            patterns.append({"kind": "nodal_axis", "planet": node, "star": hit["name"], "meaning": hit["core_pattern"], "writing_direction": "Use this as a developmental tension or unconventional pull only where relevant; do not turn it into fatalism."})

    return {"active_nakshatra_dossiers": list(active.values()), "enriched_placements": placements, "chart_patterns": patterns, "life_area_reader_questions": LIFE_AREA_READER_QUESTIONS}
