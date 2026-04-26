# newop-sdc

Velocia App — clinical study authoring (New Opportunity / SDC / Protocol) on Databricks Apps.

This is the implementation repo. The product, architecture, and ADRs live in `../velocia/design-specs/`:

- Figma exploration and product analysis: `../velocia/design-specs/figma-exploration/`
- System architecture, data model, API contracts, sequences, ADRs: `../velocia/design-specs/architecture/`

## Quick start (local dev)

Prereqs: Python 3.11+, Node 20+, `uv` or `pip`, a Databricks workspace with a Lakebase Postgres available (or run with the bundled SQLite fallback for the very first boot).

```bash
make install         # install backend + frontend deps
make dev             # runs FastAPI on :8000 and Vite on :5173 (proxied)
make migrate         # alembic upgrade head against $DATABASE_URL
make test            # backend + frontend tests
```

For local development without a real agent, start the bundled fake agent:

```bash
make fake-agent      # FastAPI on :9000 mimicking the Agent API contract
```

## Layout

```
backend/        FastAPI app, SQLAlchemy models, Alembic migrations, agent client, Volume client
frontend/      React + Vite + Tailwind + shadcn/ui
tests/         Pytest (backend) + Playwright (frontend, later)
.github/       CI
```

See [`../velocia/design-specs/architecture/08-app-repo-layout.md`](../velocia/design-specs/architecture/08-app-repo-layout.md) for the full layout and conventions.

## Status

Scaffold. Most endpoints return `501 Not Implemented` and most components are stubs. The landing page is Figma-faithful; `/healthz` and `/api/me` are wired.
