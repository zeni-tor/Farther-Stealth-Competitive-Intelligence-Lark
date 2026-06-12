# signal-classification.md — Lark · Signal Triage

Triage every raw signal before output. Four questions:

---

## 1. Relevant?
Discard if none apply:
- Mentions a contact org from the active HubSpot cohort by name or domain
- Relates to nonprofit leadership change, financial event, governance change,
  or strategic event at a contact org
- Involves a person named in the contact org's HubSpot record

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
- Conference presence (activate in Phase 2)

**Discard** — not relevant to any contact in the active cohort

---

## 4. LinkedIn URL present?

If the signal source includes a LinkedIn URL, apply the Apify decision:

```
LinkedIn URL surfaces in search results
         ↓
Is the signal High Priority?
         ↓ Yes                    ↓ No
   Always scrape          Is it the ONLY source
   via Apify              confirming this signal?
                               ↓ Yes        ↓ No
                          Scrape it     Log URL only
                          via Apify     Mark Speculative
```

Add to output:
```
APIFY_SCRAPE: [YES/NO]
APIFY_REASON: [why scrape was triggered or skipped]
LINKEDIN_URL: [URL if present]
```

---

## Output format

```
SIGNAL TYPE: [SIG-00X]
PRIORITY: [High/Medium/Contextual/Discard]
DISCARD REASON: [if discarded]
ORG NAME: [as found in source]
HUBSPOT MATCH: [Confirmed / Pending fuzzy match / No match]
SOURCE: [URL or reference]
DATE: [ISO date]
APIFY_SCRAPE: [YES/NO — only if LinkedIn URL present]
APIFY_REASON: [rationale]
LINKEDIN_URL: [URL if present]
NOTES: [ambiguity or confidence flags]
```

Stop here if Discard. Pass to alert-writer.md otherwise.
High signal + LinkedIn URL → scrape via Apify before writing findings.