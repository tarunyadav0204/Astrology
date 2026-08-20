from __future__ import annotations

import logging
import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator
from psycopg2.pool import PoolError
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from birth_charts.routes import _row_to_chart
from credits.entitlements import ASTROLOGER_TOOLS_ENTITLEMENT, require_entitlement
from db import execute, get_conn
from utils.timezone_service import get_iana_timezone
from utils.admin_settings import homepage_fomo_enabled_for_user

from .contracts import BirthChartInput, PredictionRequest, SCHEMA_VERSION
from .engine import ENGINE_VERSION
from .errors import PredictionEngineError
from .fomo_presentation import normalize_fomo_locale
from .fomo_presentation import FOMO_PRESENTATION_VERSION
from .fomo_repository import (
    FOMO_EVENT_TYPES,
    HOMEPAGE_SELECTION_VERSION,
    FomoSnapshotRepository,
    birth_chart_hash,
    snapshot_cache_key,
)
from .homepage_next_peak import generate_homepage_next_peak
from .homepage_prompts import HOMEPAGE_PROMPT_KEYS, HomepagePromptRepository
from .profiles import get_profile
from .service import PredictionService
from .manifestation_synthesis import synthesize_manifestations
from .event_windows import EVENT_DEFINITIONS, EventWindowEngine
from .primitives import build_calculation_context


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prediction-engine", tags=["prediction-engine"])
fomo_repository = FomoSnapshotRepository()
homepage_prompt_repository = HomepagePromptRepository()
HOMEPAGE_FOMO_HORIZON_DAYS = 90
HOMEPAGE_FOMO_MAXIMUM_RESULTS = 24
# Prompt state, presentation reads, and analytics share one auxiliary DB slot.
# Together with the two admitted homepage requests below, this feature can use
# at most three of the API worker's four pooled connections.
_FOMO_AUX_DB_SEMAPHORE = asyncio.Semaphore(1)
_FOMO_AUX_DB_TIMEOUT_SECONDS = 0.1
# FOMO is optional homepage work. Keep it in a dedicated executor and admit at
# most two operations per API worker so the four-connection API pool retains
# capacity for chat, credits, and other critical requests.
_FOMO_REQUEST_SEMAPHORE = asyncio.Semaphore(2)
_FOMO_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="homepage-fomo",
)
_FOMO_ADMISSION_TIMEOUT_SECONDS = 0.05
_FOMO_CALCULATION_TIMEOUT_SECONDS = 90
_FOMO_CLEANUP_INTERVAL_SECONDS = 60 * 60
_FOMO_CLEANUP_RETRY_SECONDS = 5 * 60
_FOMO_CLEANUP_LOCK = asyncio.Lock()
_fomo_cleanup_next_at = 0.0
_EVENT_WINDOW_CACHE_TTL_SECONDS = 30 * 60
_EVENT_WINDOW_CACHE_MAXIMUM = 12
_event_window_cache: Dict[tuple, tuple[float, Dict[str, Any]]] = {}
_event_window_cache_lock = Lock()


class FomoGenerationInProgress(RuntimeError):
    """Another worker currently owns generation for the same cache key."""


class ActivationExplorerRequest(BaseModel):
    birth_chart_id: Optional[int] = None
    birth_data: Optional[Dict[str, Any]] = None
    as_of: date = Field(default_factory=date.today)
    horizon_days: int = Field(default=90, ge=1, le=366)
    maximum_candidates: int = Field(default=100, ge=1, le=100)
    trace: bool = True
    language: str = "en"

    @model_validator(mode="after")
    def require_chart_source(self):
        if self.birth_chart_id is None and not self.birth_data:
            raise ValueError("birth_chart_id or birth_data is required")
        return self


class EventWindowRequest(BaseModel):
    birth_chart_id: Optional[int] = None
    birth_data: Optional[Dict[str, Any]] = None
    event_key: str = "job_change"
    year: int = Field(ge=1900, le=2200)
    include_developing: bool = False

    @model_validator(mode="after")
    def validate_request(self):
        if self.birth_chart_id is None and not self.birth_data:
            raise ValueError("birth_chart_id or birth_data is required")
        if self.event_key not in EVENT_DEFINITIONS:
            raise ValueError(f"Unsupported event focus: {self.event_key}")
        return self


