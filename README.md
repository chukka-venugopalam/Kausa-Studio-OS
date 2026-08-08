# Kausa Studio OS

The production platform behind Kausa — designed to run one media brand
today and, per the schema's `brand_id` design, more than one later
without a rebuild.

Read **ARCHITECTURE.md** first. This README is just setup.

## Stack

- **Supabase** (Postgres) — all durable state: the verified-chains
  dataset, the per-episode production state machine, analytics.
- **GitHub Actions** — where agent Python code actually executes.
  Free and unlimited on a public repo; 2,000 free minutes/month on
  private (comfortably enough for this workload — see ARCHITECTURE.md).
- **n8n** (self-hosted Community Edition — free forever, no execution
  cap) — orchestration, scheduling, and every human-approval gate.
- **Python** — agent logic, in `agents/`.
- **Gemini API** — the free, ongoing-tier model automated agents call.
  Claude and ChatGPT stay as your own manual tools via their free chat
  apps; neither has an ongoing free *API* tier as of 2026, so neither
  is part of the automated pipeline.

## Setup

1. Create a Supabase project, run `supabase/schema.sql` in the SQL editor.
2. Copy `.env.example` to `.env`, fill in real values.
3. Add the same values as GitHub Secrets (Settings → Secrets → Actions)
   so `.github/workflows/*.yml` can use them.
4. Self-host n8n (Docker: `docker run -it --rm -p 5678:5678 n8nio/n8n`
   locally to start, or on a small VPS for anything scheduled to run
   while your laptop is closed). Build the six workflows from
   `n8n-workflows/specs/` in the editor.
5. `pip install -r requirements.txt`, then `pytest tests/` to confirm
   the agent logic works before wiring up real credentials.

## What's scaffolded vs. what you extend

Fully worked, as a pattern to copy: `verification_agent.py` (semi-
automated), `script_agent.py` (semi-automated), `analytics_agent.py`
(fully automated) — one example of each automation tier. The other
seven agents in ARCHITECTURE.md's roster follow the same `BaseAgent`
shape. Same for prompts: three are here in full; the other five exist
already, worked out, in `kausa-operating-system.md` Manual 5 — port
them into `prompts/` the same way.

## A note on the sandbox this was built in

Every file here compiles and the core `BaseAgent` retry-safety logic
is verified against a mocked database (see `tests/test_base_agent.py`).
The sandbox that built this has no network access, so the real
`supabase` and `google-generativeai` packages couldn't actually be
installed and run end-to-end here — `pip install -r requirements.txt`
and a real `pytest` run in your own environment is the next step, not
optional polish.
