"""Every agent inherits from BaseAgent. It enforces the one rule that
makes retries safe across a stateless, scheduled pipeline: write a
'running' row before doing anything, write 'success' or 'failed'
after -- so a crashed run always leaves a clear, inspectable trace in
agent_runs instead of a silent gap. This is the whole failure-recovery
mechanism at the code level; see ARCHITECTURE.md for the rest of it.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from lib.supabase_client import get_client


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, brand_id: str, production_id: Optional[str] = None):
        self.brand_id = brand_id
        self.production_id = production_id
        self.db = get_client()
        self.run_id: Optional[str] = None

    def run(self, *args, **kwargs):
        self.run_id = self._start_run()
        try:
            result = self.execute(*args, **kwargs)
            self._finish_run("success")
            return result
        except Exception as exc:
            self._finish_run("failed", error=str(exc))
            raise

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Subclasses implement the actual agent logic here."""
        raise NotImplementedError

    def _start_run(self) -> str:
        row = (
            self.db.table("agent_runs")
            .insert(
                {
                    "brand_id": self.brand_id,
                    "agent_name": self.name,
                    "production_id": self.production_id,
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        return row.data[0]["id"]

    def _finish_run(self, status: str, error: Optional[str] = None):
        self.db.table("agent_runs").update(
            {
                "status": status,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error_message": error,
            }
        ).eq("id", self.run_id).execute()
