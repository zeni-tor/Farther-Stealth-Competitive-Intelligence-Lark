# rfp-intelligence.md — Lark · RFP Intelligence Protocol

> Read this file when running the RFP Intelligence channel (Channel 9).
> This protocol is separate from the monthly signal sweep.
> RFP records serve two purposes: prospect intelligence and research corpus.
> Read honesty.md before any output.

---

## What this is

The RFP Intelligence channel scans for published nonprofit investment
management RFPs — past and present — and builds a structured record of
each one found. This is not a signal channel in the SIG-001 through
SIG-010 sense. Finding an RFP does not automatically trigger outreach.

**Two distinct uses:**

1. **Pipeline match found** — if the org that published the RFP is in
   Farther's 190K contact list, flag it on the org's profile and in the
   report. The RFP history is intelligence for the advisor's call prep:
   we know what this org asked for, how they evaluated, and what they
   weighted. That is a competitive advantage.

2. **No pipeline match** — keep the full record anyway. It goes into
   `HistoricalRFPData/` as research for Farther's RFP creation team.
   Over time this folder becomes a pattern library: what do $5–15M
   transitional housing nonprofits ask for? What do museum foundations
   care about most? What do college foundations weight highest?

Neither use case discards the record. Every RFP found is worth keeping.

---

## When this channel runs

Channel 9 runs during the monthly sweep, after Channels 1–8 complete.
It also runs as a standalone pass when triggered explicitly.

Trigger phrases:
- "Run the RFP intelligence channel"
- "Scan for historical RFPs"
- "Add RFP Intelligence to this sweep"

---

## What to search for

### Primary searches (run every sweep)

These search strings find publicly indexed RFPs. Run all of them.
Date the searches — results shift month to month.

```
"investment management" "request for proposal" nonprofit endowment filetype:pdf 2024 OR 2025 OR 2026
"investment advisory" "request for proposal" foundation filetype:pdf 2024 OR 2025 OR 2026
"OCIO" "request for proposal" nonprofit foundation 2024 OR 2025 OR 2026
"investment management services" RFP nonprofit "$" million endowment 2023 OR 2024 OR 2025
nonprofit "seeking proposals" "investment management" OR "investment advisor" endowment 2024 2025 2026
```

### Pipeline-specific searches (run against HIGH matches from this sweep)

For any org that fired a signal this sweep, run a targeted historical search:

```
"[org name]" "investment" "request for proposal" OR RFP 2019 2020 2021 2022 2023 2024 2025
"[org name]" "investment advisor" OR "investment manager" "selected" OR "chosen" OR "awarded"
"[org name]" investment RFP site:[org domain]
```

### Sector and AUM band searches (rotate monthly — one per sweep)

Each sweep, run one of these broader sweeps to build the research corpus:

Month 1: Transitional housing / social services nonprofits, $1M–$20M
Month 2: Arts and culture / museums, $5M–$50M
Month 3: Community foundations, $5M–$25M
Month 4: College and university foundations, $5M–$50M
Month 5: Healthcare nonprofits, $5M–$100M
Month 6: Environmental / conservation nonprofits, $1M–$25M
(then cycle)

Current month rotation is tracked in memory.md under
`rfp_intelligence_sector_rotation`.

---

## Where to look beyond Google

Small nonprofits ($5–25M) rarely publish RFPs on Google-findable pages.
Check these channels for each search:

- **Org's own website** — procurement or news section. Common URL patterns:
  `/rfp`, `/procurement`, `/bids`, `/news`, `/press`
- **NCFP (ncfp.org)** — National Center for Family Philanthropy. PDFs
  sometimes stay indexed from member distributions
- **Exponent Philanthropy (exponentphilanthropy.org)** — member resource library
- **DemandStar (demandstar.com)** — procurement aggregator. Search by
  category: "Investment Management Services" + nonprofit
- **State nonprofit association websites** — Arizona: aznonprofits.org,
  arizonaphilanthropy.org. Search member RFP bulletin boards
- **Local business journals** — Phoenix Business Journal, etc. — sometimes
  carry procurement notices
