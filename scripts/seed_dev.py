"""Idempotent dev-data seeder for the Velocia app's Lakebase Postgres.

Inserts:
  - 1 user row (defaults to dev.user@example.com — override via env vars
    SEED_USER_EMAIL / SEED_USER_NAME).
  - 5 study_documents covering the New Opportunity / SDC mix.
  - 5 study_access_list rows granting that user the 'author' role on each doc.

Re-runnable: every INSERT uses ON CONFLICT DO NOTHING.

Authentication
--------------
Uses the Databricks SDK to mint a Lakebase OAuth token, which is the password
for the role named after the user's client_id / email. The same flow Databricks
Apps use server-side. Locally, you must point the SDK at the right workspace
(env var DATABRICKS_CONFIG_PROFILE=<your-profile> works).

Connection details
------------------
The script tries (in order):

  1. PGHOST / PGPORT / PGDATABASE / PGUSER from env (matches what the app sees
     when running inside Databricks Apps).
  2. CLI flags --host / --database / --user.
  3. `databricks apps get <app-name>` lookup of the bound 'database' resource
     to discover host + database + user automatically.

Usage
-----
    # easiest — let the script discover the deployed app's bound DB
    SEED_USER_EMAIL=you@yourcompany.com SEED_USER_NAME="Your Name" \\
        python scripts/seed_dev.py --profile <your-profile> --app velocia-newop-sdc

    # explicit
    PGHOST=... PGDATABASE=velocia PGUSER=you@yourcompany.com \\
        python scripts/seed_dev.py --profile <your-profile>

The Makefile wraps this as `make seed-dev`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import uuid
from typing import Any

import asyncpg  # type: ignore[import-not-found]


SEED_USER_EMAIL = os.environ.get("SEED_USER_EMAIL", "dev.user@example.com")
SEED_USER_NAME = os.environ.get("SEED_USER_NAME", "Dev User")

# (study_brief_title, study_acronym, study_id, document_type, study_status)
SEED_STUDIES: list[tuple[str, str, str, str, str]] = [
    (
        "Tocavalumab in Moderate-to-Severe COPD with Frequent Exacerbations",
        "TOCA-COPD",
        "D9999C00001",
        "new_opportunity",
        "draft",
    ),
    (
        "Tezepelumab Adolescent Airway Remodeling Substudy",
        "TEZ-AAR",
        "D9999C00002",
        "new_opportunity",
        "draft",
    ),
    (
        "Endometriosis Symptom Profiler — Real-World Evidence Cohort",
        "ENDO-PROFILE",
        "D9999C00003",
        "new_opportunity",
        "draft",
    ),
    (
        "Saxenda Cardiometabolic Phase IIb",
        "SAX-CARD-2B",
        "D9999C00004",
        "sdc",
        "in_review",
    ),
    (
        "Imfinzi NSCLC Adjuvant Phase III",
        "IMF-ADJ-3",
        "D9999C00005",
        "sdc",
        "approved",
    ),
]


def _stable_uuid(seed: str) -> str:
    """Deterministic UUID5 so reruns stay idempotent across invocations."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"velocia-seed:{seed}"))


def _get_oauth_token(profile: str | None, instance_name: str) -> tuple[str, str, str]:
    """Return (lakebase_token, default_user, host_hint).

    Lakebase requires an *instance-scoped* OAuth credential, not a generic
    workspace API token — minted via `database.generate_database_credential`.
    """
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        sys.exit(
            "databricks-sdk is not installed. Install with `pip install -e .` "
            "from the repo root, or `pip install databricks-sdk`."
        )

    if profile:
        os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", profile)

    w = WorkspaceClient()
    cred = w.database.generate_database_credential(instance_names=[instance_name])
    token = getattr(cred, "token", None)
    if not token:
        sys.exit(
            "Could not mint a Lakebase credential for instance "
            f"{instance_name}. Ensure the CLI profile is valid "
            "(`databricks auth profiles`) and the instance exists."
        )
    # Postgres role for U2M is the user's full email (also the SCIM userName).
    # `w.config.username` is None under PAT auth, so use current_user.me().
    try:
        me = w.current_user.me()
        user = (me.user_name or "").strip() or SEED_USER_EMAIL
    except Exception:
        user = (w.config.username or "").strip() or SEED_USER_EMAIL
    host = (w.config.host or "").rstrip("/")
    return token, user, host


