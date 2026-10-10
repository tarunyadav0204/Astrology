"""Authenticated paid Partner Portrait API."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field

from auth import User, get_current_user
from calculators.chart_calculator import ChartCalculator
from credits.credit_service import CreditService
from db import execute, get_conn
from encryption_utils import EncryptionManager

from .image_provider import OpenAIPartnerPortraitProvider, partner_portrait_provider_configured
from .art_direction import derive_art_direction
from .prompt_builder import build_full_body_prompt, build_portrait_prompt
from .service import build_partner_profile
from .synthesizer import RULESET_VERSION, synthesize_partner_profile
from .storage import PartnerPortraitStorage
from .task_queue import enqueue_partner_portrait, task_configuration_error, task_secret, tasks_enabled
from .evidence_builder import build_partner_evidence


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/partner-portrait", tags=["partner-portrait"])
credit_service = CreditService()


def _configuration_error() -> str | None:
    environment = (os.getenv("ENVIRONMENT") or "development").strip().lower()
    if not partner_portrait_provider_configured():
        return "image provider is not configured"
    try:
        PartnerPortraitStorage()
    except RuntimeError as exc:
        return str(exc)
    if environment in {"production", "prod"}:
        queue_error = task_configuration_error()
        if queue_error:
            return queue_error
    return None


def _job_exists(job_id: str, user_id: int) -> bool:
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT 1 FROM partner_portrait_jobs WHERE job_id=%s AND user_id=%s",
            (job_id, user_id),
        )
        return bool(cur.fetchone())


def _require_admin(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def _asset_for_kind(assets_json: Any, kind: str) -> dict[str, Any]:
    try:
        assets = json.loads(assets_json) if isinstance(assets_json, str) else (assets_json or [])
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=404, detail="Partner Portrait asset not found") from exc
    asset = next(
        (item for item in assets if isinstance(item, dict) and item.get("kind") == kind),
        None,
    )
    if not asset or not asset.get("stored_uri"):
        raise HTTPException(status_code=404, detail="Partner Portrait asset not found")
    return asset


def _private_asset_response(job_id: str, kind: str, assets_json: Any) -> Response:
    asset = _asset_for_kind(assets_json, kind)
    try:
        content, content_type, stored_name = PartnerPortraitStorage().read(asset["stored_uri"])
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Unable to read Partner Portrait asset job_id=%s kind=%s: %s", job_id, kind, exc)
        raise HTTPException(status_code=404, detail="Partner Portrait asset not found") from exc
    suffix = Path(stored_name).suffix or ".webp"
    filename = f"astroroshni-partner-{kind.replace('_', '-')}{suffix}"
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "private, max-age=300",
        },
    )


class GeneratePartnerPortraitRequest(BaseModel):
    birth_chart_id: int = Field(gt=0)
    # Accepted only so already-released clients keep working. The backend always
    # replaces these with values derived from the saved chart before charging.
    presentation: Literal["feminine", "masculine"] | None = None
    age_band: Literal["25-34", "35-44", "45-54", "55+"] = "25-34"
    visual_context: Literal[
        "south_asian", "east_southeast_asian", "middle_eastern_north_african",
        "sub_saharan_african", "european", "latin_american", "north_american", "central_asian", "oceania",
        "global_mixed",
    ] | None = None
    clothing_style: Literal[
        "contemporary", "traditional_regional", "modern_formal", "contemporary_indian", "classic_indian",
    ] = "contemporary"
    idempotency_key: str = Field(min_length=8, max_length=100)


class ProcessPartnerPortraitRequest(BaseModel):
    job_id: str = Field(min_length=8, max_length=100)


def init_partner_portrait_tables() -> None:
    with get_conn() as conn:
        execute(
            conn,
            f"""
            CREATE TABLE IF NOT EXISTS partner_portrait_jobs (
                job_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                birth_chart_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                request_json TEXT NOT NULL,
                profile_json TEXT,
                assets_json TEXT,
                error_message TEXT,
                credit_cost INTEGER NOT NULL,
                charged_at TIMESTAMP,
                refunded_at TIMESTAMP,
                idempotency_key TEXT NOT NULL,
                ruleset_version TEXT NOT NULL DEFAULT '{RULESET_VERSION}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(user_id, idempotency_key)
            )
            """,
        )
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_partner_portrait_user_created ON partner_portrait_jobs(user_id, created_at DESC)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_partner_portrait_chart ON partner_portrait_jobs(user_id, birth_chart_id)")
        conn.commit()


def _load_birth_data(user_id: int, chart_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT name, date, time, latitude, longitude, timezone, place, gender
            FROM birth_charts WHERE id = %s AND userid = %s
            """,
            (chart_id, user_id),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError("Birth chart not found")
    decryptor = EncryptionManager()
    return {
        "name": decryptor.decrypt(row[0]),
        "date": decryptor.decrypt(row[1]),
        "time": decryptor.decrypt(row[2]),
        "latitude": float(decryptor.decrypt(str(row[3]))),
        "longitude": float(decryptor.decrypt(str(row[4]))),
        "timezone": row[5],
        "place": decryptor.decrypt(row[6] or ""),
        "gender": row[7] or "",
    }


