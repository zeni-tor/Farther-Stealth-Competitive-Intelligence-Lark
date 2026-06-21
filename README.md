# Lark · Prospect Intelligence Agent
## Farther Institutional · Internal use only

Lark monitors Farther's cold nonprofit pipeline for signals that turn a dormant
contact into a live opportunity. It runs a monthly signal sweep, scores contacts
on signal combinations, enriches matched orgs, and writes findings back to HubSpot.

---

## File structure

```
CLAUDE.md                        ← Agent instructions — read first
honesty.md                       ← Honesty standard — read before every output
memory.md                        ← Operational state — Lark maintains this
.env                             ← API keys — never commit

data/
  signals.md                     ← 10 signal definitions, tiers, scoring
  hubspot-properties.md          ← HubSpot custom property definitions
  conferences.md                 ← Conference calendar (Channel 6)

skills/
  monthly-sweep.md               ← Sweep protocol, channel definitions
  signal-classification.md       ← Signal triage rules
  alert-writer.md                ← Output formatting (Slack + HTML)
  behavioral-flags.md            ← Standing competitor patterns

profiles/
  _template.md                   ← Blank profile template
  [org-slug]-profile.md          ← One file per prospect org (created on signal)

contact_data/
  contacts.csv                   ← Full contacts list (190K)

utilities/
  lark_fuzzy_matcher.py          ← Contact matching — batch-first
  lark_fuzzy_test.py             ← Threshold validation
  lark_dedup.py                  ← Deduplicates all_signals[] before match_batch()
  lark_linkedin_channel.py       ← Channel 5 · Apify Profile Search
  lark_rss.py                    ← Layer A · GlobeNewswire Atom feeds
  lark_newsapi.py                ← Layer B · Currents API structured news search
  lark_propublica.py             ← Phase 3 enrichment · ProPublica 990
  lark_report.py                 ← Phase 4 · HTML report generator
  lark_hubspot_csv.py            ← Phase 4 · HubSpot write-back CSV
  lark_signal_grouper.py         ← Phase 4 · groups signals by org for scoring
  lark_profile.py                ← Phase 4 · profile create/update

outputs/
  YYYY-MM-DD-lark-monthly.html           ← HTML report
  YYYY-MM-DD-lark-hubspot-writeback.csv  ← Staged HubSpot write-back
  YYYY-MM-DD-lark-hubspot-sweep-only.csv ← Quiet contacts (lark_last_sweep only)
```

---

## Current status

**Sweep cadence:** Monthly · 30-day lookback window
**Signals active:** All 10 (SIG-001 through SIG-010)
**Channels active:** 1–8 including Channel 5 (LinkedIn/Apify)
**Contacts:** 190K in contact_data/contacts.csv
**HubSpot write-back:** Staged to CSV — MCP key pending
**HubSpot custom properties:** Pending creation (see data/hubspot-properties.md)

---

## Credentials required

| Key | Purpose | Status |
|---|---|---|
| `APIFY_TOKEN` | Channel 5 — LinkedIn small org hires | ⬜ Configure in .env |
| `CURRENTS_API_KEY` | Channel B — structured news search | ⬜ Configure in .env |
| ProPublica | Phase 3 — 990 enrichment | ✅ Free, no key |
| GlobeNewswire RSS | Channel A — press releases | ✅ Free, no key |

Add keys to `.env` at the project root. Never commit `.env`.

---

## Before first sweep checklist

- [ ] `contacts.csv` exported from HubSpot and placed in `contact_data/`
- [ ] `pip install feedparser` run in Claude Code
- [ ] `CURRENTS_API_KEY` added to `.env`
- [ ] `APIFY_TOKEN` added to `.env`
- [ ] HubSpot custom properties created (data/hubspot-properties.md)
- [ ] HubSpot MCP write-back confirmed working (currently staged to CSV)

---

## Running a sweep

Open your Lark project in Claude Code (VS Code integrated terminal or standalone):

```bash
cd path/to/Lark
claude
```

Use the sweep prompt from `skills/monthly-sweep.md`, filling in today's date:

```
Run a full signal sweep. All channels active including Channel 5 (LinkedIn).
Today's date: [DATE]
Lookback window: past 30 days ([DATE-30] – [DATE])
Use contact_data/contacts.csv. Load the fuzzy matcher once, run all
searches first (including LinkedIn via Apify), then call match_batch()
once after ALL channels complete. Deduplicate all_signals[] before
calling match_batch(). Do not read the contact list directly.
Ask if anything is unclear before starting.
```

---

## Companion agent
Wren · Stealth Competitor Intelligence Agent — monitors 50 competitors.
Lark and Wren share the same honesty standard and HTML report design.