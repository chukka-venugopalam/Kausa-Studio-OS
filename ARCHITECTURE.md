# Kausa Studio OS — Technical Architecture

*Fifth in the set, and the first that's actual code: causeway-blueprint.md → kausa-redteam-teardown.md → kausa-operating-system.md → kausa-universe-bible.md → this repo. The scaffold lives alongside this document — see README.md for setup.*

---

## 1. Philosophy: boring technology, human gates where errors are expensive

The brief asked to optimize for free tools, maintainability, and reliability *over* complexity — so the design bias throughout is toward fewer moving parts, not more. Four tools, each doing exactly the thing it's best at, with no overlap:

| Tool | Job | Why not something else |
|---|---|---|
| **Supabase (Postgres)** | All durable state | One real database, not a database plus a separate cache plus a separate queue — less to keep consistent |
| **GitHub Actions** | Where Python agent code executes | Already in the stack (GitHub is a named requirement); free and unlimited on a public repo; every run is versioned, logged, and re-runnable by construction |
| **n8n (self-hosted)** | Orchestration, scheduling, human approval gates | Free forever self-hosted, with a visual workflow a non-engineer can actually audit — the approval gates need to be inspectable by a human, not just correct |
| **Python** | Agent logic too complex for n8n's built-in nodes | Testable, versionable, no vendor lock-in to n8n's own code-node limitations |

The one architectural decision everything else follows from: **GitHub Actions runs the code, n8n runs the clock and the approval gates.** n8n triggers a workflow run via the GitHub API, the Action does the work and writes results to Supabase, n8n reads the result and decides what happens next (including, sometimes, "wait for a human"). Neither tool tries to do the other's job.

---

## 2. Free-tool reality check

Checked directly rather than assumed, since the whole design leans on these numbers:

- **n8n self-hosted Community Edition is genuinely free forever** — unlimited workflows and executions, no license fee. It needs *somewhere* to run, though: a laptop that's on when scheduled workflows fire, or a small VPS (roughly $5-7/month) if you want it running while your laptop is closed. That's the one line item in this whole architecture that isn't strictly $0, and it's optional at the start.
- **GitHub Actions is free and unlimited on a public repo.** On a private repo, the free plan includes 2,000 minutes/month. This pipeline's realistic usage — short, lightweight jobs (an API call plus a database write, not heavy compute) at roughly daily cadence — lands well under that cap either way. Going public also costs nothing strategically: the teardown already established the moat isn't the workflow or the prompts, it's the time-denominated assets (the archive, the community). Building this in the open is arguably a feature, not a risk — it's the "transparency as differentiator" opportunity from the original strategy, applied to the tooling itself. Secrets stay encrypted in GitHub Secrets regardless of repo visibility either way.
- **Supabase's free tier is genuinely workable** for this scale (500MB database, 1GB file storage, 50,000 monthly active users, 500K edge function calls) — but has two real gotchas: free projects **auto-pause after 7 days with no API activity**, and there are **no automatic backups** on the free tier. Both are addressed by the same scheduled workflow (Section 6).
- **The Gemini API has a genuine, ongoing, no-credit-card free tier** suitable for low-volume production use — this pipeline's realistic load (roughly a dozen AI calls a day across all agents) is nowhere near the free tier's daily ceiling. This is the automated pipeline's model provider.
- **Neither Claude nor ChatGPT has an ongoing free API tier** as of 2026 — Claude's API gives a small one-time starter credit, then it's pay-as-you-go per token. That's why they're deliberately *not* in the automated pipeline. They remain your own tools for manual, judgment-heavy work (brainstorming, editing, review) via their free chat apps, exactly as in the original brief — just not the thing agents call programmatically.

All of these numbers have shifted more than once in the past year. Re-check the providers' own pricing pages before relying on exact figures months from now.

---

## 3. Agent roster and automation boundaries

The general rule, stated once so it doesn't need re-deriving per agent: **automate fully when an error is cheap and reversible. Keep a human gate when an error is expensive, hard to reverse, or touches trust. Every new agent starts semi-automated and only earns full automation after a track record** — a defined run of consecutive correct outputs with zero human overrides, not a launch-day default.

