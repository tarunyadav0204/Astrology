"""
Authenticated mobile-journey ingest endpoints.
Writes to the same Pub/Sub -> BigQuery activity pipeline as API logs.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth import User, get_current_user
from activity.publisher import publish_activity

router = APIRouter(prefix="/activity", tags=["activity"])


class MobileJourneyEvent(BaseModel):
    action: str = Field(..., min_length=1, max_length=120)
    screen_name: Optional[str] = Field(None, max_length=120)
    duration_ms: Optional[float] = Field(None, ge=0, le=86_400_000)
    resource_type: Optional[str] = Field(None, max_length=80)
    resource_id: Optional[str] = Field(None, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MobileJourneyBatchRequest(BaseModel):
    events: List[MobileJourneyEvent] = Field(default_factory=list, max_length=100)


def _normalize_action(action: str) -> str:
    raw = (action or "").strip().lower().replace(" ", "_")
    if not raw:
        return "mobile_event"
    return raw if raw.startswith("mobile_") else f"mobile_{raw}"


@router.post("/mobile-events")
async def ingest_mobile_events(
    body: MobileJourneyBatchRequest,
    current_user: User = Depends(get_current_user),
):
    accepted = 0
    for ev in body.events or []:
        try:
            action = _normalize_action(ev.action)
            metadata = dict(ev.metadata or {})
            if ev.screen_name:
                metadata.setdefault("screen_name", ev.screen_name)
            publish_activity(
                action,
                user_id=current_user.userid,
                user_phone=current_user.phone,
                user_name=current_user.name,
                duration_ms=ev.duration_ms,
                resource_type=ev.resource_type or "mobile",
                resource_id=ev.resource_id,
                metadata=metadata,
                user_agent="AstroRoshni-Mobile",
            )
            accepted += 1
        except Exception:
            # Never fail the endpoint due to one bad event.
            continue
    return {"ok": True, "accepted": accepted}

