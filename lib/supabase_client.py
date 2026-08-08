"""Thin wrapper around the Supabase Python client.

Reads credentials from environment variables so the same code runs
identically in GitHub Actions, locally, or anywhere else -- never
hardcode a URL or key here or anywhere else in this repo.
"""
import os
from supabase import create_client, Client


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)
