"""Cached, evidence-led Nakshatra Blueprint API.

The chart engine owns all astronomical facts.  Luna is only allowed to turn the
locked fact pack into readable prose; Luna is the primary writer and Gemini 3
Flash receives the same prompt only when Luna is unavailable.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from auth import User, get_current_user
from credits.credit_service import CreditService
from db import execute, get_conn
from reports.cache.report_hash import normalize_birth_data
from reports.context.janam_kundli_context_builder import build_janam_kundli_report_context
from reports.models import BirthInput
from .image_service import NakshatraBlueprintImageProvider, NakshatraBlueprintStorage, image_provider_configured
from .knowledge import build_nakshatra_blueprint_brief

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nakshatra-blueprint", tags=["nakshatra-blueprint"])
credit_service = CreditService()
BLUEPRINT_VERSION = "nakshatra_blueprint_v7"
VISUAL_KEYS = ("identity_foundation", "inner_nature", "relationships_and_home", "vocation_and_abundance")


class BlueprintRequest(BaseModel):
    birth_data: BirthInput
    language: Literal["english", "hindi"] = "english"
    include_images: bool = False
    birth_time_accuracy_minutes: int = Field(default=15, ge=0, le=1440)
    force_regenerate: bool = False


def _ensure_table(conn: Any) -> None:
    execute(conn, """
        CREATE TABLE IF NOT EXISTS nakshatra_blueprints (
          blueprint_id TEXT PRIMARY KEY, userid INTEGER NOT NULL, subject_hash TEXT NOT NULL,
          language TEXT NOT NULL, include_images BOOLEAN NOT NULL DEFAULT FALSE,
          blueprint_version TEXT NOT NULL, status TEXT NOT NULL, payload JSONB,
          credits_charged INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE(userid, subject_hash, language, include_images, blueprint_version)
        )
    """)
    # `subject_hash` identifies one edition (images and time-accuracy choice).
    # Keep a separate stable birth hash so the app can restore the latest paid
    # Blueprint for this native as soon as the screen opens.
    execute(conn, "ALTER TABLE nakshatra_blueprints ADD COLUMN IF NOT EXISTS birth_hash TEXT")
    execute(conn, "CREATE INDEX IF NOT EXISTS idx_nakshatra_blueprints_birth_lookup ON nakshatra_blueprints (userid, birth_hash, language, blueprint_version, updated_at DESC)")
    conn.commit()


def _birth_hash(request: BlueprintRequest) -> str:
    payload = {
        "birth": normalize_birth_data(request.birth_data), "language": request.language,
        "version": BLUEPRINT_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _subject_hash_for_options(request: BlueprintRequest, include_images: bool, accuracy: int) -> str:
    payload = {
        "birth": normalize_birth_data(request.birth_data), "language": request.language,
        "images": include_images, "accuracy": accuracy,
        "version": BLUEPRINT_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _subject_hash(request: BlueprintRequest) -> str:
    return _subject_hash_for_options(request, request.include_images, request.birth_time_accuracy_minutes)


def _cost(userid: int, include_images: bool) -> tuple[int, int, int]:
    base = credit_service.get_effective_cost(userid, credit_service.get_credit_setting("nakshatra_blueprint_cost"), "nakshatra_blueprint_cost")
    addon = credit_service.get_effective_cost(userid, credit_service.get_credit_setting("nakshatra_blueprint_images_addon_cost"), "nakshatra_blueprint_images_addon_cost") if include_images else 0
    return int(base + addon), int(base), int(addon)


def _precision(facts: dict, accuracy: int) -> dict:
    rows = facts.get("planet_matrix") or []
    # The Ascendant is especially birth-time sensitive.  We present a truthful
    # uncertainty declaration rather than claiming a universal number of minutes.
    return {
        "declared_accuracy_minutes": accuracy,
        "status": "high" if accuracy <= 15 else "review",
        "message": (
            "Pada-level interpretation is based on the supplied birth time. Ascendant and house-sensitive details should be reviewed if the recorded time may differ."
            if accuracy > 15 else
            "Your declared time accuracy supports pada-level interpretation; placements close to a boundary should still be treated as sensitive."
        ),
        "placements_checked": len(rows),
    }


def _prompt(facts: dict, language: str, native_name: str) -> str:
    # No uncurated web lore is sent to the model. This compact fact pack is
    # calculator-owned and includes every graha plus the established nakshatra data.
    evidence = {
        "ascendant": facts.get("ascendant"), "moon": facts.get("moon"),
        "planet_matrix": facts.get("planet_matrix"), "house_themes": facts.get("house_themes"),
        "nakshatra_deep_dive": facts.get("nakshatra_deep_dive"),
        # This is a controlled editorial knowledge layer for *only* the stars
        # actually active in this chart. It prevents the writer from falling
        # back to generic planet-and-house prose.
        "nakshatra_reasoning_brief": build_nakshatra_blueprint_brief(facts),
    }
    schema = {
        "headline": "string", "opening": "string",
        "presence_style": {"headline": "string", "reading": "string", "style_direction": "string"},
        "core_patterns": [{"title": "string", "reading": "string"}],
        "planet_readings": [{"planet": "Sun", "signature": "string"}],
        "life_areas": [{"key": "identity", "title": "string", "reading": "string", "application": "string"}],
        "nakshatra_remedies": [{"nakshatra": "string", "life_area": "string", "practice": "string", "purpose": "string"}],
        "closing": "string",
    }
    return f"""You are Luna, writing an evidence-led Nakshatra Blueprint in {language}.
