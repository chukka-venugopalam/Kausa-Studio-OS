"""Connectivity check for Gemini -- same pattern as
smoke_test_supabase.py. Real network call, not part of pytest.
"""
from dotenv import load_dotenv
load_dotenv()

from lib.ai_client import call_gemini

response = call_gemini("Reply in one short sentence: are you working?")
print("Gemini says:", response)