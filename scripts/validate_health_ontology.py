#!/usr/bin/env python3
"""Compile Health ontology policy with the shared local graph validator."""

from pathlib import Path

import validate_career_ontology as compiler


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "knowledge_graph" / "health_poc"
compiler.POC = POC
compiler.TTL_PATH = POC / "astroroshni-health-poc.ttl"
compiler.CASES_PATH = POC / "competency-questions.json"
compiler.PREVIEW_PATH = POC / "health-runtime-preview.json"
compiler.REPORT_PATH = POC / "health-validation-report.md"


if __name__ == "__main__":
    raise SystemExit(compiler.main())
