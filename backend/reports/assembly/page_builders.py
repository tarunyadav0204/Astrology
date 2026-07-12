from __future__ import annotations

from typing import Any, Dict, List


def render_chart_section(title: str, refs: List[str]) -> Dict[str, Any]:
    return {"title": title, "chart_refs": refs}


def render_table_section(title: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"title": title, "rows": rows}


def render_bullet_section(title: str, bullets: List[str]) -> Dict[str, Any]:
    return {"title": title, "bullets": bullets}

