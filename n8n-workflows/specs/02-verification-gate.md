# Workflow: Verification Gate (human-in-the-loop, by design)

**Trigger:** called from workflow 01 for each new candidate chain.

**Steps:**
1. HTTP Request → trigger the `verification_agent` job (same GitHub
   Action, different `job` input).
2. Postgres node → read back the chain's draft `sources` field.
3. Send Message node (Discord/Telegram/email) → post the claim, the
   agent's draft sources, and two buttons/replies: Approve / Reject.
4. **Wait for Webhook node** -- this is the actual approval gate. n8n
   pauses here until a human clicks Approve or Reject (via a simple
   webhook the message's buttons call, or a reply n8n parses).
5. IF Approved → Postgres update: `verification_status = 'verified'`,
   `verified_at = now()`, `verified_by = <approver>`.
   IF Rejected → `verification_status = 'rejected'`, chain goes back to
   the idea backlog for a rewrite, not the trash.

**Approval gate:** this whole workflow *is* the gate. Per the Universe
Bible's first rule ("nothing is invented"), this step is never fully
automated, regardless of how good the agent's draft sourcing gets.

**Error handling:** if the Wait-for-Webhook node times out (default:
flag after 48 hours with no response) rather than blocking forever.