- **NACUBO (nacubo.org)** — college and university business officers.
  Member RFP postings for college foundations
- **Council on Foundations (cof.org)** — member bulletin boards
- **Instrumentl (instrumentl.com)** — procurement notices sometimes posted

---

## What to fetch

When a result looks like a real RFP (not a template, not a guide):

1. **Fetch the full document** — PDF or HTML page. Read the whole thing.
2. **Download or cache it** — save raw to `HistoricalRFPData/[slug]-[year]-rfp.pdf`
   or `.html` if no PDF. If the document is not downloadable, note the URL
   and retrieval date.
3. **Build the structured record** — see format below.

If a result is a template, guide, or generic advice article (e.g. PNC's
"Guide to Issuing an RFP") — skip it. These are not RFPs.

How to tell the difference:
- Real RFP: names a specific organization, has a submission deadline,
  states the portfolio size, lists evaluation criteria with weights
- Template / guide: generic org name placeholder, no deadline, no
  specific portfolio size

---

## The RFP record format

Each RFP gets a structured `.md` file in `HistoricalRFPData/`.
Filename: `[org-slug]-[year]-rfp-record.md`

Write every section. If data is not available, write "Not found" —
never leave a section blank or omit it.

---

```markdown
# [Org Name] — Investment Management RFP · [Year]

> Record created: [date]
> Source: [URL or document path]
> Pipeline match: [YES — [canonical CSV name] · [HubSpot Company ID]] OR [NO — research corpus only]
> Raw document: HistoricalRFPData/[slug]-[year]-rfp.pdf (or .html, or "not downloadable — URL on file")

---

## Publisher profile

**Organization:** [full legal name]
**Location:** [city, state]
**Org type / NTEE:** [e.g. Community Foundation, NTEE T31]
**AUM at time of RFP:** $[X]M [source — e.g. stated in RFP, or 990 tax year YYYY]
**Who issued the RFP:** [e.g. Board Finance Committee, CFO, Executive Director]
**Contact person listed:** [name, title, email if provided]
**Date issued:** [date]
**Submission deadline:** [date]
**Decision timeline:** [stated or inferred]

---

## Why they issued

[One paragraph. Use the exact language from the RFP where they explain
their reason for going to market. Is this a first-time search, a periodic
due diligence review, a switch triggered by a specific problem, or a new
endowment? Quote their stated reason if they provided one, then
characterize what it reveals about their situation.

Label: Confirmed (if stated explicitly) / Inferred (if reading between the lines)]

---

## Scope of services requested

[What did they actually ask for? Be specific. Check all of the following
and note which applied:]

- Discretionary management: [Yes / No / Not specified]
- Advisory / non-discretionary: [Yes / No / Not specified]
- OCIO (Outsourced CIO): [Yes / No / Not specified]
- Custody services: [Yes / No / Separate RFP / Not specified]
- IPS development / review: [Yes / No / Not specified]
- Asset allocation recommendations: [Yes / No / Not specified]
- Performance reporting cadence: [Monthly / Quarterly / Other / Not specified]
- Board / investment committee education: [Yes / No / Not specified]
- Planned giving support: [Yes / No / Not specified]
- ESG / SRI requirements: [Yes / Preferred / Not mentioned]
- Minimum AUM requirement stated for respondents: [Yes — $X / No]

---

## The questions (verbatim)

[Reproduce the actual questions from the RFP, organized by section.
Do not summarize or paraphrase — transcribe the questions as written.
This is the primary research value of the record.

Use the same section headers the RFP used. If they had no section headers,
organize by category: Firm Background, Team, Investment Philosophy,
Fees, Reporting, References, Other.]

### [Section A: Firm Background / Organizational Information]

1. [exact question text]
2. [exact question text]
...

### [Section B: Investment Philosophy and Approach]

1. [exact question text]
...

### [Section C: Fees]

1. [exact question text]
...

### [Section D: Reporting]

1. [exact question text]
...

### [Section E: References]

1. [exact question text]
...

### [Additional sections as labeled in the RFP]

---

## Evaluation criteria and weights

[If the RFP stated how proposals would be scored, reproduce the criteria
and weights here exactly. This is critical intelligence.

If no weights were stated, note that and list the criteria as written.]

| Criterion | Weight | Notes |
|---|---|---|
| [criterion] | [X%] | [any additional context from the RFP] |
| [criterion] | [X%] | |
...

**Total:** 100%

[If weights not stated:] Evaluation criteria listed but no weights assigned.

---

## What they got right (Lark's critique — strengths)

[Constructive analysis of what this RFP did well. Be specific.
Write for two audiences: an advisor preparing for a call with this org,
and a team member building a better RFP for Farther's prospects.

Look for:]
- Questions that would genuinely differentiate advisors (not just box-checking)
- Fair and reasonable timelines
- Transparency about portfolio size and current situation
- Clear articulation of why they're going to market
- Asking for references from comparable-size nonprofits specifically
- Asking about staff stability / key person risk
- Asking about fee transparency including underlying fund expenses
- Asking about conflicts of interest
- Providing their IPS as an attachment (gives respondents real context)

---

## What they missed (Lark's critique — gaps)

[Constructive analysis of what the RFP failed to ask or address.
Be specific and honest — the gaps are as useful as the strengths
for understanding how this org thinks about advisors.

Common gaps to check:]
- Did not ask about all-in fees (just advisory fee, missed custody /
  underlying fund expenses)
- Did not ask for references from nonprofits of similar size and mission
  (any nonprofit reference is too broad)
- Did not ask about staff turnover or key-person risk
- Did not provide their IPS — respondents are flying blind on constraints
- Did not ask how the advisor would support board governance and education
- Did not ask about the advisor's approach when performance lags benchmark
- Did not define evaluation criteria or weights — subjective scoring risk
- Unrealistic timeline (less than 2 weeks to respond to a complex RFP)
- No quiet period specified — incumbent advisor may have inside access
- Required minimum AUM of respondents is too high / too low for their portfolio
- Did not ask about transition process if switching from an incumbent

---

## What the weights reveal

[If evaluation criteria and weights were stated, analyze what they reveal
about this org's actual priorities. What matters most to them?
Is this consistent with what you'd expect given their size and situation?
Any surprises?

If no weights were stated, analyze what the question set and ordering
reveal about priorities — what did they lead with, what did they bury?]

---

## What this tells Farther

[One paragraph. Translate the RFP intelligence into something actionable.
Write for an advisor preparing for a first call with this org OR a
similar org in the pipeline.

What did this org most value? What pain were they trying to solve?
What language resonated with them? What would a winning response have
emphasized? What does this suggest about how to position Farther with
a similar prospect?

If this is a pipeline match: make it specific to the named org and
their advisor relationship.

If this is a research corpus entry: make it generalizable — what does
this tell us about orgs of this type and size?]

---

## Pipeline match notes

[If YES pipeline match:]
- Canonical CSV name: [name]
- HubSpot Company ID: [ID]
- Current contact on file: [name, title]
- Current AUM: $[X]M (IRS 990 · tax year [year])
- Current incumbent: [known / unknown]
- Signal history: [any prior signals on this org]
- Recommended action: [what should the advisor know going into a call?]

[If NO pipeline match:]
- Research corpus entry only
- Sector: [NTEE / category]
- AUM band: $[low]M–$[high]M
- Useful for: [e.g. "call prep with transitional housing nonprofits in
  this AUM range" / "RFP creation team — evaluation criteria patterns"]

---

## Source notes

**Retrieved:** [date]
**URL:** [full URL]
**Document type:** [PDF / HTML page / cached copy]
**Still live as of retrieval:** [Yes / No — document has been taken down]
**Confidence in data:** [Confirmed — primary source / Inferred — partial document]
```

