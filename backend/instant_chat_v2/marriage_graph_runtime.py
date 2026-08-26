"""Runtime resolution between Instant relationship routes and the compiled graph."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from .marriage_graph_policy import MarriageGraphPolicyStore, default_marriage_graph_policy_store


MARRIAGE_CATEGORIES = frozenset({"marriage", "spouse", "partner", "relationship", "love", "separation"})
TIMING_MODES = frozenset({"event_timing", "lifetime_event_timing", "month_timing", "timing_window", "event_prediction", "daily_forecast"})
MARRIAGE_SUBTYPES = frozenset({
    "general", "love_vs_arranged", "remarriage", "engagement_vs_wedding",
    "spouse_meeting", "spouse_details", "affair",
})

_MODE_COMPATIBILITY = {
    "marriage:ModePromise": {"potential_capacity"},
    "marriage:ModeOutlook": {"topic_reading"},
    "marriage:ModeTiming": set(TIMING_MODES),
    "marriage:ModeRetrospective": set(TIMING_MODES),
    "marriage:ModeProfile": {"relationship_person"},
    "marriage:ModeDiagnosis": {"problem_diagnosis"},
    "marriage:ModeRemedy": {"remedy_action"},
    "marriage:ModeChoice": {"comparison_choice"},
    "marriage:ModeRemarriage": set(TIMING_MODES) | {"potential_capacity"},
    "marriage:ModeMilestone": set(TIMING_MODES) | {"comparison_choice"},
    "marriage:ModeMeeting": {"topic_reading", "relationship_person"},
    "marriage:ModeDetailedProfile": {"relationship_person", "topic_reading"},
    "marriage:ModeAffair": {"problem_diagnosis", "topic_reading", "event_prediction"},
    "marriage:ModeMuhurat": {"dedicated_muhurat_flow"},
    "marriage:ModeCompatibility": {"dedicated_partnership_flow"},
}

_FACTOR_LABELS = {
    "marriage:D1": "D1 natal partnership foundation",
    "marriage:D9": "D9 marriage confirmation",
    "marriage:H2": "House 2 · family continuity",
    "marriage:H5": "House 5 · romance and affection",
    "marriage:H7": "House 7 · committed partnership",
    "marriage:H8": "House 8 · intimacy and strain",
    "marriage:H11": "House 11 · fulfilment and continuity",
    "marriage:H12": "House 12 · distance and separation",
    "marriage:H3": "House 3 · initiative and meeting channels",
    "marriage:H4": "House 4 · home and settlement context",
    "marriage:H6": "House 6 · conflict and competing attachments",
    "marriage:H9": "House 9 · ceremony, distance and social framework",
    "marriage:H10": "House 10 · spouse profession and public role",
    "marriage:SeventhLord": "Seventh house and lord",
    "marriage:VenusJupiter": "Venus and Jupiter significators",
    "marriage:DarakarakaUpapada": "Darakaraka and Upapada",
    "marriage:Darakaraka": "Darakaraka spouse archetype",
    "marriage:SeventhLordNakshatra": "Seventh-lord rashi and nakshatra",
    "marriage:VenusRashiNakshatra": "Venus rashi and nakshatra",
    "marriage:KpSeventh": "KP seventh-cusp evidence",
    "marriage:DerivedSpouseFrame": "Derived spouse frame",
    "marriage:DashaActivation": "Dasha permission",
    "marriage:TransitConfirmation": "Transit delivery",
    "marriage:RelationshipContext": "Resolved relationship context",
    "marriage:SecondChart": "Second resolved chart",
    "marriage:PriorMarriageContext": "Verified prior-marriage context",
    "marriage:MuhuratInputs": "Marriage Muhurat event, range and location",
    "marriage:RemedyBlueprint": "Calculated marriage remedy blueprint",
}


def normalize_marriage_category(value: Any) -> str | None:
    key = str(value or "").strip().lower()
    aliases = {"wife": "spouse", "husband": "spouse", "relationships": "relationship", "divorce": "separation", "reconciliation": "separation"}
    key = aliases.get(key, key)
    return key if key in MARRIAGE_CATEGORIES else None


def is_marriage_category(value: Any) -> bool:
    return normalize_marriage_category(value) is not None


def is_marriage_graph_request(category: Any, query_plan: Mapping[str, Any] | None = None) -> bool:
    if is_marriage_category(category):
        return True
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    special = plan.get("special_flow") if isinstance(plan.get("special_flow"), Mapping) else {}
    subtype = str(plan.get("marriage_subtype") or "").strip().lower()
    target = plan.get("target_subject") if isinstance(plan.get("target_subject"), Mapping) else {}
    if subtype == "spouse_details" or (
        str(special.get("spouse_detail_scope") or "").strip().lower() in {"appearance", "location"}
        and str(target.get("key") or "").strip().lower() in {"spouse", "wife", "husband", "partner"}
    ):
        return True
    return bool(
        str(plan.get("answer_mode") or "").strip().lower() == "dedicated_muhurat_flow"
        and str(special.get("muhurat_event_type") or "").strip().lower() == "marriage"
    )


def spouse_detail_scope(query_plan: Mapping[str, Any] | None) -> str | None:
    """Resolve the semantic spouse-detail facet, with a narrow outage fallback."""
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    special = plan.get("special_flow") if isinstance(plan.get("special_flow"), Mapping) else {}
    explicit = str(special.get("spouse_detail_scope") or "").strip().lower()
    if explicit in {"profession", "location", "appearance", "combined"}:
        return explicit
    requested = str(special.get("requested_fact") or "").strip().lower()
    question = str(plan.get("question") or "").strip().lower()
    text = f"{requested} {question}"
    if any(marker in text for marker in (
        "appearance", "physical", "look like", "looks like", "how will they look",
        "height", "build", "complexion", "face", "facial", "body type",
    )):
        return "appearance"
    if any(marker in text for marker in ("profession", "career", "occupation", "job", "work")):
        return "profession"
    if any(marker in text for marker in ("location", "where from", "settle", "country", "city", "place")):
        return "location"
    return None


def marriage_graph_runtime_key(category: Any, query_plan: Mapping[str, Any] | None = None) -> str | None:
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    mode = str(plan.get("answer_mode") or "").strip().lower()
    special = plan.get("special_flow") if isinstance(plan.get("special_flow"), Mapping) else {}
    if mode == "dedicated_muhurat_flow" and str(special.get("muhurat_event_type") or "").strip().lower() == "marriage":
        return "marriage_muhurat"
    category_key = normalize_marriage_category(category)
    target = plan.get("target_subject") if isinstance(plan.get("target_subject"), Mapping) else {}
    if category_key is None and (
        str(plan.get("marriage_subtype") or "").strip().lower() == "spouse_details"
        or (
            spouse_detail_scope(plan) in {"appearance", "location"}
            and str(target.get("key") or "").strip().lower() in {"spouse", "wife", "husband", "partner"}
        )
    ):
        category_key = "spouse"
    if category_key is None:
        return None
    subtype = str(plan.get("marriage_subtype") or "general").strip().lower().replace("-", "_").replace(" ", "_")
    subtype = subtype if subtype in MARRIAGE_SUBTYPES else "general"
    if mode == "remedy_action":
        return "marriage_remedies"
    if mode == "dedicated_partnership_flow":
        return "compatibility_analysis"
    if spouse_detail_scope(plan) == "appearance" and mode in {"relationship_person", "topic_reading"}:
        return "spouse_appearance"
    if spouse_detail_scope(plan) == "location" and mode in {"relationship_person", "topic_reading"}:
        return "spouse_location"
    subtype_routes = {
        "love_vs_arranged": "love_arranged_marriage",
        "remarriage": "remarriage",
        "engagement_vs_wedding": "engagement_wedding_timing",
        "spouse_meeting": "spouse_meeting",
        "spouse_details": "spouse_details",
        "affair": "affair_assessment",
    }
    if subtype in subtype_routes:
        return subtype_routes[subtype]
    if mode == "relationship_person":
        return "spouse_profile"
    if mode == "problem_diagnosis":
        return "relationship_diagnosis"
    if category_key == "separation":
        return "separation_reconciliation_timing" if mode in TIMING_MODES else "separation_reconciliation"
    if category_key in {"relationship", "love"}:
        return "relationship_timing" if mode in TIMING_MODES else "relationship_outlook"
    requested_evidence = {
        str(value or "").strip().lower()
        for value in (plan.get("requested_evidence") or [])
    }
    if bool((plan.get("time_scope") or {}).get("retrospective")) or any(
        value.startswith("historical_") for value in requested_evidence
    ):
        return "marriage_history"
    if mode == "potential_capacity":
        return "marriage_promise"
    if mode in {"event_prediction", "event_timing", "lifetime_event_timing", "month_timing"}:
        return "marriage_timing"
    if mode in {"timing_window", "daily_forecast"}:
        return "married_life_timing"
    return "married_life"


def resolve_marriage_graph_inputs(*, intent: Mapping[str, Any] | None, context: Mapping[str, Any] | None, query_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    query_plan = query_plan if isinstance(query_plan, Mapping) else {}
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    category = query_plan.get("category") or summary.get("category") or intent.get("category")
    special = query_plan.get("special_flow") if isinstance(query_plan.get("special_flow"), Mapping) else {}
    if str(query_plan.get("answer_mode") or "").strip().lower() == "dedicated_muhurat_flow" and str(special.get("muhurat_event_type") or "").strip().lower() == "marriage":
        category = "marriage"
    return {
        "category": category,
        "query_plan": query_plan,
        "observed_answer_mode": query_plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode"),
    }


def _present(value: Any) -> bool:
    return value not in (None, "", [], (), {})


def observed_marriage_factors(context: Mapping[str, Any], *, runtime_key: str) -> set[str]:
    factors: set[str] = set()
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    if normalized:
        factors.update({"marriage:D1", "marriage:D9", "marriage:H7", "marriage:SeventhLord", "marriage:VenusJupiter"})
    route_houses = {
        "marriage_timing": (2, 7, 11), "marriage_history": (2, 7, 11), "married_life": (2, 7, 8, 11, 12),
        "married_life_timing": (2, 7, 8, 11, 12), "relationship_outlook": (5, 7, 11),
        "relationship_timing": (5, 7, 11), "separation_reconciliation": (2, 7, 8, 11, 12),
        "separation_reconciliation_timing": (2, 7, 8, 11, 12), "relationship_diagnosis": (5, 7, 8, 12),
        "love_arranged_marriage": (2, 5, 7, 9, 11), "remarriage": (2, 7, 8, 9, 11, 12),
        "engagement_wedding_timing": (2, 5, 7, 9, 11), "spouse_meeting": (3, 7, 9, 11, 12),
        "spouse_details": (4, 7, 9, 10, 12), "spouse_appearance": (7,),
        "spouse_location": (3, 4, 7, 9, 12),
        "affair_assessment": (5, 6, 7, 8, 12),
    }
    if normalized:
        if runtime_key == "spouse_meeting":
            meeting = normalized.get("spouse_meeting_context") if isinstance(normalized.get("spouse_meeting_context"), Mapping) else {}
            factors.update(
                f"marriage:H{int(house)}"
                for house in meeting.get("required_channel_houses_present") or []
                if str(house).isdigit() and 1 <= int(house) <= 12
            )
        else:
            factors.update(f"marriage:H{house}" for house in route_houses.get(runtime_key, ()))
    if runtime_key in {"married_life", "married_life_timing", "separation_reconciliation", "separation_reconciliation_timing", "relationship_diagnosis", "affair_assessment"}:
        summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
        if _present(summary.get("target_subject")) or normalize_marriage_category(summary.get("category")):
            factors.add("marriage:RelationshipContext")
    if runtime_key == "spouse_profile":
        temperament = normalized.get("spouse_temperament_context") if isinstance(normalized.get("spouse_temperament_context"), Mapping) else {}
        layers = temperament.get("layers") if isinstance(temperament.get("layers"), Mapping) else {}
        if _present(layers.get("seventh_house")):
            factors.update({"marriage:DerivedSpouseFrame", "marriage:H7", "marriage:SeventhLord"})
        if _present(layers.get("seventh_lord_rashi_nakshatra")):
            factors.add("marriage:SeventhLordNakshatra")
        if _present(layers.get("darakaraka_rashi_nakshatra")):
            factors.add("marriage:Darakaraka")
        if _present(layers.get("venus_rashi_nakshatra")):
            factors.add("marriage:VenusRashiNakshatra")
    if runtime_key == "spouse_appearance":
        appearance = normalized.get("spouse_appearance_context") if isinstance(normalized.get("spouse_appearance_context"), Mapping) else {}
        layers = appearance.get("layers") if isinstance(appearance.get("layers"), Mapping) else {}
        if _present(layers.get("seventh_house_sign")):
            factors.update({"marriage:DerivedSpouseFrame", "marriage:H7", "marriage:SeventhLord"})
        if _present(layers.get("seventh_lord_rashi_nakshatra")):
            factors.add("marriage:SeventhLordNakshatra")
        if _present(layers.get("darakaraka_rashi_nakshatra")):
            factors.add("marriage:Darakaraka")
        if _present(layers.get("venus_rashi_nakshatra")):
            factors.add("marriage:VenusRashiNakshatra")
    if runtime_key == "spouse_location":
        location = normalized.get("spouse_location_context") if isinstance(normalized.get("spouse_location_context"), Mapping) else {}
        layers = location.get("layers") if isinstance(location.get("layers"), Mapping) else {}
        if _present(layers.get("seventh_house")):
            factors.update({"marriage:DerivedSpouseFrame", "marriage:H7", "marriage:SeventhLord"})
        if _present(layers.get("seventh_lord_location")):
            factors.add("marriage:SeventhLordNakshatra")
        if _present(layers.get("darakaraka_location")):
            factors.add("marriage:Darakaraka")
    if runtime_key == "spouse_meeting" and _present(normalized.get("spouse_meeting_context")):
        factors.add("marriage:DerivedSpouseFrame")
    if runtime_key == "spouse_details" and _present(normalized.get("person_profile_axes")):
        factors.add("marriage:DerivedSpouseFrame")
    if runtime_key == "remarriage":
        summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
        if _present(summary.get("prior_marriage_context")) or _present((context.get("query_plan") or {}).get("prior_marriage_context")):
            factors.add("marriage:PriorMarriageContext")
    if runtime_key == "marriage_remedies" and _present(normalized.get("remedy_blueprint")):
        factors.add("marriage:RemedyBlueprint")
    if runtime_key == "marriage_muhurat":
        plan = context.get("query_plan") if isinstance(context.get("query_plan"), Mapping) else {}
        special = plan.get("special_flow") if isinstance(plan.get("special_flow"), Mapping) else {}
        if all(_present(special.get(key)) for key in ("muhurat_event_type", "muhurat_start_date", "muhurat_end_date")) and (
            _present(special.get("muhurat_location_query")) or special.get("muhurat_use_birth_location") is True
        ):
            factors.add("marriage:MuhuratInputs")
    serialized = json.dumps(normalized, default=str).lower()
    if "kp" in serialized or _present(normalized.get("kp_evidence")):
        factors.add("marriage:KpSeventh")
    if "darakaraka" in serialized or "upapada" in serialized:
        factors.add("marriage:DarakarakaUpapada")
    if runtime_key != "marriage_remedies" and (
        _present(normalized.get("forward_event_dasha_scan"))
        or _present(normalized.get("historical_event_dasha_scan"))
        or _present(normalized.get("current_timing"))
    ):
        factors.add("marriage:DashaActivation")
    transit = normalized.get("transit_activation_timeline")
    if runtime_key != "marriage_remedies" and _present(transit):
        factors.add("marriage:TransitConfirmation")
    historical = normalized.get("historical_event_dasha_scan") if isinstance(normalized.get("historical_event_dasha_scan"), Mapping) else {}
    if any((row.get("transit_trigger_windows") or row.get("peak_activation_windows")) for row in historical.get("periods") or [] if isinstance(row, Mapping)):
        factors.add("marriage:TransitConfirmation")
    charts = context.get("resolved_charts") or context.get("selected_charts")
    if isinstance(charts, (list, tuple)) and len(charts) >= 2:
        factors.add("marriage:SecondChart")
    return factors


def compare_marriage_graph_policy(*, category: Any, query_plan: Mapping[str, Any] | None, observed_answer_mode: Any, context: Mapping[str, Any], store: MarriageGraphPolicyStore | None = None) -> dict[str, Any] | None:
    if not is_marriage_category(category):
        return None
    runtime_key = marriage_graph_runtime_key(category, query_plan)
    policy_store = store or default_marriage_graph_policy_store()
    policy = policy_store.resolve(str(runtime_key or ""))
    if policy is None:
        return {"ontology_version": policy_store.ontology_version, "runtime_key": runtime_key, "match": False, "mismatches": [{"kind": "missing_compiled_policy", "runtime_key": runtime_key}]}
    factor_context = dict(context)
    factor_context["query_plan"] = dict(query_plan or {})
    actual = observed_marriage_factors(factor_context, runtime_key=str(runtime_key))
    required = set(policy.required_factors)
    excluded = set(policy.default_exclusions)
    observed_mode = str(observed_answer_mode or "")
    mode_match = observed_mode in _MODE_COMPATIBILITY.get(policy.answer_mode, set())
    missing = sorted(required - actual)
    unexpected = sorted(excluded & actual)
    mismatches: list[dict[str, Any]] = []
    if not mode_match:
        mismatches.append({"kind": "answer_mode", "expected": policy.answer_mode, "observed": observed_mode})
    if missing:
        mismatches.append({"kind": "missing_required_factors", "factors": missing})
    if unexpected:
        mismatches.append({"kind": "unexpected_default_exclusions", "factors": unexpected})
    return {
        "ontology_version": policy_store.ontology_version, "runtime_key": runtime_key,
        "ontology_resource": policy.ontology_resource, "question_label": policy.question_label,
        "graph_tree": policy.graph_tree, "expected_answer_mode": policy.answer_mode,
        "observed_answer_mode": observed_mode, "mode_match": mode_match,
        "required_factors": sorted(required), "observed_factors": sorted(actual),
        "default_exclusions": sorted(excluded),
        "missing_required_factors": missing, "unexpected_default_exclusions": unexpected,
        "required_capabilities": sorted(policy.required_capabilities), "decision_rules": sorted(policy.decision_rules),
        "guardrails": sorted(policy.guardrails), "answer_contract": policy.answer_contract,
        "evidence_policy": policy.evidence_policy, "match": not mismatches, "mismatches": mismatches,
    }


def _resource_label(value: Any) -> str:
    text = str(value or "").split(":")[-1]
    return " ".join(re.sub(r"(?<!^)(?=[A-Z])", " ", text).split()).capitalize() or "Unknown graph node"


def build_marriage_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(comparison, Mapping):
        return None
    required = [str(value) for value in comparison.get("required_factors", ())]
    observed = {str(value) for value in comparison.get("observed_factors", ())}
    return {
        "status": "matched" if comparison.get("match") else "review_needed",
        "ontology_version": comparison.get("ontology_version"), "runtime_key": comparison.get("runtime_key"),
        "question_type": comparison.get("question_label") or _resource_label(comparison.get("runtime_key")),
        "graph_tree": comparison.get("graph_tree"),
        "expected_approach": _resource_label(comparison.get("expected_answer_mode")),
        "selected_approach": _resource_label(comparison.get("observed_answer_mode")),
        "mode_match": bool(comparison.get("mode_match")),
        "required_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor)), "selected": factor in observed} for factor in required],
        "additional_selected_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))} for factor in sorted(observed - set(required))],
        "missing_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))} for factor in required if factor not in observed],
        "decision_rules": [{"id": str(value), "label": _resource_label(value)} for value in comparison.get("decision_rules", ())],
        "guardrails": [{"id": str(value), "label": _resource_label(value)} for value in comparison.get("guardrails", ())],
        "required_capabilities": [{"id": str(value), "label": _resource_label(value)} for value in comparison.get("required_capabilities", ())],
        "answer_contract": _resource_label(comparison.get("answer_contract")), "evidence_policy": _resource_label(comparison.get("evidence_policy")),
    }
