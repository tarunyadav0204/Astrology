"""Admin preview until the prediction approach is reviewed before customer rollout."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from auth import get_current_user
from .service import build_next_chapter, narrate_next_chapter

router = APIRouter(prefix='/next-chapter', tags=['next-chapter'])
logger = logging.getLogger(__name__)
_preview_slot = asyncio.Semaphore(1)


class NextChapterPreviewRequest(BaseModel):
    birth_chart_id: int = Field(gt=0)
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: Literal['en', 'hi'] = 'en'
    life_context: str = Field(default='', max_length=2000)
    narrate: bool = False

    @field_validator('as_of')
    @classmethod
    def aware_clock(cls, value):
        if value.tzinfo is None:
            raise ValueError('as_of must include a timezone')
        return value


@router.post('/preview')
async def preview_next_chapter(payload: NextChapterPreviewRequest, current_user=Depends(get_current_user)):
    if getattr(current_user, 'role', None) != 'admin':
        raise HTTPException(status_code=403, detail='Admin preview only')
    try:
        await asyncio.wait_for(_preview_slot.acquire(), timeout=0.1)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=429, detail='A Next Chapter preview is already running') from exc
    try:
        from prediction_engine.routes import _load_owned_birth_chart, _normalise_birth_data
        birth = await run_in_threadpool(_load_owned_birth_chart, payload.birth_chart_id, current_user.userid)
        birth = _normalise_birth_data(birth)
        dossier = await run_in_threadpool(build_next_chapter, birth, payload.as_of, life_context=payload.life_context)
        narration = await narrate_next_chapter(dossier, payload.language) if payload.narrate else None
        return {'dossier': dossier, 'narration': narration, 'preview_only': True}
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Next Chapter preview failed for chart=%s', payload.birth_chart_id)
        raise HTTPException(status_code=503, detail='Next Chapter could not be completed. Please try again.') from exc
    finally:
        _preview_slot.release()