---

## The HistoricalRFPData/ index

Maintain a running index at `HistoricalRFPData/_index.md`.
Update it every time a new record is added.

Format:

```markdown
# HistoricalRFPData — Index
Last updated: [date] · [N] records

| Org | Year | AUM | Sector | Pipeline match | File |
|---|---|---|---|---|---|
| [Org name] | [year] | $[X]M | [sector] | YES / NO | [filename] |
...

## By sector
### Social services / transitional housing
- [org] · [year] · $[X]M · [file]

### Arts and culture / museums
...

### Community foundations
...

### College / university foundations
...

## By AUM band
### $1M–$5M
### $5M–$15M
### $15M–$25M
### $25M–$50M
### $50M+

## Pipeline matches
- [org] · [year] · [canonical CSV name] · [HubSpot ID]
```

---

## Report: outputs/YYYY-MM-DD-lark-rfp-intelligence.html

Generate a standalone HTML report. Filename:
`outputs/YYYY-MM-DD-lark-rfp-intelligence.html`

The main monthly report gets a single line in its summary section:
"[N] RFP records added this sweep — see outputs/YYYY-MM-DD-lark-rfp-intelligence.html"
No RFP content appears in the main report.

---

### Report structure

**Page header:**
- Eyebrow: "Lark · RFP Intelligence Report"
- Title: "RFP Intelligence · [Month Year] sweep"
- Meta row: date · records found · pipeline matches · corpus additions