| Agent | What it does | Automation tier | Why |
|---|---|---|---|
| Idea Agent | Proposes candidate chains from the backlog/comment-mining | Fully automated to propose | Proposing costs nothing; nothing enters canon yet |
| **Verification Agent** | Drafts sources + confidence for a candidate chain | **Semi-automated, permanently** | The Universe Bible's first rule is "nothing is invented" — automating this away breaks the show's own foundational rule, not just a style preference |
| **Script Agent** | Drafts the episode script | **Semi-automated, can mature** | Starts human-reviewed; can graduate to auto-approve-if-linter-passes once the Content Bible's rules are codified as an actual check |
| Asset/Prompt Agent | Prepares the Veo 3 prompt block + shot list | Fully automated | Generates a *prompt*, not a final asset — low stakes either way |
| *(manual: asset generation)* | Actual Veo 3 / Canva / CapCut generation | **Permanently human** | None of these tools have reliable free APIs for full automation as of 2026 — this is an honest tool limitation, not a design choice |
| *(manual: editing)* | Assembly in CapCut | **Permanently human**, for now | Same reason |
| **Publishing Agent** | Uploads to YouTube/Instagram once a final file exists | Fully automated *after* one final human confirm | The creative risk is already resolved by this point; the confirm step is cheap insurance against the one genuinely irreversible action in the pipeline |
| Archiving Agent | Writes final links back into the knowledge graph | Fully automated | Low-stakes, easily corrected if wrong |
| Analytics Agent | Pulls and logs platform metrics | Fully automated | Read-only; a bad pull just gets overwritten tomorrow |
| Comment-Mining Agent | Scores viewer-submitted ideas | Semi-automated | Scoring is cheap to automate; letting spam/bad-faith submissions into the backlog unreviewed isn't |
| Experimentation Agent | Proposes and logs the week's single test variable | Semi-automated | Proposing is cheap; adopting a permanent change is a human call |

Five approval gates fall out of this table, not the other way around: **verification approval, script approval, final publish confirmation, experiment adoption, and agent promotion** (a human decides when an agent graduates from semi- to fully-automated).

---

## 4. Database schema

Full DDL in `supabase/schema.sql`. The one decision worth calling out: **every content table carries a `brand_id` from day one**, even though only one brand exists right now. That's the entire technical answer to "capable of running dozens in the future" — adding brand #2 later means inserting a row and populating its style-bible version, not migrating a schema under a live system. Retrofitting multi-tenancy onto a single-tenant schema after the fact is real, expensive work; building it in from the first migration costs nothing extra today.

Ten tables: `brands`, `series`, `chains` (the verified dataset — the actual sellable IP), `chain_links` (the knowledge graph edges), `productions` (the per-episode state machine — see Section 5), `episodes`, `analytics_snapshots`, `experiments`, `contributors`, and `agent_runs` (the audit log everything in Section 6 depends on).

---

## 5. Memory system

Three distinct kinds of "memory," deliberately not conflated into one mechanism:

- **Working memory** — the `productions.status` state machine (`idea → researching → verified → scripted → assets_ready → edited → published → archived`, or `failed`). Any workflow or agent can pick up an episode exactly where the last one left off by reading this one field, which is what makes the whole pipeline resumable rather than fragile.
- **Long-term memory** — the `chains` + `chain_links` tables. This *is* Lume's in-universe memory, made real: every new chain records which past chains it relates to, so callbacks are actually accurate rather than a character trait the show merely claims to have.
- **Agent memory** — deliberately *not* a persistent chat session. Every agent run is a fresh, stateless process (a GitHub Actions job), and context is reconstructed each time by pulling the relevant rows from Supabase into the prompt. This is a lightweight retrieval pattern, not a long-lived conversation — far more reliable and debuggable across scheduled, unattended runs than trying to keep a stateful session alive between them.

The style bible and prompt templates are the one thing that lives as **version-controlled files in the repo (`prompts/`)**, not database rows — git already gives free diff history, which is exactly the "version control" the Operating System's Asset Library called for, without inventing a second versioning system to keep in sync with the first.

---

## 6. Failure recovery

