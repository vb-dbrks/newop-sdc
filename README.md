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

## Package registries: internal proxy vs public

The frontend ships with `frontend/.npmrc` setting `replace-registry-host=always` (no pinned registry). This makes **one `package-lock.json` work in both environments** without any workflow changes:

- **Internal (Databricks laptops behind the firewall):** your `~/.npmrc` already points at the corporate proxy (`https://npm-proxy.dev.databricks.com/`). npm uses the proxy as usual; lock-file URLs get rewritten to proxy host on the fly.
- **GitHub Actions / external CI:** no `~/.npmrc`, so npm uses its built-in public registry (`https://registry.npmjs.org/`). Lock-file URLs (which carry the proxy host from internal `npm install`) get rewritten to public on the fly.

For Python:
- **Internal:** your `~/.pip/pip.conf` already points at the corporate PyPI mirror; nothing to do.
- **CI:** uses public PyPI by default.

pip doesn't capture URLs in a lock file the way npm does, so the npm trick isn't needed there. If we ever pin transitive deps with `uv lock` / `pip-tools`, we'll add a similar override.

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
