"""
Build push nudge copy (title, body, question) from a user's recent completed chat Q&A via Gemini.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from db import execute

logger = logging.getLogger(__name__)

_MAX_Q_CHARS = 6000
_MAX_A_CHARS = 12000

# Short JSON copy: prefer stable Flash **Lite** models (not admin "analysis", which may be Pro).
# Override with env GEMINI_ADMIN_NUDGE_MODEL (full id, e.g. models/gemini-2.5-flash-lite).
_CHEAP_NUDGE_GEMINI_MODELS = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.0-flash-lite-001",
    "models/gemini-3.1-flash-lite-preview",
]

# Rough USD rates per 1M tokens (input/output) for estimate display only.
# These are intentionally approximate and can be overridden per env.
_MODEL_RATE_USD_PER_1M: Dict[str, Dict[str, float]] = {
    # Gemini 3 family
    "models/gemini-3.1-pro-preview": {
        "input_le_200k": 2.00,
        "input_gt_200k": 4.00,
        "output_le_200k": 12.00,
        "output_gt_200k": 18.00,
    },
    "models/gemini-3-pro-preview": {
        "input_le_200k": 2.00,
        "input_gt_200k": 4.00,
        "output_le_200k": 12.00,
        "output_gt_200k": 18.00,
    },
    "models/gemini-3-flash-preview": {
        "input_le_200k": 0.50,
        "input_gt_200k": 0.50,
        "output_le_200k": 3.00,
        "output_gt_200k": 3.00,
    },
    # Gemini 2.5 family
    "models/gemini-2.5-pro": {
        "input_le_200k": 1.25,
        "input_gt_200k": 2.50,
        "output_le_200k": 10.00,
        "output_gt_200k": 15.00,
    },
    "models/gemini-2.5-flash": {
        "input_le_200k": 0.30,
        "input_gt_200k": 0.30,
        "output_le_200k": 2.50,
        "output_gt_200k": 2.50,
    },
    "models/gemini-2.5-flash-lite": {
        "input_le_200k": 0.10,
        "input_gt_200k": 0.10,
        "output_le_200k": 0.40,
        "output_gt_200k": 0.40,
    },
    # Gemini 2.0 family
    "models/gemini-2.0-flash-001": {
        "input_le_200k": 0.10,
        "input_gt_200k": 0.10,
        "output_le_200k": 0.40,
        "output_gt_200k": 0.40,
    },
    "models/gemini-2.0-flash-lite-001": {
        "input_le_200k": 0.075,
        "input_gt_200k": 0.075,
        "output_le_200k": 0.30,
        "output_gt_200k": 0.30,
    },
}


def _approx_token_count(text: str) -> int:
    # Very rough cross-model estimate: ~4 characters per token.
    return max(1, int(round(len(text or "") / 4.0)))


def _resolve_rate(used_model: str, input_tokens_est: int) -> Dict[str, float]:
    env_in = os.getenv("GEMINI_ADMIN_NUDGE_INPUT_USD_PER_1M")
    env_out = os.getenv("GEMINI_ADMIN_NUDGE_OUTPUT_USD_PER_1M")
    if env_in and env_out:
        try:
            return {"input": float(env_in), "output": float(env_out), "tier": "env_override"}
        except Exception:
            pass
    tier = "gt_200k" if int(input_tokens_est or 0) > 200_000 else "le_200k"
    cfg = _MODEL_RATE_USD_PER_1M.get(used_model or "")
    if not cfg:
        return {"input": 0.10, "output": 0.40, "tier": tier}
    if tier == "gt_200k":
        return {
            "input": float(cfg["input_gt_200k"]),
            "output": float(cfg["output_gt_200k"]),
            "tier": tier,
        }
    return {
        "input": float(cfg["input_le_200k"]),
        "output": float(cfg["output_le_200k"]),
        "tier": tier,
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


def _nudge_suggestion_model_names() -> List[str]:
    from utils.admin_settings import GEMINI_MODEL_OPTIONS

    env_override = (os.getenv("GEMINI_ADMIN_NUDGE_MODEL") or "").strip()
    seen: set[str] = set()
    out: List[str] = []
    if env_override:
        out.append(env_override)
        seen.add(env_override)
    for n in _CHEAP_NUDGE_GEMINI_MODELS:
        if n not in seen:
            out.append(n)
            seen.add(n)
    for mid, _label in GEMINI_MODEL_OPTIONS:
        if mid not in seen:
            out.append(mid)
            seen.add(mid)
    return out


def load_last_completed_qa_turns(conn, user_id: int, max_turns: int = 2) -> List[Dict[str, str]]:
    """
    Return up to `max_turns` most recent completed user→assistant pairs for chat-v2,
    in chronological order (oldest of the slice first), globally across all sessions for user_id.

    A turn counts only when an assistant message follows a user message with status `completed`
    and non-empty content. Failed/cancelled assistant clears pending user question without a turn.
    """
    max_turns = max(1, min(2, int(max_turns)))
    cur = execute(
        conn,
        """
        SELECT cm.sender, cm.content, COALESCE(NULLIF(TRIM(cm.status), ''), 'completed') AS status,
               cm.timestamp, cm.message_id
        FROM chat_messages cm
        INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cs.user_id = %s
        ORDER BY cm.timestamp ASC, cm.message_id ASC
        """,
        (int(user_id),),
    )
    rows = cur.fetchall() or []

    turns: List[Dict[str, str]] = []
    pending_q: Optional[str] = None

    for row in rows:
        sender = (row[0] or "").strip().lower()
        content = (row[1] or "").strip()
        status = (row[2] or "completed").strip().lower()

        if sender == "user":
            if content:
                pending_q = content[:_MAX_Q_CHARS]
            continue

        if sender == "assistant":
            if status in ("processing", "pending"):
                continue
            if status in ("failed", "cancelled"):
                pending_q = None
                continue
            if status == "completed" and pending_q and content:
                turns.append({"question": pending_q, "answer": content[:_MAX_A_CHARS]})
                pending_q = None

    if len(turns) <= max_turns:
        return turns
    return turns[-max_turns:]


def _gemini_response_text(response: Any) -> str:
    """Best-effort plain text from google.generativeai response (handles blocked / empty .text)."""
    try:
        t = (getattr(response, "text", None) or "").strip()
        if t:
            return t
    except Exception:
        pass
    parts: List[str] = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        for p in getattr(content, "parts", None) or []:
            txt = getattr(p, "text", None)
            if txt:
                parts.append(txt)
    return "\n".join(parts).strip()


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def generate_push_nudge_via_gemini(qa_turns: List[Dict[str, str]]) -> Dict[str, Any]:
    """Call Gemini; return title/body/question plus rough usage cost estimate."""
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    names = _nudge_suggestion_model_names()
    model = None
    used_name = None
    for name in names:
        try:
            model = genai.GenerativeModel(name)
            used_name = name
            break
        except Exception:
            continue
    if not model:
        raise RuntimeError("No Gemini model available")

    qa_block = []
    for i, t in enumerate(qa_turns, start=1):
        qa_block.append(f"--- Exchange {i} ---\nUser question:\n{t['question']}\n\nAssistant answer (excerpt ok for tone):\n{t['answer'][:8000]}")
    qa_text = "\n\n".join(qa_block)

    prompt = f"""You write short mobile push notifications for an astrology app (AstroRoshni).

