"""Fully automated: files a published episode's final links into the
episodes table and updates the knowledge graph. Low-stakes -- a bad
archive entry is easy to correct, unlike a bad verification or a bad
publish, which is why this stays fully automated per ARCHITECTURE.md
Section 3.
"""
from datetime import datetime, timezone

from agents.base_agent import BaseAgent


class ArchivingAgent(BaseAgent):
    name = "archiving_agent"

    def execute(
        self,
        production_id: str,
        title: str,
        youtube_url: str = None,
        instagram_url: str = None,
        related_chain_ids: list = None,
    ) -> dict:
        production = (
            self.db.table("productions")
            .select("*")
            .eq("id", production_id)
            .execute()
            .data[0]
        )

        episode = self.db.table("episodes").insert({
            "production_id": production_id,
            "title": title,
            "youtube_url": youtube_url,
            "instagram_url": instagram_url,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        episode_id = episode.data[0]["id"]

        self.db.table("productions").update(
            {"status": "archived"}
        ).eq("id", production_id).execute()

        links_created = []
        chain_id = production.get("chain_id")
        for related_id in (related_chain_ids or []):
            if chain_id and related_id != chain_id:
                link = self.db.table("chain_links").insert({
                    "chain_id": chain_id,
                    "related_chain_id": related_id,
                    "link_type": "related",
                }).execute()
                links_created.append(link.data[0]["id"])

        return {
            "episode_id": episode_id,
            "production_status": "archived",
            "links_created": links_created,
        }