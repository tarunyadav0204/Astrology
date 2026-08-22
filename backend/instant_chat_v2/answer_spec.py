"""Claim-bound answer specification and deterministic integrity checks."""

from __future__ import annotations

from typing import Any, Dict, List


def build_answer_spec(query_plan: Dict[str, Any], verdict: Dict[str, Any], ledger: Dict[str, Any]) -> Dict[str, Any]:
    evidence_ids = [item.get("evidence_id") for item in ledger.get("records", []) if item.get("evidence_id")]
    primary_ids = verdict.get("evidence_ids") or evidence_ids[:2]
    claims: List[Dict[str, Any]] = [
        {
            "claim_id": "claim-direct-answer",
            "purpose": "Answer the user's exact question plainly",
            "evidence_ids": primary_ids,
            "required": True,
        },
        {
            "claim_id": "claim-chart-reason",
            "purpose": "Give one compact astrological reason",
            "evidence_ids": evidence_ids[:4],
            "required": True,
        },
    ]
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
    exact_day = bool(time_scope.get("is_exact_day"))
    daily_ids = [
        item.get("evidence_id") for item in ledger.get("records", [])
        if item.get("kind") in {"daily_dasha_stack", "daily_moon_tara", "daily_kp", "daily_school_synthesis"}
    ]
    if exact_day:
        claims.append({
            "claim_id": "claim-daily-outlook",
            "purpose": "Give the exact day's ranked likely manifestations, best use, main caution and one practical action",
            "evidence_ids": daily_ids,
            "required": True,
        })
    if query_plan.get("answer_mode") == "comparison_choice":
        comparison_ids = [
            item.get("evidence_id") for item in ledger.get("records", [])
            if item.get("kind") == "option_comparison"
        ]
        if comparison_ids:
            claims.append({
                "claim_id": "claim-option-comparison",
                "purpose": "Compare every named option using the option-specific evidence and its bounded horizon",
                "evidence_ids": comparison_ids,
                "required": True,
            })
    if query_plan.get("answer_mode") == "potential_capacity":
        promise_ids = [
            item.get("evidence_id") for item in ledger.get("records", [])
            if item.get("kind") in {"natal_promise", "primary_drivers", "divisional_confirmation"}
            and item.get("evidence_id")
        ]
        claims.append({
            "claim_id": "claim-natal-promise-verdict",
            "purpose": "Judge whether the natal chart promises the requested outcome, without using current timing as proof",
            "evidence_ids": promise_ids,
            "required": True,
        })
    if not exact_day and query_plan.get("answer_mode") in {"event_timing", "lifetime_event_timing", "month_timing", "event_prediction", "timing_window"}:
        timing_ids = [item.get("evidence_id") for item in ledger.get("records", []) if item.get("kind") == "event_timing_verdict"]
        if timing_ids:
            claims.append({
                "claim_id": "claim-timing-window",
                "purpose": "State only the strongest supported timing window",
                "evidence_ids": timing_ids,
                "required": True,
            })
    activation_record = next(
        (item for item in ledger.get("records", []) if item.get("kind") == "transit_activation_timeline"),
        None,
    )
    activation_value = (activation_record or {}).get("value")
    activation_value = activation_value if isinstance(activation_value, dict) else {}
    activation_timeline = activation_value.get("timeline") if isinstance(activation_value.get("timeline"), dict) else {}
    if not exact_day and activation_record and activation_timeline:
        claims.append({
            "claim_id": "claim-dated-transit-activation",
            "purpose": "Identify only dated peaks that pass natal promise, dasha permission, and transit-trigger gates",
            "evidence_ids": [activation_record.get("evidence_id")],
            "required": True,
        })
    timing_sequence = None
    current_cause_rules = None
    timing_value: Dict[str, Any] = {}
    if not exact_day and query_plan.get("answer_mode") == "event_prediction":
        timing_record = next(
            (item for item in ledger.get("records", []) if item.get("kind") == "event_timing_verdict"),
            None,
        )
        timing_value = (timing_record or {}).get("value")
        timing_value = timing_value if isinstance(timing_value, dict) else {}
        current_window = timing_value.get("current_window") if isinstance(timing_value.get("current_window"), dict) else {}
        is_derived_target = query_plan.get("interpretation_frame") == "native_chart_derived_house"
        current_cause_rules = {
            "allowed_current_window_reason": current_window.get("why"),
            "allowed_current_topic_transits": (
                [] if is_derived_target else timing_value.get("current_topic_transits") or []
            ),
            "instruction": (
                "Explain the current problem using only these supplied current-window and topical-transit facts. "
                "Do not add a conjunction, placement, house lordship, or generic planet effect unless it is "
                "explicitly present here. If a topical transit is supplied, mention it before optional background. "
                "For a derived subject, omit native-chart transits unless they are explicitly supplied in this allow-list."
            ),
        }
        timing_sequence = {
            "order": [
                "current_cause",
                "earliest_material_improvement",
                "intermediate_strengthening_if_supplied",
                "later_peak_if_useful",
            ],
            "instruction": (
                "When the question asks why something is happening now and when it improves, explain the "
                "current cause first. State the earliest materially better window before any later absolute "
                "peak. Never make the peak sound like the first possible relief. Use current_topic_transits "
                "when supplied; do not replace them with generic planet folklore."
            ),
        }
    health_rules = None
    health_category = str(query_plan.get("category") or "").lower()
    if health_category in {"health", "mental_wellbeing", "surgery", "accident", "recovery"}:
        semantic_time = time_scope.get("semantic") if isinstance(time_scope.get("semantic"), dict) else {}
        semantic_kind = str(semantic_time.get("kind") or "none").strip().lower()
        requested_time = time_scope.get("requested")
        requested_time_text = (
            str(requested_time or "").strip().lower()
            if not isinstance(requested_time, (dict, list, tuple, set))
            else ""
        )
        generic_router_scopes = {
            "", "none",
            # Timeless birth-chart/constitution aliases emitted by different
            # versions of the semantic router. These describe the evidence
            # frame, not a requested forecast period.
            "birth", "birth_chart", "natal", "natal_chart", "constitutional",
            "constitution", "lifetime",
            # Generic router defaults. These also do not prove that the user
            # explicitly requested timing unless semantic kind/mode agrees.
            "current", "present", "now", "current_or_next", "as_of",
        }
        answer_mode = str(query_plan.get("answer_mode") or "topic_reading").strip().lower()
        timing_answer_modes = {
            "event_timing", "lifetime_event_timing", "month_timing",
            "timing_window", "daily_forecast",
        }
        # `query_context.time_scope` may be populated with the router's generic
        # default "current" even when the user asked a timeless constitutional
        # question.  It is not an explicit timing request unless the semantic
        # timeframe or selected answer mode independently confirms timing.
        explicit_requested_time = bool(
            requested_time
            and (
                isinstance(requested_time, (dict, list, tuple, set))
                or requested_time_text not in generic_router_scopes
            )
        )
        explicit_health_time_scope = bool(
            explicit_requested_time
            or exact_day
            or semantic_kind not in {"", "none", "current"}
            # `event_prediction` is intentionally not enough on its own. The
            # router can select it for questions such as "Do I have a risk of
            # diabetes?", which ask about constitutional susceptibility rather
            # than a calendar forecast. Timing needs an explicit user timeframe
            # (or a genuinely timing-specific mode).
            or answer_mode in timing_answer_modes
        )
        health_record = next(
            (item for item in ledger.get("records", []) if item.get("kind") == "health_body_area"),
            None,
        )
        health_value = (health_record or {}).get("value")
        priority_zones = health_value.get("priority_zones") if isinstance(health_value, dict) else []
        major_vulnerabilities = (
            health_value.get("major_vulnerabilities") if isinstance(health_value, dict) else []
        )
        medical_profile = (
            health_value.get("medical_profile") if isinstance(health_value, dict) else {}
        )
        medical_profile = medical_profile if isinstance(medical_profile, dict) else {}
        allowed_zones = [
            str(item.get("zone") or "").strip()
            for item in (major_vulnerabilities or [])[:3]
            if isinstance(item, dict) and str(item.get("zone") or "").strip()
        ]
        allowed_zone_evidence = []
        for item in (major_vulnerabilities or [])[:3]:
            if not isinstance(item, dict):
                continue
            zone = str(item.get("zone") or "").strip()
            if not zone or zone not in allowed_zones:
                continue
            allowed_zone_evidence.append({
                "zone": zone,
                "anatomical_members": list(item.get("anatomical_members") or [])[:6],
                "confidence": item.get("confidence"),
                "confluence_count": item.get("confluence_count"),
                "primary_medical_factors": list(item.get("primary_medical_factors") or [])[:3],
                "confirmation_factors": list(item.get("confirmation_factors") or [])[:3],
                "natal_layers": list(item.get("natal_layers") or [])[:6],
                "sources": list(item.get("sources") or [])[:5],
                "why": list(item.get("why") or [])[:4],
                "mechanisms": list(item.get("mechanisms") or [])[:3],
                "divisional_repetition": list(item.get("divisional_repetition") or [])[:5],
                "activation_sources": list(item.get("activation_sources") or [])[:3],
            })
        allowed_mechanisms = sorted({
            str(mechanism).strip()
            for item in allowed_zone_evidence
            for mechanism in (item.get("mechanisms") or [])
            if str(mechanism).strip()
        })
        condition_susceptibilities = list(medical_profile.get("condition_susceptibilities") or [])
        protective_factors = list(medical_profile.get("protective_factors") or [])
        requested_horizon = {
            "start": time_scope.get("as_of"),
            "end": time_scope.get("horizon_end"),
            "requested": requested_time,
        }
        if health_record and allowed_zones:
            claims.append({
                "claim_id": "claim-health-body-area",
                "purpose": "Name only the explicitly calculated susceptibility zones",
                "evidence_ids": [health_record.get("evidence_id")],
                "required": True,
            })
        health_rules = {
            "health_question_type": health_category,
            "is_time_bound_question": explicit_health_time_scope,
            "allowed_zone_names": allowed_zones,
            "allowed_zone_evidence": allowed_zone_evidence,
            "allowed_mechanisms": allowed_mechanisms,
            "major_vulnerabilities": major_vulnerabilities or [],
            "broader_directional_zones": priority_zones or [],
            "calculated_medical_profile": medical_profile,
            "condition_susceptibilities": condition_susceptibilities,
            "protective_factors": protective_factors,
            "requested_horizon": requested_horizon,
            "medical_framing": "Astrological susceptibility only; never a diagnosis or prediction of illness.",
            "answer_order": [
                "plain-language ranked constitutional vulnerabilities (maximum three)",
                "one concrete natal reason for each named vulnerability",
                "current activation only when the question is time-bound and an explicit activation record supports it",
                "protective or recovery factors",
                "safe practical guidance and one natural follow-up question",
            ],
            "body_part_claim": (
                "You may name the strongest allowed zone as a major constitutional vulnerability only when it "
                "appears in allowed_zone_names. Explain the independent chart factors supplied for it and say "
                "'the chart suggests susceptibility' or 'an area needing preventive attention'. If the list is "
                "empty, do not invent or name a body part. Treat anatomical_members as one regional finding: "
                "never split face/lips/chin or heart/spine/upper-back into separate independent vulnerabilities."
            ),
            "category_safety": {
                "mental_wellbeing": (
                    "You may describe an elevated calculated vulnerability to mental/emotional regulation when it appears "
                    "in condition_susceptibilities. Name possible expressions such as rumination, detachment, sleep disruption "
                    "or emotional strain, but never declare a psychiatric disorder. Preserve the exact relationship stated in "
                    "the supplied evidence: an aspect is not a conjunction, and neither may be called a nodal-axis placement. "
                    "Never say the Moon is with Ketu, conjunct Ketu, or on the Rahu-Ketu axis unless the supplied evidence says "
                    "that exact relationship. Recommend professional assessment when persistent symptoms or impaired "
                    "functioning are present."
                ),
                "health": (
                    "Separate constitutional vulnerability, timed activation, and practical prevention. Do not hide a "
                    "calculated elevated BP, metabolic/blood-sugar, or mental-wellbeing susceptibility, but state it only "
                    "as preventive attention—not a diagnosis—using the supplied confluence and protective factors. Suggest "
                    "ordinary clinical screening only when supplied responsible_guidance explicitly supports it."
                ),
                "surgery": "Never state that surgery is required or certain. Separate surgical susceptibility from timing suitability.",
                "accident": "Never predict that an accident will happen. Describe calculated injury susceptibility and cautious periods only.",
                "recovery": "Never promise recovery or a medical outcome; describe supportive or pressured recovery symbolism only.",
            }.get(health_category),
            "evidence_hierarchy": (
                "Use the requested-category judgment and D1 constitution first. D3/D6/D8/D30 only confirm "
                "a D1-established vulnerability. Dignity, functional nature, combustion and Shadbala modify "
                "severity or protection. Dasha/transit only activate an established natal theme and must never "
                "create a body-part claim. Mention the concrete mechanism (acute/inflammatory, chronic/structural, "
                "nervous/functional, fluid/hormonal, or other supplied mechanism) in plain language."
            ),
            "claim_allow_list": (
                "Every named body area must come from allowed_zone_names. Every expression pattern such as "
                "acute/inflammatory, chronic/structural, nervous/functional, or fluid/hormonal must come from "
                "allowed_mechanisms and must be attached to the specific zone whose allowed_zone_evidence "
                "contains it. Do not generalize one zone's mechanism to the whole body. Do not introduce a "
                "new body system, symptom, condition, severity, or acute-versus-degenerative comparison."
            ),
            "constitutional_question_rule": (
                "This question asks for standing health vulnerabilities, not current timing. Keep the answer "
                "anchored to natal constitution. Do not narrate the current dasha or claim Houses 6/8 are "
                "currently activated unless the user explicitly asks about now/today/this period and the "
                "adjudicated evidence contains that exact activation."
                if not explicit_health_time_scope
                else "The question includes a time scope; current activation still requires an explicit adjudicated activation record."
            ),
            "forbidden_topics": (
                [
                    "current period",
                    "current dasha or MD/AD/PD",
                    "current transit",
                    "currently active houses",
                    "timing windows or calendar forecasts",
                ]
                if not explicit_health_time_scope
                else []
            ),
            "timing_framing": (
                "No ranked health-risk window exists inside the requested horizon. Do not call the requested "
                "period heightened, dangerous, acute, or high-risk. Present the allowed zones only as standing "
                "chart susceptibilities worth ordinary attention."
                if not verdict.get("ranked_windows")
                else "Tie any heightened timing language only to the ranked window supplied in the verdict."
            ),
            "dasha_framing": (
                "Do not name an MD/AD/PD chain unless every named level is explicitly visible in current_dasha "
                "evidence. Never infer a current sub-period from a future timing window."
            ),
            "period_forecast_rule": (
                {
                    "hard_horizon": requested_horizon,
                    "required_sequence": [
                        "overall outlook for exactly the requested period",
                        "standing natal vulnerabilities supported by allowed_zone_evidence",
                        "chronological comparison of every materially distinct phase inside the horizon",
                        "for each sensitive phase: natal vulnerability plus explicit dasha activation plus transit confirmation",
                        "protective factors and restrained preventive guidance",
                        "one natural follow-up question",
                    ],
                    "activation_gate": (
                        "A natal vulnerability is not a forecast. Call a phase heightened only when the same health theme "
                        "has explicit dasha activation and transit confirmation in that dated phase. With dasha support but "
                        "no transit confirmation, call it background vigilance. With neither, do not forecast manifestation."
                    ),
                    "phase_labels": [
                        "background vigilance",
                        "heightened susceptibility",
                        "supportive/protective phase",
                    ],
                    "gandanta_rule": (
                        "Gandanta is a natal sensitivity modifier only. It cannot by itself create a health forecast, date a "
                        "phase, or prove that a vulnerability will manifest."
                    ),
                    "medical_advice_rule": (
                        "Do not recommend, reject, delay, or prefer any treatment. Never advise avoiding experimental, "
                        "conventional, or other treatment from astrology. Do not invent sleep, digestion, diet, posture, "
                        "fitness, or another body-system recommendation unless that exact concern is present in calculated "
                        "medical evidence or supplied responsible_guidance. General advice may be limited to routine care, "
                        "appropriate screening, observing persistent symptoms, and consulting a qualified professional."
                    ),
                    "scope_rule": (
                        "Do not mention any date after hard_horizon.end. Do not extend 'this year' into the next year. "
                        "Do not collapse the period into one broad window when multiple calculated phases are supplied."
                    ),
                }
                if explicit_health_time_scope
                else None
            ),
        }
    answer_mode = str(query_plan.get("answer_mode") or "topic_reading")
    if answer_mode == "factual_chart_lookup":
        max_words, word_target = 280, "Predict from this named chart; usually 120-220 words."
    elif answer_mode in {"event_prediction", "timing_window", "location_recommendation", "dedicated_muhurat_flow"}:
        max_words, word_target = 320, "Usually 140-260 words; preserve every material phase or ranked window."
    elif answer_mode in {"explanation_mechanism", "problem_diagnosis", "comparison_choice"}:
        max_words, word_target = 280, "Usually 110-220 words; be complete without repeating evidence."
    else:
        max_words, word_target = 240, "Usually 90-180 words; expand when the answer genuinely needs more explanation."
    daily_rules = None
    if exact_day:
        daily_rules = {
            "target_date": time_scope.get("target_date") or time_scope.get("as_of"),
            "answer_order": [
                "direct overall outlook for this day",
                "one or two most likely real-life manifestations",
                "best use or opportunity",
                "main caution",
                "one practical action",
                "one compact astrological reason",
                "one natural follow-up question",
            ],
            "decision_hierarchy": [
                "KP daily fructification and event-house materialisation",
                "transiting Moon, current nakshatra and Tara Bala",
                "Prana and Sookshma dasha triggers",
                "Pratyantardasha as the day frame",
                "Antardasha and Mahadasha only as background permission",
            ],
            "instruction": (
                "This is an exact-day forecast, never a shortened yearly or period reading. "
                "Do not decide the day from MD/AD/PD alone. Lead with what the user is likely to "
                "experience or should do today. Use PR/SK, Moon/Tara Bala and KP to rank the day; "
                "MD/AD may explain the background in at most one compact clause."
            ),
        }
    if answer_mode == "factual_chart_lookup":
        return {
            "schema_version": "instant-answer-spec/v1",
            "tone": "clear, technical, conversational",
            "max_words": max_words,
            "composer_word_target": word_target,
            "answer_order": [
                "direct prediction in this chart's life area",
                "lagna and lagna-lord result",
                "two strongest supported outcomes",
                "one main caution",
                "one compact proof from this named chart",
                "one domain follow-up",
            ],
            "presentation_contract": {
                "astrology_is_hidden_evidence": True,
                "opening": "Give a direct life-area prediction from this named chart first.",
                "technical_detail_limit": (
                    "Placements, dignity, and aspects are evidence. Cite one compact proof from this chart; "
                    "do not dump planet-by-planet positions as the answer."
                ),
                "invalid_shape": (
                    "A planet-by-planet placement list; generic D12=parents / D10=career lore without citing "
                    "this chart's data; a D1 dasha/transit reading; or saying the chart lacks detail when the packet is supplied."
                ),
            },
            "chart_fact_rules": {
                "instruction": (
                    "Read only evidence.chart_facts. Predict the chart's domain.life_area from lagna, lagna lord, "
                    "dignity, occupation, conjunctions, and aspects. Use support_signals and caution_signals. "
                    "Do not mention current dasha or transits. Do not write a placement inventory."
                ),
            },
            "claims": claims,
            "forbidden": [
                "planet-by-planet placement dump as the whole answer",
                "generic D12=parents lore without citing this D12 packet",
                "generic D10=career lore without citing this D10 packet",
                "generic Karkamsa/Swamsa soul essay without citing that chart's packet",
                "D1 current dasha or transits as the prediction engine",
                "inventing placements not in chart_facts",
                "claiming there is not enough detail when the chart packet is supplied",
            ],
            "target_framing": "Predict from the native's own requested chart.",
            "evidence_limitations": verdict.get("missing_required_capabilities") or [],
        }
    capacity_rules = None
    if answer_mode == "potential_capacity":
        capacity_rules = {
            "verdict_direction": verdict.get("direction"),
            "instruction": (
                "This is a natal-promise judgment, not an event-timing answer. Give only the verdict allowed by "
                "the fused natal and divisional evidence. Current dasha, transits, and active houses cannot create "
                "a natal promise and must not be used as proof. For marriage, judge the D1 seventh house and its "
                "lord first, then D9; use KP seventh-cusp and Jaimini spouse indicators only as confirmation. "
                "Houses 2 or 8 alone do not prove marriage. Rahu alone does not prove a sudden, unconventional, "
                "foreign, or different-background spouse. Do not give timing unless the user asks for timing."
            ),
        }
    return {
        "schema_version": "instant-answer-spec/v1",
        "tone": "natural, concise, daily-use language",
        "max_words": max_words,
        "composer_word_target": word_target,
        "answer_order": (
            daily_rules.get("answer_order")
            if daily_rules
            else [
                "clear natal-promise verdict",
                "direct D1 support or limitation",
                "relevant divisional confirmation or qualification",
                "main condition or obstruction",
                "natural follow-up about timing or the user's real concern",
            ]
            if answer_mode == "potential_capacity"
            else ["direct_answer", "one_chart_reason", "one_caution_if_material", "natural_follow_up_question"]
        ),
        "presentation_contract": {
            "astrology_is_hidden_evidence": False,
            "opening": "Answer the user's real-life question directly in ordinary language.",
            "broad_period_answer": [
                "overall verdict",
                "two or three supported real-life manifestations",
                "stronger or more demanding phase differences",
                "one practical takeaway",
            ],
            "technical_detail_limit": (
                "Include at least one understandable astrological reason in every completed answer. "
                "Prefer plain labels such as the active dasha, relevant house/lord, transit trigger, "
                "divisional confirmation or karaka; do not dump raw calculations."
            ),
            "invalid_shape": "A list of dashas, date ranges, planets, or house numbers that leaves the user to interpret the result.",
        },
        "activation_prediction_rules": {
            "required_reasoning_order": [
                "natal promise",
                "active dasha planets' natal house links",
                "dated transit repetition or delivery",
                "ordinary-language real-life result",
            ],
            "natal_promise": activation_value.get("natal_promise"),
            "allowed_peak_windows": activation_timeline.get("peak_windows") or [],
            "high_activity_claim_gate": activation_timeline.get("high_activity_claim_gate"),
            "instructions": (
                "Do not call a period highly active merely because a dasha is running or a score is high. "
                "A high-activity claim requires a supplied allowed_peak_window. State what the period means "
                "in the user's life before giving at most one compact proof sentence. Never open with a list "
                "of dasha periods, planets, or houses. If natal promise is not supported, do not describe the "
                "undertaking as well-supported; state that the timing evidence is conditional or insufficient. "
                "For a project/career "
                "question, translate activated areas into concrete manifestations such as workload, execution, "
                "visibility, clients, agreements, cash flow, gains, delays, or launch momentum—but include only "
                "manifestations supported by the supplied result areas and support/risk evidence. Lead with the "
                "likely project outcome and name the strongest dated phase before explaining why. If no peak is "
                "supplied, say the period is background or generally active rather than inventing a peak."
            ),
        },
        "claims": claims,
        "forbidden": [
            "unsupported dates or exact certainty",
            "a named house claim not present in evidence",
            "generic deeper-reading sales language",
            "fear-based urgency",
            "calling derived-house evidence the other person's own dasha or birth chart",
            "choosing between options when option-specific evidence is unavailable",
        ],
        "target_framing": (
            "Read this as the native chart's derived indication for the named person; never call it that person's own dasha/chart."
            if query_plan.get("interpretation_frame") == "native_chart_derived_house"
            else "Read the native's own chart."
        ),
        "dasha_level_terms": {
            "MD": "Mahadasha / major period",
            "AD": "Antardasha / sub-period",
            "PD": "Pratyantardasha / sub-sub-period",
            "instruction": (
                "A chain written MD-AD-PD names three separate levels. Never describe the whole chain as a Mahadasha, "
                "Antardasha, or Pratyantardasha, and never call its PD planet the Antardasha/sub-period lord."
            ),
        },
        "required_derived_opening": (
            f"Your chart's indications for your {str((query_plan.get('target_subject') or {}).get('label') or 'relative')}..."
            if query_plan.get("interpretation_frame") == "native_chart_derived_house"
            else None
        ),
        "evidence_limitations": verdict.get("missing_required_capabilities") or [],
        "health_rules": health_rules,
        "daily_rules": daily_rules,
        "timing_sequence": timing_sequence,
        "current_cause_rules": current_cause_rules,
        "comparison_rules": (
            {
                "required_conclusion": "It is a close call; neither option is more strongly supported overall.",
                "instruction": (
                    "Keep this conclusion consistent throughout the answer. Do not contradict it later by "
                    "calling either option slightly favored, more supported, stronger, or more likely."
                ),
            }
            if verdict.get("direction") == "close_call"
            else None
        ),
        "capacity_rules": capacity_rules,
        "event_rules": (
            {
                "hard_horizon_end": (query_plan.get("time_scope") or {}).get("horizon_end"),
                "window_comparison": timing_value.get("comparison"),
                "window_score_delta": timing_value.get("score_delta"),
                "window_answer_rule": timing_value.get("answer_rule"),
                "allowed_timing_windows": [
                    {
                        "start": row.get("start"),
                        "end": row.get("end"),
                        "chain": row.get("chain"),
                        "why": row.get("why"),
                    }
                    for row in (verdict.get("ranked_windows") or [])
                    if isinstance(row, dict) and (row.get("start") or row.get("end"))
                ],
                "required_material_windows": [
                    {
                        "start": row.get("start"),
                        "end": row.get("end"),
                        "chain": row.get("chain"),
                        "activated_focus_houses": row.get("activated_focus_houses") or [],
                        "why": row.get("why"),
                    }
                    for row in (timing_value.get("material_future_progression") or [])
                    if isinstance(row, dict) and (row.get("start") or row.get("end"))
                ],
                "dasha_level_terms": {
                    "MD": "Mahadasha / major period",
                    "AD": "Antardasha / sub-period",
                    "PD": "Pratyantardasha / sub-sub-period",
                },
                "career_manifestations": (
                    ["more calls", "more effort", "interviews", "visibility"]
                    if query_plan.get("category") == "career"
                    else []
                ),
                "derived_subject_rule": (
                    "Say 'the derived Nth-house indications for your [subject]'—never 'her/his Nth house'. "
                    "Describe the active dasha as the native chart's current cycle interpreted through that derived frame. "
                    "Do not characterize the present as preparation, adjustment, stability, pressure, or opportunity unless the exact current-window evidence says so."
                    if query_plan.get("interpretation_frame") == "native_chart_derived_house"
                    else None
                ),
                "instruction": (
                    "Never state a date after hard_horizon_end. If a supplied window was clipped, use the clipped end. "
                    "Obey window_answer_rule and window_score_delta when describing relative strength; a small gap must not become a definitive strongest-window claim. "
                    "Copy start/end values from allowed_timing_windows without changing their order or moving a year. "
                    "Treat every semicolon-separated item in a window's why field as an independent fact. "
                    "Never fuse two facts into a new relationship: for example, if Saturn rules house 7 and "
                    "Jupiter occupies house 2, say those separately; do not say Jupiter links to house 7. "
                    "activated_focus_houses describes the window as a whole, not any individual planet. If those houses "
                    "are mentioned, put them in a separate sentence beginning 'Taken together, this chain activates'. "
                    "Never say a planet placement provides, supports, creates, or links the other listed house activations. "
                    "Keep every fact explicitly marked current in the current-period explanation, before the first future window. "
                    "Mention every distinct required_material_window as a chronological stage when more than one is supplied. "
                    "Use dasha_level_terms exactly: an AD is a sub-period and a PD is a sub-sub-period; never call a PD the sub-period lord. "
                    "For career answers, prefer the supplied concrete manifestations over generic phrases such as "
                    "professional gains, responsibilities, stability, unconventional, or unsettled. Do not claim an "
                    "offer or joining date unless the contract explicitly supplies that layer."
                ),
            }
                if not exact_day and query_plan.get("answer_mode") == "event_prediction"
                else None
            ),
        "limitation_instruction": (
            "The evidence does not distinguish the named options. Do not favor, predict, or imply a winner. "
            "State that both remain open, name only the shared supported pressure/direction, and ask which "
            "real-life option is actually emerging."
            if verdict.get("direction") == "insufficient_option_evidence"
            else "The option scores are too close to justify a winner. Say it is a close call, give the distinct best window and activation logic for each option, and ask which path is becoming concrete in real life."
            if verdict.get("direction") == "close_call"
            else "No body-area evidence is available. Do not name an organ, body system, symptom, or recovery window. State only the supported general pressure and ask which area is actually troubling the user."
            if "parashari.health_body_area" in (verdict.get("missing_required_capabilities") or [])
            else None
        ),
    }


def verify_answer_spec(answer_spec: Dict[str, Any], ledger: Dict[str, Any]) -> Dict[str, Any]:
    known = {item.get("evidence_id") for item in ledger.get("records", [])}
    checks = []
    for claim in answer_spec.get("claims", []):
        refs = [ref for ref in claim.get("evidence_ids", []) if ref]
        missing = [ref for ref in refs if ref not in known]
        passed = bool(refs) and not missing
        checks.append({
            "claim_id": claim.get("claim_id"),
            "passed": passed,
            "evidence_ids": refs,
            "missing_evidence_ids": missing,
        })
    return {
        "schema_version": "instant-claim-verification/v1",
        "scope": "answer_spec_evidence_references",
        "passed": all(item["passed"] for item in checks) if checks else False,
        "checks": checks,
    }
