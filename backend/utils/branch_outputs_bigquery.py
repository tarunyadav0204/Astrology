"""
Write parallel specialist branch outputs to a dedicated BigQuery table.

This keeps large debug payloads out of core OLTP chat tables.
No-op when BigQuery env is not configured.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_bq_client = None


def _get_project() -> str:
    return (os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID") or "").strip()


def _get_dataset() -> str:
    return (os.getenv("BIGQUERY_BRANCH_OUTPUTS_DATASET_ID") or os.getenv("BIGQUERY_DATASET_ID") or "activity").strip()


def _get_table() -> str:
    return (os.getenv("BIGQUERY_BRANCH_OUTPUTS_TABLE_ID") or "chat_branch_outputs").strip()


def _table_ref() -> Optional[str]:
    project = _get_project()
    dataset = _get_dataset()
    table = _get_table()
    if not project or not dataset or not table:
        return None
    return f"{project}.{dataset}.{table}"


def _get_client():
    global _bq_client
    if _bq_client is not None:
        return _bq_client
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        from utils.env_json import parse_json_from_env

        project = _get_project()
        if not project:
            return None
        key = (
            os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
            or os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON")
            or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
            or ""
        )
        creds = None
        if key and str(key).strip():
            raw = str(key).strip()
            info = parse_json_from_env(raw)
            if info and isinstance(info, dict):
                creds = service_account.Credentials.from_service_account_info(info)
            elif os.path.isfile(raw):
                creds = service_account.Credentials.from_service_account_file(raw)
        _bq_client = bigquery.Client(project=project, credentials=creds) if creds else bigquery.Client(project=project)
        return _bq_client
    except Exception as e:
        logger.warning("branch_outputs_bigquery: client init failed: %s", e)
        return None


def write_branch_outputs_row(
    *,
    message_id: int,
    session_id: str,
    user_id: int,
    specialist_branch_outputs: Dict[str, Any],
    question: str = "",
    language: str = "english",
    chat_llm_model: str = "",
) -> bool:
    table = _table_ref()
    if not table:
        return False
    client = _get_client()
    if not client:
        return False
    try:
        row = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "message_id": int(message_id),
            "session_id": str(session_id),
            "user_id": int(user_id),
            "language": str(language or ""),
            "chat_llm_model": str(chat_llm_model or ""),
            "question_preview": str(question or "")[:1000],
            "specialist_branch_outputs": json.dumps(specialist_branch_outputs, ensure_ascii=False),
        }
        errors = client.insert_rows_json(table, [row])
        if errors:
            logger.warning("branch_outputs_bigquery: insert failed: %s", errors)
            return False
        return True
    except Exception as e:
        logger.warning("branch_outputs_bigquery: write failed: %s", e)
        return False

