# Lark · Prospect Intelligence Agent
### Farther Institutional · Internal use only

---

## What is Lark?

Lark is an AI agent that monitors Farther's cold nonprofit pipeline and alerts advisors when something happens at an org that creates a natural reason to reach out.

Farther has roughly 190,000 nonprofit contacts in HubSpot. Most of them are dormant — no active conversation, no recent touch. Lark watches that list and surfaces the ones where something just changed: a new CFO was hired, a capital campaign just launched, a new Executive Director started. These are moments when a cold call becomes a warm call.

Lark runs inside **Claude Code** — Anthropic's AI coding environment. She reads skill files that tell her how to run, searches the web and LinkedIn for signals, matches findings against Farther's contact list, enriches matched orgs with financial and leadership data, and produces a report for advisors to act on.

She is not a chatbot. She does not answer questions or have conversations. She runs a protocol, produces outputs, and stops.

---

## What Lark produces

**Monthly sweep report** (`outputs/YYYY-MM-DD-lark-monthly.html`)
An HTML report showing which pipeline orgs fired a signal this month, what the signal was, and a call-prep card for each. Organized by priority score. Advisors read this before outreach.

**HubSpot write-back CSV** (`outputs/YYYY-MM-DD-lark-hubspot-writeback.csv`)
A staged CSV ready to import into HubSpot. Updates signal fields, scores, action windows, and enrichment data on matched contacts.

**Enrichment call-prep report** (`outputs/YYYY-MM-DD-lark-enrichment-report.html`)
A deeper call-prep card for a specific list of orgs — answers five advisor questions per org (mission, fundraising, financial health, board, why reach out today).

**RFP Intelligence report** (`outputs/YYYY-MM-DD-lark-rfp-intelligence.html`)
A research report on published nonprofit investment management RFPs. Builds a pattern library for Farther's RFP creation team over time.

---

## What is a signal?

A signal is a change at a nonprofit org that suggests an investment management conversation may be timely. Lark monitors 10 signal types:

| Code | Signal | Why it matters |
|---|---|---|
| SIG-001 | New CFO or Director of Finance | New finance lead often reviews advisor relationships |
| SIG-002 | New CEO or Executive Director | New leadership often reassesses everything |
| SIG-003 | Capital campaign launched or closed | Large influx of assets needs management |
| SIG-004 | Significant grant or gift received | Same — sudden asset growth |
| SIG-005 | New Investment Committee Chair | New IC chair often triggers an RFP |
| SIG-006 | New board chair or treasurer | Governance change, fresh eyes on advisor |
| SIG-007 | AUM threshold crossing | Org just crossed $1M, $5M, or $10M — first time needing real management |
| SIG-008 | M&A or merger | Combined assets, new leadership, new structure |
| SIG-009 | New strategic plan with endowment language | Org formalizing investment policy |
| SIG-010 | First-time endowment established | Brand new endowment — greenfield opportunity |

Signals are scored. A single SIG-001 is a Score-1. A new CFO *and* a new Executive Director at the same org in the same sweep is a Score-2 — much higher priority. Score-3 is rare and represents the highest-urgency contacts.

---

## Lark's three modes

### Mode 1 — Monthly Sweep (default)

Lark scans the world for signals across 9 channels, matches findings against the 190K contact list, enriches HIGH matches, scores them, and produces the monthly report. This is the primary operation — run it once a month.

**Channels:**
- Ch 1–4: Web search — news, press releases, GuideStar, org websites
- Ch 5: LinkedIn — small org leadership hires via Apify (requires paid Apify account)
- Ch 6: Conference monitoring — NACUBO, AFP, and other nonprofit sector events
- Ch 7: ProPublica — 990 data for AUM threshold crossings
- Ch 8: Signal cross-check — compound scoring across channels
- Ch 9: RFP Intelligence — scans for published investment management RFPs (auto-runs after Ch 1–8)

### Mode 2 — Enrichment Run (on-demand)