**Summary strip (4 stat cards):**
- RFPs found
- Pipeline matches
- Corpus additions
- AUM range found (e.g. "$6–$9M")

**Section 1 — Pipeline matches**
One full card per RFP where the org is in Farther's pipeline.
Use the full card format below.

**Section 2 — Research corpus additions this sweep**
Simple table: Org | Year | AUM | Sector | Notable (one-line note)
Footer: "Full records in HistoricalRFPData/ · See _index.md for complete corpus"

---

### Full pipeline match card format

Each card has these sections in order. Do not skip sections —
write "Not found" or "Not specified" rather than omitting.

**Card header (masthead):**
- Org name (large)
- Location · org type · NTEE · EIN
- Pipeline match badge (green) OR corpus-only badge (gray)

**Stat strip (4 cells, border-separated):**
- AUM at RFP
- Date issued
- Contract term
- Incumbent (if known, or "Not disclosed")

**Publisher profile section:**
- Contact name, title, email
- Issued by (board, committee, etc.)
- Published via (DemandStar, org website, etc.)

**Selection timeline:**
- Grid of date → event, every milestone from issue to contract start

**Why they issued:**
- Full paragraph using RFP language where available
- Characterize: first-time search / periodic due diligence / switching / new endowment
- Source and confidence label at end

**Scope of services:**
- Checklist grid: each service type with ✓ (included), − (not specified)
- Cover: discretionary management, OCIO, custody, IPS development, reporting cadence,
  board attendance, board education, ESG, planned giving, personnel notifications

**Questions — verbatim:**
- Organized by the RFP's own section letters and titles
- Every question reproduced exactly as written
- Source note at bottom: "Verbatim · RFP Section [X] · [date] · Confirmed"

**Evaluation criteria and weights:**
- Bar chart layout: criterion label | proportional bar | percentage
- If weights stated: reproduce exactly, total to 100%
- If weights not stated: list criteria as written, note "No weights assigned"
- Source note

**Lark's critique — two-column layout:**

Left column — "What they got right":
- Bullet list of genuine strengths
- Be specific — name the question or section, not just "good process"
- Common things to look for that earn a positive note:
  IPS provided as attachment · published weights · nonprofit-specific references ·
  sample reports required · board education in scope · personnel change notification ·
  efficient frontier or long-horizon return data requested · conflict of interest asked ·
  all-in fees requested · transition process addressed · quiet period specified

Right column — "What they missed":
- Bullet list of genuine gaps
- Be constructive and specific — explain why the gap matters
- Common gaps to check:
  All-in fees not asked (advisory only, missing custody/fund expenses) ·
  References too broad (any nonprofit vs. similar size and type) ·
  No IPS attached (respondents flying blind) · No key-person/turnover question ·
  No conflict-of-interest question · No transition process question ·
  Timeline too short for quality responses · Geographic restriction may exclude
  better-qualified firms · Credit rating ask (unusual for RIAs) ·
  No ESG / SRI question · No question about underperformance response