Return ONLY valid JSON matching this schema: {json.dumps(schema)}
The native is {json.dumps(native_name, ensure_ascii=False)}. Write as their experienced, compassionate Vedic astrologer, speaking directly to them in a polished natal consultation. Use their name naturally in the headline and opening, then sparingly in pivotal passages; do not mechanically repeat it. When the name is "you", write directly in second person without a name.
This is a Nakshatra Blueprint, not a generic natal-chart or house reading. Write as a thoughtful astrologer speaking to an intelligent person, never as compressed notes for another astrologer. The Nakshatra standard is non-negotiable:
- Before drafting, identify the 3–5 strongest chart_patterns and use them as the Blueprint's recurring interpretive spine. A pattern that repeats through several grahas must be developed across the relevant life areas, with a different consequence in each area. Do not make every section a new, disconnected placement list.
- The active_nakshatra_dossiers are an approved interpretive library. Use their deity, symbol, ruler, mature_action, shadow_expression, life_motifs and pada_refinement selectively when they illuminate the placement. Never dump dossier fields, give a textbook entry, or claim every trait applies. Make the mythic identifier do interpretive work: explain what it changes in the native's behaviour, choices, relationships or vocation.
- A reading must contain real tension, not only additive praise. Where supported by chart_patterns or placements, distinguish mature expression from an overextended expression, and explain what helps integrate it. Do not make clinical, deterministic, or diagnostic claims.
- Every planet_readings.signature MUST name that graha's Nakshatra and, where supplied, its pada, then explain the behavioural instinct of that Nakshatra/pada before mentioning rashi or house.
- Every life_areas.reading MUST lead with a plain-language observation the native can recognise in life, then clearly name the relevant Nakshatra/pada influence. Write "Your Moon is in Swati, in its fourth pada" or "Your Sun and Rahu are both in Ardra"—never shorthand such as "Swati pada 4 Moon", "Ardra's Sun-Rahu pattern", or an unexplained stack of star names. It may then use graha, rashi and house only as supporting context for where or how the Nakshatra pattern manifests. When mentioning a house, translate its ordinary-life domain in the same sentence, for example "the sixth house of daily work and routines". Each chapter must make one clear chart-specific claim about the interaction of factors, not merely say that one placement 'adds' to another.
- Never lead a paragraph with a house, rashi, sign, or generic graha strength. A statement such as "Mercury is strong in Gemini" or "the eleventh house emphasises" is incomplete and forbidden unless it follows a clear Nakshatra/pada interpretation.
- Use the exact Nakshatra and pada only when they appear in the locked chart facts. If a pada is absent, name the Nakshatra without inventing one.
Write 3 to 5 core_patterns before the life areas. These are the chart's most consequential recurring Nakshatra dynamics, selected from chart_patterns and enriched_placements—not generic headings. Each must be 55–90 words and explain a genuine interaction, tension or reinforcement that will recur later in the reading. Do not repeat the opening or turn this into a placement list.
Write presence_style as a 70–110 word reading of presence, appearance and personal style. Anchor it in the Ascendant Nakshatra and pada, then support it only with relevant Ascendant-lord, Moon, Venus, first-house or aspect facts that are present. Describe the felt impression, gaze, voice, movement, self-presentation and aesthetic instinct—not fixed physical traits. Never claim exact height, weight, complexion, ethnicity, facial features, age, attractiveness, health, or anything deterministic. style_direction must be one concise, practical suggestion for a way of presenting oneself that aligns with the chart's Nakshatra qualities.
Cover all nine grahas exactly once in planet_readings and all twelve life areas exactly once in life_areas. The life areas are the heart of this consultation: each life_areas.reading must be a detailed, lucid synthesis of the 2–4 most relevant grahas, Nakshatras/padas and contextual houses or rashis for that area. Explain how those patterns interact in the native's lived experience, rather than listing placements. Aim for 130–180 words per life area. A good chapter has: (1) a humanly recognisable opening, (2) an explicit explanation of the relevant placements and their interaction, (3) the likely lived expression, including both a strength and an overextended expression where supported. Use complete, flowing prose with no unexplained technical shorthand. Do not reuse the same conclusion, shadow, or practical guidance in more than one chapter. Avoid empty advice such as 'set boundaries', 'communicate clearly', 'pause before reacting' or 'be authentic' unless the preceding interpretation makes that exact action uniquely necessary.
Every life area MUST also include application: 55–90 words that directly answers its matching life_area_reader_questions entry in the reasoning brief. This is the reader's practical conclusion, not a summary of placements. Write it as warm, readable guidance in connected sentences, not a checklist. Be specific about choices, environments, role types, habits, agreements, methods or priorities. For career, application MUST name 3–5 plausible role families or work domains plus the work environment and contribution that fit; present them as options to explore, not promises of occupation, income or status. For all other areas, never make guarantees about marriage, children, money, health, events or outcomes.
Planet readings are supporting reference, not nine mini-consultations: each signature must be only 1–2 concise sentences. Do not include separate gift, growth-edge, remedy, or life-area material there; reserve that depth for life_areas. Nakshatra describes behavioural instinct; rashi and house are context. Pada is a refinement, never a generic personality label. Use only the locked chart facts below. Do not invent classical quotations, events, diagnoses, dates, placements, or certainties.
Write 3 to 5 nakshatra_remedies. Each remedy must name a Nakshatra that appears in the locked chart facts and offer one gentle, low-cost traditional or devotional practice associated with that Nakshatra's energy, such as a mindful observance, selfless service, nature practice, prayer or mantra only where the relevant Nakshatra association is present in the facts. Set life_area to the one most relevant chart area it supports (for example, career and purpose, relationships, home and family, emotional wellbeing, confidence, communication, health routines, or spiritual growth). In purpose, explain in one sentence how the practice supports that specific life area; use grounded language such as "supports" or "helps cultivate", never promises that it will improve, fix, cure, attract, or guarantee an outcome. Never prescribe medical treatment, gemstones, costly purchases, fasting that risks health, coercive acts, or guaranteed outcomes.
Never mention or allude to evidence, supplied facts, supplied data, the fact pack, calculations, source material, a prompt, an AI, a model, a schema, or an analysis process. Do not use phrases such as "the evidence shows", "based on the supplied", "the data indicates", or "your chart data". State the interpretation directly and naturally, as an astrologer reading the native's chart.
FACT_PACK={json.dumps(evidence, ensure_ascii=False, default=str)}"""


async def _write_reading(facts: dict, language: str, native_name: str) -> tuple[dict, str]:
    prompt = _prompt(facts, language, native_name)
    analyzer = GeminiChatAnalyzer()
    attempts = [
        {"provider_override": "openai", "model_name_override": "gpt-5.6-luna", "openai_reasoning_effort": "minimal"},
        {"provider_override": "gemini", "model_name_override": "models/gemini-3-flash-preview", "use_gemini_rest": True},
    ]
    for attempt in attempts:
        out = await analyzer.generate_text_from_prompt(prompt, premium_analysis=True, llm_log_tag="nakshatra_blueprint", request_timeout_s=120, **attempt)
        raw = str(out.get("response") or "").strip()
        if not out.get("success") or not raw:
            continue
        try:
            parsed = json.loads(raw.removeprefix("```json").removesuffix("```").strip())
            remedy_count = len(parsed.get("nakshatra_remedies") or [])
            if len(parsed.get("planet_readings") or []) == 9 and len(parsed.get("life_areas") or []) == 12 and 3 <= remedy_count <= 5:
                return parsed, str(out.get("chat_llm_model") or attempt["model_name_override"])
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    raise RuntimeError("Nakshatra Blueprint writer was unavailable")


def _visual_prompt(key: str, facts: dict, reading: dict) -> str:
    """Chart-specific symbolic artwork with no names, faces or readable text."""
    themes = {
        "identity_foundation": "an evocative scene of a person beginning a meaningful path at dawn, with a luminous horizon, a threshold and subtle star patterns suggesting identity, roots and inner direction",
        "inner_nature": "a poetic everyday scene expressing temperament, creativity and emotional life: a quiet garden, flowing water, a handmade object or a workshop, and an anonymous figure in reflective action",
        "relationships_and_home": "a warm, emotionally resonant life scene of home, belonging and human connection: a welcoming doorway, shared light, meaningful companionship and a sense of trust without depicting identifiable people",
        "vocation_and_abundance": "an aspirational life scene of vocation, contribution and abundance: an anonymous person moving toward purposeful work, a craft or profession, open paths and symbols of steady growth",
    }
    moon = facts.get("moon") or {}
    ascendant = facts.get("ascendant") or {}
    life_context = [{"title": item.get("title") or item.get("key"), "reading": (item.get("reading") or "")[:260]} for item in (reading.get("life_areas") or [])]
    creative_context = json.dumps({"ascendant": ascendant, "moon": moon, "opening": (reading.get("opening") or "")[:500], "life_themes": life_context}, ensure_ascii=False, default=str)
    return f"""Use case: illustration-story
