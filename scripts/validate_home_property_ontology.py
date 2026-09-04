#!/usr/bin/env python3
"""Compile and validate the Home, Property and Vehicles ontology."""
from pathlib import Path
import validate_career_ontology as compiler

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "knowledge_graph" / "home_property_poc"
compiler.POC = POC
compiler.TTL_PATH = POC / "astroroshni-home-property-poc.ttl"
compiler.CASES_PATH = POC / "competency-questions.json"
compiler.PREVIEW_PATH = POC / "home-property-runtime-preview.json"
compiler.REPORT_PATH = POC / "home-property-validation-report.md"

if __name__ == "__main__":
    raise SystemExit(compiler.main())
