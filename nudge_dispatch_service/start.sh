#!/usr/bin/env bash
set -euo pipefail

cd /app

export PYTHONPATH="/app:/app/backend${PYTHONPATH:+:${PYTHONPATH}}"

exec uvicorn nudge_dispatch_service.main:app --host 0.0.0.0 --port "${PORT:-8080}"
