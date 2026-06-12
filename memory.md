# memory.md — Lark · Prospect Intelligence Agent

> This file is written and maintained by Lark, not by humans.
> Detailed prospect findings live in profiles/ — not here.
> This file tracks operational state only: last run, open threads, decisions.
> Cap: 40 lines. Prune before adding. Archive entries older than 30 days.

---

## Last run
Date: —
Cohort swept: — contacts · Phase: 1 (test cohort)
Signals processed: — · High: — · Medium: — · Contextual: — · Discarded: —
Score-3 contacts: —
HubSpot write-back: — (MCP key pending)
Report generated: —
Status: — · No sweeps run yet

---

## Open threads
- [ ] HubSpot MCP key — obtain and configure before first sweep
- [ ] Confirm HubSpot custom properties created (see hubspot-properties.md)
- [ ] Build test cohort — export 100–500 contacts from HubSpot
      Criteria: orgs with AUM $1M+ preferred · recent 990 activity
- [ ] Confirm ProPublica API access — test a single org lookup before sweep
- [ ] Confirm Google Drive 990 folder path for MCP access
- [ ] Supervisor decision: confirm which HubSpot contact statuses to sweep
      (cold only, or cold + warming?)
- [ ] Confirm minimum AUM threshold for test cohort contacts

---

## Decisions made
- 2026-06-12: Architecture updated — Lark writes back to HubSpot via MCP
- 2026-06-12: Phase 1 defined — 100–500 contact test cohort · SIG-001 only
- 2026-06-12: Hawaii-specific logic removed — Lark is a national agent
- 2026-06-12: HubSpot property definitions written to hubspot-properties.md
- 2026-06-12: contacts.md removed — Lark reads live from HubSpot via MCP
- 2026-06-09: Signal map finalized — 10 signals across 3 tiers
- 2026-06-09: Compound scoring adopted — Score 1/2/3

---

## Failures and fixes
[No failures yet — first sweep not run]

---

## Instructions to Lark
- After every sweep: update Last run, resolve open threads, log decisions
- After every failure: log error + fix here, update relevant skill file
- Detailed findings go in profiles/ not here — keep this file lean
- Never hand this file to a human to write — Lark owns it