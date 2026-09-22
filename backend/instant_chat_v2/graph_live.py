"""Live knowledge-graph policy enforcement for supported Instant domains.

The domain adapters still calculate parity details, but this module promotes
the resolved policy into the authoritative packet before answer generation.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Callable, Mapping

from .career import is_career_category
from .career_graph_runtime import (
    build_career_graph_route,
    compare_career_graph_policy,
    resolve_career_graph_inputs,
)
from .health_graph_runtime import (
    build_health_graph_route,
    compare_health_graph_policy,
    is_health_category,
    resolve_health_graph_inputs,
)
from .marriage_graph_runtime import (
    build_marriage_graph_route,
    compare_marriage_graph_policy,
    is_marriage_graph_request,
    resolve_marriage_graph_inputs,
)
from .wealth_graph_runtime import (
    build_wealth_graph_route,
    compare_wealth_graph_policy,
    is_wealth_category,
    resolve_wealth_graph_inputs,
)
from .education_graph_runtime import (
    build_education_graph_route,
    compare_education_graph_policy,
    is_education_category,
    resolve_education_graph_inputs,
)
from .children_graph_runtime import (
    build_children_graph_route,
    compare_children_graph_policy,
    is_children_category,
    resolve_children_graph_inputs,
)
from .home_graph_runtime import (
    build_home_graph_route, compare_home_graph_policy, is_home_category,
    resolve_home_graph_inputs,
)
from .foreign_graph_runtime import (
    build_foreign_graph_route, compare_foreign_graph_policy,
    is_foreign_category, resolve_foreign_graph_inputs,
)
from .nakshatra_graph_runtime import (
    build_nakshatra_graph_route, compare_nakshatra_graph_policy,
    resolve_nakshatra_graph_inputs,
)
from .nakshatra import is_nakshatra_category


LOGGER = logging.getLogger(__name__)


def required_divisional_codes_for_live_route(
    *,
    intent: Mapping[str, Any] | None,
    answer_mode: str,
) -> list[str]:
    """Return the compiled route's required vargas before evidence is built.

    Live previously selected the graph only *after* context construction. That
    allowed the router's optional ``divisional_charts`` list to omit a varga
    which the selected ontology route declares mandatory, producing a false
    missing-evidence refusal after all other calculations had succeeded. This
    lightweight preflight uses structured route fields only; it never parses
    question text and never marks a chart available before it is calculated.
    """
    routed = dict(intent or {})
    query_plan = {
        key: routed.get(key)
        for key in (
            "category", "career_subtype", "marriage_subtype", "wealth_subtype",
            "education_subtype", "children_subtype", "home_subtype", "foreign_subtype",
            "nakshatra_subtype",
            "comparison_options", "route_action",
        )
        if routed.get(key) not in (None, "", [], {})
    }
    query_plan["answer_mode"] = str(answer_mode or routed.get("answer_mode") or "topic_reading")
    policy = resolve_live_graph_policy(intent=routed, context={}, query_plan=query_plan)
    if not isinstance(policy, Mapping) or not policy.get("runtime_key"):
        return []
    codes: list[str] = []
    for factor in policy.get("required_factors") or []:
        match = re.fullmatch(
            r"[^:]+:(D\d{1,2}|Kara?kamsha|Swamsa)",
            str(factor or ""),
            re.IGNORECASE,
        )
        if match:
            raw_code = match.group(1).upper()
            code = (
                "KARAKAMSHA"
                if raw_code in {"KARAKAMSHA", "KARKAMSHA"}
                else "SWAMSA"
                if raw_code == "SWAMSA"
                else raw_code
            )
            if code not in codes:
                codes.append(code)
    return sorted(
        codes,
        key=lambda code: (0, int(code[1:])) if re.fullmatch(r"D\d{1,2}", code) else (1, code),
    )


def _deeper_mode_fallback(language: str) -> str:
    """Localized fail-closed copy for an incomplete Live evidence contract."""
    key = str(language or "english").strip().lower().replace("_", "-")
    key = key.split("-", 1)[0]
    messages = {
        "en": "I can’t answer this reliably in Live mode with the depth this question needs. Please ask it in Standard or Premium mode so Tara can use the complete analysis.",
        "hi": "इस प्रश्न का विश्वसनीय उत्तर देने के लिए Live mode में पर्याप्त गहराई उपलब्ध नहीं है। कृपया इसे Standard या Premium mode में पूछें, ताकि Tara पूरा विश्लेषण इस्तेमाल कर सके।",
        "mr": "या प्रश्नाचे विश्वासार्ह उत्तर देण्यासाठी Live mode मध्ये पुरेशी सखोल माहिती उपलब्ध नाही. कृपया हा प्रश्न Standard किंवा Premium mode मध्ये विचारा, म्हणजे Tara संपूर्ण विश्लेषण वापरू शकेल.",
        "gu": "આ પ્રશ્નનો વિશ્વસનીય જવાબ આપવા માટે Live modeમાં પૂરતી ઊંડાણભરી માહિતી ઉપલબ્ધ નથી. કૃપા કરીને તેને Standard અથવા Premium modeમાં પૂછો, જેથી Tara સંપૂર્ણ વિશ્લેષણ વાપરી શકે.",
        "ta": "இந்தக் கேள்விக்கு நம்பகமாக பதிலளிக்க Live mode-ல் தேவையான ஆழமான தகவல் இல்லை. Tara முழுமையான ஆய்வைப் பயன்படுத்த Standard அல்லது Premium mode-ல் கேளுங்கள்.",
        "te": "ఈ ప్రశ్నకు నమ్మకంగా సమాధానం ఇవ్వడానికి Live modeలో అవసరమైన లోతైన సమాచారం లేదు. Tara పూర్తి విశ్లేషణను ఉపయోగించేందుకు Standard లేదా Premium modeలో అడగండి.",
        "bn": "এই প্রশ্নের নির্ভরযোগ্য উত্তর দেওয়ার জন্য Live mode-এ প্রয়োজনীয় গভীর তথ্য নেই। Tara-কে সম্পূর্ণ বিশ্লেষণ ব্যবহার করতে দিতে Standard বা Premium mode-এ প্রশ্নটি করুন।",
        "kn": "ಈ ಪ್ರಶ್ನೆಗೆ ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಉತ್ತರಿಸಲು Live modeನಲ್ಲಿ ಅಗತ್ಯವಾದ ಆಳವಾದ ಮಾಹಿತಿ ಇಲ್ಲ. Tara ಸಂಪೂರ್ಣ ವಿಶ್ಲೇಷಣೆಯನ್ನು ಬಳಸಲು Standard ಅಥವಾ Premium modeನಲ್ಲಿ ಕೇಳಿ.",
        "ml": "ഈ ചോദ്യത്തിന് വിശ്വസനീയമായി മറുപടി നൽകാൻ Live mode-ൽ ആവശ്യമായ ആഴത്തിലുള്ള വിവരങ്ങൾ ലഭ്യമല്ല. Tara പൂർണ്ണ വിശകലനം ഉപയോഗിക്കാൻ Standard അല്ലെങ്കിൽ Premium mode-ൽ ചോദിക്കുക.",
        "pa": "ਇਸ ਸਵਾਲ ਦਾ ਭਰੋਸੇਯੋਗ ਜਵਾਬ ਦੇਣ ਲਈ Live mode ਵਿੱਚ ਲੋੜੀਂਦੀ ਡੂੰਘਾਈ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। Tara ਨੂੰ ਪੂਰਾ ਵਿਸ਼ਲੇਸ਼ਣ ਵਰਤਣ ਲਈ ਇਹ ਸਵਾਲ Standard ਜਾਂ Premium mode ਵਿੱਚ ਪੁੱਛੋ।",
        "ur": "اس سوال کا قابلِ اعتماد جواب دینے کے لیے Live mode میں مطلوبہ گہرائی دستیاب نہیں ہے۔ براہِ کرم اسے Standard یا Premium mode میں پوچھیں تاکہ Tara مکمل تجزیہ استعمال کر سکے۔",
        "es": "No puedo responder esto de forma fiable en el modo Live con la profundidad que requiere. Pregúntalo en el modo Standard o Premium para que Tara pueda usar el análisis completo.",
        "fr": "Je ne peux pas répondre de façon fiable en mode Live avec la profondeur nécessaire. Posez cette question en mode Standard ou Premium afin que Tara puisse utiliser l’analyse complète.",
        "de": "Im Live-Modus kann ich diese Frage nicht mit der nötigen Tiefe zuverlässig beantworten. Bitte stelle sie im Standard- oder Premium-Modus, damit Tara die vollständige Analyse nutzen kann.",
        "ru": "В режиме Live недостаточно данных для надёжного и глубокого ответа. Задайте этот вопрос в режиме Standard или Premium, чтобы Tara могла использовать полный анализ.",
        "zh": "Live 模式目前没有足够的深度来可靠回答这个问题。请在 Standard 或 Premium 模式中提问，以便 Tara 使用完整分析。",
    }
    aliases = {
        "english": "en", "hindi": "hi", "marathi": "mr", "gujarati": "gu",
        "tamil": "ta", "telugu": "te", "bengali": "bn", "kannada": "kn",
        "malayalam": "ml", "punjabi": "pa", "urdu": "ur", "spanish": "es",
        "french": "fr", "german": "de", "russian": "ru", "chinese": "zh",
    }
    return messages.get(aliases.get(key, key), messages["en"])


def _output_sections(graph_tree: Any) -> list[dict[str, str]]:
    if not isinstance(graph_tree, Mapping):
        return []
    questions = graph_tree.get("children")
    if not isinstance(questions, list) or not questions:
        return []
    question = questions[0] if isinstance(questions[0], Mapping) else {}
    relations = question.get("children") if isinstance(question.get("children"), list) else []
    contract_relation = next(
        (row for row in relations if isinstance(row, Mapping) and row.get("label") == "Answer contract"),
        None,
    )
    contracts = contract_relation.get("children") if isinstance(contract_relation, Mapping) else []
    contract = contracts[0] if isinstance(contracts, list) and contracts and isinstance(contracts[0], Mapping) else {}
    branches = contract.get("children") if isinstance(contract.get("children"), list) else []
    sections_branch = next(
        (row for row in branches if isinstance(row, Mapping) and row.get("label") == "Output sections"),
        None,
    )
    sections = sections_branch.get("children") if isinstance(sections_branch, Mapping) else []
    return [
        {"id": str(row.get("id")), "label": str(row.get("label"))}
        for row in sections
        if isinstance(row, Mapping) and row.get("id") and row.get("label")
    ]


def _live_contract(domain: str, comparison: Mapping[str, Any], review: Mapping[str, Any]) -> dict[str, Any]:
    missing_required = list(comparison.get("missing_required_factors") or [])
    unexpected_exclusions = list(comparison.get("unexpected_default_exclusions") or [])
    mode_match = bool(comparison.get("mode_match"))
    # A comparator mismatch has two very different meanings. Missing required
    # factors are a genuine evidence gap. Unexpected exclusions mean the
    # shared calculation workspace contains an incidental branch (usually
    # current dasha/transit) which this route explicitly says not to use. The
    # composer boundary removes the latter structurally, so it must never send
    # a customer to a paid/deeper mode.
    # D1 and D10 are the primary Career Fit evidence. Amatyakaraka and
    # Karakamsha are confirmation layers: if a legacy/saved chart cannot
    # calculate one of them, Live must qualify the Jaimini portion rather than
    # discard the complete Parashari career reading and advertise a paid mode.
    partial_career_confirmation = bool(
        domain == "career"
        and str(comparison.get("runtime_key") or "") == "career_fit"
        and missing_required
        and set(missing_required).issubset({"career:Amatyakaraka", "career:Karakamsha"})
    )
    missing_evidence = bool(missing_required) and not partial_career_confirmation
    contract_contamination = bool(unexpected_exclusions)
    route_contract_error = not mode_match
    if partial_career_confirmation:
        evidence_status = "partial_confirmation"
    elif missing_evidence:
        evidence_status = "missing_required_evidence"
    elif route_contract_error:
        evidence_status = "route_contract_error"
    elif contract_contamination:
        # It is complete from the customer's perspective; the separate audit
        # flag records that the composer boundary had exclusions to remove.
        evidence_status = "complete"
    else:
        evidence_status = "complete"
    return {
        "live": True,
        "enforcement": "authoritative_pre_generation",
        "domain": domain,
        "ontology_version": comparison.get("ontology_version"),
        "runtime_key": comparison.get("runtime_key"),
        "ontology_resource": comparison.get("ontology_resource"),
        "question_type": comparison.get("question_label"),
        "expected_answer_mode": comparison.get("expected_answer_mode"),
        "period_outlook_override": bool(comparison.get("period_outlook_override")),
        "mode_match": mode_match,
        "evidence_status": evidence_status,
        "fallback_to_deeper_mode": missing_evidence,
        "fallback_reason": "missing_required_evidence" if missing_evidence else None,
        "partial_confirmation": partial_career_confirmation,
        "route_contract_error": route_contract_error,
        "excluded_evidence_sanitized": contract_contamination,
        "required_factors": list(comparison.get("required_factors") or []),
        "observed_factors": list(comparison.get("observed_factors") or []),
        "missing_required_factors": missing_required,
        "default_exclusions": list(comparison.get("default_exclusions") or []),
        "unexpected_default_exclusions": unexpected_exclusions,
        "required_capabilities": list(comparison.get("required_capabilities") or []),
        "decision_rules": list(comparison.get("decision_rules") or []),
        "guardrails": list(comparison.get("guardrails") or []),
        "answer_contract": comparison.get("answer_contract"),
        "evidence_policy": comparison.get("evidence_policy"),
        "required_output_sections": _output_sections(comparison.get("graph_tree")),
        "instruction": (
            "This compiled graph route is authoritative. Follow its decision rules, guardrails and output "
            "sections; never use default-excluded factors. Treat missing required factors as unavailable "
            "evidence and do not make a conclusion that depends on them. "
            + (
                "The route cannot support a reliable Live answer. In the same language and script as the user, "
                "briefly say that this needs a deeper Standard or Premium reading. Do not name another domain, "
                "invent a comparison, expose missing-factor names, or ask an unrelated follow-up."
                if missing_evidence else
                "Use the complete D1 and D10 career evidence to answer strengths, suitable work, work setting and "
                "earning viability. State briefly that the unavailable Jaimini layer could not confirm or refine "
                "the result; do not replace the supported answer with a deeper-mode refusal."
                if partial_career_confirmation else ""
            )
        ),
        "route": dict(review),
    }


def resolve_live_graph_policy(
    *,
    intent: Mapping[str, Any] | None,
    context: Mapping[str, Any] | None,
    query_plan: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Resolve exactly one supported domain policy from the final query plan."""
    context = context if isinstance(context, Mapping) else {}
    query_plan = query_plan if isinstance(query_plan, Mapping) else {}
    intent = intent if isinstance(intent, Mapping) else {}
    category = query_plan.get("category") or (context.get("intent_summary") or {}).get("category") or intent.get("category")

    resolver: Callable[..., dict[str, Any]]
    comparator: Callable[..., dict[str, Any] | None]
    reviewer: Callable[[Mapping[str, Any] | None], dict[str, Any] | None]
    domain: str
    wealth_subtype = str(
        query_plan.get("wealth_subtype")
        or (context.get("intent_summary") or {}).get("wealth_subtype")
        or intent.get("wealth_subtype")
        or ""
    ).strip().lower()
    prefer_wealth_graph = wealth_subtype in {
        "source", "savings_instability", "multiple_income", "debt_repayment",
        "loan_support", "loan_decision", "investing_vs_trading", "investment_risk",
        "loss_vulnerability", "windfall", "intraday_trading",
    }
    # ``income`` is shared vocabulary with the Career salary route. A typed
    # Wealth subtype is the more specific domain signal and must win before
    # the broad Career alias check.
    if prefer_wealth_graph and is_wealth_category(category):
        domain, resolver, comparator, reviewer = (
            "wealth", resolve_wealth_graph_inputs, compare_wealth_graph_policy, build_wealth_graph_route,
        )
    elif is_career_category(category):
        domain, resolver, comparator, reviewer = (
            "career", resolve_career_graph_inputs, compare_career_graph_policy, build_career_graph_route,
        )
    elif is_health_category(category):
        domain, resolver, comparator, reviewer = (
            "health", resolve_health_graph_inputs, compare_health_graph_policy, build_health_graph_route,
        )
    elif is_marriage_graph_request(category, query_plan):
        domain, resolver, comparator, reviewer = (
            "marriage", resolve_marriage_graph_inputs, compare_marriage_graph_policy, build_marriage_graph_route,
        )
    elif is_wealth_category(category):
        domain, resolver, comparator, reviewer = (
            "wealth", resolve_wealth_graph_inputs, compare_wealth_graph_policy, build_wealth_graph_route,
        )
    elif is_education_category(category):
        domain, resolver, comparator, reviewer = (
            "education", resolve_education_graph_inputs, compare_education_graph_policy, build_education_graph_route,
        )
    elif is_children_category(category):
        domain, resolver, comparator, reviewer = (
            "children", resolve_children_graph_inputs, compare_children_graph_policy, build_children_graph_route,
        )
    elif is_foreign_category(category):
        domain, resolver, comparator, reviewer = (
            "foreign_life", resolve_foreign_graph_inputs, compare_foreign_graph_policy, build_foreign_graph_route,
        )
    elif is_home_category(category):
        domain, resolver, comparator, reviewer = (
            "home_property", resolve_home_graph_inputs, compare_home_graph_policy, build_home_graph_route,
        )
    elif is_nakshatra_category(category):
        domain, resolver, comparator, reviewer = (
            "nakshatra", resolve_nakshatra_graph_inputs, compare_nakshatra_graph_policy, build_nakshatra_graph_route,
        )
    else:
        return None

    try:
        inputs = resolver(intent=intent, context=context, query_plan=query_plan)
        comparison = comparator(**inputs, context=context)
        review = reviewer(comparison)
        if not isinstance(comparison, Mapping) or not isinstance(review, Mapping):
            raise RuntimeError(f"No compiled {domain} graph route resolved")
        review = dict(review)
        review["live"] = True
        review["enforcement"] = "authoritative_pre_generation"
        return _live_contract(domain, comparison, review)
    except Exception as exc:
        LOGGER.exception("INSTANT_GRAPH_LIVE_RESOLUTION_FAILED domain=%s", domain)
        return {
            "live": False,
            "enforcement": "fallback_non_graph",
            "domain": domain,
            "evidence_status": "graph_unavailable",
            "error": f"{type(exc).__name__}: {exc}",
        }