**What the weights reveal:**
- Paragraph analyzing what the scoring structure tells us about the org's priorities
- What did they weight highest? Is that surprising given their size or situation?
- Did any factions show up in tied weights?
- Does the weight order match the question emphasis?
- Note if board reserves right to go beyond stated criteria (limits weight reliability)

**What this tells Farther:**
- One substantial paragraph — the so-what
- Written for an advisor preparing for a call with this org or a similar one
- What did they value most? What pain were they solving?
- What would a winning response have led with?
- How should Farther position against this org type?
- What governance or service offer would differentiate without competing on scored criteria?

**Pipeline match notes:**
- Label/value grid: status · contact · selection status · incumbent ·
  next RFP window · recommended action

**Card action buttons:**
- "Add to [year] watch list ↗" → sendPrompt to update memory.md
- "Find similar RFPs ↗" → sendPrompt to search for comparable orgs
- "← Back" → sendPrompt to return to report index

---

### Design guidance

The RFP report must use the **same design system as `lark_report.py`** — same CSS
variables, same masthead, same stats bar, same card structure, same color tokens.
A reader opening both reports should immediately recognise they come from the same
system.

Copy the following CSS block exactly into the `<style>` tag of every RFP report:

```css
:root {
  --bg: #f5f4ef; --surface: #ffffff; --dark: #1a1916;
  --mid: #5a5852; --light: #a8a49e; --border: #e2e0d8;
  --green: #3d6b4f; --amber: #c8861a; --alert-red: #8b2222;
  --tag-ambiguous: #5a5852; --score1-bg: #3d6b4f; --info-blue: #2b5278;
  --clay: #9B4E1E; --clay2: #B5622A; --clay-pale: #E8C9A0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg); color: var(--dark); line-height: 1.55; font-size: 14px; }

/* ── Masthead (identical to monthly report) ── */
.masthead { background: var(--dark); color: var(--bg); padding: 28px 40px 24px;
  border-bottom: 3px solid var(--clay); }
.masthead-eyebrow { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--light); margin-bottom: 6px; }
.masthead-title { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 4px; }
.masthead-sub { font-size: 13px; color: var(--light); }
.stats-bar { background: var(--dark); border-top: 1px solid rgba(255,255,255,0.08);
  padding: 12px 40px; display: flex; gap: 32px; flex-wrap: wrap; }
.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--light); }
.stat-value { font-size: 18px; font-weight: 700; color: var(--bg); }
.stat-value.green { color: #6bcf8f; }
.stat-value.amber { color: #f0b84a; }
.stat-value.dim { color: var(--light); }

/* ── Main content area ── */
.main { max-width: 900px; margin: 0 auto; padding: 24px 40px 60px; }
.section-header { display: flex; align-items: center; gap: 12px; margin: 32px 0 16px;
  padding-bottom: 10px; border-bottom: 2px solid var(--border); }
.section-tag { padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; color: #fff; }
.tag-match { background: var(--clay); }
.tag-corpus { background: var(--mid); }
.tag-sector { background: var(--info-blue); }
.section-title { font-size: 16px; font-weight: 600; color: var(--dark); }

/* ── RFP cards ── */
.card { background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; margin-bottom: 20px; overflow: hidden; }
.card-header { padding: 16px 20px 12px; border-bottom: 1px solid var(--border);
  display: flex; align-items: flex-start; gap: 14px; background: #f9f8f4; }
.card-org-name { font-size: 18px; font-weight: 700; letter-spacing: -0.01em; }
.card-org-sub { font-size: 12.5px; color: var(--mid); margin-top: 2px; }
.card-body { padding: 16px 20px; }

/* Match badges */
.badge-match { padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: 700;
  letter-spacing: 0.06em; color: #fff; background: var(--green); white-space: nowrap; }
.badge-corpus { padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: 700;
  letter-spacing: 0.06em; color: #fff; background: var(--mid); white-space: nowrap; }
.badge-archived { padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: 700;
  letter-spacing: 0.06em; color: #fff; background: var(--amber); white-space: nowrap; }

/* Stat strip inside card */
.card-stats { display: flex; border-bottom: 1px solid var(--border); }
.card-stat { flex: 1; padding: 10px 16px; border-right: 1px solid var(--border); }
.card-stat:last-child { border-right: none; }
.card-stat-label { font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--mid); margin-bottom: 2px; }
.card-stat-value { font-size: 13px; font-weight: 700; color: var(--dark); }

/* Section blocks within a card */
.card-section { padding: 14px 20px; border-bottom: 1px solid var(--border); }
.card-section:last-child { border-bottom: none; }
.card-section-title { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--mid); margin-bottom: 8px; }
.card-section p { font-size: 13px; color: var(--dark); line-height: 1.65; }

/* Verbatim questions */
.q-group { margin-bottom: 14px; }
.q-group-title { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--info-blue); border-bottom: 1px solid var(--border);
  padding-bottom: 4px; margin-bottom: 8px; }
.q-item { display: flex; gap: 10px; font-size: 13px; line-height: 1.6;
  padding: 4px 0; border-bottom: 1px solid #f0ede8; }
.q-item:last-child { border-bottom: none; }
.q-num { color: var(--mid); min-width: 28px; flex-shrink: 0; font-variant-numeric: tabular-nums; }

/* Evaluation weights */
.weight-row { display: flex; align-items: center; gap: 10px; padding: 5px 0;
  border-bottom: 1px solid var(--border); font-size: 13px; }
.weight-row:last-child { border-bottom: none; }
.weight-label { flex: 1; color: var(--dark); }
.weight-bar-bg { width: 100px; height: 6px; background: var(--border);
  border-radius: 3px; flex-shrink: 0; }
.weight-bar-fill { height: 6px; background: var(--clay); border-radius: 3px; opacity: 0.75; }
.weight-pct { font-weight: 700; color: var(--mid); min-width: 36px; text-align: right; font-size: 12px; }

/* Critique two-column */
.critique-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 4px; }
.critique-box { background: #f9f8f4; border: 1px solid var(--border); border-radius: 4px;
  padding: 12px 14px; }
.critique-title { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; margin-bottom: 8px; display: flex; align-items: center; gap: 5px; }
.critique-title.pos { color: var(--green); }
.critique-title.neg { color: var(--amber); }
.critique-item { display: flex; gap: 7px; font-size: 12.5px; color: var(--mid);
  line-height: 1.55; padding: 3px 0; }
.critique-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.critique-dot.pos { background: var(--green); }
.critique-dot.neg { background: var(--amber); }

/* Farther insight box */
.insight-box { background: #edf7f0; border-left: 4px solid var(--green);
  padding: 14px 18px; border-radius: 0 4px 4px 0; font-size: 13px;
  color: #2d4a38; line-height: 1.65; margin-top: 4px; }
.insight-box strong { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--green); display: block; margin-bottom: 4px; }

/* Pipeline match notes */
.match-grid { display: grid; grid-template-columns: 160px 1fr; gap: 5px 14px;
  font-size: 13px; margin-top: 4px; }
.match-label { color: var(--mid); }
.match-value { color: var(--dark); }

/* Corpus table */
.corpus-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
.corpus-table th { text-align: left; font-size: 11px; letter-spacing: 0.07em;
  text-transform: uppercase; color: var(--mid); padding: 6px 10px 8px 0;
  border-bottom: 2px solid var(--border); font-weight: 700; }
.corpus-table td { padding: 8px 10px 8px 0; border-bottom: 1px solid var(--border);
  color: var(--dark); vertical-align: top; }
.corpus-table tr:last-child td { border-bottom: none; }

/* Sector rotation table */
.sector-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
.sector-table th { text-align: left; font-size: 11px; letter-spacing: 0.07em;
  text-transform: uppercase; color: var(--mid); padding: 6px 12px 8px;
  border-bottom: 2px solid var(--border); font-weight: 700; background: #f9f8f4; }
.sector-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
.sector-table tr.current { background: #fff8ee; }
.sector-table tr.current td { font-weight: 500; }

/* Coverage gaps (matches monthly report) */
.gap-section { background: #fff8ee; border: 1px solid #f0d4a0; border-radius: 6px;
  padding: 16px 20px; margin-top: 24px; }
.gap-section h3 { font-size: 13px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--amber); margin-bottom: 10px; }
.gap-section ul { list-style: none; padding: 0; }
.gap-section li { font-size: 13px; color: var(--dark); padding: 3px 0 3px 16px; position: relative; }
.gap-section li::before { content: '—'; position: absolute; left: 0; color: var(--amber); }

/* Footer (identical to monthly report) */
.footer { background: var(--dark); color: var(--light); padding: 18px 40px;
  font-size: 11.5px; border-top: 1px solid rgba(255,255,255,0.08); margin-top: 40px;
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
```

