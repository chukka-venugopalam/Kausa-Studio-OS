"""Verification is the one production step this whole system refuses
to fully automate, on purpose. The Universe Bible's first rule is
"nothing is invented" -- automating this check away would break the
show's own foundational rule, not just a style preference.

So this agent does the tedious part (drafting source candidates and a
confidence estimate) and stops there. It writes a draft back to the
chains row and leaves verification_status at 'pending'. A human
approves in the n8n gate before it ever flips to 'verified' -- see
n8n-workflows/specs/02-verification-gate.md.
"""
from pathlib import Path

from agents.base_agent import BaseAgent
from lib.ai_client import call_gemini

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "fact_verification.md"


class VerificationAgent(BaseAgent):
    name = "verification_agent"

    def execute(self, chain_id: str, claim: str) -> dict:
        template = PROMPT_PATH.read_text()
        prompt = template.replace("[CLAIM]", claim)
        draft = call_gemini(prompt)

        self.db.table("chains").update(
            {
                "sources": draft,  # parse into structured JSON in production
                "verification_status": "pending",
            }
        ).eq("id", chain_id).execute()

        return {"chain_id": chain_id, "draft_verification": draft}