def _calculate_chart(birth: dict[str, Any]) -> dict[str, Any]:
    from types import SimpleNamespace

    return ChartCalculator({}).calculate_chart(SimpleNamespace(**birth), node_type="mean", ayanamsha="lahiri")


def _portrait_chart_fingerprint(birth: dict[str, Any]) -> str:
    """Identity of every saved-chart field that can change this product."""
    from utils.birth_hash import birth_hash_from_birth_details_dict

    birth_hash = birth_hash_from_birth_details_dict(birth)
    gender = str(birth.get("gender") or "").strip().lower()
    raw_time = str(birth.get("time") or "").strip()
    exact_time = raw_time.split("T", 1)[-1][:8]
    material = json.dumps(
        {"birth_hash": birth_hash, "exact_time": exact_time, "gender": gender},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _legacy_evidence_signature(evidence: Any) -> str | None:
    """Compare pre-fingerprint portraits by the classical evidence that made them."""
    if not isinstance(evidence, dict):
        return None
    relevant = {"d1": evidence.get("d1"), "d9": evidence.get("d9")}
    if not isinstance(relevant["d1"], dict) or not isinstance(relevant["d9"], dict):
        return None
    encoded = json.dumps(relevant, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _job_matches_current_chart(
    request_data: dict[str, Any],
    profile: dict[str, Any] | None,
    current_birth: dict[str, Any],
    *,
    current_evidence_signature: str | None = None,
) -> bool:
    stored = str(request_data.get("chart_fingerprint") or "").strip()
    if stored:
        return hmac.compare_digest(stored, _portrait_chart_fingerprint(current_birth))
    if not profile:
        # A legacy pending job will calculate from the latest saved chart when
        # its worker starts. Keeping it attached avoids a duplicate purchase.
        return True
    stored_signature = _legacy_evidence_signature(profile.get("evidence"))
    return bool(stored_signature and current_evidence_signature and hmac.compare_digest(stored_signature, current_evidence_signature))


def _public_result(profile: dict[str, Any], assets: list[dict[str, str]]) -> dict[str, Any]:
    storage = PartnerPortraitStorage()
    public_assets = [{**asset, "url": storage.display_uri(asset["stored_uri"])} for asset in assets]
    factor_readings = profile.get("factor_readings")
    resolved_summary = profile.get("resolved_summary")
    portrait_inference = profile.get("portrait_inference")
    # Results created before factor readings were added still contain their
    # complete evidence packet. Enrich them when read so an existing paid
    # portrait gains the explanation without requiring another purchase.
    if (not factor_readings or not resolved_summary or portrait_inference is None) and isinstance(profile.get("evidence"), dict):
        enriched = synthesize_partner_profile(profile["evidence"])
        factor_readings = factor_readings or enriched.get("factor_readings")
        resolved_summary = resolved_summary or enriched.get("resolved_summary")
        portrait_inference = portrait_inference or enriched.get("portrait_inference")
    safe_profile = {
        "schema_version": profile.get("schema_version"),
        "ruleset_version": profile.get("ruleset_version"),
        "scope": profile.get("scope"),
        "appearance": profile.get("appearance"),
        "portrait_inference": portrait_inference,
        "personality": profile.get("personality"),
        "factor_readings": factor_readings,
        "resolved_summary": resolved_summary,
        "references": profile.get("references"),
        "method_note": profile.get("method_note"),
        "generation": profile.get("generation"),
        "art_direction": profile.get("art_direction"),
        "chart_factors": {
            "d1_seventh_house": ((profile.get("evidence") or {}).get("d1") or {}).get("seventh_house"),
            "d1_seventh_lord": ((profile.get("evidence") or {}).get("d1") or {}).get("seventh_lord"),
            "d9_seventh_house": ((profile.get("evidence") or {}).get("d9") or {}).get("seventh_house"),
            "d9_seventh_lord": ((profile.get("evidence") or {}).get("d9") or {}).get("seventh_lord"),
            "darakaraka": ((profile.get("evidence") or {}).get("d1") or {}).get("darakaraka"),
        },
    }
    return {"profile": safe_profile, "assets": public_assets}


def _progress_stage(
    status: str,
    profile_json: Any = None,
    assets_json: Any = None,
    started_at: datetime | None = None,
) -> str:
    """Expose genuine generation milestones without changing existing statuses."""
    if status == "completed":
        return "ready"
    if status == "failed":
        return "failed"
    if status == "pending":
        return "queued"
    if not profile_json:
        # Chart synthesis normally completes in well under a second. Some
        # multi-process/database combinations can briefly return the coarse
        # processing row without its newly persisted profile. Do not leave the
        # client claiming that it is still reading the chart while the image
        # provider is already working.
        if status == "processing" and started_at:
            current_time = datetime.now(tz=started_at.tzinfo) if started_at.tzinfo else datetime.now()
            elapsed = current_time - started_at
            if elapsed.total_seconds() >= 5:
                return "creating_portrait"
        return "reading_chart"
    try:
        assets = json.loads(assets_json) if isinstance(assets_json, str) else (assets_json or [])
    except (TypeError, ValueError):
        assets = []
    if any(isinstance(asset, dict) and asset.get("kind") == "portrait" for asset in assets):
        return "creating_full_body"
    return "creating_portrait"


async def _run_generation(job_id: str, user_id: int, request_data: dict[str, Any], cost: int) -> None:
    portrait_uri = ""
    full_body_uri = ""
    try:
        now = datetime.now()
        with get_conn() as conn:
            cur = execute(
                conn,
                """UPDATE partner_portrait_jobs
                   SET status=%s, started_at=%s, profile_json=NULL, assets_json=NULL, error_message=NULL
                   WHERE job_id=%s AND user_id=%s
                   AND charged_at IS NOT NULL
                   AND (status=%s OR (status=%s AND started_at < %s))""",
                ("processing", now, job_id, user_id, "pending", "processing", now - timedelta(minutes=35)),
            )
            conn.commit()
        if getattr(cur, "rowcount", 0) == 0:
            return
        birth = _load_birth_data(user_id, int(request_data["birth_chart_id"]))
        request_data["chart_fingerprint"] = _portrait_chart_fingerprint(birth)
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE partner_portrait_jobs SET request_json=%s WHERE job_id=%s AND user_id=%s",
                (json.dumps(request_data), job_id, user_id),
            )
            conn.commit()
        if request_data.get("source") != "birth_chart_gender_and_coordinates":
            # Supports jobs created by an older API build without trusting the
            # client-supplied presentation or region from that build.
            request_data.update(await derive_art_direction(birth))
        profile = build_partner_profile(_calculate_chart(birth), native_gender=str(birth.get("gender") or ""))
        if profile.get("portrait_readiness") != "ready":
            raise RuntimeError("The chart does not provide enough repeated visual testimony for a responsible portrait")

        seed = int(hashlib.sha256(f"{job_id}:{profile['ruleset_version']}".encode()).hexdigest()[:8], 16)
        provider = OpenAIPartnerPortraitProvider()
        profile["generation"] = provider.metadata
        profile["art_direction"] = {
            "presentation": request_data["presentation"],
            "visual_context": request_data["visual_context"],
            "country_name": request_data["country_name"],
            "country_code": request_data["country_code"],
            "source": request_data["source"],
            "age_band": request_data["age_band"],
            "clothing_style": request_data["clothing_style"],
        }
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE partner_portrait_jobs SET profile_json=%s, ruleset_version=%s WHERE job_id=%s AND user_id=%s",
                (json.dumps(profile), profile["ruleset_version"], job_id, user_id),
            )
            conn.commit()
        storage = PartnerPortraitStorage()
        portrait = await provider.generate_portrait(
            build_portrait_prompt(
                profile,
                presentation=request_data["presentation"],
                age_band=request_data["age_band"],
                clothing_style=request_data["clothing_style"],
                visual_context=request_data["visual_context"],
            ),
            seed,
        )
        portrait_uri = storage.save(
            user_id=user_id, job_id=job_id, kind="portrait", content=portrait.content, content_type=portrait.content_type
        )
        if not _job_exists(job_id, user_id):
            storage.delete(portrait_uri)
            return
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE partner_portrait_jobs SET assets_json=%s WHERE job_id=%s AND user_id=%s",
                (json.dumps([{"kind": "portrait", "stored_uri": portrait_uri}]), job_id, user_id),
            )
            conn.commit()
        full_body = await provider.generate_full_body(
            build_full_body_prompt(
                profile,
                presentation=request_data["presentation"],
                age_band=request_data["age_band"],
                clothing_style=request_data["clothing_style"],
                visual_context=request_data["visual_context"],
            ),
            storage.provider_input_uri(portrait_uri),
            seed,
        )
        full_body_uri = storage.save(
            user_id=user_id, job_id=job_id, kind="full_body", content=full_body.content, content_type=full_body.content_type
        )
        if not _job_exists(job_id, user_id):
            storage.delete(portrait_uri)
            storage.delete(full_body_uri)
            return
        assets = [
            {"kind": "portrait", "stored_uri": portrait_uri},
            {"kind": "full_body", "stored_uri": full_body_uri},
        ]
        with get_conn() as conn:
            cur = execute(
                conn,
                """UPDATE partner_portrait_jobs
                   SET status=%s, profile_json=%s, assets_json=%s, ruleset_version=%s, completed_at=%s
                   WHERE job_id=%s AND user_id=%s""",
                (
                    "completed", json.dumps(profile), json.dumps(assets), profile["ruleset_version"],
                    datetime.now(), job_id, user_id,
                ),
            )
            conn.commit()
        if getattr(cur, "rowcount", 0) == 0:
            storage.delete(portrait_uri)
            storage.delete(full_body_uri)
    except Exception as exc:
        logger.exception("Partner Portrait generation failed job_id=%s", job_id)
        for stored_uri in (portrait_uri, full_body_uri):
            if stored_uri:
                try:
                    PartnerPortraitStorage().delete(stored_uri)
                except Exception:
                    logger.exception("Could not clean up a partial Partner Portrait asset")
        try:
            refund_marker = datetime.now()
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """UPDATE partner_portrait_jobs SET refunded_at=%s
                       WHERE job_id=%s AND user_id=%s AND charged_at IS NOT NULL AND refunded_at IS NULL""",
                    (refund_marker, job_id, user_id),
                )
                conn.commit()
            if getattr(cur, "rowcount", 0) > 0:
                refunded = credit_service.refund_credits(
                    user_id, cost, "partner_portrait", f"Partner Portrait generation refund ({job_id})"
                )
                if not refunded:
                    with get_conn() as conn:
                        execute(conn, "UPDATE partner_portrait_jobs SET refunded_at=NULL WHERE job_id=%s", (job_id,))
                        conn.commit()
        except Exception:
            logger.exception("Partner Portrait refund failed job_id=%s", job_id)
        with get_conn() as conn:
            execute(
                conn,
                """UPDATE partner_portrait_jobs SET status=%s, error_message=%s,
                   completed_at=%s WHERE job_id=%s AND user_id=%s""",
                ("failed", str(exc)[:1000], datetime.now(), job_id, user_id),
            )
            conn.commit()


