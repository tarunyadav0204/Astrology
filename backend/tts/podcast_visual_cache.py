"""Persistent JSON cache for visual-podcast sources and generated manifests."""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from typing import Any, Optional

from tts.podcast_cache import PODCAST_CACHE_BUCKET_ENV


logger = logging.getLogger(__name__)
# Only rendered manifests are versioned. The source contains the dialogue and
# per-speaker audio timing for the unchanged MP3, so it must survive visual
# renderer/cache upgrades.
PODCAST_VISUAL_VERSION = "v20"
_LEGACY_SOURCE_VERSIONS = ("v5", "v4", "v3")
_MEMORY: dict[tuple[str, str, str], dict[str, Any]] = {}
_MEMORY_MAX = 500


def _safe(value: str, limit: int = 200) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", str(value or "").strip())
    return (cleaned or "unknown")[:limit]


def _key(message_id: str, lang: str, kind: str) -> tuple[str, str, str]:
    return (str(message_id).strip(), (lang or "en").strip()[:10], kind)


def _object_name(message_id: str, lang: str, kind: str) -> str:
    if kind == "source":
        return f"podcast-visual/{_safe(message_id)}_{_safe(lang, 10)}_source.json"
    return f"podcast-visual/{_safe(message_id)}_{_safe(lang, 10)}_{PODCAST_VISUAL_VERSION}_{kind}.json"


def _legacy_source_object_names(message_id: str, lang: str) -> list[str]:
    return [
        f"podcast-visual/{_safe(message_id)}_{_safe(lang, 10)}_{version}_source.json"
        for version in _LEGACY_SOURCE_VERSIONS
    ]


def _disk_path(message_id: str, lang: str, kind: str) -> str:
    root = (os.getenv("PODCAST_CACHE_DIR") or "").strip()
    if root:
        root = os.path.join(root, "visual")
    else:
        root = os.path.join(tempfile.gettempdir(), "astroroshni_podcast_visual_cache")
    return os.path.join(root, os.path.basename(_object_name(message_id, lang, kind)))


def _gcs_client():
    from google.cloud import storage
    from google.oauth2 import service_account
    from utils.env_json import parse_json_from_env

    raw = (os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or "").strip()
    if raw:
        info = parse_json_from_env(raw)
        if info:
            return storage.Client(credentials=service_account.Credentials.from_service_account_info(info))
        if os.path.isfile(raw):
            return storage.Client(credentials=service_account.Credentials.from_service_account_file(raw))
    return storage.Client()


def _remember(message_id: str, lang: str, kind: str, payload: dict[str, Any]) -> None:
    key = _key(message_id, lang, kind)
    if len(_MEMORY) < _MEMORY_MAX or key in _MEMORY:
        _MEMORY[key] = payload


def get_visual_json(message_id: str, lang: str, kind: str) -> Optional[dict[str, Any]]:
    key = _key(message_id, lang, kind)
    if key in _MEMORY:
        return _MEMORY[key]

    path = _disk_path(message_id, lang, kind)
    disk_paths = [path]
    if kind == "source":
        disk_paths.extend(
            os.path.join(os.path.dirname(path), os.path.basename(name))
            for name in _legacy_source_object_names(message_id, lang)
        )
    for candidate_path in disk_paths:
        try:
            if os.path.isfile(candidate_path):
                with open(candidate_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    _remember(message_id, lang, kind, payload)
                    return payload
        except Exception as exc:
            logger.warning("Visual podcast disk cache read failed (%s): %s", candidate_path, exc)

    bucket_name = (os.getenv(PODCAST_CACHE_BUCKET_ENV) or "").strip()
    if not bucket_name:
        return None
    object_names = [_object_name(message_id, lang, kind)]
    if kind == "source":
        object_names.extend(_legacy_source_object_names(message_id, lang))
    try:
        bucket = _gcs_client().bucket(bucket_name)
        for object_name in object_names:
            blob = bucket.blob(object_name)
            if not blob.exists():
                continue
            payload = json.loads(blob.download_as_text(encoding="utf-8"))
            if isinstance(payload, dict):
                _remember(message_id, lang, kind, payload)
                return payload
    except Exception as exc:
        logger.warning("Visual podcast GCS cache read failed (%s): %s", object_names, exc)
    return None


def put_visual_json(message_id: str, lang: str, kind: str, payload: dict[str, Any]) -> None:
    if not message_id or not isinstance(payload, dict):
        return
    _remember(message_id, lang, kind, payload)
    path = _disk_path(message_id, lang, kind)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
    except Exception as exc:
        logger.warning("Visual podcast disk cache write failed (%s): %s", path, exc)

    bucket_name = (os.getenv(PODCAST_CACHE_BUCKET_ENV) or "").strip()
    if not bucket_name:
        return
    object_name = _object_name(message_id, lang, kind)
    try:
        blob = _gcs_client().bucket(bucket_name).blob(object_name)
        blob.upload_from_string(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            content_type="application/json; charset=utf-8",
        )
    except Exception as exc:
        # Visual metadata must never make podcast audio generation fail.
        logger.warning("Visual podcast GCS cache write failed (%s): %s", object_name, exc)
