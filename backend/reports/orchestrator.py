from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from credits.credit_service import CreditService
from db import execute
from marriage_matching.engine import KundliMatchingEngine

from .assembly.page_assembler import assemble_partnership_pages, build_chart_manifest
from .assembly.pdf_manifest_builder import build_pdf_manifest
from .assembly.wealth_page_assembler import assemble_wealth_pages, build_wealth_chart_manifest
from .assembly.health_page_assembler import assemble_health_pages, build_health_chart_manifest
from .cache.report_hash import build_pair_hash, build_subject_hash, normalize_birth_data
from .cache.report_storage import get_cached_report, upsert_report_cache
from .context.base_context_builder import calculate_divisional_chart
from .context.partnership_context_builder import build_partnership_report_context
from .context.wealth_context_builder import build_wealth_report_context
from .context.health_context_builder import build_health_report_context
from .llm.report_llm_service import (
    generate_partnership_premium_report,
    generate_wealth_premium_report,
    generate_health_premium_report,
)
from .models import ReportDocument
from .report_types import PARTNERSHIP_REPORT_CONFIG, WEALTH_REPORT_CONFIG, HEALTH_REPORT_CONFIG
from .pdf_service import store_report_pdf


def _annotate_chart(chart: Any, person: Dict[str, Any]) -> Any:
    """Stamp native identity onto chart payloads so PDF labels cannot cross-wire."""
    if not isinstance(chart, dict):
        return chart
    annotated = dict(chart)
    annotated["_native_name"] = person.get("name")
    annotated["_native_date"] = person.get("date")
    annotated["_native_time"] = person.get("time")
    annotated["_native_place"] = person.get("place")
    inner = annotated.get("divisional_chart")
    if isinstance(inner, dict):
        nested = dict(inner)
        nested["_native_name"] = person.get("name")
        nested["_native_date"] = person.get("date")
        nested["_native_time"] = person.get("time")
        nested["_native_place"] = person.get("place")
        annotated["divisional_chart"] = nested
    return annotated


def _apply_document_cache_usage(cached: Dict[str, Any]) -> Dict[str, Any]:
    cached = dict(cached)
    original_usage = None
    premium = cached.get("premium_report") if isinstance(cached.get("premium_report"), dict) else {}
    if isinstance(cached.get("llm_usage"), dict):
        original_usage = cached.get("llm_usage")
    elif isinstance(premium.get("llm_usage"), dict):
        original_usage = premium.get("llm_usage")
    if isinstance(original_usage, dict) and not original_usage.get("document_cache_hit"):
        avoided = {
            "input_tokens": int(original_usage.get("input_tokens") or 0),
            "output_tokens": int(original_usage.get("output_tokens") or 0),
            "cached_input_tokens": int(original_usage.get("cached_input_tokens") or 0),
            "non_cached_input_tokens": int(original_usage.get("non_cached_input_tokens") or 0),
            "cache_setup_input_tokens": int(original_usage.get("cache_setup_input_tokens") or 0),
        }
        cache_hit_usage = {
            "model": original_usage.get("model") or "",
            "vendor": original_usage.get("vendor") or "",
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "non_cached_input_tokens": 0,
            "cache_setup_input_tokens": 0,
            "total_tokens": 0,
            "chapters_generated": 0,
            "chapters_from_db_cache": int(original_usage.get("chapters_generated") or 0)
            + int(original_usage.get("chapters_from_db_cache") or 0),
            "gemini_context_cache": False,
            "document_cache_hit": True,
            "avoided_by_chapter_cache": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_input_tokens": 0,
                "non_cached_input_tokens": 0,
            },
            "avoided_by_document_cache": avoided,
        }
        cached["llm_usage"] = cache_hit_usage
        if premium:
            premium = dict(premium)
            premium["llm_usage"] = cache_hit_usage
            cached["premium_report"] = premium
    return cached


