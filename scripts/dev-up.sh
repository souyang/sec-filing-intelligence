#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d
echo "Postgres :5432 | Redis :6379 | Temporal :7233 | Temporal UI :8080"
