"""Defensive backend poller for agent runs.

The frontend is the primary path for advancing agent_runs. This worker drains any
runs that are still queued/running so they reach a terminal state even if no client
is polling. Runs as an asyncio task scheduled at app startup.
"""


async def run_once() -> None:
    raise NotImplementedError(
        "TODO: SELECT agent_runs WHERE status IN (queued, running); call AgentClient.get_run; "
        "apply terminal-state side effects (materialise fields on success, mark failed otherwise)."
    )
