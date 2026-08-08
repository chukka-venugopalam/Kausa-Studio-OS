# Workflow: Publish Pipeline

**Trigger:** a `productions` row reaches `status = 'edited'`.

**Steps:**
1. Send Message → final go/no-go confirmation to a human (cheap
   insurance against publishing the wrong file or wrong metadata --
   the one irreversible step in the whole pipeline).
2. On confirm → HTTP Request → YouTube Data API v3 (authenticated
   upload) with title/description built from the standard "A connects
   to B" template (Content Bible, Manual 2).
3. HTTP Request → Instagram Graph API publish, staggered 1-2 hours
   after the YouTube post (not simultaneous).
4. Postgres node → insert `episodes` row with both URLs.
5. Postgres update → `productions.status = 'published'`.
6. HTTP Request → trigger `archiving_agent` (writes final links back
   into the knowledge graph, updates `chain_links`).
7. Postgres update → `status = 'archived'`.

**Approval gate:** step 1, the final human confirmation. Everything
after that is fully automated -- the creative risk is already resolved
by this point.

**Error handling:** if either platform upload fails, do NOT retry
automatically (risk of double-publish) -- route to Error Workflow and
require manual re-trigger after checking what actually happened.
