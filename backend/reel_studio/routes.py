"""The first production boundary for Reel Studio.

This router intentionally creates a deterministic *render plan*, not an MP4.  A
renderer can consume the returned scenes without being allowed to change chart
claims, and its actual provider usage is written back through the cost-event
endpoint.  Keeping planning and measured spend separate lets us learn the real
unit economics before committing to a video provider.
"""
from __future__ import annotations

import re
import uuid
import os
import json
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn
from reel_studio.text import plain_text
from reel_studio.billing import (
    REEL_DEEP_DURATION_SECONDS,
    REEL_SHORT_DURATION_SECONDS,
    charge_reel,
    reel_pricing,
)

router = APIRouter(prefix="/reel-studio", tags=["reel-studio"])

DEFAULT_BASE_COSTS_INR = {
    "analysis": 2.0,
    "validation": 1.0,
    "tts": 6.0,
    "chart_animation": 3.0,
    "captions_and_render": 6.0,
    "retry_allowance": 6.0,
}
# Gemini Omni Flash video is presently about USD 0.10/s. This is a planning
# estimate at the current USD/INR budget rate, not a provider invoice.
VIDEO_COST_PER_SECOND_INR = {"none": 0.0, "hybrid": 9.65, "cinematic": 9.65}
OMNI_VIDEO_ENABLED = os.getenv("REEL_ENABLE_OMNI_VIDEO", "false").strip().lower() in {"1", "true", "yes", "on"}
_VISUAL_MODULES = {
    "opening", "chart_focus", "evidence_card", "dasha_stack", "timing_window",
    "transit_overlay", "ashtakavarga", "support_caution", "lifestyle_image", "closing",
}
_SIGN_NAMES = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_OMNI_VIDEO_TOKEN_INR = 17.50 * 95 / 1_000_000
_OMNI_INPUT_TOKEN_INR = 1.50 * 95 / 1_000_000
_OMNI_THOUGHT_TOKEN_INR = 9.00 * 95 / 1_000_000


def _recovered_video_cost(metadata: dict) -> float:
    """Recover legacy Omni cost from its stored Interaction API usage payload."""
    usage = (metadata or {}).get("usage") or {}
    rows = usage.get("output_tokens_by_modality") or []
    video_tokens = 0.0
    for row in rows:
        if str(row.get("modality") or "").lower() == "video":
            try: video_tokens = float(row.get("tokens") or 0)
            except (TypeError, ValueError): pass
    for key in ("video_output_tokens", "output_video_tokens", "total_output_tokens", "output_tokens"):
        if video_tokens:
            break
        try:
            value = float(usage.get(key) or 0)
            if value: video_tokens = value
        except (TypeError, ValueError): pass
    def token(name: str) -> float:
        try: return float(usage.get(name) or 0)
        except (TypeError, ValueError): return 0.0
    input_tokens = token("total_input_tokens") or token("input_tokens")
    thought_tokens = token("total_thought_tokens") or token("thought_tokens")
    return video_tokens * _OMNI_VIDEO_TOKEN_INR + input_tokens * _OMNI_INPUT_TOKEN_INR + thought_tokens * _OMNI_THOUGHT_TOKEN_INR


class DraftRequest(BaseModel):
    message_id: int
    duration_seconds: Literal[REEL_SHORT_DURATION_SECONDS, REEL_DEEP_DURATION_SECONDS] = REEL_SHORT_DURATION_SECONDS
    language: Literal["en", "hi"] = "en"
    visual_level: Literal["none", "hybrid", "cinematic"] = "none"
    brand_name: str = Field(default="AstroRoshni", max_length=80)


class CostEventRequest(BaseModel):
    run_id: str = Field(min_length=8, max_length=64)
    stage: Literal["analysis", "validation", "tts", "image", "video", "render", "storage"]
    provider: str = Field(min_length=1, max_length=80)
    units: float = Field(ge=0, le=100000)
    unit_cost_inr: float = Field(ge=0, le=100000)
    metadata: dict = Field(default_factory=dict)


class RenderRequest(DraftRequest):
    """An explicitly approved plan to be consumed by the render worker."""
    draft_id: str = Field(min_length=8, max_length=80)
    approved_claim_ids: list[str] = Field(min_length=1, max_length=24)
    confirmed_credit_cost: int = Field(ge=0)


