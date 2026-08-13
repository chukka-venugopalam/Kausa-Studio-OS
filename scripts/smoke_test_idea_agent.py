"""Runs IdeaAgent for real: real Supabase, real Gemini."""
from dotenv import load_dotenv
load_dotenv()

from lib.supabase_client import get_client
from agents.idea_agent import IdeaAgent

db = get_client()

existing = db.table("brands").select("*").eq("slug", "kausa-test").execute()
if existing.data:
    brand_id = existing.data[0]["id"]
else:
    brand = db.table("brands").insert({"name": "Kausa", "slug": "kausa-test"}).execute()
    brand_id = brand.data[0]["id"]
print("Using brand:", brand_id)

agent = IdeaAgent(brand_id=brand_id)
result = agent.run(series_name="Word Origin Chains")
print("Agent result:", result)