async def build_and_cache_partnership_report(
    userid: int,
    request: Any,
    *,
    credit_service: CreditService,
    get_conn: Any,
    execute_fn=execute,
    report_id: str | None = None,
) -> Dict[str, Any]:
    pair_hash = build_pair_hash(request.boy_birth_data, request.girl_birth_data, request.report_type, request.language)
    report_version = PARTNERSHIP_REPORT_CONFIG.key + "_v6_nakshatra_nature"
    resolved_report_id = report_id or pair_hash[:16]
    effective_cost = credit_service.get_effective_cost(
        userid,
        credit_service.get_credit_setting("partnership_report_cost"),
        "partnership_report_cost",
    )

    if not request.force_regenerate:
        cached = get_cached_report(userid, request.report_type, pair_hash, request.language, report_version, get_conn, execute_fn)
        if cached:
            # Keep the cached PDF object as-is; only stamp the current job id for status/history.
            # Callers that need a new PDF must pass force_regenerate=true.
            # Cache hits are free — credits were already charged on first successful generate.
            cached = dict(cached)
            cached["report_id"] = resolved_report_id
            cached["cached"] = True
            cached["credits_charged"] = 0
            original_usage = None
            premium = cached.get("premium_report") if isinstance(cached.get("premium_report"), dict) else {}
            if isinstance(cached.get("llm_usage"), dict):
                original_usage = cached.get("llm_usage")
            elif isinstance(premium.get("llm_usage"), dict):
                original_usage = premium.get("llm_usage")
            if isinstance(original_usage, dict) and not original_usage.get("document_cache_hit"):
                avoided = {
                    "input_tokens": int(original_usage.get("input_tokens") or 0),
                    "output_tokens": int(original_usage.get("output_tokens") or 0),
                    "cached_input_tokens": int(original_usage.get("cached_input_tokens") or 0),
                    "non_cached_input_tokens": int(original_usage.get("non_cached_input_tokens") or 0),
                    "cache_setup_input_tokens": int(original_usage.get("cache_setup_input_tokens") or 0),
                }
                cache_hit_usage = {
                    "model": original_usage.get("model") or "",
                    "vendor": original_usage.get("vendor") or "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_input_tokens": 0,
                    "non_cached_input_tokens": 0,
                    "cache_setup_input_tokens": 0,
                    "total_tokens": 0,
                    "chapters_generated": 0,
                    "chapters_from_db_cache": int(original_usage.get("chapters_generated") or 0)
                    + int(original_usage.get("chapters_from_db_cache") or 0),
                    "gemini_context_cache": False,
                    "document_cache_hit": True,
                    "avoided_by_chapter_cache": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cached_input_tokens": 0,
                        "non_cached_input_tokens": 0,
                    },
                    "avoided_by_document_cache": avoided,
                }
                cached["llm_usage"] = cache_hit_usage
                if premium:
                    premium = dict(premium)
                    premium["llm_usage"] = cache_hit_usage
                    cached["premium_report"] = premium
            if not cached.get("pdf_gcs_path"):
                cached_pdf = store_report_pdf(cached)
                cached.update(cached_pdf)
                upsert_report_cache(
                    userid,
                    request.report_type,
                    pair_hash,
                    request.language,
                    report_version,
                    cached,
                    get_conn,
                    execute_fn,
                )
            return cached

    if credit_service.get_user_credits(userid) < effective_cost:
        return {"ok": False, "error": f"Insufficient credits. You need {effective_cost} credits."}

    context = build_partnership_report_context(request)
    engine = KundliMatchingEngine().analyze(
        context["boy_chart"],
        context["girl_chart"],
        context["person_a"],
        context["person_b"],
    )

    premium = await generate_partnership_premium_report(
        userid,
        context["boy_chart"],
        context["girl_chart"],
        context["person_a"],
        context["person_b"],
        language=context["language"],
        force_regenerate=bool(request.force_regenerate),
        effective_cost=effective_cost,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
        spend_on_success=False,
    )

    if not premium.get("ok"):
        return {"ok": False, "error": premium.get("error") or "Report generation failed"}

    faq_items = _build_faq_items(premium.get("report", {}), engine)

    report_payload = ReportDocument(
        report_id=resolved_report_id,
        report_type=request.report_type,
        language=context["language"],
        generated_at=datetime.now(),
        report_version=report_version,
        status="completed",
        pair={"boy": normalize_birth_data(request.boy_birth_data), "girl": normalize_birth_data(request.girl_birth_data)},
        score_summary={
            **(engine.get("overall_score") or {}),
            "ashtakoota": engine.get("ashtakoota") or {},
            "guna_milan": engine.get("ashtakoota") or {},
            "recommendation": engine.get("recommendation") or {},
            "timing_overlay": engine.get("timing_overlay") or {},
        },
        branch_payloads=context["branches"],
        pages=assemble_partnership_pages(
            {
                "pair": {"boy": normalize_birth_data(request.boy_birth_data), "girl": normalize_birth_data(request.girl_birth_data)},
                "chart_style": request.chart_style,
                "summaries": context.get("summaries", {}),
                "faq_items": faq_items,
            },
            premium.get("report", {}),
            engine,
        ),
        chart_manifest=build_chart_manifest({"chart_style": request.chart_style}),
        faq=faq_items,
        cta={"text": "Download the app or book a consultation."},
        premium_report=premium.get("report", {}),
        chart_data={
            "boy": _annotate_chart(context["boy_chart"], normalize_birth_data(request.boy_birth_data)),
            "girl": _annotate_chart(context["girl_chart"], normalize_birth_data(request.girl_birth_data)),
            "boy_d9": _annotate_chart(calculate_divisional_chart(context["boy_chart"], 9), normalize_birth_data(request.boy_birth_data)),
            "girl_d9": _annotate_chart(calculate_divisional_chart(context["girl_chart"], 9), normalize_birth_data(request.girl_birth_data)),
            "boy_d2": _annotate_chart(calculate_divisional_chart(context["boy_chart"], 2), normalize_birth_data(request.boy_birth_data)),
            "girl_d2": _annotate_chart(calculate_divisional_chart(context["girl_chart"], 2), normalize_birth_data(request.girl_birth_data)),
            "boy_d7": _annotate_chart(calculate_divisional_chart(context["boy_chart"], 7), normalize_birth_data(request.boy_birth_data)),
            "girl_d7": _annotate_chart(calculate_divisional_chart(context["girl_chart"], 7), normalize_birth_data(request.girl_birth_data)),
            "boy_d60": _annotate_chart(calculate_divisional_chart(context["boy_chart"], 60), normalize_birth_data(request.boy_birth_data)),
            "girl_d60": _annotate_chart(calculate_divisional_chart(context["girl_chart"], 60), normalize_birth_data(request.girl_birth_data)),
        },
        chart_style=("south" if getattr(request, "chart_style", "both") == "south" else "north"),
        cached=False,
    ).model_dump()

    report_payload["pdf_manifest"] = build_pdf_manifest(report_payload)
    report_payload.update(store_report_pdf(report_payload))

    if not credit_service.spend_credits(
        userid,
        effective_cost,
        "partnership_report",
        f"Partnership report for {normalize_birth_data(request.boy_birth_data).get('name', 'Person 1')} and {normalize_birth_data(request.girl_birth_data).get('name', 'Person 2')}",
    ):
        return {"ok": False, "error": "Credit deduction failed"}

    report_payload["credits_charged"] = int(effective_cost)
    premium_report = premium.get("report") if isinstance(premium.get("report"), dict) else {}
    if isinstance(premium_report.get("llm_usage"), dict):
        report_payload["llm_usage"] = premium_report["llm_usage"]

    upsert_report_cache(
        userid,
        request.report_type,
        pair_hash,
        request.language,
        report_version,
        report_payload,
        get_conn,
        execute_fn,
    )

    return report_payload


