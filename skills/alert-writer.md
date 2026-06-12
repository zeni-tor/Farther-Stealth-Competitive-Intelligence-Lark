# behavioral_flags.md — Standing Behavioral Patterns

> Read this file at the start of every sweep for Channel 11
> (behavioral cross-check).
> This file is written and maintained by the agent — not by humans.
> Humans may review but should not overwrite confirmed entries.
> Last updated: 2026-06-09

---

## How Channel 11 uses this file

At the end of every sweep, after Channels 1–10 have run:
1. Read all Active flags in this file
2. Cross-reference every signal found this sweep against each flag's known
   playbook
3. If a new signal matches a standing pattern → escalate to High Priority
   and note "consistent with standing flag"
4. If a new signal contradicts a standing pattern → note "possible strategy
   shift" and escalate
5. If a new pattern is emerging across 2+ new signals → create a new entry
   below as Watching

---

## Active Flags

### ⚑ FLAG-001 — eCIO RFP Funnel
**Firm:** eCIO (getecio.com)
**Status:** Active
**Confidence:** High
**Date confirmed:** 2026-06-05
**Pattern type:** Contradiction + Funnel + Market-shaping + Cross-channel

**Sourcing note — important:**
The LinkedIn layer of this flag (RFP win posts, skip-the-RFP coaching posts)
was originally identified via manual human research (pre-2026-06-09). Those
LinkedIn findings are valid and confirmed by the human researcher, but they
are **human-sourced**, not automated. Label them accordingly:
`Source: eCIO LinkedIn — human-sourced [date]`

When Apify subsequently confirms the same LinkedIn posts or finds new ones
matching this pattern, upgrade the sourcing label to:
`Source: eCIO LinkedIn — retrieved via Apify [date]`
and log the upgrade in New iterations below.

**The playbook — five confirmed steps:**
1. Nonprofit searches for RFP guidance → finds eCIO's free RFP template
   (gated — captures name, email, org)
2. Downloads template → encounters "Should You Issue an RFP?" content
   coaching prospects to skip formal process
3. eCIO frames its own evaluation criteria inside the process guide
   (buyer conditioning)
4. Nonprofit submits RFP directly to eCIO via dedicated submission portal
5. Zero public RFPs found in SAM.gov — wins appear to come from
   private/informal processes

**Contradiction confirmed:** RFP submission portal live at same time as
skip-the-RFP coaching content. Both actively promoted simultaneously.

**Primary sources:**
- getecio.com/submit-an-investment-management-request-for-proposal-rfp ·
  retrieved Jun 2026 · Confirmed (web search)
- getecio.com/resources/should-you-issue-an-rfp-to-select-your-next-investment-advisor ·
  retrieved Jun 2026 · Confirmed (web search)
- getecio.com/resource-center/rfp-resources · retrieved Jun 2026 ·
  Confirmed (web search)
- SAM.gov search — "eCIO investment advisory" — zero results ·
  retrieved Jun 5, 2026 · Confirmed (web search)
- eCIO LinkedIn — RFP win posts + skip-the-RFP coaching posts ·
  human-sourced pre-2026-06-09 · Confirmed (human researcher)

**What to check every sweep:**
- Any new LinkedIn post from eCIO — does it promote the RFP portal,
  skip-the-RFP content, or a new gated asset?
  → If LinkedIn URL surfaces in Channel 8 search results → scrape via Apify
- Any new gated PDF or guide on getecio.com → document what the gate collects
- Any new RFP-related content → does it reinforce or contradict the
  dual-track strategy?
- SAM.gov → still zero results?

**New iterations logged:**
- 2026-06-09: Apify integration added — LinkedIn layer of this flag will now
  be Apify-verified going forward. Pre-integration LinkedIn findings
  reclassified as human-sourced.
- 2026-06-06: Funnel fully re-confirmed from primary sources — no strategy
  shift. Gated template, skip-the-RFP coaching, embedded evaluation criteria,
  live submission portal, zero SAM.gov all intact. Two unverified LinkedIn
  client-win posts (Tucson IDA, Perinatal Foundation) observed as adjacent
  "publicize the win" behavior — not the funnel itself. LinkedIn sourcing:
  human-sourced (pre-Apify).
- 2026-06-05: Full five-step funnel confirmed and documented from primary
  sources · first sweep

