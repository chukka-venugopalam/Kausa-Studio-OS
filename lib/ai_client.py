"""Thin wrapper around the Gemini API for automated agent calls.

Uses the google-genai SDK (the old google-generativeai package is
fully deprecated -- no more updates or bug fixes, per Google's own
README). Model name is overridable via GEMINI_MODEL since we just
watched a hardcoded model string 404 on a brand-new API key -- this
is the fix so the next model retirement is a one-line .env edit,
not a code change.

Free-tier numbers and model availability have shifted more than once
in 2026. Verify current limits before relying on this in production:
https://ai.google.dev/gemini-api/docs/rate-limits
"""
import os
import time
from google import genai

MAX_RETRIES = 5
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")


def call_gemini(prompt: str, model: str = DEFAULT_MODEL) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError("unreachable")