Asset type: a premium in-app chapter image for a Vedic Nakshatra Blueprint
Primary request: {themes[key]}.
Astrological creative direction: {creative_context}
Style/medium: sophisticated hand-painted editorial illustration with cinematic human warmth, Indian astronomical manuscript influence reimagined for a contemporary premium reading; deep indigo, plum, warm gold, terracotta and moonlit ivory.
Composition/framing: square image, balanced and serene, with generous visual depth.
Constraints: portray only anonymous, non-identifiable people from a respectful middle or wide distance; never make a portrait or recognizable likeness. Blend real-life scenes with subtle stars, constellations, lotuses, paths and light. No deity depictions, readable words, letters, numbers, zodiac labels, watermarks, logos, charts, UI, or text."""


async def _generate_visuals(*, user_id: int, blueprint_id: str, facts: dict, reading: dict) -> list[dict]:
    if not image_provider_configured():
        raise RuntimeError("Nakshatra Blueprint image provider is not configured")
    provider = NakshatraBlueprintImageProvider()
    storage = NakshatraBlueprintStorage()

    async def create(key: str) -> dict:
        content, content_type = await provider.generate(_visual_prompt(key, facts, reading))
        stored_uri = storage.save(user_id=user_id, blueprint_id=blueprint_id, kind=key, content=content, content_type=content_type)
        return {"key": key, "status": "ready", "stored_uri": stored_uri, "alt_text": "Illustrated Nakshatra Blueprint visual"}

    return list(await asyncio.gather(*(create(key) for key in VISUAL_KEYS)))


def _with_display_urls(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    visuals = payload.get("visual_slots") or []
    if not visuals:
        return payload
    storage = NakshatraBlueprintStorage()
    hydrated = dict(payload)
    hydrated["visual_slots"] = [
        {**slot, "url": storage.display_uri(slot["stored_uri"])} if isinstance(slot, dict) and slot.get("stored_uri") else slot
        for slot in visuals
    ]
    return hydrated


@router.get("/pricing")
async def pricing(current_user: User = Depends(get_current_user)):
    total, base, addon = _cost(current_user.userid, True)
    text_total, _, _ = _cost(current_user.userid, False)
    return {"text_cost": text_total, "images_addon_cost": addon, "illustrated_cost": total}


@router.post("/existing")
async def existing(request: BlueprintRequest, current_user: User = Depends(get_current_user)):
    subject_hash = _subject_hash(request)
    with get_conn() as conn:
        _ensure_table(conn)
        row = execute(conn, "SELECT blueprint_id, payload, credits_charged FROM nakshatra_blueprints WHERE userid=%s AND subject_hash=%s AND language=%s AND include_images=%s AND blueprint_version=%s AND status='completed'", (current_user.userid, subject_hash, request.language, request.include_images, BLUEPRINT_VERSION)).fetchone()
    if not row:
        return {"exists": False}
    return {"exists": True, "blueprint_id": row[0], "payload": _with_display_urls(row[1]), "credits_charged": row[2]}


@router.post("/existing-latest")
async def existing_latest(request: BlueprintRequest, current_user: User = Depends(get_current_user)):
    """Restore a paid Blueprint on entry, independent of its edition choices.

    The fallback supports rows created before `birth_hash` was introduced. The
    app's available accuracy choices are deliberately enumerated here, so those
    legacy readings are also restored without asking the user to press Generate.
    """
    with get_conn() as conn:
        _ensure_table(conn)
        row = execute(conn, "SELECT blueprint_id, payload, credits_charged FROM nakshatra_blueprints WHERE userid=%s AND birth_hash=%s AND language=%s AND blueprint_version=%s AND status='completed' ORDER BY updated_at DESC LIMIT 1", (current_user.userid, _birth_hash(request), request.language, BLUEPRINT_VERSION)).fetchone()
        if not row:
            legacy_hashes = [_subject_hash_for_options(request, images, accuracy) for images in (False, True) for accuracy in (0, 15, 60)]
            placeholders = ", ".join(["%s"] * len(legacy_hashes))
            row = execute(conn, f"SELECT blueprint_id, payload, credits_charged FROM nakshatra_blueprints WHERE userid=%s AND subject_hash IN ({placeholders}) AND language=%s AND blueprint_version=%s AND status='completed' ORDER BY updated_at DESC LIMIT 1", (current_user.userid, *legacy_hashes, request.language, BLUEPRINT_VERSION)).fetchone()
    if not row:
        return {"exists": False}
    return {"exists": True, "blueprint_id": row[0], "payload": _with_display_urls(row[1]), "credits_charged": row[2]}


@router.post("/generate")
async def generate(request: BlueprintRequest, current_user: User = Depends(get_current_user)):
    subject_hash = _subject_hash(request)
    if not request.force_regenerate:
        cached = await existing(request, current_user)
        if cached.get("exists"):
            cached["cached"] = True
            return cached
    total, base, addon = _cost(current_user.userid, request.include_images)
    if credit_service.get_user_credits(current_user.userid) < total:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. You need {total} credits.")
    try:
        context = build_janam_kundli_report_context(request)
        facts = context.get("fact_pack") or {}
        native_name = (request.birth_data.name or "").strip()[:80] or "you"
        reading, model = await _write_reading(facts, request.language, native_name)
    except Exception as exc:
        logger.exception("Nakshatra Blueprint generation failed")
        raise HTTPException(status_code=503, detail="The Blueprint could not be generated. No credits were used; please try again.") from exc
    blueprint_id = str(uuid.uuid4())
    try:
        visual_slots = await _generate_visuals(user_id=current_user.userid, blueprint_id=blueprint_id, facts=facts, reading=reading) if request.include_images else []
    except Exception as exc:
        logger.exception("Nakshatra Blueprint illustration generation failed")
        raise HTTPException(status_code=503, detail="The illustrated Blueprint could not be generated. No credits were used; please try again.") from exc
    if not credit_service.spend_credits(current_user.userid, total, "nakshatra_blueprint", "Nakshatra Blueprint", json.dumps({"base": base, "images_addon": addon, "model": model})):
        raise HTTPException(status_code=402, detail="Your credit balance changed. Please try again.")
    payload = {"blueprint_id": blueprint_id, "version": BLUEPRINT_VERSION, "generated_at": datetime.now(timezone.utc).isoformat(), "language": request.language, "native_name": native_name, "include_images": request.include_images, "visual_slots": visual_slots, "precision": _precision(facts, request.birth_time_accuracy_minutes), "fact_summary": {"planet_matrix": facts.get("planet_matrix") or [], "ascendant": facts.get("ascendant"), "moon": facts.get("moon")}, "reading": reading, "model": model, "credits_charged": total}
    with get_conn() as conn:
        _ensure_table(conn)
        execute(conn, "INSERT INTO nakshatra_blueprints (blueprint_id, userid, subject_hash, birth_hash, language, include_images, blueprint_version, status, payload, credits_charged) VALUES (%s,%s,%s,%s,%s,%s,%s,'completed',%s::jsonb,%s) ON CONFLICT (userid, subject_hash, language, include_images, blueprint_version) DO UPDATE SET blueprint_id=EXCLUDED.blueprint_id,birth_hash=EXCLUDED.birth_hash,payload=EXCLUDED.payload,credits_charged=EXCLUDED.credits_charged,updated_at=NOW()", (blueprint_id, current_user.userid, subject_hash, _birth_hash(request), request.language, request.include_images, BLUEPRINT_VERSION, json.dumps(payload), total))
        conn.commit()
    return {"exists": True, "cached": False, "blueprint_id": blueprint_id, "payload": _with_display_urls(payload), "credits_charged": total}


@router.get("/{blueprint_id}")
async def get_blueprint(blueprint_id: str, current_user: User = Depends(get_current_user)):
    with get_conn() as conn:
        _ensure_table(conn)
        row = execute(conn, "SELECT payload, credits_charged FROM nakshatra_blueprints WHERE blueprint_id=%s AND userid=%s AND status='completed'", (blueprint_id, current_user.userid)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Nakshatra Blueprint not found")
    return {"blueprint_id": blueprint_id, "payload": _with_display_urls(row[0]), "credits_charged": row[1]}
