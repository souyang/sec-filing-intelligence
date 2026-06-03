#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --package sec-alphaops-worker python -m sec_alphaops_worker.main