@router.get("/config")
async def get_partner_portrait_config(current_user: User = Depends(get_current_user)):
    base = credit_service.get_credit_setting("partner_portrait_cost")
    cost = credit_service.get_effective_cost(current_user.userid, base, "partner_portrait_cost")
    return {
        "cost": cost,
        "ruleset_version": RULESET_VERSION,
        "output": ["portrait", "full_body", "classical_profile", "source_trace"],
        "personalized_free_preview": False,
        "available": _configuration_error() is None,
    }


@router.get("/direction/{birth_chart_id}")
async def get_partner_portrait_direction(
    birth_chart_id: int,
    current_user: User = Depends(get_current_user),
):
    try:
        birth = _load_birth_data(current_user.userid, birth_chart_id)
        return await derive_art_direction(birth)
    except ValueError as exc:
        code = "GENDER_REQUIRED" if "Male or Female" in str(exc) else "INVALID_BIRTH_COORDINATES"
        raise HTTPException(status_code=422, detail={"code": code, "message": str(exc)}) from exc
    except RuntimeError as exc:
        logger.warning("Partner Portrait direction unavailable chart_id=%s: %s", birth_chart_id, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/generate", status_code=202)
async def start_partner_portrait(
    request: GeneratePartnerPortraitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    configuration_error = _configuration_error()
    if configuration_error:
        logger.error("Partner Portrait unavailable: %s", configuration_error)
        raise HTTPException(status_code=503, detail="Partner Portrait is temporarily unavailable")
    init_partner_portrait_tables()
    request_data = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT job_id, status FROM partner_portrait_jobs WHERE user_id=%s AND idempotency_key=%s",
            (current_user.userid, request.idempotency_key),
        )
        existing = cur.fetchone()
    if existing:
        return {"job_id": existing[0], "status": existing[1], "reused": True}

    try:
        birth = _load_birth_data(current_user.userid, request.birth_chart_id)
        request_data.update(await derive_art_direction(birth))
        request_data["chart_fingerprint"] = _portrait_chart_fingerprint(birth)
    except ValueError as exc:
        status_code = 404 if str(exc) == "Birth chart not found" else 422
        if status_code == 404:
            detail: str | dict[str, str] = str(exc)
        else:
            code = "GENDER_REQUIRED" if "Male or Female" in str(exc) else "INVALID_BIRTH_COORDINATES"
            detail = {"code": code, "message": str(exc)}
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except RuntimeError as exc:
        logger.warning("Partner Portrait direction unavailable chart_id=%s: %s", request.birth_chart_id, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    base = credit_service.get_credit_setting("partner_portrait_cost")
    cost = credit_service.get_effective_cost(current_user.userid, base, "partner_portrait_cost")
    if credit_service.get_user_credits(current_user.userid) < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. You need {cost} credits.")

    job_id = str(uuid.uuid4())
    with get_conn() as conn:
        execute(
            conn,
            """INSERT INTO partner_portrait_jobs
               (job_id,user_id,birth_chart_id,status,request_json,credit_cost,idempotency_key,ruleset_version)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                job_id, current_user.userid, request.birth_chart_id, "pending",
                json.dumps(request_data), cost, request.idempotency_key, RULESET_VERSION,
            ),
        )
        conn.commit()
    charged = credit_service.spend_credits(
        current_user.userid,
        cost,
        "partner_portrait",
        f"Partner Portrait for chart {request.birth_chart_id}",
        metadata=json.dumps({"job_id": job_id, "birth_chart_id": request.birth_chart_id}),
    )
    if not charged:
        with get_conn() as conn:
            execute(conn, "DELETE FROM partner_portrait_jobs WHERE job_id=%s", (job_id,))
            conn.commit()
        raise HTTPException(status_code=402, detail="Insufficient credits")
    with get_conn() as conn:
        execute(conn, "UPDATE partner_portrait_jobs SET charged_at=%s WHERE job_id=%s", (datetime.now(), job_id))
        conn.commit()
    queued = enqueue_partner_portrait(job_id)
    if not queued:
        if tasks_enabled():
            refunded = credit_service.refund_credits(
                current_user.userid, cost, "partner_portrait", f"Partner Portrait queue refund ({job_id})"
            )
            with get_conn() as conn:
                execute(
                    conn,
                    "UPDATE partner_portrait_jobs SET status=%s,error_message=%s,refunded_at=%s,completed_at=%s WHERE job_id=%s",
                    (
                        "failed",
                        "Generation queue unavailable",
                        datetime.now() if refunded else None,
                        datetime.now(),
                        job_id,
                    ),
                )
                conn.commit()
            detail = (
                "Portrait generation is temporarily unavailable. Your credits were returned."
                if refunded
                else "Portrait generation is temporarily unavailable. Please contact support about this transaction."
            )
            raise HTTPException(status_code=503, detail=detail)
        background_tasks.add_task(_run_generation, job_id, current_user.userid, request_data, cost)
    return {"job_id": job_id, "status": "pending", "cost": cost}


@router.post("/internal/process")
async def process_partner_portrait_job(
    request: ProcessPartnerPortraitRequest,
    x_partner_portrait_task_secret: str = Header(default="", alias="X-Partner-Portrait-Task-Secret"),
):
    expected = task_secret()
    if not expected or not hmac.compare_digest(x_partner_portrait_task_secret, expected):
        raise HTTPException(status_code=403, detail="Invalid worker secret")
    init_partner_portrait_tables()
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT user_id,request_json,credit_cost FROM partner_portrait_jobs WHERE job_id=%s",
            (request.job_id,),
        )
        row = cur.fetchone()
    if not row:
        return {"status": "gone"}
    await _run_generation(request.job_id, int(row[0]), json.loads(row[1]), int(row[2]))
    with get_conn() as conn:
        cur = execute(conn, "SELECT status FROM partner_portrait_jobs WHERE job_id=%s", (request.job_id,))
        current = cur.fetchone()
    if current and current[0] == "processing":
        # Preserve Cloud Tasks retry semantics if an earlier worker died while it
        # held the lease. A stale lease becomes claimable after 35 minutes.
        raise HTTPException(status_code=503, detail="Portrait job is still processing")
    return {"status": current[0] if current else "gone"}


@router.get("/status/{job_id}")
async def get_partner_portrait_status(
    job_id: str,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    init_partner_portrait_tables()
    with get_conn() as conn:
        cur = execute(
            conn,
            """SELECT status,profile_json,assets_json,error_message,credit_cost,refunded_at,completed_at,started_at,
                      birth_chart_id,request_json
               FROM partner_portrait_jobs WHERE job_id=%s AND user_id=%s""",
            (job_id, current_user.userid),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Partner Portrait job not found")
    result: dict[str, Any] = {
        "job_id": job_id,
        "status": row[0],
        "cost": row[4],
        "progress_stage": _progress_stage(row[0], row[1], row[2], row[7]),
    }
    try:
        current_birth = _load_birth_data(current_user.userid, int(row[8]))
        request_data = json.loads(row[9])
        profile = json.loads(row[1]) if row[1] else None
        current_signature = None
        if profile and not request_data.get("chart_fingerprint"):
            current_evidence = build_partner_evidence(
                _calculate_chart(current_birth), native_gender=str(current_birth.get("gender") or "")
            )
            current_signature = _legacy_evidence_signature(current_evidence)
        result["chart_matches_current_version"] = _job_matches_current_chart(
            request_data, profile, current_birth, current_evidence_signature=current_signature
        )
    except (ValueError, TypeError, json.JSONDecodeError):
        result["chart_matches_current_version"] = False
    if row[7]:
        result["started_at"] = row[7]
    if row[0] == "completed":
        result["data"] = _public_result(json.loads(row[1]), json.loads(row[2]))
        result["completed_at"] = row[6]
    elif row[0] == "failed":
        result["error"] = row[3] or "Generation failed"
        result["credits_refunded"] = bool(row[5])
    return result


@router.get("/history")
async def get_partner_portrait_history(current_user: User = Depends(get_current_user)):
    init_partner_portrait_tables()
    with get_conn() as conn:
        cur = execute(
            conn,
            """SELECT job_id,birth_chart_id,status,request_json,profile_json,assets_json,created_at,completed_at
               FROM partner_portrait_jobs WHERE user_id=%s
               ORDER BY created_at DESC LIMIT 20""",
            (current_user.userid,),
        )
        rows = cur.fetchall() or []
    items = []
    current_chart_cache: dict[int, tuple[dict[str, Any] | None, str | None]] = {}
    for row in rows:
        req = json.loads(row[3])
        profile = json.loads(row[4]) if row[4] else None
        data = _public_result(profile, json.loads(row[5])) if row[2] == "completed" and profile and row[5] else None
        chart_id = int(row[1])
        if chart_id not in current_chart_cache:
            try:
                current_birth = _load_birth_data(current_user.userid, chart_id)
                current_signature = None
                if not req.get("chart_fingerprint"):
                    current_evidence = build_partner_evidence(
                        _calculate_chart(current_birth), native_gender=str(current_birth.get("gender") or "")
                    )
                    current_signature = _legacy_evidence_signature(current_evidence)
                current_chart_cache[chart_id] = (current_birth, current_signature)
            except (ValueError, TypeError):
                current_chart_cache[chart_id] = (None, None)
        current_birth, current_signature = current_chart_cache[chart_id]
        if current_birth and not req.get("chart_fingerprint") and current_signature is None:
            current_evidence = build_partner_evidence(
                _calculate_chart(current_birth), native_gender=str(current_birth.get("gender") or "")
            )
            current_signature = _legacy_evidence_signature(current_evidence)
            current_chart_cache[chart_id] = (current_birth, current_signature)
        matches_current = bool(current_birth) and _job_matches_current_chart(
            req, profile, current_birth, current_evidence_signature=current_signature
        )
        items.append({
            "job_id": row[0], "birth_chart_id": row[1], "status": row[2],
            "presentation": req.get("presentation"), "visual_context": req.get("visual_context", "global_mixed"),
            "created_at": row[6], "completed_at": row[7],
            "matches_current_chart": matches_current,
            "thumbnail_url": next((a["url"] for a in data["assets"] if a["kind"] == "portrait"), None) if data else None,
        })
    return {"items": items}


@router.get("/admin/job/{job_id}")
async def get_partner_portrait_admin_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Show the paid result and source chart to an authenticated administrator."""
    _require_admin(current_user)
    init_partner_portrait_tables()
    with get_conn() as conn:
        cur = execute(
            conn,
            """SELECT user_id,birth_chart_id,status,request_json,assets_json,error_message,
                      credit_cost,charged_at,refunded_at,ruleset_version,created_at,started_at,completed_at
               FROM partner_portrait_jobs WHERE job_id=%s""",
            (job_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Partner Portrait job not found")

    request_data: dict[str, Any] = {}
    if row[3]:
        try:
            parsed_request = json.loads(row[3]) if isinstance(row[3], str) else row[3]
            if isinstance(parsed_request, dict):
                request_data = parsed_request
        except (TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Invalid Partner Portrait request JSON job_id=%s", job_id)
    try:
        chart = _load_birth_data(int(row[0]), int(row[1]))
    except ValueError:
        chart = None
    chart_matches_generated_version: bool | None = None
    stored_fingerprint = str(request_data.get("chart_fingerprint") or "").strip()
    if chart and stored_fingerprint:
        chart_matches_generated_version = hmac.compare_digest(
            stored_fingerprint,
            _portrait_chart_fingerprint(chart),
        )

    asset_kinds: list[str] = []
    if row[4]:
        try:
            parsed_assets = json.loads(row[4]) if isinstance(row[4], str) else row[4]
            asset_kinds = [
                item["kind"]
                for item in (parsed_assets or [])
                if isinstance(item, dict) and item.get("kind") in {"portrait", "full_body"} and item.get("stored_uri")
            ]
        except (TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Invalid Partner Portrait assets JSON job_id=%s", job_id)

    return {
        "job_id": job_id,
        "user_id": int(row[0]),
        "birth_chart_id": int(row[1]),
        "status": row[2],
        "error": row[5],
        "credit_cost": row[6],
        "charged_at": row[7],
        "refunded_at": row[8],
        "ruleset_version": row[9],
        "created_at": row[10],
        "started_at": row[11],
        "completed_at": row[12],
        "chart": chart,
        "chart_matches_generated_version": chart_matches_generated_version,
        "generation": {
            key: request_data.get(key)
            for key in ("presentation", "age_band", "visual_context", "country_name", "country_code", "clothing_style")
            if request_data.get(key) is not None
        },
        "assets": [
            {
                "kind": kind,
                "url": f"/api/partner-portrait/admin/job/{job_id}/asset/{kind}",
            }
            for kind in asset_kinds
        ],
    }


@router.get("/admin/job/{job_id}/asset/{kind}")
async def get_partner_portrait_admin_asset(
    job_id: str,
    kind: Literal["portrait", "full_body"],
    current_user: User = Depends(get_current_user),
):
    """Stream a private generated image to an authenticated administrator."""
    _require_admin(current_user)
    init_partner_portrait_tables()
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT status,assets_json FROM partner_portrait_jobs WHERE job_id=%s",
            (job_id,),
        )
        row = cur.fetchone()
    if not row or row[0] != "completed" or not row[1]:
        raise HTTPException(status_code=404, detail="Partner Portrait asset not found")
    return _private_asset_response(job_id, kind, row[1])


@router.get("/asset/{job_id}/{kind}")
async def get_partner_portrait_asset(
    job_id: str,
    kind: Literal["portrait", "full_body"],
    current_user: User = Depends(get_current_user),
):
    """Return one paid portrait through the authenticated API.

    Browser share/download actions cannot attach the bearer token to a plain
    storage link. Serving the private bytes here keeps ownership enforcement
    intact and avoids expired signed URLs opening as blank tabs.
    """
    init_partner_portrait_tables()
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT status,assets_json FROM partner_portrait_jobs WHERE job_id=%s AND user_id=%s",
            (job_id, current_user.userid),
        )
        row = cur.fetchone()
    if not row or row[0] != "completed" or not row[1]:
        raise HTTPException(status_code=404, detail="Partner Portrait asset not found")
    return _private_asset_response(job_id, kind, row[1])
