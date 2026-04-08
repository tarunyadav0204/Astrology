"""
Persist each user's latest AstroVastu run (Postgres) so they can reload without recomputing.

One row per userid (UPSERT on each successful analyze). See GET /latest + POST /analyze.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db import execute, get_conn

from .mapping_engine import MAPPING_VERSION, normalize_door_facing

logger = logging.getLogger(__name__)

_TABLE = "user_astrovastu_latest"


def _canonical_birth(birth: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("name", "date", "time", "latitude", "longitude", "timezone", "place", "gender")
    out: Dict[str, Any] = {}
    for k in keys:
        v = birth.get(k)
        if k in ("latitude", "longitude") and v is not None:
            try:
                out[k] = round(float(v), 6)
            except (TypeError, ValueError):
                out[k] = v
        else:
            out[k] = v
    return out


def compute_input_hash(
    birth_data: Dict[str, Any],
    goal: str,
    door_facing: str,
    zone_tags: Optional[Dict[str, Any]],
    mapping_version: str,
) -> str:
    body = {
        "birth": _canonical_birth(birth_data),
        "goal": (goal or "").strip().lower().replace(" ", "_"),
        "door": normalize_door_facing(door_facing or "E"),
        "tags": zone_tags or {},
        "mapping": mapping_version or MAPPING_VERSION,
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def ensure_table() -> None:
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_astrovastu_latest (
                userid INTEGER PRIMARY KEY,
                input_hash TEXT NOT NULL,
                mapping_version TEXT NOT NULL,
                request_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        )
        conn.commit()


def save_latest_run(
    userid: int,
    birth_data: Dict[str, Any],
    goal: str,
    door_facing: str,
    zone_tags: Optional[Dict[str, Any]],
    mapping_version: str,
    result: Dict[str, Any],
) -> None:
    ensure_table()
    ih = compute_input_hash(birth_data, goal, door_facing, zone_tags, mapping_version)
    request_obj = {
        "birth_data": _canonical_birth(birth_data),
        "goal": goal,
        "door_facing": normalize_door_facing(door_facing or "E"),
        "zone_tags": zone_tags,
    }
    req_json = json.dumps(request_obj, default=str)
    res_json = json.dumps(result, default=str)
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO user_astrovastu_latest (userid, input_hash, mapping_version, request_json, result_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (userid) DO UPDATE SET
                input_hash = EXCLUDED.input_hash,
                mapping_version = EXCLUDED.mapping_version,
                request_json = EXCLUDED.request_json,
                result_json = EXCLUDED.result_json,
                updated_at = EXCLUDED.updated_at
            """,
            (userid, ih, mapping_version, req_json, res_json, now),
        )
        conn.commit()


def get_latest_run(userid: int) -> Optional[Dict[str, Any]]:
    ensure_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT input_hash, mapping_version, request_json, result_json, updated_at
            FROM user_astrovastu_latest
            WHERE userid = ?
            """,
            (userid,),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        request = json.loads(row[2])
        result = json.loads(row[3])
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Corrupt astrovastu JSON for userid=%s: %s", userid, e)
        return None
    return {
        "input_hash": row[0],
        "mapping_version": row[1],
        "request": request,
        "result": result,
        "updated_at": row[4],
    }
