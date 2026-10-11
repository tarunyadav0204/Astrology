"""Persistent conversation socket reusing the authenticated durable ask pipeline."""
import asyncio
import logging
from fastapi import BackgroundTasks, HTTPException, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

_tasks = set()
logger = logging.getLogger(__name__)


def _work_done(task):
    _tasks.discard(task)
    if not task.cancelled() and task.exception():
        logger.error("Conversation background work failed", exc_info=task.exception())


class TurnRelay:
    """Keep the conversation open when a per-message relay completes."""
    def __init__(self, socket):
        self.socket = socket
        self.query_params = socket.query_params
        self.headers = socket.headers

    async def accept(self):
        pass

    async def send_json(self, payload):
        await self.socket.send_json(payload)

    async def close(self, **kwargs):
        pass


async def serve_conversation(socket, *, authenticate, token, ask, relay):
    try:
        user = await asyncio.to_thread(authenticate, token(socket))
    except ValueError:
        await socket.close(code=4401)
        return
    await socket.accept()
    await socket.send_json({"type": "conversation_ready", "version": 1})
    try:
        while True:
            try:
                payload = await asyncio.wait_for(socket.receive_json(), timeout=600)
            except ValueError:
                await socket.send_json({"type": "error", "status": 400, "error": "Invalid JSON"})
                continue
            if not isinstance(payload, dict):
                await socket.send_json({"type": "error", "status": 400, "error": "Invalid command"})
                continue
            if payload.get("type") == "ping":
                await socket.send_json({"type": "pong"})
                continue
            request = payload.get("request")
            request_id = payload.get("request_id")
            if payload.get("type") != "ask" or not isinstance(request, dict):
                await socket.send_json({"type": "error", "request_id": request_id, "status": 400, "error": "Expected ask command"})
                continue
            if not request.get("client_request_id"):
                await socket.send_json({"type": "error", "request_id": request_id, "status": 400, "error": "client_request_id is required"})
                continue
            background = BackgroundTasks()
            try:
                result = await ask(request, background_tasks=background, current_user=user)
            except HTTPException as exc:
                await socket.send_json({"type": "error", "request_id": request_id,
                                        "status": exc.status_code, "detail": jsonable_encoder(exc.detail)})
                continue
            # Accepted work survives a disconnected client. Recovery uses the same
            # client_request_id and the existing status/stream endpoints.
            task = asyncio.create_task(background())
            _tasks.add(task)
            task.add_done_callback(_work_done)
            await socket.send_json({"type": "queued", "request_id": request_id, "payload": jsonable_encoder(result)})
            if result.get("message_id"):
                await relay(TurnRelay(socket), result["message_id"])
    except WebSocketDisconnect:
        return
    except asyncio.TimeoutError:
        await socket.close(code=1000)
