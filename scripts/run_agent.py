"""Dispatcher for agent-daily-pipeline.yml. Reads which agent to run
and its arguments from environment variables set by the workflow,
imports the matching class from agents/, and calls .run(). A registry
dict, not a growing if/elif chain -- same pattern you'll see again
once there are more than two agents to dispatch.
"""
import os

from lib.supabase_client import get_client
from agents.verification_agent import VerificationAgent
from agents.idea_agent import IdeaAgent


def get_or_create_brand_id() -> str:
    db = get_client()
    existing = db.table("brands").select("*").eq("slug", "kausa-test").execute()
    if existing.data:
        return existing.data[0]["id"]
    created = db.table("brands").insert({"name": "Kausa", "slug": "kausa-test"}).execute()
    return created.data[0]["id"]


def run_verification_agent(brand_id: str):
    return VerificationAgent(brand_id=brand_id).run(
        chain_id=os.environ["CHAIN_ID"],
        claim=os.environ["CLAIM"],
    )


def run_idea_agent(brand_id: str):
    return IdeaAgent(brand_id=brand_id).run(
        series_name=os.environ["SERIES_NAME"],
    )


DISPATCH = {
    "verification_agent": run_verification_agent,
    "idea_agent": run_idea_agent,
}


def main():
    agent_name = os.environ["AGENT_NAME"]
    handler = DISPATCH.get(agent_name)
    if handler is None:
        raise ValueError(f"No dispatch logic for: {agent_name}")

    brand_id = get_or_create_brand_id()
    result = handler(brand_id)
    print("Agent result:", result)


if __name__ == "__main__":
    main()