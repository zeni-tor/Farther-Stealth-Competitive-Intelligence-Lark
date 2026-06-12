# weekly-sweep.md — Lark Signal-First Sweep Protocol

> Not: "visit each HubSpot contact and see what's new."
> Yes: "scan for signals that fire on contacts in the pipeline."
> If nothing fires, say so. Don't check in on quiet contacts.

---

## The model

Lark does not visit every contact.
8 signal channels run across the active cohort loaded from HubSpot via MCP.
When a signal fires on a contact, that contact's profile lights up.
If no profile exists yet, create one from `profiles/_template.md`.
If nothing fires on a channel, one line: "No activity detected."

The report reflects what actually changed in the pipeline this week —
not a status update on what organizations are generally up to.

A quiet week is short. That is correct.

---

## Phase 1 — Test cohort rules (active now)

- Cohort: 100–500 contacts loaded from HubSpot via MCP
- Signal: SIG-001 (New CFO/Finance Director) only — Channel 1 only
- Purpose: validate signal quality, matching, write-back before full rollout
- Do not run Channels 2–8 until Phase 1 is validated
- Selection criteria for cohort: orgs with known AUM above $5M preferred ·
  orgs with recent 990 activity · any segment team already has conviction on
- Do not run against full 65K until Phase 1 complete

---

## Radar / Telescope rule

Web search is radar — broad, fast, free. Always runs first.
Apify is the telescope — narrow, deep, paid. Only fires when radar
surfaces a LinkedIn URL worth verifying.

**Before any Apify call:** check credit balance and call syntax.
Never scrape proactively.

**LinkedIn URL decision tree:**
```
LinkedIn URL surfaces in search results
         ↓
Is it from a High Priority channel (1, 2, 3)?
         ↓ Yes                    ↓ No
   Always scrape          Is it the ONLY source
   via Apify              confirming this signal?
                               ↓ Yes        ↓ No
                          Scrape it     Log URL only
                          via Apify     Mark Speculative
```

---

## Compound scoring — apply after all channels run

After all active channels complete, score each contact that fired at
least one signal. Read `data/signals.md` for full scoring reference.

```
Score 3 → 2+ High signals, or High + Medium + Contextual
Score 2 → 1 High + 1 Medium, or 2+ Medium signals
Score 1 → Single signal, any tier
```

Score-3 contacts are the highest priority output. Flag prominently.
Always include a recommended outreach angle.

---

## HubSpot write-back (after scoring)

After scoring, write results back to HubSpot via MCP.
Read `data/hubspot-properties.md` before any write.
MCP key: [PENDING] — when available, confirm single-record write works
before running a full cohort sweep.

Write per matched contact:
- lark_signal_type · lark_signal_date · lark_signal_source
- lark_compound_score · lark_score_updated · lark_signals_active
- lark_action_window · lark_contact_status → Signal Detected
- lark_aum_estimated · lark_aum_source (if ProPublica data found)
- lark_incumbent_advisor (if found)
- lark_last_sweep · lark_notes

Write on quiet contacts (no signal fired):
- lark_last_sweep only

---

## The 8 signal channels

Channels 2–8 are defined but inactive during Phase 1.
Only Channel 1 runs until the test cohort is validated.

---

### Channel 1 — Leadership changes · ACTIVE (Phase 1)
**Signals:** SIG-001 (New CFO) · SIG-002 (New CEO/ED) · SIG-005 (New IC chair)
**Purpose:** Has a key decision-maker changed at this org?

**Queries — run for each contact org:**
- `"[org name]" "new" "CFO" OR "chief financial officer" OR "finance director" 2026`
- `"[org name]" "new" "executive director" OR "CEO" OR "president" 2026`
- `"[org name]" "joins" OR "named" OR "appointed" 2026 site:linkedin.com`
- `"[org name]" "investment committee" "chair" OR "chairman" 2026`
- `"[org name]" leadership OR "staff announcement" 2026`

**Phase 1 focus — SIG-001 only:**
During Phase 1 run CFO/finance director queries only. Do not score
SIG-002 or SIG-005 hits until Phase 1 is validated and signals expanded.

**Fires when:** Named leadership change at a contact org confirmed or
strongly inferred from a primary source.
**LinkedIn rule:** High Priority → always scrape via Apify when LinkedIn
URL surfaces. Extract: name, title, previous org, start date, post text.
**Small org note:** Small nonprofits announce hires almost exclusively on
LinkedIn — never discount LinkedIn-only signals.
**Profile action:** Update Leadership section · Update compound score ·
Flag action window in open threads.

---

### Channel 2 — Financial events · INACTIVE (Phase 2)
**Signals:** SIG-003 · SIG-004 · SIG-006 · SIG-007
**Activate after Phase 1 validation.**

