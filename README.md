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

## Deploy to Databricks

Everything (the FastAPI app on Databricks Apps and the Lakebase Postgres it talks to) is described by `databricks.yml` at the repo root. There is no manual click-through step. The default target is `dev`, pointing at the field-eng workspace via the `fieldeng` CLI profile.

```bash
make build                 # populate frontend/dist (the SPA bundle the app serves)
make bundle-validate       # databricks bundle validate -t dev --profile fieldeng
make bundle-deploy         # provisions Lakebase + app and deploys code
make seed-dev              # idempotent: 1 user + 5 study_documents + access grants
make bundle-destroy        # tear it all down
```

After `bundle-deploy`, the app URL follows the pattern:

```
https://velocia-newop-sdc-<workspace-id>.azure.databricksapps.com
```

(Resolved at runtime; `make app-status` prints it. The first `bundle-deploy` blocks on Lakebase provisioning, which can take a few minutes.)

### What the bundle owns

- `database_instances.velocia_db` — Lakebase Postgres instance (`velocia-newop-sdc-db`, CU_1, single node).
- `database_catalogs.velocia_db_catalog` — UC catalog wrapping the Postgres database (`velocia`).
- `apps.velocia` — the Databricks App, with the Postgres database bound under resource key `database` (perm `CAN_CONNECT_AND_CREATE`).

`app.yaml` reads the runtime-injected `PGHOST` / `PGUSER` / `PGDATABASE`, assembles a credential-free `DATABASE_URL`, and execs uvicorn against `$DATABRICKS_APP_PORT`. `backend/db/session.py` mints a Lakebase OAuth token (via `WorkspaceClient.database.generate_database_credential`) for every new physical pool connection — a static `PGPASSWORD` is **not** injected by the runtime, by design. Schema is auto-created on app startup via SQLAlchemy `Base.metadata.create_all` (see `backend/db/session.py:init_db`); no Alembic.

> **First-deploy ordering note:** Lakebase's default `public` schema doesn't grant `CREATE` to non-superuser Postgres roles, so the app's service principal can't run `init_db()` until it's been granted CREATE on `public`. `make seed-dev` handles this (it runs as the human DB-instance creator, who is a Lakebase superuser, and idempotently grants the SP). On a fresh deploy run `make seed-dev` once before the app's first SSO login — afterwards the app's `lifespan()` will be able to create tables on its own.

### Seeding

`scripts/seed_dev.py` mints a Lakebase OAuth token through the SDK, connects with `asyncpg`, and inserts a small fixture (1 user, 5 study documents, 5 access grants). It uses `ON CONFLICT DO NOTHING` and stable UUIDs so reruns are safe. By default the script auto-discovers the bound DB from `databricks apps get velocia-newop-sdc`; pass `--app` to point at a different deployment.

### Day-2 ops

```bash
make app-status            # databricks apps get velocia-newop-sdc
make app-restart           # stop + start the app (picks up env / resource changes)
databricks bundle deploy -t dev --profile fieldeng   # redeploy code only
databricks bundle destroy -t dev --profile fieldeng -y   # full cleanup
```
