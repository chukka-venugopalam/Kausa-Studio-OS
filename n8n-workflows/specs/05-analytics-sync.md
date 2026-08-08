# Workflow: Analytics Sync

**Trigger:** Schedule node, daily, for every `episodes` row published
in the last 30 days (recent episodes move fast; older ones barely change).

**Steps:**
1. HTTP Request → YouTube Analytics API + Instagram Graph API insights,
   per episode.
2. HTTP Request → trigger `analytics_agent` job with the pulled metrics.
3. Postgres node → compare against Manual 7's thresholds (3-second
   retention, avg view duration, share rate, subscriber conversion).
4. IF any threshold breached → Send Message alert with the specific
   metric and episode -- not a generic "check your dashboard" ping.

**Approval gate:** none. Fully automated by design -- read-only, low-stakes,
exactly the kind of step that should never wait on a human.
