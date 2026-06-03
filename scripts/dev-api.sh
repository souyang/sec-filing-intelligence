#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --package sec-alphaops-api uvicorn sec_alphaops_api.main:app --reload --host 0.0.0.0 --port 8000
