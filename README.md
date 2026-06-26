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

## What is a channel?

A channel is a data source or search method Lark uses to look for signals. Channels are *where* Lark looks; signals are *what* she is looking for.

| Channel | Source | Signals it can detect |
|---|---|---|
| Ch 1 | General web search | SIG-001 through SIG-010 |
| Ch 2 | Nonprofit news and press release sites | SIG-003, SIG-004, SIG-006, SIG-007 |
| Ch 3 | GuideStar / Candid database | SIG-007, SIG-010 |
| Ch 4 | Org websites directly | SIG-001, SIG-002, SIG-009 |
| Ch 5 | LinkedIn via Apify | SIG-001, SIG-002, SIG-005 |
| Ch 6 | Conference monitoring | Conference presence as signal amplifier |
| Ch 7 | ProPublica 990 data | SIG-007, SIG-010 |
| Ch 8 | Signal cross-check | Reviews all channels for compound scoring |
| Ch 9 | RFP Intelligence | Investment management RFPs (research corpus) |

The relationship is many-to-many — one channel can detect multiple signal types, and one signal type can surface through multiple channels. A new CFO (SIG-001) might appear in a press release (Ch 2), on LinkedIn (Ch 5), and on the org's leadership page (Ch 4). When it does, that cross-channel confirmation raises Lark's confidence in the finding.

**A simple way to remember it: channels are the fishing spots, signals are what you're fishing for.**

Signals are scored. A single SIG-001 is a Score-1. A new CFO *and* a new Executive Director at the same org in the same sweep is a Score-2 — much higher priority. Score-3 is rare and represents the highest-urgency contacts.

---

## RFP Intelligence (Channel 9)

In addition to the 10 signals above, Lark runs a separate research operation called the RFP Intelligence channel. This is not an outreach trigger — it is a research corpus that builds over time.

**What it does:**
Lark scans for published nonprofit investment management RFPs — requests for proposal where an org is going to market for an investment advisor or OCIO. When she finds one, she builds a structured record containing:

- Who published it, their AUM, and why they issued it
- Every question they asked, verbatim
- Their evaluation criteria and weights (if stated)
- A critique of what the RFP got right and what it missed
- What the RFP tells Farther about how to position with similar orgs

**Two uses:**

1. **Pipeline match** — if the org that published the RFP is in Farther's contact list, the record is flagged as call-prep intelligence. Knowing what questions an org asked three years ago, and how they weighted their criteria, is a significant advantage before a call.

2. **Research corpus** — all records are kept regardless of pipeline match. Over time `HistoricalRFPData/` becomes a pattern library: what do $5–15M transitional housing nonprofits ask for? What do college foundations weight most heavily? This intelligence informs how Farther positions its offering and writes its own RFP responses.

**Sector rotation:**
Each sweep, Channel 9 runs a broad search focused on a different nonprofit sector and AUM band, cycling through six sectors over six months. This builds the corpus systematically rather than randomly.

**Output:**
A separate HTML report (`outputs/YYYY-MM-DD-lark-rfp-intelligence.html`) — not included in the main monthly report, which only gets a one-line summary. The RFP report is intended for the RFP creation team and for advisors doing deep prep on specific orgs.

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

This script prefetches Layer A (GlobeNewswire RSS) and Layer B (Currents API news) on your local machine — these APIs block Claude Code's server IPs so they must be fetched locally first. It then builds the full sweep prompt, writes it to `preflight/sweep-prompt-YYYY-MM-DD.txt`, and prints the one-liner to paste.

### Step 2 — Paste the one-liner into Claude Code

```
Read preflight/sweep-prompt-YYYY-MM-DD.txt and follow the instructions.
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

   ✓ Prompt written to: preflight/enrichment-prompt-YYYY-MM-DD-[advisor-slug].txt
```

### Step 3 — Paste the one-liner into Claude Code

The launcher writes the full enrichment prompt to `preflight/` and prints a one-liner:

```
Read preflight/enrichment-prompt-YYYY-MM-DD-[advisor-slug].txt and follow the instructions.
```

Lark reads the prompt file — which contains the full org list with all contact data, GS figures, and instructions — and runs the enrichment.

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

## Maintaining Lark

Lark needs periodic human upkeep to stay accurate. Here's what to maintain, when, and how.

---

### conferences.md — update before each sweep

**What it is:** The nonprofit conference calendar Lark reads when running Channel 6. It tells Lark which conferences are coming up, who the audience is, and when monitoring and outreach windows open.

**What needs updating:**
- Add upcoming conferences for the next 6 months when you become aware of them
- Mark conferences as PASSED once they've occurred
- Update the "Farther attending?" column when Farther confirms attendance at an event — this changes the outreach angle from cold to "see you there"
- Add any new regional associations or conferences Lark surfaces during sweeps