---

### ⚑ FLAG-002 — BofA "OCIO 2.0" + Consolidation Displacement
**Firm:** Bank of America
**Status:** ACTIVE — upgraded from Watching 2026-06-06
**Confidence:** Medium-High
**Date flagged:** 2026-06-05 · **Date confirmed Active:** 2026-06-06
**Pattern type:** Market-shaping (consolidate-to-the-largest-provider)

**Sourcing note:**
All FLAG-002 sources confirmed via web search. No LinkedIn dependency.

**The pattern — two coordinated pieces:**
1. April 7, 2026 press release introduces "OCIO 2.0" — service framed as
   going beyond investment management (governance advisory, spending policy
   design, leadership development, fundraising strategy).
2. Companion article "Should Nonprofits Consolidate Outsourced CIO Providers?"
   explicitly advises nonprofits to reduce to a SINGLE OCIO — "choosing a
   single OCIO provider remains a best practice… a unified OCIO gives you
   clarity, control and cohesion" (Bernard Reidy, BofA Private Bank).

**Upgrade test result:**
- Test 1 (advises reducing # of advisors): MET
- Test 2 (frames OCIO 2.0 as a required new standard): NOT met yet

**Primary sources:**
- privatebank.bankofamerica.com/articles/should-nonprofits-consolidate-ocio-providers.html ·
  retrieved 2026-06-06 · Confirmed (web search)
- newsroom.bankofamerica.com — "OCIO 2.0" release · Apr 7, 2026 ·
  retrieved 2026-06-06 · Confirmed (web search)

**What to check every sweep:**
- New "consolidation" / "single OCIO" content, or OCIO 2.0 framed as a
  required standard (would satisfy Test 2)
- Any nonprofit board-facing campaign reinforcing the consolidation theme
- William Jarvis (BofA) NACUBO Endowment Leadership Series appearance

**Evidence gaps:** Consolidation article carries no visible date. Chestnut
Solutions Institute survey not directly retrieved — treat ranking as Inferred.

**New iterations logged:**
- 2026-06-06: Upgraded Watching → Active. Consolidation article confirmed.
  Jarvis NACUBO presence noted as reinforcing channel.

---

## Watching (Potential Patterns — Not Yet Confirmed)

### WATCH-001 — CAPTRUST acquisition pattern
**Firm:** CAPTRUST
**Date flagged:** 2026-06-05 · **Updated:** 2026-06-06
**Observation:** Stillwater Capital Advisors ($1.25B, explicitly serves
endowments & foundations) CONFIRMED closed May 14, 2026. Carnegie ($7.5B)
remains "in talks" only — unconfirmed.
**Escalate to Active if:** Carnegie acquisition confirmed, or a third
nonprofit-specialist firm acquired within 12 months.

### WATCH-002 — Cerity Partners rapid expansion
**Firm:** Cerity Partners
**Date flagged:** 2026-06-05 · **Updated:** 2026-06-06
**Observation:** Verus merger CONFIRMED closed March 31, 2026 (~$1.2T
institutional AUA). PE-backed (Genstar). Hold at Watching.
**Escalate to Active if:** Another institutional acquisition announced within
6 months, or Verus nonprofit-OCIO line confirmed as actively marketed under
the Cerity brand.

### WATCH-003 — Industry-wide E&F / OCIO consolidation wave
**Firms:** CAPTRUST · Cerity Partners · Fiducient (Wealthspire)
**Date flagged:** 2026-06-06
**Observation:** Three Tier A firms expanded E&F capability via M&A within
~6 weeks. Pairs thematically with BofA FLAG-002.
**Escalate to Active if:** A fourth E&F-relevant acquisition lands within the
quarter (by ~Sept 2026).

---

## Resolved Flags
> Patterns confirmed as ended, reversed, or no longer active.

None yet.

---

## Instructions
- Read this file at the start of every sweep before running Channel 11
- After Channel 11 runs: update "New iterations logged" for any active flag
  that fired this sweep
- When Apify verifies a previously human-sourced LinkedIn finding: upgrade
  the sourcing label and log it in New iterations
- When behavioral-pattern-analysis.md confirms a new pattern: add a new
  Active Flag entry
- When a Watching entry reaches Medium+ confidence: move it to Active Flags
- When a pattern resolves or reverses: move it to Resolved with a note