"""Semi-automated: drafts the script, but a human reviews it before a
production's status advances to 'scripted'. As trust builds, this gate
can relax to "auto-approve if it passes the Content Bible linter" --
see the trust-ladder note in ARCHITECTURE.md. It should never start
there, only earn its way there.
"""
from pathlib import Path

from agents.base_agent import BaseAgent
from lib.ai_client import call_gemini

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "script_writing.md"


class ScriptAgent(BaseAgent):
    name = "script_agent"

    def execute(self, production_id: str, chain_summary: str) -> dict:
        template = PROMPT_PATH.read_text()
        prompt = template.replace("[PASTE CHAIN + SOURCES]", chain_summary)
        script = call_gemini(prompt)

        self.db.table("productions").update(
            {
                "script_text": script,
                # deliberately NOT "scripted" yet -- stays short of that
                # status until a human approves the draft
                "status": "researching",
            }
        ).eq("id", production_id).execute()

        return {"production_id": production_id, "draft_script": script}