def _discover_app_db(app_name: str, profile: str | None) -> dict[str, str]:
    """Run `databricks apps get <name>` and pull the bound database details + SP id."""
    cmd = ["databricks", "apps", "get", app_name]
    if profile:
        cmd += ["--profile", profile]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sys.exit(f"`databricks apps get {app_name}` failed:\n{e.stderr}")

    data = json.loads(out)
    sp_client_id = data.get("service_principal_client_id", "") or ""
    # Walk the active deployment's resources to find one of kind 'database'.
    deployment = data.get("active_deployment") or data.get("pending_deployment") or {}
    spec = (deployment.get("deployment_artifacts") or {}).get("source_code_path", "")
    # The full app object also has the resources list under app_status / resources
    # in newer schemas; fall back to scanning the whole blob for instance_name + database_name.
    resources = data.get("resources") or []
    for r in resources:
        db = r.get("database")
        if db:
            return {
                "instance_name": db.get("instance_name", ""),
                "database_name": db.get("database_name", ""),
                "sp_client_id": sp_client_id,
            }
    # Newer CLIs nest under config:
    cfg_resources = (data.get("default_source_code_path") and []) or []
    if cfg_resources:
        for r in cfg_resources:
            db = r.get("database")
            if db:
                return {
                    "instance_name": db.get("instance_name", ""),
                    "database_name": db.get("database_name", ""),
                }
    sys.exit(
        f"Could not find a bound 'database' resource on app {app_name}. "
        f"Available top-level keys in app object: {list(data)}"
    )


def _resolve_pg_host(instance_name: str, profile: str | None) -> str:
    """Look up the read_write_dns for a Lakebase instance."""
    cmd = ["databricks", "database", "get-database-instance", instance_name]
    if profile:
        cmd += ["--profile", profile]
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
    inst = json.loads(out)
    dns = inst.get("read_write_dns")
    if not dns:
        sys.exit(f"Lakebase instance {instance_name} has no read_write_dns yet.")
    return dns


async def _ensure_schema(conn: asyncpg.Connection, app_sp_client_id: str | None) -> None:
    """Ensure the velocia schema exists and the app SP can use it.

    With seed-on-startup (SEED_ON_STARTUP=true in app.yaml) the app's SP
    creates and owns the velocia schema itself, and this CLI script is
    just a fallback. We still create the schema (no-op if already there)
    and grant access to the SP — covers the case where the human runs
    this BEFORE the app has had a chance to boot.
    """
    await conn.execute(
        'CREATE SCHEMA IF NOT EXISTS velocia AUTHORIZATION CURRENT_USER'
    )
    await conn.execute("SET search_path TO velocia")

    if not app_sp_client_id:
        return
    print(f"Granting CREATE/USAGE on schema velocia to SP {app_sp_client_id}...")
    await conn.execute(f'GRANT CREATE, USAGE ON SCHEMA velocia TO "{app_sp_client_id}"')
    await conn.execute(
        f'GRANT ALL ON ALL TABLES IN SCHEMA velocia TO "{app_sp_client_id}"'
    )
    await conn.execute(
        f'GRANT ALL ON ALL SEQUENCES IN SCHEMA velocia TO "{app_sp_client_id}"'
    )
    # Default privileges on future objects too.
    await conn.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA velocia '
        f'GRANT ALL ON TABLES TO "{app_sp_client_id}"'
    )
    await conn.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA velocia '
        f'GRANT ALL ON SEQUENCES TO "{app_sp_client_id}"'
    )


