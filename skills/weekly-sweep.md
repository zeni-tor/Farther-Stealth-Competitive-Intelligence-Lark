# weekly-sweep.md — Lark Signal-First Sweep Protocol

> Not: "visit each HubSpot contact and see what's new."
> Yes: "scan for signals that fire on contacts in the pipeline."
> If nothing fires, say so. Don't check in on quiet contacts.

---

## The model

Every HubSpot contact in `data/contacts.md` does not get visited.
8 signal channels get run across the full contact list.
When a signal fires on a contact, that contact's profile lights up.
If no profile exists yet, create one from `profiles/_template.md`.
If nothing fires on a channel, one line: "No activity detected."

The report reflects what actually changed in the pipeline this week —
not a status update on what 50 organizations are generally up to.

A quiet week is short. That is correct.

---

## Radar / Telescope rule

Web search is radar — broad, fast, free. Always runs first.
Apify is the telescope — narrow, deep, paid. Only fires when radar
surfaces a LinkedIn URL worth verifying.

**Before any Apify call:** read `data/apify-config.md` for credit balance,
tier thresholds, and call syntax. Never scrape proactively.

**LinkedIn URL decision tree:**
```
LinkedIn URL surfaces in search results
         ↓
Is it from a High Priority channel (1, 2, 3, 5)?
         ↓ Yes                    ↓ No
   Always scrape          Is it the ONLY source
   via Apify              confirming this signal?
                               ↓ Yes        ↓ No
                          Scrape it     Log URL only
                          via Apify     Mark Speculative
```

---

## Compound scoring — apply after all channels run

After Channels 1–8 have completed, score each contact that fired at
least one signal. Read `data/signals.md` for full scoring reference.

```
Score 3 → 2+ High signals, or High + Medium + Contextual
Score 2 → 1 High + 1 Medium, or 2+ Medium signals
Score 1 → Single signal, any tier
```

Score-3 contacts are the highest priority output. Flag prominently in
both Slack and HTML report. Always include a recommended outreach angle.

---

## The 8 signal channels

Run these queries every sweep against every contact in `data/contacts.md`.
Each channel maps to one or more named signals in `data/signals.md`.

---

### Channel 1 — Leadership changes
**Signals:** SIG-001 (New CFO) · SIG-002 (New CEO/ED) · SIG-005 (New IC chair)
**Purpose:** Has a key decision-maker changed at this org?

**Queries — run for each contact org:**
- `"[org name]" "new" "CFO" OR "chief financial officer" OR "finance director" 2026`
- `"[org name]" "new" "executive director" OR "CEO" OR "president" 2026`
- `"[org name]" "joins" OR "named" OR "appointed" 2026 site:linkedin.com`
- `"[org name]" "investment committee" "chair" OR "chairman" 2026`
- `"[org name]" leadership OR "staff announcement" OR "team" 2026`

**Fires when:** Named leadership change at a contact org confirmed or
strongly inferred from a primary source
**LinkedIn rule:** High Priority channel → always scrape via Apify when
LinkedIn URL surfaces · extract: name, title, previous org, start date,
post text, engagement, top comments
**Small org note:** Small nonprofits announce hires almost exclusively on
LinkedIn — do not discount LinkedIn-only signals. A post with low engagement
from a $3M community foundation is still a High Priority signal.
**Profile action:** Update Leadership section · Update compound score ·
Flag action window in open threads

---

### Channel 2 — Financial events
**Signals:** SIG-003 (Campaign close) · SIG-004 (Large gift) · SIG-006 (Campaign launch) · SIG-007 (AUM threshold)
**Purpose:** Has a significant financial event occurred that changes this org's investment needs?

**Queries — run for each contact org:**
- `"[org name]" "campaign" "raised" OR "goal" OR "complete" OR "close" 2026`
- `"[org name]" "gift" OR "donation" OR "bequest" OR "pledge" "$" 2026`
- `"[org name]" "capital campaign" OR "endowment campaign" 2026`
- `"[org name]" "endowment" "million" 2026`
- `"[org name]" "largest gift" OR "transformative gift" OR "legacy gift" 2026`

**Fires when:** Confirmed or announced financial event that materially
changes the org's asset base or investment trajectory
**LinkedIn rule:** High Priority channel → always scrape via Apify when
LinkedIn URL surfaces
**Gift threshold guidance:**
- $500K–$1M: Score-1 standalone · combine with other signals
- $1M–$5M: Score-1 standalone · High signal for most pipeline contacts
- $5M+: Score-3 regardless of other signals — move immediately
**Sources:** Org website · local news · Chronicle of Philanthropy ·
Inside Philanthropy · press releases · ProPublica 990 (for AUM threshold)
**Profile action:** Update Financial profile · Recalculate compound score

---

