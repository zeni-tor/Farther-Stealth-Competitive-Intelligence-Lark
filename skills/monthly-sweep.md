# monthly-sweep.md — Lark Signal-First Sweep Protocol

> NOT EVER!: "visit each contact and see what's new."
> Yes: "scan the world for signals, match against the pipeline."
> If nothing fires, say so. Don't check in on quiet contacts.

---

## The model

Lark does not loop through contacts.
Signal channels scan the world broadly for nonprofit events.
When a signal fires, the org name is extracted and matched against
the contacts CSV using the fuzzy matcher.
If a match is confirmed, that contact's profile lights up.
If no profile exists yet, create one from `profiles/_template.md`.
If nothing fires on a channel, one line: "No activity detected."

The report reflects what actually changed in the market this month —
not a status update on what organizations are generally up to.

A quiet month is short. That is correct.

```
SIGNAL SCAN (broad) → ORG EXTRACTION → FUZZY MATCH → ENRICH → SCORE → REPORT
```

---

## Current sweep configuration

### Always state the date explicitly
Claude Code does not always know the current date reliably.
Include today's date and lookback window in every sweep prompt.

**Standard monthly sweep prompt:**
```
Run a full signal sweep. All channels active including Channel 5 (LinkedIn/Apify).

Today's date: [DATE]

Lookback window: past 30 days ([DATE-30] – [DATE])

Use contact_data/contacts.csv. Load the fuzzy matcher once, run all
searches first (including LinkedIn via Apify), then run Phase 2 by
writing all_signals to /tmp/lark_signals.json and running
python3 utilities/lark_run_matcher.py as a standalone script.
Wait for MATCH_BATCH_COMPLETE to print before proceeding to Phase 3.
Do not use inline python3 -c for match_batch().
Each signal in all_signals[] must be a dict with keys: org_name, domain,
signal_type, channel, source_url, finding_text, signal_date, confidence.
Deduplicate all_signals[] before calling match_batch().
Do not read the contact list directly.
Ask if anything is unclear before starting.
```

**First sweep / catch-up sweeps:**
```
Run a full signal sweep. All channels active including Channel 5 (LinkedIn/Apify).

Today's date: [DATE]
Lookback window: past 30 days ([DATE-30] – [DATE])
Use contact_data/contacts.csv. Load the fuzzy matcher once, run all
searches first (including LinkedIn via Apify), then run Phase 2 by
writing all_signals to /tmp/lark_signals.json and running
python3 utilities/lark_run_matcher.py as a standalone script.
Wait for MATCH_BATCH_COMPLETE to print before proceeding to Phase 3.
Do not use inline python3 -c for match_batch().
Each signal in all_signals[] must be a dict with keys: org_name, domain,
signal_type, channel, source_url, finding_text, signal_date, confidence.
Deduplicate all_signals[] before calling match_batch().
Do not read the contact list directly.
Ask if anything is unclear before starting.
```

All channels 1–8 active. Channel 5 runs via Apify — confirm APIFY_TOKEN is set.
Channel 9 (RFP Intelligence) runs automatically after Channels 1–8 — no extra prompt needed.
Full signal sweep — all 10 signals active.

```
All sweeps    → All channels 1–8 active (SIG-001 through SIG-010)
Channel 5     → LinkedIn/Apify · requires APIFY_TOKEN env var
Channel 9     → RFP Intelligence · runs after Channels 1–8 · see skills/rfp-intelligence.md
Phase 2       → HubSpot MCP live                 ← separate milestone
```

---

## Contact source

Contacts are loaded from `contact_data/` CSV — not from HubSpot via MCP.
HubSpot MCP key is pending. Write-back is staged to CSV output only.

```python
from utilities.lark_fuzzy_matcher import LarkMatcher
matcher = LarkMatcher("contact_data/contacts.csv")
result  = matcher.match(org_name, domain=domain)
```

Fuzzy matcher thresholds (validated 2026-06-16):
- HIGH ≥ 80     → confirmed match → proceed to enrichment
- AMBIGUOUS 50–79 → flag for manual review
- - NO_MATCH < 50  → AMBIGUOUS (flagged for human review — never silently discarded)

