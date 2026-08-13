"""Fully automated: proposes new candidate chains from the backlog.
Nothing here enters canon -- proposing costs nothing, per the
automation-boundary rule in ARCHITECTURE.md Section 3. Every row this
agent inserts starts at verification_status = 'pending', same as
every other path into the chains table.
"""
import json
from pathlib import Path

from agents.base_agent import BaseAgent
from lib.ai_client import call_gemini

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "idea_generation_structured.md"


class IdeaAgent(BaseAgent):
    name = "idea_agent"

    def execute(self, series_name: str, series_id: str = None) -> dict:
        template = PROMPT_PATH.read_text()
        prompt = template.replace("{series}", series_name)
        raw = call_gemini(prompt)

        chains = self._parse_chains(raw)

        inserted = []
        for chain in chains:
            row = self.db.table("chains").insert({
                "brand_id": self.brand_id,
                "series_id": series_id,
                "hook_text": chain["hook_text"],
                "node_1": chain["node_1"],
                "node_2": chain["node_2"],
                "payoff": chain["payoff"],
                "sources": chain.get("sources", []),
            }).execute()
            inserted.append(row.data[0]["id"])

        return {"series_name": series_name, "inserted_chain_ids": inserted}

    @staticmethod
    def _parse_chains(raw: str) -> list:
        # Gemini sometimes wraps JSON in markdown fences despite
        # instructions not to -- strip before parsing rather than
        # letting a formatting quirk crash the whole run.
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned.strip())