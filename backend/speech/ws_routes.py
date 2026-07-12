from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import jwt
from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect

from auth import ALGORITHM, SECRET_KEY, User
from chat_history.routes import ask_question_async, check_message_status
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech", tags=["speech_ws"])

POLL_INTERVAL_SECONDS = 0.9
MAX_TURN_SECONDS = 150
PING_INTERVAL_SECONDS = 25


def _json_preview(value: Any, limit: int = 240) -> str:
    try:
        raw = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        raw = str(value)
    raw = raw.replace("\n", " ").strip()
    return raw[:limit]


def _split_answer_chunks(text: str, max_chars: int = 520) -> List[str]:
    raw = " ".join(str(text or "").split()).strip()
    if not raw:
        return []

    import re

    sentences = re.findall(r"[^.!?।]+[.!?।]+|[^.!?।]+$", raw) or [raw]
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        item = sentence.strip()
        if not item:
            continue
        candidate = f"{current} {item}".strip() if current else item
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = item
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [raw]


def _token_from_websocket(websocket: WebSocket) -> Optional[str]:
    token = websocket.query_params.get("token") or websocket.query_params.get("access_token")
    if token:
        return str(token).strip()
    auth = websocket.headers.get("authorization") or websocket.headers.get("x-astroroshni-authorization")
    if not auth:
        return None
    auth = str(auth).strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return auth or None


def _user_from_token(token: str) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone = payload.get("sub")
        if not phone:
            raise ValueError("missing subject")
    except Exception as exc:
        raise ValueError("invalid token") from exc

    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT userid, name, phone, role, signup_client FROM users WHERE phone = ?",
            (phone,),
        )
        row = cur.fetchone()
    if row is None:
        raise ValueError("user not found")
    signup_client = row[4] if len(row) > 4 else None
    if signup_client is not None and str(signup_client).strip() == "":
        signup_client = None
    return User(userid=row[0], name=row[1], phone=row[2], role=row[3], signup_client=signup_client)


async def _send(websocket: WebSocket, event_type: str, **payload: Any) -> None:
    try:
        await websocket.send_json(
            {
                "type": event_type,
                "ts": int(time.time() * 1000),
                **payload,
            }
        )
    except (WebSocketDisconnect, RuntimeError) as exc:
        text = str(exc)
        if isinstance(exc, WebSocketDisconnect) or "websocket.close" in text or "websocket.send" in text:
            logger.debug("SPEECH_WS send skipped after close event=%s error=%s", event_type, text[:160])
            return
        raise


async def _run_background_tasks(background_tasks: BackgroundTasks) -> None:
    for task in list(getattr(background_tasks, "tasks", []) or []):
        result = task.func(*task.args, **task.kwargs)
        if inspect.isawaitable(result):
            await result


async def _invoke_chat_v2(request: Dict[str, Any], user: User) -> Dict[str, Any]:
    background_tasks = BackgroundTasks()
    response = await ask_question_async(request, background_tasks, user)
    if getattr(background_tasks, "tasks", None):
        asyncio.create_task(_run_background_tasks(background_tasks))
    return response


