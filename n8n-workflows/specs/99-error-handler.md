# Workflow: Error Handler

Set as the **Error Workflow** in n8n's instance settings so every other
workflow calls this automatically on failure -- one place all failures
surface, instead of ten separate workflow logs nobody checks daily.

**Trigger:** n8n's built-in Error Trigger node.

**Steps:**
1. Extract the failing workflow name, node, and error message from the
   trigger's input data.
2. Send Message → a single alert channel (Discord/Telegram/email) with
   all three.
3. Postgres node → log to `agent_runs` if the failure maps to a known
   agent run (cross-reference by `github_run_id` if present), so the
   audit trail stays in one place even for n8n-side failures, not just
   Python-side ones.

**Also handles:** the weekly "orphan check" -- a separate Schedule
node (in this same workflow, or its own) that queries `productions`
for any row stuck in a non-terminal status for more than 3 days, and
alerts on those too. This is what catches a silent stall, as opposed
to a loud crash.