async def process_partnership_report_job(
    report_id: str,
    userid: int,
    request: Any,
    *,
    credit_service: CreditService,
    get_conn: Any,
    execute_fn=execute,
) -> Dict[str, Any]:
    return await build_and_cache_partnership_report(
        userid,
        request,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
        report_id=report_id,
    )


def _build_faq_items(premium_report: Dict[str, Any], engine: Dict[str, Any]) -> list[Dict[str, Any]]:
    sections = {section.get("key"): section for section in premium_report.get("sections", [])}
    qas = []
    questions = premium_report.get("follow_up_questions", []) or []

    for idx, question in enumerate(questions):
        q_lower = str(question).lower()
        if "timing" in q_lower or "when" in q_lower:
            answer = (
                sections.get("timing_and_marriage_windows", {}).get("decision_guidance")
                or engine.get("recommendation", {}).get("timing_note")
                or "Timing should be judged from the combined dasha and transit climate."
            )
        elif "remedies" in q_lower or "improve" in q_lower:
            answer = (
                sections.get("final_guidance_and_remedies", {}).get("decision_guidance")
                or "Use the remedies matched to the exact friction points rather than generic upayas."
            )
        elif "score" in q_lower:
            answer = (
                sections.get("ashtakoota_and_exceptions", {}).get("practical_meaning")
                or "The score is meaningful, but it should be read with exceptions, timing, and D9 support."
            )
        else:
            answer = (
                sections.get("overall_foundation", {}).get("practical_meaning")
                or engine.get("recommendation", {}).get("verdict")
                or "The answer depends on the combined chart evidence, not one factor alone."
            )
        qas.append({"question": question, "answer": answer})
    return qas


