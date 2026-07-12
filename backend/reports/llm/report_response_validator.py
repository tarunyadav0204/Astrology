from __future__ import annotations

from typing import Any, Dict


def validate_report_json(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Report payload must be a JSON object")
    if "sections" in payload and not isinstance(payload["sections"], list):
        raise ValueError("sections must be a list")
    return payload

