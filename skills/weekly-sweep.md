# weekly-sweep.md — Lark Signal-First Sweep Protocol

> Not: "visit each contact and see what's new."
> Yes: "scan the world for signals, match against pipeline."
> If nothing fires, say so. Don't check in on quiet contacts.

---

## The model

```
STEP 1 · SIGNAL SCAN (broad web search)
  Search for signals across all US nonprofits.
  Do NOT loop through contacts asking "what happened to you?"
  Radar first — collect raw hits from news, press, org sites, 990s.

STEP 2 · ORG EXTRACTION
  For each hit, extract org name + domain if available.

STEP 3 · FUZZY MATCH
  Compare each org name against contact_data/ using the matcher.
  from utilities.lark_fuzzy_matcher import LarkMatcher
  HIGH → enrich · AMBIGUOUS → flag · NO_MATCH → discard

STEP 4 · ENRICHMENT (HIGH matches only)
  ProPublica API per confirmed match. Never on unmatched orgs.

STEP 5 · SCORE
  Apply compound scoring from data/signals.md

STEP 6 · OUTPUT
  HTML report + HubSpot write-back CSV
  Update memory.md
```

---

## Sweep 1 gate — SIG-001 only

Run Channel 1 (SIG-001) only for the first sweep.
Purpose: validate pipeline end-to-end before adding signal volume.
After sweep 1 is confirmed working → activate all channels.

```
Sweep 1    → Channel 1 only (SIG-001)      ← current
Sweep 2+   → All channels (all 10 signals) ← after validation
Phase 2    → Apify + HubSpot MCP live      ← separate milestone
```

---

## LinkedIn / Apify — DEFERRED

LinkedIn scanning is not active. Do not attempt LinkedIn scrapes.
See signal-classification.md for full coverage gap note.
When a LinkedIn URL appears in search results:
- Log the URL
- Mark signal Speculative if LinkedIn is the only source
- Do not scrape

---

## Compound scoring

After all active channels run, score each org that fired a signal.

```
Score 3 → 2+ High signals, or High + Medium + Contextual
Score 2 → 1 High + 1 Medium, or 2+ Medium signals
Score 1 → Single signal, any tier
```

Score-3 contacts are the highest priority output.
Sweep 1: all contacts are Score-1 (single SIG-001 signal).

---

## HubSpot write-back

MCP key: PENDING — stage all write-back in CSV output.
Do not attempt MCP calls.
Read data/hubspot-properties.md before writing any field.

---

## Channel 1 — Leadership changes · ACTIVE (Sweep 1)
**Signals:** SIG-001 · SIG-002 · SIG-005
**Phase 1 focus:** SIG-001 only

**Web search queries — run each sweep:**
```
"nonprofit" "new CFO" OR "new chief financial officer" 2026
"nonprofit" "new finance director" OR "finance director joins" 2026
"foundation" OR "endowment" "named CFO" OR "appointed CFO" 2026
"nonprofit" "CFO" "joins" OR "named" OR "appointed" site:prnewswire.com OR site:businesswire.com 2026
"nonprofit" "new" "vice president of finance" OR "VP finance" OR "director of finance" 2026
```

**When SIG-002 / SIG-005 activate (sweep 2+):**
```
"nonprofit" "new executive director" OR "new CEO" 2026
"nonprofit" "executive director" "joins" OR "named" OR "appointed" 2026
"foundation" "new" "investment committee" "chair" 2026
```

**Fires when:** Named leadership change at a contact org confirmed or
strongly inferred from a primary source.
**Small org note:** Small nonprofits may announce hires only on LinkedIn —
these will be missed until Apify activates. Note as coverage gap.
**Profile action:** Update Leadership section · compound score · action window.

---

## Channel 2 — Financial events · READY (activate sweep 2+)
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

## Channel 3 — Governance events · READY (activate sweep 2+)
**Signals:** SIG-005 · SIG-008

**Web search queries:**
```
"nonprofit" "merger" OR "merge" OR "consolidation" OR "affiliation" 2026
"nonprofit" "board" "restructur" OR "reorganiz" 2026
"foundation" "investment committee" "new chair" OR "restructur" 2026
```

---

## Channel 4 — Strategic signals · READY (activate sweep 2+)
**Signals:** SIG-009 · SIG-010