async def _poll_answer(message_id: int, user: User, cancel_event: asyncio.Event, websocket: WebSocket, turn_id: str) -> Dict[str, Any]:
    started = time.monotonic()
    last_status = None
    while True:
        if cancel_event.is_set():
            raise asyncio.CancelledError()
        if time.monotonic() - started > MAX_TURN_SECONDS:
            raise TimeoutError("The answer is taking too long. Please try again.")
        status_payload = await check_message_status(message_id, user)
        status = status_payload.get("status")
        if status != last_status:
            await _send(
                websocket,
                "turn_status",
                turn_id=turn_id,
                message_id=message_id,
                status=status,
                message_type=status_payload.get("message_type") or "answer",
            )
            last_status = status
        if status == "completed" or status_payload.get("recovered_after_failure"):
            return status_payload
        if status == "failed":
            raise RuntimeError(status_payload.get("error_message") or "Answer failed. Please try again.")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _handle_ask(
    websocket: WebSocket,
    user: User,
    payload: Dict[str, Any],
    cancel_event: asyncio.Event,
) -> None:
    turn_id = str(payload.get("turn_id") or uuid.uuid4())
    question = str(payload.get("question") or payload.get("transcript") or "").strip()
    if not question:
        await _send(websocket, "turn_error", turn_id=turn_id, error="empty_question", message="No question text received.")
        return

    session_id = str(payload.get("session_id") or "").strip()
    birth_details = payload.get("birth_details") or {}
    if not session_id or not isinstance(birth_details, dict):
        await _send(websocket, "turn_error", turn_id=turn_id, error="missing_context", message="Missing session_id or birth_details.")
        return

    language = payload.get("language") or "english"
    request = {
        "session_id": session_id,
        "question": question,
        "query_context": payload.get("query_context") or {},
        "language": language,
        "response_style": "concise",
        "premium_analysis": False,
        "chat_tier": "instant",
        "speech_chat": True,
        "speech_billing": False,
        "native_name": payload.get("native_name") or birth_details.get("name"),
        "birth_details": birth_details,
        "client_request_id": str(payload.get("client_request_id") or f"speech_ws_{turn_id}"),
    }

    logger.info(
        "SPEECH_WS ask user_id=%s turn_id=%s session_id=%s question=%r",
        user.userid,
        turn_id,
        session_id,
        question[:160],
    )
    await _send(websocket, "turn_started", turn_id=turn_id, question=question)
    await _send(websocket, "answer_processing", turn_id=turn_id, message="Reading the chart...")

    ask_response = await _invoke_chat_v2(request, user)
    message_id = ask_response.get("message_id")
    if not message_id:
        if ask_response.get("status") == "completed":
            final_payload = ask_response
        else:
            raise RuntimeError("Could not start answer generation.")
    elif ask_response.get("status") == "completed":
        final_payload = ask_response
    else:
        await _send(websocket, "turn_queued", turn_id=turn_id, message_id=message_id)
        final_payload = await _poll_answer(int(message_id), user, cancel_event, websocket, turn_id)

    content = str(final_payload.get("content") or final_payload.get("response") or "").strip()
    if not content:
        raise RuntimeError("The answer came back empty. Please try again.")

    chunks = _split_answer_chunks(content)
    for index, chunk in enumerate(chunks):
        if cancel_event.is_set():
            raise asyncio.CancelledError()
        await _send(
            websocket,
            "answer_chunk",
            turn_id=turn_id,
            message_id=message_id,
            index=index,
            total=len(chunks),
            text=chunk,
        )
        await asyncio.sleep(0)

    await _send(
        websocket,
        "turn_completed",
        turn_id=turn_id,
        message_id=message_id,
        content=content,
        follow_up_questions=final_payload.get("follow_up_questions") or [],
        next_action=final_payload.get("next_action"),
    )


@router.websocket("/ws")
async def speech_conversation_ws(websocket: WebSocket) -> None:
    token = _token_from_websocket(websocket)
    try:
        user = _user_from_token(token or "")
    except Exception:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    await websocket.accept()
    logger.info("SPEECH_WS connected user_id=%s client=%s", user.userid, websocket.client)
    await _send(
        websocket,
        "ready",
        protocol="astroroshni.speech.v1",
        user_id=user.userid,
        ping_interval_seconds=PING_INTERVAL_SECONDS,
    )

    active_task: Optional[asyncio.Task] = None
    active_cancel = asyncio.Event()
    last_ping = time.monotonic()

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=PING_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                if time.monotonic() - last_ping >= PING_INTERVAL_SECONDS:
                    await _send(websocket, "ping")
                    last_ping = time.monotonic()
                continue

            try:
                payload = json.loads(raw)
            except Exception:
                await _send(websocket, "error", error="bad_json", message="Invalid websocket message.")
                continue

            event_type = str(payload.get("type") or "").strip()
            if event_type == "pong":
                continue
            if event_type == "cancel":
                active_cancel.set()
                if active_task and not active_task.done():
                    active_task.cancel()
                await _send(websocket, "cancelled", turn_id=payload.get("turn_id"))
                continue
            if event_type in {"ask", "user_transcript"}:
                active_cancel.set()
                if active_task and not active_task.done():
                    active_task.cancel()
                    try:
                        await active_task
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        logger.exception("SPEECH_WS previous turn failed while cancelling")
                active_cancel = asyncio.Event()

                async def run_turn(turn_payload: Dict[str, Any], turn_cancel: asyncio.Event) -> None:
                    turn_id = str(turn_payload.get("turn_id") or "")
                    try:
                        await _handle_ask(websocket, user, turn_payload, turn_cancel)
                    except asyncio.CancelledError:
                        await _send(websocket, "turn_cancelled", turn_id=turn_id)
                    except Exception as exc:
                        logger.exception(
                            "SPEECH_WS turn failed user_id=%s payload=%s",
                            user.userid,
                            _json_preview(turn_payload),
                        )
                        await _send(
                            websocket,
                            "turn_error",
                            turn_id=turn_id,
                            error=type(exc).__name__,
                            message=str(exc) or "Something went wrong. Please try again.",
                        )

                active_task = asyncio.create_task(run_turn(dict(payload), active_cancel))
                continue

            await _send(websocket, "error", error="unknown_type", message=f"Unknown event type: {event_type}")
    except WebSocketDisconnect:
        pass
    finally:
        active_cancel.set()
        if active_task and not active_task.done():
            active_task.cancel()
            try:
                await active_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.debug("SPEECH_WS active turn ended during websocket cleanup", exc_info=True)
