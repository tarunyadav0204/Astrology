#!/usr/bin/env python3
"""Compile and validate the Travel, Relocation and Foreign Life ontology."""
from pathlib import Path
import validate_career_ontology as compiler

ROOT=Path(__file__).resolve().parents[1]
POC=ROOT / "knowledge_graph" / "foreign_life_poc"
compiler.POC=POC
compiler.TTL_PATH=POC / "astroroshni-foreign-life-poc.ttl"
compiler.CASES_PATH=POC / "competency-questions.json"
compiler.PREVIEW_PATH=POC / "foreign-life-runtime-preview.json"
compiler.REPORT_PATH=POC / "foreign-life-validation-report.md"

if __name__ == "__main__":
    raise SystemExit(compiler.main())
