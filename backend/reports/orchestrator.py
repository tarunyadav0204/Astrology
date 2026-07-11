from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from credits.credit_service import CreditService
from db import execute
from marriage_matching.engine import KundliMatchingEngine

from .assembly.page_assembler import assemble_partnership_pages, build_chart_manifest
from .assembly.pdf_manifest_builder import build_pdf_manifest
from .cache.report_hash import build_pair_hash, normalize_birth_data
from .cache.report_storage import get_cached_report, upsert_report_cache
from .context.base_context_builder import calculate_divisional_chart
from .context.partnership_context_builder import build_partnership_report_context
from .llm.report_llm_service import generate_partnership_premium_report
from .models import ReportDocument
from .report_types import PARTNERSHIP_REPORT_CONFIG
from .pdf_service import store_report_pdf


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
    report_version = PARTNERSHIP_REPORT_CONFIG.key + "_v1"
    resolved_report_id = report_id or pair_hash[:16]

    if not request.force_regenerate:
        cached = get_cached_report(userid, request.report_type, pair_hash, request.language, report_version, get_conn, execute_fn)
        if cached:
            cached["report_id"] = resolved_report_id
            cached["cached"] = True
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
        effective_cost=credit_service.get_effective_cost(
            userid,
            credit_service.get_credit_setting("marriage_analysis_cost"),
            "marriage_analysis_cost",
        ),
        credit_service=credit_service,
        get_conn=get_conn,
        execute_fn=execute_fn,
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
        score_summary=engine.get("overall_score", {}),
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
            "boy": context["boy_chart"],
            "girl": context["girl_chart"],
            "boy_d9": calculate_divisional_chart(context["boy_chart"], 9),
            "girl_d9": calculate_divisional_chart(context["girl_chart"], 9),
        },
        cached=False,
    ).model_dump()

    report_payload["pdf_manifest"] = build_pdf_manifest(report_payload)
    report_payload.update(store_report_pdf(report_payload))

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
