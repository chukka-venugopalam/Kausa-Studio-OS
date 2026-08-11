"""Dispatcher for agent-daily-pipeline.yml. Reads which agent to run
and its arguments from environment variables set by the workflow,
imports the matching class from agents/, and calls .run(). Deliberately
thin -- all real logic stays in agents/, testable without a GitHub
Actions run.
"""
import os

from lib.supabase_client import get_client
from agents.verification_agent import VerificationAgent

AGENT_REGISTRY = {
    "verification_agent": VerificationAgent,
}


def get_or_create_brand_id() -> str:
    # Single-brand today -- per ARCHITECTURE.md Section 7, this becomes
    # a real lookup keyed by an input once brand #2 exists, not before.
    db = get_client()
    existing = db.table("brands").select("*").eq("slug", "kausa-test").execute()
    if existing.data:
        return existing.data[0]["id"]
    created = db.table("brands").insert({"name": "Kausa", "slug": "kausa-test"}).execute()
    return created.data[0]["id"]


def main():
    agent_name = os.environ["AGENT_NAME"]
    agent_cls = AGENT_REGISTRY.get(agent_name)
    if agent_cls is None:
        raise ValueError(f"Unknown agent: {agent_name}")

    brand_id = get_or_create_brand_id()

    if agent_name == "verification_agent":
        result = agent_cls(brand_id=brand_id).run(
            chain_id=os.environ["CHAIN_ID"],
            claim=os.environ["CLAIM"],
        )
    else:
        raise ValueError(f"No dispatch logic yet for: {agent_name}")

    print("Agent result:", result)


if __name__ == "__main__":
    main()