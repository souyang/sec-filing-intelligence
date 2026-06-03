# SEC AlphaOps

Configurable batch SEC filing intelligence pipeline (10-K MVP) using Temporal, LangGraph, FastAPI, Postgres, Redis, and a Next.js SSE dashboard.

## Quick start (local)

```bash
cp .env.example .env
./scripts/dev-up.sh
uv sync --all-packages
pnpm install
uv run alphaops-migrate   # or auto-runs on API startup

./scripts/dev-api.sh       # :8000
./scripts/dev-worker.sh    # Temporal worker
pnpm dev:web             # :3000
```

- API docs: http://localhost:8000/docs
- Temporal UI: http://localhost:8080
- Dashboard: http://localhost:3000

## Typical flow

1. **Hydrate cache** (optional locally; uses demo text if no EDGAR cache): Dashboard → “Hydrate cache” or `POST /api/cache/hydrate`
2. **Start batch**: Dashboard → tickers/years → “Start batch run”
3. **Watch SSE**: Run detail page streams `run:{id}:events` from Redis
4. **Review**: Low-confidence extractions appear in `/review` → Approve/Reject resumes Temporal workflow

## Monorepo layout

| Path | Purpose |
|------|---------|
| `apps/web` | Next.js dashboard + reviewer UI |
| `apps/api` | FastAPI REST + SSE |
| `apps/worker` | Temporal worker + activities |
| `packages/common` | Config, schemas, R2/Redis/Temporal helpers |
| `packages/workflows` | Temporal workflow definitions |
| `packages/langgraph` | Extraction pipeline + prompts |
| `packages/db` | Postgres models + repositories |
| `packages/contracts` | OpenAPI + SSE schema codegen |

## Commands

```bash
uv run pytest packages/ -q
uv run ruff check .
pnpm typecheck:web
pnpm generate:contracts
./scripts/e2e-smoke.sh   # API + worker must be running
```

See [project-plan.md](./project-plan.md) for architecture and scaling notes.
