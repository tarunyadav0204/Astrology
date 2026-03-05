from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from auth import get_current_user
from reddit.reddit_service import RedditService
from reddit.collector import run_collector


router = APIRouter()
service = RedditService()


def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class RedditQuestionIn(BaseModel):
    reddit_id: str
    subreddit: str
    title: Optional[str] = None
    body: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    created_utc: Optional[float] = None
    has_birth_data: Optional[bool] = False
    extracted_birth_data: Optional[str] = None
    status: Optional[str] = "collected"
    notes: Optional[str] = None


class ApproveAnswerRequest(BaseModel):
    edited_markdown: str


@router.post("/api/admin/reddit/collect", dependencies=[Depends(require_admin)])
async def run_reddit_collect(
    days_back: int = 7,
    limit_per_sub: int = 100,
):
    """
    Run the Reddit collector: fetch recent posts from configured subreddits
    (last N days), detect birth details, store in DB.
    Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in env.
    """
    result = run_collector(days_back=days_back, limit_per_sub=min(limit_per_sub, 200))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Collector failed"))
    return result


@router.post("/api/admin/reddit/questions", dependencies=[Depends(require_admin)])
async def upsert_reddit_question(payload: RedditQuestionIn):
    """
    Upsert a Reddit question into the local DB.
    This endpoint is mainly for internal tools / cron jobs that
    collect questions via the Reddit API.
    """
    question_id = service.upsert_question(payload.model_dump())
    return {"question_id": question_id}


@router.get("/api/admin/reddit/questions", dependencies=[Depends(require_admin)])
async def list_reddit_questions(
    status: Optional[str] = None,
    has_birth_data: Optional[bool] = None,
    limit: int = 50,
):
    """List collected Reddit questions for debugging or tooling."""
    questions = service.list_questions(
        status=status,
        has_birth_data=has_birth_data,
        limit=min(max(limit, 1), 200),
    )
    return {"questions": questions}


@router.get("/api/admin/reddit/answers/drafts", dependencies=[Depends(require_admin)])
async def list_draft_answers(limit: int = 50):
    """
    List draft answers awaiting human review.
    Admin UI can call this to show question + draft side by side.
    """
    drafts = service.list_draft_answers(limit=min(max(limit, 1), 200))
    return {"drafts": drafts}


@router.post("/api/admin/reddit/answers/{answer_id}/approve")
async def approve_reddit_answer(
    answer_id: int,
    payload: ApproveAnswerRequest,
    current_user = Depends(require_admin),
):
    """
    Mark a draft answer as approved and ready to post.
    Actual Reddit posting should be performed by a separate worker
    that uses the stored markdown text.
    """
    if not payload.edited_markdown or not payload.edited_markdown.strip():
        raise HTTPException(status_code=400, detail="edited_markdown is required")

    service.update_answer_status(
        answer_id=answer_id,
        status="approved",
        reviewed_by=current_user.phone if hasattr(current_user, "phone") else "admin",
        draft_markdown=payload.edited_markdown.strip(),
    )
    return {"answer_id": answer_id, "status": "approved"}


@router.post("/api/admin/reddit/answers/{answer_id}/reject", dependencies=[Depends(require_admin)])
async def reject_reddit_answer(answer_id: int):
    """Mark a draft answer as rejected (will never be posted)."""
    service.update_answer_status(answer_id=answer_id, status="rejected")
    return {"answer_id": answer_id, "status": "rejected"}

