#!/usr/bin/env bash

set -euo pipefail

APP_ROOT="${APP_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-${APP_ROOT}/backend/venv/bin/python}"

if [ ! -x "${PYTHON_BIN}" ]; then
  echo "❌ Knowledge-graph compiler Python is unavailable: ${PYTHON_BIN}"
  exit 1
fi

required_sources=(
  "${APP_ROOT}/knowledge_graph/core/astroroshni-life-domains.ttl"
  "${APP_ROOT}/knowledge_graph/manifestation/manifestation-ontology.ttl"
  "${APP_ROOT}/knowledge_graph/manifestation/competency-cases.json"
)
for source_path in "${required_sources[@]}"; do
  if [ ! -s "${source_path}" ]; then
    echo "❌ Required knowledge-graph source is missing: ${source_path}"
    exit 1
  fi
done

echo "🧠 Compiling knowledge-graph runtime bundles..."
"${PYTHON_BIN}" "${APP_ROOT}/scripts/validate_life_domain_ontology.py"
"${PYTHON_BIN}" "${APP_ROOT}/scripts/validate_manifestation_ontology.py"

required_outputs=(
  "${APP_ROOT}/knowledge_graph/core/life-domain-runtime.json"
  "${APP_ROOT}/knowledge_graph/manifestation/manifestation-runtime.json"
)
for output_path in "${required_outputs[@]}"; do
  if [ ! -s "${output_path}" ]; then
    echo "❌ Knowledge-graph compiler did not produce: ${output_path}"
    exit 1
  fi
done

echo "✅ Knowledge-graph runtime bundles compiled and validated"