- **Every agent run writes `running` before doing anything, and `success` or `failed` after** (enforced once, in `BaseAgent`, not re-implemented per agent) — a crashed run always leaves an inspectable row in `agent_runs`, never a silent gap.
- **Idempotency is the actual retry mechanism.** Every agent checks current status before acting (e.g., the Publishing Agent checks "is this already published?" before calling the upload API) — this is what makes a retry *safe* instead of dangerous, such as a double-publish.
- **n8n's built-in Error Workflow** (spec 99) is the single place every other workflow's failures surface, rather than ten separate logs nobody checks.
- **A weekly orphan check** flags any `productions` row stuck in a non-terminal status for more than three days — this is what catches a silent stall, as distinct from a loud crash the Error Workflow already handles.
- **The keepalive-and-backup GitHub Action** (Section 2's two Supabase gotchas) runs every three days regardless of whether anything else fires that week, so the free-tier pause and the missing-backups problem are solved by infrastructure, not by remembering to think about them.

---

## 7. Scaling strategy: one brand to dozens

Nothing new needs to be built to add a second brand — that's the point of Section 4's schema decision. What actually changes per new brand:

1. A new `brands` row, with its own `style_bible_version`.
2. Its own `prompts/` overrides where the house style genuinely differs (most won't — the verification standard and the automation-boundary rules in Section 3 are brand-agnostic by design).
3. Its own n8n workflow instances (or the same six workflows, parameterized by `brand_id` — simpler to maintain, and the honest starting choice, since running six workflows twice with a filter is less to keep synchronized than duplicating and forking twelve).
4. Its own GitHub Actions secrets, if it needs separate platform accounts.

What does **not** change: the schema, the agent code, the failure-recovery mechanism, or the approval-gate philosophy. Multi-brand is a configuration exercise once the first brand's pipeline is real, not a rebuild — which is the actual test of whether "modular" was true or just claimed.

---

## 8. Implementation roadmap

- **Phase 0 (this week):** run `schema.sql`, set up Secrets, confirm `pytest tests/` passes locally with real credentials. No automation live yet — this is plumbing.
- **Phase 1 (weeks 1-2):** build n8n workflows 01 and 02 only (idea intake + verification gate). Run the rest of production (script, assets, edit, publish) by hand, logging into `productions` manually. The goal here is a working, observable state machine before any agent writes to it.
- **Phase 2 (weeks 3-4):** add the Script Agent and Publish Pipeline (workflows 03-04). Asset generation and editing stay manual — that's an honest, permanent tool limitation, not a phase to graduate out of.
- **Phase 3 (month 2):** add Analytics Sync and the Error Handler/orphan check. This is the point where the system starts being genuinely observable instead of just automated.
- **Phase 4 (month 3+):** revisit the trust-ladder for Script Agent approval — if 20+ consecutive scripts have needed zero edits, consider a linter-based auto-approve. Add Comment-Mining and Experimentation agents once there's enough real audience data for either to have something to work with.
- **Phase 5 (whenever brand #2 is real, not before):** execute Section 7. Building it earlier than this is premature generalization — a second brand's actual needs will reveal what the parameterization should look like better than guessing now would.

## File structure

```
kausa-studio-os/
├── README.md
├── ARCHITECTURE.md          (this file)
├── .env.example
├── .gitignore
├── requirements.txt
├── .github/workflows/
│   ├── agent-daily-pipeline.yml
│   ├── keepalive-and-backup.yml
│   └── ci-test.yml
├── supabase/
│   └── schema.sql
├── agents/
│   ├── base_agent.py
│   ├── verification_agent.py    (semi-automated example)
│   ├── script_agent.py          (semi-automated example)
│   └── analytics_agent.py       (fully-automated example)
├── lib/
│   ├── supabase_client.py
│   └── ai_client.py             (Gemini, with backoff)
├── prompts/
│   ├── idea_generation.md
│   ├── script_writing.md
│   └── fact_verification.md
├── n8n-workflows/specs/         (six workflow specs, not JSON — see Section 1's note)
└── tests/
    └── test_base_agent.py       (verified against a mocked DB — see README)
```
