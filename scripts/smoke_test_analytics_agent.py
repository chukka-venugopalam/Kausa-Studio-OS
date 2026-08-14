"""Runs AnalyticsAgent for real: real Supabase.
Uses the episode created by smoke_test_archiving_agent.py -- run
that one first.
"""
from dotenv import load_dotenv
load_dotenv()

from lib.supabase_client import get_client
from agents.analytics_agent import AnalyticsAgent

db = get_client()

existing_brand = db.table("brands").select("*").eq("slug", "kausa-test").execute()
brand_id = existing_brand.data[0]["id"]

episodes = db.table("episodes").select("*").order("published_at", desc=True).limit(1).execute()
if not episodes.data:
    raise RuntimeError("No episodes found -- run smoke_test_archiving_agent.py first.")
episode_id = episodes.data[0]["id"]
print("Logging analytics for episode:", episode_id)

agent = AnalyticsAgent(brand_id=brand_id)
result = agent.run(
    episode_id=episode_id,
    platform_metrics={
        "platform": "youtube",
        "ctr": 4.2,
        "retention_3s": 61.0,
        "avg_view_duration_pct": 58.0,
        "shares": 12,
        "saves": 30,
        "comments": 5,
        "subscriber_delta": 3,
    },
)
print("Agent result:", result)