An advisor has a list of orgs they want deeper intelligence on. Lark skips the signal search and goes straight to research — mission, financials, board, recent news, and a call-prep card for each org. No scoring, no action windows.

Use this when an advisor has a meeting coming up, is preparing for a conference, or wants to prep a specific list of prospects.

### Mode 3 — RFP Intelligence (standalone or automatic)

Scans for published nonprofit investment management RFPs — current and historical. Builds structured records including verbatim questions, evaluation criteria and weights, and Lark's critique of each RFP. Useful for:
- Understanding what orgs ask for when they go to market for an advisor
- Building the pattern library for Farther's RFP creation team
- Flagging when a pipeline org has published an RFP in the past

---

## How to run a monthly sweep

### Prerequisites
1. Install dependencies: `pip install feedparser pandas openpyxl python-dotenv`
2. Configure `.env` at the project root (see Credentials section below)
3. Make sure `contacts.csv` is in the project root (export from HubSpot)
4. Have an Apify paid account (Starter plan, $49/month) for Channel 5

### Step 1 — Run the launcher from your terminal
```bash
cd path/to/LARK
python3 lark_launch.py
```

This script:
- Fetches Layer A (GlobeNewswire RSS) and Layer B (Currents API news) locally — these APIs block Claude Code's server IPs, so they must be pre-fetched on your machine
- Builds the full sweep prompt and writes it to `preflight/sweep-prompt-YYYY-MM-DD.txt`
- Launches Claude Code
- Prints a one-liner to paste

### Step 2 — Paste into Claude Code
```
Read preflight/sweep-prompt-2026-06-24.txt and follow the instructions.
```

Lark reads the prompt file, runs the sweep, and produces all outputs. A full sweep takes 15–45 minutes depending on how many signals fire.

### Step 3 — Review the report
Open `outputs/YYYY-MM-DD-lark-monthly.html` in a browser. Score-2 and Score-3 contacts at the top are the highest-priority outreach candidates.

---

## How to run an enrichment run

### Step 1 — Prepare your input file
Export a contact list from HubSpot as Excel (.xlsx) or put org names in a plain text file (one per line). Place it in the project root or anywhere accessible.

If using HubSpot export: the script auto-detects the "Associated Company (Primary)" column and extracts org names, contact details, and any GS asset figures already in HubSpot.

### Step 2 — Run the enrichment launcher
```bash
cd path/to/LARK
python3 lark_enrich.py
```

The script lists Excel/CSV/text files it finds, you select one, optionally filter by advisor name, and it builds the enrichment prompt:

```
🪶  Lark · Enrichment Run Launcher

   Files available in inputs/:

   [1] Jay_Chang_Pilot.xlsx  (10KB)
   [2] Will_Gilmore_Pilot.xlsx  (13KB)

   Select file (number or path): 1
   Filter by advisor name? (press Enter to include all):

   ✓ Prompt written to: preflight/enrichment-prompt-2026-06-24-jay_chang_pilot.txt
```

### Step 3 — Paste into Claude Code
```
Read preflight/enrichment-prompt-2026-06-24-jay_chang_pilot.txt and follow the instructions.
```

Lark enriches every org in the list and produces the call-prep report.

---

## File structure

The project currently lives as a flat directory (no subdirectories). Files are organized by naming convention.