def _ensure_tables(conn) -> None:
    execute(conn, """
        CREATE TABLE IF NOT EXISTS reel_generation_costs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            run_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            provider TEXT NOT NULL,
            units DOUBLE PRECISION NOT NULL,
            unit_cost_inr DOUBLE PRECISION NOT NULL,
            total_cost_inr DOUBLE PRECISION NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(conn, """
        CREATE TABLE IF NOT EXISTS reel_render_jobs (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            source_message_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            output_url TEXT,
            error_message TEXT,
            task_claim_id TEXT,
            task_claimed_until TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(conn, """
        CREATE TABLE IF NOT EXISTS reel_storyboard_drafts (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            source_message_id INTEGER NOT NULL,
            plan_json TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(conn, """
        CREATE INDEX IF NOT EXISTS reel_generation_costs_user_run_idx
        ON reel_generation_costs (user_id, run_id, created_at)
    """)
    execute(conn, "ALTER TABLE reel_render_jobs ADD COLUMN IF NOT EXISTS task_claim_id TEXT")
    execute(conn, "ALTER TABLE reel_render_jobs ADD COLUMN IF NOT EXISTS task_claimed_until TIMESTAMP")
    execute(conn, """
        CREATE INDEX IF NOT EXISTS reel_render_jobs_worker_claim_idx
        ON reel_render_jobs (status, task_claimed_until, created_at)
    """)


def _answer_for_user(message_id: int, user_id: int) -> tuple[str, int | None, str]:
    with get_conn() as conn:
        row = execute(conn, """
            SELECT cm.content, cs.birth_chart_id,
              COALESCE((SELECT prior.content FROM chat_messages prior
                WHERE prior.session_id=cm.session_id AND prior.sender='user' AND prior.message_id < cm.message_id
                ORDER BY prior.message_id DESC LIMIT 1), '')
            FROM chat_messages cm
            JOIN chat_sessions cs ON cs.session_id = cm.session_id
            WHERE cm.message_id = %s AND cm.sender = 'assistant' AND cs.user_id = %s
            LIMIT 1
        """, (message_id, user_id)).fetchone()
    if not row or not str(row[0] or "").strip():
        raise HTTPException(status_code=404, detail="A completed answer for this chart was not found.")
    return str(row[0]), (int(row[1]) if row[1] is not None else None), str(row[2] or "")


def _chart_snapshot(chart_id: int | None, user_id: int) -> dict | None:
    """Create a privacy-safe, deterministic visual source for the reel.

    The reel deliberately stores placements, dasha dates, and only a coarse
    visual-presentation value; it never stores the person's name, date of
    birth, time, coordinates, or place of birth.
    """
    if not chart_id:
        return None
    try:
        from prediction_engine.routes import _load_owned_birth_chart
        from calculators.chart_calculator import ChartCalculator
        from shared.dasha_calculator import DashaCalculator
        from calculators.ashtakavarga import AshtakavargaCalculator
        from calculators.real_transit_calculator import RealTransitCalculator
        from reel_studio.visual_graph import build_visual_graph

        birth = _load_owned_birth_chart(chart_id, user_id)
        chart = ChartCalculator({}).calculate_chart(type("Birth", (), birth)())
        dashas = DashaCalculator().calculate_current_dashas(birth)
        placements = []
        for planet, value in (chart.get("planets") or {}).items():
            if planet not in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}:
                continue
            longitude = float(value.get("longitude") or 0)
            sign_index = int(longitude // 30) % 12
            placements.append({
                "planet": planet,
                "house": int(value.get("house") or 0),
                # Reel plans use display-safe zodiac values only. Internal
                # zero-based sign indexes must never be sent to an image model.
                "rashi_number": sign_index + 1,
                "rashi_name": _SIGN_NAMES[sign_index],
                "degree_in_sign": round(longitude % 30, 1),
            })
        raw_sav = (AshtakavargaCalculator(dict(birth), chart).calculate_sarvashtakavarga() or {}).get("sarvashtakavarga") or {}
        asc = int(float(chart.get("ascendant") or 0) // 30) % 12
        gender = str(birth.get("gender") or "").strip().lower()
        presentation = "female" if gender in {"female", "woman", "f"} else "male" if gender in {"male", "man", "m"} else "unspecified"
        snapshot = {
            "chart_id": chart_id,
            "native_presentation": presentation,
            "ascendant_sign": int(float(chart.get("ascendant") or 0) // 30),
            "placements": placements,
            "current_dashas": {
                level: {key: value for key, value in (dashas.get(level) or {}).items() if key in {"planet", "start", "end"}}
                for level in ("mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana")
            },
            "ashtakavarga": {"sav_by_house": {str(h): int(raw_sav.get(str((asc + h - 1) % 12), raw_sav.get((asc + h - 1) % 12, 0))) for h in range(1, 13)}},
        }
        as_of = datetime.now(timezone.utc)
        profile = birth.get("calculation_profile") or {}
        transit_calculator = RealTransitCalculator(profile.get("ayanamsha", "lahiri"), profile.get("node_type", "mean"))
        transits = {planet: transit_calculator.get_planet_state(as_of, planet, exact_time=True)
                    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")}
        snapshot["visual_graph"] = build_visual_graph(snapshot, transits, as_of.isoformat())
        return snapshot
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Verified reel evidence could not be calculated: {str(exc)[:180]}")


def _clean_text(value: str) -> str:
    return plain_text(value)


def _sentences(value: str) -> list[str]:
    items = re.split(r"(?<=[.!?।])\s+", _clean_text(value))
    return [item.strip() for item in items if len(item.strip()) > 18]


def _scene_kind(sentence: str) -> str:
    lower = sentence.lower()
    if any(token in lower for token in ("dasha", "period", "transit", "timing", "timeline")):
        return "dasha_timeline"
    if any(token in lower for token in ("house", "lagna", "ascendant", "navamsha", "chart")):
        return "chart_focus"
    if any(token in lower for token in ("mercury", "venus", "jupiter", "saturn", "mars", "moon", "sun", "rahu", "ketu")):
        return "planet_focus"
    return "insight"


def _extract_claims(answer: str, max_claims: int = 24) -> list[dict]:
    claims = []
    for index, sentence in enumerate(_sentences(answer)[:max_claims]):
        factual = bool(re.search(r"\b(house|lord|placed|ascendant|lagna|dasha|transit|navamsha)\b", sentence, re.I))
        claims.append({
            "id": f"claim_{index + 1}",
            "text": sentence,
            "status": "needs_chart_validation" if factual else "interpretation",
            "type": "chart_fact" if factual else "interpretation",
        })
    if not claims:
        raise HTTPException(status_code=422, detail="The answer has no complete claims that can be directed into a reel.")
    return claims


def _cost_projection(duration: int, visual_level: str) -> dict:
    # This edit is intentionally narrator-led rather than avatar-led. It does
    # not generate a presenter video or a presenter image.
    video_seconds = 0
    base = sum(DEFAULT_BASE_COSTS_INR.values())
    video = VIDEO_COST_PER_SECOND_INR[visual_level] * video_seconds
    min_scenes, _ = _scene_count_range(duration)
    # The dynamic planner creates a format-specific number of images. Every scene uses GPT Image's
    # low-quality 9:16 tier; the worker records the exact final scene count.
    image = round(min_scenes * (0.005 * 1.1875 * 95), 2) if visual_level != "none" else 0.0
    total = round(base + video + image, 2)
    return {
        "currency": "INR",
        "estimated_total": total,
        "line_items": [
            {"label": label.replace("_", " ").title(), "estimated_inr": cost}
            for label, cost in DEFAULT_BASE_COSTS_INR.items()
        ] + ([{"label": f"{video_seconds}s generated video", "estimated_inr": round(video, 2)}] if video else [])
          + ([{"label": f"Minimum {min_scenes}-scene LLM image plan: all low-quality images (9:16)", "estimated_inr": image}] if image else []),
        "assumptions": {
            "duration_seconds": duration,
            "generated_video_seconds": video_seconds,
            "retry_allowance_included": DEFAULT_BASE_COSTS_INR["retry_allowance"],
        },
    }


def _scene_count_range(duration_seconds: int) -> tuple[int, int]:
    return (8, 10) if int(duration_seconds) == REEL_SHORT_DURATION_SECONDS else (12, 18)


def _planned_beats(answer: str, question: str, claims: list[dict], snapshot: dict | None, language: str, duration_seconds: int) -> list[dict]:
    """Text model directs the creative edit; rendering remains fact-bound."""
    answer = plain_text(answer)
    def complete_line(value: object) -> str | None:
        text = _clean_text(str(value or ""))
        # Never replace failed direction with a generic line: that creates a
        # pretty reel which says nothing about the user's actual answer.
        if not text:
            return None
        return text if text.endswith((".", "!", "?", "।")) else f"{text}."
    if not question.strip():
        raise HTTPException(status_code=422, detail="The originating user question is missing, so an answer-specific reel cannot be directed.")
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="Reel direction is unavailable: the text planner is not configured.")
    graph = (snapshot or {}).get("visual_graph") or {"nodes": [], "edges": []}
    source = {"placements": (snapshot or {}).get("placements", []), "dashas": (snapshot or {}).get("current_dashas", {}), "ashtakavarga": (snapshot or {}).get("ashtakavarga", {}), "visual_graph": graph}
    min_beats, max_beats = _scene_count_range(duration_seconds)
    output_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["beats"],
        "properties": {
            "beats": {
                "type": "array", "minItems": min_beats, "maxItems": max_beats,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["type", "narration", "pause_after", "evidence_ids", "visual_instruction", "focus_nodes", "draw_edges"],
                    "properties": {
                        "type": {"type": "string", "minLength": 1},
                        "narration": {"type": "string", "minLength": 1},
                        "pause_after": {"type": "string", "enum": ["none", "short", "medium", "long"]},
                        "evidence_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
                        "visual_instruction": {"type": "string"},
                        "focus_nodes": {"type": "array", "items": {"type": "string"}},
                        "draw_edges": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    }
    language_instruction = (
        "REEL LANGUAGE: Hindi (Devanagari). Write every narration and visual instruction in natural, fluent Hindi. "
        "Translate the approved answer faithfully; do not merely transliterate English."
        if language == "hi" else
        "REEL LANGUAGE: English. Write every narration and visual instruction in natural, fluent English."
    )
    prompt = f'''Return JSON only: {{"beats":[{{"type":"", "narration":"", "pause_after":"short", "evidence_ids":[], "visual_instruction":"", "focus_nodes":[], "draw_edges":[]}}]}}.
Write a detailed {duration_seconds}-second premium vertical reel plan that ANSWERS THE USER'S ACTUAL QUESTION and explains why the approved answer reaches that conclusion. Do not make a generic astrology reel. Select {min_beats} to {max_beats} beats from these supported visual modules only: {sorted(_VISUAL_MODULES)}. Choose modules that fit the answer; do not force chart, dasha, Ashtakavarga, transit, or timing scenes when the evidence does not support them. Use opening first and closing last. Write complete, naturally spoken passages. The combined narration MUST contain between {round(duration_seconds * 2.35)} and {round(duration_seconds * 2.5)} words for a calm podcast pace. Never cut a sentence, use ellipses, or repeat a closing/thank-you line. Every beat must include a concrete visual_instruction describing the desired image. Set pause_after to none, short, medium, or long to direct the silence between this beat and the next: use none when the next beat continues the same thought; use short for ordinary sentence transitions; use medium or long only after a complete conclusion, important shift, or final line. Never use a pause within an unfinished sentence. Every beat must include a concrete visual_instruction describing the desired image. For chart_focus, select relevant verified focus nodes and arrows when the graph has them. For lifestyle_image, describe a real-life scene tied to the answer. All images are created by GPT Image from this directed data; no visual may introduce a fact outside the approved claims or VERIFIED VISUAL DATA. EVIDENCE RULE: every beat's evidence_ids must be a non-empty array containing only exact id values from the CLAIMS list below. Never create a new claim ID and never leave evidence_ids empty.
Use plain text for narration and all visible image labels. Strip Markdown syntax from source copy: a heading such as 'Key Insights' must never include hash, asterisk, or backtick formatting markers.
{language_instruction}
USER QUESTION: {question[:2000]}
APPROVED ANSWER: {answer[:9000]}
CLAIMS: {json.dumps(claims, ensure_ascii=False)}
VERIFIED VISUAL DATA: {json.dumps(source, ensure_ascii=False)}'''
    try:
        from openai import OpenAI
        response = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=45).responses.create(
            model=os.getenv("REEL_PLANNER_MODEL", "gpt-5.6-luna"), input=prompt, store=False,
            text={"format": {"type": "json_schema", "name": "reel_plan", "strict": True, "schema": output_schema}}, max_output_tokens=3600)
        generated = json.loads(response.output_text).get("beats")
        if not isinstance(generated, list) or not min_beats <= len(generated) <= max_beats:
            raise ValueError(f"The director must return {min_beats} to {max_beats} complete beats.")
        valid_ids = {c["id"] for c in claims}
        node_ids = {str(node.get("id")) for node in graph.get("nodes", [])}
        edge_ids = {str(edge.get("id")) for edge in graph.get("edges", [])}
        beats = []
        for i, item in enumerate(generated):
            if not isinstance(item, dict):
                raise ValueError(f"Beat {i + 1} is not an object.")
            if item.get("type") not in _VISUAL_MODULES:
                raise ValueError(f"Beat {i + 1} has an unsupported visual module.")
            narration = complete_line(item.get("narration"))
            if not narration:
                raise ValueError(f"Beat {i + 1} is not a complete short sentence.")
            pause_after = str(item.get("pause_after") or "").strip().lower()
            if pause_after not in {"none", "short", "medium", "long"}:
                raise ValueError(f"Beat {i + 1} has an invalid transition pause.")
            visual_instruction = _clean_text(str(item.get("visual_instruction") or ""))
            if not visual_instruction:
                raise ValueError(f"Beat {i + 1} has no visual direction.")
            focus_nodes = [str(x) for x in item.get("focus_nodes", [])]
            draw_edges = [str(x) for x in item.get("draw_edges", [])]
            if any(node not in node_ids for node in focus_nodes) or any(edge not in edge_ids for edge in draw_edges):
                raise ValueError(f"Beat {i + 1} references evidence that is not in the verified graph.")
            ids = [str(x) for x in item.get("evidence_ids", []) if str(x) in valid_ids]
            if not ids:
                raise ValueError(f"Beat {i + 1} is not grounded in an approved claim.")
            beats.append({"id": f"beat_{i + 1}", "start_seconds": 0, "end_seconds": 0,
                          "type": str(item["type"]), "narrator": "podcast",
                          "narration": narration, "pause_after": pause_after, "visual_instruction": visual_instruction,
                          "focus_nodes": focus_nodes, "draw_edges": draw_edges, "evidence_ids": ids})
        for beat in beats:
            if beat["type"] == "chart_focus" and graph.get("nodes") and (not beat["focus_nodes"] or not beat["draw_edges"]):
                raise ValueError("Every chart-focus scene must select verified nodes and at least one verified arrow.")
        total_words = sum(len(beat["narration"].split()) for beat in beats)
        if total_words > 900:
            raise ValueError("The director returned more than 900 spoken words; split this reading into separate reels.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Reel direction failed validation: {str(exc)[:180]}")
    cursor = 0.0
    for beat in beats:
        # This is only a planning estimate; the renderer measures the actual
        # TTS MP3 and never cuts speech to make it fit a template.
        pause_seconds = {"none": 0.0, "short": 0.35, "medium": 0.6, "long": 0.9}[beat["pause_after"]]
        seconds = max(2.0, len(beat["narration"].split()) / 2.5 + pause_seconds)
        beat["start_seconds"] = round(cursor, 1)
        cursor += seconds
        beat["end_seconds"] = round(cursor, 1)
    return beats


def _draft_payload(request: DraftRequest, user_id: int) -> dict:
    answer, chart_id, question = _answer_for_user(request.message_id, user_id)
    chart_snapshot = _chart_snapshot(chart_id, user_id)
    claims = _extract_claims(answer)
    scenes = _planned_beats(answer, question, claims, chart_snapshot, request.language, request.duration_seconds)
    return {
        "run_id": f"reel_{uuid.uuid4().hex}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {"message_id": request.message_id, "birth_chart_id": chart_id, "kind": "chat_answer", "question": question},
        "chart_snapshot": chart_snapshot,
        "premium_readiness": {
            "real_chart": bool(chart_snapshot),
            "presenter": False,
            "generated_lifestyle_broll": request.visual_level in {"hybrid", "cinematic"},
            "note": "The final reel uses chart and dasha source images transformed into editorial 9:16 visuals, deterministic astrology inserts, and generated live-action b-roll. Uploaded licensed b-roll can replace generated b-roll in a later pass.",
        },
        "settings": request.model_dump(),
        "claims": claims,
        "storyboard": scenes,
        "estimated_duration_seconds": scenes[-1]["end_seconds"] if scenes else 0,
        "creative_plan": {"planner": "text-model-with-gpt-image-rendering", "beat_count": len(scenes)},
        "cost_projection": _cost_projection(request.duration_seconds, request.visual_level),
        "approval_required": True,
        "privacy_note": "Client identifiers and birth details are excluded from the reel plan; only a coarse visual-presentation value is retained to avoid depicting the native as a different gender.",
    }


@router.post("/drafts/from-answer")
def create_draft(request: DraftRequest, current_user: User = Depends(get_current_user)):
    quote = reel_pricing(current_user.userid, request.duration_seconds)
    if quote["credits"] < quote["credit_cost"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. You need {quote['credit_cost']} credits.")
    draft = _draft_payload(request, current_user.userid)
    draft["credit_cost"] = quote["credit_cost"]
    # The approval screen must queue precisely the plan the user reviewed.
    # Persist it rather than directing the LLM again at queue time.
    draft_id = f"draft_{uuid.uuid4().hex}"
    with get_conn() as conn:
        _ensure_tables(conn)
        execute(conn, """
            INSERT INTO reel_storyboard_drafts (id, user_id, source_message_id, plan_json)
            VALUES (%s, %s, %s, %s)
        """, (draft_id, current_user.userid, request.message_id, json.dumps(draft)))
        conn.commit()
    draft["draft_id"] = draft_id
    return draft


@router.post("/jobs")
def queue_render(request: RenderRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """Commit the approved job and credit debit together, once per draft."""
    quote = reel_pricing(current_user.userid, request.duration_seconds)
    job_id = f"job_{uuid.uuid5(uuid.NAMESPACE_URL, f'reel:{current_user.userid}:{request.draft_id}').hex}"
    renderer_ready = bool(os.getenv("OPENAI_API_KEY") or os.getenv("PARTNER_PORTRAIT_OPENAI_API_KEY"))
    if renderer_ready:
        # Resolve renderer dependencies before a debit can be committed.
        from reel_studio.worker import process_reel_job
    with get_conn() as conn:
        _ensure_tables(conn)
        row = execute(conn, """
            SELECT plan_json FROM reel_storyboard_drafts
            WHERE id=%s AND user_id=%s AND source_message_id=%s FOR UPDATE
        """, (request.draft_id, current_user.userid, request.message_id)).fetchone()
        if not row:
            raise HTTPException(status_code=409, detail="This storyboard has expired or does not belong to this answer. Prepare a new storyboard before queuing it.")
        try:
            draft = json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            raise HTTPException(status_code=503, detail="The approved storyboard could not be read. Prepare it again before queuing.")
        existing = execute(conn, "SELECT status FROM reel_render_jobs WHERE id=%s", (job_id,)).fetchone()
        if existing:
            return {"job_id": job_id, "run_id": draft["run_id"], "status": existing[0], "cost_projection": draft["cost_projection"], "credit_cost": draft.get("credit_cost"), "reused": True}
        settings = draft.get("settings") or {}
        if any(settings.get(key) != getattr(request, key) for key in ("message_id", "duration_seconds", "language", "visual_level")):
            raise HTTPException(status_code=422, detail="Queue settings do not match the storyboard you approved. Prepare a new storyboard.")
        available = {claim["id"] for claim in draft["claims"]}
        if not set(request.approved_claim_ids).issubset(available):
            raise HTTPException(status_code=422, detail="Approval contains an unknown claim.")
        if quote["credit_cost"] != request.confirmed_credit_cost:
            raise HTTPException(status_code=409, detail="Reel credit pricing has changed. Reopen Reel Studio to review the current price.")
        if not renderer_ready:
            raise HTTPException(status_code=503, detail="Reel generation is not configured. No credits were charged.")
        if not charge_reel(conn, current_user.userid, quote["credit_cost"], job_id, request.message_id):
            raise HTTPException(status_code=402, detail=f"Insufficient credits. You need {quote['credit_cost']} credits.")
        status = "queued"
        draft["approved_claim_ids"] = request.approved_claim_ids
        draft["credit_charge"] = {"cost": quote["credit_cost"], "refunded": False}
        execute(conn, """
            INSERT INTO reel_render_jobs (id, user_id, source_message_id, mode, status, plan_json)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (job_id, current_user.userid, request.message_id, request.visual_level, status, json.dumps(draft)))
        conn.commit()
    from reel_studio.task_queue import enqueue_reel_render_task, reel_tasks_enabled

    if reel_tasks_enabled():
        if not enqueue_reel_render_task(job_id):
            # A paid render must never be left in a queue that no worker can
            # reach. Mark/refund it atomically through the existing idempotent
            # refund path, then make the client retryable.
            from reel_studio.billing import refund_reel

            refund_reel(job_id)
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    UPDATE reel_render_jobs
                    SET status = 'failed', error_message = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    ("The Reel worker queue could not accept this job. Your credits were returned.", job_id),
                )
                conn.commit()
            raise HTTPException(status_code=503, detail="Reel worker queue is temporarily unavailable. Your credits were returned; please try again.")
    else:
        # Local development remains self-contained. Production enables the
        # durable path automatically once the Cloud Run worker registers.
        background_tasks.add_task(process_reel_job, job_id)
    return {
        "job_id": job_id, "run_id": draft["run_id"], "status": status,
        "cost_projection": draft["cost_projection"], "credit_cost": quote["credit_cost"],
        "next_step": None if renderer_ready else "Configure OpenAI image generation before this storyboard can become an MP4.",
    }


@router.get("/pricing")
def get_reel_pricing(
    duration_seconds: int = Query(default=REEL_SHORT_DURATION_SECONDS, ge=1),
    current_user: User = Depends(get_current_user),
):
    # Query parameters arrive as text. Pydantic's Literal[int, int] performs
    # an exact literal match before coercion on some supported versions, so a
    # valid URL such as ?duration_seconds=90 was rejected. Parse first, then
    # enforce the two supported formats explicitly.
    if duration_seconds not in {REEL_SHORT_DURATION_SECONDS, REEL_DEEP_DURATION_SECONDS}:
        raise HTTPException(status_code=422, detail="duration_seconds must be 90 or 180")
    return reel_pricing(current_user.userid, duration_seconds)


@router.get("/saved/{message_id}")
def saved_reel(message_id: int, language: Literal["en", "hi"] | None = None, current_user: User = Depends(get_current_user)):
    """Reopen a completed reel or reconnect to its render without planning again.

    A message with no earlier reel is a normal fresh-generation state and
    returns ``{"job": None}``, never a 404.
    """
    with get_conn() as conn:
        _ensure_tables(conn)
        rows = execute(conn, """SELECT id, status, output_url, error_message, plan_json
            FROM reel_render_jobs WHERE user_id=%s AND source_message_id=%s
            ORDER BY created_at DESC""", (current_user.userid, message_id)).fetchall()
        conn.commit()
    for job_id, status, output_url, error, raw in rows:
        plan = json.loads(raw or "{}")
        if language and plan.get("settings", {}).get("language", "en") != language:
            continue
        if status == "failed":
            continue
        return {"job": {"job_id": job_id, "status": status, "output_url": output_url,
                        "error_message": error, "settings": plan.get("settings", {}), "cached": status == "completed"}}
    return {"job": None}


@router.get("/history")
def reel_history(current_user: User = Depends(get_current_user)):
    """The caller's reel library, including in-progress renders."""
    with get_conn() as conn:
        _ensure_tables(conn)
        rows = execute(conn, """
            SELECT id, source_message_id, status, output_url, error_message, plan_json, created_at, updated_at
            FROM reel_render_jobs
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 100
        """, (current_user.userid,)).fetchall()
        conn.commit()
    reels = []
    for job_id, message_id, status, output_url, error_message, raw_plan, created_at, updated_at in rows:
        try:
            plan = json.loads(raw_plan or "{}")
        except (TypeError, json.JSONDecodeError):
            plan = {}
        source = plan.get("source") or {}
        settings = plan.get("settings") or {}
        reels.append({
            "job_id": job_id,
            "message_id": int(message_id),
            "status": status,
            "output_url": output_url,
            "error_message": error_message,
            "question": str(source.get("question") or "").strip(),
            "language": settings.get("language", "en"),
            "duration_seconds": settings.get("duration_seconds"),
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
        })
    return {"reels": reels}


@router.get("/jobs/{job_id}")
def get_render_job(job_id: str, current_user: User = Depends(get_current_user)):
    with get_conn() as conn:
        _ensure_tables(conn)
        row = execute(conn, """
            SELECT status, output_url, error_message, created_at, updated_at
            FROM reel_render_jobs WHERE id = %s AND user_id = %s
        """, (job_id, current_user.userid)).fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Reel job not found.")
    status = row[0]
    next_step = None
    renderer_ready = bool(os.getenv("OPENAI_API_KEY") or os.getenv("PARTNER_PORTRAIT_OPENAI_API_KEY"))
    if status == "queued" and not renderer_ready:
        status = "awaiting_provider_configuration"
        next_step = "Configure OpenAI image generation before this storyboard can become an MP4."
    return {"job_id": job_id, "status": status, "output_url": row[1], "error_message": row[2], "next_step": next_step,
            "created_at": row[3].isoformat() if row[3] else None,
            "updated_at": row[4].isoformat() if row[4] else None}


@router.get("/jobs/{job_id}/download")
def download_render(job_id: str, request: Request, current_user: User = Depends(get_current_user)):
    from reel_studio.storage import load_reel
    with get_conn() as conn:
        row = execute(conn, "SELECT user_id, status FROM reel_render_jobs WHERE id=%s AND user_id=%s", (job_id, current_user.userid)).fetchone()
    if not row or row[1] != "completed":
        raise HTTPException(status_code=404, detail="Reel is not ready yet.")
    output = load_reel(row[0], job_id)
    if output is None:
        raise HTTPException(status_code=404, detail="Reel output is unavailable.")
    return _video_response(output, request.headers.get("range"))


def _video_response(path, range_header: str | None):
    """Authenticated byte ranges allow native/web video players to seek."""
    size = path.stat().st_size
    start, end, status = 0, size - 1, 200
    headers = {"Accept-Ranges": "bytes", "Content-Disposition": 'inline; filename="astroroshni-reel.mp4"',
               "Cache-Control": "private, max-age=86400"}
    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match or not any(match.groups()):
            raise HTTPException(status_code=416, headers={"Content-Range": f"bytes */{size}"})
        left, right = match.groups()
        start = int(left) if left else max(0, size - int(right))
        end = min(int(right), size - 1) if left and right else size - 1
        if start > end or start >= size:
            raise HTTPException(status_code=416, headers={"Content-Range": f"bytes */{size}"})
        status = 206
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    headers["Content-Length"] = str(end - start + 1)
    def chunks():
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = end - start + 1
            while remaining:
                data = handle.read(min(1024 * 1024, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data
    return StreamingResponse(chunks(), status_code=status, media_type="video/mp4", headers=headers)


@router.post("/cost-events")
def record_cost_event(request: CostEventRequest, current_user: User = Depends(get_current_user)):
    import json
    total = round(request.units * request.unit_cost_inr, 4)
    with get_conn() as conn:
        _ensure_tables(conn)
        execute(conn, """
            INSERT INTO reel_generation_costs
              (user_id, run_id, stage, provider, units, unit_cost_inr, total_cost_inr, metadata_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (current_user.userid, request.run_id, request.stage, request.provider,
              request.units, request.unit_cost_inr, total, json.dumps(request.metadata)))
        conn.commit()
    return {"recorded": True, "total_cost_inr": total}


@router.get("/costs/{run_id}")
def run_costs(run_id: str, current_user: User = Depends(get_current_user)):
    with get_conn() as conn:
        _ensure_tables(conn)
        rows = execute(conn, """
            SELECT stage, provider, units, unit_cost_inr, total_cost_inr, created_at
            FROM reel_generation_costs WHERE user_id = %s AND run_id = %s ORDER BY created_at
        """, (current_user.userid, run_id)).fetchall()
        conn.commit()
    events = [dict(stage=row[0], provider=row[1], units=float(row[2]), unit_cost_inr=float(row[3]),
                   total_cost_inr=float(row[4]), created_at=row[5].isoformat() if row[5] else None) for row in rows]
    return {"run_id": run_id, "actual_total_inr": round(sum(row["total_cost_inr"] for row in events), 4), "events": events}


@router.get("/admin/runs")
def admin_reel_runs(limit: int = Query(100, ge=1, le=500), current_user: User = Depends(get_current_user)):
    """Provider-cost ledger for Reel Studio; only recorded charges are totalled."""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    with get_conn() as conn:
        _ensure_tables(conn)
        jobs = execute(conn, """SELECT id, user_id, status, plan_json, created_at, updated_at
            FROM reel_render_jobs ORDER BY created_at DESC LIMIT %s""", (limit,)).fetchall()
        result = []
        for job_id, user_id, status, raw_plan, created_at, updated_at in jobs:
            plan = json.loads(raw_plan or "{}")
            run_id = str(plan.get("run_id") or "")
            rows = execute(conn, """SELECT stage, provider, units, unit_cost_inr, total_cost_inr, metadata_json, created_at
                FROM reel_generation_costs WHERE run_id=%s ORDER BY created_at""", (run_id,)).fetchall() if run_id else []
            charges = []
            for row in rows:
                metadata = json.loads(row[5] or "{}")
                recorded = float(row[4])
                recovered = _recovered_video_cost(metadata) if row[0] == "video" and recorded == 0 else 0.0
                charges.append({"stage": row[0], "provider": row[1], "units": float(row[2]), "unit_cost_inr": float(row[3]),
                                "total_inr": recovered or recorded, "metadata": metadata,
                                "recovered_from_usage": bool(recovered), "created_at": row[6].isoformat() if row[6] else None})
            result.append({"job_id": job_id, "run_id": run_id, "user_id": int(user_id), "status": status,
                           "actual_total_inr": round(sum(item["total_inr"] for item in charges), 4), "charges": charges,
                           "created_at": created_at.isoformat() if created_at else None,
                           "updated_at": updated_at.isoformat() if updated_at else None})
        conn.commit()
    return {"currency": "INR", "runs": result,
            "note": "Total is the recorded provider cost for each run. GST, payment fees, or provider discounts are included only when configured in the recorded unit price."}