---

### Channel 3 — Governance events · INACTIVE (Phase 2)
**Signals:** SIG-005 · SIG-008
**Activate after Phase 1 validation.**

---

### Channel 4 — Strategic signals · INACTIVE (Phase 2)
**Signals:** SIG-009 · SIG-010
**Activate after Phase 1 validation.**

---

### Channel 5 — LinkedIn activity · INACTIVE (Phase 2)
**All signal types — LinkedIn sweep.**
**Activate after Phase 1 validation.**

---

### Channel 6 — Conference presence · INACTIVE (Phase 2)
**Read `data/conferences.md` before running.**
**Activate after Phase 1 validation.**

---

### Channel 7 — 990 and regulatory signals · INACTIVE (Phase 2)
**Signals:** SIG-007 · SIG-010
**Activate after Phase 1 validation.**

---

### Channel 8 — Signal cross-check · ACTIVE (Phase 1, limited)
**Purpose:** Score contacts that fired in Channel 1. Detect patterns.

**Action — Phase 1:**
1. Read `data/signals.md`
2. For each contact that fired SIG-001:
   - Score is automatically Score-1 (single signal)
   - Write score to profile and HubSpot
   - Flag action window: 60–90 days from signal date
3. Look across contacts:
   - Are multiple orgs showing new CFO hires this week?
   - Note as a sector trend in the report if 3+ contacts show same signal

**Always log:** contacts swept · signals processed · score breakdown ·
HubSpot write-back status · Apify calls made

---

## Enrichment (matched contacts only)

Run after a signal fires and org is confirmed matched to HubSpot record.
Never run on unmatched orgs or on the full contact list.

```
Step 1 · ProPublica API (free · every match)
  → search by org name or EIN
  → extract: total assets, revenue, endowment, NTEE code, filing year
  → write to: lark_aum_estimated, lark_aum_source, lark_propublica_ein

Step 2 · Google Drive 990s (high-score only · via MCP)
  → open only for Score-2 or Score-3 contacts
  → extract: Schedule D endowment, incumbent advisor, spending policy

Step 3 · Web fetch (gap fill)
  → org website: leadership page, news, strategic plan
  → fill remaining gaps in the profile
```

---

## Sweep output rules

### If signals fire:
- Report only contacts where something actually happened
- One finding card per signal (use `skills/alert-writer.md` format)
- Score-3 contacts first — always
- Label Apify-sourced LinkedIn data:
  `Source: [org] LinkedIn — [post date] — retrieved via Apify [date]`

### If no signals fire on a channel:
- One line: `Channel [N] — [name]: No activity detected this sweep.`
- Do not fabricate findings

### If HubSpot MCP key is pending:
- Complete the sweep and produce the HTML report normally
- Note at top of report: `HubSpot write-back pending — MCP key not yet
  configured. Findings ready to write when key is available.`
- List all write-back actions that would have been taken

### If Apify credits are low:
- Note in report: `LinkedIn verification unavailable — Apify credits low.
  [N] LinkedIn URLs logged for manual review.`
- List unverified URLs in a gap box

---

## Report structure

```
Lark · Weekly Brief · [DATE]

COHORT: [N] contacts swept · PHASE: [1 / 2]
SIGNALS PROCESSED: [N] · HIGH: [N] · MEDIUM: [N] · CONTEXTUAL: [N] · DISCARDED: [N]
SCORE-3: [N] · SCORE-2: [N] · SCORE-1: [N]
HUBSPOT WRITE-BACK: [Complete / Pending — MCP key not configured]
APIFY CALLS: [N] · CREDITS USED: ~$[X]

SCORE-3 — [Org name] — [signals] — Move immediately
[Finding cards]

SCORE-2 — [Org name] — [signals] — Outreach within 2 weeks
[Finding cards]

SCORE-1 — [Org name] — [signal] — Soft touch
[Finding cards]

CHANNELS WITH NO ACTIVITY: [list]
HUBSPOT WRITE-BACK LOG: [list of records written / pending]
PROFILES UPDATED: [list]
PROFILES CREATED: [list]
Next sweep: [date]
```

---

## Coverage gaps — note when applicable
- HubSpot MCP key pending: write-back staged, not executed
- LinkedIn Ad Library: not accessible via Apify standard actors
- Apify credits exhausted: LinkedIn URLs logged, not scraped
- IRS 990 lag: 12–18 months behind — always state tax year
- Board meeting minutes: not always public
- Gated content: partially inaccessible — never fabricate

---

## What this is not
- Not a status report on what organizations are generally doing
- Not padding with low-signal observations to fill the report
- Not a check-in. An early warning system.
- Not proactive LinkedIn scraping — Apify fires on demand only
- Not geography-specific — Lark is a national agent