#!/usr/bin/env python3
"""Compile Children ontology policy with the shared local graph validator."""

from pathlib import Path

import validate_career_ontology as compiler


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "knowledge_graph" / "children_poc"
compiler.POC = POC
compiler.TTL_PATH = POC / "astroroshni-children-poc.ttl"
compiler.CASES_PATH = POC / "competency-questions.json"
compiler.PREVIEW_PATH = POC / "children-runtime-preview.json"
compiler.REPORT_PATH = POC / "children-validation-report.md"


if __name__ == "__main__":
    raise SystemExit(compiler.main())
