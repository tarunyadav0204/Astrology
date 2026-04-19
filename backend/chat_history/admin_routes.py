import re
import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import json
from datetime import datetime
from auth import get_current_user
from db import get_conn, execute

# YYYY-MM-DD for date filters (today / this month)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
logger = logging.getLogger(__name__)


def _normalize_date_range(
    start_date: Optional[str], end_date: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Return (start, end) as YYYY-MM-DD if both valid; else (None, None)."""
    if not start_date or not end_date:
        return None, None
    s = (start_date or "").strip()
    e = (end_date or "").strip()
    if not DATE_RE.match(s) or not DATE_RE.match(e) or s > e:
        return None, None
    return s, e


class AdminSetting(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class GlossaryTerm(BaseModel):
    term_id: str
    display_text: str
    definition: str
    language: Optional[str] = "english"
    aliases: Optional[List[str]] = None


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


router = APIRouter()


def _parse_parallel_llm_usage(raw: Any) -> Optional[Dict[str, Any]]:
    if not raw or not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _timestamp_to_ist_iso(val) -> Optional[str]:
    """Convert DB timestamp (naive, stored as server local / IST) to ISO string with +05:30 so frontend displays correct IST."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    # Already has timezone suffix
    if "Z" in s or "+" in s or (s.count("-") >= 2 and len(s) > 19 and s[-6] in ("+", "-")):
        return s
    # Naive: treat as IST and append +05:30
    s = s.replace(" ", "T", 1)
    if len(s) >= 19:
        s = s[:19]  # YYYY-MM-DDTHH:MM:SS
    return s + "+05:30"


# Rough USD rates per 1M tokens for chat-history cost estimates.
# Gemini 3.1 published pricing (USD per 1M tokens unless noted). INR ≈ USD × rate from _usd_to_inr_rate().
_CHAT_MODEL_RATE_USD_PER_1M: Dict[str, Dict[str, float]] = {
    # Gemini 3.1 (current product pricing)
    "models/gemini-3.1-flash-lite-preview": {
        "input_le_200k": 0.25,
        "input_gt_200k": 0.25,
        "output_le_200k": 1.50,
        "output_gt_200k": 1.50,
    },
    "models/gemini-3.1-pro-preview": {
        "input_le_200k": 2.00,
        "input_gt_200k": 4.00,
        "output_le_200k": 12.00,
        "output_gt_200k": 18.00,
    },
    "models/gemini-3.1-flash-live-preview": {
        "input_le_200k": 0.75,
        "input_gt_200k": 0.75,
        "output_le_200k": 4.50,
        "output_gt_200k": 4.50,
    },
    # Text output pricing; image generation billed separately (e.g. per image) in provider — not token-parity here.
    "models/gemini-3.1-flash-image-preview": {
        "input_le_200k": 0.25,
        "input_gt_200k": 0.25,
        "output_le_200k": 1.50,
        "output_gt_200k": 1.50,
    },
    "models/gemini-3.1-flash-tts-preview": {
        "input_le_200k": 1.00,
        "input_gt_200k": 1.00,
        "output_le_200k": 20.00,
        "output_gt_200k": 20.00,
    },
    # Gemini 3 (non-3.1) legacy preview ids
    "models/gemini-3-pro-preview": {
        "input_le_200k": 2.00, "input_gt_200k": 4.00, "output_le_200k": 12.00, "output_gt_200k": 18.00
    },
    "models/gemini-3-flash-preview": {
        "input_le_200k": 0.50, "input_gt_200k": 0.50, "output_le_200k": 3.00, "output_gt_200k": 3.00
    },
    # Gemini 2.5 family
    "models/gemini-2.5-pro": {
        "input_le_200k": 1.25, "input_gt_200k": 2.50, "output_le_200k": 10.00, "output_gt_200k": 15.00
    },
    "models/gemini-2.5-flash": {
        "input_le_200k": 0.30, "input_gt_200k": 0.30, "output_le_200k": 2.50, "output_gt_200k": 2.50
    },
    "models/gemini-2.5-flash-lite": {
        "input_le_200k": 0.10, "input_gt_200k": 0.10, "output_le_200k": 0.40, "output_gt_200k": 0.40
    },
    # Gemini 2.0 family
    "models/gemini-2.0-flash-001": {
        "input_le_200k": 0.10, "input_gt_200k": 0.10, "output_le_200k": 0.40, "output_gt_200k": 0.40
    },
    "models/gemini-2.0-flash-lite-001": {
        "input_le_200k": 0.075, "input_gt_200k": 0.075, "output_le_200k": 0.30, "output_gt_200k": 0.30
    },
    # OpenAI (approx)
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o4-mini": {"input": 1.10, "output": 4.40},
    "gpt-5.4-pro": {"input": 15.00, "output": 60.00},
    # DeepSeek (api-docs.deepseek.com/quick_start/pricing): cache-miss input + output; no >200k tier in public table.
    "deepseek-chat": {
        "input_le_200k": 0.28,
        "input_gt_200k": 0.28,
        "output_le_200k": 0.42,
        "output_gt_200k": 0.42,
    },
    "deepseek-reasoner": {
        "input_le_200k": 0.28,
        "input_gt_200k": 0.28,
        "output_le_200k": 0.42,
        "output_gt_200k": 0.42,
    },
    "deepseek-v4": {
        "input_le_200k": 0.28,
        "input_gt_200k": 0.28,
        "output_le_200k": 0.42,
        "output_gt_200k": 0.42,
    },
    "deepseek-v4-reasoner": {
        "input_le_200k": 0.28,
        "input_gt_200k": 0.28,
        "output_le_200k": 0.42,
        "output_gt_200k": 0.42,
    },
}


def _usd_to_inr_rate() -> float:
    raw = (os.getenv("USD_TO_INR_RATE") or "").strip()
    if raw:
        try:
            v = float(raw)
            if v > 0:
                return v
        except Exception:
            pass
    return 93.0


def _approx_tokens(text: Any) -> int:
    s = str(text or "")
    return max(1, int(round(len(s) / 4.0)))


def _row_optional_int(val: Any) -> Optional[int]:
    """SQL NULL → None; integer token/char counts preserved (including 0)."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _resolve_model_rate(model_name: Optional[str], input_tokens_est: int = 0) -> Dict[str, float]:
    if not model_name:
        return {"input": 0.10, "output": 0.40, "tier": "le_200k"}
    m = str(model_name).strip()
    tier = "gt_200k" if int(input_tokens_est or 0) > 200_000 else "le_200k"
    if m in _CHAT_MODEL_RATE_USD_PER_1M:
        cfg = _CHAT_MODEL_RATE_USD_PER_1M[m]
        if tier == "gt_200k":
            return {"input": float(cfg["input_gt_200k"]), "output": float(cfg["output_gt_200k"]), "tier": tier}
        return {"input": float(cfg["input_le_200k"]), "output": float(cfg["output_le_200k"]), "tier": tier}
    ml = m.lower()
    # Safe fallback by family if exact key not configured.
    if "gemini-3.1-flash-lite" in ml or ("3.1" in ml and "flash-lite" in ml):
        return {"input": 0.25, "output": 1.50, "tier": tier}
    if "gemini-3.1-flash-live" in ml or ("3.1" in ml and "flash-live" in ml):
        return {"input": 0.75, "output": 4.50, "tier": tier}
    if "gemini-3.1-flash-image" in ml or ("3.1" in ml and "flash-image" in ml):
        return {"input": 0.25, "output": 1.50, "tier": tier}
    if "gemini-3.1-flash-tts" in ml or ("3.1" in ml and "flash-tts" in ml) or (
        "gemini-3.1" in ml and "tts" in ml
    ):
        return {"input": 1.00, "output": 20.00, "tier": tier}
    if "gemini-3.1-pro" in ml:
        if tier == "gt_200k":
            return {"input": 4.00, "output": 18.00, "tier": tier}
        return {"input": 2.00, "output": 12.00, "tier": tier}
    if "flash-lite" in ml:
        return {"input": 0.10, "output": 0.40, "tier": tier}
    if "flash" in ml:
        return {"input": 0.50, "output": 3.00, "tier": tier}
    if "pro" in ml:
        return {"input": 2.00, "output": 12.00, "tier": tier}
    if "gpt-4o-mini" in ml:
        return {"input": 0.15, "output": 0.60, "tier": tier}
    if "gpt-4o" in ml:
        return {"input": 5.00, "output": 15.00, "tier": tier}
    # Any other deepseek-* (future ids): same ballpark as published chat/reasoner cache-miss pricing.
    if ml.startswith("deepseek-"):
        return {"input": 0.28, "output": 0.42, "tier": tier}
    return {"input": 0.10, "output": 0.40, "tier": tier}


_FIXED_INPUT_CHARS_PER_QUESTION = 200_000
_FIXED_INPUT_TOKENS_PER_QUESTION = max(1, int(round(_FIXED_INPUT_CHARS_PER_QUESTION / 4.0)))
_LIGHT_INPUT_CHARS_PER_QUESTION = 5_000
_LIGHT_INPUT_TOKENS_PER_QUESTION = max(1, int(round(_LIGHT_INPUT_CHARS_PER_QUESTION / 4.0)))

@router.get("/admin/chat/history/{user_id}")
async def get_user_chat_history(user_id: int, current_user: dict = Depends(require_admin)):
    """Get chat history for a specific user (admin only)"""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT session_id, created_at,
                       (SELECT content FROM chat_messages
                        WHERE session_id = cs.session_id
                        AND sender = 'user'
                        ORDER BY timestamp ASC LIMIT 1) as preview
                FROM chat_sessions cs
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall() or []
        sessions = []
        for row in rows:
            preview = row[2]
            preview_str = (preview[:100] + '...') if preview and len(preview) > 100 else preview
            sessions.append({
                'session_id': row[0],
                'created_at': _timestamp_to_ist_iso(row[1]),
                'preview': preview_str,
            })
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.get("/admin/chat/all-history")
async def get_all_chat_history(current_user: dict = Depends(require_admin)):
    """Get chat history for all users (admin only)"""
    try:
        from encryption_utils import EncryptionManager
        enc = EncryptionManager()
        sessions = []

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT cs.session_id, cs.user_id, cs.created_at, cs.birth_chart_id,
                       cs.chat_llm_provider, cs.chat_llm_model,
                       u.name, u.phone,
                       bc.name as native_name_raw,
                       (SELECT content FROM chat_messages
                        WHERE session_id = cs.session_id
                        AND sender = 'user'
                        ORDER BY timestamp ASC LIMIT 1) as preview,
                       (SELECT MAX(timestamp) FROM chat_messages
                        WHERE session_id = cs.session_id) as last_activity,
                       'new' as system_type
                FROM chat_sessions cs
                LEFT JOIN users u ON cs.user_id = u.userid
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                ORDER BY cs.created_at DESC
                LIMIT 500
                """,
                (),
            )
            for row in cur.fetchall() or []:
                native_name = None
                raw = row[8] if row[8] is not None else None
                if raw:
                    try:
                        native_name = enc.decrypt(raw)
                    except Exception:
                        native_name = raw
                display_time = row[10] if row[10] else row[2]
                preview = row[9]
                preview_str = (preview[:100] + '...') if preview and len(preview) > 100 else preview
                sessions.append({
                    'session_id': row[0],
                    'user_id': row[1],
                    'user_name': row[6] or 'Unknown User',
                    'user_phone': row[7] or 'No phone',
                    'created_at': _timestamp_to_ist_iso(display_time),
                    'preview': preview_str,
                    'system_type': row[11],
                    'native_name': native_name,
                    'chat_llm_provider': row[4],
                    'chat_llm_model': row[5],
                })

            cur = execute(
                conn,
                """
                SELECT cc.birth_hash, cc.conversation_data, cc.created_at,
                       'old' as system_type
                FROM chat_conversations cc
                ORDER BY cc.created_at DESC
                LIMIT 200
                """,
                (),
            )
            for row in cur.fetchall() or []:
                try:
                    conv_data = json.loads(row[1])
                    messages = conv_data.get('messages', [])
                    birth_data = conv_data.get('birth_data', {})
                    user_name = birth_data.get('name', f'Legacy User #{row[0][:8]}')
                    if messages:
                        first_question = messages[0].get('question', 'Chat conversation')
                        sessions.append({
                            'session_id': row[0],
                            'user_id': 'legacy',
                            'user_name': user_name,
                            'user_phone': 'Legacy System',
                            'created_at': _timestamp_to_ist_iso(row[2]),
                            'preview': first_question[:100] + '...' if len(first_question) > 100 else first_question,
                            'system_type': row[3],
                        })
                except Exception:
                    pass

        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return {"sessions": sessions[:500]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all chat history: {str(e)}")

@router.get("/admin/chat/session/{session_id}")
async def get_session_details(session_id: str, current_user: dict = Depends(require_admin)):
    """Get detailed messages for a specific session (admin only). Includes native_name (birth chart name) for the session."""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT cs.session_id, cs.user_id, cs.created_at, cs.birth_chart_id,
                       cs.chat_llm_provider, cs.chat_llm_model,
                       bc.name as native_name_raw
                FROM chat_sessions cs
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                WHERE cs.session_id = %s
                """,
                (session_id,),
            )
            session_row = cur.fetchone()

        if session_row:
            native_name = None
            raw_name = session_row[6] if len(session_row) > 6 and session_row[6] is not None else None
            chat_llm_provider = session_row[4] if len(session_row) > 4 else None
            chat_llm_model = session_row[5] if len(session_row) > 5 else None
            if raw_name:
                try:
                    from encryption_utils import EncryptionManager
                    enc = EncryptionManager()
                    native_name = enc.decrypt(raw_name)
                except Exception:
                    native_name = raw_name

            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'chat_messages'
                    """,
                    (),
                )
                msg_cols = {r[0] for r in (cur.fetchall() or [])}
                has_message_type = "message_type" in msg_cols

                has_llm_input_tokens = "llm_input_tokens" in msg_cols
                has_llm_output_tokens = "llm_output_tokens" in msg_cols
                has_llm_prompt_chars = "llm_prompt_chars" in msg_cols
                has_llm_response_chars = "llm_response_chars" in msg_cols
                has_parallel_llm_usage = "parallel_llm_usage" in msg_cols
                select_message_type = "COALESCE(message_type, '')" if has_message_type else "''"
                # Preserve SQL NULL so we can tell "not stored" from real API zeros.
                select_llm_input_tokens = (
                    "llm_input_tokens" if has_llm_input_tokens else "CAST(NULL AS INTEGER)"
                )
                select_llm_output_tokens = (
                    "llm_output_tokens" if has_llm_output_tokens else "CAST(NULL AS INTEGER)"
                )
                select_llm_prompt_chars = (
                    "llm_prompt_chars" if has_llm_prompt_chars else "CAST(NULL AS INTEGER)"
                )
                select_llm_response_chars = (
                    "llm_response_chars" if has_llm_response_chars else "CAST(NULL AS INTEGER)"
                )
                select_parallel_llm_usage = (
                    "parallel_llm_usage" if has_parallel_llm_usage else "CAST(NULL AS TEXT)"
                )
                cur = execute(
                    conn,
                    f"""
                    SELECT message_id, sender, content, timestamp, {select_message_type},
                           {select_llm_input_tokens}, {select_llm_output_tokens},
                           {select_llm_prompt_chars}, {select_llm_response_chars},
                           {select_parallel_llm_usage}
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY message_id ASC
                    """,
                    (session_id,),
                )
                msg_rows = cur.fetchall() or []
            session_input_tokens_est = sum(
                _approx_tokens(r[2]) for r in msg_rows if str(r[1] or "").strip().lower() == "user"
            )
            rates = _resolve_model_rate(chat_llm_model, session_input_tokens_est)
            fx = _usd_to_inr_rate()
            total_inr = 0.0
            messages = []
            for idx, r in enumerate(msg_rows):
                sender = r[1]
                content = r[2]
                # User question input is charged with fixed assumed context size per request.
                tokens_est = _approx_tokens(content)
                if sender == "user":
                    next_msg = msg_rows[idx + 1] if idx + 1 < len(msg_rows) else None
                    next_sender = (next_msg[1] if next_msg else "") or ""
                    next_type = ((next_msg[4] if next_msg else "") or "").strip().lower()
                    next_in_m = _row_optional_int(next_msg[5]) if next_msg and len(next_msg) > 5 else None
                    # Clarification/routing turn likely uses much smaller context than full answer turn.
                    if next_in_m is not None and next_in_m > 0:
                        tokens_est = next_in_m
                    elif next_sender == "assistant" and next_type == "clarification":
                        tokens_est = _LIGHT_INPUT_TOKENS_PER_QUESTION
                    else:
                        tokens_est = _FIXED_INPUT_TOKENS_PER_QUESTION
                elif sender == "assistant":
                    out_m = _row_optional_int(r[6]) if len(r) > 6 else None
                    if out_m is not None and out_m > 0:
                        tokens_est = out_m
                if sender == "user":
                    usd_per_1m = float(rates["input"])
                else:
                    usd_per_1m = float(rates["output"])
                cost_inr = (tokens_est / 1_000_000.0) * usd_per_1m * fx
                total_inr += cost_inr
                raw_in = _row_optional_int(r[5]) if len(r) > 5 else None
                raw_out = _row_optional_int(r[6]) if len(r) > 6 else None
                raw_pc = _row_optional_int(r[7]) if len(r) > 7 else None
                raw_rc = _row_optional_int(r[8]) if len(r) > 8 else None
                raw_parallel = r[9] if len(r) > 9 else None
                llm_in_display: Optional[int] = None
                llm_out_display: Optional[int] = None
                llm_prompt_chars_display: Optional[int] = None
                llm_response_chars_display: Optional[int] = None
                parallel_llm_usage_display: Optional[Dict[str, Any]] = None
                if str(sender or "").strip().lower() == "assistant":
                    if has_llm_input_tokens:
                        llm_in_display = raw_in
                    if has_llm_output_tokens:
                        llm_out_display = raw_out
                    if has_llm_prompt_chars and raw_pc is not None and raw_pc > 0:
                        llm_prompt_chars_display = raw_pc
                    if has_llm_response_chars and raw_rc is not None and raw_rc > 0:
                        llm_response_chars_display = raw_rc
                    if has_parallel_llm_usage:
                        parallel_llm_usage_display = _parse_parallel_llm_usage(raw_parallel)
                else:
                    # User row: full prompt / usage / reply size come from the assistant message for this turn.
                    nxt = msg_rows[idx + 1] if idx + 1 < len(msg_rows) else None
                    if nxt and str(nxt[1] or "").strip().lower() == "assistant" and len(nxt) > 9:
                        if has_llm_input_tokens:
                            llm_in_display = _row_optional_int(nxt[5])
                        if has_llm_output_tokens:
                            llm_out_display = _row_optional_int(nxt[6])
                        npc = _row_optional_int(nxt[7])
                        nrc = _row_optional_int(nxt[8])
                        if has_llm_prompt_chars and npc is not None and npc > 0:
                            llm_prompt_chars_display = npc
                        if has_llm_response_chars and nrc is not None and nrc > 0:
                            llm_response_chars_display = nrc
                        if has_parallel_llm_usage:
                            parallel_llm_usage_display = _parse_parallel_llm_usage(nxt[9])
                messages.append(
                    {
                        "sender": sender,
                        "content": content,
                        "timestamp": _timestamp_to_ist_iso(r[3]),
                        "native_name": native_name,
                        "llm_input_tokens": llm_in_display,
                        "llm_output_tokens": llm_out_display,
                        "llm_prompt_chars": llm_prompt_chars_display,
                        "llm_response_chars": llm_response_chars_display,
                        "parallel_llm_usage": parallel_llm_usage_display,
                        "cost_estimate": {
                            "tokens_estimate": tokens_est,
                            "cost_inr_estimate": round(cost_inr, 6),
                        },
                    }
                )
            return {
                "session_id": session_row[0],
                "user_id": session_row[1],
                "created_at": _timestamp_to_ist_iso(session_row[2]),
                "native_name": native_name,
                "chat_llm_provider": chat_llm_provider,
                "chat_llm_model": chat_llm_model,
                "messages": messages,
                "cost_summary": {
                    "currency": "INR",
                    "usd_to_inr_rate": fx,
                    "input_usd_per_1m": float(rates["input"]),
                    "output_usd_per_1m": float(rates["output"]),
                    "pricing_tier": rates.get("tier"),
                    "total_cost_inr_estimate": round(total_inr, 6),
                    "input_assumption": {
                        "input_chars_per_question_full": _FIXED_INPUT_CHARS_PER_QUESTION,
                        "input_tokens_per_question_full_estimate": _FIXED_INPUT_TOKENS_PER_QUESTION,
                        "input_chars_per_question_light": _LIGHT_INPUT_CHARS_PER_QUESTION,
                        "input_tokens_per_question_light_estimate": _LIGHT_INPUT_TOKENS_PER_QUESTION,
                    },
                    "note": "Rough estimate only. User-question input uses full-context estimate for normal turns and light estimate for clarification/routing turns; assistant output uses answer length.",
                },
            }

        with get_conn() as conn:
            cur = execute(
                conn,
                "SELECT birth_hash, conversation_data, updated_at FROM chat_conversations WHERE birth_hash = %s",
                (session_id,),
            )
            legacy_conv = cur.fetchone()

        if legacy_conv:
            try:
                conv_data = json.loads(legacy_conv[1])
                birth_data = conv_data.get('birth_data', {})
                legacy_native_name = birth_data.get('name') or None
                session_input_tokens_est = sum(
                    _approx_tokens(m.get("question")) for m in conv_data.get("messages", []) if m.get("question")
                )
                rates = _resolve_model_rate(None, session_input_tokens_est)
                fx = _usd_to_inr_rate()
                total_inr = 0.0
                messages = []
                updated_at = legacy_conv[2]
                for msg in conv_data.get('messages', []):
                    ts = _timestamp_to_ist_iso(msg.get('timestamp') or updated_at)
                    if msg.get('question'):
                        # Legacy rows do not reliably preserve message_type; use conservative light estimate for short questions.
                        q_tokens_est = (
                            _LIGHT_INPUT_TOKENS_PER_QUESTION
                            if len(str(msg.get("question") or "")) < 180
                            else _FIXED_INPUT_TOKENS_PER_QUESTION
                        )
                        q_cost_inr = (q_tokens_est / 1_000_000.0) * float(rates["input"]) * fx
                        total_inr += q_cost_inr
                        messages.append({
                            'sender': 'user',
                            'content': msg['question'],
                            'timestamp': ts,
                            'native_name': legacy_native_name,
                            'cost_estimate': {
                                'tokens_estimate': q_tokens_est,
                                'cost_inr_estimate': round(q_cost_inr, 6),
                            },
                        })
                    if msg.get('response'):
                        a_tokens_est = _approx_tokens(msg['response'])
                        a_cost_inr = (a_tokens_est / 1_000_000.0) * float(rates["output"]) * fx
                        total_inr += a_cost_inr
                        messages.append({
                            'sender': 'assistant',
                            'content': msg['response'],
                            'timestamp': ts,
                            'native_name': legacy_native_name,
                            'cost_estimate': {
                                'tokens_estimate': a_tokens_est,
                                'cost_inr_estimate': round(a_cost_inr, 6),
                            },
                        })
                return {
                    "session_id": session_id,
                    "user_id": "legacy",
                    "created_at": _timestamp_to_ist_iso(updated_at),
                    "native_name": legacy_native_name,
                    "messages": messages,
                    "cost_summary": {
                        "currency": "INR",
                        "usd_to_inr_rate": fx,
                        "input_usd_per_1m": float(rates["input"]),
                        "output_usd_per_1m": float(rates["output"]),
                        "pricing_tier": rates.get("tier"),
                        "total_cost_inr_estimate": round(total_inr, 6),
                        "input_assumption": {
                            "input_chars_per_question_full": _FIXED_INPUT_CHARS_PER_QUESTION,
                            "input_tokens_per_question_full_estimate": _FIXED_INPUT_TOKENS_PER_QUESTION,
                            "input_chars_per_question_light": _LIGHT_INPUT_CHARS_PER_QUESTION,
                            "input_tokens_per_question_light_estimate": _LIGHT_INPUT_TOKENS_PER_QUESTION,
                        },
                        "note": "Rough estimate only (legacy session). User-question input uses full/light fixed assumption based on prompt length; assistant output uses answer length.",
                    },
                }
            except Exception:
                pass

        raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching admin chat session details: session_id=%s", session_id)
        raise HTTPException(status_code=500, detail=f"Error fetching session details: {str(e)}")


