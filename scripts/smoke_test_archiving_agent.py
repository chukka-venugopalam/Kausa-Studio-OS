"""Runs ArchivingAgent for real: real Supabase.
Uses the production seeded by smoke_test_script_agent.py -- run that
one first if this can't find a production to archive.
"""
from dotenv import load_dotenv
load_dotenv()

from lib.supabase_client import get_client
from agents.archiving_agent import ArchivingAgent

db = get_client()

existing_brand = db.table("brands").select("*").eq("slug", "kausa-test").execute()
brand_id = existing_brand.data[0]["id"]

productions = (
    db.table("productions")
    .select("*")
    .eq("brand_id", brand_id)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
)
if not productions.data:
    raise RuntimeError("No productions found -- run smoke_test_script_agent.py first.")
production_id = productions.data[0]["id"]
print("Archiving production:", production_id)

agent = ArchivingAgent(brand_id=brand_id, production_id=production_id)
result = agent.run(
    production_id=production_id,
    title="Why Stop Signs Are Red",
    youtube_url="https://youtube.com/watch?v=placeholder",
    instagram_url="https://instagram.com/reel/placeholder",
)
print("Agent result:", result)