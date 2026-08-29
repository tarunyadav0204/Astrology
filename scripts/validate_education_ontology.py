#!/usr/bin/env python3
"""Compile Education ontology policy with the shared local graph validator."""

from pathlib import Path

import validate_career_ontology as compiler


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "knowledge_graph" / "education_poc"
compiler.POC = POC
compiler.TTL_PATH = POC / "astroroshni-education-poc.ttl"
compiler.CASES_PATH = POC / "competency-questions.json"
compiler.PREVIEW_PATH = POC / "education-runtime-preview.json"
compiler.REPORT_PATH = POC / "education-validation-report.md"


if __name__ == "__main__":
    raise SystemExit(compiler.main())