---


## HubSpot write-back (after scoring)

MCP key: PENDING — stage all write-back in CSV output.
Do not attempt MCP calls until key is configured.
Read `data/hubspot-properties.md` before writing any field.

**Write per matched contact (to CSV):**
- lark_signal_type · lark_signal_date · lark_signal_source
- lark_compound_score · lark_score_updated · lark_signals_active
- lark_action_window · lark_contact_status → Signal Detected
- lark_aum_estimated · lark_aum_source (if ProPublica data found)
- lark_incumbent_advisor (if found)
- lark_last_sweep · lark_notes

**Write on quiet contacts:**
- lark_last_sweep only

---

## The 8 signal channels

---

### Channel 1 — Leadership changes · ACTIVE
**Signals:** SIG-001 · SIG-002 · SIG-005
**All signals active from sweep 1.**

**Web search queries — broad national scan:**
```
"nonprofit" "new CFO" OR "new chief financial officer" 2026
"nonprofit" "new finance director" OR "finance director joins" 2026
"foundation" OR "endowment" "named CFO" OR "appointed CFO" 2026
"nonprofit" "CFO" "joins" OR "named" OR "appointed" site:prnewswire.com OR site:businesswire.com 2026
"nonprofit" "new" "vice president of finance" OR "VP finance" OR "director of finance" 2026
```

**SIG-002 / SIG-005 queries:**
```
"nonprofit" "new executive director" OR "new CEO" 2026
"nonprofit" "executive director" "joins" OR "named" OR "appointed" 2026
"foundation" "new" "investment committee" "chair" 2026
```

**Fires when:** Named leadership change confirmed or strongly inferred
from a primary non-LinkedIn source.
**Small org note:** Small org hires announced only on LinkedIn are now
caught by Channel 5 (Apify). Channel 5 signals are Inferred — confirm
via org website or press release before labeling Confirmed.
**Profile action:** Update Leadership section · compound score · action window.

---

### Channel 2 — Financial events · ACTIVE
**Signals:** SIG-003 · SIG-004 · SIG-006 · SIG-007

**Web search queries:**
```
"nonprofit" "capital campaign" "raised" OR "goal" OR "complete" OR "close" 2026
"foundation" OR "endowment" "gift" OR "bequest" OR "pledge" "$" million 2026
"nonprofit" "capital campaign" "launch" OR "announces" 2026
"endowment" "million" site:prnewswire.com OR site:businesswire.com 2026
"nonprofit" "largest gift" OR "transformative gift" OR "legacy gift" 2026
```

**ProPublica 990 queries (SIG-007):**
Search by EIN or org name for AUM threshold crossing.
Always state tax year — 990 data is 12–18 months behind.

---

### Channel 3 — Governance events · ACTIVE
**Signals:** SIG-005 · SIG-008

**Web search queries:**
```
"nonprofit" "merger" OR "merge" OR "consolidation" OR "affiliation" 2026
"nonprofit" "board" "restructur" OR "reorganiz" 2026
"foundation" "investment committee" "new chair" OR "restructur" 2026
```

---

### Channel 4 — Strategic signals · ACTIVE
**Signals:** SIG-009 · SIG-010

**Web search queries:**
```
"nonprofit" "strategic plan" "endowment" 2026
"nonprofit" "endowment" "establish" OR "launch" OR "first" 2026
"foundation" "grow endowment" OR "permanent endowment" OR "endowment goal" 2026
```

**Watch for:** Language like "grow endowment to $X by [year]" —
plans without explicit investment language do not fire.

---

### Channel 5 — LinkedIn / Apify · ACTIVE
**Signals:** SIG-001 · SIG-002 · SIG-005
**Runner:** `from utilities.lark_linkedin_channel import run_linkedin_sweep`

