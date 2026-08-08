# Workflow: Script and Asset Prep

**Trigger:** a `chains` row flips to `verification_status = 'verified'`
(Supabase Realtime, or a polling Schedule node if Realtime isn't wired up).

**Steps:**
1. Postgres node → insert a new `productions` row, `status = 'idea'`.
2. HTTP Request → trigger `script_agent` job for that production.
3. Send Message → post the draft script for human review (same
   approve/reject pattern as workflow 02, lighter touch).
4. On approval → Postgres update `status = 'scripted'`.
5. HTTP Request → trigger the asset-prompt step (Veo 3 character-
   consistency block + shot list) -- this one drafts a *prompt*, not a
   final asset, so it's lower-stakes and can auto-advance.
6. Send Message → notify that assets are ready to generate by hand in
   Veo 3 / Canva / CapCut (these tools don't have reliable free APIs
   for full automation as of 2026 -- see ARCHITECTURE.md). This is a
   deliberate human handoff, not a gap in the automation.
7. Manual step (outside n8n): generate, edit, export the final video file
   to a watched folder (Google Drive / local folder n8n can poll).
8. File-trigger node → detects the final export → Postgres update
   `status = 'edited'` → hands off to workflow 04.

**Approval gate:** script approval (step 3). Note in ARCHITECTURE.md's
trust-ladder: this can graduate to auto-approve-if-linter-passes later.
