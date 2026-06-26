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
Sector rotation: Month 1 complete · next sweep: Month 2 (Arts & culture / museums · $5M–$50M)
Last RFP scan: 2026-06-24
Records in corpus: 1 (RFFA, archived — deadline passed May 8, 2026)
Pipeline matches found: 0
HistoricalRFPData/_index.md: created 2026-06-24

---

## Last run
Date: 2026-06-24 · Sweep #2
Signals batched: 7 · Lookback: 2026-05-24 – 2026-06-24
Matches: 5 HIGH (all above AUM) · 2 AMBIGUOUS · 0 NO_MATCH
Score-2 contacts: 1 (Historic Macon Foundation — SIG-001+SIG-002 compound) · Score-1: 4 · Score-3: 0
False positives removed: 1 (Service Year Alliance — matcher returned wrong org, Utilities Service Alliance Inc)
HubSpot write-back: STAGED — MCP key pending · 5 records queued
Report generated: outputs/2026-06-24-lark-monthly.html · outputs/2026-06-24-lark-rfp-intelligence.html
Status: COMPLETE — all 4 phases complete + Channel 9 first run

---

## Open threads
- [ ] HubSpot MCP key — obtain and configure for write-back
- [ ] HubSpot custom properties — create 15 properties (hubspot-properties.md)
- [ ] ACTION WINDOW URGENT: Historic Macon Foundation SIG-002 — closes August 1, 2026 (38 days) — Score-2 · Move now
- [ ] ACTION WINDOW URGENT: Fiver Children's Foundation SIG-004 — closes ~July 22, 2026 (28 days) — Move now
- [ ] Channel 5 (LinkedIn/Apify) COMPLETE FAILURE Sweep 2 — all 6 queries returned 0 profiles (regression from Sweep 1) · investigate Apify actor parameters and account status
- [ ] Layer B (Currents API) blocked Sweep 2 — HTTP 403 Cloudflare on all 7 queries (second consecutive sweep) · must run lark_launch.py from local terminal
- [ ] TACA AUM near $1M floor — team judgment needed before outreach
- [ ] Verify 7 LinkedIn signals from Sweep 1 (NSABP Foundation, Int'l Tennis Hall of Fame, Urban Edge Housing, Boston Senior Home Care, Kids In Need Foundation, DT Institute, EFI Foundation)
- [ ] Urban Edge Housing — ProPublica 404 · find correct EIN
- [ ] Candid — permanent CEO hire: monitor and upgrade score when announced
- [ ] Unleashing Potential — watch for permanent CEO announcement (triggers outreach window)
- [ ] Fiver matcher fix: use "Fiver Children's Foundation" (apostrophe) in Sweep 3 signals list

---

## Decisions made
- 2026-06-24: Chicago Sinfonietta SIG-002 window EXPIRED — appointment was June 13, 2025 start; window closed ~Dec 2025. Financial distress (May 2026 operational pause) noted but not actionable under standard signals. Moved to NOTED.
- 2026-06-24: TACA (The Autism Community in Action) confirmed SIG-002 external hire — Mike Le JD/MBA from PRNewswire. Score-1. AUM near floor — flagged for team judgment.
- 2026-06-24: Fiver AMBIGUOUS (55) confirmed correct match — apostrophe name variant. Treated as HIGH. Fix name for Sweep 3.
- 2026-06-24: Service Year Alliance discarded — matcher returned Utilities Service Alliance Inc (wrong org, score 50) · signal also outside lookback window
- 2026-06-24: Channel 9 first run — Month 1 sector (social services/transitional housing) · 1 RFP found (RFFA, archived) · HistoricalRFPData/ created
- 2026-06-22: lark_report.py filename fixed — was lark-weekly.html, corrected to lark-monthly.html
- 2026-06-22: Sweep #1 original complete — 18 HIGH matches, 3 Score-1 contacts
- 2026-06-17: Fuzzy matcher thresholds validated — HIGH ≥ 80 · AMBIGUOUS ≥ 50
- 2026-06-17: HubSpot write-back staged to CSV — MCP key pending
- 2026-06-09: Compound scoring adopted — Score 1/2/3

---

## Failures and fixes
- 2026-06-24: Channel 5 (LinkedIn/Apify) complete failure — all 6 queries returned 0 profiles. Regression: Sweep 1 had queries 1-3 returning data. Investigate Apify actor rate limits and harvestapi~linkedin-profile-search parameters.
- 2026-06-24: Monthly HTML report overwritten by Channel 9 RFP stub — second generate_report() call used minimal SweepData (0 signals). Fixed: regenerated full report with complete SweepData. Prevention: never call generate_report() twice in same session.
- 2026-06-17 (validation): Layer B (Currents API) blocked — HTTP 403 Cloudflare error on all 7 queries; second sweep same failure; must run lark_launch.py from local terminal (not via Claude Code server IPs)
- 2026-06-22: Phase 1 signals stored as plain (org_name, domain) tuples — signal_type, source, date, finding_text not preserved → all 18 HIGH matches scored Score-1 with Inferred confidence; FIX APPLIED: validation run writes full metadata dicts ✓

---

## Instructions to Lark
- After every sweep: update Last run, resolve open threads, log decisions
- After every failure: log error + fix here, update relevant skill file
- Detailed findings go in profiles/ not here — keep this file lean
- Never hand this file to a human to write — Lark owns it