**Masthead structure:**
```html
<div class="masthead">
  <div class="masthead-eyebrow">Farther Institutional · RFP Intelligence</div>
  <div class="masthead-title">🪶 Lark · RFP Intelligence Report</div>
  <div class="masthead-sub">
    Sweep #[N] · [DATE] · Lookback: [DATE] – [DATE]<br>
    Sector rotation: Month [N] — [sector] · [AUM band]<br>
    Separate from the monthly signal report.
  </div>
</div>
<div class="stats-bar">
  <div class="stat-item">
    <span class="stat-label">Searches run</span>
    <span class="stat-value">[N]</span>
  </div>
  <div class="stat-item">
    <span class="stat-label">RFPs identified</span>
    <span class="stat-value green">[N]</span>
  </div>
  <div class="stat-item">
    <span class="stat-label">Pipeline matches</span>
    <span class="stat-value amber">[N]</span>
  </div>
  <div class="stat-item">
    <span class="stat-label">Corpus total</span>
    <span class="stat-value dim">[N]</span>
  </div>
</div>
```

**Footer structure:**
```html
<div class="footer">
  <div>Lark · RFP Intelligence · Farther Institutional</div>
  <div>Sweep #[N] · Generated [DATE]</div>
  <div>Next sector: Month [N] · [sector]</div>
</div>
```

