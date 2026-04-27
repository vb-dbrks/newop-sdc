"""Local stub of the Agent API. Run via `make fake-agent` (port 9000).

Mimics POST /agent/run and GET /agent/run/{id} to support offline development.
The fake progresses through canned step names with a fixed delay.
"""

import asyncio
import time
import uuid
from typing import Any

from fastapi import FastAPI

app = FastAPI(title="Fake Velocia Agent", version="0.0.1")

_RUNS: dict[str, dict[str, Any]] = {}
_TASKS: set[asyncio.Task[None]] = set()

STEP_SEQUENCE = [
    "analyzing_internal_assets",
    "cross_referencing_trials",
    "simulating_feasibility",
    "drafting_concepts",
]


@app.post("/agent/run")
async def start(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(uuid.uuid4())
    _RUNS[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "started_at": time.time(),
        "steps": [{"name": s, "status": "pending"} for s in STEP_SEQUENCE],
        "kind": payload.get("kind", "generate"),
    }
    task = asyncio.create_task(_advance(run_id))
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
    return {"run_id": run_id, "status": "queued"}


@app.get("/agent/run/{run_id}")
async def status(run_id: str) -> dict[str, Any]:
    return _RUNS.get(run_id, {"run_id": run_id, "status": "not_found"})


async def _advance(run_id: str, step_seconds: float = 1.5) -> None:
    run = _RUNS[run_id]
    await asyncio.sleep(step_seconds)
    run["status"] = "running"
    for i, _ in enumerate(STEP_SEQUENCE):
        run["steps"][i]["status"] = "running"
        await asyncio.sleep(step_seconds)
        run["steps"][i]["status"] = "succeeded"
    run["status"] = "succeeded"
    run["output"] = {
        "fields": [
            {"field_key": "study_title", "value_text": "Fake — generated study title"},
            {"field_key": "strategic_intent", "value_text": "Fake — generated intent."},
        ],
        "summary": "Fake agent output for local dev.",
        "warnings": [],
    }
