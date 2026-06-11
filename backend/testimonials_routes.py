import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn
from utils.env_json import parse_json_from_env

logger = logging.getLogger(__name__)

router = APIRouter(tags=["testimonials"])

PLAY_CREDENTIAL_ENV_KEYS = ("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "GOOGLE_SERVICE_ACCOUNT_KEY")
ANDROID_PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
DEFAULT_PACKAGE_NAME = "com.astroroshni.mobile"


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def ensure_testimonials_table() -> None:
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS app_testimonials (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL DEFAULT 'google_play',
                external_review_id TEXT NOT NULL UNIQUE,
                author_name TEXT,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                review_text TEXT NOT NULL,
                language TEXT,
                app_version_name TEXT,
                review_created_at TIMESTAMPTZ,
                review_updated_at TIMESTAMPTZ,
                status TEXT NOT NULL DEFAULT 'pending',
                display_name TEXT,
                display_location TEXT,
                display_order INTEGER NOT NULL DEFAULT 0,
                approved_at TIMESTAMPTZ,
                approved_by_userid INTEGER,
                fetched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                raw_review JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        execute(
            conn,
            """
            CREATE INDEX IF NOT EXISTS idx_app_testimonials_status_order
            ON app_testimonials (status, display_order, review_updated_at DESC)
            """,
        )
        conn.commit()


class SyncTestimonialsRequest(BaseModel):
    max_results: int = Field(default=50, ge=1, le=100)
    min_rating: int = Field(default=4, ge=1, le=5)
    package_name: Optional[str] = None


class UpdateTestimonialRequest(BaseModel):
    status: Optional[str] = None
    display_name: Optional[str] = None
    display_location: Optional[str] = None
    display_order: Optional[int] = None


def _dt_from_play_modified(value: Optional[dict[str, Any]]) -> Optional[datetime]:
    if not value:
        return None
    try:
        seconds = int(value.get("seconds") or 0)
        nanos = int(value.get("nanos") or 0)
        if seconds <= 0:
            return None
        return datetime.fromtimestamp(seconds + nanos / 1_000_000_000, tz=timezone.utc)
    except Exception:
        return None


def _serialize_dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _testimonial_from_row(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "source": row[1],
        "external_review_id": row[2],
        "author_name": row[3],
        "rating": row[4],
        "review_text": row[5],
        "language": row[6],
        "app_version_name": row[7],
        "review_created_at": _serialize_dt(row[8]),
        "review_updated_at": _serialize_dt(row[9]),
        "status": row[10],
        "display_name": row[11],
        "display_location": row[12],
        "display_order": row[13],
        "approved_at": _serialize_dt(row[14]),
        "fetched_at": _serialize_dt(row[15]),
        "created_at": _serialize_dt(row[16]),
        "updated_at": _serialize_dt(row[17]),
    }


def _public_testimonial_from_row(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "source": row[1],
        "name": row[2] or row[3] or "Google Play user",
        "location": row[4] or "Google Play review",
        "rating": row[5],
        "text": row[6],
        "review_updated_at": _serialize_dt(row[7]),
    }


def _get_play_credentials():
    from google.oauth2 import service_account

    _ensure_play_env_loaded()
    for key in PLAY_CREDENTIAL_ENV_KEYS:
        raw = (os.getenv(key) or "").strip()
        if not raw:
            continue
        info = parse_json_from_env(raw)
        if info:
            return service_account.Credentials.from_service_account_info(
                info,
                scopes=[ANDROID_PUBLISHER_SCOPE],
            )
        if os.path.isfile(raw):
            return service_account.Credentials.from_service_account_file(
                raw,
                scopes=[ANDROID_PUBLISHER_SCOPE],
            )
        logger.warning("Google Play testimonials: %s is not JSON or a file path", key)
    return None


def _ensure_play_env_loaded() -> None:
    if any((os.getenv(key) or "").strip() for key in PLAY_CREDENTIAL_ENV_KEYS):
        return
    try:
        from dotenv import load_dotenv

        backend_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(backend_dir, ".env")
        if os.path.isfile(env_path):
            load_dotenv(env_path, override=False)
    except Exception as exc:
        logger.warning("Google Play testimonials: could not load .env: %s", exc)


def _fetch_google_play_reviews(package_name: str, max_results: int) -> list[dict[str, Any]]:
    import requests
    from google.auth.transport.requests import AuthorizedSession

    credentials = _get_play_credentials()
    if not credentials:
        raise HTTPException(
            status_code=503,
            detail="Google Play service account JSON is not configured.",
        )

    session = AuthorizedSession(credentials)
    url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/reviews"
    response = session.get(url, params={"maxResults": max_results}, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.error("Google Play testimonials sync failed: %s %s", response.status_code, response.text[:500])
        raise HTTPException(status_code=502, detail="Google Play reviews fetch failed") from exc

    data = response.json() or {}
    return data.get("reviews") or []


def _extract_user_comment(review: dict[str, Any]) -> Optional[dict[str, Any]]:
    for comment in reversed(review.get("comments") or []):
        user_comment = comment.get("userComment")
        if user_comment:
            return user_comment
    return None


def _upsert_reviews(reviews: list[dict[str, Any]], min_rating: int) -> dict[str, int]:
    ensure_testimonials_table()
    inserted = updated = skipped = 0
    with get_conn() as conn:
        for review in reviews:
            user_comment = _extract_user_comment(review)
            if not user_comment:
                skipped += 1
                continue
            text = (user_comment.get("text") or "").strip()
            rating = int(user_comment.get("starRating") or 0)
            review_id = (review.get("reviewId") or "").strip()
            if not review_id or not text or rating < min_rating:
                skipped += 1
                continue

            author_name = (review.get("authorName") or "").strip() or None
            updated_at = _dt_from_play_modified(user_comment.get("lastModified"))
            created_at = updated_at
            language = user_comment.get("reviewerLanguage")
            app_version_name = user_comment.get("appVersionName")

            cur = execute(
                conn,
                """
                INSERT INTO app_testimonials (
                    source, external_review_id, author_name, rating, review_text, language,
                    app_version_name, review_created_at, review_updated_at, raw_review
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (external_review_id) DO UPDATE SET
                    author_name = EXCLUDED.author_name,
                    rating = EXCLUDED.rating,
                    review_text = EXCLUDED.review_text,
                    language = EXCLUDED.language,
                    app_version_name = EXCLUDED.app_version_name,
                    review_updated_at = EXCLUDED.review_updated_at,
                    fetched_at = CURRENT_TIMESTAMP,
                    raw_review = EXCLUDED.raw_review,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0) AS inserted
                """,
                (
                    "google_play",
                    review_id,
                    author_name,
                    rating,
                    text,
                    language,
                    app_version_name,
                    created_at,
                    updated_at,
                    __import__("json").dumps(review),
                ),
            )
            if cur.fetchone()[0]:
                inserted += 1
            else:
                updated += 1
        conn.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


@router.get("/testimonials")
async def public_testimonials(limit: int = Query(default=12, ge=1, le=30)):
    ensure_testimonials_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT id, source, display_name, author_name, display_location, rating, review_text, review_updated_at
            FROM app_testimonials
            WHERE status = 'approved'
            ORDER BY display_order ASC, approved_at DESC NULLS LAST, review_updated_at DESC NULLS LAST, id DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall() or []
    return {"testimonials": [_public_testimonial_from_row(row) for row in rows]}


@router.get("/admin/testimonials")
async def admin_list_testimonials(
    status: str = Query(default="all", pattern="^(all|pending|approved|hidden)$"),
    current_user: User = Depends(_require_admin),
):
    ensure_testimonials_table()
    params: tuple[Any, ...] = ()
    where = ""
    if status != "all":
        where = "WHERE status = %s"
        params = (status,)
    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT id, source, external_review_id, author_name, rating, review_text, language,
                   app_version_name, review_created_at, review_updated_at, status, display_name,
                   display_location, display_order, approved_at, fetched_at, created_at, updated_at
            FROM app_testimonials
            {where}
            ORDER BY
              CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
              display_order ASC,
              review_updated_at DESC NULLS LAST,
              id DESC
            LIMIT 250
            """,
            params,
        )
        rows = cur.fetchall() or []
    return {"testimonials": [_testimonial_from_row(row) for row in rows]}


@router.post("/admin/testimonials/sync")
async def admin_sync_testimonials(
    body: SyncTestimonialsRequest,
    current_user: User = Depends(_require_admin),
):
    package_name = (body.package_name or os.getenv("GOOGLE_PLAY_PACKAGE_NAME") or DEFAULT_PACKAGE_NAME).strip()
    reviews = _fetch_google_play_reviews(package_name, body.max_results)
    result = _upsert_reviews(reviews, body.min_rating)
    return {"ok": True, "fetched": len(reviews), "package_name": package_name, **result}


@router.patch("/admin/testimonials/{testimonial_id}")
async def admin_update_testimonial(
    testimonial_id: int,
    body: UpdateTestimonialRequest,
    current_user: User = Depends(_require_admin),
):
    ensure_testimonials_table()
    updates = []
    params: list[Any] = []
    if body.status is not None:
        if body.status not in ("pending", "approved", "hidden"):
            raise HTTPException(status_code=400, detail="Invalid status")
        updates.append("status = %s")
        params.append(body.status)
        if body.status == "approved":
            updates.append("approved_at = COALESCE(approved_at, CURRENT_TIMESTAMP)")
            updates.append("approved_by_userid = COALESCE(approved_by_userid, %s)")
            params.append(current_user.userid)
        elif body.status != "approved":
            updates.append("approved_at = NULL")
            updates.append("approved_by_userid = NULL")
    if body.display_name is not None:
        updates.append("display_name = %s")
        params.append(body.display_name.strip() or None)
    if body.display_location is not None:
        updates.append("display_location = %s")
        params.append(body.display_location.strip() or None)
    if body.display_order is not None:
        updates.append("display_order = %s")
        params.append(body.display_order)
    if not updates:
        raise HTTPException(status_code=400, detail="No changes provided")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(testimonial_id)
    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            UPDATE app_testimonials
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, source, external_review_id, author_name, rating, review_text, language,
                      app_version_name, review_created_at, review_updated_at, status, display_name,
                      display_location, display_order, approved_at, fetched_at, created_at, updated_at
            """,
            tuple(params),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Testimonial not found")
        conn.commit()
    return {"testimonial": _testimonial_from_row(row)}
