import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

from auth import User, get_current_user
from db import execute, get_conn

router = APIRouter(prefix="/user-settings", tags=["User Settings"])


class UserSettings(BaseModel):
    node_type: str = "mean"  # "mean" or "true"
    default_chart_style: str = "north"  # "north" or "south"


class ChatAnswerStylePreference(BaseModel):
    answer_style: Literal["simple", "technical"]


def _upsert_setting(conn, user_id: int, key: str, value_json: str) -> None:
    """Update if row exists, else insert (Postgres; no UNIQUE on (user_id, setting_key) required)."""
    cur = execute(
        conn,
        """
        UPDATE user_settings
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND setting_key = ?
        """,
        (value_json, user_id, key),
    )
    if cur.rowcount == 0:
        execute(
            conn,
            """
            INSERT INTO user_settings (user_id, setting_key, setting_value)
            VALUES (?, ?, ?)
            """,
            (user_id, key, value_json),
        )


def _read_setting(conn, user_id: int, key: str) -> Optional[object]:
    cur = execute(
        conn,
        "SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = ?",
        (user_id, key),
    )
    row = cur.fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return row[0]


@router.get("/chat-answer-style")
async def get_chat_answer_style(current_user: User = Depends(get_current_user)):
    """Return the account-wide chat answer style, or request first-time selection."""
    try:
        with get_conn() as conn:
            stored = _read_setting(conn, current_user.userid, "chat_answer_style")
        answer_style = str(stored or "").strip().lower()
        if answer_style not in {"simple", "technical"}:
            answer_style = None
        return {
            "answer_style": answer_style,
            "selection_required": answer_style is None,
            "default_answer_style": "simple",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/chat-answer-style")
async def update_chat_answer_style(
    preference: ChatAnswerStylePreference,
    current_user: User = Depends(get_current_user),
):
    """Persist one answer style for Standard, Premium and Live chat."""
    try:
        with get_conn() as conn:
            _upsert_setting(
                conn,
                current_user.userid,
                "chat_answer_style",
                json.dumps(preference.answer_style),
            )
            conn.commit()
        return {
            "answer_style": preference.answer_style,
            "selection_required": False,
            "default_answer_style": "simple",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/settings/{phone}")
async def get_user_settings(phone: str):
    """Get user settings"""
    try:
        with get_conn() as conn:
            cur = execute(conn, "SELECT userid FROM users WHERE phone = ?", (phone,))
            user_result = cur.fetchone()
            if not user_result:
                raise HTTPException(status_code=404, detail="User not found")

            user_id = user_result[0]

            cur = execute(
                conn,
                """
                SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?
                """,
                (user_id,),
            )
            settings_rows = cur.fetchall()

        settings = {}
        for key, value in settings_rows:
            try:
                settings[key] = json.loads(value)
            except Exception:
                settings[key] = value

        return {
            "node_type": settings.get("node_type", "mean"),
            "default_chart_style": settings.get("default_chart_style", "north"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{phone}")
async def update_user_settings(phone: str, settings: UserSettings):
    """Update user settings"""
    try:
        with get_conn() as conn:
            cur = execute(conn, "SELECT userid FROM users WHERE phone = ?", (phone,))
            user_result = cur.fetchone()
            if not user_result:
                raise HTTPException(status_code=404, detail="User not found")

            user_id = user_result[0]

            data = settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
            for key, value in data.items():
                _upsert_setting(conn, user_id, key, json.dumps(value))

            conn.commit()

        return {"message": "Settings updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
