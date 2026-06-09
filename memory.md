# memory.md — Lark · Prospect Intelligence Agent

> This file is written and maintained by Lark, not by humans.
> Detailed prospect findings live in profiles/ — not here.
> This file tracks operational state only: last run, open threads, decisions.
> Cap: 40 lines. Prune before adding. Archive entries older than 30 days.

---

## Last run
Date: —
Contacts swept: —
Signals processed: — · High: — · Medium: — · Contextual: — · Discarded: —
Score-3 contacts: —
Report generated: —
Status: — · No sweeps run yet

---

## Open threads (cross-contact)
- [ ] Confirm HubSpot contact export format — fields needed: org name, contact name,
      title, email, org type, estimated AUM, last outreach date, status, notes
- [ ] Confirm minimum AUM threshold for contacts in the pipeline — helps calibrate
      SIG-007 (AUM threshold crossed) scoring
- [ ] Supervisor decision: confirm which HubSpot contact statuses Lark should sweep
      (cold only, or cold + warming?)
- [ ] Confirm 990 data source — ProPublica Nonprofit Explorer preferred unless
      GuideStar/Candid access is available

---

## Decisions made
- 2026-06-09: Lark initialized — prospect intelligence agent for Farther Institutional
- 2026-06-09: Signal map finalized — 10 signals across 3 tiers (High / Medium /
  Contextual) · Full definitions in data/signals.md
- 2026-06-09: Compound scoring adopted — Score 1/2/3 based on signal combinations ·
  Score-3 contacts are highest priority output
- 2026-06-09: Lark does not write back to HubSpot directly — findings flagged for
  manual action by Farther Institutional team

---

## Failures and fixes
> Lark logs errors here. When something breaks: document it, fix it, update the
> relevant skill file.

[No failures yet — first sweep not run]

---

## Instructions to Lark
- After every sweep: update Last run, resolve open threads, log decisions
- After every failure: log error + fix here, then update the relevant skill file
- Detailed findings go in profiles/ not here — keep this file lean
- Never hand this file to a human to write — Lark owns it