**How often:** Annually — update dates for the coming year's conferences, typically in Q4 when organizations publish their schedules. Also update as needed when: a conference is confirmed as PASSED, Farther confirms attendance, or a new relevant conference is discovered. Lark reads the monitoring window dates from this file automatically — if the dates are current, you don't need to touch it between sweeps.

**Format:** Follow the existing table structure in the file. Every conference needs at minimum: dates, location, audience, and monitoring window open/close dates.

---

### contacts.csv — refresh quarterly

**What it is:** The full Farther contact list (~190K contacts) that Lark matches signals against. Every signal Lark finds gets fuzzy-matched against this file to determine whether it's a Farther pipeline org.

**What needs updating:** Export a fresh copy from HubSpot and replace the existing `contacts.csv` in the project root. If new contacts are added to HubSpot between sweeps, Lark won't find matches for them until the CSV is refreshed.

**How often:** At minimum quarterly. Ideally before each sweep if the contact list changes frequently.

**How to export from HubSpot:** Contacts → Export → All contacts → CSV. Make sure the export includes at minimum: Company Name, Associated Company (Primary), Email, City, State.

---

### signals.md — update when signal definitions change

**What it is:** The definitions, scoring rules, and action windows for all 10 signal types. Lark reads this during every sweep to know what counts as a signal, how to score it, and how long the action window lasts.

**What needs updating:**
- Action window durations if Farther's sales process changes
- Signal tier assignments if certain signals prove more or less valuable over time
- New signal types if Lark starts monitoring for something new
- Retired signal types — mark as retired with a note rather than deleting

**How often:** Only when something structural changes. Not a routine maintenance item.

**Important:** Lark also maintains a running iteration log in `signals.md` — she adds entries when a signal pattern is confirmed, refined, or retired. Don't overwrite her entries.

---

### memory.md — Lark maintains this, but review monthly

**What it is:** Lark's operational state file. She updates it after every sweep — recording what ran, what was found, open threads, bugs encountered, and what needs follow-up.