### Channel 3 — Governance events
**Signals:** SIG-005 (New IC chair) · SIG-008 (Merger/restructuring)
**Purpose:** Has a governance reset occurred that creates an advisor review moment?

**Queries — run for each contact org:**
- `"[org name]" "merger" OR "merge" OR "consolidation" OR "affiliation" 2026`
- `"[org name]" "board" "restructur" OR "new chair" OR "reorganiz" 2026`
- `"[org name]" "investment committee" "new" OR "restructur" 2026`
- `"[org name]" "strategic plan" OR "new direction" OR "transformation" 2026`

**Fires when:** Confirmed governance change that creates a fiduciary review
moment or removes incumbent advisor entrenchment
**LinkedIn rule:** High Priority for merger signals → always scrape via Apify
· Medium for board changes → scrape only if sole source
**Merger note:** Two boards + two investment committees = political pressure
to reset the advisor relationship. Move immediately when merger confirmed.
**Profile action:** Update Leadership section · Flag for compound scoring

---

### Channel 4 — Strategic signals
**Signals:** SIG-009 (New strategic plan) · SIG-010 (First-time endowment)
**Purpose:** Has the org published a plan or announcement that signals financial intent?

**Queries — run for each contact org:**
- `"[org name]" "strategic plan" 2026`
- `"[org name]" "endowment" "establish" OR "launch" OR "first" OR "new" 2026`
- `"[org name]" "annual report" 2026`
- `"[org name]" "financial sustainability" OR "long-term" OR "permanent fund" 2026`

**Fires when:** Strategic plan with explicit endowment growth language, OR
confirmed first-time endowment establishment
**Watch for:** Language like "grow endowment to $X by [year]" or "build a
permanent endowment" — passive plans without investment language do not fire
**LinkedIn rule:** Medium Priority → scrape only if sole source
**First-time endowment note:** No incumbent to displace — highest conversion
potential in the pipeline. Move immediately.
**Profile action:** Note in What Lark knows · Flag for soft outreach

---

### Channel 5 — LinkedIn activity
**Signals:** All signal types — LinkedIn-specific sweep
**Purpose:** Surface announcements, wins, and leadership changes that appear
exclusively on LinkedIn and are not indexed by general web search yet.

**Queries — run for each contact org:**
- `site:linkedin.com "[org name]" 2026`
- `site:linkedin.com "[org name]" "new" "director" OR "CFO" OR "executive" 2026`
- `site:linkedin.com "[org name]" "gift" OR "campaign" OR "endowment" 2026`
- `site:linkedin.com "[org name]" "strategic" OR "plan" OR "announce" 2026`

**Fires when:** Any signal-relevant post surfaces for a contact org
**LinkedIn rule:** High Priority channel → apply radar/telescope decision
tree to every LinkedIn URL that surfaces. For small orgs, LinkedIn is
often the primary announcement channel — always scrape when signal-relevant.
**Apify extraction targets:**
- Full post text + date
- Author name and title
- Engagement metrics (reactions, comments, shares)
- Top 3–5 comments
- Company page recent posts (last 5)
**Profile action:** Classify signal type · update compound score ·
label source as Apify-verified

---

### Channel 6 — Conference presence
**Signals:** Compound amplifier for SIG-001 and SIG-002
**Purpose:** Is a contact org presenting, attending, or mentioned at a
sector conference — and does it create an outreach timing window?

**Read `data/conferences.md` before running this channel.**
Only run queries for conferences in their active monitoring window.

**Queries — run for each contact org during monitoring windows:**
- `"[conference name]" "[org name]" speaker OR presenter OR panelist [year]`
- `"[conference name]" "[org name]" attending OR registration [year]`
- `site:linkedin.com "[org name]" "[conference name]" [year]`

**Regional query framework (for contacts outside major metros):**
- `"[state] nonprofit" conference 2026 "[org name]"`
- `AFP "[chapter]" conference 2026 "[org name]"`
- `"[state] council of nonprofits" annual 2026 "[org name]"`

**Fires when:** Contact org confirmed presenting or attending a Tier A or
regional conference during the monitoring window
**Conference + leadership signal = compound:** A new ED presenting at a
sector conference within 6 months of appointment → Score-2 minimum
**Farther presence note:** If Farther is attending the same conference
(check `data/conferences.md` Farther presence table) → flag for warm
outreach angle: "We'll both be at [event] — would love to connect."
**LinkedIn rule:** Medium Priority → scrape only if sole source
**Profile action:** Log conference presence · apply compound scoring ·
flag outreach timing window

---

### Channel 7 — 990 and regulatory signals
**Signals:** SIG-007 (AUM threshold) · SIG-010 (First-time endowment)
**Purpose:** What does the most recent 990 reveal about this org's financial
position that may not be visible in public announcements?

**Run for contacts where 990 has not been pulled this quarter, or where
an AUM threshold event is suspected.**

