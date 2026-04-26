"""HTTP client for the Agent API. Stateless: every call carries full context.

See ADR 0003 (async + poll) and ADR 0004 (stateless agent).
"""

from typing import Any

import httpx

from backend.settings import settings


class AgentClient:
    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or settings.agent_api_base).rstrip("/")
        self.token = token or settings.agent_api_token

    async def start_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base_url}/agent/run",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            r.raise_for_status()
            return r.json()

    async def get_run(self, run_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/agent/run/{run_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            r.raise_for_status()
            return r.json()
