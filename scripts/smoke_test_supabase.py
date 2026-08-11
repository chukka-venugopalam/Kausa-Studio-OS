"""One-time check that .env is read correctly and Supabase is
reachable. Not part of the automated test suite -- makes a real
network call, so it should never run in CI.
"""
from dotenv import load_dotenv
load_dotenv()  # reads .env into the environment -- must run before
                # anything imports lib.supabase_client, which expects
                # SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY to already
                # be set

from lib.supabase_client import get_client

db = get_client()

inserted = db.table("brands").insert({
    "name": "Kausa",
    "slug": "kausa-test",
}).execute()
print("Inserted:", inserted.data)

rows = db.table("brands").select("*").execute()
print("Read back:", rows.data)
