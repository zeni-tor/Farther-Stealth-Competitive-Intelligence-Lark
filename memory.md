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

## RFP Intelligence (Channel 9)
Sector rotation: NOT YET RUN · start with Month 1 (Social services / transitional housing · $1M–$20M)
Last RFP scan: never
Records in corpus: 0
Pipeline matches found: 0
HistoricalRFPData/_index.md: not yet created — Lark creates on first run

---

## Last run
Date: 2026-06-17 · Sweep #1 validation re-run
Signals batched: 75 · Lookback: 2026-05-17 – 2026-06-17
Matches: 11 HIGH (all above AUM) · 22 AMBIGUOUS · 42 NO_MATCH
Score-2 contacts: 1 (Historic Macon Foundation — SIG-001+SIG-002 compound) · Score-1: 7 · Score-3: 0
False positives removed: 3 (SC INC acronym fallback · GlamourGals chapter VP · InTouch geographic mismatch)
HubSpot write-back: STAGED — MCP key pending · 8 records queued
Report generated: outputs/2026-06-17-lark-monthly.html
Status: COMPLETE — full metadata pipeline working · all 4 phases complete

---

## Open threads
- [ ] HubSpot MCP key — obtain and configure for write-back
- [ ] HubSpot custom properties — create 15 properties (hubspot-properties.md)
- [x] RESOLVED: Signal types classified for all 18 HIGH matches — recovered via parallel research
- [x] RESOLVED: Fix Phase 1 pipeline — validation run now writes full metadata dicts (signal_type, source_url, finding_text, signal_date, confidence) to lark_signals.json
- [ ] ACTION WINDOW EXPIRING: Historic Macon Foundation SIG-002 — expires August 1, 2026 (~40 days) — Score-2 now (SIG-001+SIG-002)
- [ ] Verify LinkedIn signal hire dates — validation run signals all Inferred (Short mode, no exact dates)
- [ ] Fix Layer B (Currents API) — 403 Cloudflare block on all queries; investigate alternative or new key
- [ ] LinkedIn queries 4–6 (SIG-002 ED, SIG-005 CIO) returned 0 profiles — investigate query parameters
- [ ] Urban Edge Housing — ProPublica 404 · find correct EIN · verify investable assets vs. real estate

---

## Decisions made
- 2026-06-17 (validation): Full metadata pipeline confirmed working — signal_type/source/finding/date/confidence carried through all 4 phases
- 2026-06-17 (validation): Historic Macon Foundation upgraded to Score-2 — SIG-001 (Stefanie Joyner) + SIG-002 (Emily Hopkins) compound
- 2026-06-17 (validation): 3 false positives removed at Phase 4 — SC INC acronym fallback wrong match · GlamourGals chapter VP not org hire · InTouch geographic mismatch
- 2026-06-22: lark_report.py filename fixed — was lark-weekly.html, corrected to lark-monthly.html
- 2026-06-22: Sweep #1 original complete — 18 HIGH matches, 3 Score-1 contacts
- 2026-06-17: LinkedIn/Apify active — Apify Starter plan approved · ~$1.20/sweep
- 2026-06-17: Fuzzy matcher thresholds validated — HIGH ≥ 80 · AMBIGUOUS ≥ 50
- 2026-06-17: HubSpot write-back staged to CSV — MCP key pending
- 2026-06-09: Compound scoring adopted — Score 1/2/3

---

## Failures and fixes
- 2026-06-22: Phase 1 signals stored as plain (org_name, domain) tuples — signal_type, source, date, finding_text not preserved → all 18 HIGH matches scored Score-1 with Inferred confidence; FIX APPLIED: validation run writes full metadata dicts to lark_signals.json ✓
- 2026-06-17 (validation): Layer B (Currents API) blocked — HTTP 403 Cloudflare error on all 7 queries; zero news signals captured; investigate new key or alternative endpoint for next sweep
- 2026-06-17 (validation): LinkedIn queries 4–6 (SIG-002 ED, SIG-005 CIO) returned 0 profiles from Apify — review recentlyChangedJobs + headcount + functionIds parameters for ED/CIO queries

---

## Instructions to Lark
- After every sweep: update Last run, resolve open threads, log decisions
- After every failure: log error + fix here, update relevant skill file
- Detailed findings go in profiles/ not here — keep this file lean
- Never hand this file to a human to write — Lark owns it