async def _seed(conn: asyncpg.Connection) -> dict[str, int]:
    counts = {"users": 0, "study_documents": 0, "study_access_list": 0}

    user_id = _stable_uuid(SEED_USER_EMAIL)
    # Upsert: insert-or-refresh-display-name. The app's lifespan/login path
    # creates user rows with `name = email` if the SSO header doesn't carry a
    # preferred display name; we replace that with a friendly name on every
    # seed run.
    res = await conn.execute(
        """
        INSERT INTO users (user_id, sso_subject, email, name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (sso_subject) DO UPDATE SET name = EXCLUDED.name
        """,
        user_id,
        SEED_USER_EMAIL,
        SEED_USER_EMAIL,
        SEED_USER_NAME,
    )
    counts["users"] = 1 if res.endswith("1") else 0

    # If the row already existed, fetch its existing user_id so we grant access
    # against the right primary key.
    row = await conn.fetchrow(
        "SELECT user_id FROM users WHERE sso_subject = $1", SEED_USER_EMAIL
    )
    if row:
        user_id = row["user_id"]

    for title, acronym, study_id, doc_type, status in SEED_STUDIES:
        sd_id = _stable_uuid(study_id)
        res = await conn.execute(
            """
            INSERT INTO study_documents (
                study_document_id, document_type, study_brief_title,
                study_acronym, study_id, study_status, last_modified_by, current_version
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 1)
            ON CONFLICT (study_document_id) DO NOTHING
            """,
            sd_id,
            doc_type,
            title,
            acronym,
            study_id,
            status,
            user_id,
        )
        if res.endswith("1"):
            counts["study_documents"] += 1

        res = await conn.execute(
            """
            INSERT INTO study_access_list (
                study_document_id, user_id, role, granted_by, is_active
            )
            VALUES ($1, $2, 'author', $3, TRUE)
            ON CONFLICT (study_document_id, user_id, role) DO NOTHING
            """,
            sd_id,
            user_id,
            user_id,
        )
        if res.endswith("1"):
            counts["study_access_list"] += 1

    return counts


async def _run(args: argparse.Namespace) -> None:
    pghost = os.environ.get("PGHOST") or args.host
    pgport = int(os.environ.get("PGPORT") or args.port or 5432)
    pgdatabase = os.environ.get("PGDATABASE") or args.database
    pguser_override = os.environ.get("PGUSER") or args.user

    # We need to know the Lakebase *instance name* to mint a credential.
    # Order of resolution: explicit --instance flag → app discovery → fail.
    instance_name = args.instance
    sp_client_id: str | None = None
    if not instance_name:
        if not args.app:
            sys.exit(
                "Need either --instance <lakebase-instance-name> or --app "
                "<app-name> so the script can mint a Lakebase OAuth token."
            )
        binding = _discover_app_db(args.app, args.profile)
        instance_name = binding["instance_name"]
        sp_client_id = binding.get("sp_client_id") or None
        if not pghost:
            pghost = _resolve_pg_host(instance_name, args.profile)
        if not pgdatabase:
            pgdatabase = binding["database_name"]
    elif args.app:
        # Even with an explicit --instance, still try to discover the SP for
        # the GRANT step.
        try:
            binding = _discover_app_db(args.app, args.profile)
            sp_client_id = binding.get("sp_client_id") or None
        except SystemExit:
            sp_client_id = None

    token, default_user, _ = _get_oauth_token(args.profile, instance_name)
    pguser = pguser_override or default_user

    print(
        f"Connecting to {pghost}:{pgport}/{pgdatabase} as {pguser} "
        f"(SSL required, OAuth token from SDK)"
    )

    conn: asyncpg.Connection = await asyncpg.connect(
        host=pghost,
        port=pgport,
        database=pgdatabase,
        user=pguser,
        password=token,
        ssl="require",
    )
    try:
        # Idempotent: ensure velocia schema exists + SP has access.
        await _ensure_schema(conn, sp_client_id)

        # Wait for the schema the app's lifespan creates. If the app hasn't
        # booted at least once yet, fail loudly so the human knows to start it.
        tables = {
            r["tablename"]
            for r in await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'velocia'"
            )
        }
        missing = {"users", "study_documents", "study_access_list"} - tables
        if missing:
            sys.exit(
                f"Schema 'velocia' not yet populated in {pgdatabase}: "
                f"missing {missing}. Hit the app once (e.g. /healthz) so its "
                f"lifespan() runs init_db(), or enable SEED_ON_STARTUP=true in "
                f"app.yaml so the app does this end-to-end on boot."
            )

        counts = await _seed(conn)
    finally:
        await conn.close()

    print(json.dumps({"inserted": counts}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=os.environ.get("DATABRICKS_CONFIG_PROFILE"))
    parser.add_argument("--app", default="velocia-newop-sdc",
                        help="App name to auto-discover the bound DB from.")
    parser.add_argument("--instance", default=os.environ.get("DATABRICKS_DATABASE_INSTANCE_NAME"),
                        help="Lakebase instance name (else auto-discovered from --app).")
    parser.add_argument("--host", help="PGHOST override (else env PGHOST else app discovery).")
    parser.add_argument("--port", type=int)
    parser.add_argument("--database", help="PGDATABASE override.")
    parser.add_argument("--user", help="PGUSER override (defaults to SDK's username).")
    args = parser.parse_args()

    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
