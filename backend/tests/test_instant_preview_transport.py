import asyncio
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from chat_history import routes


@pytest.mark.parametrize("terminal", ["completed", "failed"])
def test_socket_relays_separate_preview_then_answer_or_failure(monkeypatch, terminal):
    preview = {"type": "instant_preview", "content": "Calculated fact.", "language": "english"}
    encoded = json.dumps([preview])
    rows = [("processing", "", None, 7, encoded)]
    if terminal == "completed":
        rows += [("processing", "LLM explanation", None, 7, encoded),
                 ("completed", "LLM explanation.", None, 7, encoded)]
    else:
        rows += [("failed", "", "Generation failed", 7, encoded)]
    snapshots = iter(rows)

    @contextmanager
    def connection():
        yield object()

    monkeypatch.setattr(routes, "get_conn", connection)
    monkeypatch.setattr(routes, "execute", lambda *args: SimpleNamespace(fetchone=lambda: next(snapshots)))
    monkeypatch.setattr(routes, "_chat_stream_token", lambda ws: "token")
    monkeypatch.setattr(routes, "_chat_stream_user", lambda token: SimpleNamespace(userid=7))

    async def final_status(*args, **kwargs):
        return {"status": "completed", "content": "LLM explanation."}

    monkeypatch.setattr(routes, "check_message_status", final_status)

    class Socket:
        def __init__(self):
            self.events = []
        async def accept(self):
            pass
        async def send_json(self, payload):
            self.events.append(payload)
        async def close(self, **kwargs):
            pass

    socket = Socket()
    asyncio.run(routes.stream_message_status(socket, 42))
    assert socket.events[1] == {"type": "preview", "message_id": 42, "preview": preview}
    assert socket.events[-1]["type"] == terminal
    if terminal == "failed":
        assert not any(e["type"] in {"content_delta", "completed"} for e in socket.events)
    else:
        chunks = [e for e in socket.events if e["type"] == "content_delta"]
        assert chunks[0]["content"] == "LLM explanation"
        assert chunks[-1]["delta"] == "."
        assert "Calculated fact" not in chunks[-1]["content"]
