"""
Local LLM for event timeline (yearly / monthly deep) — no Gemini API billing.

Targets **Ollama** on the same machine or LAN (common setup for Gemma-class models).
Pull your Gemma build into Ollama first, e.g. when a `gemma4` tag exists:

  ollama pull <your-gemma4-tag>

Environment (enable local path):

  EVENT_TIMELINE_USE_LOCAL_LLM=1
  OLLAMA_HOST=http://127.0.0.1:11434    # optional, default shown
  OLLAMA_MODEL=gemma4:31b-it            # must match `ollama list` name
  OLLAMA_TIMEOUT_SEC=3600               # optional; long JSON needs high value
  OLLAMA_NUM_PREDICT=65536              # optional; max output tokens (timeline JSON is huge)
  OLLAMA_NUM_CTX=32768                  # optional; context length if model supports it

If EVENT_TIMELINE_USE_LOCAL_LLM is unset/false, EventPredictor uses Gemini as before.

Yearly timeline: prompt is often 150k+ characters and the model must emit 12 months of dense JSON.
On a local 12B class model this can take tens of minutes to hours; logs print a heartbeat every 45s
while waiting. For faster local iteration use EVENT_TIMELINE_TEST_MONTH=1..12 in EventPredictor’s
yearly path, or run monthly-deep (single month) from the app.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict

import requests


def event_timeline_uses_local_llm() -> bool:
    v = (os.getenv("EVENT_TIMELINE_USE_LOCAL_LLM") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _ollama_host() -> str:
    return (os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")


def _ollama_model() -> str:
    return (os.getenv("OLLAMA_MODEL") or "").strip()


def _ollama_timeout() -> float:
    try:
        return float(os.getenv("OLLAMA_TIMEOUT_SEC") or "3600")
    except ValueError:
        return 3600.0


def generate_event_timeline_json(prompt: str) -> str:
    """
    Send the full timeline prompt to Ollama with JSON-constrained output.
    Returns raw text expected to be a single JSON object (same contract as Gemini).
    """
    model = _ollama_model()
    if not model:
        raise RuntimeError(
            "OLLAMA_MODEL is not set. Example: OLLAMA_MODEL=gemma4:31b-it "
            "(name must match an installed Ollama model)."
        )

    host = _ollama_host()
    url = f"{host}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
    }
    opts: Dict[str, Any] = {}
    num_ctx = os.getenv("OLLAMA_NUM_CTX")
    if num_ctx:
        try:
            opts["num_ctx"] = int(num_ctx)
        except ValueError:
            pass
    try:
        opts["num_predict"] = int(os.getenv("OLLAMA_NUM_PREDICT") or "65536")
    except ValueError:
        opts["num_predict"] = 65536
    if opts:
        payload["options"] = opts

    timeout = _ollama_timeout()
    print(f"\n🦙 Ollama request: POST {url} model={model!r} timeout={timeout}s")

    plen = len(prompt)
    if plen > 80_000 and not (os.getenv("OLLAMA_NUM_CTX") or "").strip():
        print(
            "⚠️  Large prompt but OLLAMA_NUM_CTX is unset — Ollama may use the model default "
            "and truncate input. Set OLLAMA_NUM_CTX (e.g. 65536 or 131072) if generation hangs or "
            "returns empty/invalid JSON."
        )

    stop_hb = threading.Event()
    t0 = time.monotonic()

    def _heartbeat() -> None:
        interval = 45.0
        while not stop_hb.wait(interval):
            elapsed = int(time.monotonic() - t0)
            print(
                f"⏳ Ollama still generating (yearly JSON can take many minutes on local GPU) — "
                f"elapsed {elapsed}s, prompt ~{plen} chars…"
            )

    hb = threading.Thread(target=_heartbeat, daemon=True)
    hb.start()
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    finally:
        stop_hb.set()
    resp.raise_for_status()
    data = resp.json()

    message = data.get("message") or {}
    content = message.get("content")
    if not content or not isinstance(content, str):
        raise RuntimeError(f"Ollama returned no message.content: keys={list(data.keys())}")

    return content
