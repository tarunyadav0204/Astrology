#!/usr/bin/env python3
"""Compile Marriage and Relationship ontology with the shared graph validator."""

from pathlib import Path

import validate_career_ontology as compiler


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "knowledge_graph" / "marriage_poc"
compiler.POC = POC
compiler.TTL_PATH = POC / "astroroshni-marriage-poc.ttl"
compiler.CASES_PATH = POC / "competency-questions.json"
compiler.PREVIEW_PATH = POC / "marriage-runtime-preview.json"
compiler.REPORT_PATH = POC / "marriage-validation-report.md"


if __name__ == "__main__":
    raise SystemExit(compiler.main())
