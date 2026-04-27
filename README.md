# newop-sdc

Velocia App — clinical study authoring (New Opportunity / SDC / Protocol) on Databricks Apps.

This is the implementation repo. The product, architecture, and ADRs live in `../velocia/design-specs/`:

- Figma exploration and product analysis: `../velocia/design-specs/figma-exploration/`
- System architecture, data model, API contracts, sequences, ADRs: `../velocia/design-specs/architecture/`

## Quick start (local dev)

Prereqs: Python 3.12+, Node 20+, `uv` or `pip`, a Databricks workspace with a Lakebase Postgres available (or run with the bundled SQLite fallback for the very first boot).

```bash
make install         # install backend + frontend deps
make dev             # runs FastAPI on :8000 and Vite on :5173 (proxied)
make test            # backend + frontend tests
```

**Windows users:** the project also ships `tasks.ps1`, a PowerShell wrapper that mirrors every Makefile target, so you don't need GNU Make:

```powershell
.\tasks.ps1 install
.\tasks.ps1 build
.\tasks.ps1 bundle-deploy -Profile <your-profile>
.\tasks.ps1 help                    # full task list
```

For local development without a real agent, start the bundled fake agent:

```bash
make fake-agent      # or: .\tasks.ps1 fake-agent  (FastAPI on :9000 mimicking the Agent API contract)
```

## Package registries

The frontend ships with `frontend/.npmrc` setting `replace-registry-host=always` (no pinned registry). This makes **one `package-lock.json` work in any environment** without workflow changes: npm fetches from whichever registry your `~/.npmrc` (or `npm_config_registry`) points at, and `resolved` URLs in the lockfile get rewritten to that host on the fly. If you have no `~/.npmrc`, npm uses its built-in public registry (`https://registry.npmjs.org/`).

This pattern is useful if some developers sit behind a corporate npm proxy and CI uses public npm — both work from the same lockfile.

For Python: pip doesn't capture URLs in a lock file the way npm does, so the trick isn't needed. If you later pin transitive deps with `uv lock` / `pip-tools`, add a similar override.

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

Everything (the FastAPI app on Databricks Apps and the Lakebase Postgres it talks to) is described by `databricks.yml` at the repo root. There is no manual click-through step.

Before you deploy, set:

1. **Workspace host** — edit `targets.dev.workspace.host` in `databricks.yml`.
2. **CLI profile** — set `DBX_PROFILE` (Makefile var) to your Databricks CLI profile name, or pass `--profile <name>` directly.

```bash
make build                                       # populate frontend/dist (the SPA bundle the app serves)
make bundle-validate DBX_PROFILE=<your-profile>  # databricks bundle validate -t dev
make bundle-deploy   DBX_PROFILE=<your-profile>  # provisions Lakebase + app and deploys code
make seed-dev        DBX_PROFILE=<your-profile>  # idempotent: 1 user + 5 study_documents + access grants
make bundle-destroy  DBX_PROFILE=<your-profile>  # tear it all down
```

After `bundle-deploy`, the app URL follows the pattern:

```
https://velocia-newop-sdc-<workspace-id>.azure.databricksapps.com
```

(Resolved at runtime; `make app-status` prints it. The first `bundle-deploy` blocks on Lakebase provisioning, which can take a few minutes.)

### What the bundle owns

- `database_instances.velocia_db` — Lakebase Postgres instance (`velocia-newop-sdc-db`, CU_1, single node).
- `apps.velocia` — the Databricks App, with the Lakebase database bound under resource key `database` (perm `CAN_CONNECT_AND_CREATE`). Defaults to the auto-created `databricks_postgres` logical database; override with `--var db_logical_name=...` if you want to bind to a different existing database on the instance.

The bundle does NOT create a Unity Catalog wrapping the Postgres database — the app talks to Lakebase directly via asyncpg and doesn't need UC. This avoids requiring `CREATE CATALOG` on the metastore (a permission engagement / customer service principals frequently lack). To opt in to a UC catalog later, uncomment the `database_catalogs` block in `databricks.yml` (or have a UC admin create it manually).

`app.yaml` reads the runtime-injected `PGHOST` / `PGUSER` / `PGDATABASE`, assembles a credential-free `DATABASE_URL`, and execs uvicorn against `$DATABRICKS_APP_PORT`. `backend/db/session.py` mints a Lakebase OAuth token (via `WorkspaceClient.database.generate_database_credential`) for every new physical pool connection — a static `PGPASSWORD` is **not** injected by the runtime, by design. Schema is auto-created on app startup via SQLAlchemy `Base.metadata.create_all` (see `backend/db/session.py:init_db`); no Alembic.

> **First-deploy ordering note:** Lakebase's default `public` schema doesn't grant `CREATE` to non-superuser Postgres roles, so the app's service principal can't run `init_db()` until it's been granted CREATE on `public`. `make seed-dev` handles this (it runs as the human DB-instance creator, who is a Lakebase superuser, and idempotently grants the SP). On a fresh deploy run `make seed-dev` once before the app's first SSO login — afterwards the app's `lifespan()` will be able to create tables on its own.

### Seeding

`scripts/seed_dev.py` mints a Lakebase OAuth token through the SDK, connects with `asyncpg`, and inserts a small fixture (1 user, 5 study documents, 5 access grants). It uses `ON CONFLICT DO NOTHING` and stable UUIDs so reruns are safe. By default the script auto-discovers the bound DB from `databricks apps get velocia-newop-sdc`; pass `--app` to point at a different deployment.

If your laptop can't reach the Lakebase host on port 5432 (corporate firewalls, no VPN — symptom on Windows is `semaphore timeout period has expired`), use **`scripts/seed_dev.sql`** instead. It's a self-contained SQL script — DDL + grants + the same fixture rows — that you paste into the workspace's SQL editor (or any in-workspace Postgres client). Replace `<SEED_USER_EMAIL>`, `<SEED_USER_NAME>`, and `<APP_SP_CLIENT_ID>` placeholders before running.

### Day-2 ops

```bash
make app-status                                            # databricks apps get velocia-newop-sdc
make app-restart                                           # stop + start the app (picks up env / resource changes)
databricks bundle deploy -t dev --profile <your-profile>   # redeploy code only
databricks bundle destroy -t dev --profile <your-profile> -y   # full cleanup
```
