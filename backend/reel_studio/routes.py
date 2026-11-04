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

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn

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
_BEAT_TYPES = ("presenter", "presenter", "chart", "lifestyle_image", "dasha", "ashtakavarga", "lifestyle_image", "lifestyle_image", "closing")
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
    duration_seconds: int = Field(default=180, ge=30, le=180)
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

    The reel deliberately stores placements and dasha dates, never the person's
    name, date of birth, time, coordinates, or place of birth.
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
            placements.append({"planet": planet, "house": int(value.get("house") or 0), "sign": int(value.get("longitude", 0) // 30)})
        raw_sav = (AshtakavargaCalculator(dict(birth), chart).calculate_sarvashtakavarga() or {}).get("sarvashtakavarga") or {}
        asc = int(float(chart.get("ascendant") or 0) // 30) % 12
        snapshot = {
            "chart_id": chart_id,
            "ascendant_sign": int(float(chart.get("ascendant") or 0) // 30),
            "placements": placements,
            "current_dashas": {
                level: {key: value for key, value in (dashas.get(level) or {}).items() if key in {"planet", "start", "end"}}
                for level in ("mahadasha", "antardasha", "pratyantardasha")
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
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


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
    # One 10-second Omni presenter source is split into two five-second beats.
    video_seconds = 10 if visual_level != "none" and OMNI_VIDEO_ENABLED else 0
    base = sum(DEFAULT_BASE_COSTS_INR.values())
    video = VIDEO_COST_PER_SECOND_INR[visual_level] * video_seconds
    image = 12.0 if visual_level != "none" else 0.0
    total = round(base + video + image, 2)
    return {
        "currency": "INR",
        "estimated_total": total,
        "line_items": [
            {"label": label.replace("_", " ").title(), "estimated_inr": cost}
            for label, cost in DEFAULT_BASE_COSTS_INR.items()
        ] + ([{"label": f"{video_seconds}s generated video", "estimated_inr": round(video, 2)}] if video else [])
          + ([{"label": "Supporting images", "estimated_inr": image}] if image else []),
        "assumptions": {
            "duration_seconds": duration,
            "generated_video_seconds": video_seconds,
            "retry_allowance_included": DEFAULT_BASE_COSTS_INR["retry_allowance"],
        },
    }


def _planned_beats(answer: str, question: str, claims: list[dict], snapshot: dict | None, language: str, duration_seconds: int) -> list[dict]:
    """Text model directs the creative edit; rendering remains fact-bound."""
    types = _BEAT_TYPES
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
    output_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["beats"],
        "properties": {
            "beats": {
                "type": "array", "minItems": 9, "maxItems": 9,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["type", "narration", "evidence_ids", "visual_instruction", "focus_nodes", "draw_edges"],
                    "properties": {
                        "type": {"type": "string", "minLength": 1},
                        "narration": {"type": "string", "minLength": 1},
                        "evidence_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
                        "visual_instruction": {"type": "string"},
                        "focus_nodes": {"type": "array", "items": {"type": "string"}},
                        "draw_edges": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    }
    prompt = f'''Return JSON only: {{"beats":[{{"type":"", "narration":"", "evidence_ids":[], "visual_instruction":"", "focus_nodes":[], "draw_edges":[]}}]}}.
Write a detailed {duration_seconds}-second premium vertical reel plan that ANSWERS THE USER'S ACTUAL QUESTION and explains why the approved answer reaches that conclusion. Do not make a generic astrology reel. Use exactly nine directed beats in this order: presenter, presenter, chart, lifestyle_image, dasha, ashtakavarga, lifestyle_image, lifestyle_image, closing. Write complete, naturally spoken passages. The combined narration MUST contain between {round(duration_seconds * 2.35)} and {round(duration_seconds * 2.5)} words for a calm podcast pace. Never cut a sentence, use ellipses, or repeat a closing/thank-you line. The two presenter beats form the opening explanation. For the chart beat, select at least one relevant verified focus node and edge when the graph has one. Each lifestyle_image needs a concrete prompt tied to the answer. Chart, dasha, ashtakavarga and closing are deterministic data visual directions only. Do not invent facts or use facts not in the approved answer. EVIDENCE RULE: every beat's evidence_ids must be a non-empty array containing only exact id values from the CLAIMS list below. Never create a new claim ID and never leave evidence_ids empty.
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
        if not isinstance(generated, list) or len(generated) != 9:
            raise ValueError("The director did not return nine complete beats.")
        valid_ids = {c["id"] for c in claims}
        node_ids = {str(node.get("id")) for node in graph.get("nodes", [])}
        edge_ids = {str(edge.get("id")) for edge in graph.get("edges", [])}
        beats = []
        for i, item in enumerate(generated):
            if not isinstance(item, dict):
                raise ValueError(f"Beat {i + 1} is not an object.")
            if item.get("type") != types[i]:
                raise ValueError(f"Beat {i + 1} must be a {types[i]} scene.")
            narration = complete_line(item.get("narration"))
            if not narration:
                raise ValueError(f"Beat {i + 1} is not a complete short sentence.")
            visual_instruction = _clean_text(str(item.get("visual_instruction") or ""))
            if item.get("type") == "lifestyle_image" and not visual_instruction:
                raise ValueError(f"Lifestyle beat {i + 1} has no visual direction.")
            focus_nodes = [str(x) for x in item.get("focus_nodes", [])]
            draw_edges = [str(x) for x in item.get("draw_edges", [])]
            if any(node not in node_ids for node in focus_nodes) or any(edge not in edge_ids for edge in draw_edges):
                raise ValueError(f"Beat {i + 1} references evidence that is not in the verified graph.")
            ids = [str(x) for x in item.get("evidence_ids", []) if str(x) in valid_ids]
            if not ids:
                raise ValueError(f"Beat {i + 1} is not grounded in an approved claim.")
            beats.append({"id": f"beat_{i + 1}", "start_seconds": 0, "end_seconds": 0,
                          "type": types[i], "narrator": "omni" if types[i] == "presenter" else "podcast",
                          "narration": narration, "visual_instruction": visual_instruction,
                          "focus_nodes": focus_nodes, "draw_edges": draw_edges, "evidence_ids": ids})
        if not beats[2]["focus_nodes"] or not beats[2]["draw_edges"]:
            raise ValueError("The chart explanation must select verified nodes and at least one verified arrow.")
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
        seconds = max(4.0, len(beat["narration"].split()) / 2.5 + 0.35)
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
            "presenter": True,
            "generated_lifestyle_broll": request.visual_level in {"hybrid", "cinematic"},
            "note": "The final reel uses an on-screen AI presenter, deterministic chart/dasha inserts, and generated live-action b-roll. Uploaded licensed b-roll can replace generated b-roll in a later pass.",
        },
        "settings": request.model_dump(),
        "claims": claims,
        "storyboard": scenes,
        "estimated_duration_seconds": scenes[-1]["end_seconds"] if scenes else 0,
        "creative_plan": {"planner": "text-model-with-deterministic-rendering", "beat_count": 9},
        "cost_projection": _cost_projection(request.duration_seconds, request.visual_level),
        "approval_required": True,
        "privacy_note": "Client identifiers and birth details are excluded from the reel plan by default.",
    }


@router.post("/drafts/from-answer")
def create_draft(request: DraftRequest, current_user: User = Depends(get_current_user)):
    draft = _draft_payload(request, current_user.userid)
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
    """Persist an approved job; a separately deployed worker renders it.

    The worker must reject any generated-video scene carrying evidence IDs. This
    prevents cinematic footage from becoming a false visual proof of a claim.
    """
    with get_conn() as conn:
        _ensure_tables(conn)
        row = execute(conn, """
            SELECT plan_json FROM reel_storyboard_drafts
            WHERE id=%s AND user_id=%s AND source_message_id=%s
        """, (request.draft_id, current_user.userid, request.message_id)).fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=409, detail="This storyboard has expired or does not belong to this answer. Prepare a new storyboard before queuing it.")
    try:
        draft = json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="The approved storyboard could not be read. Prepare it again before queuing.")
    settings = draft.get("settings") or {}
    if any(settings.get(key) != getattr(request, key) for key in ("message_id", "duration_seconds", "language", "visual_level")):
        raise HTTPException(status_code=422, detail="Queue settings do not match the storyboard you approved. Prepare a new storyboard.")
    available = {claim["id"] for claim in draft["claims"]}
    if not set(request.approved_claim_ids).issubset(available):
        raise HTTPException(status_code=422, detail="Approval contains an unknown claim.")
    job_id = f"job_{uuid.uuid4().hex}"
    draft["approved_claim_ids"] = request.approved_claim_ids
    renderer_ready = bool(os.getenv("OPENAI_API_KEY") or os.getenv("PARTNER_PORTRAIT_OPENAI_API_KEY"))
    status = "queued" if renderer_ready else "awaiting_provider_configuration"
    with get_conn() as conn:
        _ensure_tables(conn)
        execute(conn, """
            INSERT INTO reel_render_jobs (id, user_id, source_message_id, mode, status, plan_json)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (job_id, current_user.userid, request.message_id, request.visual_level, status, json.dumps(draft)))
        conn.commit()
    if renderer_ready:
        from reel_studio.worker import process_reel_job
        background_tasks.add_task(process_reel_job, job_id)
    return {
        "job_id": job_id, "run_id": draft["run_id"], "status": status,
        "cost_projection": draft["cost_projection"],
        "next_step": None if renderer_ready else "Configure OpenAI image generation before this storyboard can become an MP4.",
    }


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
def download_render(job_id: str, current_user: User = Depends(get_current_user)):
    from reel_studio.worker import ROOT
    with get_conn() as conn:
        row = execute(conn, "SELECT user_id, status FROM reel_render_jobs WHERE id=%s AND user_id=%s", (job_id, current_user.userid)).fetchone()
    if not row or row[1] != "completed":
        raise HTTPException(status_code=404, detail="Reel is not ready yet.")
    output = ROOT / str(row[0]) / job_id / "final-reel.mp4"
    if not output.is_file():
        raise HTTPException(status_code=404, detail="Reel output is unavailable.")
    return FileResponse(output, media_type="video/mp4", filename="astroroshni-reel.mp4")


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