Detects small org leadership hires announced only on LinkedIn — the primary
coverage gap for orgs that never issue press releases. Runs 6 queries via
Apify Profile Search (harvestapi~linkedin-profile-search): Director of Finance,
CFO, VP Finance, Executive Director, President & CEO, CIO. Short mode, 2 pages
each (~50 profiles/query), recentlyChangedJobs=true. Targets headcount B/C/D
(1–200 employees). Cost: ~$1.20/month.

**Lookback window note:** LinkedIn's recentlyChangedJobs filter covers the
past 90 days — wider than Lark's standard 30-day sweep window. Signals older
than 30 days that surface through Channel 5 should be checked against their
action window before scoring. A SIG-001 that is 75 days old may have an
expired or closing window.

**Confidence:** Channel 5 signals are always Inferred. LinkedIn is a
self-reported source. Confirm via org website or press release before
labeling Confirmed or recommending outreach.

---

### Channel 6 — Conference presence · ACTIVE
Read `data/conferences.md` before running.
Only run for conferences in active monitoring window.

**Queries per org in monitoring window:**
```
"[conference name]" "[org name]" speaker OR presenter OR panelist [year]
"[conference name]" "[org name]" attending OR registration [year]
```

---

### Channel 7 — 990 and regulatory signals · ACTIVE
**Signals:** SIG-007 · SIG-010

ProPublica API — free, no key required:
```
https://projects.propublica.org/nonprofits/api/v2/search.json?q=[ORG]
https://projects.propublica.org/nonprofits/api/v2/organizations/[EIN].json
```

Extract: total assets · NTEE code · tax year · EIN
Always state tax year. Never present 990 AUM as current.

---

### Channel 8 — Signal cross-check · ACTIVE (all sweeps)
**Purpose:** Score orgs that fired in active channels. Detect patterns.

**Action:**
1. Read `data/signals.md`
2. For each org that fired a signal:
   - Calculate compound score
   - Write score to profile
   - Flag action window from signal date
3. Look across all hits:
   - Are 3+ orgs showing the same signal this sweep?
   - Note as a sector trend in the report
4. Flag Score-3 contacts prominently

**Always log:** signals processed · score breakdown ·
HubSpot write-back status (STAGED) · coverage gaps

---

## Enrichment (matched contacts only)

Run after a signal fires and org is confirmed HIGH match.
Never run on unmatched orgs or AMBIGUOUS matches.

```
Step 1 · ProPublica API (free · every HIGH match)
  URL: https://projects.propublica.org/nonprofits/api/v2/search.json?q=[ORG]
  Extract: total_assets · ntee_code · tax_prd_yr · ein · state
  Write: lark_aum_estimated · lark_aum_source · lark_propublica_ein
  If no result: log as gap — do not estimate

Step 2 · Org website (mission, leadership, board, campaigns)
  Fetch the org's website. Look for:
  - About page: mission statement, programs, communities served
  - Leadership page: current CFO, CEO, board chair, IC chair
  - Board page: full board list — flag any recognizable names
  - News / press releases: campaigns, gifts, strategic plans, new programs,
    new facilities, annual reports
  Fill: hire confirmation · endowment status · campaign status · board list

Step 3 · Recent news search (talking points)
  Search: "[org name]" recent news [year]
  Also search:
    "[org name]" "capital campaign" OR "campaign goal"
    "[org name]" "strategic plan"
    "[org name]" "new" "director" OR "president" OR "CEO"
    "[org name]" "new building" OR "renovation" OR "expansion"
  Prioritize results from the past 6 months.
  If nothing recent, go back 12 months and note the age.
  If nothing meaningful found: log explicitly — do not fabricate a hook.

Step 4 · Google Drive 990s (Phase 2 · via MCP when live)
  Activate when MCP key is configured.
```

---

### Channel 9 — RFP Intelligence · ACTIVE
**Protocol:** `skills/rfp-intelligence.md`
**Runs:** After Channels 1–8 complete — every sweep, automatically.

Scans for published nonprofit investment management RFPs — past and present.
Builds structured records in `HistoricalRFPData/`. Does NOT score contacts
or trigger outreach. Produces a separate HTML report.

