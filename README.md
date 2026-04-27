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

**Windows users:** install GNU make once (`winget install ezwinports.make` or `choco install make`); the Makefile is written to be portable (no `rm` / `find` / bash-only constructs) so the same targets work under cmd.exe, PowerShell, and POSIX shells.

For local development without a real agent, start the bundled fake agent:

```bash
make fake-agent      # FastAPI on :9000 mimicking the Agent API contract
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

Before `bundle-deploy`, also edit **`app.yaml`** and set the dev seed values:

```yaml
- name: SEED_USER_EMAIL
  value: "alice@yourcompany.com"   # the human who'll log in via SSO
- name: SEED_USER_NAME
  value: "Alice Customer"
```

The app's lifespan inserts the dev fixture (1 user + 5 studies + author grants) into a freshly-owned `velocia` Postgres schema on first boot — zero SQL/Python steps. Set `SEED_ON_STARTUP=false` if you'd rather seed manually with `make seed-dev`.

```bash
make build                                       # populate frontend/dist (the SPA bundle the app serves)
make bundle-validate DBX_PROFILE=<your-profile>  # databricks bundle validate -t dev
make bundle-deploy   DBX_PROFILE=<your-profile>  # provisions Lakebase + app, deploys code, app self-seeds
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

`app.yaml` reads the runtime-injected `PGHOST` / `PGUSER` / `PGDATABASE`, assembles a credential-free `DATABASE_URL`, and execs uvicorn against `$DATABRICKS_APP_PORT`. `backend/db/session.py` mints a Lakebase OAuth token (via `WorkspaceClient.database.generate_database_credential`) for every new physical pool connection — a static `PGPASSWORD` is **not** injected by the runtime, by design.

### Schema lifecycle (zero-touch first deploy)

The app owns its own Postgres schema. `init_db()` runs `CREATE SCHEMA IF NOT EXISTS velocia AUTHORIZATION CURRENT_USER` before `Base.metadata.create_all`, which makes the app's service principal the schema owner. Result: every subsequent `CREATE TABLE` succeeds against the SP's own schema, and **no out-of-band `GRANT ... ON public TO <sp>` is ever needed** — the bundle's `CAN_CONNECT_AND_CREATE` resource permission gives the SP database-level CREATE, which is enough.

If `SEED_ON_STARTUP=true` (set by default in `app.yaml`), the lifespan also inserts the dev fixture (1 user + 5 studies + author grants) right after `init_db()`. The user row uses `SEED_USER_EMAIL` / `SEED_USER_NAME`, so the customer's first SSO login lands on a populated dashboard.

### Manual seeding (only when needed)

For ad-hoc reruns or when seed-on-startup is off, two paths:

- **`scripts/seed_dev.py`** mints a Lakebase OAuth token via the SDK, connects with `asyncpg`, and applies the same fixture. Auto-discovers the bound DB from `databricks apps get`. Run with `make seed-dev`.
- **`scripts/seed_dev.sql`** — a self-contained SQL fallback for when networking blocks the Python path (e.g. `semaphore timeout period has expired` on Windows). Paste into the workspace SQL editor; replace `<SEED_USER_EMAIL>`, `<SEED_USER_NAME>`, and `<APP_SP_CLIENT_ID>` placeholders before running.

### Day-2 ops

```bash
make app-status                                            # databricks apps get velocia-newop-sdc
make app-restart                                           # stop + start the app (picks up env / resource changes)
databricks bundle deploy -t dev --profile <your-profile>   # redeploy code only
databricks bundle destroy -t dev --profile <your-profile> -y   # full cleanup
```