Note: the monthly report uses a green `border-bottom` on the masthead. The RFP
report uses clay (`--clay`) to visually distinguish the two reports at a glance.

---

## What this channel does NOT do

- Does NOT automatically trigger outreach — finding an RFP is not a SIG
- Does NOT score contacts based on RFP history alone
- Does NOT discard records where there is no pipeline match
- Does NOT attempt to reconstruct RFPs from partial information —
  if the full document is not accessible, note what was found and move on
- Does NOT fabricate evaluation criteria or questions —
  if partial, label as partial and note what is missing

---

## File naming conventions

```
HistoricalRFPData/
  _index.md                                    ← running index (Lark maintains)
  [org-slug]-[year]-rfp.pdf                   ← raw document (if fetchable)
  [org-slug]-[year]-rfp.html                  ← raw page (if PDF not available)
  [org-slug]-[year]-rfp-record.md             ← full structured record
```

Org slug: lowercase, hyphens, no special characters.
Examples:
  house-of-refuge-2022-rfp-record.md
  st-johns-river-state-college-foundation-2024-rfp-record.md
  community-foundation-south-puget-sound-2023-rfp-record.md

---

## Coverage gaps — always note

- Most $5–25M nonprofits do not publish RFPs publicly — they shop by
  referral. Absence of an RFP record does not mean the org has never
  run an advisor search.
- RFPs are often taken down after selection. A URL that returns 404
  may have been a live RFP in the past. Note the source and date if
  secondary evidence (press release, advisor announcement) confirms
  an RFP occurred.
- 990 Schedule D can sometimes confirm an advisor change even when no
  RFP was published — investment fees appearing or disappearing,
  or a new manager named in footnotes.
- RFP documents are point-in-time. The org's priorities may have
  evolved since the document was published.