"""Runs ScriptAgent for real: real Supabase, real Gemini.
Seeds one productions row first -- ScriptAgent updates an existing
row rather than creating one, matching the real pipeline where
Idea/Verification happen before a production exists.
"""
from dotenv import load_dotenv
load_dotenv()

from lib.supabase_client import get_client
from agents.script_agent import ScriptAgent

db = get_client()

existing_brand = db.table("brands").select("*").eq("slug", "kausa-test").execute()
brand_id = existing_brand.data[0]["id"]

# Reuse the stop-signs chain from Step 5.
chain_id = "6cb96d1a-3ac2-4c3b-9b5f-c30b57eee788"
chain = db.table("chains").select("*").eq("id", chain_id).execute().data[0]

# Find the next free episode number for season 1 -- safe to rerun,
# unlike hardcoding episode_number=1 against a unique constraint.
existing_productions = (
    db.table("productions")
    .select("episode_number")
    .eq("brand_id", brand_id)
    .eq("season_number", 1)
    .order("episode_number", desc=True)
    .limit(1)
    .execute()
)
next_episode = (existing_productions.data[0]["episode_number"] + 1) if existing_productions.data else 1

production = db.table("productions").insert({
    "brand_id": brand_id,
    "chain_id": chain_id,
    "season_number": 1,
    "episode_number": next_episode,
}).execute()
production_id = production.data[0]["id"]
print("Seeded production:", production_id, "episode", next_episode)

chain_summary = (
    f"Hook: {chain['hook_text']}\n"
    f"Node 1: {chain['node_1']}\n"
    f"Node 2: {chain['node_2']}\n"
    f"Payoff: {chain['payoff']}"
)

agent = ScriptAgent(brand_id=brand_id, production_id=production_id)
result = agent.run(production_id=production_id, chain_summary=chain_summary)
print("Agent result:", result)