**What you should do:** Read it after each sweep to understand what Lark flagged as needing human attention. Look for:
- Open threads (things Lark couldn't resolve herself)
- Bug fixes she applied and whether they need to be reflected in a skill file
- RFP corpus state — sector rotation, records count

**What you should NOT do:** Hand-edit memory.md except to add the `APIFY_TASK_ID` or similar operational notes Lark can't set herself. Lark owns this file.

---

### rfp-intelligence.md — update sector rotation monthly

**What it is:** The Channel 9 protocol. Includes a 6-month sector rotation schedule — each sweep focuses the broad RFP search on a different sector and AUM band.

**What needs updating:** After each sweep, check `memory.md` to see which sector ran and advance the rotation. Lark does this herself, but if memory.md is reset or the rotation gets out of sync, you may need to set it manually.

**Sector rotation schedule:**
| Month | Sector | AUM band |
|---|---|---|
| 1 | Social services / transitional housing | $1M–$20M |
| 2 | Arts & culture / museums | $5M–$50M |
| 3 | Community foundations | $5M–$25M |
| 4 | College / university foundations | $5M–$50M |
| 5 | Healthcare nonprofits | $5M–$100M |
| 6 | Environmental / conservation | $1M–$25M |

---

### profiles/ — review periodically, never hand-edit signal data

**What it is:** One markdown file per pipeline org that has fired a signal. Contains the org's full intelligence record — signal timeline, compound score, AUM, leadership, action window, and call-prep notes.

**What you should do:** Read profiles before outreach calls. The call-prep section at the bottom of each profile is written for the advisor, not for Lark.

**What you should NOT do:** Edit the signal timeline, compound score, or action window manually. These are set by Lark during sweeps. If something looks wrong, flag it as an open thread in memory.md and let Lark correct it on the next sweep.

You can add notes to the "What Lark currently knows" section if you have intelligence from a call or meeting — just label it clearly as human-added so Lark doesn't overwrite it.

---

### Credential rotation

| Key | When to rotate | How |
|---|---|---|
| `APIFY_TOKEN` | If compromised or if you switch Apify accounts | console.apify.com → Settings → Integrations → Generate new token |
| `CURRENTS_API_KEY` | If compromised | currentsapi.services → Dashboard |
| contacts.csv export | Quarterly or when HubSpot contacts list changes significantly | HubSpot → Contacts → Export |

---

### What to do after each sweep

1. Open `outputs/YYYY-MM-DD-lark-monthly.html` and review Score-2 and Score-3 cards
2. Check `memory.md` for open threads Lark flagged
3. Import `outputs/YYYY-MM-DD-lark-hubspot-writeback.csv` into HubSpot (until MCP is live)
4. Check `outputs/YYYY-MM-DD-lark-rfp-intelligence.html` for any pipeline RFP matches
5. Forward Score-2+ call-prep cards to the relevant advisor
6. Update `conferences.md` if any monitoring windows have opened or passed
7. Note any signal quality issues (wrong org matched, signal misclassified) in `memory.md`

---

## Running Lark in the cloud — what changes

The current architecture runs Lark locally inside Claude Code, with a human triggering each sweep manually. This is the right approach for a pilot — it lets the team validate that signals are real, enrichment is useful, and advisors act on the reports. Once that's confirmed, Lark can be moved to a fully automated cloud deployment.

Here is what changes at each stage.

---

### Stage 1 — Current (local, manual trigger)

```
Human runs lark_launch.py in terminal
       ↓
Preflight files written locally
       ↓
Human pastes one-liner into Claude Code
       ↓
Lark runs sweep
       ↓
Outputs written to local outputs/ folder
       ↓
Human imports CSV to HubSpot manually
       ↓
Human emails/Slacks report to advisors
```

**What stays manual:** everything. Good for validation, not for production.

---

### Stage 2 — HubSpot MCP connected (next milestone)

The MCP key is configured and Lark writes directly to HubSpot. The CSV import step disappears.

**What changes:**
- Add `HUBSPOT_MCP_KEY` to `.env`
- Remove "MCP key pending" note from `CLAUDE.md`
- Lark calls HubSpot write-back directly at the end of Phase 4 instead of writing a CSV
- The sweep-only CSV (quiet contacts — `lark_last_sweep` only) still writes as a backup

**What stays manual:** human still triggers the sweep, human still distributes the report.

**Effort:** Low — the write-back code in `lark_hubspot_csv.py` already has the MCP path stubbed. Configure the key and flip the flag.

---

### Stage 3 — Automated trigger (cloud scheduler)

A scheduler fires the sweep automatically on a set cadence — no human needed to initiate.

**What changes:**

*Replace `lark_launch.py` with a cloud trigger.* Options:
- **GitHub Actions** — free, simple, runs on a cron schedule. Add a `.github/workflows/lark-sweep.yml` that calls the Claude API directly with the sweep prompt on the first Monday of each month.
- **AWS EventBridge + Lambda** — more robust, better for production. EventBridge fires monthly, Lambda calls the Claude API.
- **Anthropic's own scheduling infrastructure** — if available, the cleanest path.

*Layer A and Layer B no longer need local prefetch.* The Cloudflare block that forced local prefetching was specific to Anthropic's consumer server IPs. A cloud deployment on a dedicated IP (AWS, GCP, etc.) won't be blocked. The preflight step goes away entirely.

*The prompt file pattern stays.* The scheduler writes the prompt to a known location and passes it to the Claude API — same logic, no human copy-paste.

**What stays manual:** enrichment runs (an advisor still decides which list to enrich and when), conference calendar updates, and contacts.csv refresh.

**Effort:** Medium. Requires cloud infrastructure setup, Claude API integration, and testing. Lark's skill files and intelligence logic are unchanged.

---

### Stage 4 — Fully automated enrichment (HubSpot trigger)

HubSpot triggers an enrichment run automatically when a new contact is added to a specific list — for example, a "New Prospects" list that advisors add contacts to.

**What changes:**
- HubSpot webhook fires when a contact is added to the trigger list
- Webhook calls the Claude API with an enrichment prompt for that contact
- Lark enriches the org and writes back to HubSpot directly via MCP
- Advisor gets a Slack notification with the call-prep card

**What this looks like for an advisor:** add an org to "New Prospects" in HubSpot, get a Slack message with the call-prep card 20 minutes later. No script, no Claude Code.

**Effort:** Higher. Requires HubSpot webhook configuration, a lightweight API endpoint to receive the webhook and call Claude, and Slack integration.

---

### What never changes

Regardless of how Lark is triggered or where she runs, the following stay exactly the same:

- `CLAUDE.md` — her operating instructions
- `honesty.md` — her honesty standard
- All skill files (`monthly-sweep.md`, `enrichment-run.md`, `rfp-intelligence.md`, etc.)
- Signal definitions (`signals.md`)
- All utility scripts (`lark_fuzzy_matcher.py`, `lark_propublica.py`, etc.)
- The output format — HTML reports, call-prep cards, HubSpot property structure

The intelligence layer is fully portable. Only the trigger and delivery mechanism change.

---

### Migration checklist

When ready to move to cloud:

- [ ] HubSpot MCP key configured and tested (Stage 2)
- [ ] Claude API key provisioned for server-side use
- [ ] Cloud scheduler configured (GitHub Actions or AWS EventBridge)
- [ ] Layer A and B prefetch removed from sweep prompt (no longer needed in cloud)
- [ ] Lark tested on cloud IP — confirm Cloudflare no longer blocks news APIs
- [ ] Report delivery configured (email or Slack) to replace manual distribution
- [ ] HubSpot webhook configured for enrichment trigger (Stage 4, optional)
- [ ] `lark_launch.py` retired or repurposed for local dev/testing only

---

## Questions?

Ask the person who set this up, or open `CLAUDE.md` — it contains Lark's full operating instructions and is the authoritative source on how she works.