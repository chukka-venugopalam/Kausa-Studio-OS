"""Runs VerificationAgent for real: real Supabase, real Gemini.
Agents operate on existing data, never invent their own subject
matter -- so this seeds one brand and one chain first.
"""
from dotenv import load_dotenv
load_dotenv()

from lib.supabase_client import get_client
from agents.verification_agent import VerificationAgent

db = get_client()

existing = db.table("brands").select("*").eq("slug", "kausa-test").execute()
if existing.data:
    brand_id = existing.data[0]["id"]
else:
    brand = db.table("brands").insert({"name": "Kausa", "slug": "kausa-test"}).execute()
    brand_id = brand.data[0]["id"]
print("Using brand:", brand_id)

chain = db.table("chains").insert({
    "brand_id": brand_id,
    "hook_text": "Why stop signs are red",
    "node_1": "red is chosen for maximum visual contrast and urgency",
    "node_2": "a 1968 UN road-signs treaty standardized it internationally",
    "payoff": "that treaty is why almost every country's stop sign matches",
}).execute()
chain_id = chain.data[0]["id"]
print("Seeded chain:", chain_id)

agent = VerificationAgent(brand_id=brand_id)
result = agent.run(
    chain_id=chain_id,
    claim="Stop signs are red because of an international road-sign treaty.",
)
print("Agent result:", result)