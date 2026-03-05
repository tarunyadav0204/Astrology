"""
Reddit question collector for AstroRoshni outreach.

Fetches recent posts from configured subreddits (last 7 days), detects
birth-detail patterns, and upserts into reddit_questions.

Required env (in .env or environment):
  REDDIT_CLIENT_ID     - from https://www.reddit.com/prefs/apps (script app)
  REDDIT_CLIENT_SECRET
  REDDIT_USER_AGENT    - e.g. "AstroRoshniCollector/1.0 by YourRedditUsername"

Optional:
  REDDIT_SUBREDDITS    - comma-separated, default: astrology,AskAstrologers,vedicastrology
"""
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from reddit.reddit_service import RedditService


# Heuristic: likely birth-detail phrases and date/time/place patterns
BIRTH_PATTERNS = [
    re.compile(r"\b(?:dob|date\s+of\s+birth|birth\s+date)\s*[:\-]?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", re.I),
    re.compile(r"\b(?:birth\s+time|time\s+of\s+birth|tob|born\s+at)\s*[:\-]?\s*\d{1,2}[:\-]\d{2}", re.I),
    re.compile(r"\b(?:place\s+of\s+birth|birth\s+place|born\s+in)\s*[:\-]?\s*[A-Za-z\s,]+", re.I),
    re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\s+(?:at\s+)?\d{1,2}[:\-]\d{2}", re.I),
    re.compile(r"\b(?:kundli|kundali|chart|rasi)\s+(?:for|of|details|data)\b", re.I),
]


def _has_birth_data(text: str) -> bool:
    if not text or not text.strip():
        return False
    combined = (text or "")[: 10000]
    for pat in BIRTH_PATTERNS:
        if pat.search(combined):
            return True
    return False


def _extract_birth_data_json(text: str) -> Optional[str]:
    """Optional: store a minimal JSON snippet for analyzer to use. Placeholder for now."""
    return None


def run_collector(
    subreddits: Optional[List[str]] = None,
    days_back: int = 7,
    limit_per_sub: int = 100,
    db_path: str = "astrology.db",
) -> Dict[str, Any]:
    """
    Fetch recent posts from Reddit, detect birth data, upsert into DB.
    Returns counts: collected, with_birth_data, errors.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "AstroRoshniCollector/1.0")

    if not client_id or not client_secret:
        return {
            "ok": False,
            "error": "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set",
            "collected": 0,
            "with_birth_data": 0,
        }

    if not subreddits:
        raw = os.getenv("REDDIT_SUBREDDITS", "astrology,AskAstrologers,vedicastrology")
        subreddits = [s.strip() for s in raw.split(",") if s.strip()]

    service = RedditService(db_path=db_path)
    cutoff_utc = (datetime.utcnow() - timedelta(days=days_back)).timestamp()
    collected = 0
    with_birth_data = 0
    errors: List[str] = []

    try:
        import praw
    except ImportError:
        return {
            "ok": False,
            "error": "praw not installed. pip install praw",
            "collected": 0,
            "with_birth_data": 0,
        }

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    for sub_name in subreddits:
        try:
            sub = reddit.subreddit(sub_name)
            for post in sub.new(limit=limit_per_sub):
                try:
                    if post.created_utc < cutoff_utc:
                        continue
                    title = getattr(post, "title", "") or ""
                    body = getattr(post, "selftext", "") or ""
                    text = f"{title}\n{body}"
                    has_birth = _has_birth_data(text)
                    url = f"https://www.reddit.com{post.permalink}" if getattr(post, "permalink", None) else None
                    service.upsert_question({
                        "reddit_id": post.id,
                        "subreddit": sub_name,
                        "title": title[: 2000] if title else None,
                        "body": body[: 50000] if body else None,
                        "url": url,
                        "author": getattr(post.author, "name", None) if post.author else None,
                        "created_utc": post.created_utc,
                        "has_birth_data": has_birth,
                        "extracted_birth_data": _extract_birth_data_json(text),
                    })
                    collected += 1
                    if has_birth:
                        with_birth_data += 1
                except Exception as e:
                    errors.append(f"{sub_name}/{getattr(post, 'id', '?')}: {e}")
                time.sleep(0.5)
        except Exception as e:
            errors.append(f"subreddit {sub_name}: {e}")
        time.sleep(1)

    return {
        "ok": True,
        "collected": collected,
        "with_birth_data": with_birth_data,
        "subreddits": subreddits,
        "errors": errors[: 20],
    }
