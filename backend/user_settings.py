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


CHAT_ANSWER_STYLE_SETTING_KEY = "chat_answer_style"


def parse_stored_chat_answer_style(value: object) -> Optional[str]:
    """Normalize a JSON-encoded or raw user_settings answer-style value."""
    if value is None:
        return None
    parsed = value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
    normalized = str(parsed or "").strip().lower()
    return normalized if normalized in {"simple", "technical"} else None


ALLOWED_APP_THEMES = frozenset({
    "heritage",
    "midnight",
    "obsidian",
    "aurora",
    "deepLagoon",
    "oliveGold",
    "oxfordTan",
    "stargazing",
    "mistyRose",
    "amethystEmber",
    "umberGold",
    "lilacRose",
    "obsidianPlum",
    "refinedEarth",
    "clarity",
    "monochrome",
})
APP_THEME_LABELS = {
    "heritage": "Heritage",
    "midnight": "Midnight",
    "obsidian": "Celestial Obsidian",
    "aurora": "Astral Aurora",
    "deepLagoon": "Deep Lagoon",
    "oliveGold": "Olive Gold",
    "oxfordTan": "Oxford Tan",
    "stargazing": "Stargazing",
    "mistyRose": "Misty Rose",
    "amethystEmber": "Amethyst Ember",
    "umberGold": "Umber Gold",
    "lilacRose": "Lilac Rose",
    "obsidianPlum": "Obsidian Plum",
    "refinedEarth": "Refined Earth",
    "clarity": "Clarity",
    "monochrome": "Black & white",
}
DEFAULT_APP_THEME = "heritage"
APP_THEME_SETTING_KEY = "app_theme"


def normalize_app_theme_id(value: object) -> Optional[str]:
    raw = str(value or "").strip()
    if raw == "dark":
        return "midnight"
    if raw == "light":
        return "heritage"
    if raw in ALLOWED_APP_THEMES:
        return raw
    return None


def parse_stored_app_theme(value: object) -> Optional[str]:
    """Normalize a user_settings row (JSON-encoded or raw) to a known theme id."""
    if value is None:
        return None
    parsed = value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
    return normalize_app_theme_id(parsed)


def app_theme_label(theme_id: Optional[str]) -> Optional[str]:
    if not theme_id:
        return None
    return APP_THEME_LABELS.get(theme_id, theme_id)


class AppThemePreference(BaseModel):
    theme_id: str

    def normalized_theme_id(self) -> str:
        theme_id = normalize_app_theme_id(self.theme_id)
        if not theme_id:
            raise HTTPException(status_code=422, detail="Unknown theme")
        return theme_id


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
            stored = _read_setting(conn, current_user.userid, CHAT_ANSWER_STYLE_SETTING_KEY)
        answer_style = parse_stored_chat_answer_style(stored)
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
                CHAT_ANSWER_STYLE_SETTING_KEY,
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


@router.get("/theme")
async def get_app_theme(current_user: User = Depends(get_current_user)):
    """Return the account-wide appearance theme, if one has been saved."""
    try:
        with get_conn() as conn:
            stored = _read_setting(conn, current_user.userid, APP_THEME_SETTING_KEY)
        theme_id = normalize_app_theme_id(stored)
        return {
            "theme_id": theme_id,
            "default_theme_id": DEFAULT_APP_THEME,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/theme")
async def update_app_theme(
    preference: AppThemePreference,
    current_user: User = Depends(get_current_user),
):
    """Persist the appearance theme for this account across devices."""
    theme_id = preference.normalized_theme_id()
    try:
        with get_conn() as conn:
            _upsert_setting(
                conn,
                current_user.userid,
                APP_THEME_SETTING_KEY,
                json.dumps(theme_id),
            )
            conn.commit()
        return {
            "theme_id": theme_id,
            "default_theme_id": DEFAULT_APP_THEME,
        }
    except HTTPException:
        raise
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