**Each sweep:**
1. Run the primary RFP searches from rfp-intelligence.md
2. Run the current month's sector rotation search (check memory.md for current sector)
3. For any HIGH match orgs from this sweep, run a targeted historical RFP search
4. Fetch any real RFPs found, build structured records, save to HistoricalRFPData/
5. Update HistoricalRFPData/_index.md
6. Generate outputs/YYYY-MM-DD-lark-rfp-intelligence.html
7. Update memory.md: rfp_intelligence_sector_rotation · last RFP scan · corpus count

**Monthly report:** Add one line to the main report summary only:
"Channel 9: [N] RFP records found · [N] pipeline matches · see outputs/YYYY-MM-DD-lark-rfp-intelligence.html"
No RFP card content in the main report.

Compound scoring is Lark's judgment call — not a script. After all channels
run, reason through each matched org's signal stack and assign a score.
The rubric below is the floor; apply judgment above it.

**Base scoring rules:**

```
Score 3 → 2+ High signals, or High + Medium + Contextual
Score 2 → 1 High + 1 Medium, or 2+ Medium signals
Score 1 → Single signal, any tier
```

**Signal strength — reason within the tier:**

SIG-001 (New CFO / Finance Director):
- Strongest: external hire + "investment oversight" or "endowment management"
  in the job posting or announcement
- Weaker: internal promotion, no investment language
- Upgrade consideration: external hire + AUM ≥ $5M → treat as Score-2 candidate
  even without a second signal

SIG-002 (New CEO / Executive Director):
- Strongest: external hire + announcement language includes "strategic reset,"
  "new direction," or "transformation" + prior ED had long tenure (7+ years)
- Weaker: internal promotion, board member stepping in as interim
- Interim designation is a weaker form — note as such, and watch for permanent
  hire confirmation next sweep (confirmation upgrades the score)

SIG-003 (Capital Campaign Close):
- Strongest: oversubscribed + endowment component explicitly named
- Standard: campaign completed at or near goal
- Context check: what was the org's endowment before the campaign? A $3M → $28M
  jump is a Score-3 candidate on its own regardless of other signals

SIG-004 (Large Gift / Bequest):
- $5M+: floor is Score-3 regardless of other signals — rivals see the same
  press release; move immediately
- $1M–$5M: standard High
- $500K–$1M: only consider Score-2 if the paired signal is Confirmed, not
  Inferred — a LinkedIn-only second signal does not qualify

**Context modifiers — adjust up or down:**

Reason UP (consider raising score by one) when:
- Org is 990PF with investments > $5M — investment management is core to
  operations, not incidental
- No advisor change on record for 3+ years — entrenchment creates review
  motivation when a new leader arrives
- Org's investments-to-total-assets ratio is high — the advisor relationship
  is central to how the org operates
- Two signals both fall within their active action windows in this sweep

Reason DOWN (hold or note as weaker) when:
- Signal source is LinkedIn only — label Inferred, not Confirmed; do not
  recommend outreach without a non-LinkedIn corroboration
- Org is near the $1M AUM floor — the advisory fee is likely too small to
  justify the sales cycle
- SIG-001 signal was an internal promotion with no investment language in
  the announcement — still worth tracking, but below the threshold for
  immediate outreach

**Window alignment:**

Signals that fire within the same sweep compound more strongly than signals
separated by months. A SIG-003 and SIG-001 in the same sweep = Score-3
unless both individually show weaknesses.

SIG-007 (AUM threshold) and SIG-010 (First-Time Endowment) always confirm,
never lead. They only contribute to Score-2 or Score-3 when paired with a
fresher signal from this sweep. Either signal alone is not an outreach trigger.

SIG-009 (New Strategic Plan) is Contextual — it creates a talking point,
not an action window. Confirm endowment language before treating it as a
signal at all. Only contributes to scoring when stacked with a High signal.

**Score-3 contacts are the highest priority output.** Always first in both
the Slack summary and the HTML report. Include a specific one-sentence outreach
angle tied to the exact signal combination — not a generic opener.

