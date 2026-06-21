# signal-classification.md — Lark · Signal Triage

Triage every raw signal before output. Three questions.
LinkedIn / Apify is deferred — see note at bottom.

---

## 1. Relevant?

Discard if none apply:
- Relates to a US nonprofit, foundation, endowment, or similar org
- Event type matches a leadership change, financial event, governance
  change, or strategic event (one of the 10 signals in data/signals.md)
- Source is credible — press release, news outlet, org website, or 990

**Do NOT check the contact list at this stage.**
Whether the org is in Farther's pipeline is determined by the fuzzy
matcher in Step 3 — not here. Lark never accesses the contact list
during triage. Keep these two jobs separate.

If uncertain → flag `RELEVANCE: Uncertain`, pass through with note.

---

## 2. Signal type?
Match to one of the 10 named signals in `data/signals.md`:

`SIG-001` New CFO / Finance Director
`SIG-002` New CEO / Executive Director
`SIG-003` Capital campaign close
`SIG-004` Large gift or bequest
`SIG-005` New investment committee chair
`SIG-006` Capital campaign launch
`SIG-007` AUM threshold crossed
`SIG-008` Merger or restructuring
`SIG-009` New strategic plan
`SIG-010` First-time endowment

If spans multiple → classify by primary signal, note secondary.

---

## 3. Priority?

**High** — any of:
- Named leadership change (CFO, CEO, ED, IC chair)
- Capital campaign close or large gift confirmed
- Merger or restructuring announced
- First-time endowment confirmed

**Medium** — any of:
- Capital campaign launch announced
- AUM threshold crossed (990 data)
- Board or committee restructuring (not leadership change)
- Strategic plan with explicit endowment growth target

**Contextual** — any of:
- New strategic plan without explicit investment language
- Conference presence (Phase 2)

**Discard** — not a US nonprofit event, or not one of the 10 signals

---

## Output format

```
SIGNAL TYPE: [SIG-00X]
PRIORITY: [High/Medium/Contextual/Discard]
DISCARD REASON: [if discarded]
ORG NAME: [as found in source — exact text, do not look up]
DOMAIN: [if visible in source URL or article]
SOURCE: [URL or reference]
DATE: [ISO date]
NOTES: [ambiguity or confidence flags]
```

Stop here if Discard.
Pass to fuzzy matcher (utilities/lark_fuzzy_matcher.py) with ORG NAME + DOMAIN.
Fuzzy matcher determines whether org is in the pipeline — not this file.

---

## LinkedIn / Apify

**Impact on coverage:**
- Large orgs (CEO/ED hires, capital campaigns, major gifts) → well covered
  by press releases, nonprofit news, and org websites
- Small orgs ($1M–$5M, community-based) → CFO/finance director hires
  may appear on LinkedIn only and will be missed until Apify activates

**Coverage gap note — include in every report:**
"LinkedIn not scanned this sweep. Small org leadership changes
announced exclusively on LinkedIn are outside current coverage.
Apify integration deferred pending financial justification."

**When LinkedIn URL appears in web search results:**
- Do not attempt to scrape
- Log the URL as a coverage note
- Mark the signal Speculative if LinkedIn is the only source
- Confirmed or Inferred requires a non-LinkedIn source

**To activate LinkedIn scanning:**
1. Confirm Apify Starter plan ($29/mo) is justified by signal volume
2. Add Apify credentials to utilities/
3. Update this file: remove DEFERRED status
4. Update monthly-sweep.md Channel 5: remove DEFERRED status