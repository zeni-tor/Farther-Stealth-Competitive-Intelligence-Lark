# signal-classification.md

Triage every raw signal before output. Three questions:

## 1. Relevant?
Discard if none apply:
- Mentions any of the 50 monitored competitors by name or brand
- Relates to nonprofit investment advisory, endowments, OCIO, or RFP activity
- Involves personnel, content, clients, or filings from any monitored firm

If uncertain → flag `RELEVANCE: Uncertain`, pass through with note.

## 2. Signal type?
`RFP` · `Client` · `Content` · `LinkedIn` · `ADV` · `Behavioral` · `Campaign`

If spans multiple → classify by primary action, note secondary.
Campaign vs. Content: a single published piece is `Content`. Two or more
surfaces running a shared nonprofit theme within 60 days is `Campaign`.

## 3. Priority?

**High** — any of:
- Named client win announced
- New gated asset published (always flag for behavioral-pattern-analysis)
- Content coaching nonprofits to skip/reframe RFP process
- New RFP response or public RFP issued to any monitored firm found
- New hire or departure at director level+
- ADV shows 20%+ change in charitable org client count
- Coordinated campaign detected: 2+ surfaces, shared nonprofit theme,
  within 60 days (always flag for behavioral-pattern-analysis)

**Medium** — any of (Tier 1 only):
- New article, guide, webinar, market commentary
- LinkedIn post with 50+ reactions or 10+ comments
- Minor ADV change

**Low** — relevant but doesn't meet above thresholds

**Discard** — not relevant

## 4. LinkedIn URL present?

If the signal source includes a LinkedIn URL, apply the Apify decision:

```
Is this signal High Priority AND from channel 1, 2, 3, 6, 8, or 11?
         ↓ Yes                        ↓ No
  Flag: APIFY_SCRAPE: YES      Is LinkedIn the ONLY source?
  Read apify-config.md               ↓ Yes        ↓ No
  before proceeding             APIFY_SCRAPE: YES  APIFY_SCRAPE: NO
                                                   Log URL only
```

Add to output:
```
APIFY_SCRAPE: [YES/NO]
APIFY_REASON: [why scrape was triggered or skipped]
LINKEDIN_URL: [URL if present]
```

## Output format
```
SIGNAL TYPE: [type]
PRIORITY: [High/Medium/Low/Discard]
DISCARD REASON: [if discarded]
SOURCE: [URL or reference]
DATE: [ISO date]
APIFY_SCRAPE: [YES/NO — only if LinkedIn URL present]
APIFY_REASON: [rationale]
LINKEDIN_URL: [URL if present]
NOTES: [ambiguity or behavioral flag]
```

Stop here if Discard. Pass to alert-writer.md otherwise.
Gated content → always also flag for behavioral-pattern-analysis.md.
APIFY_SCRAPE: YES → read data/apify-config.md before calling Apify.
