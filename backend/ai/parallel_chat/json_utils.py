"""Best-effort JSON extraction from LLM branch outputs."""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def parse_branch_json(raw: str, branch_id: str) -> Dict[str, Any]:
    """
    Parse branch JSON. On failure, wrap raw text so synthesis can still proceed.
    """
    text = (raw or "").strip()
    if not text:
        return {"branch": branch_id, "status": "empty", "analysis": "", "bullets": []}
    # Strip ```json ... ``` if present
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            data.setdefault("branch", branch_id)
            return data
    except json.JSONDecodeError:
        pass
    return {
        "branch": branch_id,
        "status": "unparsed",
        "analysis": text[:16000],
        "bullets": [],
    }
