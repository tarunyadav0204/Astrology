#!/bin/bash

set -euo pipefail

APP_ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "${APP_ROOT}/scripts/deploy-release.sh" "$@"