class FomoEventItem(BaseModel):
    event_id: str = Field(min_length=8, max_length=120)
    presentation_id: Optional[str] = Field(default=None, max_length=120)
    event_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FomoEventRequest(FomoEventItem):
    snapshot_id: str = Field(min_length=8, max_length=120)


class FomoEventBatchRequest(BaseModel):
    snapshot_id: str = Field(min_length=8, max_length=120)
    events: List[FomoEventItem] = Field(min_length=1, max_length=50)


class FomoPreferenceRequest(BaseModel):
    homepage_disabled: bool


class HomepagePromptShownRequest(BaseModel):
    prompt_key: str
    session_id: Optional[str] = Field(default=None, max_length=120)


def _load_owned_birth_chart(chart_id: int, user_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT id, userid, name, date, time, latitude, longitude, timezone,
                   created_at, place, gender, relation, relation_order,
                   relation_side, relation_label, is_family_member
            FROM birth_charts
            WHERE id = %s AND userid = %s
            """,
            (chart_id, user_id),
        )
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Birth chart not found")
    return _row_to_chart(row)


def _load_homepage_birth_chart(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT id, userid, name, date, time, latitude, longitude, timezone,
                   created_at, place, gender, relation, relation_order,
                   relation_side, relation_label, is_family_member
            FROM birth_charts
            WHERE userid = %s
            ORDER BY
                CASE WHEN LOWER(COALESCE(relation, '')) = 'self' THEN 0 ELSE 1 END,
                created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    return _row_to_chart(row) if row else None


def _normalise_birth_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    value = dict(payload)
    if value.get("chart_id") is not None and value.get("birth_chart_id") is None:
        value["birth_chart_id"] = value["chart_id"]
    if value.get("id") is not None and value.get("birth_chart_id") is None:
        value["birth_chart_id"] = value["id"]
    if not value.get("timezone") and value.get("latitude") is not None and value.get("longitude") is not None:
        value["timezone"] = get_iana_timezone(
            float(value["latitude"]),
            float(value["longitude"]),
        )
    value["date"] = str(value.get("date") or "").split("T", 1)[0]
    raw_time = str(value.get("time") or "")
    value["time"] = raw_time.split("T", 1)[-1][:8] if "T" in raw_time else raw_time[:8]
    return value


def _generate_activation_dossier(payload: ActivationExplorerRequest, chart: Dict[str, Any]) -> Dict[str, Any]:
    birth = BirthChartInput.from_mapping(_normalise_birth_data(chart))
    result = PredictionService().generate(
        PredictionRequest(
            birth=birth,
            as_of=payload.as_of,
            horizon_days=payload.horizon_days,
            maximum_candidates=payload.maximum_candidates,
            trace=payload.trace,
            exploration_mode=True,
            language=payload.language,
        ),
        include_exact_transit_returns=True,
    )
    response = result.to_dict(include_evidence=payload.trace)
    response["chart"] = {
        "id": birth.birth_chart_id,
        "name": birth.name,
        "date": birth.date,
        "time": birth.time,
        "place": birth.place,
    }
    return response


@router.post("/activation-explorer")
async def get_activation_explorer(
    payload: ActivationExplorerRequest,
    current_user: User = Depends(get_current_user),
):
    """Return a deterministic, traceable activation dossier for one chart."""
    try:
        require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
        chart = (
            _load_owned_birth_chart(payload.birth_chart_id, current_user.userid)
            if payload.birth_chart_id is not None
            else dict(payload.birth_data or {})
        )
        response = await run_in_threadpool(_generate_activation_dossier, payload, chart)
        deterministic = response.get("chart_manifestations") or []
        if deterministic:
            # LLM receives only subject + activated house significations + tone.
            # Timing, dasha, evidence and reasons stay on the deterministic rows.
            synthesis = await synthesize_manifestations(
                deterministic=deterministic,
                locale=payload.language or "en",
            )
            response["chart_manifestations_deterministic"] = deterministic
            response["chart_manifestations"] = synthesis.get("manifestations") or deterministic
            response["manifestation_synthesis"] = {
                "version": synthesis.get("synthesis_version"),
                "cached_or_generated": not bool(synthesis.get("synthesis_error")),
            }
        return response
    except HTTPException:
        raise
    except PredictionEngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Activation Explorer calculation failed for user=%s chart=%s",
            current_user.userid,
            payload.birth_chart_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Activation calculation failed. No fallback result was generated.",
        ) from exc


def _generate_event_window_search(payload: EventWindowRequest, chart: Dict[str, Any]) -> Dict[str, Any]:
    birth = BirthChartInput.from_mapping(_normalise_birth_data(chart))
    cache_key = (
        birth.birth_chart_id, birth.date, birth.time, birth.latitude, birth.longitude,
        str(birth.timezone), payload.year, payload.event_key, payload.include_developing,
    )
    now = time.monotonic()
    with _event_window_cache_lock:
        cached = _event_window_cache.get(cache_key)
        if cached and now - cached[0] <= _EVENT_WINDOW_CACHE_TTL_SECONDS:
            return {**cached[1], "cache_hit": True}
        if cached:
            _event_window_cache.pop(cache_key, None)
    start = date(payload.year, 1, 1)
    end = date(payload.year, 12, 31)
    request = PredictionRequest(
        birth=birth,
        as_of=start,
        horizon_days=(end - start).days + 1,
        maximum_candidates=100,
        trace=False,
        exploration_mode=True,
        subjects=("self",),
    )
    # Build strict ephemeris/dasha state once.  Both the house ledger and the
    # higher-level event resolver consume the same immutable context.
    calculation = build_calculation_context(
        birth,
        start,
        end,
        include_exact_transit_returns=True,
    )
    result = PredictionService().generate_from_context(request, calculation)
    response = EventWindowEngine().resolve(
        event_key=payload.event_key,
        calculation=calculation,
        activations=result.house_activations,
        include_developing=payload.include_developing,
    )
    response.update({
        "year": payload.year,
        "as_of": start.isoformat(),
        "horizon_end": end.isoformat(),
        "chart": {
            "id": birth.birth_chart_id,
            "name": birth.name,
            "date": birth.date,
            "time": birth.time,
            "place": birth.place,
        },
        "cache_hit": False,
    })
    with _event_window_cache_lock:
        if len(_event_window_cache) >= _EVENT_WINDOW_CACHE_MAXIMUM:
            oldest_key = min(_event_window_cache, key=lambda key: _event_window_cache[key][0])
            _event_window_cache.pop(oldest_key, None)
        _event_window_cache[cache_key] = (now, response)
    return response


@router.post("/event-windows")
async def get_event_windows(
    payload: EventWindowRequest,
    current_user: User = Depends(get_current_user),
):
    """Search one calendar year with an auditable, event-specific definition."""
    try:
        require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
        chart = (
            _load_owned_birth_chart(payload.birth_chart_id, current_user.userid)
            if payload.birth_chart_id is not None
            else dict(payload.birth_data or {})
        )
        return await run_in_threadpool(_generate_event_window_search, payload, chart)
    except HTTPException:
        raise
    except PredictionEngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Event-window calculation failed for user=%s chart=%s event=%s year=%s",
            current_user.userid,
            payload.birth_chart_id,
            payload.event_key,
            payload.year,
        )
        raise HTTPException(
            status_code=500,
            detail="Event-window calculation failed. No fallback result was generated.",
        ) from exc


def _generate_homepage_fomo(
    *,
    userid: int,
    chart: Dict[str, Any],
    locale: str,
    limit: int,
    force_display: bool = False,
    include_ineligible: bool = False,
    _pending_synthesis: Optional[List] = None,
) -> Dict[str, Any]:
    birth = BirthChartInput.from_mapping(_normalise_birth_data(chart))
    profile = get_profile("parashari_fomo_v1")
    chart_hash = birth_chart_hash(chart)
    as_of = date.today()
    cache_key = snapshot_cache_key(
        userid=userid,
        birth_chart_id=int(chart["id"]),
        chart_hash=chart_hash,
        as_of=as_of,
        horizon_days=HOMEPAGE_FOMO_HORIZON_DAYS,
        profile=profile.key,
        profile_version=profile.version,
        engine_version=ENGINE_VERSION,
        schema_version=SCHEMA_VERSION,
        locale=locale,
        provider_versions=profile.provider_versions,
        ephemeris_settings=profile.conventions.__dict__,
        presentation_version=(
            f"{FOMO_PRESENTATION_VERSION}:{HOMEPAGE_SELECTION_VERSION}"
        ),
    )
    stored = fomo_repository.load_cached(
        userid=userid,
        cache_key=cache_key,
        chart_name=str(chart.get("name") or ""),
        limit=limit,
    )
    # Heal partial snapshots: more LLM themes may have been cached since the
    # first write (shared theme cache / Activation Explorer / later synthesis).
    if stored is not None:
        refreshed = fomo_repository.refresh_teasers_from_llm_cache(
            userid=userid,
            cache_key=cache_key,
            chart_name=str(chart.get("name") or ""),
            locale=locale,
            limit=limit,
        )
        if refreshed is not None:
            stored = refreshed
    llm_wording_pending = False
    if stored is None or not stored.teasers:
        generation_owner = uuid.uuid4().hex
        claimed = fomo_repository.try_claim_generation(
            cache_key=cache_key,
            owner_token=generation_owner,
        )
        if not claimed:
            # If we already have an empty snapshot, do not throw an error:
            # just keep the card hidden until LLM wording cache is ready.
            if stored is not None:
                return {"status": "analyzing", "teasers": []}
            raise FomoGenerationInProgress("Chart themes are already being generated")
        try:
            # A competing worker may have completed between the initial cache
            # read and this lease acquisition.
            stored = fomo_repository.load_cached(
                userid=userid,
                cache_key=cache_key,
                chart_name=str(chart.get("name") or ""),
                limit=limit,
            )
            if stored is None or not stored.teasers:
                result = PredictionService().generate(
                    PredictionRequest(
                        birth=birth,
                        as_of=as_of,
                        horizon_days=HOMEPAGE_FOMO_HORIZON_DAYS,
                        subjects=("self", "spouse", "mother", "father"),
                        maximum_candidates=HOMEPAGE_FOMO_MAXIMUM_RESULTS,
                        trace=True,
                        exploration_mode=True,
                        language=locale,
                    )
                )
                # Collect deterministic data for async LLM synthesis later
                # (cannot run async LLM calls from this sync thread without
                # gRPC event loop conflicts).
                deterministic = [m.to_dict() for m in result.chart_manifestations]
                if deterministic and _pending_synthesis is not None:
                    _pending_synthesis.extend(deterministic)
                stored, llm_wording_pending = fomo_repository.save(
                    userid=userid,
                    birth_chart_id=int(chart["id"]),
                    chart_name=str(chart.get("name") or ""),
                    cache_key=cache_key,
                    chart_hash=chart_hash,
                    as_of=as_of,
                    horizon_days=HOMEPAGE_FOMO_HORIZON_DAYS,
                    locale=locale,
                    result=result,
                    limit=limit,
                )
        finally:
            try:
                fomo_repository.release_generation_claim(
                    cache_key=cache_key,
                    owner_token=generation_owner,
                )
            except Exception:
                logger.warning(
                    "Could not release FOMO generation lease cache=%s",
                    cache_key[:12],
                    exc_info=True,
                )
    if llm_wording_pending:
        return {"status": "analyzing", "teasers": []}
    if not stored.teasers:
        return {"status": "empty", "teasers": []}
    auto_eligible = bool(force_display or fomo_repository.eligible_for_display(
        userid=userid,
        display_signature=stored.display_signature,
    ))
    if not auto_eligible and not include_ineligible:
        return {"status": "cooldown", "teasers": []}
    return {
        "status": "ready",
        "auto_eligible": auto_eligible,
        **stored.to_public_dict(),
    }


async def _admit_homepage_fomo() -> None:
    try:
        await asyncio.wait_for(
            _FOMO_REQUEST_SEMAPHORE.acquire(),
            timeout=_FOMO_ADMISSION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="Chart themes are busy. Please try again shortly.",
        ) from exc


async def _cleanup_expired_fomo_if_due() -> None:
    global _fomo_cleanup_next_at
    now = time.monotonic()
    if now < _fomo_cleanup_next_at:
        return
    async with _FOMO_CLEANUP_LOCK:
        now = time.monotonic()
        if now < _fomo_cleanup_next_at:
            return
        # Advance before the DB call so concurrent requests never fan out
        # cleanup writes. On failure, use a shorter bounded retry interval.
        _fomo_cleanup_next_at = now + _FOMO_CLEANUP_INTERVAL_SECONDS
        try:
            await run_in_threadpool(fomo_repository.delete_expired)
        except Exception:
            _fomo_cleanup_next_at = time.monotonic() + _FOMO_CLEANUP_RETRY_SECONDS
            logger.warning("Deferred FOMO cleanup failed", exc_info=True)


async def _run_fomo_aux_db(func, /, *args, **kwargs):
    try:
        await asyncio.wait_for(
            _FOMO_AUX_DB_SEMAPHORE.acquire(),
            timeout=_FOMO_AUX_DB_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise PoolError("FOMO auxiliary DB capacity is busy") from exc
    try:
        return await run_in_threadpool(func, *args, **kwargs)
    finally:
        _FOMO_AUX_DB_SEMAPHORE.release()


@router.get("/homepage-fomo")
async def get_homepage_fomo(
    request: Request,
    language: str = Query(default="en", min_length=2, max_length=16),
    limit: int = Query(default=24, ge=1, le=24),
    birth_chart_id: Optional[int] = Query(default=None, ge=1),
    force_display: bool = Query(default=False),
    include_ineligible: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
):
    """Return safe teaser copy only; the evidence snapshot remains server-side."""
    capacity_owned_by_request = False
    try:
        if not homepage_fomo_enabled_for_user(current_user.userid):
            return {"status": "disabled", "teasers": []}
        locale = normalize_fomo_locale(language)
        await _admit_homepage_fomo()
        capacity_owned_by_request = True
        await _cleanup_expired_fomo_if_due()
        if birth_chart_id is not None:
            chart = await run_in_threadpool(
                _load_owned_birth_chart,
                birth_chart_id,
                current_user.userid,
            )
        else:
            chart = await run_in_threadpool(
                _load_homepage_birth_chart,
                current_user.userid,
            )
        if not chart:
            return {"status": "no_chart", "teasers": []}
        client_host = str(request.client.host if request.client else "").strip()
        local_force_display = bool(
            force_display and client_host in {"127.0.0.1", "::1", "localhost"}
        )
        pending_synthesis: List[Dict[str, Any]] = []
        loop = asyncio.get_running_loop()
        calculation = loop.run_in_executor(
            _FOMO_EXECUTOR,
            lambda: _generate_homepage_fomo(
                userid=current_user.userid,
                chart=chart,
                locale=locale,
                limit=limit,
                force_display=local_force_display,
                include_ineligible=include_ineligible,
                _pending_synthesis=pending_synthesis,
            ),
        )
        # Capacity follows the actual synchronous work, not the HTTP request.
        # If the client disconnects or times out, the slot remains occupied until
        # the bounded executor job really finishes.
        calculation.add_done_callback(
            lambda _future: _FOMO_REQUEST_SEMAPHORE.release()
        )
        capacity_owned_by_request = False
        fomo_result = await asyncio.wait_for(
            asyncio.shield(calculation),
            timeout=_FOMO_CALCULATION_TIMEOUT_SECONDS,
        )
        # Always synthesize after a fresh engine run. A partial shared-cache hit
        # used to return status=ready with 1 tile and skip this step, locking
        # production FOMO at a single card.
        if pending_synthesis:
            try:
                await synthesize_manifestations(
                    deterministic=pending_synthesis,
                    locale=locale,
                )
                profile = get_profile("parashari_fomo_v1")
                refresh_key = snapshot_cache_key(
                    userid=current_user.userid,
                    birth_chart_id=int(chart["id"]),
                    chart_hash=birth_chart_hash(chart),
                    as_of=date.today(),
                    horizon_days=HOMEPAGE_FOMO_HORIZON_DAYS,
                    profile=profile.key,
                    profile_version=profile.version,
                    engine_version=ENGINE_VERSION,
                    schema_version=SCHEMA_VERSION,
                    locale=locale,
                    provider_versions=profile.provider_versions,
                    ephemeris_settings=profile.conventions.__dict__,
                    presentation_version=(
                        f"{FOMO_PRESENTATION_VERSION}:{HOMEPAGE_SELECTION_VERSION}"
                    ),
                )
                refreshed = await run_in_threadpool(
                    fomo_repository.refresh_teasers_from_llm_cache,
                    userid=current_user.userid,
                    cache_key=refresh_key,
                    chart_name=str(chart.get("name") or ""),
                    locale=locale,
                    limit=limit,
                )
                if refreshed is not None and refreshed.teasers:
                    auto_eligible = bool(
                        local_force_display
                        or fomo_repository.eligible_for_display(
                            userid=current_user.userid,
                            display_signature=refreshed.display_signature,
                        )
                    )
                    if not auto_eligible and not include_ineligible:
                        fomo_result = {"status": "cooldown", "teasers": []}
                    else:
                        fomo_result = {
                            "status": "ready",
                            "auto_eligible": auto_eligible,
                            **refreshed.to_public_dict(),
                        }
            except Exception:
                logger.warning(
                    "FOMO post-synthesis re-save failed; card will appear on next poll",
                    exc_info=True,
                )
        return fomo_result
    except asyncio.TimeoutError as exc:
        logger.warning(
            "Homepage FOMO calculation timed out user=%s",
            current_user.userid,
        )
        raise HTTPException(
            status_code=503,
            detail="Chart themes are still being prepared. Please try again later.",
        ) from exc
    except FomoGenerationInProgress as exc:
        raise HTTPException(
            status_code=503,
            detail="Chart themes are already being prepared. Please try again shortly.",
        ) from exc
    except PoolError as exc:
        logger.warning(
            "Homepage FOMO skipped because DB pool is busy user=%s",
            current_user.userid,
        )
        raise HTTPException(
            status_code=503,
            detail="Chart themes are temporarily unavailable.",
        ) from exc
    except HTTPException:
        raise
    except PredictionEngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Homepage FOMO failed user=%s",
            current_user.userid,
        )
        raise HTTPException(
            status_code=500,
            detail="Could not prepare chart themes.",
        ) from exc
    finally:
        if capacity_owned_by_request:
            _FOMO_REQUEST_SEMAPHORE.release()


@router.get("/homepage-next-peak")
async def get_homepage_next_peak(
    birth_chart_id: Optional[int] = Query(default=None, ge=1),
    horizon_days: int = Query(default=120, ge=30, le=365),
    current_user: User = Depends(get_current_user),
):
    """Forward-looking Parashari peak window for the home card."""
    try:
        if birth_chart_id is not None:
            chart = await run_in_threadpool(
                _load_owned_birth_chart,
                birth_chart_id,
                current_user.userid,
            )
        else:
            chart = await run_in_threadpool(
                _load_homepage_birth_chart,
                current_user.userid,
            )
        if not chart:
            return {"status": "no_chart", "peak": None}
        return await asyncio.wait_for(
            run_in_threadpool(
                generate_homepage_next_peak,
                chart,
                as_of=date.today(),
                horizon_days=horizon_days,
            ),
            timeout=45,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="Your upcoming chart timing is still being prepared. Please try again shortly.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Homepage next peak failed user=%s", current_user.userid)
        raise HTTPException(
            status_code=500,
            detail="Could not prepare upcoming chart timing.",
        ) from exc


@router.get("/homepage-prompts/state")
async def get_homepage_prompt_state(
    current_user: User = Depends(get_current_user),
):
    try:
        prompts = await _run_fomo_aux_db(
            homepage_prompt_repository.state,
            current_user.userid,
        )
    except PoolError as exc:
        raise HTTPException(
            status_code=503,
            detail="Homepage prompt state is temporarily unavailable.",
        ) from exc
    return {"prompts": prompts}


@router.post("/homepage-prompts/shown")
async def record_homepage_prompt_shown(
    payload: HomepagePromptShownRequest,
    current_user: User = Depends(get_current_user),
):
    if payload.prompt_key not in HOMEPAGE_PROMPT_KEYS:
        raise HTTPException(status_code=422, detail="Unsupported homepage prompt")
    try:
        state = await _run_fomo_aux_db(
            homepage_prompt_repository.record_shown,
            userid=current_user.userid,
            prompt_key=payload.prompt_key,
            session_id=payload.session_id,
        )
    except PoolError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not record homepage prompt exposure.",
        ) from exc
    return {"prompt_key": payload.prompt_key, "state": state}


@router.get("/homepage-fomo/{presentation_id}")
async def open_homepage_fomo(
    presentation_id: str,
    snapshot_id: str = Query(min_length=8, max_length=120),
    current_user: User = Depends(get_current_user),
):
    try:
        presentation = await _run_fomo_aux_db(
            fomo_repository.load_owned_presentation,
            userid=current_user.userid,
            snapshot_id=snapshot_id,
            presentation_id=presentation_id,
        )
    except PoolError as exc:
        raise HTTPException(
            status_code=503,
            detail="Chart theme is temporarily unavailable.",
        ) from exc
    if not presentation:
        raise HTTPException(status_code=404, detail="Chart theme not found or expired")
    return presentation


@router.post("/homepage-fomo/events")
async def record_homepage_fomo_event(
    payload: FomoEventRequest,
    current_user: User = Depends(get_current_user),
):
    if payload.event_type not in FOMO_EVENT_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported event type")
    if len(_canonical_event_metadata(payload.metadata)) > 2000:
        raise HTTPException(status_code=422, detail="Event metadata is too large")
    try:
        inserted = await _run_fomo_aux_db(
            fomo_repository.record_event,
            userid=current_user.userid,
            event_id=payload.event_id,
            snapshot_id=payload.snapshot_id,
            presentation_id=payload.presentation_id,
            event_type=payload.event_type,
            metadata=payload.metadata,
        )
    except PoolError:
        logger.warning(
            "Dropped FOMO analytics event because DB pool is busy user=%s event=%s",
            current_user.userid,
            payload.event_type,
        )
        return {"recorded": False, "dropped": True, "reason": "database_busy"}
    if not inserted:
        try:
            owned = await _run_fomo_aux_db(
                fomo_repository.load_owned_presentation,
                userid=current_user.userid,
                snapshot_id=payload.snapshot_id,
                presentation_id=payload.presentation_id or "",
            ) if payload.presentation_id else True
        except PoolError:
            return {"recorded": False, "dropped": True, "reason": "database_busy"}
        if not owned:
            raise HTTPException(status_code=404, detail="Chart theme not found or expired")
    return {"recorded": inserted}


@router.post("/homepage-fomo/events/batch")
async def record_homepage_fomo_events(
    payload: FomoEventBatchRequest,
    current_user: User = Depends(get_current_user),
):
    event_rows = []
    for event in payload.events:
        if event.event_type not in FOMO_EVENT_TYPES:
            raise HTTPException(status_code=422, detail="Unsupported event type")
        if len(_canonical_event_metadata(event.metadata)) > 2000:
            raise HTTPException(status_code=422, detail="Event metadata is too large")
        event_rows.append(event.model_dump())
    if sum(len(_canonical_event_metadata(row["metadata"])) for row in event_rows) > 20000:
        raise HTTPException(status_code=422, detail="Event batch metadata is too large")
    try:
        inserted = await _run_fomo_aux_db(
            fomo_repository.record_events,
            userid=current_user.userid,
            snapshot_id=payload.snapshot_id,
            events=event_rows,
        )
    except PoolError:
        logger.warning(
            "Dropped FOMO analytics batch because DB pool is busy user=%s count=%s",
            current_user.userid,
            len(event_rows),
        )
        return {
            "recorded": 0,
            "dropped": len(event_rows),
            "reason": "database_busy",
        }
    if inserted is None:
        raise HTTPException(status_code=404, detail="Chart themes not found or expired")
    return {"recorded": inserted, "received": len(event_rows)}


def _canonical_event_metadata(value: Dict[str, Any]) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


@router.put("/homepage-fomo/preferences")
async def update_homepage_fomo_preferences(
    payload: FomoPreferenceRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        await _run_fomo_aux_db(
            fomo_repository.set_homepage_disabled,
            current_user.userid,
            payload.homepage_disabled,
        )
    except PoolError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not update chart-theme preferences.",
        ) from exc
    return {"homepage_disabled": payload.homepage_disabled}