async def build_and_cache_wealth_report(
    userid: int,
    request: Any,
    *,
    credit_service: CreditService,
    get_conn: Any,
    execute_fn=execute,
    report_id: str | None = None,
) -> Dict[str, Any]:
    subject_hash = build_subject_hash(request.birth_data, request.report_type, request.language)
    report_version = WEALTH_REPORT_CONFIG.key + "_v1"
    resolved_report_id = report_id or subject_hash[:16]
    effective_cost = credit_service.get_effective_cost(
        userid,
        credit_service.get_credit_setting("wealth_report_cost"),
        "wealth_report_cost",
    )

    if not request.force_regenerate:
        cached = get_cached_report(
            userid, request.report_type, subject_hash, request.language, report_version, get_conn, execute_fn
        )
        if cached:
            cached = _apply_document_cache_usage(cached)
            cached["report_id"] = resolved_report_id
            cached["cached"] = True
            cached["credits_charged"] = 0
            if not cached.get("pdf_gcs_path"):
                cached_pdf = store_report_pdf(cached)
                cached.update(cached_pdf)
                upsert_report_cache(
                    userid,
                    request.report_type,
                    subject_hash,
                    request.language,
                    report_version,
                    cached,
                    get_conn,
                    execute_fn,
                )
            return cached

    if credit_service.get_user_credits(userid) < effective_cost:
        return {"ok": False, "error": f"Insufficient credits. You need {effective_cost} credits."}

    context = build_wealth_report_context(request)
    person = normalize_birth_data(request.birth_data)

    premium = await generate_wealth_premium_report(
        userid,
        context,
        language=context["language"],
        force_regenerate=bool(request.force_regenerate),
        effective_cost=effective_cost,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
        spend_on_success=False,
    )
    if not premium.get("ok"):
        return {"ok": False, "error": premium.get("error") or "Wealth report generation failed"}

    wealth = context.get("wealth") or {}
    dashas = context.get("current_dashas") or {}
    faq_items = [
        {"question": q, "answer": "See the timing and action chapters in this report."}
        for q in (premium.get("report") or {}).get("follow_up_questions") or []
    ]

    report_payload = ReportDocument(
        report_id=resolved_report_id,
        report_type=request.report_type,
        language=context["language"],
        generated_at=datetime.now(),
        report_version=report_version,
        status="completed",
        pair={"native": person, "boy": person},
        score_summary={
            "wealth_score": wealth.get("wealth_score"),
            "grade": wealth.get("wealth_score"),
            "verdict": (premium.get("report") or {}).get("wealth_verdict"),
            "px_wealth": context.get("px_wealth") or {},
            "current_dashas": {
                "mahadasha": (dashas.get("mahadasha") or {}).get("planet"),
                "antardasha": (dashas.get("antardasha") or {}).get("planet"),
                "pratyantardasha": (dashas.get("pratyantardasha") or {}).get("planet"),
            },
            "twelve_month_dasha": context.get("twelve_month_dasha") or [],
        },
        branch_payloads=context.get("branches") or {},
        pages=assemble_wealth_pages(
            {
                "person": person,
                "chart_style": request.chart_style,
                "wealth": wealth,
                "current_dashas": dashas,
                "twelve_month_dasha": context.get("twelve_month_dasha") or [],
                "px_wealth": context.get("px_wealth") or {},
                "lords_nakshatra": context.get("lords_nakshatra") or {},
                "trading_luck": context.get("trading_luck") or {},
                "indu_lagna": context.get("indu_lagna"),
            },
            premium.get("report") or {},
        ),
        chart_manifest=build_wealth_chart_manifest({"chart_style": request.chart_style}),
        faq=faq_items,
        cta={"text": "Download the app or book a consultation."},
        premium_report=premium.get("report") or {},
        chart_data={
            "boy": _annotate_chart(context["chart"], person),
            "native": _annotate_chart(context["chart"], person),
            "boy_d2": _annotate_chart(context.get("d2_chart"), person),
            "native_d2": _annotate_chart(context.get("d2_chart"), person),
            "boy_d9": _annotate_chart(context.get("d9_chart"), person),
            "native_d9": _annotate_chart(context.get("d9_chart"), person),
            "native_d10": _annotate_chart(context.get("d10_chart"), person),
            "boy_d10": _annotate_chart(context.get("d10_chart"), person),
        },
        chart_style=("south" if getattr(request, "chart_style", "both") == "south" else "north"),
        cached=False,
    ).model_dump()

    report_payload["pdf_manifest"] = build_pdf_manifest(report_payload)
    report_payload.update(store_report_pdf(report_payload))

    if not credit_service.spend_credits(
        userid,
        effective_cost,
        "wealth_report",
        f"Wealth report for {person.get('name') or 'native'}",
    ):
        return {"ok": False, "error": "Credit deduction failed"}

    report_payload["credits_charged"] = int(effective_cost)
    premium_report = premium.get("report") if isinstance(premium.get("report"), dict) else {}
    if isinstance(premium_report.get("llm_usage"), dict):
        report_payload["llm_usage"] = premium_report["llm_usage"]

    upsert_report_cache(
        userid,
        request.report_type,
        subject_hash,
        request.language,
        report_version,
        report_payload,
        get_conn,
        execute_fn,
    )
    return report_payload


