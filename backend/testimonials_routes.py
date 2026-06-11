import logging
import os
import json
from collections import Counter
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
    page_token: Optional[str] = None
    start_index: Optional[int] = Field(default=None, ge=0)
    pages: int = Field(default=1, ge=1, le=100)
    package_name: Optional[str] = None
    source_mode: str = Field(default="public", pattern="^(public|publisher)$")
    country: Optional[str] = None
    language: Optional[str] = None


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


def _json_default(value: Any) -> str:
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


def _fetch_google_play_reviews(
    package_name: str,
    max_results: int,
    page_token: Optional[str] = None,
    start_index: Optional[int] = None,
    pages: int = 1,
) -> dict[str, Any]:
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
    all_reviews: list[dict[str, Any]] = []
    next_page_token = (page_token or "").strip() or None
    next_start_index = start_index if start_index is not None else None
    total_results: Optional[int] = None
    pages_fetched = 0

    for _ in range(max(1, pages)):
        params: dict[str, Any] = {"maxResults": max_results}
        if next_page_token:
            params["token"] = next_page_token
        elif next_start_index is not None:
            params["startIndex"] = next_start_index

        response = session.get(url, params=params, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.error("Google Play testimonials sync failed: %s %s", response.status_code, response.text[:500])
            raise HTTPException(status_code=502, detail="Google Play reviews fetch failed") from exc

        data = response.json() or {}
        reviews = data.get("reviews") or []
        all_reviews.extend(reviews)
        pages_fetched += 1
        logger.info(
            "Google Play testimonials publisher page package=%s page=%s start_index=%s returned=%s",
            package_name,
            pages_fetched,
            params.get("startIndex"),
            len(reviews),
        )

        page_info = data.get("pageInfo") or {}
        try:
            total_results = int(page_info.get("totalResults")) if page_info.get("totalResults") is not None else total_results
        except (TypeError, ValueError):
            pass

        next_page_token = ((data.get("tokenPagination") or {}).get("nextPageToken") or "").strip() or None
        if next_page_token:
            next_start_index = None
            continue

        try:
            current_start = int(page_info.get("startIndex") or (next_start_index or 0))
        except (TypeError, ValueError):
            current_start = next_start_index or 0

        # Google may report resultPerPage as the requested page size even when fewer reviews are returned.
        # Advance by actual rows returned so we do not skip sparse pages of text reviews.
        candidate_next_start = current_start + len(reviews)
        if reviews and (total_results is None or candidate_next_start < total_results):
            next_start_index = candidate_next_start
            continue

        next_start_index = None
        if not next_page_token:
            break

    return {
        "reviews": all_reviews,
        "source_mode": "publisher",
        "next_page_token": next_page_token,
        "next_start_index": next_start_index,
        "total_results": total_results,
        "pages_fetched": pages_fetched,
    }


def _review_datetime_to_timestamp(value: Any) -> Optional[dict[str, int]]:
    if not isinstance(value, datetime):
        return None
    dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return {"seconds": int(dt.timestamp()), "nanos": dt.microsecond * 1000}


def _public_review_to_play_shape(review: dict[str, Any]) -> Optional[dict[str, Any]]:
    content = (review.get("content") or "").strip()
    if not content:
        return None
    review_id = (review.get("reviewId") or "").strip()
    if not review_id:
        fallback = f"{review.get('userName') or ''}|{review.get('at') or ''}|{content}"
        review_id = f"public:{__import__('hashlib').sha256(fallback.encode('utf-8')).hexdigest()}"
    return {
        "reviewId": review_id,
        "authorName": (review.get("userName") or "").strip() or None,
        "comments": [
            {
                "userComment": {
                    "text": content,
                    "lastModified": _review_datetime_to_timestamp(review.get("at")),
                    "starRating": review.get("score") or 0,
                    "reviewerLanguage": review.get("reviewerLanguage"),
                    "appVersionName": review.get("appVersion"),
                    "thumbsUpCount": review.get("thumbsUpCount"),
                }
            }
        ],
        "publicPlayReview": review,
    }


def _review_import_summary(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    ratings: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    with_user_comment = 0
    with_text = 0
    with_original_text = 0
    missing_text = 0

    for review in reviews:
        user_comment = _extract_user_comment(review)
        if not user_comment:
            continue
        with_user_comment += 1
        rating = user_comment.get("starRating")
        ratings[str(rating or "missing")] += 1
        language = user_comment.get("reviewerLanguage")
        if language:
            languages[str(language)] += 1
        text = (user_comment.get("text") or "").strip()
        original_text = (user_comment.get("originalText") or "").strip()
        if text:
            with_text += 1
        if original_text:
            with_original_text += 1
        if not text and not original_text:
            missing_text += 1

    return {
        "raw_reviews": len(reviews),
        "with_user_comment": with_user_comment,
        "with_text": with_text,
        "with_original_text": with_original_text,
        "missing_text": missing_text,
        "ratings": dict(sorted(ratings.items())),
        "languages": dict(languages.most_common(8)),
    }


def _fetch_public_google_play_reviews(
    package_name: str,
    max_results: int,
    start_index: Optional[int] = None,
    pages: int = 1,
    country: Optional[str] = None,
    language: Optional[str] = None,
) -> dict[str, Any]:
    try:
        from google_play_scraper import Sort, reviews
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Public Google Play review fetch is not installed. Install backend requirements and restart.",
        ) from exc

    all_reviews: list[dict[str, Any]] = []
    continuation_token = None
    pages_fetched = 0
    raw_seen = 0
    returned_pages = 0
    skip_until = start_index or 0
    lang = (language or os.getenv("GOOGLE_PLAY_REVIEWS_LANGUAGE") or "en").strip().lower()
    country_code = (country or os.getenv("GOOGLE_PLAY_REVIEWS_COUNTRY") or "in").strip().lower()

    for _ in range(max(1, pages) + (skip_until // max(1, max_results)) + 1):
        page_reviews, continuation_token = reviews(
            package_name,
            lang=lang,
            country=country_code,
            sort=Sort.NEWEST,
            count=max_results,
            continuation_token=continuation_token,
        )
        pages_fetched += 1
        page_reviews = page_reviews or []
        page_contributed = False
        page_shaped = 0
        for item in page_reviews:
            raw_seen += 1
            if raw_seen <= skip_until:
                continue
            shaped = _public_review_to_play_shape(item)
            if shaped:
                all_reviews.append(shaped)
                page_contributed = True
                page_shaped += 1
        logger.info(
            "Google Play testimonials public page package=%s country=%s lang=%s page=%s raw_returned=%s shaped_text_reviews=%s raw_seen=%s skip_until=%s has_more=%s",
            package_name,
            country_code,
            lang,
            pages_fetched,
            len(page_reviews),
            page_shaped,
            raw_seen,
            skip_until,
            bool(continuation_token),
        )
        if page_contributed:
            returned_pages += 1
            if returned_pages >= max(1, pages):
                break
        if not page_reviews or not continuation_token:
            continuation_token = None
            break

    next_start_index = raw_seen if continuation_token and raw_seen > skip_until else None
    return {
        "reviews": all_reviews,
        "source_mode": "public",
        "next_page_token": None,
        "next_start_index": next_start_index,
        "total_results": None,
        "pages_fetched": pages_fetched,
        "country": country_code,
        "language": lang,
    }


def _extract_user_comment(review: dict[str, Any]) -> Optional[dict[str, Any]]:
    for comment in reversed(review.get("comments") or []):
        user_comment = comment.get("userComment")
        if user_comment:
            return user_comment
    return None


def _upsert_reviews(reviews: list[dict[str, Any]], min_rating: int) -> dict[str, Any]:
    ensure_testimonials_table()
    inserted = updated = skipped = 0
    skip_reasons = {
        "no_user_comment": 0,
        "missing_review_id": 0,
        "missing_text": 0,
        "below_min_rating": 0,
    }
    with get_conn() as conn:
        for review in reviews:
            user_comment = _extract_user_comment(review)
            if not user_comment:
                skipped += 1
                skip_reasons["no_user_comment"] += 1
                continue
            text = (user_comment.get("text") or user_comment.get("originalText") or "").strip()
            rating = int(user_comment.get("starRating") or 0)
            review_id = (review.get("reviewId") or "").strip()
            if not review_id:
                skipped += 1
                skip_reasons["missing_review_id"] += 1
                continue
            if not text:
                skipped += 1
                skip_reasons["missing_text"] += 1
                continue
            if rating < min_rating:
                skipped += 1
                skip_reasons["below_min_rating"] += 1
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
                    json.dumps(review, default=_json_default),
                ),
            )
            if cur.fetchone()[0]:
                inserted += 1
            else:
                updated += 1
        conn.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "skip_reasons": skip_reasons}


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
    logger.info(
        "Google Play testimonials sync start package=%s source=%s min_rating=%s max_results=%s pages=%s start_index=%s has_page_token=%s country=%s language=%s admin_user=%s",
        package_name,
        body.source_mode,
        body.min_rating,
        body.max_results,
        body.pages,
        body.start_index,
        bool(body.page_token),
        body.country,
        body.language,
        current_user.userid,
    )
    if body.source_mode == "publisher":
        fetched = _fetch_google_play_reviews(
            package_name,
            body.max_results,
            page_token=body.page_token,
            start_index=body.start_index,
            pages=body.pages,
        )
    else:
        fetched = _fetch_public_google_play_reviews(
            package_name,
            body.max_results,
            start_index=body.start_index,
            pages=body.pages,
            country=body.country,
            language=body.language,
        )
    reviews = fetched["reviews"]
    diagnostics = _review_import_summary(reviews)
    logger.info(
        "Google Play testimonials sync fetched package=%s source=%s fetched=%s pages_fetched=%s next_start_index=%s total_results=%s diagnostics=%s",
        package_name,
        fetched["source_mode"],
        len(reviews),
        fetched["pages_fetched"],
        fetched["next_start_index"],
        fetched["total_results"],
        diagnostics,
    )
    result = _upsert_reviews(reviews, body.min_rating)
    logger.info(
        "Google Play testimonials sync saved package=%s source=%s inserted=%s updated=%s skipped=%s skip_reasons=%s",
        package_name,
        fetched["source_mode"],
        result["inserted"],
        result["updated"],
        result["skipped"],
        result["skip_reasons"],
    )
    return {
        "ok": True,
        "fetched": len(reviews),
        "package_name": package_name,
        "source_mode": fetched["source_mode"],
        "next_page_token": fetched["next_page_token"],
        "next_start_index": fetched["next_start_index"],
        "total_results": fetched["total_results"],
        "pages_fetched": fetched["pages_fetched"],
        "country": fetched.get("country"),
        "language": fetched.get("language"),
        "diagnostics": diagnostics,
        **result,
    }


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
