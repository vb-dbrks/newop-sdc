"""Push app source code from the bundle workspace path.

Cross-platform replacement for the previous bash | python | json
pipeline. Used by `make bundle-deploy` after `databricks bundle
deploy` uploads the files but doesn't auto-attach them to the app.

Discovers the deploying user's workspace email and runs:

    databricks --profile <p> apps deploy <app> \\
        --source-code-path /Workspace/Users/<email>/.bundle/<bundle>/<target>/files

Tracked upstream as databricks/cli#4181 — when bundle deploy auto-
attaches source_code_path, this whole script becomes obsolete.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def _databricks(profile: str, *args: str) -> str:
    return subprocess.check_output(
        ["databricks", "--profile", profile, *args], text=True
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile", required=True, help="Databricks CLI profile.")
    p.add_argument("--target", default="dev", help="Bundle target name.")
    p.add_argument(
        "--app",
        default="velocia-newop-sdc",
        help="Databricks Apps app name.",
    )
    p.add_argument(
        "--bundle-name",
        default="velocia-newop-sdc",
        help="Bundle name from databricks.yml (`bundle.name`).",
    )
    args = p.parse_args()

    me = json.loads(_databricks(args.profile, "current-user", "me", "-o", "json"))
    try:
        email = me["emails"][0]["value"]
    except (KeyError, IndexError) as e:
        print(
            f"Could not find an email on `current-user me` response: {me!r}",
            file=sys.stderr,
        )
        raise SystemExit(1) from e

    source_path = (
        f"/Workspace/Users/{email}/.bundle/{args.bundle_name}/{args.target}/files"
    )
    print(f">>> source-code-path: {source_path}")
    subprocess.check_call(
        [
            "databricks",
            "--profile",
            args.profile,
            "apps",
            "deploy",
            args.app,
            "--source-code-path",
            source_path,
        ]
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
