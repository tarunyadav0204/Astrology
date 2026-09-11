from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from credits.routes import (  # noqa: E402
    _speech_billing_description,
    _speech_billing_metadata,
    _speech_confirmed_elapsed_seconds,
    _speech_confirmed_interval_seconds,
    _speech_minutes_from_seconds,
)


def test_speech_billing_uses_started_minutes_and_captured_rate() -> None:
    assert _speech_minutes_from_seconds(446) == 8
    description = _speech_billing_description(8, 446, 5, "connection_lost")
    assert description == (
        "Talk To Tara call: 8 started minute(s), 446s at 5 credits/min (connection_lost)"
    )


def test_speech_ledger_metadata_makes_rate_auditable() -> None:
    metadata = json.loads(_speech_billing_metadata("speech_123", 8, 446, 5, "connection_lost"))
    assert metadata == {
        "billing_type": "speech",
        "speech_billing_session_id": "speech_123",
        "billed_started_minutes": 8,
        "elapsed_seconds": 446,
        "per_minute_cost": 5,
        "ended_reason": "connection_lost",
    }


def test_speech_meter_rejects_suspended_or_abandoned_wall_clock_gap() -> None:
    assert _speech_confirmed_interval_seconds(0) == 0
    assert _speech_confirmed_interval_seconds(10) == 10
    assert _speech_confirmed_interval_seconds(20) == 20
    assert _speech_confirmed_interval_seconds(21) == 0
    assert _speech_confirmed_interval_seconds(446) == 0
    assert _speech_confirmed_elapsed_seconds(50, 446) == 50
    assert _speech_minutes_from_seconds(_speech_confirmed_elapsed_seconds(50, 446)) == 1