```
LARK/
  ── Core ──────────────────────────────────────────────────────
  CLAUDE.md                    ← Agent instructions (read by Lark at every session start)
  honesty.md                   ← Honesty standard (read before every output)
  memory.md                    ← Operational state (Lark maintains this)
  .env                         ← API keys — never commit
  .env.example                 ← Safe-to-commit template

  ── Launchers ─────────────────────────────────────────────────
  lark_launch.py               ← Monthly sweep launcher · run from terminal
  lark_enrich.py               ← Enrichment run launcher · run from terminal

  ── Skills (protocols Lark reads and follows) ─────────────────
  monthly-sweep.md             ← Monthly sweep protocol and channel definitions
  enrichment-run.md            ← Enrichment run protocol
  rfp-intelligence.md          ← Channel 9 RFP Intelligence protocol
  signal-classification.md     ← Signal triage rules
  alert-writer.md              ← Output formatting
  behavioral-flags.md          ← Standing competitor patterns

  ── Data ──────────────────────────────────────────────────────
  signals.md                   ← 10 signal definitions, scoring, action windows
  hubspot-properties.md        ← HubSpot custom property definitions
  conferences.md               ← Conference calendar (Channel 6)

  ── Utilities (Python scripts Lark runs directly) ─────────────
  lark_fuzzy_matcher.py        ← Contact matching — fuzzy name matching
  lark_run_matcher.py          ← Standalone matcher script (called by launcher)
  lark_fuzzy_test.py           ← Matcher threshold validation
  lark_dedup.py                ← Signal deduplication before matching
  lark_linkedin_channel.py     ← Channel 5 · LinkedIn via Apify
  lark_rss.py                  ← Layer A · GlobeNewswire RSS
  lark_newsapi.py              ← Layer B · Currents API news search
  lark_propublica.py           ← Enrichment · ProPublica 990 data
  lark_report.py               ← HTML report generator
  lark_hubspot_csv.py          ← HubSpot write-back CSV generator
  lark_signal_grouper.py       ← Groups signals by org for compound scoring
  lark_profile.py              ← Profile create/update

  ── Profiles (one per org, created when a signal fires) ───────
  _template.md                 ← Blank profile template
  [org-slug]-profile.md        ← e.g. historic-macon-foundation-profile.md

  ── Enrichment profiles (created by enrichment runs) ──────────
  [org-slug]-profile.md        ← enrichment data only, no signal timeline
  (Note: currently also in root — will be moved to subfolder)

  ── RFP records ───────────────────────────────────────────────
  _index.md                    ← Running index of all RFP records
  reproductive-freedom-for-all-2026-rfp-record.md ← first corpus entry
  (Note: currently in root — will be moved to HistoricalRFPData/)

  ── Preflight (pre-fetched API data + prompt files) ───────────
  preflight/
    rss-YYYY-MM-DD.json        ← GlobeNewswire RSS · written by lark_launch.py
    currents-YYYY-MM-DD.json   ← Currents API · written by lark_launch.py
    sweep-prompt-YYYY-MM-DD.txt          ← Full sweep prompt
    enrichment-prompt-YYYY-MM-DD-[slug].txt ← Full enrichment prompt

  ── Inputs (source files for enrichment runs) ─────────────────
  [advisor]-pilot.xlsx         ← HubSpot export for enrichment run

  ── Contact data (never read directly by Lark) ────────────────
  contacts.csv                 ← Full Farther contact list (190K) · matcher only

  ── Outputs ───────────────────────────────────────────────────
  YYYY-MM-DD-lark-monthly.html             ← Monthly sweep report
  YYYY-MM-DD-lark-hubspot-writeback.csv    ← HubSpot write-back (signal records)
  YYYY-MM-DD-lark-hubspot-sweep-only.csv  ← Quiet contacts (lark_last_sweep only)
  YYYY-MM-DD-lark-enrichment.csv          ← Enrichment write-back
  YYYY-MM-DD-lark-enrichment-report.html  ← Enrichment call-prep report
  YYYY-MM-DD-lark-rfp-intelligence.html   ← Channel 9 RFP report
```

---

## Credentials

Add all keys to `.env` at the project root. Never commit `.env`.

| Key | Purpose | How to get it | Status |
|---|---|---|---|
| `APIFY_TOKEN` | Channel 5 — LinkedIn leadership hires | console.apify.com → Settings → Integrations | Required |
| `APIFY_TASK_ID` | Optional — only if using a saved Apify task | console.apify.com → Actors → Tasks | Optional |
| `CURRENTS_API_KEY` | Layer B — structured news search | currentsapi.services | Required |
| ProPublica | Phase 3 — 990 enrichment | Free, no key needed | ✅ Ready |
| GlobeNewswire RSS | Layer A — press releases | Free, no key needed | ✅ Ready |

