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
    if query_plan.get("category") == "health":
        health_record = next(
            (item for item in ledger.get("records", []) if item.get("kind") == "health_body_area"),
            None,
        )
        health_value = (health_record or {}).get("value")
        priority_zones = health_value.get("priority_zones") if isinstance(health_value, dict) else []
        allowed_zones = [
            str(item.get("zone") or "").strip()
            for item in (priority_zones or [])[:5]
            if isinstance(item, dict) and str(item.get("zone") or "").strip()
        ]
        if health_record and allowed_zones:
            claims.append({
                "claim_id": "claim-health-body-area",
                "purpose": "Name only the explicitly calculated susceptibility zones",
                "evidence_ids": [health_record.get("evidence_id")],
                "required": True,
            })
        health_rules = {
            "allowed_zone_names": allowed_zones,
            "medical_framing": "Astrological susceptibility only; never a diagnosis or prediction of illness.",
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
        }
    answer_mode = str(query_plan.get("answer_mode") or "topic_reading")
    if answer_mode == "factual_chart_lookup":
        max_words, word_target = 140, "Usually 30-100 words; add only the context needed to identify the chart/system."
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
    return {
        "schema_version": "instant-answer-spec/v1",
        "tone": "natural, concise, daily-use language",
        "max_words": max_words,
        "composer_word_target": word_target,
        "answer_order": daily_rules.get("answer_order") if daily_rules else ["direct_answer", "one_chart_reason", "one_caution_if_material", "natural_follow_up_question"],
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