async def process_wealth_report_job(
    report_id: str,
    userid: int,
    request: Any,
    *,
    credit_service: CreditService,
    get_conn: Any,
    execute_fn=execute,
) -> Dict[str, Any]:
    return await build_and_cache_wealth_report(
        userid,
        request,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
        report_id=report_id,
    )


async def build_and_cache_health_report(
    userid: int,
    request: Any,
    *,
    credit_service: CreditService,
    get_conn: Any,
    execute_fn=execute,
    report_id: str | None = None,
) -> Dict[str, Any]:
    subject_hash = build_subject_hash(request.birth_data, request.report_type, request.language)
    report_version = HEALTH_REPORT_CONFIG.key + "_v1"
    resolved_report_id = report_id or subject_hash[:16]
    effective_cost = credit_service.get_effective_cost(
        userid,
        credit_service.get_credit_setting("health_report_cost"),
        "health_report_cost",
    )

    if not request.force_regenerate:
        cached = get_cached_report(
            userid, request.report_type, subject_hash, request.language, report_version, get_conn, execute_fn
        )
        if cached:
            cached = _apply_document_cache_usage(cached)
            cached["report_id"] = resolved_report_id
            cached["cached"] = True
            cached["credits_charged"] = 0
            if not cached.get("pdf_gcs_path"):
                cached_pdf = store_report_pdf(cached)
                cached.update(cached_pdf)
                upsert_report_cache(
                    userid,
                    request.report_type,
                    subject_hash,
                    request.language,
                    report_version,
                    cached,
                    get_conn,
                    execute_fn,
                )
            return cached

    if credit_service.get_user_credits(userid) < effective_cost:
        return {"ok": False, "error": f"Insufficient credits. You need {effective_cost} credits."}

    context = build_health_report_context(request)
    person = normalize_birth_data(request.birth_data)

    premium = await generate_health_premium_report(
        userid,
        context,
        language=context["language"],
        force_regenerate=bool(request.force_regenerate),
        effective_cost=effective_cost,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
        spend_on_success=False,
    )
    if not premium.get("ok"):
        return {"ok": False, "error": premium.get("error") or "Health report generation failed"}

    health = context.get("health") or {}
    dashas = context.get("current_dashas") or {}
    faq_items = [
        {"question": q, "answer": "See the timing and action chapters in this report."}
        for q in (premium.get("report") or {}).get("follow_up_questions") or []
    ]

    report_payload = ReportDocument(
        report_id=resolved_report_id,
        report_type=request.report_type,
        language=context["language"],
        generated_at=datetime.now(),
        report_version=report_version,
        status="completed",
        pair={"native": person, "boy": person},
        score_summary={
            "health_score": health.get("health_score"),
            "grade": health.get("health_score"),
            "constitution_type": health.get("constitution_type"),
            "verdict": (premium.get("report") or {}).get("health_verdict"),
            "medical_disclaimer": context.get("medical_disclaimer"),
            "health_agent": context.get("health_agent") or {},
            "current_dashas": {
                "mahadasha": (dashas.get("mahadasha") or {}).get("planet"),
                "antardasha": (dashas.get("antardasha") or {}).get("planet"),
                "pratyantardasha": (dashas.get("pratyantardasha") or {}).get("planet"),
            },
            "twelve_month_dasha": context.get("twelve_month_dasha") or [],
            "priority_body_zones": (context.get("body_zone_map") or {}).get("top_zone_names") or [],
            "health_event_patterns": [
                p.get("key") for p in ((context.get("body_zone_map") or {}).get("event_patterns") or [])
            ],
        },
        branch_payloads=context.get("branches") or {},
        pages=assemble_health_pages(
            {
                "person": person,
                "chart_style": request.chart_style,
                "health": health,
                "health_agent": context.get("health_agent") or {},
                "medical_disclaimer": context.get("medical_disclaimer"),
                "current_dashas": dashas,
                "twelve_month_dasha": context.get("twelve_month_dasha") or [],
                "lords_nakshatra": context.get("lords_nakshatra") or {},
                "planet_system_ranks": context.get("planet_system_ranks") or [],
                "attention_houses": context.get("attention_houses") or [],
                "body_zone_map": context.get("body_zone_map") or {},
                "vitality_analysis": context.get("vitality_analysis") or {},
                "d30_analysis": context.get("d30_analysis") or {},
            },
            premium.get("report") or {},
        ),
        chart_manifest=build_health_chart_manifest({"chart_style": request.chart_style}),
        faq=faq_items,
        cta={"text": "Download the app or book a consultation."},
        premium_report=premium.get("report") or {},
        chart_data={
            "boy": _annotate_chart(context["chart"], person),
            "native": _annotate_chart(context["chart"], person),
            "boy_d9": _annotate_chart(context.get("d9_chart"), person),
            "native_d9": _annotate_chart(context.get("d9_chart"), person),
            "native_d30": _annotate_chart(context.get("d30_chart"), person),
            "boy_d30": _annotate_chart(context.get("d30_chart"), person),
        },
        chart_style=("south" if getattr(request, "chart_style", "both") == "south" else "north"),
        cached=False,
    ).model_dump()

    report_payload["pdf_manifest"] = build_pdf_manifest(report_payload)
    report_payload.update(store_report_pdf(report_payload))

    if not credit_service.spend_credits(
        userid,
        effective_cost,
        "health_report",
        f"Health report for {person.get('name') or 'native'}",
    ):
        return {"ok": False, "error": "Credit deduction failed"}

    report_payload["credits_charged"] = int(effective_cost)
    premium_report = premium.get("report") if isinstance(premium.get("report"), dict) else {}
    if isinstance(premium_report.get("llm_usage"), dict):
        report_payload["llm_usage"] = premium_report["llm_usage"]

    upsert_report_cache(
        userid,
        request.report_type,
        subject_hash,
        request.language,
        report_version,
        report_payload,
        get_conn,
        execute_fn,
    )
    return report_payload


async def process_health_report_job(
    report_id: str,
    userid: int,
    request: Any,
    *,
    credit_service: CreditService,
    get_conn: Any,
    execute_fn=execute,
) -> Dict[str, Any]:
    return await build_and_cache_health_report(
        userid,
        request,
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
        report_id=report_id,
    )