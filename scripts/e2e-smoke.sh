#!/usr/bin/env bash
# Local smoke test — requires docker compose, API (:8000), and worker running.
set -euo pipefail
cd "$(dirname "$0")/.."
API="${API_BASE:-http://localhost:8000}"

curl -sf "$API/health" | grep -q ok || { echo "API not healthy at $API"; exit 1; }

RUN=$(curl -sf -X POST "$API/api/runs" -H "Content-Type: application/json" -d \
  '{"profile":{"filing_types":["10-K"],"tickers":["AAPL"],"years":[2023],"hitl_mode":"auto_approve_all"}}')
RUN_ID=$(echo "$RUN" | python3 -c "import json,sys; print(json.load(sys.stdin)['run_id'])")
echo "Started run $RUN_ID"

for _ in $(seq 1 30); do
  STATUS=$(curl -sf "$API/api/runs/$RUN_ID" | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])")
  COMPLETED=$(curl -sf "$API/api/runs/$RUN_ID" | python3 -c "import json,sys; print(json.load(sys.stdin)['completed_filings'])")
  echo "  status=$STATUS completed=$COMPLETED"
  [[ "$STATUS" == "completed" && "$COMPLETED" -ge 1 ]] && break
  sleep 3
done

curl -sf "$API/api/runs/$RUN_ID/filings" | python3 -c "
import json,sys
f=json.load(sys.stdin)
assert len(f)>=1, f
assert f[0]['status']=='completed', f
print('E2E smoke passed')
"