**Queries:**
- ProPublica Nonprofit Explorer: search by org name or EIN
- Candid / GuideStar: EIN lookup for Schedule D (endowment funds)
- `"[org name]" 990 endowment [year]`

**What to extract from 990:**
- Schedule D Part V: endowment fund beginning/end of year balance
- Schedule D footnotes: named investment advisor (if disclosed)
- Part IX: total expenses — signals org size and complexity
- Part X: total assets — proxy for investable assets if endowment not broken out
- Revenue trend: year-over-year growth signals capacity change

**Fires when:**
- Endowment crosses a threshold ($5M · $10M · $25M · $50M)
- Endowment appears on Schedule D for the first time
- Named advisor changes between tax years
**990 lag note:** Data is 12–18 months old. Always state the tax year.
Never present 990 AUM as current — use as confirmation layer.
**LinkedIn rule:** Low Priority → log URL, do not scrape
**Profile action:** Update Financial profile · Update AUM · Note tax year ·
Flag threshold crossed if applicable

---

### Channel 8 — Signal cross-check
**Signals:** All — compound scoring and pattern detection
**Purpose:** Do any signals fired this sweep stack on the same contact?
Does a new pattern emerge across multiple contacts?

**Action:** After Channels 1–7 have run:
1. Read `data/signals.md` — all Active signals
2. For each contact that fired at least one signal:
   - Count signals by tier (High / Medium / Contextual)
   - Calculate compound score (1 / 2 / 3)
   - Write score to the contact's profile
   - Flag recommended action and window
3. Look across the full contact list:
   - Are 2+ contacts showing the same signal type this week?
     → Note as a sector trend in the report
   - Is a contact showing a signal that contradicts a prior Speculative
     finding? → Upgrade or drop the prior finding
4. Flag Score-3 contacts prominently — these drive the Slack summary

**New pattern rule:** If a signal type fires on 3+ contacts in the same
sweep → log as a pipeline-wide observation in the report. Example:
"Three Hawaii community foundations announced new EDs this sweep —
possible sector-wide leadership transition moment."

**LinkedIn rule:** High Priority → always scrape via Apify when a LinkedIn
URL surfaces and is relevant to compound scoring
**Always log:** total signals processed · High / Medium / Contextual /
Discarded counts · Score-3 contacts · Apify calls made · credits used

---

## Sweep output rules

### If signals fire:
- Report only contacts where something actually happened
- One finding card per signal (use `skills/alert-writer.md` format)
- Load the relevant profile, update it, note it in the report
- Score-3 contacts first — always
- Label all Apify-sourced LinkedIn data:
  `Source: [org] LinkedIn — [post date] — retrieved via Apify [date]`

### If no signals fire on a channel:
- One line only: `Channel [N] — [name]: No activity detected this sweep.`
- Do not fabricate findings to fill the report

### If Apify credits are exhausted:
- Note in report: `LinkedIn verification unavailable this sweep —
  Apify credits exhausted. [N] LinkedIn URLs logged for manual review.`
- List the unverified URLs in a gap box at the end of the report

### Report structure:
```
🪦 Lark · Weekly Brief · [DATE]

CONTACTS SWEPT: [N] · SIGNALS FIRED: [N]
HIGH: [N] · MEDIUM: [N] · CONTEXTUAL: [N] · DISCARDED: [N]
SCORE-3 CONTACTS: [N] · APIFY CALLS: [N] · CREDITS USED: ~$[X]

SCORE-3 — [Org name] — [signals] — Move immediately
[Finding cards]

SCORE-2 — [Org name] — [signals] — Outreach within 2 weeks
[Finding cards]

SCORE-1 — [Org name] — [signal] — Soft touch
[Finding cards]

CHANNELS WITH NO ACTIVITY: [list]
LINKEDIN URLS LOGGED BUT NOT SCRAPED: [list if any]
PROFILES UPDATED: [list]
PROFILES CREATED: [list — new contacts encountered]
Next sweep: [date]
```

---

## Coverage gaps — note when applicable
- LinkedIn Ad Library: sponsored content not accessible via Apify standard
  actors — requires manual check · never fabricate ad data
- Apify credits exhausted: LinkedIn URLs logged but not scraped — note as
  gap, list URLs for manual review
- IRS 990 lag: 12–18 months behind real time — always state tax year
- Board meeting minutes: not always public — note when relevant
- Gated content: partially inaccessible — note as gap, do not fabricate

---

## What this is not
- Not a status report on what 50 orgs are generally doing
- Not "I checked the Aloha Community Foundation website and nothing changed"
- Not padding with low-signal observations to make the report look full
- Not a check-in. An early warning system.
- Not proactive LinkedIn scraping — Apify fires on demand only

If nothing fired this week, the report is short. That is a good outcome.
A quiet week is intelligence too.