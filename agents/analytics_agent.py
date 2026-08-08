"""Fully automated from day one, on purpose: this step is read-only
and low-stakes. A bad pull just gets overwritten by tomorrow's
scheduled run. This is exactly the kind of step the automation-boundary
rule in ARCHITECTURE.md says to automate immediately -- cheap and
reversible to get wrong, unlike verification or publishing.
"""
from agents.base_agent import BaseAgent


class AnalyticsAgent(BaseAgent):
    name = "analytics_agent"

    def execute(self, episode_id: str, platform_metrics: dict) -> dict:
        self.db.table("analytics_snapshots").insert(
            {
                "episode_id": episode_id,
                "platform": platform_metrics["platform"],
                "ctr": platform_metrics.get("ctr"),
                "retention_3s": platform_metrics.get("retention_3s"),
                "avg_view_duration_pct": platform_metrics.get("avg_view_duration_pct"),
                "shares": platform_metrics.get("shares"),
                "saves": platform_metrics.get("saves"),
                "comments": platform_metrics.get("comments"),
                "subscriber_delta": platform_metrics.get("subscriber_delta"),
            }
        ).execute()
        return {"episode_id": episode_id, "logged": True}