@router.get("/admin/chat/analysis-stats")
async def get_chat_analysis_stats(current_user: dict = Depends(require_admin)):
    """Get category counts and FAQ (canonical_question) counts for chat analysis dashboard (admin only)."""
    try:
        with get_conn() as conn:
            # Post-migration safety: older DBs may miss these columns.
            cur = execute(
                conn,
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'chat_messages'
                """,
                (),
            )
            cols = {row[0] for row in (cur.fetchall() or [])}
            has_category = "category" in cols
            has_canonical = "canonical_question" in cols

            by_category = []
            by_faq = []

            if has_category:
                cur = execute(
                    conn,
                    """
                    SELECT category, COUNT(*) AS count
                    FROM chat_messages
                    WHERE sender = 'user' AND category IS NOT NULL AND trim(category) != ''
                    GROUP BY category
                    ORDER BY count DESC
                    """,
                    (),
                )
                by_category = [{"category": row[0], "count": row[1]} for row in (cur.fetchall() or [])]

            if has_canonical:
                cur = execute(
                    conn,
                    """
                    SELECT canonical_question, COUNT(*) AS count
                    FROM chat_messages
                    WHERE sender = 'user' AND canonical_question IS NOT NULL AND trim(canonical_question) != ''
                    GROUP BY canonical_question
                    ORDER BY count DESC
                    """,
                    (),
                )
                by_faq = [{"canonical_question": row[0], "count": row[1]} for row in (cur.fetchall() or [])]
        return {"by_category": by_category, "by_faq": by_faq}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat analysis stats: {str(e)}")


@router.get("/admin/settings")
async def get_all_settings(current_user: dict = Depends(require_admin)):
    """Get all admin settings plus Gemini model options and current model IDs."""
    try:
        from utils.admin_settings import (
            _ensure_admin_settings_table,
            GEMINI_MODEL_OPTIONS,
            OPENAI_CHAT_MODEL_OPTIONS,
            DEEPSEEK_CHAT_MODEL_OPTIONS,
            CHAT_LLM_GEMINI,
            CHAT_LLM_OPENAI,
            CHAT_LLM_DEEPSEEK,
            get_gemini_chat_model,
            get_gemini_premium_model,
            get_gemini_analysis_model,
            get_podcast_provider,
            get_chat_llm_provider,
            get_openai_chat_model,
            get_openai_premium_model,
            get_deepseek_chat_model,
            get_deepseek_premium_model,
            get_setting,
        )
        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            cur = execute(conn, "SELECT key, value, description FROM admin_settings", ())
            settings = [{"key": row[0], "value": row[1], "description": row[2]} for row in (cur.fetchall() or [])]
        _raw_premium = (get_setting("chat_llm_provider_premium") or "").strip().lower()
        _premium_ui = (
            _raw_premium
            if _raw_premium in (CHAT_LLM_GEMINI, CHAT_LLM_OPENAI, CHAT_LLM_DEEPSEEK)
            else ""
        )
        return {
            "settings": settings,
            "gemini_model_options": [{"value": v, "label": l} for v, l in GEMINI_MODEL_OPTIONS],
            "openai_model_options": [{"value": v, "label": l} for v, l in OPENAI_CHAT_MODEL_OPTIONS],
            "deepseek_model_options": [{"value": v, "label": l} for v, l in DEEPSEEK_CHAT_MODEL_OPTIONS],
            "gemini_chat_model": get_gemini_chat_model(),
            "gemini_premium_model": get_gemini_premium_model(),
            "gemini_analysis_model": get_gemini_analysis_model(),
            "chat_llm_provider": get_chat_llm_provider(),
            "chat_llm_provider_premium": _premium_ui,
            "openai_chat_model": get_openai_chat_model(),
            "openai_premium_model": get_openai_premium_model(),
            "deepseek_chat_model": get_deepseek_chat_model(),
            "deepseek_premium_model": get_deepseek_premium_model(),
            "podcast_provider": get_podcast_provider(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching settings: {str(e)}")


@router.get("/admin/terms")
async def get_glossary_terms(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(require_admin),
):
    """Get glossary terms (for chat glossary) with optional search and pagination."""
    try:
        where_clause = ""
        params: List[Any] = []
        if search:
            where_clause = "WHERE term_id LIKE %s OR display_text LIKE %s"
            like = f"%{search}%"
            params = [like, like]

        with get_conn() as conn:
            cur = execute(
                conn,
                f"SELECT COUNT(*) AS total FROM glossary_terms {where_clause}",
                tuple(params),
            )
            total = (cur.fetchone() or [0])[0]

            offset = (page - 1) * limit
            cur = execute(
                conn,
                f"""
                SELECT term_id, display_text, definition, language, COALESCE(aliases, '[]') AS aliases_json
                FROM glossary_terms
                {where_clause}
                ORDER BY term_id ASC
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (limit, offset),
            )
            rows = cur.fetchall() or []

        terms: List[Dict[str, Any]] = []
        for row in rows:
            try:
                aliases = json.loads(row[4]) if row[4] else []
                if not isinstance(aliases, list):
                    aliases = []
            except Exception:
                aliases = []
            terms.append({
                "term_id": row[0],
                "display_text": row[1],
                "definition": row[2],
                "language": row[3],
                "aliases": aliases,
            })

        return {
            "terms": terms,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "has_more": offset + limit < total,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching terms: {str(e)}")


@router.post("/admin/terms")
async def create_glossary_term(
    term: GlossaryTerm, current_user: dict = Depends(require_admin)
):
    """Create or overwrite a glossary term."""
    try:
        aliases_json = json.dumps(term.aliases or [])
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO glossary_terms (term_id, display_text, definition, language, aliases)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (term_id) DO UPDATE SET
                    display_text = EXCLUDED.display_text,
                    definition = EXCLUDED.definition,
                    language = EXCLUDED.language,
                    aliases = EXCLUDED.aliases
                """,
                (
                    term.term_id.strip(),
                    term.display_text.strip(),
                    term.definition.strip(),
                    term.language or "english",
                    aliases_json,
                ),
            )
        return {"message": "Term saved", "term_id": term.term_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving term: {str(e)}")


@router.put("/admin/terms/{term_id}")
async def update_glossary_term(
    term_id: str, term: GlossaryTerm, current_user: dict = Depends(require_admin)
):
    """Update an existing glossary term."""
    try:
        aliases_json = json.dumps(term.aliases or [])
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                UPDATE glossary_terms
                SET display_text = %s, definition = %s, language = %s, aliases = %s
                WHERE term_id = %s
                """,
                (
                    term.display_text.strip(),
                    term.definition.strip(),
                    term.language or "english",
                    aliases_json,
                    term_id,
                ),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Term not found")
            conn.commit()
        return {"message": "Term updated", "term_id": term_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating term: {str(e)}")


@router.delete("/admin/terms/{term_id}")
async def delete_glossary_term(
    term_id: str, current_user: dict = Depends(require_admin)
):
    """Delete a glossary term."""
    try:
        with get_conn() as conn:
            cur = execute(conn, "DELETE FROM glossary_terms WHERE term_id = %s", (term_id,))
            deleted = cur.rowcount
            conn.commit()
        if deleted == 0:
            raise HTTPException(status_code=404, detail="Term not found")
        return {"message": "Term deleted", "term_id": term_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting term: {str(e)}")

@router.put("/admin/settings/{key}")
async def update_setting(key: str, setting: AdminSetting, current_user: dict = Depends(require_admin)):
    """Update admin setting"""
    try:
        from utils.admin_settings import _ensure_admin_settings_table
        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            execute(
                conn,
                """
                INSERT INTO admin_settings (key, value, description, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT ("key") DO UPDATE SET
                    value = EXCLUDED.value,
                    description = EXCLUDED.description,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, setting.value, setting.description),
            )
            conn.commit()
        return {"message": "Setting updated", "key": key, "value": setting.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating setting: {str(e)}")

@router.get("/admin/facts")
async def get_all_user_facts(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """Get all facts in flat table format"""
    try:
        from encryption_utils import EncryptionManager
        encryption = EncryptionManager()

        where_clause = ""
        params: List[Any] = []
        if search:
            # Postgres: ILIKE is case-insensitive (LIKE alone is case-sensitive and often fails username search).
            # Match account name, phone, email, chart name (may be ciphertext), and stored fact text.
            pat = f"%{search}%"
            where_clause = (
                " WHERE (u.name ILIKE %s OR u.phone ILIKE %s OR COALESCE(u.email, '') ILIKE %s "
                "OR bc.name ILIKE %s OR uf.fact ILIKE %s)"
            )
            params = [pat, pat, pat, pat, pat]

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT COUNT(*) as total
                FROM user_facts uf
                INNER JOIN birth_charts bc ON bc.id = uf.birth_chart_id
                INNER JOIN users u ON u.userid = bc.userid
                {where_clause}
                """,
                tuple(params),
            )
            total = (cur.fetchone() or [0])[0]

            offset = (page - 1) * limit
            cur = execute(
                conn,
                f"""
                SELECT
                    u.userid, COALESCE(u.name, u.phone) as username, u.phone,
                    bc.id as birth_chart_id, bc.name as native_name,
                    uf.category, uf.fact, uf.extracted_at
                FROM user_facts uf
                INNER JOIN birth_charts bc ON bc.id = uf.birth_chart_id
                INNER JOIN users u ON u.userid = bc.userid
                {where_clause}
                ORDER BY u.name, bc.id, uf.category, uf.extracted_at DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (limit, offset),
            )
            rows = cur.fetchall() or []

        facts = []
        for row in rows:
            native_name = row[4]
            try:
                native_name = encryption.decrypt(native_name)
            except Exception:
                pass
            facts.append({
                'user_id': row[0],
                'username': row[1],
                'phone': row[2],
                'birth_chart_id': row[3],
                'native_name': native_name,
                'category': row[5],
                'fact': row[6],
                'extracted_at': row[7],
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return {
            'success': True,
            'facts': facts,
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': total_pages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facts: {str(e)}")


# Duration bucket keys and (min_sec, max_sec) for list filter. max_sec None = no upper bound.
DURATION_BUCKETS_LIST = [
    ("<30s", 0, 30),
    ("30-60s", 30, 60),
    ("60-90s", 60, 90),
    ("90-120s", 90, 120),
    ("2-3min", 120, 180),
    ("3-4min", 180, 240),
    ("4-5min", 240, 300),
    (">5min", 300, None),
]


@router.get("/admin/chat-performance")
async def get_chat_performance(
    page: int = 1,
    per_page: int = 20,
    duration_bucket: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Paginated chat performance. Optional duration_bucket and start_date/end_date (YYYY-MM-DD) to filter by completed_at."""
    if per_page < 1 or per_page > 100:
        per_page = 20
    if page < 1:
        page = 1
    offset = (page - 1) * per_page
    duration_filter = None
    if duration_bucket and duration_bucket != "all":
        for key, lo, hi in DURATION_BUCKETS_LIST:
            if key == duration_bucket:
                duration_filter = (lo, hi)
                break
    try:
        from encryption_utils import EncryptionManager
        try:
            encryption = EncryptionManager()
        except Exception:
            encryption = None

        base_where = """
            cm.sender = 'assistant' AND cm.status = 'completed'
            AND (cm.message_type = 'answer' OR (cm.content IS NOT NULL AND cm.content != ''))
        """
        duration_where = ""
        count_params: List[Any] = []
        if duration_filter:
            lo, hi = duration_filter
            duration_where = " AND cm.started_at IS NOT NULL AND cm.completed_at IS NOT NULL"
            duration_where += " AND EXTRACT(EPOCH FROM (cm.completed_at::timestamp - cm.started_at::timestamp)) >= %s"
            count_params.append(lo)
            if hi is not None:
                duration_where += " AND EXTRACT(EPOCH FROM (cm.completed_at::timestamp - cm.started_at::timestamp)) < %s"
                count_params.append(hi)
        date_where = ""
        sdate, edate = _normalize_date_range(start_date, end_date)
        if sdate and edate:
            date_where = " AND cm.completed_at IS NOT NULL AND cm.completed_at::date >= %s AND cm.completed_at::date <= %s"
            count_params.extend([sdate, edate])

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT COUNT(*) FROM chat_messages cm
                WHERE {base_where}{duration_where}{date_where}
                """,
                tuple(count_params),
            )
            total = (cur.fetchone() or [0])[0]

            # Optional columns: check Postgres information_schema
            cur = execute(
                conn,
                "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'chat_messages'",
                (),
            )
            cols = [r[0] for r in (cur.fetchall() or [])]
            has_language = 'language' in cols
            has_intent_ms = 'intent_router_ms' in cols

            sel = """
                SELECT cm.message_id, cm.content, cm.started_at, cm.completed_at,
                       cs.session_id, u.name as user_name, u.phone as user_phone,
                       bc.name as native_name,
                       (SELECT content FROM chat_messages m2
                        WHERE m2.session_id = cm.session_id AND m2.sender = 'user' AND m2.message_id < cm.message_id
                        ORDER BY m2.message_id DESC LIMIT 1) as user_question
            """
            if has_language:
                sel += ", cm.language"
            if has_intent_ms:
                sel += ", cm.intent_router_ms"
            sel += f"""
                FROM chat_messages cm
                JOIN chat_sessions cs ON cs.session_id = cm.session_id
                LEFT JOIN users u ON u.userid = cs.user_id
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                WHERE {base_where}{duration_where}{date_where}
                ORDER BY cm.message_id DESC
                LIMIT %s OFFSET %s
            """
            cur = execute(conn, sel, tuple(count_params) + (per_page, offset))
            rows = cur.fetchall() or []
            colnames = [d[0] for d in cur.description] if cur.description else []

        items = []
        for row in rows:
            row_dict = dict(zip(colnames, row)) if colnames else {}
            content = row_dict.get('content') or ''
            preview = content[:300].strip() + ('…' if len(content) > 300 else '')
            user_question = row_dict.get('user_question') or ''
            uq_preview = user_question[:150].strip() + ('…' if len(user_question) > 150 else '')
            started = row_dict.get('started_at')
            completed = row_dict.get('completed_at')
            duration_seconds = None
            if started and completed:
                try:
                    s = datetime.fromisoformat(started.replace('Z', '+00:00')) if isinstance(started, str) else started
                    c = datetime.fromisoformat(completed.replace('Z', '+00:00')) if isinstance(completed, str) else completed
                    duration_seconds = round((c - s).total_seconds(), 2)
                except Exception:
                    pass
            raw_native = row_dict.get('native_name')
            if raw_native and encryption:
                try:
                    native_name = encryption.decrypt(raw_native)
                except Exception:
                    native_name = raw_native
            else:
                native_name = raw_native or '—'
            items.append({
                'message_id': row_dict.get('message_id'),
                'user_name': row_dict.get('user_name') or '—',
                'user_phone': row_dict.get('user_phone') or '—',
                'user_question': uq_preview,
                'response_preview': preview,
                'native_name': native_name,
                'intent_router_ms': row_dict.get('intent_router_ms') if has_intent_ms else None,
                'duration_seconds': duration_seconds,
                'completed_at': row_dict.get('completed_at'),
            })
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if per_page else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat performance: {str(e)}")


# Duration buckets for charts: (label, min_seconds, max_seconds). max_seconds None = no upper bound.
DURATION_BUCKETS = [
    ("<30s", 0, 30),
    ("30-60s", 30, 60),
    ("60-90s", 60, 90),
    ("90-120s", 90, 120),
    ("2-3 min", 120, 180),
    ("3-4 min", 180, 240),
    ("4-5 min", 240, 300),
    (">5 min", 300, None),
]


@router.get("/admin/chat-performance/stats")
async def get_chat_performance_stats(
    limit: int = 5000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Aggregated duration bucket counts (overall and by user) for Charts tab. Optional start_date/end_date (YYYY-MM-DD)."""
    if limit < 1 or limit > 20000:
        limit = 5000
    try:
        date_where = ""
        params: List[Any] = [limit]
        sdate, edate = _normalize_date_range(start_date, end_date)
        if sdate and edate:
            date_where = " AND cm.completed_at IS NOT NULL AND cm.completed_at::date >= %s AND cm.completed_at::date <= %s"
            params = [sdate, edate, limit]
        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT cm.message_id, cm.started_at, cm.completed_at,
                       COALESCE(u.name, u.phone, 'Unknown') as user_name, u.phone as user_phone
                FROM chat_messages cm
                JOIN chat_sessions cs ON cs.session_id = cm.session_id
                LEFT JOIN users u ON u.userid = cs.user_id
                WHERE cm.sender = 'assistant' AND cm.status = 'completed'
                AND (cm.message_type = 'answer' OR (cm.content IS NOT NULL AND cm.content != ''))
                AND cm.started_at IS NOT NULL AND cm.completed_at IS NOT NULL
                {date_where}
                ORDER BY cm.message_id DESC
                LIMIT %s
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            colnames = [d[0] for d in cur.description] if cur.description else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

    def duration_seconds(started, completed):
        if not started or not completed:
            return None
        try:
            s = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            c = datetime.fromisoformat(str(completed).replace("Z", "+00:00"))
            return (c - s).total_seconds()
        except Exception:
            return None

    def bucket_for(sec):
        if sec is None:
            return None
        for label, lo, hi in DURATION_BUCKETS:
            if hi is None:
                if sec >= lo:
                    return label
            elif lo <= sec < hi:
                return label
        return None

    bucket_counts = {label: 0 for label, _, _ in DURATION_BUCKETS}
    user_buckets = {}

    for row in rows:
        r = dict(zip(colnames, row)) if colnames else {}
        sec = duration_seconds(r.get("started_at"), r.get("completed_at"))
        b = bucket_for(sec)
        if b is None:
            continue
        bucket_counts[b] = bucket_counts.get(b, 0) + 1
        user_key = (r.get("user_name") or "Unknown", r.get("user_phone") or "")
        if user_key not in user_buckets:
            user_buckets[user_key] = {label: 0 for label, _, _ in DURATION_BUCKETS}
        user_buckets[user_key][b] = user_buckets[user_key].get(b, 0) + 1

    buckets = [{"name": label, "count": bucket_counts[label]} for label, _, _ in DURATION_BUCKETS]
    by_user = []
    for (uname, uphone), counts in user_buckets.items():
        by_user.append({
            "user_name": uname,
            "user_phone": uphone or "",
            "buckets": [{"name": label, "count": counts.get(label, 0)} for label, _, _ in DURATION_BUCKETS],
        })

    SLOW_THRESHOLD_SEC = 120
    hour_labels = [
        "12am", "1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am",
        "12pm", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm",
    ]
    slow_by_hour = {h: 0 for h in range(24)}
    for row in rows:
        r = dict(zip(colnames, row)) if colnames else {}
        sec = duration_seconds(r.get("started_at"), r.get("completed_at"))
        if sec is None or sec < SLOW_THRESHOLD_SEC:
            continue
        completed = r.get("completed_at")
        if not completed:
            continue
        try:
            if isinstance(completed, str):
                dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            else:
                dt = completed
            hour = dt.hour
            slow_by_hour[hour] = slow_by_hour.get(hour, 0) + 1
        except Exception:
            pass
    slow_by_hour_list = [
        {"hour": h, "hour_label": hour_labels[h], "count": slow_by_hour[h]}
        for h in range(24)
    ]

    return {"buckets": buckets, "by_user": by_user, "slow_by_hour": slow_by_hour_list}