def apply_live_graph_policy(
    packet: dict[str, Any],
    *,
    intent: Mapping[str, Any] | None,
    context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach a live graph contract to the packet before composer generation."""
    result = dict(packet or {})
    query_plan = dict(result.get("query_plan") or {})
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), Mapping) else {}
    if time_scope.get("is_exact_day"):
        # Exact-day materialisation has its own calculator contract (five-level
        # dasha, Moon/Tara and KP). A static domain route must never overwrite
        # that temporal lens with vocation, promise or profile evidence.
        # The sole exception is the authored Wealth intraday-trading route,
        # which is itself an exact-day session contract.
        wealth_subtype = str(
            query_plan.get("wealth_subtype")
            or (intent or {}).get("wealth_subtype")
            or ""
        ).strip().lower()
        if wealth_subtype != "intraday_trading":
            return result
    graph_context = dict(context or {})
    # The fused verdict owns option-specific comparison rows.  Make that
    # adjudicated evidence visible to the graph comparator without copying it
    # into the legacy normalized context.
    graph_context["_graph_packet_verdict"] = result.get("verdict") or {}
    policy = resolve_live_graph_policy(intent=intent, context=graph_context, query_plan=query_plan)
    if policy is None:
        return result

    result["knowledge_graph_policy"] = policy
    query_plan["knowledge_graph_route"] = {
        key: policy.get(key)
        for key in ("live", "domain", "runtime_key", "ontology_resource", "ontology_version", "enforcement")
        if policy.get(key) is not None
    }
    result["query_plan"] = query_plan

    answer_spec = dict(result.get("answer_spec") or {})
    compact_policy = {
        key: value for key, value in policy.items() if key != "route"
    }
    if (
        policy.get("domain") == "career"
        and policy.get("runtime_key") == "general"
        and policy.get("period_outlook_override")
    ):
        compact_policy["claim_permission"] = "bounded_career_period_outlook"
        compact_policy["instruction"] = (
            "Answer the requested overall career period from the calculated natal career foundation plus the "
            "supplied dasha and transit delivery evidence. Cover the whole requested period, keep D1 and D10 "
            "identities separate, and do not replace the answer with a static career profile or a deeper-mode fallback."
        )
        compact_policy["period_outlook_rules"] = {
            "scope": "bounded overall-career outlook",
            "required_evidence": [
                "D1 career foundation",
                "D10 professional expression",
                "Amatyakaraka and Karakamsha vocation context",
                "dasha activation",
                "transit delivery",
            ],
            "forbidden_moves": [
                "Do not omit the requested period.",
                "Do not apply the static-route exclusion to requested dasha or transit evidence.",
                "Do not send a complete bounded career outlook to Standard or Premium mode.",
            ],
        }
    if policy.get("domain") == "marriage" and str(policy.get("runtime_key") or "") in {
        "marriage_timing", "relationship_timing", "separation_reconciliation_timing",
        "engagement_wedding_timing",
    }:
        compact_policy["specific_partner_scope"] = {
            "single_chart_can_answer": [
                "the native chart's marriage or relationship promise",
                "the native chart's relationship activation and reconnection periods",
                "pressure, delay, family-resistance, or continuity themes shown in the native chart",
            ],
            "single_chart_cannot_prove": [
                "that one named independent person will choose marriage",
                "the named person's feelings, intentions, family decision, or future actions",
                "two-chart compatibility or mutually aligned timing",
            ],
            "answer_rule": (
                "Answer every supported native-chart part first. If the user asks about one named partner, add one "
                "plain limitation sentence for the identity-specific part; do not refuse or suppress the supported "
                "relationship direction and timing merely because the partner's chart is unavailable."
            ),
        }
    if (
        policy.get("domain") == "marriage"
        and str(query_plan.get("marriage_subtype") or "")
        in {"current_relationship_state", "specific_partner_decision"}
    ):
        specific_decision = (
            str(query_plan.get("marriage_subtype") or "") == "specific_partner_decision"
        )
        compact_policy["claim_permission"] = "native_current_relationship_climate_only"
        rule_key = (
            "specific_partner_decision_rules" if specific_decision
            else "current_relationship_state_rules"
        )
        compact_policy[rule_key] = {
            "scope": "current relationship climate in the native chart",
            "requested_action": (
                str(query_plan.get("third_party_action") or "other_voluntary_action")
                if specific_decision else None
            ),
            "required_answer_order": [
                (
                    "state that the specific voluntary action actually asked about, and its decision date, cannot be predicted from the native chart"
                    if specific_decision else
                    "state that the other person's private state cannot be confirmed from the native chart"
                ),
                "give only the native's relationship opportunity or clarification climate from supplied dasha and transit evidence",
                "separate a relationship-active period from the independent person's consent or choice",
                "give one grounded observation the user can verify through direct, respectful communication",
            ],
            "forbidden_claims": [
                "the ex or partner has definitely moved on",
                "the ex or partner still loves, misses, remembers or thinks about the native",
                "the ex or partner made a difficult emotional decision",
                "the other person will accept or reject the proposal",
                "the other person will return, reconnect, contact, respond, commit or marry",
                "the couple will definitely be happy together",
                "a date or window when the other person will decide or consent",
                "the ex or partner's motives, memories, intentions or emotional rebirth",
                "generic Yogi, Gandanta or other natal modifiers as proof of the other person's state",
            ],
        }
        compact_policy["instruction"] = (
            (
                "This asks for an independent person's future voluntary decision. Open by naming the actual action "
                "the user asked about (proposal, return/reconciliation, contact/response, commitment/marriage, or "
                "another voluntary choice) and saying the native chart cannot predict whether or when that person "
                "will take it. Never mention a proposal unless the user actually asked about a proposal. If calculated timing is "
                "available, label it only as the native's relationship-opportunity or clarification period—not the "
                "other person's acceptance window. Respect consent and existing commitments. "
                if specific_decision else
                "This is a present-state timing question, not a static natal profile. Use the supplied current dasha "
                "and transit evidence to describe only the native chart's present relationship climate. Open by saying "
                "that the ex or partner's private emotional state cannot be confirmed from this chart. "
            )
            + "Never convert relationship pressure, closure or reconnection activation into a factual claim about "
            "that person's mind or choice. Never use Yogi, Gandanta, Dagdha or unrelated natal modifiers as the reason."
        )
    missing = [str(value) for value in policy.get("missing_required_factors") or []]
    timing_missing = [
        value for value in missing
        if any(marker in value.lower() for marker in ("dasha", "transit", "kp"))
    ]
    time_bound_mode = str(query_plan.get("answer_mode") or "") in {
        "event_prediction", "timing_window", "event_timing"
    } or bool(
        policy.get("domain") == "wealth"
        and policy.get("runtime_key") in {
            "wealth_timing", "income_timing", "debt_repayment",
            "loan_support", "loan_decision", "investment_timing", "inheritance_timing",
            "intraday_trading",
        }
    ) or bool(
        policy.get("domain") == "education"
        and str(policy.get("runtime_key") or "").endswith("_timing")
    ) or bool(
        policy.get("domain") == "children"
        and str(policy.get("runtime_key") or "") in {
            "conception_timing", "childbirth_timing", "first_child", "subsequent_child",
            "assisted_conception_timing", "adoption_timing", "parenthood_vs_career_timing",
            "parent_child_reconciliation_timing", "retrospective_child_timing",
        }
    ) or bool(
        policy.get("domain") == "foreign_life"
        and str(policy.get("runtime_key") or "") in {
            "short_travel_timing", "long_travel_timing", "retrospective_travel",
            "domestic_relocation_timing", "foreign_travel_timing", "foreign_residence_timing",
            "settlement_timing", "visa_timing", "return_home_timing",
        }
    ) or bool(
        policy.get("domain") == "home_property"
        and str(policy.get("runtime_key") or "") in {
            "property_purchase_timing", "property_sale_timing", "construction_timing",
            "relocation_timing", "vehicle_timing", "possession_documentation_timing",
            "retrospective_property_timing",
        }
    )
    love_arranged_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "love_arranged_marriage"
    )
    married_life_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "married_life"
    )
    spouse_meeting_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_meeting"
    )
    spouse_profile_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_profile"
    )
    spouse_appearance_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_appearance"
    )
    spouse_location_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_location"
    )
    marriage_remedy_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "marriage_remedies"
    )
    property_remedy_route = bool(
        policy.get("domain") == "home_property"
        and policy.get("runtime_key") == "property_remedy"
    )
    wealth_route = policy.get("domain") == "wealth"
    # Career option comparisons use calculated future option windows.  Love
    # versus arranged marriage is a static natal-pathway comparison, so it
    # must never inherit that timing-based winner machinery.
    comparison_mode = bool(
        str(query_plan.get("answer_mode") or "") == "comparison_choice"
        and not love_arranged_route
        and not (
            policy.get("domain") == "wealth"
            and policy.get("runtime_key") == "investing_vs_trading"
        )
        and not (
            policy.get("domain") == "education"
            and policy.get("runtime_key") in {"course_comparison", "education_vs_work"}
        )
    )
    verdict_missing = {
        str(value) for value in (result.get("verdict") or {}).get("missing_required_capabilities") or []
    }
    if policy.get("domain") == "health" and "parashari.health_body_area" in verdict_missing:
        compact_policy["body_area_permission"] = "none"
        compact_policy["instruction"] = (
            "Body-area evidence is unavailable, so do not name a body zone, organ, system, symptom pattern, or "
            "condition. Continue answering the requested general health outlook from the supported natal health "
            "foundation and, for a time-bound question, its supplied dasha and transit phases."
        )
        answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and policy.get("domain") == "education":
        runtime_key = str(policy.get("runtime_key") or "education")
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        foundation = normalized.get("education_foundation") if isinstance(normalized.get("education_foundation"), Mapping) else {}
        static_route = not runtime_key.endswith("_timing")
        education_rules = {
            "runtime_key": runtime_key,
            "static_route": static_route,
            "primary_evidence": "evidence.education_foundation",
            "route_synthesis": foundation.get("route_synthesis") or {},
            "higher_education_synthesis": (
                foundation.get("higher_education_synthesis") or {}
                if runtime_key in {"higher_education", "higher_education_timing"}
                else {}
            ),
            "timing_windows": list(foundation.get("timing_windows") or [])[:6],
            "route_specific_syntheses": {
                key: foundation.get(key) or {}
                for key in (
                    "overall_synthesis", "learning_style_synthesis", "subject_synthesis",
                    "target_assessment", "option_synthesis", "exam_synthesis",
                    "admission_synthesis", "scholarship_synthesis", "research_synthesis",
                    "foreign_study_synthesis", "obstacle_synthesis", "resume_synthesis",
                    "education_vs_work_synthesis", "remedy_synthesis",
                )
            },
            "required_order": [
                "answer the exact education/exam/research question",
                "state the D1 promise",
                "state how D24 confirms or qualifies it using at least one supplied D24 planet/house/lord condition",
                "apply the route-specific house chain and significators",
                "give one grounded practical implication",
            ],
            "forbidden_moves": [
                "Never decide from one house, lord or planet.",
                "Never treat D24 availability as a positive confirmation by itself.",
                "Never say D1 or D24 confirms/supports without naming at least one actual supplied condition from route_synthesis; if no condition survived, state that limitation.",
                "Never guarantee an exam result, admission, scholarship, course outcome, research completion or foreign study.",
                "Never label intelligence or cognitive worth.",
                "Never convert foreign-study evidence into settlement or immigration evidence.",
                "Never use D9 outside research qualification. Use D10 only for education-versus-work or research-career conversion.",
                "Never mention timing in a static route or a date absent from calculated timing_windows.",
                "Never use H4 to decide postgraduate or higher-education promise; H9 is primary, H5 qualifies academic depth, H11 realizes the outcome, and D24 must be interpreted rather than merely named.",
                "Never recommend a subject, profession or creative/analytical field in a higher-education capacity answer unless the user separately asks field fit.",
            ],
        }
        compact_policy["education_answer_rules"] = education_rules
        answer_spec["education_answer_rules"] = education_rules
        compact_policy["instruction"] = (
            "Use the calculated Education foundation as the sole answer-bearing source. Synthesize D1 and D24; "
            "then apply route_synthesis and its named route-specific ledger. A chart being calculated is not itself "
            "a supportive result. Do not replace a pressured or not-established verdict with generic optimism."
        )
        if runtime_key in {"higher_education", "higher_education_timing"}:
            compact_policy["instruction"] += (
                " For postgraduate education, higher_education_synthesis is controlling: begin with H9, then H5 "
                "and H11, and use actual D24 house-lord conditions. H4 is explicitly excluded. Do not turn this "
                "capacity question into a subject or profession recommendation."
            )
        if missing and not timing_missing:
            compact_policy["claim_permission"] = "qualified_education_only"
            compact_policy["instruction"] += (
                " Some required static factors are unavailable; identify the missing layer and limit only the claim "
                "that depends on it rather than replacing the whole answer with a generic refusal."
            )
    if bool(policy.get("live")) and policy.get("domain") == "children":
        runtime_key = str(policy.get("runtime_key") or "children_overview")
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        foundation = normalized.get("children_foundation") if isinstance(normalized.get("children_foundation"), Mapping) else {}
        boundary_permissions = {
            "two_chart_children_handoff": "children_two_chart_handoff",
            "child_chart_required_handoff": "children_child_chart_handoff",
            "muhurat_handoff": "children_muhurat_handoff",
            "legal_custody_handoff": "children_legal_handoff",
            "fetal_sex_refusal": "children_fetal_sex_refusal",
        }
        if runtime_key in boundary_permissions:
            compact_policy["claim_permission"] = boundary_permissions[runtime_key]
        elif runtime_key == "medical_safety_handoff":
            compact_policy["claim_permission"] = "children_medical_hybrid"
        static_route = runtime_key not in {
            "conception_timing", "childbirth_timing", "first_child", "subsequent_child",
            "assisted_conception_timing", "adoption_timing", "parenthood_vs_career_timing",
            "parent_child_reconciliation_timing", "retrospective_child_timing",
        }
        children_rules = {
            "runtime_key": runtime_key,
            "static_route": static_route,
            "primary_evidence": "evidence.children_foundation",
            "route_synthesis": foundation.get("route_synthesis") or {},
            "promise_synthesis": foundation.get("promise_synthesis") or {},
            "child_order_synthesis": foundation.get("child_order_synthesis") or {},
            "pathway_synthesis": foundation.get("pathway_synthesis") or {},
            "claim_boundaries": foundation.get("claim_boundaries") or {},
            "required_order": [
                "answer the exact children or parenthood question",
                "state the D1 promise using an actual supplied condition",
                "state how D7 confirms or qualifies it using an actual supplied condition",
                "apply the route-specific child-order, pathway, relationship or timing synthesis",
                "give one grounded next step without replacing medical, legal or personal judgment",
            ],
            "forbidden_moves": [
                "Never infer conception, birth, adoption, reconciliation or treatment success from one planet or house.",
                "Never call D7 supportive merely because it was calculated.",
                "Never turn delay or pressure into automatic denial.",
                "Never diagnose infertility, pregnancy risk, miscarriage, symptoms or treatment outcome.",
                "Never predict pregnancy loss, fetal sex, an exact child count or twins.",
                "Never use a parent's chart as the child's own personality, health, education, career, marriage or fate chart.",
                "Never present a remedy as fertility treatment or a guarantee.",
                "Never mention timing on a static route or dates absent from timing_windows.",
                "Never expose scores, weights, margins or ranking numbers; translate them into the adjudicated verdict.",
                "Every planet named as a timing reason must have an explicit supplied connection to the selected child-order house and realization chain. Venus is not a generic childbirth carrier and cannot be justified only as happiness, comfort, love or new life.",
                "For nodes, never use fifth or ninth aspects; retain occupation, conjunction and seventh aspect only.",
            ],
        }
        compact_policy["children_answer_rules"] = children_rules
        answer_spec["children_answer_rules"] = children_rules
        compact_policy["instruction"] = (
            "Use the calculated Children foundation as the sole answer-bearing source. D1 establishes promise and "
            "D7 independently confirms or qualifies it. Use the exact route synthesis; first and later children, "
            "conception and childbirth, assisted conception and adoption are not interchangeable routes."
        )
        if runtime_key == "medical_safety_handoff":
            compact_policy["instruction"] += (
                " This is a non-diagnostic hybrid route: calculate and explain the general D1/D7 pregnancy or "
                "parenthood climate after a direct clinical limitation. Never convert support or pressure into a "
                "test, diagnosis, fetal-health, growth, loss, symptom-safety, condition-effect, or treatment claim."
            )
    if bool(policy.get("live")) and policy.get("domain") == "home_property":
        runtime_key = str(policy.get("runtime_key") or "home_life")
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        foundation = normalized.get("home_foundation") if isinstance(normalized.get("home_foundation"), Mapping) else {}
        timing = foundation.get("timing_synthesis") if isinstance(foundation.get("timing_synthesis"), Mapping) else {}
        timing_route = runtime_key in {
            "property_purchase_timing", "property_sale_timing", "construction_timing",
            "relocation_timing", "vehicle_timing", "possession_documentation_timing",
            "retrospective_property_timing",
        }
        def compact_home_transit(row: Mapping[str, Any] | None) -> dict[str, Any]:
            value = row if isinstance(row, Mapping) else {}
            return {
                key: value.get(key)
                for key in (
                    "start", "end", "planet", "strength", "trigger_score",
                    "transit_native_house", "natal_placement_house",
                    "delivered_event_houses", "activated_focus_houses", "why",
                )
                if value.get(key) not in (None, "", [], {})
            }

        def compact_home_window(row: Mapping[str, Any] | None) -> dict[str, Any]:
            value = row if isinstance(row, Mapping) else {}
            activation = value.get("dasha_activation") if isinstance(value.get("dasha_activation"), Mapping) else {}
            transits = value.get("transit_confirmation") or value.get("route_peak_windows") or []
            return {
                key: item
                for key, item in {
                    "start": value.get("start"),
                    "end": value.get("end"),
                    "mahadasha": value.get("mahadasha"),
                    "antardasha": value.get("antardasha"),
                    "pratyantardasha": value.get("pratyantardasha"),
                    "route_success_coverage": value.get("route_success_coverage") or value.get("activated_focus_houses"),
                    "transit_confirmed": value.get("transit_confirmed"),
                    "dasha_activation": {
                        key: activation.get(key)
                        for key in ("mahadasha", "antardasha", "pratyantardasha", "activated_houses", "mechanism")
                        if activation.get(key) not in (None, "", [], {})
                    },
                    "transit_confirmation": [
                        compact_home_transit(item)
                        for item in transits[:2]
                        if isinstance(item, Mapping)
                    ],
                }.items()
                if item not in (None, "", [], {})
            }

        compact_windows = [
            compact_home_window(row)
            for row in list(timing.get("timing_windows") or [])[:2]
            if isinstance(row, Mapping)
        ]
        requested = timing.get("requested_window_assessment") if isinstance(timing.get("requested_window_assessment"), Mapping) else {}
        compact_requested = {
            key: requested.get(key)
            for key in (
                "question_scope", "kind", "start", "end", "dasha_window_matches_requested_period",
                "transit_confirmation_overlaps_requested_period", "supportive_now", "verdict", "rule",
            )
            if requested.get(key) not in (None, "", [], {})
        }
        home_timing_rules = {
            "runtime_key": runtime_key,
            "timing_route": timing_route,
            "primary_evidence": "evidence.home_foundation.timing_synthesis",
            "requested_window_assessment": compact_requested,
            "now_vs_wait_synthesis": timing.get("now_vs_wait_synthesis") or {},
            "kp_fructification": timing.get("kp_fructification") or {},
            "allowed_timing_windows": compact_windows,
            "next_window": compact_home_window(timing.get("next_window")),
            "strongest_window": compact_home_window(timing.get("strongest_window")),
            "required_answer_order": [
                "for an open-ended when question, lead with the next supported window from now_vs_wait_synthesis; otherwise give the direct verdict for the period the user actually asked about",
                "one brief human bridge explaining what that verdict means emotionally and what it does not mean; when natal promise is supported but the requested period is not, frame this as timing rather than permanent denial or personal failure",
                (
                    "one concise D1 vehicle-promise qualification followed by actual D16 vehicle-and-comfort confirmation; use D4 only as an additional comfort/property layer"
                    if runtime_key == "vehicle_timing"
                    else "one concise natal D1 and D4 property-promise qualification"
                ),
                "KP cusp/sub-lord materialisation result",
                "the relevant MD-AD-PD planets and the exact property houses each activates by lordship, occupation or aspect",
                "the named transit planet, dated transit band and exact delivered property houses",
                "the next or stronger calculated window when it differs from the requested period",
                "one practical and psychologically grounding orientation without guaranteeing a transaction or replacing financial/legal judgment",
                "one emotionally relevant question about the user's urgency, hoped-for security, family pressure or actual competing timeframe",
            ],
            "human_bridge_rules": {
                "required": True,
                "length": "one or two natural sentences",
                "language": "same language, script and conversational register as the user's question",
                "grounding": "derive only from promise_verdict, requested_window_assessment and now_vs_wait_synthesis",
                "allowed_distinctions": [
                    "timing mismatch versus permanent denial when natal promise is supported",
                    "careful waiting versus passive avoidance",
                    "transaction caution versus lack of personal capacity",
                ],
                "forbidden": [
                    "canned empathy",
                    "invented feelings or family circumstances",
                    "therapy language or psychological diagnosis",
                    "fear, scarcity, fake urgency or dependency",
                    "withholding the calculated answer to provoke another message",
                ],
            },
            "claim_gates": [
                "Natal promise establishes capacity only; it never proves that the requested period is good.",
                "A dasha name alone is not timing evidence. State its supplied activated houses and mechanism.",
                "KP completeness is not the same as support. An affirmative window requires kp_fructification.verdict=supported; qualified must be described as conditional and pressured cannot produce a positive window.",
                "A transit is confirmation only when its supplied dated row names the transit planet and delivered event houses.",
                "A present-period yes is allowed only when requested_window_assessment.supportive_now is true.",
                "When requested_window_assessment.question_scope is next_event_window, never call the scan-anchor day a requested or supportive period; lead with next_window.",
                "For a now-versus-wait question, copy the direction of now_vs_wait_synthesis.decision and required_visible_conclusion; never leave the user to infer it from dates.",
                "A future transit peak elsewhere in the same dasha cannot be presented as proof that today is supportive.",
                "Never invent a date from the as-of date, scan boundary, current dasha boundary or first sampled transit date.",
                "Never print internal schema or workflow labels such as route synthesis, runtime key, graph policy, evidence status, selected mode or source.",
                "Do not end with a generic offer to compare timeframes when a more human question can clarify why buying now matters to the user.",
            ],
        }
        if timing_route:
            compact_policy["home_timing_rules"] = home_timing_rules
            answer_spec["home_timing_rules"] = home_timing_rules
            compact_policy["instruction"] = (
                "Use the calculated Home foundation as the sole answer-bearing source. "
                + (
                    "For vehicles, D1 establishes the base promise and D16 confirms vehicles and comforts; D4 is only an additional qualification. Never call D16 a property chart or describe the vehicle event as a home/property purchase. "
                    if runtime_key == "vehicle_timing" else
                    "D1 and D4 establish and qualify property promise; "
                )
                + "Only KP fructification, route-filtered dasha-house activation and a dated transit "
                "delivery can establish timing. Follow home_timing_rules and never expose internal field names as headings."
            )
        else:
            compact_policy["instruction"] = (
                (
                    "Use the calculated static D1 and D16 vehicle foundation and the active route synthesis. For vehicle_selection, return only the ranked colour families supplied by route_synthesis with their actual carriers; never invent a lucky colour, purchase window, dasha, transit, KP or date."
                    if runtime_key == "vehicle_selection" else
                    "Use the calculated static D1, D4 and D16 vehicle foundation and the active route synthesis. Do not introduce dasha, transit, KP or dates on this non-timing vehicle route."
                    if runtime_key.startswith("vehicle_") else
                    "Use the calculated static D1 and D4 Home foundation and the active route synthesis. Do not introduce dasha, transit, KP or dates on this non-timing route."
                )
            )
        if property_remedy_route:
            blueprint = normalized.get("remedy_blueprint") if isinstance(normalized.get("remedy_blueprint"), Mapping) else {}
            top = blueprint.get("top_recommendation") if isinstance(blueprint.get("top_recommendation"), Mapping) else {}
            remedy_rules = {
                "scope": "classical property remedy selected from static D1 and D4 obstruction evidence",
                "selection_mode": "single_top",
                "required_count": 1,
                "top_recommendation": dict(top),
                "primary_evidence": "evidence.remedy_blueprint.top_recommendation",
                "required_fields": ["planet", "action", "frequency", "dana", "astrological_reason"],
                "required_answer_order": [
                    "name the single calculated graha-shanti remedy immediately",
                    "state the practice and repetition",
                    "state its traditional dana as optional and according to means",
                    "explain the exact D1 or D4 property pressure that selected this graha",
                    "state that a remedy supports effort and does not guarantee a transaction",
                ],
                "forbidden_moves": [
                    "Do not substitute budgeting, journaling, communication advice or a modern behavioral exercise.",
                    "Do not select the remedy from current dasha, transit or a favorable date.",
                    "Do not prescribe a gemstone without a separate suitability analysis.",
                    "Do not make a Vastu claim without the actual property plan and orientation.",
                    "Do not give another property-delay diagnosis without delivering the remedy.",
                    "Do not guarantee purchase, sale, possession or legal success.",
                ],
            }
            compact_policy["property_remedy_rules"] = remedy_rules
            answer_spec["property_remedy_rules"] = remedy_rules
            compact_policy["instruction"] = (
                "Deliver the single classical property remedy exactly from remedy_blueprint.top_recommendation. "
                "Translate it into the user's language without changing the mantra, count, practice or chart reason."
            )
            verdict = dict(result.get("verdict") or {})
            verdict["missing_required_capabilities"] = [
                value for value in verdict.get("missing_required_capabilities") or []
                if not any(token in str(value).lower() for token in ("dasha", "transit", "kp"))
            ]
            result["verdict"] = verdict
            if not top:
                compact_policy["fallback_to_deeper_mode"] = True
                compact_policy["instruction"] = (
                    "A calculated D1/D4 property obstruction and classical remedy are unavailable. Do not improvise "
                    "a generic or modern remedy; use the same-language Standard or Premium fallback."
                )
        if timing_route and timing:
            # home_timing_rules already carries the same compact adjudication.
            # Duplicating it inside the graph policy previously pushed the
            # primary prompt past its budget and made the writer drop facts.
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = compact_windows
            event_rules["required_material_windows"] = compact_windows[:2]
            event_rules["window_answer_rule"] = (
                "For next_event_window scope, answer with next_window first. Otherwise judge the requested period from requested_window_assessment first. Then mention next_window or "
                "strongest_window only as a distinct later/alternate window. Every positive timing statement must "
                "name its dasha-house activation and dated transit confirmation."
            )
            answer_spec["event_rules"] = event_rules
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = (timing.get("requested_window_assessment") or {}).get("verdict") or timing.get("verdict")
            verdict["ranked_windows"] = compact_windows
            verdict["requested_window_assessment"] = compact_requested
            result["verdict"] = verdict
    if bool(policy.get("live")) and policy.get("domain") == "foreign_life":
        runtime_key=str(policy.get("runtime_key") or "foreign_overview")
        normalized=context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"),Mapping) else {}
        foundation=normalized.get("foreign_foundation") if isinstance(normalized.get("foreign_foundation"),Mapping) else {}
        timing=foundation.get("timing_synthesis") if isinstance(foundation.get("timing_synthesis"),Mapping) else {}
        birth_summary=context.get("birth_summary") if isinstance(context.get("birth_summary"),Mapping) else {}
        ascendant_value=birth_summary.get("ascendant")
        if isinstance(ascendant_value,Mapping):
            native_ascendant=str(ascendant_value.get("sign") or ascendant_value.get("name") or "").strip()
        else:
            native_ascendant=str(ascendant_value or "").strip()
        zodiac_match=re.search(
            r"\b(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)\b",
            native_ascendant,
            re.IGNORECASE,
        )
        native_ascendant=zodiac_match.group(1).title() if zodiac_match else ""
        foundation_text=str(foundation).lower()
        allowed_special_claim_terms=[
            term for term in ("yogi", "avayogi", "gandanta", "tithi-shunya", "dagdha")
            if term in foundation_text
        ]
        def compact_foreign_window(value: Mapping[str,Any] | None) -> dict[str,Any]:
            row=value if isinstance(value,Mapping) else {}
            raw_peaks=row.get("route_peak_windows") or row.get("transit_confirmation") or []
            peaks=[]
            for peak in list(raw_peaks)[:2]:
                if not isinstance(peak,Mapping):
                    continue
                peaks.append({
                    key:peak.get(key) for key in (
                        "start","end","planet","strength","activated_focus_houses","why",
                    ) if peak.get(key) not in (None,"",[],{})
                })
            return {
                key:item for key,item in {
                    "start":row.get("start"),"end":row.get("end"),
                    "mahadasha":row.get("mahadasha"),"antardasha":row.get("antardasha"),
                    "pratyantardasha":row.get("pratyantardasha"),
                    "activated_focus_houses":list(row.get("activated_focus_houses") or [])[:8],
                    "route_success_coverage":list(row.get("route_success_coverage") or [])[:8],
                    "transit_confirmed":row.get("transit_confirmed"),
                    "why":str(row.get("why") or "")[:500],
                    "transit_confirmation":peaks,
                    "claim_rule":row.get("claim_rule"),
                }.items() if item not in (None,"",[],{})
            }
        compact_windows=[
            compact_foreign_window(row)
            for row in list(timing.get("timing_windows") or [])[:3]
            if isinstance(row,Mapping)
        ]
        raw_kp=timing.get("kp_fructification") if isinstance(timing.get("kp_fructification"),Mapping) else {}
        compact_timing={
            "verdict":timing.get("verdict"),
            "dasha_evaluation_complete":timing.get("dasha_evaluation_complete"),
            "transit_evaluation_complete":timing.get("transit_evaluation_complete"),
            "kp_fructification":{
                key:raw_kp.get(key) for key in (
                    "complete","verdict","supported_cusps","required_cusps","cusp_judgments","rule",
                ) if raw_kp.get(key) not in (None,"",[],{})
            },
            "timing_windows":compact_windows,
            "next_window":compact_windows[0] if compact_windows else {},
        }
        timing_route=runtime_key in {
            "short_travel_timing","long_travel_timing","retrospective_travel","domestic_relocation_timing",
            "foreign_travel_timing","foreign_residence_timing","settlement_timing","visa_timing","return_home_timing",
        }
        boundary_permissions={
            "location_recommendation_handoff":"foreign_location_handoff",
            "legal_immigration_handoff":"foreign_legal_handoff",
            "muhurat_handoff":"foreign_muhurat_handoff",
            "travel_safety_handoff":"foreign_safety_handoff",
            "other_person_handoff":"foreign_other_person_handoff",
        }
        if runtime_key in boundary_permissions:
            compact_policy["claim_permission"]=boundary_permissions[runtime_key]
        foreign_rules={
            "runtime_key":runtime_key,
            "timing_route":timing_route,
            "native_ascendant":native_ascendant,
            "allowed_special_claim_terms":allowed_special_claim_terms,
            "primary_evidence":"evidence.foreign_foundation",
            "route_synthesis":foundation.get("route_synthesis") or {},
            "fact_contract":(
                (foundation.get("route_synthesis") or {}).get("fact_contract")
                if isinstance(foundation.get("route_synthesis"), Mapping) else {}
            ) or {},
            "technical_output_contract":{
                "form":"connected explanatory prose, not a chart-fact inventory",
                "maximum_core_facts":3,
                "required_flow":[
                    "give the real-world verdict in plain language",
                    "explain one decisive D1 mechanism by connecting the supplied lord/placement to the life meanings of both houses",
                    "weigh one materially different support or pressure so the reader understands why the verdict is supportive, qualified or pressured",
                    "synthesize the required divisional chart as confirmation or qualification; do not report its rows as a list",
                    "translate the combined evidence into what it means for the requested travel, residence or settlement question",
                ],
                "forbidden_forms":[
                    "three or more consecutive sentences shaped as 'D-chart: H-house fact'",
                    "a standalone dignity statement without explaining why that dignity matters to the route",
                    "listing every relevant house, planet, aspect or divisional chart",
                    "internal methodology language such as 'these links show activation and its direction'",
                    "ending the proof without a synthesis of how the factors combine",
                ],
            },
            "timing_synthesis":compact_timing if timing_route else {},
            "required_order":[
                "answer the exact travel, relocation, residence, visa or settlement question",
                "add one brief human bridge about what the result means for belonging, disruption, uncertainty or readiness, without inventing the user's feelings",
                "state the D1 route promise from the required house combination",
                "use D3 for movement, D4 for residence, D9 for long distance and D12 for rootedness/separation only where the selected route requires them",
                "state how the required divisional charts confirm or qualify the route",
                "for timing only, use complete KP fructification, route-filtered dasha activation and dated transit confirmation",
                "give one grounded practical implication without promising an official or life outcome",
            ],
            "forbidden_moves":[
                "Never establish foreign travel, residence or settlement from House 12 or Rahu alone.",
                "Never convert evidence for travel into evidence for residence or permanent settlement.",
                "Never call a chart supportive merely because it was calculated.",
                "Never guarantee a visa, immigration approval, permanent settlement, safety or legal outcome.",
                "Never introduce timing, dasha, transit or dates on a static route.",
                "Never use a date absent from timing_synthesis.timing_windows.",
                "Never answer a foreign-career, foreign-study or foreign-spouse question as a generic settlement question.",
            ],
            "human_bridge_rules":{
                "required":True,
                "length":"one or two natural sentences",
                "grounding":"derive only from the route verdict, residence continuity, movement pressure and timing result",
                "allowed":"acknowledge the emotional weight of leaving, belonging, waiting, restarting or maintaining roots",
                "forbidden":"invented emotions, family pressure, trauma, psychological diagnosis, canned empathy or dependency language",
            },
            "fact_gate":(
                "Every ascendant, lord, dignity, occupant, aspect and special-condition claim must exactly match "
                "foreign_foundation.charts. Every causal planet claim must name its supplied chart, house and role; "
                "omit any fact or inferred trait that is not supplied there."
            ),
        }
        compact_policy["foreign_answer_rules"]=foreign_rules
        answer_spec["foreign_answer_rules"]=foreign_rules
        compact_policy["instruction"]=(
            "Use the calculated Foreign Life foundation as the sole answer-bearing source. Keep movement, domestic "
            "relocation, foreign travel, residence and permanent settlement distinct. D3 confirms movement, D4 "
            "residence, D9 long distance and D12 rootedness/separation; no one chart or Rahu alone proves the result."
        )
        if timing_route:
            # Keep only route-filtered calculated windows in the composer
            # contract; the full scan remains in the audit packet.
            windows=compact_windows
            event_rules=dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"]=windows
            event_rules["required_material_windows"]=windows[:2]
            event_rules["window_answer_rule"]=(
                "Lead with timing_synthesis.next_window. If KP is supported, call it the next supported window. If "
                "KP is pressured or unsupported, still give its dates as the strongest conditional calculated window "
                "and immediately state that KP does not fully confirm departure. Never replace the requested dates "
                "with the current dasha or preparation advice."
            )
            answer_spec["event_rules"]=event_rules
            verdict=dict(result.get("verdict") or {})
            verdict["direction"]=timing.get("verdict") or (foundation.get("route_synthesis") or {}).get("verdict")
            verdict["ranked_windows"]=windows
            result["verdict"]=verdict
    if bool(policy.get("live")) and policy.get("domain") == "nakshatra":
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        foundation = normalized.get("nakshatra_foundation") if isinstance(normalized.get("nakshatra_foundation"), Mapping) else {}
        runtime_key = str(policy.get("runtime_key") or "birth_star_overview")
        nakshatra_rules = {
            "runtime_key": runtime_key,
            "primary_evidence": "evidence.nakshatra_foundation",
            "carriers": list(foundation.get("carriers") or []),
            "timing_carriers": list(foundation.get("timing_carriers") or []),
            "current_transit_nakshatras": list(foundation.get("current_transit_nakshatras") or []),
            "claim_boundaries": list(foundation.get("claim_boundaries") or []),
            "required_flow": [
                "answer the exact Nakshatra question directly",
                "name the selected carrier, its exact nakshatra and pada",
                "explain the nakshatra quality through the supplied deity/quality and the pada's Navamsha sign",
                "qualify the expression through the supplied nakshatra-lord placement and condition",
                "synthesize the factors in connected prose rather than listing chart rows",
            ],
            "simple_mode": (
                "Use plain language and at most two astrology anchors. Explain what the pattern feels like in life; "
                "do not dump degrees, internal factors, scores or a placement inventory."
            ),
            "technical_mode": (
                "Give connected technical reasoning: carrier -> exact nakshatra/pada -> pada Navamsha -> "
                "nakshatra lord and its actual house/sign condition -> synthesis. Do not output scores or a raw list."
            ),
            "forbidden_moves": [
                "Do not replace the selected carrier with Moon, Mercury, Mars, Rahu, Yogi or Gandanta merely because a generic rule mentions it.",
                "Do not let one nakshatra establish a profession, marriage, money, health outcome or event date.",
                "Do not prescribe a remedy unless runtime_key is nakshatra_remedy.",
                "Do not describe all Gandamoola births as dosha-bearing or remedy-requiring.",
                "Do not infer another person's private feelings, consent or decision.",
            ],
        }
        compact_policy["nakshatra_answer_rules"] = nakshatra_rules
        answer_spec["nakshatra_answer_rules"] = nakshatra_rules
        compact_policy["instruction"] = (
            "Use nakshatra_foundation as the sole source for placements and carrier selection. Interpret the exact "
            "nakshatra, pada, pada Navamsha and nakshatra-lord condition together. A nakshatra modifies a topic; it "
            "does not independently prove a life event."
        )
    if bool(policy.get("live")) and wealth_route:
        runtime_key = str(policy.get("runtime_key") or "")
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        wealth_foundation = normalized.get("wealth_foundation") if isinstance(normalized.get("wealth_foundation"), Mapping) else {}
        wealth_adjudication = (
            dict(wealth_foundation.get("route_adjudication"))
            if isinstance(wealth_foundation.get("route_adjudication"), Mapping)
            else {}
        )
        route_focus = {
            "wealth": "overall wealth potential, accumulation and retention",
            "wealth_source": "primary wealth-building channels",
            "wealth_diagnosis": "savings instability and financial leakage",
            "wealth_timing": "wealth-growth timing",
            "income": "income and cash-flow stability",
            "income_timing": "income-growth timing",
            "multiple_income": "capacity for multiple income streams",
            "debt": "debt and borrowing pattern",
            "debt_diagnosis": "persistent debt mechanism",
            "debt_repayment": "debt-repayment timing",
            "loan_support": "loan-support timing and conditions",
            "loan_decision": "whether new borrowing is advisable for the stated productive purpose and horizon",
            "investing_vs_trading": "long-term investing versus active trading suitability",
            "investment": "investment and speculation suitability",
            "investment_timing": "investment-support timing",
            "intraday_trading": "exact-day intraday trading session climate and market-hour windows",
            "investment_risk": "investment volatility and risk mechanism",
            "loss_vulnerability": "financial-loss vulnerability",
            "inheritance": "inheritance and settlement potential",
            "inheritance_timing": "inheritance or settlement timing",
            "windfall": "sudden-gain potential and retention",
            "wealth_remedies": "calculated financial remedy",
        }.get(runtime_key, "the requested financial timing or decision")
        is_static_wealth = runtime_key not in {
            "wealth_timing", "income_timing", "debt_repayment",
            "loan_support", "loan_decision", "investment_timing", "inheritance_timing",
            "intraday_trading",
        }
        investment_family = runtime_key in {
            "investment", "investing_vs_trading", "investment_timing",
            "investment_risk", "loss_vulnerability", "windfall",
        }
        wealth_answer_rules = {
            "runtime_key": runtime_key,
            "scope": route_focus,
            "static_route": is_static_wealth,
            "primary_evidence": "evidence.wealth_foundation",
            "route_adjudication": wealth_adjudication,
            "investment_synthesis": (
                dict(wealth_foundation.get("investment_synthesis"))
                if investment_family and isinstance(wealth_foundation.get("investment_synthesis"), Mapping)
                else {}
            ),
            "wealth_source_synthesis": (
                dict(wealth_foundation.get("wealth_source_synthesis"))
                if runtime_key in {"wealth_source", "multiple_income"} and isinstance(wealth_foundation.get("wealth_source_synthesis"), Mapping)
                else {}
            ),
            "multiple_income_synthesis": (
                dict(wealth_foundation.get("multiple_income_synthesis"))
                if runtime_key == "multiple_income" and isinstance(wealth_foundation.get("multiple_income_synthesis"), Mapping)
                else {}
            ),
            "loss_vulnerability_synthesis": (
                dict(wealth_foundation.get("loss_vulnerability_synthesis"))
                if runtime_key == "loss_vulnerability" and isinstance(wealth_foundation.get("loss_vulnerability_synthesis"), Mapping)
                else {}
            ),
            "wealth_growth_timing_synthesis": (
                dict(wealth_foundation.get("wealth_growth_timing_synthesis"))
                if runtime_key == "wealth_timing" and isinstance(wealth_foundation.get("wealth_growth_timing_synthesis"), Mapping)
                else {}
            ),
            "loan_decision_synthesis": (
                dict(wealth_foundation.get("loan_decision_synthesis"))
                if runtime_key == "loan_decision" and isinstance(wealth_foundation.get("loan_decision_synthesis"), Mapping)
                else {}
            ),
            "required_answer_order": [
                "direct route-specific financial verdict",
                (
                    "D1 promise, complete fifth-lord/carrier condition, D2 retention, D5 refinement and supporting D9 qualification"
                    if investment_family
                    else "D1 promise and D2 Hora confirmation or qualification"
                ),
                "route-specific financial mechanism from the required houses and divisional chart",
                "earning or gain capacity separated from savings, retention, liabilities and loss exposure",
                (
                    "Indu Lagna, Hora Lagna and Arudha manifestation as supporting evidence"
                    if is_static_wealth
                    else "dasha permission followed by dated transit confirmation within the requested horizon"
                ),
                "one practical non-prescriptive takeaway",
            ],
            "factor_precedence": [
                "D1 establishes financial promise.",
                "D2 confirms or qualifies accumulation and retention.",
                "Route-specific houses and D5, D8 or D10 answer only their authorized question.",
                (
                    "For investment routes, D5 refines speculative judgment and D9 qualifies the underlying carriers; D9 cannot replace D1, D2 or D5."
                    if investment_family
                    else "D9 is not a substitute for the Wealth route's required divisional evidence."
                ),
                "Judge every relevant lord as a combined carrier: placement, dignity, strength, Gandanta, special lordships, conjunctions and declared overlap rules.",
                "Dhana yogas must be operational through actual lords and placements, not merely named.",
                "Indu Lagna, Hora Lagna and Arudha are manifestation support and cannot override D1/D2.",
                "Dasha and transit may time an established promise but cannot create one.",
            ],
            "forbidden_moves": [
                (
                    "Do not use D9 as a standalone Wealth confirmation; on investment routes it may only qualify the supplied D1/D2/D5 carrier evidence."
                    if investment_family
                    else "Do not use D9 as the Wealth confirmation chart; D2 is mandatory."
                ),
                "Do not judge investment or speculation from the fifth lord's destination alone; include every supplied carrier condition and contradiction.",
                (
                    "For an investment route, state the calculated investment_synthesis verdict and actual fifth-lord, D2, D5 and D9 evidence; never say these factors merely 'need to be weighed'."
                    if investment_family
                    else "Do not introduce investment suitability unless the selected route asks for it."
                ),
                "Do not say a natal house is active or activated on a static route; use supports, challenges, strengthens, weakens, connects, occupies or aspects.",
                "Do not call the result a clear yes unless the supplied D1 and D2 synthesis actually supports that strength.",
                "Do not infer salary/service, business, speculation, debt, expenses, inheritance or windfall unless the selected route and supplied evidence support it.",
                "For wealth_source, name and rank the supplied concrete earning channels; savings automation, budgeting and retention discipline are qualifications, not wealth sources.",
                "For multiple_income, answer yes or no from multiple_income_synthesis and name the supplied primary and secondary streams; do not replace them with generic diversification or savings advice.",
                "For loss_vulnerability, rank the supplied loss mechanisms and distinguish volatility, retention leakage and shared-liability exposure; do not answer as generic investment suitability.",
                "Do not let Gandanta, Dagdha Rashi or another special factor replace the D1/D2 synthesis; use it only as a connected modifier.",
                "Do not turn a numerical wealth score into certainty or quote it as a probability.",
                "D2 availability is not a positive verdict; use only wealth_foundation.d2_synthesis.verdict to say whether it confirms or qualifies retention.",
                "When route_adjudication.strength_claim_permission is qualified_only, do not call the foundation strong, genuinely strong, clear, confirmed or unqualified.",
                "Do not infer creativity, beauty, luxury, profession or income channel from Indu Lagna's sign or lord alone.",
                "Do not describe the fifth house as the house of gains. The fifth governs judgment, speculation and investment intelligence; gains belong primarily to the eleventh.",
                "Do not mention current dasha, transit, dates, peaks or current activation on a static route.",
                "Do not use Rahu or Ketu fifth/ninth aspects.",
            ],
        }
        compact_policy["financial_safety_rules"] = {
            "scope": "astrological financial tendencies and timing; not regulated financial advice",
            "required_order": [
                "direct chart-based verdict",
                "promise or capacity evidence",
                "retention and risk qualification",
                "practical non-prescriptive takeaway",
            ],
            "forbidden_moves": [
                "Do not guarantee wealth, returns, profit, inheritance, loan approval, or freedom from loss.",
                "Do not recommend a named security, asset, leverage level, trade, lender, or transaction.",
                "Do not predict index, sector or ticker direction on an intraday trading route.",
                "Do not infer timing from natal promise or Indu Lagna alone.",
                "Do not use dasha or transit language on a static route.",
                "Do not treat Indu Lagna as an exact-degree point or as overriding D1 and D2.",
                "Do not describe Rahu or Ketu fifth/ninth aspects; node activation is occupation, conjunction, or seventh aspect only.",
                "Do not predict another person's death in an inheritance answer.",
            ],
        }
        compact_policy["instruction"] = (
            "Synthesize only the supplied Wealth foundation in the graph's decision order. Generic natal-promise "
            "or D9 evidence cannot replace D1 and D2; investment routes may use supplied D9 only as a carrier "
            "qualification after D5. Separate earning capacity, retention, risk and timing. "
            "Follow wealth_answer_rules and financial_safety_rules exactly."
        )
        compact_policy["wealth_answer_rules"] = wealth_answer_rules
        compact_policy["wealth_adjudication"] = wealth_adjudication
        answer_spec["financial_safety_rules"] = compact_policy["financial_safety_rules"]
        answer_spec["wealth_answer_rules"] = wealth_answer_rules
        if runtime_key == "intraday_trading":
            session = (
                dict(wealth_foundation.get("intraday_trading_session"))
                if isinstance(wealth_foundation.get("intraday_trading_session"), Mapping)
                else {}
            )
            wealth_answer_rules["intraday_trading_session"] = session
            wealth_answer_rules["required_answer_order"] = [
                "sit-out, reduce-size or participate verdict for the requested session day",
                "Vimshottari MD/AD/PD period permission, then today's Tara, Chandra, gochara, Ashtakavarga and Panchanga climate",
                "usable versus caution Muhurta segments inside the verified market session",
                "one practical risk (overtrading, stops, calculation error) and the non-market-forecast disclaimer",
                "at most one plain sentence about natal D1/D2 capacity; never use D5, Indu Lagna or KP on this route",
            ]
            wealth_answer_rules["forbidden_moves"].extend([
                "Do not predict whether Nifty, a sector, option or named security will rise or fall.",
                "Do not recommend a ticker, strike, leverage level or guaranteed P&L.",
                "Do not treat Choghadiya alone as an entry signal; every window must also contain Hora, Muhurta ascendant, house-lord, active-dasha and Panchanga evidence.",
                "Do not answer a lifetime investing-versus-trading suitability question on this route.",
                "Do not use windows outside 09:15-15:30 or invent times when windows are empty.",
                "If participation is sit_out or the market is closed, do not still advise new entries.",
            ])
            compact_policy["instruction"] = (
                "Answer only the requested trading session. Lead with sit-out versus participate from "
                "intraday_trading_session.participation, explain period permission and today's changing evidence, "
                "then give the calculated market-hour Muhurta windows. Natal charts are background capacity only, "
                "not today's trigger. This is the native's judgment climate, not a market call."
            )
            session_windows = [
                {
                    "start": row.get("start"),
                    "end": row.get("end"),
                    "label": f"{row.get('hora_lord') or ''} Hora / {row.get('choghadiya') or ''}".strip(" /"),
                    "quality": row.get("verdict"),
                }
                for row in list(session.get("entry_windows") or [])
                if isinstance(row, Mapping)
            ]
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = str(session.get("participation") or "cautious")
            verdict["ranked_windows"] = session_windows
            verdict["rationale"] = {
                "source": "wealth_foundation.intraday_trading_session",
                "signal": session.get("signal"),
                "headline": session.get("headline"),
                "claim_rule": session.get("claim_rule"),
            }
            result["verdict"] = verdict
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = session_windows
            event_rules["window_answer_rule"] = session.get("claim_rule")
            answer_spec["event_rules"] = event_rules
        if runtime_key == "wealth_timing":
            growth_synthesis = (
                dict(wealth_foundation.get("wealth_growth_timing_synthesis"))
                if isinstance(wealth_foundation.get("wealth_growth_timing_synthesis"), Mapping)
                else {}
            )
            growth_windows = [
                dict(row) for row in list(growth_synthesis.get("ranked_growth_windows") or [])
                if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
            ]
            compact_policy["wealth_growth_timing_synthesis"] = growth_synthesis
            wealth_answer_rules["wealth_growth_timing_synthesis"] = growth_synthesis
            wealth_answer_rules["forbidden_moves"].extend([
                "Do not call the current/as-of date or current dasha boundary the next wealth-growth period.",
                "Do not equate financial activity, house 5, Rahu opportunity or a high generic event score with realized wealth growth.",
                "Lead with the earliest supplied future meaningful-growth phase; name the stronger later phase separately when supplied.",
                "Do not claim an exact gain, transaction or windfall date; present the supplied broad support windows.",
            ])
            if growth_synthesis.get("forecast_kind") == "bounded_period_support_forecast":
                wealth_answer_rules["forbidden_moves"].extend([
                    "Do not apply the open-future event threshold to a bounded month, quarter or year forecast.",
                    "Do not refuse a bounded forecast when bounded_period_synthesis maps stronger, secondary and lower-support months.",
                    "Do not collapse the requested calendar period into one dasha boundary; cover its full chronological progression.",
                ])
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = (
                "bounded_wealth_support_forecast"
                if growth_synthesis.get("forecast_kind") == "bounded_period_support_forecast"
                else "future_wealth_growth_phases"
                if growth_windows else "insufficient_future_wealth_growth_evidence"
            )
            verdict["ranked_windows"] = growth_windows
            verdict["rationale"] = {
                "source": "wealth_foundation.wealth_growth_timing_synthesis",
                "current_window_assessment": growth_synthesis.get("current_window_assessment"),
                "partial_support_windows": growth_synthesis.get("partial_support_windows"),
                "claim_rule": growth_synthesis.get("claim_rule"),
            }
            result["verdict"] = verdict
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = growth_windows
            event_rules["required_material_windows"] = growth_windows[:2]
            event_rules["window_answer_rule"] = growth_synthesis.get("claim_rule")
            answer_spec["event_rules"] = event_rules
            if (
                not growth_windows
                and growth_synthesis.get("forecast_kind") != "bounded_period_support_forecast"
                and not timing_missing
            ):
                compact_policy["claim_permission"] = "no_ranked_wealth_growth_window"
                compact_policy["instruction"] = (
                    "No route-adjudicated future wealth-growth phase is available. Do not turn the current date, "
                    "financial activity or a dasha boundary into growth timing."
                )
        if runtime_key == "debt_repayment":
            debt_synthesis = (
                dict(wealth_foundation.get("debt_repayment_synthesis"))
                if isinstance(wealth_foundation.get("debt_repayment_synthesis"), Mapping)
                else {}
            )
            repayment_windows = [
                dict(row) for row in list(debt_synthesis.get("ranked_repayment_windows") or [])
                if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
            ]
            compact_policy["debt_repayment_synthesis"] = debt_synthesis
            wealth_answer_rules["debt_repayment_synthesis"] = debt_synthesis
            wealth_answer_rules["forbidden_moves"].extend([
                "Do not call the current/as-of date a repayment marker merely because a current dasha segment begins there.",
                "Debt, eighth-house or twelfth-house activation is pressure/activity, not repayment support by itself.",
                "Do not claim an exact payoff or debt-free date; present only the supplied broad repayment-support windows.",
                "Do not prescribe consolidation, refinancing, highest-interest-first repayment or another financial strategy unless the user explicitly asks for practical financial guidance.",
            ])
            compact_policy["financial_safety_rules"]["forbidden_moves"].append(
                "Do not prescribe debt consolidation, refinancing or a repayment ordering in an astrology answer."
            )
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = (
                "probable_repayment_support_windows"
                if repayment_windows else "insufficient_debt_repayment_timing_evidence"
            )
            verdict["ranked_windows"] = repayment_windows
            verdict["rationale"] = {
                "source": "wealth_foundation.debt_repayment_synthesis",
                "current_window_assessment": debt_synthesis.get("current_window_assessment"),
                "preparatory_relief_windows": debt_synthesis.get("preparatory_relief_windows"),
                "claim_rule": debt_synthesis.get("claim_rule"),
            }
            result["verdict"] = verdict
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = repayment_windows
            event_rules["required_material_windows"] = repayment_windows[:2]
            event_rules["window_answer_rule"] = debt_synthesis.get("claim_rule")
            answer_spec["event_rules"] = event_rules
            if not repayment_windows and not timing_missing:
                compact_policy["claim_permission"] = "no_ranked_debt_repayment_window"
                compact_policy["instruction"] = (
                    "No route-adjudicated debt-repayment window is available. Do not turn debt-house activity or the "
                    "current date into repayment timing. Explain that a reliable window was not established."
                )
        if runtime_key == "loan_decision":
            loan_synthesis = (
                dict(wealth_foundation.get("loan_decision_synthesis"))
                if isinstance(wealth_foundation.get("loan_decision_synthesis"), Mapping)
                else {}
            )
            scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), Mapping) else {}
            scope_start = str(scope.get("as_of") or "")[:10]
            scope_end = str(scope.get("horizon_end") or "")[:10]
            decision_windows = []
            for raw_row in list(loan_synthesis.get("decision_windows") or []):
                if not isinstance(raw_row, Mapping):
                    continue
                row = dict(raw_row)
                row_start = str(row.get("start") or "")[:10]
                row_end = str(row.get("end") or "")[:10]
                if scope_start and row_end and row_end < scope_start:
                    continue
                if scope_end and row_start and row_start > scope_end:
                    continue
                if scope_start and row_start and row_start < scope_start:
                    row["start"] = scope_start
                if scope_end and row_end and row_end > scope_end:
                    row["end"] = scope_end
                bounded_peaks = []
                for raw_peak in list(row.get("peak_windows") or []):
                    if not isinstance(raw_peak, Mapping):
                        continue
                    peak = dict(raw_peak)
                    peak_start = str(peak.get("start") or "")[:10]
                    peak_end = str(peak.get("end") or "")[:10]
                    if scope_start and peak_end and peak_end < scope_start:
                        continue
                    if scope_end and peak_start and peak_start > scope_end:
                        continue
                    if scope_start and peak_start and peak_start < scope_start:
                        peak["start"] = scope_start
                    if scope_end and peak_end and peak_end > scope_end:
                        peak["end"] = scope_end
                    bounded_peaks.append(peak)
                row["peak_windows"] = bounded_peaks
                decision_windows.append(row)
            decision_windows.sort(key=lambda row: str(row.get("start") or ""))
            supportive_windows = [
                row for row in decision_windows if int(row.get("tier") or 0) >= 2
            ]
            loan_synthesis["requested_horizon_windows"] = decision_windows
            loan_synthesis["supportive_horizon_windows"] = supportive_windows
            loan_synthesis["horizon_verdict"] = (
                "conditional_support_only_not_a_borrowing_recommendation"
                if supportive_windows
                else "not_a_clean_astrological_green_light_for_new_expansion_debt"
            )
            compact_policy["loan_decision_synthesis"] = loan_synthesis
            wealth_answer_rules["loan_decision_synthesis"] = loan_synthesis
            wealth_answer_rules["forbidden_moves"].extend([
                "Do not treat loan availability, house 6/8 activation or possible approval as evidence that taking the loan is advisable.",
                "Do not call the decision supported unless repayment resources 2/11 and business conversion 7/10/11 are confirmed in the same KP-dasha-transit chain.",
                "Do not turn general business or gain potential into approval of new leverage during the requested horizon.",
                "Do not recommend borrowing from astrology alone; explicitly require conventional cash-flow, borrowing-cost and downside review.",
            ])
            compact_policy["financial_safety_rules"]["forbidden_moves"].append(
                "Do not recommend taking, increasing or refinancing debt from astrology alone."
            )
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = loan_synthesis["horizon_verdict"]
            verdict["ranked_windows"] = decision_windows
            verdict["rationale"] = {
                "source": "wealth_foundation.loan_decision_synthesis",
                "d2_retention": loan_synthesis.get("d2_retention"),
                "business_expansion_foundation": loan_synthesis.get("business_expansion_foundation"),
                "decision_rule": loan_synthesis.get("decision_rule"),
                "claim_rule": loan_synthesis.get("claim_rule"),
            }
            result["verdict"] = verdict
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = decision_windows
            event_rules["required_material_windows"] = decision_windows
            event_rules["window_answer_rule"] = loan_synthesis.get("claim_rule")
            answer_spec["event_rules"] = event_rules
            if not decision_windows and not timing_missing:
                compact_policy["claim_permission"] = "no_loan_decision_horizon_evidence"
                compact_policy["instruction"] = (
                    "No route-adjudicated evidence covers the requested loan-decision horizon. Do not substitute a "
                    "static debt pattern, generic business promise or current dasha for a proceed/avoid verdict."
                )
        if time_bound_mode:
            # Every required Wealth factor belongs to the timing chain. Missing
            # natal/divisional promise is as disqualifying as missing dasha or
            # transit confirmation; timing must not be manufactured on top of it.
            timing_missing = list(missing)
        elif missing:
            compact_policy["claim_permission"] = "no_complete_wealth_verdict"
            compact_policy["instruction"] = (
                "Required Wealth evidence is incomplete. State which graph factors are unavailable and give only "
                "the bounded observations supported by evidence.wealth_foundation. Do not substitute D9, generic "
                "natal promise, current activation, or planet folklore for the missing layer."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and married_life_route:
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        foundation = (
            normalized.get("married_life_foundation")
            if isinstance(normalized.get("married_life_foundation"), Mapping)
            else {}
        )
        married_life_rules = {
            "scope": "static married-life quality and continuity; no timing",
            "evidence_complete": bool(foundation.get("evidence_complete")),
            "primary_evidence": "evidence.married_life_foundation",
            "required_answer_order": list(foundation.get("interpretation_order") or []),
            "required_layers": [
                "D1 Houses 7, 2, 11, 8 and 12 with seventh-lord condition",
                "D9 Houses 1, 7, 2, 8, 11 and 12",
                "Venus and Jupiter in D1 and D9",
                "Darakaraka, Upapada, second from Upapada and Darapada A7",
            ],
            "forbidden_moves": [
                "Do not decide married-life quality from House 2, Yogi lord, Gandanta or another single modifier.",
                "Do not use communication advice as a substitute for analyzing the marriage bond and D9.",
                "Do not mix D1 and D9 identities or mix Parashari reasoning with Jaimini reasoning.",
                "Do not mention dasha, transit, dates, divorce certainty or the spouse's hidden motives.",
                "Do not expose scores or weights.",
            ],
        }
        compact_policy["married_life_rules"] = married_life_rules
        answer_spec["married_life_rules"] = married_life_rules
        answer_spec["max_words"] = max(int(answer_spec.get("max_words") or 0), 480)
        answer_spec["composer_word_target"] = "Usually 260-420 words; preserve every D1, D9 and Jaimini layer without listing raw scores."
        compact_policy["instruction"] = (
            "Use the married_life_foundation as the sole answer-bearing source. Begin with D1 House 7 and its lord; "
            "then judge continuity through Houses 2/11 and intimacy/strain through Houses 8/12. Require D9 confirmation "
            "and separately qualify the result with Venus/Jupiter and Jaimini Darakaraka-Upapada evidence."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["direction"] = "synthesize_from_married_life_foundation"
        verdict["scope"] = "static married-life quality from D1, D9 and Jaimini evidence"
        result["verdict"] = verdict
        if not foundation.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_complete_married_life_verdict"
            compact_policy["instruction"] = (
                "The required D1-D9-Jaimini married-life foundation is incomplete. State the missing calculation layer "
                "and do not replace it with generic House 2, Mercury, Yogi or Gandanta advice."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and love_arranged_route:
        relation = str((query_plan.get("time_scope") or {}).get("relation") or "").strip().lower()
        pathway_rules = {
            "scope": "static natal marriage-pathway comparison; no event timing",
            "question_time_relation": relation or "unspecified",
            "love_led_pathway": {
                "required_factors": ["marriage:H5", "marriage:H7", "marriage:D9"],
                "meaning": "romance or personal choice develops into committed partnership",
            },
            "family_mediated_pathway": {
                "required_factors": [
                    "marriage:H2", "marriage:H7", "marriage:H9", "marriage:H11", "marriage:D9",
                ],
                "meaning": "family, community or a formal introduction mediates the committed partnership",
            },
            "allowed_verdicts": [
                "love-led pathway is stronger",
                "family-mediated pathway is stronger",
                "mixed or hybrid pathway",
                "insufficient comparative evidence",
            ],
            "required_answer_order": [
                "direct comparative verdict",
                "love-led evidence",
                "family-mediated evidence",
                "D9 confirmation or qualification",
                "one question asking whether the reading matches how the marriage happened",
            ],
            "past_tense_rule": (
                "Because the question asks about an already-past marriage, describe what the chart suggests was "
                "more likely to have happened. Do not switch to future tense or ask about the user's current "
                "relationship status."
                if relation == "past"
                else "Match the tense of the user's question."
            ),
            "forbidden_moves": [
                "Do not answer only whether marriage is promised.",
                "Do not say historical data, dasha evidence or transit evidence is required.",
                "Do not mention a current or future dasha, transit, date, period or timing window.",
                "Do not use vague sudden-change or hidden-matter language unless supplied comparative evidence requires it.",
                "Do not ask whether the user is currently in a relationship or considering an arranged setup.",
                "Do not claim binary certainty; a mixed or hybrid pathway is valid when both sides are supported.",
                "Do not call a natal house active or activated; activation is reserved for timing routes.",
            ],
            "static_vocabulary": [
                "supports", "challenges", "has mixed tone", "connects", "contains", "receives an aspect", "confirms",
            ],
        }
        compact_policy["marriage_pathway_rules"] = pathway_rules
        compact_policy["instruction"] = (
            "Compare the love-led and family-mediated marriage pathways from the supplied D1/D9 evidence. "
            "Explain both pathways before supporting one or calling the result mixed. This is not a marriage-"
            "promise or historical-timing question. Follow marriage_pathway_rules exactly."
        )
        answer_spec["marriage_pathway_rules"] = pathway_rules
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        # The shared comparison fusion ranks dated option windows. This route
        # instead compares natal pathways, so its generic option verdict and
        # timing gaps must not compete with the D1/D9 pathway ledger.
        verdict["direction"] = "synthesize_from_marriage_pathway_comparison"
        verdict.pop("rationale", None)
        verdict.pop("modifiers", None)
        verdict.pop("missing_required_capabilities", None)
        verdict["scope"] = "static love-led versus family-mediated marriage-pathway comparison"
        result["verdict"] = verdict
    if bool(policy.get("live")) and spouse_meeting_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        meeting = normalized.get("spouse_meeting_context") if isinstance(normalized.get("spouse_meeting_context"), Mapping) else {}
        relation = str((query_plan.get("time_scope") or {}).get("relation") or "").strip().lower()
        meeting_rules = {
            "scope": "static natal probable meeting context; no timing",
            "question_time_relation": relation or "unspecified",
            "evidence_complete": bool(meeting.get("evidence_complete")),
            "primary_evidence": "evidence.spouse_meeting_context.primary_channel",
            "required_answer_order": [
                "one direct probable meeting context",
                "the seventh-lord natal-placement basis",
                "at most one concretely supported secondary channel",
                "D9 confirmation or qualification",
                "one question asking whether that context matches how they met",
            ],
            "forbidden_moves": [
                "Do not mention dasha, transit, activation, a planet-driven period, date or life phase.",
                "Do not infer work or duty from Saturn unless the supplied primary channel is House 6 or House 10.",
                "Do not infer friends or a shared circle unless supplied House 11 evidence supports it.",
                "Do not claim an exact venue or known historical fact from a one-chart probability.",
                "Do not turn meeting context into spouse personality or relationship quality.",
            ],
            "past_tense_rule": (
                "The user asks about an event that already happened. Use past tense and ask whether the probable "
                "context matches their actual meeting."
                if relation == "past"
                else "Match the tense of the user's question."
            ),
        }
        compact_policy["spouse_meeting_rules"] = meeting_rules
        answer_spec["spouse_meeting_rules"] = meeting_rules
        compact_policy["instruction"] = (
            "Answer only from the calculated spouse_meeting_context. Lead with its seventh-lord natal-placement "
            "channel and keep it probabilistic. Never substitute dasha timing, spouse personality or generic marriage promise."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static probable spouse-meeting channel from natal evidence"
        result["verdict"] = verdict
        if not meeting.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_meeting_story"
            compact_policy["instruction"] = (
                "The calculated spouse-meeting packet is incomplete. Do not invent work, friends, travel, family, "
                "an exact venue or any other meeting story. State that a reliable channel cannot be distinguished."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and spouse_profile_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        temperament = normalized.get("spouse_temperament_context") if isinstance(normalized.get("spouse_temperament_context"), Mapping) else {}
        temperament_rules = {
            "scope": "static five-layer spouse temperament; no timing",
            "evidence_complete": bool(temperament.get("evidence_complete")),
            "primary_evidence": "evidence.spouse_temperament_context.layers",
            "required_layers": [
                "seventh_house",
                "seventh_lord_rashi_nakshatra",
                "darakaraka_rashi_nakshatra",
                "venus_rashi_nakshatra",
                "d9_confirmation",
            ],
            "required_answer_order": [
                "direct synthesized temperament",
                "seventh house and seventh-lord contribution",
                "seventh-lord nakshatra refinement",
                "Darakaraka spouse archetype",
                "Venus relationship style",
                "D9 confirmation or qualification",
                "one question about which traits match the spouse",
            ],
            "forbidden_moves": [
                "Do not infer the whole personality from the seventh house or Mercury alone.",
                "Do not omit Darakaraka, seventh-lord nakshatra, Venus rashi/nakshatra or D9.",
                "Do not mention dasha, transit, activation, timing or current-period effects.",
                "Do not diagnose, assert hidden motives or describe fixed identity with certainty.",
            ],
        }
        compact_policy["spouse_temperament_rules"] = temperament_rules
        answer_spec["spouse_temperament_rules"] = temperament_rules
        compact_policy["instruction"] = (
            "Synthesize the supplied five spouse-temperament layers. Give each layer a distinct role and let D9 "
            "confirm or qualify the natal picture; no single house, planet, rashi or nakshatra may dominate the answer."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static five-layer spouse temperament synthesis"
        result["verdict"] = verdict
        if not temperament.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_spouse_temperament"
            compact_policy["missing_temperament_layers"] = list(temperament.get("missing_layers") or [])
            compact_policy["instruction"] = (
                "Required spouse-temperament layers are missing. Do not invent a personality profile from the seventh "
                "house alone. State which calculation layers are unavailable."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and spouse_appearance_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        appearance = normalized.get("spouse_appearance_context") if isinstance(normalized.get("spouse_appearance_context"), Mapping) else {}
        appearance_rules = {
            "scope": "spouse physical appearance and visual presence only; no temperament or timing",
            "evidence_complete": bool(appearance.get("evidence_complete")),
            "primary_evidence": "evidence.spouse_appearance_context.layers",
            "required_layers": [
                "seventh_house_sign",
                "seventh_lord_rashi_nakshatra",
                "darakaraka_rashi_nakshatra",
                "venus_rashi_nakshatra",
                "d9_confirmation",
            ],
            "required_answer_order": [
                "direct visual summary",
                "probable build and stature band",
                "face and visible expression",
                "style grooming and visual presence",
                "one or two strongest distinguishing visible markers",
                "native-chart probability disclosure",
            ],
            "forbidden_moves": [
                "Do not replace appearance with temperament or character.",
                "Do not discuss profession, location, compatibility or marriage timing.",
                "Do not infer exact height, exact measurements, exact skin colour, ethnicity, caste or nationality.",
                "Do not diagnose, sexualize or claim photographic certainty.",
                "Do not mention dasha, transit, activation or current periods.",
            ],
        }
        compact_policy["spouse_appearance_rules"] = appearance_rules
        answer_spec["spouse_appearance_rules"] = appearance_rules
        compact_policy["instruction"] = (
            "Answer the requested physical-appearance facet directly from the calculated spouse_appearance_context. "
            "Synthesize all five layers into bounded visual ranges and keep personality prose out of the answer."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static probable spouse appearance from native-chart symbolism"
        result["verdict"] = verdict
        if not appearance.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_spouse_appearance"
            compact_policy["missing_appearance_layers"] = list(appearance.get("missing_layers") or [])
            compact_policy["instruction"] = (
                "Required spouse-appearance layers are missing. Do not answer with personality traits or invent "
                "physical features; state which calculation layers are unavailable."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and spouse_location_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        location = normalized.get("spouse_location_context") if isinstance(normalized.get("spouse_location_context"), Mapping) else {}
        location_rules = {
            "scope": "static local-versus-different city, culture or geographical background; no timing",
            "evidence_complete": bool(location.get("evidence_complete")),
            "calculated_verdict": location.get("verdict"),
            "distance_score": location.get("distance_score"),
            "local_score": location.get("local_score"),
            "primary_evidence": [
                "evidence.spouse_location_context.distance_signals",
                "evidence.spouse_location_context.local_signals",
            ],
            "allowed_verdicts": [
                "different_city_culture_or_background_supported",
                "local_or_familiar_background_supported",
                "mixed_distance_and_local_signals",
                "insufficient_specific_distance_evidence",
            ],
            "required_answer_order": [
                "direct plain-language verdict",
                "strongest direct distance evidence if present",
                "strongest local or familiar-root evidence if present",
                "D9 confirmation or qualification",
                "one question asking whether this matches the known background",
            ],
            "forbidden_moves": [
                "Do not infer foreignness from Saturn, Virgo, a nakshatra or a planet's generic nature alone.",
                "Do not convert ordinary conjunctions into a different-city or cultural claim.",
                "Do not mention dasha, transit, activation or whether the result has manifested yet.",
                "Do not describe temperament, appearance, profession or relationship quality.",
                "Do not name a city, country, ethnicity, caste, religion or nationality not supplied by the user.",
            ],
        }
        compact_policy["spouse_location_rules"] = location_rules
        answer_spec["spouse_location_rules"] = location_rules
        compact_policy["instruction"] = (
            "Use the calculated local-versus-distance verdict exactly. Explain only direct spouse links to houses 3, "
            "4, 9 or 12 and explicit Rahu linkage; weak sign modality cannot decide the answer."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static spouse geographical or cultural-background tendency"
        verdict["spouse_location_verdict"] = location.get("verdict")
        result["verdict"] = verdict
        if not location.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_spouse_location"
            compact_policy["missing_location_layers"] = list(location.get("missing_layers") or [])
            compact_policy["instruction"] = (
                "Required spouse-location layers are missing. Do not invent a foreign, different-city, cultural or "
                "local-background story; state which calculation layers are unavailable."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and marriage_remedy_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        blueprint = normalized.get("remedy_blueprint") if isinstance(normalized.get("remedy_blueprint"), Mapping) else {}
        selection_mode = str(blueprint.get("selection_mode") or "ranked_three")
        top = blueprint.get("top_recommendation") if isinstance(blueprint.get("top_recommendation"), Mapping) else {}
        remedy_rules = {
            "scope": "calculated marriage remedy delivery; no fresh diagnosis or timing",
            "selection_mode": selection_mode,
            "required_count": 1 if selection_mode == "single_top" else 3,
            "top_recommendation": dict(top),
            "primary_evidence": "evidence.remedy_blueprint.ranked_remedies",
            "required_fields_per_remedy": ["action", "frequency", "astrological_reason"],
            "required_answer_order": [
                "name the top calculated remedy immediately",
                "state the exact action",
                "state frequency or duration",
                "state the calculated chart reason",
                "one concise practicality caution",
            ],
            "forbidden_moves": [
                "Do not answer with another marital-conflict diagnosis.",
                "Do not mention current dasha, transit, activation, manifestation or forecast timing.",
                "Do not replace the calculated remedy with generic communication advice.",
                "Do not ask what the conflict is about before delivering the available top remedy.",
                "Do not invent a mantra, gemstone, charity or behavioral action absent from ranked_remedies.",
                "Do not guarantee reconciliation or conflict resolution.",
            ],
        }
        compact_policy["marriage_remedy_rules"] = remedy_rules
        answer_spec["marriage_remedy_rules"] = remedy_rules
        compact_policy["instruction"] = (
            "Deliver the calculated remedy selection directly from remedy_blueprint.ranked_remedies. If the user "
            "asks which remedy is most relevant, give exactly top_recommendation with action, frequency and reason."
        )
        if not blueprint or not top:
            compact_policy["claim_permission"] = "no_calculated_marriage_remedy"
            compact_policy["instruction"] = (
                "The calculated marriage remedy blueprint or its ranked top recommendation is unavailable. Do not "
                "improvise a remedy or substitute another conflict diagnosis."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and comparison_mode and not missing:
        verdict = dict(result.get("verdict") or {})
        rationale = verdict.get("rationale") if isinstance(verdict.get("rationale"), Mapping) else {}
        favored = str(rationale.get("favored_option") or "")
        option_windows: list[dict[str, Any]] = []
        for option in rationale.get("options") or []:
            if not isinstance(option, Mapping):
                continue
            window = option.get("best_window") if isinstance(option.get("best_window"), Mapping) else {}
            if not window:
                continue
            row = dict(window)
            row["option"] = str(option.get("event_profile") or option.get("label") or "")
            option_windows.append(row)
        if option_windows:
            option_windows.sort(key=lambda row: (str(row.get("option")) != favored, str(row.get("start") or "")))
            verdict["ranked_windows"] = option_windows
            verdict["option_window_rule"] = (
                "Each ranked window is labeled with its owning option. The first row belongs to the favored option; "
                "never attach another option's window to it."
            )
            result["verdict"] = verdict
    if bool(policy.get("live")) and comparison_mode and missing:
        compact_policy["claim_permission"] = "no_option_winner"
        compact_policy["fallback_to_deeper_mode"] = True
        compact_policy["instruction"] = (
            "Required option-comparison factors are missing. Do not favor, recommend, or call either option "
            "more likely. In the same language and script as the user, briefly say this needs a deeper Standard "
            "or Premium reading. Do not name missing factors or ask an unrelated follow-up."
        )
        verdict = dict(result.get("verdict") or {})
        verdict["direction"] = "insufficient_option_evidence"
        verdict["missing_required_capabilities"] = list(dict.fromkeys(
            list(verdict.get("missing_required_capabilities") or []) + missing
        ))
        result["verdict"] = verdict
        answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and time_bound_mode and timing_missing:
        compact_policy["claim_permission"] = "directional_only_no_timing"
        compact_policy["timing_missing_factors"] = timing_missing
        compact_policy["instruction"] = (
            "Required timing evidence is missing. Give only a supported directional reading; "
            "do not name, rank, or imply any date, month, year, period, or timing window. "
            "State the evidence limitation plainly."
        )
        verdict = dict(result.get("verdict") or {})
        verdict["direction"] = "insufficient_timing_evidence"
        verdict["ranked_windows"] = []
        verdict["missing_required_capabilities"] = list(dict.fromkeys(
            list(verdict.get("missing_required_capabilities") or []) + timing_missing
        ))
        result["verdict"] = verdict
        event_rules = dict(answer_spec.get("event_rules") or {})
        event_rules["allowed_timing_windows"] = []
        event_rules["required_material_windows"] = []
        event_rules["window_answer_rule"] = "No timing claim is permitted because required graph evidence is missing."
        answer_spec["event_rules"] = event_rules
        answer_spec["limitation_instruction"] = compact_policy["instruction"]
    answer_spec["knowledge_graph_policy"] = compact_policy
    result["answer_spec"] = answer_spec

    verification = dict(result.get("verification") or {})
    verification["knowledge_graph"] = {
        "live": bool(policy.get("live")),
        "domain": policy.get("domain"),
        "runtime_key": policy.get("runtime_key"),
        "mode_match": policy.get("mode_match"),
        "evidence_status": policy.get("evidence_status"),
    }
    result["verification"] = verification

    route = policy.get("route")
    if isinstance(route, Mapping):
        route = dict(route)
        route["domain"] = policy.get("domain")
        derivation = dict(result.get("user_derivation") or {})
        graph_routes = [
            row for row in list(derivation.get("knowledge_graph_routes") or [])
            if not isinstance(row, Mapping) or row.get("domain") != policy.get("domain")
        ]
        graph_routes.append(route)
        derivation["knowledge_graph_routes"] = graph_routes
        derivation[f"{policy.get('domain')}_graph_route"] = route
        result["user_derivation"] = derivation
    return result


def enforce_live_graph_answer(
    answer: str,
    packet: Mapping[str, Any] | None,
    *,
    language: str = "english",
) -> str:
    """Fail closed when the live route denies timing specificity.

    This is deliberately deterministic: unsupported dates must not reach the
    user even if the single composer call ignores its contract.
    """
    clean_answer = str(answer or "")
    # In an MD-AD-PD chain, the third planet is the sub-sub-period lord.
    # Correct this common wording slip before any answer reaches the client.
    chain_pattern = re.compile(
        r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s*[-–—]\s*"
        r"(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s*[-–—]\s*"
        r"(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b",
        re.IGNORECASE,
    )
    for match in chain_pattern.finditer(clean_answer):
        pd_planet = re.escape(match.group(3))
        clean_answer = re.sub(
            rf"\b({pd_planet})(\s*,?\s+as\s+(?:the\s+)?)sub-period lord\b",
            r"\1\2sub-sub-period lord",
            clean_answer,
            flags=re.IGNORECASE,
        )
    packet = packet if isinstance(packet, Mapping) else {}
    spec = packet.get("answer_spec") if isinstance(packet.get("answer_spec"), Mapping) else {}
    policy = spec.get("knowledge_graph_policy") if isinstance(spec.get("knowledge_graph_policy"), Mapping) else {}
    children_boundary = str(policy.get("claim_permission") or "")
    if children_boundary == "children_fetal_sex_refusal":
        return (
            "I can’t predict or imply whether a baby will be a son or daughter. I can still help with the chart’s "
            "broader parenthood themes or supportive periods without making a fetal-sex claim."
        )
    if children_boundary == "children_medical_handoff":
        return (
            "A birth chart cannot determine whether a pregnancy is healthy, diagnose fertility, assess a symptom, "
            "or predict pregnancy loss. Please use your obstetrician or fertility specialist for that decision; "
            "seek urgent medical care for severe pain, heavy bleeding, fainting, breathing difficulty, or any symptom "
            "your clinician has told you is urgent. Once medical safety is covered, I can discuss only the chart’s "
            "non-medical parenthood themes."
        )
    if children_boundary == "children_two_chart_handoff":
        return (
            "A joint parenthood question needs both resolved birth charts. Please open Partnership Analysis and "
            "select both people; one chart cannot reliably represent the other partner’s parenthood factors."
        )
    if children_boundary == "children_child_chart_handoff":
        return (
            "Your chart can describe your experience of parenting and your relationship pattern with children, but "
            "it cannot reliably give the child’s personality, education, career, marriage, or future. Those personal "
            "questions need the child’s own chart and appropriate consent. A chart—even the child’s own chart—cannot "
            "determine whether the child is healthy; health concerns belong with a qualified clinician."
        )
    if children_boundary == "children_muhurat_handoff":
        return (
            "Choosing among treatment, ceremony, naming, or planned-delivery dates requires the dedicated Muhurat "
            "flow with actual Panchang conditions. A natal Children reading alone cannot rank those dates."
        )
    if children_boundary == "children_legal_handoff":
        return (
            "A chart cannot guarantee custody or a court outcome. This needs the Legal flow and advice from a "
            "qualified lawyer; the Children graph can only discuss your parent-child relationship pattern."
        )
    home_key = str(policy.get("runtime_key") or "")
    if home_key == "property_dispute_handoff":
        return "A property dispute needs the dedicated Legal, Competition and Conflict analysis. I can discuss only the non-legal home/property pattern here; I cannot predict a court win, settlement, title outcome, or another party’s conduct."
    if home_key == "muhurat_handoff":
        return "Choosing a property-registration, possession, construction-start, griha-pravesh, or vehicle-purchase date requires the dedicated Muhurat flow with Panchang and location details. A natal Property reading cannot rank exact dates."
    if home_key == "foreign_handoff":
        return "Foreign relocation, immigration and permanent-settlement questions need the dedicated Foreign Life analysis. The Home and Property graph can discuss domestic stability, but should not turn that into a settlement claim."
    if home_key == "inheritance_handoff":
        return "Inheritance, title ownership and estate entitlement belong to the Wealth and Inheritance analysis. A Home and Property reading cannot determine ownership or legal entitlement."
    if home_key == "vastu_handoff":
        return "A Vastu assessment needs the home’s actual plan, orientation, entrance and room placement. A birth-chart Property reading cannot certify a building as Vastu compliant."
    if home_key == "property_business_handoff":
        return "A real-estate business question needs the Career and Wealth analysis, including business aptitude and financial-risk evidence. The Home and Property graph only assesses personal home and property themes."
    foreign_boundary = str(policy.get("claim_permission") or "")
    if foreign_boundary == "foreign_location_handoff":
        return "An open-ended best-country or best-city recommendation needs the dedicated Location flow with an explicit scope and comparable places. This chart route can compare named options, but it should not invent a destination from the whole world."
    if foreign_boundary == "foreign_legal_handoff":
        return "A birth chart cannot determine legal eligibility or guarantee a visa or immigration approval. Please verify the current rules and your documents with the relevant immigration authority or a qualified adviser; I can discuss only the chart's non-legal timing and relocation themes."
    if foreign_boundary == "foreign_muhurat_handoff":
        return "Choosing an exact departure, filing or relocation date requires the dedicated Muhurat flow with the actual location, timezone and Panchang conditions. A natal Foreign Life reading alone cannot rank exact dates."
    if foreign_boundary == "foreign_safety_handoff":
        return "A birth chart cannot guarantee that a trip will be safe or replace official travel, weather, health or security guidance. Use current advisories and practical precautions; I can discuss only non-safety travel themes."
    if foreign_boundary == "foreign_other_person_handoff":
        return "Your chart cannot reliably determine another adult's travel, residence or settlement outcome. That question needs their own birth chart and consent; this reading can only discuss how their move may affect your experience."
    wealth_rules = (
        policy.get("wealth_answer_rules")
        if isinstance(policy.get("wealth_answer_rules"), Mapping)
        else {}
    )
    if str(wealth_rules.get("runtime_key") or "") == "intraday_trading":
        session = (
            wealth_rules.get("intraday_trading_session")
            if isinstance(wealth_rules.get("intraday_trading_session"), Mapping)
            else {}
        )
        if session:
            participation = str(session.get("participation") or "cautious")
            market_open = bool(session.get("market_open"))
            windows = [
                row for row in list(session.get("windows") or [])
                if isinstance(row, Mapping) and row.get("start") and row.get("end")
            ]

            # Session times are calculated facts. The composer may explain the
            # verdict, but it must not omit, rename, or invent a Choghadiya
            # period. Remove its timing prose and render the ledger verbatim.
            timing_names = {
                "amrita", "kala", "labha", "roga", "shubha", "udvega", "chara",
            }
            timing_name_pattern = re.compile(
                r"\b(?:" + "|".join(sorted(timing_names)) + r")\b",
                re.IGNORECASE,
            )
            clock_pattern = re.compile(
                r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?:\s*[AaPp]\.?[Mm]\.?)?\b"
            )
            retained_sentences = []
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", clean_answer):
                sentence = sentence.strip()
                if not sentence:
                    continue
                if timing_name_pattern.search(sentence) or clock_pattern.search(sentence):
                    continue
                if re.search(
                    r"\b(?:D1|D2|D5|Hora|Panchamsha|Indu Lagna|natal chart|birth chart)\b",
                    sentence,
                    re.IGNORECASE,
                ):
                    continue
                if re.search(
                    r"\b(?:Sun|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b",
                    sentence,
                    re.IGNORECASE,
                ):
                    continue
                if re.search(
                    r"\b(?:this combination|these placements|this alignment)\b",
                    sentence,
                    re.IGNORECASE,
                ):
                    continue
                if re.search(r"\bmateriali[sz]ation\b", sentence, re.IGNORECASE):
                    continue
                # KP availability is not a positive intraday materialization
                # verdict. Do not let the writer turn it into one.
                if re.search(r"\bKP\b", sentence, re.IGNORECASE) and re.search(
                    r"\b(?:strong|support(?:ive|ed)?|materiali[sz]ation)\b",
                    sentence,
                    re.IGNORECASE,
                ):
                    continue
                retained_sentences.append(sentence)
            practical_sentences = [
                sentence for sentence in retained_sentences
                if sentence.endswith("?")
                or re.search(
                    r"\b(?:risk|disciplin|overtrad|stop(?:-loss)?|capital|profit|loss|plan|"
                    r"impuls|restraint|precision|position size)\w*\b",
                    sentence,
                    re.IGNORECASE,
                )
            ]
            question_sentence = next(
                (sentence for sentence in reversed(practical_sentences) if sentence.endswith("?")),
                "",
            )
            explanation_rows = [
                sentence for sentence in practical_sentences if not sentence.endswith("?")
            ][:2]
            if question_sentence:
                explanation_rows.append(question_sentence)
            explanation = " ".join(explanation_rows).strip()

            if not bool(session.get("available", True)):
                error = session.get("calculation_error") if isinstance(session.get("calculation_error"), Mapping) else {}
                reason = session.get("reason") or error.get("message") or "The required session evidence could not be calculated."
                return (
                    "**Today's session indication: Calculation unavailable**\n\n"
                    f"{reason} No trading indication or time window has been inferred."
                )
            if not market_open:
                return (
                    "**Today's session indication: Market closed**\n\n"
                    f"{((session.get('market') or {}).get('reason') if isinstance(session.get('market'), Mapping) else '') or 'The configured cash-market session is closed on this date.'} "
                    "No intraday entry windows are provided."
                )

            decision = {
                "sit_out": "Sit out",
                "reduce_size": "Use reduced position size",
                "participate": "Participation is permitted with normal risk controls",
                "cautious": "Proceed cautiously",
            }.get(participation, "Proceed cautiously")
            lines = [
                f"**Today's session indication: {decision}**",
                "",
                "**Why today's result**",
            ]
            period = session.get("period_permission") if isinstance(session.get("period_permission"), Mapping) else {}
            daily = session.get("daily_climate") if isinstance(session.get("daily_climate"), Mapping) else {}
            active = [row for row in list(period.get("active_periods") or []) if isinstance(row, Mapping)]
            if active:
                lines.append(
                    f"- Period permission is **{period.get('status', 'mixed')}**: "
                    + " / ".join(str(row.get("planet")) for row in active)
                    + f" activate houses {', '.join(str(x) for x in period.get('activated_houses') or [])}."
                )
            tara = daily.get("tara_bala") if isinstance(daily.get("tara_bala"), Mapping) else {}
            chandra = daily.get("chandra_bala") if isinstance(daily.get("chandra_bala"), Mapping) else {}
            if not tara and isinstance(session.get("tara_bala"), Mapping):
                tara = session.get("tara_bala")
            if not chandra and isinstance(session.get("chandra_bala"), Mapping):
                chandra = session.get("chandra_bala")
            if tara:
                if daily:
                    lines.append(f"- Today's Tara is {tara.get('name')}; the Moon is {chandra.get('house_from_natal_moon')} from your natal Moon.")
                else:
                    tara_quality = str(tara.get("quality") or "mixed").lower()
                    tara_plain = "supportive" if tara_quality in {"good", "excellent"} else "challenging" if tara_quality in {"danger", "obstacle", "critical"} else "mixed"
                    lines.append(f"- Today's lunar-star relationship is {tara_plain} ({tara.get('name') or 'Tara Bala'} Tara).")
            for row in list(daily.get("supports") or [])[:3]:
                if isinstance(row, Mapping): lines.append(f"- Support: {row.get('reason')}")
            for row in list(daily.get("obstructions") or [])[:4]:
                if isinstance(row, Mapping): lines.append(f"- Caution: {row.get('reason')}")
            lines.extend([
                "- D1 and D2 set the background capacity; they do not decide today's signal.",
                "",
                "**Calculated market-hour Muhurta windows**",
            ])
            for row in windows:
                window_verdict = row.get("verdict")
                if not window_verdict:
                    legacy_quality = str(row.get("quality") or "").lower()
                    window_verdict = "supportive" if legacy_quality.startswith("good") else ("avoid" if legacy_quality.startswith("bad") else "neutral")
                choghadiya_name = row.get("choghadiya") or row.get("name") or "Unknown"
                lines.append(
                    f"- {row.get('start')}–{row.get('end')} — **{window_verdict}** · "
                    f"{row.get('hora_lord') or 'Unknown'} Hora · {choghadiya_name} Choghadiya · "
                    f"Ascendant sign {int(row.get('ascendant_sign', 0)) + 1}"
                )
            lines.extend([
                "",
                "Each window combines planetary Hora, Choghadiya, the changing ascendant, 2nd/5th/11th house lords, active dasha lords and Panchanga. It describes your execution climate, not market direction.",
            ])
            if explanation:
                lines.extend(["", explanation])
            clean_answer = "\n".join(lines)
    nakshatra_rules = (
        policy.get("nakshatra_answer_rules")
        if isinstance(policy.get("nakshatra_answer_rules"), Mapping) else {}
    )
    if policy.get("domain") == "nakshatra" and nakshatra_rules:
        carriers = [
            row for row in (
                list(nakshatra_rules.get("carriers") or [])
                + list(nakshatra_rules.get("timing_carriers") or [])
                + list(nakshatra_rules.get("current_transit_nakshatras") or [])
            ) if isinstance(row, Mapping)
        ]
        allowed_planets = {
            str(value).lower()
            for row in carriers
            for value in (row.get("carrier"), row.get("planet"), row.get("nakshatra_lord"))
            if value and str(value) != "Ascendant"
        }
        allowed_stars = {str(row.get("nakshatra") or "").lower() for row in carriers if row.get("nakshatra")}
        all_stars = (
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
            "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
            "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
            "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
        )
        planet_pattern = re.compile(r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b", re.IGNORECASE)
        star_pattern = re.compile(r"\b(" + "|".join(re.escape(value) for value in all_stars) + r")\b", re.IGNORECASE)
        timing_pattern = re.compile(r"\b(dasha|mahadasha|antardasha|pratyantardasha|transit|active period|\d{4})\b", re.IGNORECASE)
        runtime_key = str(policy.get("runtime_key") or "")
        retained = []
        for sentence in re.split(r"(?<=[.!?])\s+", clean_answer):
            named_planets = {match.group(1).lower() for match in planet_pattern.finditer(sentence)}
            named_stars = {match.group(1).lower() for match in star_pattern.finditer(sentence)}
            if named_planets - allowed_planets:
                continue
            if named_stars - allowed_stars:
                continue
            if runtime_key != "nakshatra_timing" and timing_pattern.search(sentence):
                continue
            if runtime_key != "nakshatra_remedy" and re.search(r"\b(remedy|mantra|chant|donate|puja)\b", sentence, re.IGNORECASE):
                continue
            if runtime_key != "special_nakshatra_conditions" and re.search(r"\b(gandamoola|ganda\s*mool|gandanta|dosha)\b", sentence, re.IGNORECASE):
                continue
            retained.append(sentence.strip())
        if retained:
            clean_answer = "\n\n".join(retained)
    foreign_rules = (
        policy.get("foreign_answer_rules")
        if isinstance(policy.get("foreign_answer_rules"), Mapping)
        else {}
    )
    if policy.get("domain") == "foreign_life" and foreign_rules:
        # The Foreign Life writer is allowed to interpret only the calculated
        # route ledger. Drop a sentence rather than cosmetically replacing a
        # wrong sign: a sentence that says "Mercury for Virgo ascendant" still
        # contains a false lordship after Virgo is changed to Cancer.
        zodiac_pattern = re.compile(
            r"\b(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)\b",
            re.IGNORECASE,
        )
        expected_ascendant = str(foreign_rules.get("native_ascendant") or "").strip().lower()
        allowed_special = {
            str(value).strip().lower()
            for value in foreign_rules.get("allowed_special_claim_terms") or []
        }
        unsupported_special_pattern = re.compile(
            r"\b(Yogi|Avayogi|Gandanta|Tithi[- ]Shunya|Dagdha)\b",
            re.IGNORECASE,
        )
        static_timing_pattern = re.compile(
            r"\b(dasha|mahadasha|antardasha|pratyantardasha|transit|currently active|active period|"
            r"current\b.{0,80}\bperiod|"
            r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s*[-–—]\s*"
            r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)(?:\s*[-–—]\s*"
            r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu))?)\b",
            re.IGNORECASE,
        )
        planet_pattern = re.compile(
            r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b",
            re.IGNORECASE,
        )
        explicit_planet_fact_pattern = re.compile(
            r"\bD(?:1|3|4|9|10|12)\b.{0,100}\b(?:H(?:ouse)?\s*\d+|\d+(?:st|nd|rd|th)\s+house)\b"
            r"|\b(?:H(?:ouse)?\s*\d+|\d+(?:st|nd|rd|th)\s+house)\b.{0,100}\bD(?:1|3|4|9|10|12)\b",
            re.IGNORECASE,
        )
        invented_planet_meaning_pattern = re.compile(
            r"\b(?:hunger|pull|urge)\s+(?:toward|towards|for)\s+(?:the\s+)?(?:foreign|unfamiliar|distant)"
            r"|\b(?:confidence|recognition|authority)\b",
            re.IGNORECASE,
        )
        fact_contract = (
            foreign_rules.get("fact_contract")
            if isinstance(foreign_rules.get("fact_contract"), Mapping) else {}
        )
        route_synthesis = (
            foreign_rules.get("route_synthesis")
            if isinstance(foreign_rules.get("route_synthesis"), Mapping) else {}
        )
        planet_directions = {
            str(row.get("planet") or "").lower():str(row.get("net_direction") or "")
            for row in route_synthesis.get("planet_contributions") or []
            if isinstance(row, Mapping) and row.get("planet")
        }
        visible_rules = spec.get("visible_astrology") if isinstance(spec.get("visible_astrology"), Mapping) else {}
        technical_answer = bool(visible_rules.get("technical_detail_allowed"))
        excluded_direct_houses = {
            int(value) for value in fact_contract.get("excluded_direct_houses") or []
            if str(value).isdigit()
        }
        fact_contract_violated = False
        retained_sentences = []
        for sentence in re.split(r"(?<=[.!?])\s+", clean_answer):
            if not sentence.strip():
                continue
            if re.search(r"\bascendant\b", sentence, re.IGNORECASE) and expected_ascendant:
                named_signs = {match.group(1).lower() for match in zodiac_pattern.finditer(sentence)}
                if named_signs and (expected_ascendant not in named_signs or any(
                    sign != expected_ascendant for sign in named_signs
                )):
                    continue
            unsupported_terms = {
                match.group(1).lower().replace(" ", "-")
                for match in unsupported_special_pattern.finditer(sentence)
            }
            if any(term not in allowed_special for term in unsupported_terms):
                continue
            if not foreign_rules.get("timing_route") and static_timing_pattern.search(sentence):
                continue
            if not foreign_rules.get("timing_route") and planet_pattern.search(sentence):
                named_planets={match.group(1).lower() for match in planet_pattern.finditer(sentence)}
                missing_planets={planet for planet in named_planets if planet not in planet_directions}
                positive_claim=bool(re.search(r"\b(?:support|supportive|favour|favor|help|strengthen|promise)\w*\b",sentence,re.IGNORECASE))
                unqualified_mixed=any(
                    planet_directions.get(planet)=="mixed" for planet in named_planets
                ) and positive_claim and not re.search(r"\b(?:mixed|qualified|but|however|also|while)\b",sentence,re.IGNORECASE)
                direction_conflict=any(
                    planet_directions.get(planet)=="challenging" for planet in named_planets
                ) and positive_claim
                # Technical prose must expose the exact chart/house binding.
                # Simple prose may translate it, but the planet must exist in
                # the route ledger and its direction cannot be reversed.
                if (
                    invented_planet_meaning_pattern.search(sentence)
                    or missing_planets
                    or direction_conflict
                    or unqualified_mixed
                    or (technical_answer and not explicit_planet_fact_pattern.search(sentence))
                ):
                    fact_contract_violated = True
                    continue
            if excluded_direct_houses and any(
                re.search(rf"\b(?:H(?:ouse)?\s*{house}|{house}(?:st|nd|rd|th)\s+house)\b", sentence, re.IGNORECASE)
                for house in excluded_direct_houses
            ):
                fact_contract_violated = True
                continue
            retained_sentences.append(sentence)
        filtered_answer = " ".join(retained_sentences).strip()
        if filtered_answer:
            clean_answer = filtered_answer
        if foreign_rules.get("timing_route"):
            timing = foreign_rules.get("timing_synthesis") if isinstance(foreign_rules.get("timing_synthesis"), Mapping) else {}
            next_window = timing.get("next_window") if isinstance(timing.get("next_window"), Mapping) else {}
            if next_window.get("start") and next_window.get("end"):
                def format_foreign_date(value: Any) -> str:
                    try:
                        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                    except (TypeError, ValueError):
                        return str(value or "")

                start_text = format_foreign_date(next_window.get("start"))
                end_text = format_foreign_date(next_window.get("end"))
                expected_year = str(next_window.get("start") or "")[:4]
                start_month = start_text.split()[1] if len(start_text.split()) >= 2 else ""
                end_month = end_text.split()[1] if len(end_text.split()) >= 2 else ""
                names_window = bool(
                    expected_year
                    and expected_year in clean_answer
                    and start_month.lower() in clean_answer.lower()
                    and end_month.lower() in clean_answer.lower()
                )
                evades_timing = bool(re.search(
                    r"\b(?:no (?:clear|specific|dated) (?:window|timing)|cannot (?:give|identify)|"
                    r"doesn['’]?t yet show (?:the )?(?:clear|dated)|green light not fully)\b",
                    clean_answer,
                    re.IGNORECASE,
                ))
                if not names_window or evades_timing:
                    labels = {
                        "short_travel_timing": "short-distance travel",
                        "long_travel_timing": "long-distance travel",
                        "retrospective_travel": "past travel",
                        "domestic_relocation_timing": "domestic relocation",
                        "foreign_travel_timing": "foreign travel",
                        "foreign_residence_timing": "foreign residence",
                        "settlement_timing": "permanent settlement",
                        "visa_timing": "visa-related progress",
                        "return_home_timing": "returning home",
                    }
                    event_label = labels.get(str(foreign_rules.get("runtime_key") or ""), "the requested foreign-life event")
                    kp = timing.get("kp_fructification") if isinstance(timing.get("kp_fructification"), Mapping) else {}
                    conditional = str(kp.get("verdict") or "").lower() != "supported"
                    peak_rows = next_window.get("transit_confirmation") if isinstance(next_window.get("transit_confirmation"), list) else []
                    peak = peak_rows[0] if peak_rows and isinstance(peak_rows[0], Mapping) else {}
                    peak_text = ""
                    if peak.get("start") and peak.get("end"):
                        peak_text = (
                            f" The sharpest transit concentration inside it is {format_foreign_date(peak.get('start'))} "
                            f"to {format_foreign_date(peak.get('end'))}."
                        )
                    technical = spec.get("visible_astrology") if isinstance(spec.get("visible_astrology"), Mapping) else {}
                    chain = "–".join(
                        str(next_window.get(key) or "")
                        for key in ("mahadasha", "antardasha", "pratyantardasha")
                        if next_window.get(key)
                    )
                    houses = ", ".join(f"H{value}" for value in next_window.get("activated_focus_houses") or [])
                    if technical.get("technical_detail_allowed") and chain:
                        mechanism = f" Technically, the {chain} MD–AD–PD chain activates {houses or 'the route houses'} with dated transit reinforcement."
                    else:
                        mechanism = " The dasha and transit calculations converge most strongly in that period."
                    qualification = (
                        " This is the strongest conditional window, not a confirmed departure prediction, because the KP cusp test does not fully support fructification."
                        if conditional else
                        " This is the next fully supported calculated window, though it is not a guaranteed real-world outcome."
                    )
                    clean_answer = (
                        f"The strongest calculated window for {event_label} is {start_text} to {end_text}."
                        f"{peak_text}{qualification}{mechanism} What concrete opportunity, application, or deadline are you working toward?"
                    )
    if policy.get("fallback_to_deeper_mode"):
        return _deeper_mode_fallback(language)
    if policy.get("domain") == "education":
        education_rules = (
            policy.get("education_answer_rules")
            if isinstance(policy.get("education_answer_rules"), Mapping)
            else {}
        )
        route_synthesis = (
            education_rules.get("route_synthesis")
            if isinstance(education_rules.get("route_synthesis"), Mapping)
            else {}
        )
        compound = (
            route_synthesis.get("compound_part_synthesis")
            if isinstance(route_synthesis.get("compound_part_synthesis"), Mapping)
            else {}
        )
        comparison = (
            compound.get("course_comparison")
            if isinstance(compound.get("course_comparison"), Mapping)
            else {}
        )
        option_rows = [
            row for row in comparison.get("options") or []
            if isinstance(row, Mapping) and row.get("option")
        ]
        timing_windows = [
            row for row in education_rules.get("timing_windows") or []
            if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
        ]
        if len(option_rows) >= 2:
            visible = spec.get("visible_astrology") if isinstance(spec.get("visible_astrology"), Mapping) else {}
            # Older callers did not carry a presentation contract and used
            # the technical renderer. An explicit False is the Simple-mode
            # signal and must never be treated like a missing value.
            technical_mode = (
                bool(visible.get("technical_detail_allowed"))
                if "technical_detail_allowed" in visible
                else True
            )
            lower_answer = clean_answer.lower()
            names_all_options = all(
                str(row.get("option") or "").lower() in lower_answer
                for row in option_rows
            )
            has_concrete_chart_reason = bool(
                re.search(r"\bD1\b", clean_answer, re.IGNORECASE)
                and re.search(r"\bD24\b", clean_answer, re.IGNORECASE)
                and re.search(r"\b(?:H|house\s*)\d{1,2}\b", clean_answer, re.IGNORECASE)
            )
            timing_verdict = str(route_synthesis.get("timing_verdict") or "")
            expected_year = str((timing_windows[0] if timing_windows else {}).get("start") or "")[:4]
            names_timing = bool(
                timing_verdict != "supportive_windows_found"
                or (expected_year and expected_year in clean_answer)
            )
            exposes_internal_scoring = bool(
                re.search(r"\b(?:score|scores|margin)\b", clean_answer, re.IGNORECASE)
            )
            if technical_mode or exposes_internal_scoring or not (
                names_all_options and has_concrete_chart_reason and names_timing
            ):
                ranked = [row for row in comparison.get("ranked_options") or [] if isinstance(row, Mapping)]
                direction = str(comparison.get("direction") or "")
                if direction == "clear_lead" and ranked:
                    opening = (
                        f"The chart comparison favors {ranked[0].get('option')} over "
                        f"{ranked[1].get('option')} because its relevant D1–D24 combination repeats more clearly."
                        if technical_mode
                        else
                        f"The chart leans toward {ranked[0].get('option')} over "
                        f"{ranked[1].get('option')}, although practical eligibility and genuine interest still matter."
                    )
                else:
                    opening = (
                        f"The chart supports both {option_rows[0].get('option')} and "
                        f"{option_rows[1].get('option')} through different combinations, but it does not establish "
                        "a decisive astrological winner between them."
                    )
                reasons = []
                for row in option_rows[:2]:
                    reasoning = row.get("technical_reasoning") if isinstance(row.get("technical_reasoning"), Mapping) else {}
                    fact_rows = [
                        value for value in reasoning.get("decisive_facts") or []
                        if isinstance(value, Mapping) and value.get("fact")
                    ]
                    facts = [str(value.get("fact") or "").replace("_", " ") for value in fact_rows[:3]]
                    if not facts:
                        seen_facts: set[str] = set()
                        for trait in row.get("trait_results") or []:
                            if not isinstance(trait, Mapping):
                                continue
                            for carrier in trait.get("carriers") or []:
                                if not isinstance(carrier, Mapping):
                                    continue
                                for fact in carrier.get("support") or []:
                                    clean_fact = str(fact or "").replace("_", " ")
                                    if clean_fact and clean_fact not in seen_facts:
                                        facts.append(clean_fact)
                                        seen_facts.add(clean_fact)
                                    if len(facts) >= 3:
                                        break
                                if len(facts) >= 3:
                                    break
                            if len(facts) >= 3:
                                break
                    labels = [str(value) for value in row.get("demand_labels") or [] if str(value)]
                    if not labels:
                        labels = [
                            str(value).replace("_", " ")
                            for value in row.get("demand_traits") or [] if str(value)
                        ]
                    demands = ", ".join(labels)
                    combination_rule = str(reasoning.get("combination_rule") or "").strip()
                    planets = list(dict.fromkeys(
                        str(value.get("planet") or "").strip()
                        for value in fact_rows
                        if str(value.get("planet") or "").strip()
                    ))
                    if facts and technical_mode:
                        reasons.append(
                            f"For {row.get('option')}, I tested {demands or 'its actual study demands'}, not a "
                            f"single planet. {'; '.join(facts)}. {combination_rule}"
                        )
                    elif planets:
                        if len(planets) == 1:
                            planet_text = planets[0]
                        else:
                            planet_text = f"{', '.join(planets[:-1])} and {planets[-1]}"
                        reason = (
                            f"For {row.get('option')}, {planet_text} work together around "
                            f"{demands or 'the course’s main learning demands'}. This is a combined pattern, "
                            "not a conclusion drawn from one planet."
                        )
                        if reasoning.get("moon_standalone_forbidden"):
                            reason += (
                                " The Moon can add a caring or receptive quality, but it is not being used by "
                                "itself as proof of a medical path."
                            )
                        reasons.append(reason)
                    else:
                        reasons.append(
                            f"For {row.get('option')}, the option-specific evidence is incomplete, so a preference "
                            "should not be invented."
                        )
                if timing_verdict == "supportive_windows_found" and timing_windows:
                    window = timing_windows[0]
                    timing_sentence = (
                        f"Separately, the next calculated admission-support window runs from "
                        f"{str(window.get('start') or '')[:10]} to {str(window.get('end') or '')[:10]}. "
                        "It is a supportive application/admission period, not a guaranteed seat."
                    )
                elif timing_verdict:
                    timing_sentence = (
                        f"Separately, the admission timing result is {timing_verdict.replace('_', ' ')}; "
                        "no date should be invented beyond that calculated result."
                    )
                else:
                    timing_sentence = "The admission-timing part has no calculated verdict, so no year should be invented."
                clean_answer = " ".join([
                    opening,
                    *reasons,
                    timing_sentence,
                    "Use entrance eligibility and your actual subject performance to break an astrologically close "
                    "result. Which entrance cycle are you preparing for?",
                ])
    if policy.get("claim_permission") == "no_specific_meeting_story":
        if str(language or "").lower().startswith("hi"):
            return (
                "उपलब्ध जन्म-कुंडली साक्ष्य यह विश्वसनीय रूप से अलग नहीं करते कि जीवनसाथी से मुलाकात परिवार, काम, "
                "दोस्तों, यात्रा या किसी अन्य माध्यम से हुई थी। कोई खास कहानी बताना अनुमान होगा। "
                "क्या आप बताना चाहेंगे कि मुलाकात किस परिस्थिति में हुई थी?"
            )
        return (
            "The available natal evidence does not reliably distinguish whether you met through family, work, "
            "friends, travel, or another channel. Choosing a specific story would be speculation. "
            "What was the actual setting in which you first met?"
        )
    if policy.get("claim_permission") == "no_specific_spouse_temperament":
        missing = ", ".join(
            str(value).replace("_", " ")
            for value in list(policy.get("missing_temperament_layers") or [])[:5]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं जीवनसाथी के स्वभाव का विश्वसनीय विश्लेषण नहीं दे सकता क्योंकि आवश्यक परतें पूरी नहीं हैं"
                f" ({missing})। केवल सातवें भाव से व्यक्तित्व बनाना अनुमान होगा।"
            )
        return (
            "I can’t give a reliable spouse-temperament profile because the required chart layers are incomplete"
            f" ({missing}). Building the personality from the seventh house alone would be speculation."
        )
    if policy.get("claim_permission") == "no_specific_spouse_appearance":
        missing = ", ".join(
            str(value).replace("_", " ")
            for value in list(policy.get("missing_appearance_layers") or [])[:5]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं जीवनसाथी के रूप-रंग का विश्वसनीय संभावित विवरण नहीं दे सकता क्योंकि आवश्यक कुंडली-परतें "
                f"पूरी नहीं हैं ({missing})। स्वभाव को शारीरिक रूप बताना अनुमान होगा।"
            )
        return (
            "I can’t give a reliable probable appearance description because the required chart layers are incomplete"
            f" ({missing}). Replacing physical evidence with personality traits would be speculation."
        )
    if policy.get("claim_permission") == "no_specific_spouse_location":
        missing = ", ".join(
            str(value).replace("_", " ")
            for value in list(policy.get("missing_location_layers") or [])[:4]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं यह विश्वसनीय रूप से नहीं बता सकता कि जीवनसाथी किसी अलग शहर, संस्कृति या पृष्ठभूमि से जुड़े हैं, "
                f"क्योंकि आवश्यक कुंडली-परतें पूरी नहीं हैं ({missing})।"
            )
        return (
            "I can’t reliably distinguish a different-city, cultural, or local-background connection because the "
            f"required chart layers are incomplete ({missing}). Choosing one would be speculation."
        )
    if policy.get("claim_permission") == "no_calculated_marriage_remedy":
        if str(language or "").lower().startswith("hi"):
            return "गणना किया हुआ विवाह-उपाय उपलब्ध नहीं है, इसलिए कोई सामान्य या मनगढ़ंत उपाय बताना उचित नहीं होगा।"
        return (
            "The calculated marriage-remedy recommendation is unavailable, so I won’t replace it with a generic "
            "remedy or another conflict diagnosis."
        )
    if policy.get("runtime_key") == "spouse_meeting":
        # A static meeting-context answer may not borrow timing prose even if
        # the composer disregards the graph exclusions.
        sentences = re.split(r"(?<=[.!?])\s+", clean_answer)
        clean_answer = " ".join(
            sentence for sentence in sentences
            if not re.search(
                r"\b(dasha|mahadasha|antardasha|pratyantardasha|transit|activated|activation|"
                r"(?:sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)[- ]driven period)\b",
                sentence,
                re.IGNORECASE,
            )
        ).strip()
    if (
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "love_arranged_marriage"
    ):
        # Static natal comparison must never borrow timing vocabulary. Keep a
        # deterministic last line of defense in case the composer disregards
        # the route-specific instruction.
        clean_answer = re.sub(
            r"\bactivated\b",
            "emphasized in the natal chart",
            clean_answer,
            flags=re.IGNORECASE,
        )
        clean_answer = re.sub(r"\bactivation\b", "natal emphasis", clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(
            r"\b(is|are|was|were)\s+active\b",
            r"\1 relevant in the natal chart",
            clean_answer,
            flags=re.IGNORECASE,
        )
    wealth_rules = policy.get("wealth_answer_rules") if isinstance(policy.get("wealth_answer_rules"), Mapping) else {}
    if policy.get("domain") == "wealth" and wealth_rules.get("static_route"):
        # Static Wealth routes use D2 as the mandatory Wealth divisional and
        # natal relationships are conditions rather than time activations.
        # D9 is retained only for the authored investment-family carrier check.
        sentences = re.split(r"(?<=[.!?])\s+", clean_answer)
        investment_family = str(policy.get("runtime_key") or "") in {
            "investment", "investing_vs_trading", "investment_risk",
            "loss_vulnerability", "windfall",
        }
        if not investment_family:
            clean_answer = " ".join(
                sentence for sentence in sentences
                if not re.search(r"\b(?:D9|Navamsha|Navamsa)\b", sentence, re.IGNORECASE)
            ).strip()
        clean_answer = re.sub(r"\bactivated\b", "emphasized in the natal chart", clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r"\bactivation\b", "natal emphasis", clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r"\b(is|are|was|were)\s+active\b", r"\1 relevant in the natal chart", clean_answer, flags=re.IGNORECASE)
        adjudication = policy.get("wealth_adjudication") if isinstance(policy.get("wealth_adjudication"), Mapping) else {}
        if adjudication.get("strength_claim_permission") == "qualified_only":
            # The writer may not turn calculator availability or a legacy
            # aggregate score into an unqualified Wealth verdict. Preserve the
            # prose while deterministically correcting the common overclaims.
            clean_answer = re.sub(
                r"\b(?:a\s+)?genuinely strong foundation\b",
                "a real but qualified foundation",
                clean_answer,
                flags=re.IGNORECASE,
            )
            clean_answer = re.sub(
                r"\ba clear pattern of accumulation and retention\b",
                "a mixed pattern of accumulation capacity and retention pressure",
                clean_answer,
                flags=re.IGNORECASE,
            )
            clean_answer = re.sub(
                r"\bthe potential is clearly there\b",
                "the potential is present but qualified",
                clean_answer,
                flags=re.IGNORECASE,
            )
            clean_answer = re.sub(
                r"\bhas a good chance of staying with you and multiplying over time\b",
                "requires deliberate retention discipline to compound over time",
                clean_answer,
                flags=re.IGNORECASE,
            )
            # A mixed D2 can qualify a D1 promise but cannot positively confirm
            # retention. Limit this correction to sentences that name D2/Hora.
            sentences = re.split(r"(?<=[.!?])\s+", clean_answer)
            corrected_sentences = []
            for sentence in sentences:
                if re.search(r"\b(?:D2|Hora)\b", sentence, re.IGNORECASE):
                    sentence = re.sub(r"\bconfirms?\b", "qualifies", sentence, flags=re.IGNORECASE)
                if re.search(r"\bIndu Lagna\b", sentence, re.IGNORECASE) and re.search(
                    r"\b(?:creativ\w*|beauty|luxury|profession|income channel)\b", sentence, re.IGNORECASE
                ):
                    sentence = (
                        "Indu Lagna is a supplementary wealth lens here; its sign or lord alone does not establish "
                        "a profession, industry, or income channel."
                    )
                sentence = re.sub(
                    r"\b5th house\s*\(\s*gains(?:\s+and\s+smart\s+allocation)?\s*\)",
                    "5th house (judgment, speculation and investment intelligence)",
                    sentence,
                    flags=re.IGNORECASE,
                )
                corrected_sentences.append(sentence)
            clean_answer = " ".join(corrected_sentences).strip()
        source_synthesis = (
            wealth_rules.get("wealth_source_synthesis")
            if isinstance(wealth_rules.get("wealth_source_synthesis"), Mapping)
            else {}
        )
        if (
            str(policy.get("runtime_key") or "") == "wealth_source"
            and source_synthesis
            and str(language or "").lower().startswith("en")
        ):
            ranked_channels = [
                dict(row) for row in list(source_synthesis.get("ranked_channels") or [])
                if isinstance(row, Mapping) and row.get("label")
            ]
            top_keywords = [
                str(value).lower() for value in list((ranked_channels[0] if ranked_channels else {}).get("required_keywords") or [])
                if value
            ]
            names_calculated_source = bool(
                ranked_channels
                and any(re.search(rf"\b{re.escape(keyword)}\w*\b", clean_answer, re.IGNORECASE) for keyword in top_keywords)
            )
            substitutes_retention_for_source = bool(
                re.search(r"\b(?:automated savings|spending account|investment account|budgeting system)\b", clean_answer, re.IGNORECASE)
                and not names_calculated_source
            )
            if ranked_channels and (not names_calculated_source or substitutes_retention_for_source):
                def channel_sentence(row: Mapping[str, Any], *, lead: str) -> str:
                    label = str(row.get("label") or "supported work").strip()
                    evidence = [str(value).strip() for value in list(row.get("evidence") or []) if str(value).strip()]
                    basis = "; ".join(evidence[:2])
                    return f"{lead} {label}. The chart basis is that {basis}." if basis else f"{lead} {label}."

                parts = [channel_sentence(ranked_channels[0], lead="Your strongest wealth-building path is")]
                if len(ranked_channels) > 1:
                    parts.append(channel_sentence(ranked_channels[1], lead="Your second channel is"))
                if len(ranked_channels) > 2:
                    parts.append(f"A third supported channel is {ranked_channels[2].get('label')}.")
                structure = str(source_synthesis.get("earning_structure") or "")
                structure_text = {
                    "profession_or_service_led": "Overall, the structure is profession- or service-led rather than primarily speculative or partnership-dependent.",
                    "business_or_enterprise_led": "Overall, the structure is business- or enterprise-led, with professional skill supplying the value being sold.",
                    "profession_led_hybrid_with_enterprise_upside": "Overall, this is a profession-led hybrid: specialized expertise is the base, with stronger upside when it is scaled through products, platforms, consulting or enterprise rather than kept as salary alone.",
                }.get(structure)
                if structure_text:
                    parts.append(structure_text)
                if str(source_synthesis.get("retention_qualification") or "") == "mixed_capacity_with_retention_pressure":
                    parts.append(
                        "D2 adds a separate caution: earning capacity is better supported than retention, so keeping and compounding the money needs discipline—but that is a qualification, not the source itself."
                    )
                parts.append("Which of these paths matches the work or business you are already building?")
                clean_answer = " ".join(parts)
        multiple_income_synthesis = (
            wealth_rules.get("multiple_income_synthesis")
            if isinstance(wealth_rules.get("multiple_income_synthesis"), Mapping)
            else {}
        )
        if (
            str(policy.get("runtime_key") or "") == "multiple_income"
            and multiple_income_synthesis
            and str(language or "").lower().startswith("en")
        ):
            primary_stream = (
                multiple_income_synthesis.get("primary_stream")
                if isinstance(multiple_income_synthesis.get("primary_stream"), Mapping)
                else {}
            )
            secondary_streams = [
                dict(row) for row in list(multiple_income_synthesis.get("secondary_streams") or [])
                if isinstance(row, Mapping) and row.get("label")
            ]
            required_channel_keywords = [
                str(value).lower()
                for row in [primary_stream, *secondary_streams[:1]]
                for value in list(row.get("required_keywords") or [])
                if value
            ]
            names_streams = sum(
                1 for keyword in required_channel_keywords
                if re.search(rf"\b{re.escape(keyword)}\w*\b", clean_answer, re.IGNORECASE)
            ) >= 2
            gives_direct_verdict = bool(re.search(r"\b(?:yes|supports? more than one|multiple (?:income )?streams?)\b", clean_answer, re.IGNORECASE))
            if not names_streams or not gives_direct_verdict:
                verdict = str(multiple_income_synthesis.get("verdict") or "")
                if verdict == "multiple_complementary_streams_supported":
                    parts = [
                        "Yes—your chart supports more than one income stream, but the strongest pattern is complementary streams built around one core expertise, not unrelated side hustles."
                    ]
                else:
                    parts = [
                        "Your chart is clearer for one primary income engine than for several equally strong streams."
                    ]
                if primary_stream.get("label"):
                    primary_evidence = [str(value) for value in list(primary_stream.get("evidence") or []) if value]
                    basis = "; ".join(primary_evidence[:2])
                    parts.append(
                        f"The primary stream is {primary_stream.get('label')}."
                        + (f" The chart basis is that {basis}." if basis else "")
                    )
                if secondary_streams:
                    parts.append(f"The strongest secondary stream is {secondary_streams[0].get('label')}.")
                if len(secondary_streams) > 1:
                    parts.append(f"A further supporting stream is {secondary_streams[1].get('label')}.")
                parts.append(
                    "This favors a structure such as core professional income plus a scalable product/platform or consulting-advisory layer, rather than several disconnected ventures."
                )
                if str(multiple_income_synthesis.get("retention_qualification") or "") == "mixed_capacity_with_retention_pressure":
                    parts.append(
                        "D2 separately shows retention pressure, so several inflows can still feel financially thin unless the streams are consolidated and retained; that does not cancel the multiple-income promise."
                    )
                parts.append("Which second stream are you considering alongside your main work?")
                clean_answer = " ".join(parts)
        loss_synthesis = (
            wealth_rules.get("loss_vulnerability_synthesis")
            if isinstance(wealth_rules.get("loss_vulnerability_synthesis"), Mapping)
            else {}
        )
        if (
            str(policy.get("runtime_key") or "") == "loss_vulnerability"
            and loss_synthesis
            and str(language or "").lower().startswith("en")
        ):
            vulnerabilities = [
                dict(row) for row in list(loss_synthesis.get("ranked_vulnerabilities") or [])
                if isinstance(row, Mapping) and row.get("label")
            ]
            top_keywords = [
                str(value) for value in list((vulnerabilities[0] if vulnerabilities else {}).get("required_keywords") or [])
                if value
            ]
            names_top_loss = any(
                re.search(rf"\b{re.escape(keyword)}\w*\b", clean_answer, re.IGNORECASE)
                for keyword in top_keywords
            )
            has_loss_layers = bool(
                re.search(r"\bD2\b", clean_answer, re.IGNORECASE)
                and re.search(r"\b(?:D5|Panchamsha)\b", clean_answer, re.IGNORECASE)
                and re.search(r"\b(?:D9|Navamsha|Navamsa)\b", clean_answer, re.IGNORECASE)
            )
            if vulnerabilities and (not names_top_loss or not has_loss_layers):
                def vulnerability_sentence(row: Mapping[str, Any], lead: str) -> str:
                    evidence = [str(value).strip() for value in list(row.get("evidence") or []) if str(value).strip()]
                    basis = "; ".join(evidence[:4])
                    return f"{lead} {row.get('label')}. The evidence is that {basis}."

                parts = [vulnerability_sentence(vulnerabilities[0], "Your chart is most vulnerable to loss through")]
                if len(vulnerabilities) > 1:
                    parts.append(vulnerability_sentence(vulnerabilities[1], "The second vulnerability is"))
                if len(vulnerabilities) > 2:
                    parts.append(f"A further pressure point is {vulnerabilities[2].get('label')}.")
                counterweight = loss_synthesis.get("protective_counterweight") if isinstance(loss_synthesis.get("protective_counterweight"), Mapping) else {}
                eleventh = counterweight.get("eleventh_lord") if isinstance(counterweight.get("eleventh_lord"), Mapping) else {}
                if eleventh.get("planet"):
                    dignity = str(eleventh.get("dignity") or "").replace("_", " ")
                    parts.append(
                        f"This does not deny gain capacity: the eleventh lord {eleventh.get('planet')} is in house {eleventh.get('placement_house')}"
                        + (f" with {dignity} dignity" if dignity else "")
                        + ". The vulnerability is in decision quality and retention, not an inability to earn."
                    )
                parts.append("Which feels more familiar in real life—losses from risky decisions, or money leaving after you earn it?")
                clean_answer = " ".join(parts)
        investment_synthesis = (
            wealth_rules.get("investment_synthesis")
            if isinstance(wealth_rules.get("investment_synthesis"), Mapping)
            else {}
        )
        if (
            investment_family
            and str(policy.get("runtime_key") or "") != "loss_vulnerability"
            and investment_synthesis
            and str(language or "").lower().startswith("en")
        ):
            fifth_lord = (
                investment_synthesis.get("fifth_lord")
                if isinstance(investment_synthesis.get("fifth_lord"), Mapping)
                else {}
            )
            fifth_planet = str(fifth_lord.get("planet") or "")
            d5 = investment_synthesis.get("d5") if isinstance(investment_synthesis.get("d5"), Mapping) else {}
            d9 = investment_synthesis.get("d9") if isinstance(investment_synthesis.get("d9"), Mapping) else {}
            d5_named_planets = [
                str(row.get("planet") or "")
                for row in list(d5.get("supporting_placements") or []) + list(d5.get("caution_placements") or [])
                if isinstance(row, Mapping) and row.get("planet")
            ]
            d9_named_planets = [
                str(row.get("planet") or "")
                for row in list(d9.get("supporting_placements") or []) + list(d9.get("caution_placements") or [])
                if isinstance(row, Mapping) and row.get("planet")
            ]
            has_concrete_fifth = bool(fifth_planet and re.search(rf"\b{re.escape(fifth_planet)}\b", clean_answer, re.IGNORECASE))
            has_concrete_d5 = bool(
                re.search(r"\b(?:D5|Panchamsha)\b", clean_answer, re.IGNORECASE)
                and any(re.search(rf"\b{re.escape(planet)}\b", clean_answer, re.IGNORECASE) for planet in d5_named_planets)
            )
            has_concrete_d9 = bool(
                re.search(r"\b(?:D9|Navamsha|Navamsa)\b", clean_answer, re.IGNORECASE)
                and any(re.search(rf"\b{re.escape(planet)}\b", clean_answer, re.IGNORECASE) for planet in d9_named_planets)
            )
            if not (has_concrete_fifth and has_concrete_d5 and has_concrete_d9):
                def ordinal(value: Any) -> str:
                    try:
                        number = int(value)
                    except (TypeError, ValueError):
                        return str(value or "")
                    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
                    return f"{number}{suffix}"

                def placement_text(row: Mapping[str, Any]) -> str:
                    planet = str(row.get("planet") or "a carrier")
                    house = row.get("house")
                    dignity = str(row.get("dignity") or "").replace("_", " ")
                    text = f"{planet} in the {ordinal(house)} house" if house else planet
                    if dignity and dignity != "neutral":
                        text += f" ({dignity})"
                    return text

                def join_items(values: list[str]) -> str:
                    values = [value for value in values if value]
                    if len(values) < 2:
                        return "".join(values)
                    if len(values) == 2:
                        return f"{values[0]} and {values[1]}"
                    return f"{', '.join(values[:-1])}, and {values[-1]}"

                flag_labels = {
                    "gandanta": "Gandanta",
                    "avayogi_lord": "Avayogi lordship",
                    "dagdha_lord": "Dagdha lordship",
                    "tithi_shunya_lord": "Tithi-Shunya lordship",
                    "avayogi_tithi_shunya_override": "the Avayogi–Tithi-Shunya cancellation",
                    "mixed_or_malefic_conjunctions": "mixed or difficult conjunctions",
                }
                flags = [flag_labels.get(str(flag), str(flag).replace("_", " ")) for flag in fifth_lord.get("caution_flags") or []]
                fifth_strength = str(fifth_lord.get("shadbala_grade") or "").lower()
                fifth_parts = []
                if fifth_strength:
                    fifth_parts.append(f"{fifth_strength} Shadbala")
                if fifth_lord.get("retrograde"):
                    fifth_parts.append("retrograde motion")
                fifth_parts.extend(flags)

                eleventh = (
                    investment_synthesis.get("eleventh_lord")
                    if isinstance(investment_synthesis.get("eleventh_lord"), Mapping)
                    else {}
                )
                eleventh_planet = str(eleventh.get("planet") or "The eleventh lord")
                eleventh_house = eleventh.get("placement_house")
                eleventh_dignity = str(eleventh.get("dignity") or "").replace("_", " ")
                gains_sentence = (
                    f"{eleventh_planet}, the eleventh lord, is in the {ordinal(eleventh_house)} house"
                    if eleventh_house else f"{eleventh_planet}, the eleventh lord"
                )
                if eleventh_dignity == "own sign":
                    gains_sentence += " in its own sign"
                elif eleventh_dignity and eleventh_dignity != "neutral":
                    gains_sentence += f" with {eleventh_dignity} dignity"

                d5_support = [placement_text(row) for row in list(d5.get("supporting_placements") or [])[:2] if isinstance(row, Mapping)]
                d5_cautions = [placement_text(row) for row in list(d5.get("caution_placements") or [])[:2] if isinstance(row, Mapping)]
                node_notes = [
                    f"{row.get('node')} sharing the {ordinal(row.get('house'))} house with {', '.join(str(value) for value in row.get('companions') or [])}"
                    for row in list(d5.get("node_cooccupancies") or [])[:1]
                    if isinstance(row, Mapping)
                ]
                d9_support = [placement_text(row) for row in list(d9.get("supporting_placements") or [])[:2] if isinstance(row, Mapping)]
                d9_cautions = [placement_text(row) for row in list(d9.get("caution_placements") or [])[:2] if isinstance(row, Mapping)]

                d5_sentence = "D5 is mixed"
                if d5_support:
                    d5_sentence += f": {join_items(d5_support)} support investment judgment"
                if d5_cautions or node_notes:
                    d5_sentence += f", while {join_items(d5_cautions + node_notes)} add volatility or pressure"
                d5_sentence += "."
                d9_sentence = "D9 provides supporting qualification"
                if d9_support:
                    d9_sentence += f": {join_items(d9_support)} sustain the carriers"
                if d9_cautions:
                    d9_sentence += f", while {join_items(d9_cautions)} temper consistency"
                d9_sentence += "."

                clean_answer = (
                    "Your chart supports investing, but high-risk speculation is a qualified area rather than an open green light. "
                    f"{gains_sentence}, supporting the capacity to realize gains. "
                    f"The fifth lord {fifth_planet or 'carrier'} is placed in the {ordinal(fifth_lord.get('placement_house'))} house"
                    f"; its complete condition includes {join_items(fifth_parts) if fifth_parts else 'mixed evidence'}, so that placement cannot be read as positive by itself. "
                    f"D2 gives a {str(investment_synthesis.get('retention') or 'mixed').replace('_', ' ')} verdict, separating gain capacity from the ability to retain it. "
                    f"{d5_sentence} {d9_sentence} "
                    "Overall, disciplined, researched and longer-horizon investing is better supported than frequent, leveraged or impulsive speculation. "
                    "That does not mean every speculative decision must fail; it means volatility and retention risk need tighter control."
                )
    if policy.get("domain") == "wealth" and policy.get("runtime_key") == "wealth_timing":
        growth_synthesis = (
            policy.get("wealth_growth_timing_synthesis")
            if isinstance(policy.get("wealth_growth_timing_synthesis"), Mapping)
            else {}
        )
        growth_windows = [
            dict(row) for row in list(growth_synthesis.get("ranked_growth_windows") or [])
            if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
        ]
        bounded_forecast = (
            growth_synthesis.get("bounded_period_synthesis")
            if isinstance(growth_synthesis.get("bounded_period_synthesis"), Mapping)
            else {}
        )
        if (
            policy.get("claim_permission") == "no_ranked_wealth_growth_window"
            or (not growth_windows and not bounded_forecast)
        ):
            if str(language or "").lower().startswith("hi"):
                return (
                    "गणना में भविष्य की कोई विश्वसनीय धन-वृद्धि अवधि स्थापित नहीं हुई। केवल वर्तमान दशा, "
                    "पाँचवें भाव या वित्तीय गतिविधि को धन-वृद्धि मानकर मैं कोई तारीख नहीं बनाऊँगा।"
                )
            return (
                "I can’t identify a reliable future wealth-growth phase from the calculated evidence. Current "
                "financial activity or a dasha boundary alone is not realized growth, so I won’t turn today into the answer."
            )
        if bounded_forecast and str(language or "").lower().startswith("en"):
            def format_bounded_date(value: Any) -> str:
                try:
                    return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                except (TypeError, ValueError):
                    return str(value or "")

            def natural_months(values: Any) -> str:
                months = [str(value) for value in list(values or []) if value]
                if not months:
                    return ""
                if len(months) == 1:
                    return months[0]
                if len(months) == 2:
                    return f"{months[0]} and {months[1]}"
                return f"{', '.join(months[:-1])}, and {months[-1]}"

            strongest_phase = (
                bounded_forecast.get("strongest_phase")
                if isinstance(bounded_forecast.get("strongest_phase"), Mapping)
                else {}
            )
            peak_rows = [
                row for row in list(bounded_forecast.get("strongest_peak_months") or [])
                if isinstance(row, Mapping) and row.get("month")
            ]
            peak_months = [str(row.get("month")) for row in peak_rows]
            reinforced = [
                str(value) for value in list(bounded_forecast.get("reinforced_support_months") or [])
                if value and str(value) not in peak_months
            ]
            background = list(bounded_forecast.get("background_support_months") or [])
            secondary = list(bounded_forecast.get("secondary_support_months") or [])
            lower = list(bounded_forecast.get("lower_support_months") or [])
            peak_text = natural_months(peak_months) or "the strongest dated transit concentration"
            parts = [
                f"{peak_text} is the strongest financially supportive part of the requested period."
            ]
            if strongest_phase.get("start") and strongest_phase.get("end"):
                parts.append(
                    f"The broader supportive phase runs from {format_bounded_date(strongest_phase.get('start'))} "
                    f"to {format_bounded_date(strongest_phase.get('end'))}, during {strongest_phase.get('chain')}."
                )
            if reinforced:
                parts.append(
                    f"Within that phase, {natural_months(reinforced)} receive additional dated transit reinforcement."
                )
            if background:
                parts.append(
                    f"{natural_months(background)} remains part of the supportive dasha phase, but without the same concentrated transit peak."
                )
            if secondary:
                parts.append(
                    f"{natural_months(secondary)} {'form' if len(secondary) > 1 else 'forms'} a secondary supportive period: "
                    "the financial houses remain engaged, but the KP/gain confirmation is less complete than in the strongest phase."
                )
            if lower:
                parts.append(
                    f"{natural_months(lower)} {'are' if len(lower) > 1 else 'is'} comparatively lower-support, so "
                    f"{'they are' if len(lower) > 1 else 'it is'} better read as consolidation and financial management rather than a primary growth window."
                )
            if growth_synthesis.get("retention_qualification") == "mixed_capacity_with_retention_pressure":
                parts.append(
                    "Your D2 still shows retention pressure, so supportive months are better for creating or collecting gains than assuming every inflow will automatically stay."
                )
            parts.append(
                "This is a relative astrological forecast across the year, not a guarantee of profit or a substitute for financial planning."
            )
            parts.append(
                "Would you like me to separate these months further for career income, business, investments, or debt repayment?"
            )
            return " ".join(parts)
        if str(language or "").lower().startswith("en"):
            def format_growth_date(value: Any) -> str:
                try:
                    return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                except (TypeError, ValueError):
                    return str(value or "")

            def growth_range(row: Mapping[str, Any]) -> str:
                return f"{format_growth_date(row.get('start'))} to {format_growth_date(row.get('end'))}"

            required_dates = [
                (str(row.get(key) or "")[:10], format_growth_date(row.get(key)))
                for row in growth_windows[:2]
                for key in ("start", "end")
                if row.get(key)
            ]
            names_required_windows = all(
                iso_value in clean_answer or human_value in clean_answer
                for iso_value, human_value in required_dates
            )
            current = (
                growth_synthesis.get("current_window_assessment")
                if isinstance(growth_synthesis.get("current_window_assessment"), Mapping)
                else {}
            )
            current_start = format_growth_date(current.get("start")) if current.get("start") else ""
            mislabels_current = bool(
                current_start
                and current_start in clean_answer
                and re.search(
                    rf"(?:next|meaningful|growth|significant marker).{{0,100}}{re.escape(current_start)}|"
                    rf"{re.escape(current_start)}.{{0,100}}(?:next|meaningful|growth|significant marker)",
                    clean_answer,
                    re.IGNORECASE,
                )
            )
            unsafe_exact_claim = bool(re.search(
                r"\b(?:exact gain date|guaranteed gains?|will become wealthy|certain profit)\b",
                clean_answer,
                re.IGNORECASE,
            ))
            if not names_required_windows or mislabels_current or unsafe_exact_claim:
                next_window = growth_windows[0]
                strongest = next(
                    (
                        row for row in growth_windows
                        if row.get("answer_role") == "strongest_later_growth_phase"
                    ),
                    max(
                        growth_windows,
                        key=lambda row: (
                            int(row.get("tier") or 0),
                            len(row.get("transit_growth_houses") or []),
                        ),
                    ),
                )
                current_sentence = (
                    f"The current {current.get('chain')} phase beginning {format_growth_date(current.get('start'))} "
                    "shows financial activity, but it does not have the complete KP-and-transit gain combination, so it is not the answer to ‘next meaningful growth’. "
                    if current else "The current period is context, not automatically the next growth phase. "
                )
                next_sentence = (
                    f"Your next meaningful wealth-growth phase is {growth_range(next_window)}, during {next_window.get('chain')}. "
                    f"The period connects wealth houses {', '.join(str(value) for value in next_window.get('growth_houses') or [])}; "
                    f"the dasha chain supplies KP support through houses {', '.join(str(value) for value in next_window.get('kp_growth_houses') or [])}, "
                    f"and transit confirms realized-gain house 11."
                )
                strongest_sentence = ""
                if strongest is not next_window:
                    strongest_sentence = (
                        f" The fuller and stronger later phase is {growth_range(strongest)}, during {strongest.get('chain')}, "
                        f"when houses {', '.join(str(value) for value in strongest.get('growth_houses') or [])} combine with broader KP and transit confirmation."
                    )
                retention_sentence = (
                    " D2 still shows mixed accumulation capacity with retention pressure, so these periods support growth opportunities more clearly than automatic wealth retention."
                    if growth_synthesis.get("retention_qualification") == "mixed_capacity_with_retention_pressure"
                    else ""
                )
                clean_answer = (
                    f"{current_sentence}{next_sentence}{strongest_sentence}{retention_sentence} "
                    "These are broad astrological support periods, not guaranteed gains or exact transaction dates. "
                    "Are you looking for growth through career income, business, or investments?"
                ).strip()
    if policy.get("domain") == "wealth" and policy.get("runtime_key") == "loan_decision":
        loan_synthesis = (
            policy.get("loan_decision_synthesis")
            if isinstance(policy.get("loan_decision_synthesis"), Mapping)
            else {}
        )
        decision_windows = [
            dict(row) for row in list(loan_synthesis.get("requested_horizon_windows") or [])
            if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
        ]
        if policy.get("claim_permission") == "no_loan_decision_horizon_evidence" or not decision_windows:
            if str(language or "").lower().startswith("hi"):
                return (
                    "अनुरोधित अवधि के लिए ऋण-निर्णय का पूरा गणितीय साक्ष्य उपलब्ध नहीं है। केवल जन्मकुंडली की "
                    "ऋण-प्रवृत्ति या सामान्य व्यवसाय-योग से नया ऋण लेने की सलाह देना उचित नहीं होगा।"
                )
            return (
                "I can’t make a reliable chart-based loan decision for the requested period because the complete "
                "borrowing, repayment, business-conversion and timing chain is unavailable. A static debt tendency "
                "alone is not enough to recommend new borrowing."
            )
        if str(language or "").lower().startswith("en"):
            def format_loan_date(value: Any) -> str:
                try:
                    return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                except (TypeError, ValueError):
                    return str(value or "")

            supportive_windows = [
                row for row in decision_windows if int(row.get("tier") or 0) >= 2
            ]
            horizon_start = format_loan_date(decision_windows[0].get("start"))
            horizon_end = format_loan_date(decision_windows[-1].get("end"))
            if supportive_windows:
                opening = (
                    f"From an astrological perspective, the loan decision is only conditionally supported between "
                    f"{horizon_start} and {horizon_end}—this is not a blanket recommendation to borrow."
                )
            else:
                opening = (
                    f"From an astrological perspective, I would lean against taking a new business-expansion loan "
                    f"between {horizon_start} and {horizon_end}; the requested period is not a clean green light for new leverage."
                )
            phase_sentences: list[str] = []
            for row in decision_windows[:3]:
                active_debt = list(row.get("debt_access_houses") or [])
                resources = list(row.get("resource_houses") or [])
                business = list(row.get("business_conversion_houses") or [])
                pressure = list(row.get("pressure_houses") or [])
                details = []
                if active_debt:
                    details.append(f"debt-access houses {', '.join(str(value) for value in active_debt)}")
                if resources:
                    details.append(f"resource houses {', '.join(str(value) for value in resources)}")
                if business:
                    details.append(f"business-conversion houses {', '.join(str(value) for value in business)}")
                if pressure:
                    details.append(f"pressure houses {', '.join(str(value) for value in pressure)}")
                phase_sentences.append(
                    f"From {format_loan_date(row.get('start'))} to {format_loan_date(row.get('end'))}, "
                    f"the {row.get('chain')} phase emphasizes {', '.join(details) or 'incomplete financial factors'}; "
                    f"its calculated verdict is {str(row.get('classification') or '').replace('_', ' ')}."
                )
            if supportive_windows:
                conversion_sentence = (
                    "The supportive phase connects borrowing access with repayment resources and business conversion, "
                    "but the real decision still depends on whether projected cash flow can service the debt under a downside case."
                )
            else:
                conversion_sentence = (
                    "The key weakness is conversion: debt/liability activity is present, but houses 7, 10 and 11 do not "
                    "come together strongly enough with KP and transit confirmation to show that borrowed money converts "
                    "cleanly into business cash flow and repayment capacity during this horizon."
                )
            retention_sentence = (
                "D2 also shows mixed accumulation capacity with retention pressure, increasing the risk that new capital is absorbed by outflow before it compounds."
                if loan_synthesis.get("d2_retention") == "mixed_capacity_with_retention_pressure"
                else "D2 does not remove the need to test repayment capacity independently."
            )
            return " ".join([
                opening,
                *phase_sentences,
                conversion_sentence,
                retention_sentence,
                "Astrology cannot establish affordability or replace underwriting. Before taking any loan, verify debt-service coverage, total borrowing cost and a downside revenue scenario with a qualified financial professional.",
                "Would you like me to calculate the next period in which borrowing support and business conversion align more cleanly?",
            ])
    if policy.get("domain") == "wealth" and policy.get("runtime_key") == "debt_repayment":
        debt_synthesis = (
            policy.get("debt_repayment_synthesis")
            if isinstance(policy.get("debt_repayment_synthesis"), Mapping)
            else {}
        )
        repayment_windows = [
            dict(row) for row in list(debt_synthesis.get("ranked_repayment_windows") or [])
            if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
        ]
        if policy.get("claim_permission") == "no_ranked_debt_repayment_window" or not repayment_windows:
            if str(language or "").lower().startswith("hi"):
                return (
                    "गणना में कोई विश्वसनीय ऋण-चुकौती अवधि स्थापित नहीं हुई। केवल ऋण या दबाव वाले भावों का सक्रिय "
                    "होना चुकौती का संकेत नहीं है, इसलिए मैं उससे कोई तारीख नहीं बनाऊँगा।"
                )
            return (
                "I can’t identify a reliable repayment-support window from the calculated evidence. Debt-house "
                "activity alone is not repayment, so I won’t turn the current date or dasha into a payoff prediction."
            )
        if str(language or "").lower().startswith("en"):
            allowed_dates = {
                str(row.get(key) or "")[:10]
                for row in repayment_windows for key in ("start", "end")
                if row.get(key)
            }
            names_allowed_window = any(value in clean_answer for value in allowed_dates)
            contains_unsafe_debt_claim = bool(re.search(
                r"\b(significant marker|repayment season|highest[- ]interest|consolidat\w*|refinanc\w*)\b",
                clean_answer,
                re.IGNORECASE,
            ))
            if not names_allowed_window or contains_unsafe_debt_claim:
                def format_date(value: Any) -> str:
                    try:
                        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                    except (TypeError, ValueError):
                        return str(value or "")

                def range_text(row: Mapping[str, Any]) -> str:
                    return f"{format_date(row.get('start'))} to {format_date(row.get('end'))}"

                def house_list(values: Any) -> str:
                    items = [str(value) for value in list(values or [])]
                    if len(items) < 2:
                        return "".join(items)
                    return f"{', '.join(items[:-1])} and {items[-1]}"

                earliest = min(repayment_windows, key=lambda row: str(row.get("start") or ""))
                strongest = max(
                    repayment_windows,
                    key=lambda row: (int(row.get("tier") or 0), len(row.get("support_houses") or [])),
                )
                current = (
                    debt_synthesis.get("current_window_assessment")
                    if isinstance(debt_synthesis.get("current_window_assessment"), Mapping)
                    else {}
                )
                opening = (
                    "The current period shows debt pressure and financial activity, but it is not a clean repayment window"
                    if current.get("classification") == "debt_activity_not_repayment_support"
                    else "The current period does not establish a debt-free date"
                )
                earliest_sentence = (
                    f"The first calculated repayment-progress phase is {range_text(earliest)} "
                    f"during {earliest.get('chain')}. It connects repayment houses "
                    f"{house_list(earliest.get('support_houses'))}, with KP and transit support, "
                    "but pressure houses remain involved, so this is better described as progress than guaranteed clearance."
                )
                strongest_sentence = ""
                if strongest is not earliest:
                    strongest_sentence = (
                        f"The fuller repayment-support combination appears from {range_text(strongest)} "
                        f"during {strongest.get('chain')}, when houses "
                        f"{house_list(strongest.get('support_houses'))} come together. "
                    )
                clean_answer = (
                    f"{opening}; its active houses show resources and burden without the complete repayment combination. "
                    f"{earliest_sentence} {strongest_sentence}"
                    "These are broad astrological support periods, not an exact payoff date. Your actual debt-free date "
                    "depends on the outstanding balance, interest, cash flow and repayments, which the chart does not calculate. "
                    "Are you asking about one specific loan or your total debt burden?"
                ).strip()
    if policy.get("claim_permission") == "no_health_area_specificity":
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं अगले छह महीनों के लिए किसी विशेष स्वास्थ्य क्षेत्र को विश्वसनीय रूप से प्राथमिकता नहीं दे सकता, "
                "क्योंकि आवश्यक शरीर-क्षेत्र गणना उपलब्ध नहीं है। किसी अंग, लक्षण या जोखिम-अवधि का नाम देना अनुमान होगा। "
                "सामान्य रोकथाम, नियमित जाँच और लगातार बने रहने वाले लक्षणों पर चिकित्सकीय सलाह सबसे उचित है। "
                "क्या कोई विशेष स्वास्थ्य चिंता है जिसे आप ध्यान में रखना चाहते हैं?"
            )
        return (
            "I can’t reliably identify one health area as needing the most caution because the required body-area "
            "calculation is unavailable. Naming a body zone or risk window would be speculation. General preventive "
            "care, routine check-ups, and professional advice for persistent symptoms are the safest guidance. "
            "Is there a specific health concern you want me to keep in view?"
        )
    if policy.get("claim_permission") == "no_complete_wealth_verdict":
        missing = ", ".join(
            str(value).split(":")[-1]
            for value in list(policy.get("missing_required_factors") or [])[:5]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                f"मैं अभी पूर्ण धन-वित्त निष्कर्ष नहीं दे सकता क्योंकि आवश्यक गणना-परतें ({missing}) उपलब्ध नहीं हैं। "
                "D9 या सामान्य ग्रह-अर्थ से इस कमी को भरना अनुमान होगा।"
            )
        return (
            f"I can’t give a complete Wealth reading because required calculated layers are unavailable ({missing}). "
            "Substituting D9 or generic planet meanings for them would be speculation."
        )
    if policy.get("claim_permission") != "directional_only_no_timing":
        return clean_answer
    return _deeper_mode_fallback(language)
