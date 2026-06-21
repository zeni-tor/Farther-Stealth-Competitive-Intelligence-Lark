# alert-writer.md — Lark · Prospect Intelligence Output Formatter

## Purpose
Lark uses this file to format all output — Slack summaries and HTML reports.
Every output is organized by compound score, not by signal type.
Score-3 contacts are always first. They are the reason the report exists.
In Phase 1 all contacts are Score-1 — they still get full treatment.

---

## Slack format — monthly summary

```
🪶 Lark · Prospect Intelligence Brief — Week of [DATE]

📊 PIPELINE SUMMARY
[N] signals scanned · [N] HIGH matches · [N] AMBIGUOUS · [N] discarded
[N] Score-1 contacts · HubSpot write-back: STAGED (MCP key pending)

━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 SCORE-1 — Soft touch · monitor closely
━━━━━━━━━━━━━━━━━━━━━━━━━━

[Org name] · [City, State] · Est. AUM: $[X]M
Signal: SIG-001 — [New hire name], [Title]
Window: Move within 60–90 days · expires [date]
Angle: [1-sentence outreach angle — why now, what to say]
Source: [publication] · [date]

[Repeat for each Score-1 contact]

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ AMBIGUOUS — Manual review required
━━━━━━━━━━━━━━━━━━━━━━━━━━

• [Signal org name] — top match: [CSV candidate] (score [N]) · confirm or discard

━━━━━━━━━━━━━━━━━━━━━━━━━━
Full report attached · Next sweep: [DATE] · Questions: mention @Lark
```

---

## Outreach angle — how to write it

The outreach angle is the single most important element in Lark's output.
It tells the Farther team not just *that* something happened, but *what to say*.

**Rules:**
- One sentence only
- Frame around the prospect's situation, not Farther's product
- Reference the specific signal — never generic
- Never say "we noticed" or "we saw" — frame as awareness of their milestone
- End with an implicit opening, not a hard ask

**Good examples:**
- "A new CFO in the first 90 days almost always takes a quiet look at the advisor
  relationship — this is exactly the window."
- "With [Name] just stepping into the CFO role, now is when the investment advisor
  relationship gets re-examined whether they plan it or not."
- "New finance directors want to own their vendor relationships — this is the
  natural moment to be the option they choose."

**Weak examples (avoid):**
- "We saw you hired a new CFO — we'd love to connect." ✗
- "Congratulations on your recent news." ✗
- "Farther Institutional specializes in nonprofits like yours." ✗

---

## HTML report format

### Report header components

```html
<!-- Masthead: dark background, Lark branding, week dates -->
<!-- Stats bar: signals scanned · HIGH · AMBIGUOUS · NO MATCH · Score-1 -->
<!-- Lark note: transparency banner — never skip -->
<!-- Slack preview block -->
```

### Lark transparency note — always include, never skip

The Lark note (green banner at top of report) must state:
- Total web searches run this sweep
- Total raw signal hits extracted
- Total HIGH / AMBIGUOUS / NO MATCH routing
- ProPublica enrichment: [N] successful · [N] not found
- HubSpot write-back: STAGED — MCP key pending · [N] records queued
- Coverage gaps: LinkedIn not scanned (Phase 1) · Apify activates Phase 2

Example:
```
Lark — 5 searches run · 12 raw hits extracted · 3 HIGH matches ·
2 AMBIGUOUS (flagged for review) · 7 NO MATCH discarded.
ProPublica enrichment: 3 successful. HubSpot write-back: STAGED —
MCP key pending, 3 records queued for import.
Coverage gap: LinkedIn not scanned in Phase 1.
```

### Score-1 contact block (Phase 1 standard)

```html
<div class="layer">
  <div class="layer-header">
    <div class="layer-tag tag-score1">Score 1</div>
    <div class="layer-name">[Org name]</div>
  </div>
  <div class="layer-sub">
    [city, state] · [org type from NTEE] · Est. AUM: $[X]M · [tax year]
  </div>
  <div class="layer-rule"></div>

  <div class="finding">
    <div class="finding-meta">
      <div class="cert-badge c-confirmed">Confirmed</div>
      <div class="finding-priority p-high">High</div>
    </div>
    <div class="finding-body">
      <div class="finding-title">SIG-001 — New CFO: [Name], [Title]</div>
      <div class="finding-desc">
        [2–3 sentences. What was announced, when, source.
        What it means for Farther. Neutral language.]
      </div>
      <div class="finding-source">
        Source: <a href="[URL]">[publication]</a> · [date] · retrieved [date]
      </div>
    </div>
  </div>

  <div class="finding-action">
    <strong>Outreach angle</strong>
    [1 sentence — framed around the prospect's situation]
    Window: Move within 60–90 days · expires [date]
  </div>

  <!-- ProPublica enrichment block -->
  <div class="gap-box">
    <strong>Enrichment · ProPublica</strong>
    Total assets: $[X] · Tax year: [year] · NTEE: [code] · EIN: [number]
    AUM note: [institutional range / early stage / not found]
  </div>

  <!-- HubSpot write-back status -->
  <div class="gap-box">
    <strong>HubSpot write-back · STAGED</strong>
    Record: [org name from CSV] · Properties queued: lark_signal_type=SIG-001 ·
    lark_contact_status=Signal Detected · lark_compound_score=1 ·
    lark_action_window=[window] · lark_aum_estimated=[value]
    Status: Pending MCP key — import via hubspot-writeback CSV when ready.
  </div>
</div>
```

### AMBIGUOUS match block

```html
<div class="competitor">
  <div class="comp-header">
    <div class="comp-name">[Signal org name — as found in news]</div>
    <div class="comp-aka">Fuzzy match — manual review required</div>
    <div class="comp-count">score [N] · AMBIGUOUS</div>
  </div>
  <div class="gap-box">
    <strong>Review required</strong>
    Top candidates from CSV:
    1. [Candidate name] — score [N]
    2. [Candidate name] — score [N]
    3. [Candidate name] — score [N]
    Action: confirm the correct record in HubSpot, then manually apply
    signal data. Source: [URL]
  </div>
</div>
```

### No-signal sweep result

```html
<div class="gap-box">
  <strong>No signals fired this sweep</strong>
  5 searches run · [N] results reviewed · 0 HIGH matches ·
  [N] discarded as not relevant to pipeline.
  A quiet sweep is correct. Next sweep: [date]
</div>
```

---

## Layer tags for Lark reports

```css
.tag-score1 { background: #3d6b4f; color: #f5f4ef; }
.tag-score2 { background: var(--amber); color: #f5f4ef; }
.tag-score3 { background: var(--alert-red); color: #f5f4ef; }
.tag-ambiguous { background: #5a5852; color: #f5f4ef; }
```

---

## File naming

```
outputs/YYYY-MM-DD-lark-monthly.html          ← HTML report
outputs/YYYY-MM-DD-lark-hubspot-writeback.csv ← HubSpot import file
outputs/YYYY-MM-DD-lark-ambiguous.txt        ← manual review list
```

---

## Language rules

**Use:**
"This suggests" · "The pattern indicates" · "Based on the data" ·
"Worth moving on" · "The window is open" · "A natural conversation starter" ·
"Unverified — confirm before outreach"

**Avoid:**
"This proves" · "They are definitely" · "This confirms that" ·
"Without a doubt" · "Clearly they are" · "We saw" · "We noticed" ·
Generic outreach angles not tied to the specific signal

---

## No action available?

If a contact fired a signal but no clear outreach angle exists:
```
No outreach angle identified. File for context —
monitor next sweep for confirming signal before acting.
```