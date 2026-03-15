"""
NotebookLM-style podcast generation via Google Discovery Engine Podcast API.

Uses the standalone Podcast API: send full message text as context, get back an MP3.
No separate Gemini script step. Requires Discovery Engine API enabled and
Podcast API User role (roles/discoveryengine.podcastApiUser).

Env (typically from .env):
- GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID or credentials.project_id for project ID.
- Same credentials as TTS: GOOGLE_TTS_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY.
"""

import os
import time
import logging
from typing import Optional

import requests
from utils.env_json import parse_json_from_env

logger = logging.getLogger(__name__)

TTS_CREDENTIALS_ENV = "GOOGLE_TTS_SERVICE_ACCOUNT_JSON"
TTS_CREDENTIALS_ENV_ALT = "GOOGLE_SERVICE_ACCOUNT_KEY"
DISCOVERY_BASE = "https://discoveryengine.googleapis.com/v1"
POLL_INTERVAL_SEC = 10
POLL_MAX_WAIT_SEC = 600  # 10 minutes


def _get_credentials():
    """Google Cloud credentials for Discovery Engine (same sources as TTS)."""
    raw = os.environ.get(TTS_CREDENTIALS_ENV) or os.environ.get(TTS_CREDENTIALS_ENV_ALT)
    if not raw or not str(raw).strip():
        return None
    raw = str(raw).strip()
    from google.oauth2 import service_account

    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    info = parse_json_from_env(raw)
    if info and isinstance(info, dict):
        try:
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)
        except (ValueError, TypeError):
            return None
    if os.path.isfile(raw):
        try:
            return service_account.Credentials.from_service_account_file(raw, scopes=scopes)
        except Exception:
            return None
    return None


def _get_access_token(credentials) -> Optional[str]:
    from google.auth.transport.requests import Request

    if not credentials or not credentials.valid:
        if credentials and hasattr(credentials, "refresh"):
            credentials.refresh(Request())
    return credentials.token if credentials else None


def _language_code(lang: str) -> str:
    """Map app language to Discovery Engine languageCode (e.g. en, hi)."""
    if not lang or not str(lang).strip():
        return "en"
    l = str(lang).lower().strip()
    return "hi" if l.startswith("hi") else "en"


def generate_podcast_mp3(
    message_content: str,
    lang: str = "en",
    title: Optional[str] = None,
    description: Optional[str] = None,
    length: str = "STANDARD",
) -> bytes:
    """
    Generate a podcast MP3 from full message text using Discovery Engine Podcast API.

    Args:
        message_content: Full response/message text (no separate script step).
        lang: Language code (en/hi).
        title: Optional podcast title.
        description: Optional description.
        length: "STANDARD" (~10 min) or "SHORT" (~4–5 min).

    Returns:
        MP3 audio bytes.

    Raises:
        RuntimeError: If credentials, project, or API calls fail.
    """
    text = (message_content or "").strip()
    if not text:
        raise ValueError("message_content is required")

    creds = _get_credentials()
    if not creds:
        raise RuntimeError(
            "NotebookLM podcast: Google credentials not set "
            "(GOOGLE_TTS_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY)"
        )

    project_id = (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT_ID")
        or (getattr(creds, "project_id", None) or "")
    )
    project_id = project_id.strip() if project_id else ""
    if not project_id:
        raise RuntimeError(
            "NotebookLM podcast: set GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID in .env (or use credentials with project_id)"
        )

    token = _get_access_token(creds)
    if not token:
        raise RuntimeError("NotebookLM podcast: Failed to obtain access token")

    language_code = _language_code(lang)
    url = f"{DISCOVERY_BASE}/projects/{project_id}/locations/global/podcasts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "podcastConfig": {
            "length": length,
            "languageCode": language_code,
        },
        "contexts": [{"text": text}],
        "title": (title or "AstroRoshni Podcast")[:200],
        "description": (description or "Generated from your astrological reading.")[:500],
    }

    logger.info("NotebookLM podcast: creating operation (length=%s, lang=%s)", length, language_code)
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    if resp.status_code == 404:
        try:
            err_body = resp.text or str(resp.json())
        except Exception:
            err_body = resp.text or ""
        # "Method not found" = Podcast create is not exposed for this project (limited-availability API).
        is_method_not_found = "Method not found" in err_body or "method" in err_body.lower()
        logger.error(
            "NotebookLM podcast: 404. URL=%s response=%s",
            url,
            err_body,
        )
        if is_method_not_found:
            raise RuntimeError(
                "NotebookLM podcast: 'Method not found' (404). The Podcast API is in limited availability: "
                "the create method is not exposed for all projects. IAM and Discovery Engine API are correct; "
                "you may need to contact Google Cloud sales to get your project (%s) allowlisted for the Podcast API."
                % (project_id,)
            )
        raise RuntimeError(
            "NotebookLM podcast: 404. Enable Discovery Engine API and grant roles/discoveryengine.podcastApiUser "
            "for project %s." % (project_id,)
        )
    resp.raise_for_status()
    data = resp.json()
    op_name = data.get("name")
    if not op_name:
        raise RuntimeError("NotebookLM podcast: create response missing operation name")

    # Poll until done
    op_url = f"{DISCOVERY_BASE}/{op_name}"
    started = time.monotonic()
    while True:
        if time.monotonic() - started > POLL_MAX_WAIT_SEC:
            raise RuntimeError("NotebookLM podcast: operation timed out")
        time.sleep(POLL_INTERVAL_SEC)
        token = _get_access_token(creds)
        r = requests.get(op_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        r.raise_for_status()
        op_data = r.json()
        done = op_data.get("done", False)
        if done:
            if "error" in op_data:
                err = op_data["error"]
                raise RuntimeError(
                    f"NotebookLM podcast operation failed: {err.get('message', op_data)}"
                )
            break

    # Download MP3
    download_url = f"{DISCOVERY_BASE}/{op_name}:download?alt=media"
    token = _get_access_token(creds)
    r = requests.get(download_url, headers={"Authorization": f"Bearer {token}"}, timeout=120, stream=True)
    r.raise_for_status()
    audio_bytes = r.content
    if not audio_bytes:
        raise RuntimeError("NotebookLM podcast: download returned empty body")
    logger.info("NotebookLM podcast: downloaded %d bytes", len(audio_bytes))
    return audio_bytes
