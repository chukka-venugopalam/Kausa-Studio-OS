"""Thin wrapper around the Gemini API for automated agent calls.

Automated agents call Gemini specifically, not Claude or ChatGPT.
As of 2026, neither Claude nor ChatGPT offers an ongoing free API tier
(Claude's API gives a small one-time starter credit, then it's pure
pay-as-you-go) -- while Google AI Studio's Gemini API has a genuine,
ongoing, no-credit-card free tier that's a real fit for a low-volume
pipeline like this one (roughly a dozen calls a day, nowhere near the
free tier's daily request ceiling).

Claude and ChatGPT remain the human's own tools for manual, judgment-
heavy work via their free chat apps -- brainstorming, editing, review.
They are deliberately NOT part of the automated pipeline.

Free-tier numbers here have shifted more than once in the past year.
Verify current limits before relying on this in production:
https://ai.google.dev/gemini-api/docs/rate-limits
"""
import os
import time
import google.generativeai as genai

MAX_RETRIES = 5
DEFAULT_MODEL = "gemini-2.5-flash"  # the free-tier workhorse; re-check
                                     # current model names periodically


def call_gemini(prompt: str, model: str = DEFAULT_MODEL) -> str:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    client = genai.GenerativeModel(model)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.generate_content(prompt)
            return response.text
        except Exception:
            # Narrow this to the SDK's specific rate-limit exception in
            # production rather than a bare except -- left broad here
            # so the retry pattern is visible without extra imports.
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s, 8s, 16s

    raise RuntimeError("unreachable")
