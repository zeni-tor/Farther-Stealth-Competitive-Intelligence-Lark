# memory.md — Lark · Prospect Intelligence Agent

> This file is written and maintained by Lark, not by humans.
> Detailed prospect findings live in profiles/ — not here.
> This file tracks operational state only: last run, open threads, decisions.
> Cap: 40 lines. Prune before adding. Archive entries older than 30 days.

## FUZZY MATCH
  Compare each extracted org name against contact_data/ using the matcher.

  **Do NOT check the contact list directly — ever.**
  The fuzzy matcher is the only thing that touches contact_data/.
  Lark never reads, searches, or references the CSV except by
  calling lark_fuzzy_matcher.py.

---

## Last run
Date: —
Signals processed: — · High: — · Medium: — · Contextual: — · Discarded: —
Matches: — HIGH · — AMBIGUOUS · — discarded
Score-1 contacts: —
HubSpot write-back: STAGED — MCP key pending
Report generated: —
Status: No sweeps run yet

---

## Open threads
- [ ] HubSpot MCP key — obtain and configure for write-back
- [ ] HubSpot custom properties — create 15 properties (hubspot-properties.md)
- [ ] Run lark_fuzzy_matcher.py self-test to confirm module loads cleanly
- [ ] Confirm ProPublica API — test single org lookup before first sweep
- [ ] Review first sweep results — validate signal quality before expanding channels
- [ ] Decision pending: activate Channels 2–7 after sweep 1 validated

---

## Decisions made
- 2026-06-17: LinkedIn/Apify deferred — financial justification required
- 2026-06-17: Fuzzy matcher thresholds validated — HIGH ≥ 80 · AMBIGUOUS ≥ 50
- 2026-06-17: Claude Code runtime confirmed — Lark runs locally, not Claude.ai
- 2026-06-17: Contact source = contact_data/ CSV (local) — not HubSpot MCP
- 2026-06-17: HubSpot write-back staged to CSV — MCP key pending
- 2026-06-17: Sweep 1 gate = SIG-001 only · Channels 2–7 READY after validation
- 2026-06-17: Channel 5 (LinkedIn) DEFERRED — separate from channel activation
- 2026-06-16: lark_fuzzy_matcher.py built — callable module in utilities/
- 2026-06-16: lark_fuzzy_test.py validated — 10/10 exact matches scored HIGH
- 2026-06-12: Phase 1 defined — SIG-001 only · CSV contacts · broad web search
- 2026-06-12: Hawaii-specific logic removed — Lark is a national agent
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