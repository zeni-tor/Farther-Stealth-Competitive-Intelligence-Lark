# Lark · Prospect Intelligence Agent
## Farther Institutional · Internal use only

Lark monitors Farther's cold nonprofit pipeline for signals that turn a dormant
contact into a live opportunity. It runs a weekly signal sweep, scores contacts
on signal combinations, enriches matched orgs, and writes findings back to HubSpot.

---

## File structure

```
CLAUDE.md                   ← Agent instructions — read first
honesty.md                  ← Honesty standard — read before every output
memory.md                   ← Operational state — Lark maintains this

data/
  signals.md                ← 10 signal definitions, tiers, scoring
  hubspot-properties.md     ← HubSpot custom property definitions
  conferences.md            ← Conference calendar (Channel 6 · Phase 2)

skills/
  weekly-sweep.md           ← Sweep protocol, channel definitions
  signal-classification.md  ← Signal triage rules
  alert-writer.md           ← Output formatting (Slack + HTML)
  behavioral-pattern-analysis.md  ← (from Wren — adapt for Lark)

profiles/
  _template.md              ← Blank profile template
  [org-slug]-profile.md     ← One file per prospect org (created on signal)

outputs/
  YYYY-MM-DD-lark-weekly.html  ← Weekly HTML report
```

---

## Current status

**Phase:** 1 — Test cohort
**Signal active:** SIG-001 (New CFO / Finance Director) only
**Cohort size:** 100–500 contacts (pending selection)
**HubSpot MCP key:** Pending
**HubSpot custom properties:** Pending creation (see data/hubspot-properties.md)

---

## Before first sweep checklist

- [ ] HubSpot MCP key obtained and configured
- [ ] HubSpot custom properties created (hubspot-properties.md)
- [ ] Test cohort selected and confirmed (100–500 contacts)
- [ ] ProPublica API test — single org lookup confirmed working
- [ ] Google Drive 990 folder path confirmed for MCP access
- [ ] Single HubSpot record write-back test confirmed working

---

## Companion agent
Wren · Stealth Competitor Intelligence Agent — monitors 50 competitors.
Lark and Wren share the same honesty standard and HTML report design.