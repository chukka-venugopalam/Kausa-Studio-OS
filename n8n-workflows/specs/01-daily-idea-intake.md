# Workflow: Daily Idea Intake

**Trigger:** Schedule node, once daily (e.g., 06:00).

**Steps:**
1. HTTP Request → GitHub API: `workflow_dispatch` the `agent-daily-pipeline.yml`
   Action with `job=idea_agent` in the payload.
2. Wait node → poll (or better, wait for a webhook callback the Action
   posts to this workflow when it finishes writing candidate chains to
   Supabase).
3. Postgres/Supabase node → read newly-inserted `chains` rows where
   `verification_status = 'pending'` and `created_at` is today.
4. IF node → if zero new candidates, send a low-priority Discord/Slack
   note ("no new ideas today, backlog may need attention") and stop.
5. Otherwise → hand off to workflow 02.

**Approval gate:** none at this stage -- candidates aren't real until verified.

**Error handling:** any failed HTTP Request or Postgres node routes to
the shared Error Workflow (spec 99), not a dead end.