**Apify note:** Channel 5 requires a paid Apify account (Starter plan, $49/month). The free tier limits you to 10 runs total and will silently return 0 results once exhausted. Channel 5 costs approximately $1.20/month in usage on a paid plan.

`.env` format:
```
APIFY_TOKEN=apify_api_your_token_here
CURRENTS_API_KEY=your_currents_key_here
# APIFY_TASK_ID=optional_task_id
```

---

## Before your first sweep

- [ ] Export contacts from HubSpot as CSV and place in project root as `contacts.csv`
- [ ] Run `pip install feedparser pandas openpyxl python-dotenv` in terminal
- [ ] Add `APIFY_TOKEN` and `CURRENTS_API_KEY` to `.env`
- [ ] Upgrade Apify to Starter plan ($49/month)
- [ ] Create the 15 HubSpot custom properties defined in `hubspot-properties.md`
- [ ] Test Channel 5: `python3 lark_linkedin_channel.py` from the project directory
- [ ] Run `python3 lark_launch.py --no-rss --no-currents --no-launch` to verify setup

---

## HubSpot integration

HubSpot write-back is currently **staged to CSV** — Lark generates a ready-to-import CSV after every sweep. The MCP (direct API connection) key is pending.

Until the MCP key is configured, import the CSV manually:
1. Open `outputs/YYYY-MM-DD-lark-hubspot-writeback.csv`
2. HubSpot → Contacts → Import → update existing contacts
3. Match on Email or Company Name

The 15 custom properties Lark writes to are defined in `hubspot-properties.md`. These must be created in HubSpot before any write-back will work.

---

## Output guide for advisors

### Reading the monthly report

The report opens with a stats bar showing how many signals fired and at what score level. Scroll past it to the cards.

**Score-2 and Score-3 cards** are at the top — these are the highest-priority contacts. Each card shows:
- What signal fired and when
- The org's AUM, location, and EIN
- A call-prep section with mission, talking points, and incumbent advisor if known
- An action window (how long you have before the signal goes stale)

**Score-1 cards** follow — worth a look, lower urgency.

**AMBIGUOUS** section lists orgs where Lark found a signal but couldn't confidently match it to a HubSpot contact. These need a human to confirm before outreach.

### Reading the enrichment report

One card per org, answering five questions:
1. What does this org do?
2. Any capital campaigns recently or coming up?
3. Are they financially healthy — growing, flat, or contracting?
4. Who is on the board — anyone worth referencing?
5. Is there something happening right now worth mentioning on a call?

Each answer is labeled Confirmed, Inferred, or Speculative so you know how much to rely on it.

---

## Current status (as of Sweep 2 · 2026-06-24)

| Item | Status |
|---|---|
| Sweeps completed | 2 |
| Contacts in pipeline | 190K |
| Active signal profiles | 12 |
| HubSpot write-back | Staged to CSV · MCP key pending |
| Channel 5 (LinkedIn) | Down · Apify free tier exhausted · upgrade to Starter to restore |
| Layer B (Currents API) | Must run `lark_launch.py` locally — Cloudflare blocks Claude Code server IPs |
| RFP corpus | 1 record (Reproductive Freedom for All · June 2026) |
| **URGENT** | Historic Macon Foundation · Score-2 · action window closes Aug 1, 2026 |

---

## Companion agent

**Wren** is a separate agent that monitors 50 competitor firms for Farther Intelligence. Lark and Wren share the same honesty standard and HTML report design but run independently in separate project folders. This README covers Lark only.

---

## Questions?

Ask the person who set this up, or open `CLAUDE.md` — it contains Lark's full operating instructions and is the authoritative source on how she works.