**Web search queries:**
```
"nonprofit" "strategic plan" "endowment" 2026
"nonprofit" "endowment" "establish" OR "launch" OR "first" 2026
"foundation" "grow endowment" OR "permanent endowment" OR "endowment goal" 2026
```

**Watch for:** Language like "grow endowment to $X by [year]" —
passive plans without investment language do not fire.

---

## Channel 5 — LinkedIn activity · DEFERRED
**All signal types — LinkedIn sweep.**
Deferred pending Apify financial justification.
Do not activate until Apify credentials are configured.

**When activated:** Run org name + signal keyword queries against
LinkedIn via Apify. Extract post text, author, date, engagement.

---

## Channel 6 — Conference presence · READY (activate sweep 2+)
Read `data/conferences.md` before running.
Only run for conferences in active monitoring window.

**Queries per org in monitoring window:**
```
"[conference name]" "[org name]" speaker OR presenter OR panelist [year]
"[conference name]" "[org name]" attending OR registration [year]
```

---

## Channel 7 — 990 and regulatory signals · READY (activate sweep 2+)
**Signals:** SIG-007 · SIG-010

ProPublica API — free, no key:
```
https://projects.propublica.org/nonprofits/api/v2/search.json?q=[ORG]
https://projects.propublica.org/nonprofits/api/v2/organizations/[EIN].json
```

Extract: Schedule D endowment balance · total assets · NTEE code
Always state tax year. Never present 990 AUM as current.

---

## Channel 8 — Signal cross-check · ACTIVE (all sweeps)
**Purpose:** Score contacts, detect patterns across pipeline.

After all active channels run:
1. Read data/signals.md
2. Score each org that fired a signal
3. Write score to profile
4. Look across all hits — are 3+ orgs showing the same signal?
   → Note as sector trend in report
5. Flag Score-3 contacts prominently

---

## Enrichment stack (matched contacts only)

```
Step 1 · ProPublica API (free · every HIGH match)
  URL: https://projects.propublica.org/nonprofits/api/v2/search.json?q=[ORG]
  Extract: total_assets · ntee_code · tax_prd_yr · ein · state
  Write to: lark_aum_estimated · lark_aum_source · lark_propublica_ein

Step 2 · Web fetch org site (gap fill · high-score contacts)
  Check: leadership page · news · strategic plan · campaign pages
  Fill: CFO name confirmation · endowment status · campaign status

Step 3 · Google Drive 990s (Phase 2 · via MCP)
  Activate when MCP key is live.
```

---

## Compound scoring

Compound scoring is Lark's judgment call — not a script. After all channels
run, reason through each matched org's signal stack and assign a score.
The rubric below is the floor; apply judgment above it.

**Base scoring rules:**

Score 3 → 2+ High signals, or High + Medium + Contextual
Score 2 → 1 High + 1 Medium, or 2+ Medium signals
Score 1 → Single signal, any tier

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
- $500K–$1M + any other signal: consider Score-2

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
- One line: `Channel [N]: No activity detected this sweep.`
- Do not fabricate findings
- Short report is correct

### If LinkedIn is the only source:
- Mark signal Speculative
- Log URL for manual review
- Note in coverage gaps section

### If HubSpot MCP key is pending:
- Complete sweep and report normally
- Note: `HubSpot write-back staged — MCP key pending`
- Output write-back CSV to outputs/

---

## Report structure

```
SWEEP DATE: [date] · PHASE: 1 · SWEEP: [N]
CHANNELS ACTIVE: [list] · CHANNELS DEFERRED: Channel 5 (LinkedIn)
SIGNALS: [N] raw hits · HIGH: [N] · AMBIGUOUS: [N] · DISCARDED: [N]
MATCHES: [N] HIGH · [N] AMBIGUOUS
SCORES: Score-3: [N] · Score-2: [N] · Score-1: [N]
HUBSPOT: STAGED — MCP key pending · [N] records queued
COVERAGE GAP: LinkedIn not scanned · small org hires may be missed

[Score-3 finding cards]
[Score-2 finding cards]
[Score-1 finding cards]
[AMBIGUOUS review list]
[Channels with no activity]
[Coverage gaps]
[HubSpot write-back log]
```

---

## Coverage gaps — always note when applicable
- LinkedIn not scanned — Apify deferred
- IRS 990 lag — 12–18 months behind, always state tax year
- HubSpot write-back staged — MCP key pending
- Board meeting minutes not always public
- Gated content partially inaccessible — never fabricate