---

## Output rules

### If signals fire:
- Report only orgs where something actually happened
- Score-3 first, then Score-2, then Score-1
- Label every finding: Confirmed / Inferred / Speculative
- One finding card per signal per org

### If nothing fires:
- One line per channel: `Channel [N]: No activity detected.`
- Do not fabricate findings — quiet sweep is correct

### On LinkedIn signals:
- Channel 5 (Apify) results: always label Inferred — requires non-LinkedIn
  corroboration before labeling Confirmed or recommending outreach
- LinkedIn URL found during web search (other channels): do not scrape —
  mark the signal Speculative and note it; Channel 5 is the correct LinkedIn
  detection path

### If HubSpot MCP key is pending:
- Complete sweep and report normally
- Output write-back CSV to `outputs/`
- Note in report: `HubSpot write-back staged — MCP key pending`

---

## Report structure

```
Lark · Monthly Brief · [DATE]

SWEEP: [N] · PHASE: 1
CHANNELS ACTIVE: 1–9 · CHANNEL 5: LinkedIn/Apify (requires APIFY_TOKEN)
SIGNALS: [N] raw hits · HIGH: [N] · AMBIGUOUS: [N] · DISCARDED: [N]
SCORES: Score-3: [N] · Score-2: [N] · Score-1: [N]
HUBSPOT: STAGED — MCP key pending · [N] records queued
CHANNEL 9: [N] RFP records found · [N] pipeline matches · see outputs/YYYY-MM-DD-lark-rfp-intelligence.html
COVERAGE: [list any active gaps this sweep]

[Score-3 finding cards]
[Score-2 finding cards]
[Score-1 finding cards]
[AMBIGUOUS review list]
[Channels with no activity]
[Coverage gaps]
[HubSpot write-back log — staged]
```

Each finding card includes a **call-prep section** beneath the signal summary.
The goal of the first call is a second meeting:
"I would love to set up time to visit and learn more about the work you all are doing."

**Finding card format:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ORG NAME] · Score-[N] · [signal type]
[City, State] · AUM: $[X]M (IRS 990 · tax year [year]) · EIN: [number]
Incumbent advisor: [firm or Unknown]
Signal: [finding text] · [date] · [Confirmed / Inferred] · [source URL]
Action window: [window] · HubSpot: STAGED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MISSION
  [1–2 sentences on what this org is focused on and who they serve.
   Source: org website About page. Label: Confirmed / Inferred.]

FUNDRAISING
  Capital campaigns:  [active / recent / none known · name · goal · status]
  Recent major gifts: [if found — amount, purpose, source]

FINANCIAL HEALTH (IRS 990 · tax year [year])
  Revenue:    $[X]M   YoY: [+X% / -X% / flat / unknown]
  Expenses:   $[X]M   Budget: [balanced / surplus / deficit]
  Net assets: $[X]M   Trend: [growing / flat / declining]

BOARD (from org website · retrieved [date])
  [Board member list with titles]
  Notable: [Name · Title · why worth referencing on the call, if applicable]

TALKING POINTS — why reach out today
  [2–3 items. Each: what happened · when · source · Confirmed/Inferred/Speculative.
   If nothing recent found: state explicitly — do not fabricate a hook.]
  1. [Hook] — [date] — [source] — [confidence]
  2. [Hook] — [date] — [source] — [confidence]

CALL CONTACT
  ED / CEO:  [name · title · source]
  CFO:       [name · title · source]
  IC Chair:  [name · title · source]

OPEN THREADS
  - [anything unresolved before outreach]
```

---

## Coverage gaps — always note when applicable
- HubSpot write-back staged — MCP key pending
- IRS 990 lag — 12–18 months behind, always state tax year
- Board meeting minutes not always public
- Gated content partially inaccessible — never fabricate

---

## What this is not
- Not a status report on what organizations are generally doing
- Not looping through contacts asking "did anything happen to you?"
- Not padding with low-signal observations to fill the report
- Not a check-in. An early warning system.
- Not geography-specific — Lark is a national agent