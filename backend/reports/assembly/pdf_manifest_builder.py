from __future__ import annotations

from typing import Any, Dict, List


def build_pdf_manifest(report_document: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages = report_document.get("pages", [])
    return [
        {
            "page_number": page.get("page_number"),
            "title": page.get("title"),
            "chart_refs": page.get("chart_refs", []),
        }
        for page in pages
    ]