You are given one or two completed chat exchanges (user question + assistant answer). Craft ONE follow-up nudge that:
- Feels personal but does NOT paste private details verbatim in the title (lock screen safe).
- Encourages the user to continue in chat with a focused astrological follow-up.
- Make the suggested question clearly astrological and useful.

Return ONLY valid JSON (no markdown outside JSON) with exactly these keys:
- "title": string, max 90 characters, engaging, no quotes inside.
- "body": string, max 190 characters, expands slightly on title (notification body).
- "question": string, max 480 characters, ONE suggested message the user could send in chat.

Question quality requirements:
- Must be astrology-specific (mention dasha / transit / planetary period / chart factor when relevant).
- Must ask for practical guidance (daily or weekly actions, timing windows, or cautions).
- Prefer a concrete time window (e.g., next 30/90 days) when natural.
- Keep it as one clear question sentence (no bullet points, no multiple unrelated asks).
- Avoid generic motivation language.

Good style example:
"In my current Saturn-Rahu dasha, what daily diet and stress-management routine should I follow over the next 3 months, and which periods should I be extra careful about?"

Chat context:
{qa_text}
"""

    try:
        response = model.generate_content(prompt, request_options={"timeout": 90})
        text = _gemini_response_text(response)
    except Exception as e:
        logger.exception("Gemini generate nudge failed: %s", e)
        raise RuntimeError(str(e)) from e

    data = _extract_json_object(text)
    if not isinstance(data, dict):
        raise RuntimeError("Gemini did not return parseable JSON")

    title = str(data.get("title") or "").strip()[:100]
    body = str(data.get("body") or "").strip()[:200]
    question = str(data.get("question") or "").strip()[:500]
    if not title or not body or not question:
        raise RuntimeError("Gemini JSON missing title, body, or question")

    input_chars = len(prompt)
    output_chars = len(text)
    input_tokens_est = _approx_token_count(prompt)
    output_tokens_est = _approx_token_count(text)
    rates = _resolve_rate(used_name or "", input_tokens_est)
    input_cost_usd = (input_tokens_est / 1_000_000.0) * float(rates["input"])
    output_cost_usd = (output_tokens_est / 1_000_000.0) * float(rates["output"])
    total_cost_usd = input_cost_usd + output_cost_usd
    usd_to_inr = _usd_to_inr_rate()
    input_cost_inr = input_cost_usd * usd_to_inr
    output_cost_inr = output_cost_usd * usd_to_inr
    total_cost_inr = total_cost_usd * usd_to_inr

    logger.info(
        "Generated nudge from chat via Gemini model=%s est_usd=%.8f",
        used_name,
        total_cost_usd,
    )
    return {
        "title": title,
        "body": body,
        "question": question,
        "model_used": used_name,
        "usage_estimate": {
            "input_chars": input_chars,
            "output_chars": output_chars,
            "input_tokens_estimate": input_tokens_est,
            "output_tokens_estimate": output_tokens_est,
            "input_usd_per_1m": float(rates["input"]),
            "output_usd_per_1m": float(rates["output"]),
            "pricing_tier": rates.get("tier"),
            "usd_to_inr_rate": usd_to_inr,
            "input_cost_inr_estimate": round(input_cost_inr, 6),
            "output_cost_inr_estimate": round(output_cost_inr, 6),
            "total_cost_inr_estimate": round(total_cost_inr, 6),
            "note": "Rough INR estimate only (token approximation, pricing and FX can vary).",
        },
    }
