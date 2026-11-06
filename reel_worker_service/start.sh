#!/usr/bin/env bash
set -euo pipefail
cd /app
export PYTHONPATH="/app${PYTHONPATH:+:${PYTHONPATH}}"
exec uvicorn reel_worker_service.main:app --host 0.0.0.0 --port "${PORT:-8080}"
