# alert-writer.md — Lark · Prospect Intelligence Output Formatter

## Purpose
Lark uses this file to format all output — Slack summaries and HTML reports.
Every output is organized by compound score, not by signal type.
Score-3 contacts are always first. They are the reason the report exists.

---

## Slack format — weekly summary

```
🪦 Lark · Prospect Intelligence Brief — Week of [DATE]

📊 PIPELINE SUMMARY
[N] contacts swept · [N] signals fired · [N] Score-3 · [N] Score-2 · [N] Score-1

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 SCORE-3 — Move immediately
━━━━━━━━━━━━━━━━━━━━━━━━━━

[Org name] · [City, State] · Est. AUM: $[X]M
Signals: [Signal 1] + [Signal 2] + [Signal 3]
Window: [X days/weeks]
Angle: [1-sentence outreach angle — why now, what to say]
Source: [primary source]

[Repeat for each Score-3 contact]

━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 SCORE-2 — Outreach within 2 weeks
━━━━━━━━━━━━━━━━━━━━━━━━━━

[Org name] · [Signal 1] + [Signal 2] · [Window]
Angle: [1-sentence outreach angle]

[Repeat for each Score-2 contact]

━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 SCORE-1 — Soft touch · monitor closely
━━━━━━━━━━━━━━━━━━━━━━━━━━

• [Org name] — [signal fired] · [source]
• [Org name] — [signal fired] · [source]

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
- "Congratulations on closing the $8M campaign — a great moment to talk about what the endowment needs to do differently now that it's 4x larger."
- "With a new CFO coming in, this is exactly when boards ask whether the current investment advisor is still the right fit."
- "The merger creates a natural reset point — both advisors can't stay, and a clean process protects everyone."
- "A first endowment is a first advisor search — no incumbent to displace, just the right relationship to build."

**Weak examples (avoid):**
- "We saw you hired a new CFO — we'd love to connect." ✗
- "Congratulations on your recent news." ✗
- "Farther Institutional specializes in nonprofits like yours." ✗

---

## HTML report format

### Report structure — always in this order

```
1. Masthead + stats bar + Lark note
2. Slack preview block
3. Score-3 contacts (full detail)
4. Score-2 contacts (full detail)
5. Score-1 contacts (abbreviated)
6. Contacts monitored with no signals fired (gap box only)
7. Coverage gaps this sweep
```

### Score-3 contact block (full detail)

```html
<div class="layer">
  <div class="layer-header">
    <div class="layer-tag tag-score3">Score 3</div>
    <div class="layer-name">[Org name]</div>
  </div>
  <div class="layer-sub">
    [city · org type · est. AUM · HubSpot contact: name, title]
  </div>
  <div class="layer-rule"></div>

  <!-- One finding block per signal -->
  <div class="finding">
    <div class="finding-meta">
      <div class="cert-badge c-confirmed">Confirmed</div>
      <div class="finding-priority p-high">High</div>
    </div>
    <div class="finding-body">
      <div class="finding-title">[Signal name — e.g. New CFO appointed]</div>
      <div class="finding-desc">
        [2–3 sentences. What happened, when, why it matters for Farther.
        Neutral language. No banned phrases.]
      </div>
      <div class="finding-source">
        Source: <a href="[URL]">[domain/path]</a> · retrieved [date]
      </div>
    </div>
  </div>

  <!-- Outreach recommendation (Score-3 only — always present) -->
  <div class="finding-action">
    <strong>Recommended outreach</strong>
    [Outreach angle — 1–2 sentences. Who at Farther should reach out.
    What to say. When to move.]
  </div>
</div>
```

### Score-2 contact block (full detail, no outreach box)

Same as Score-3 but without the outreach recommendation box.
Include a `finding-action` only if the signal combination is unusually strong.

### Score-1 contact block (abbreviated)

```html
<div class="competitor">
  <div class="comp-header">
    <div class="comp-name">[Org name]</div>
    <div class="comp-aka">[city · org type]</div>
    <div class="comp-count">Score 1 · [signal type]</div>
  </div>
  <div class="finding">
    <div class="finding-meta">
      <div class="cert-badge c-[tier]">[Confirmed/Inferred/Speculative]</div>
      <div class="finding-priority p-[level]">[priority]</div>
    </div>
    <div class="finding-body">
      <div class="finding-title">[Signal — one line]</div>
      <div class="finding-desc">[1–2 sentences max.]</div>
      <div class="finding-source">Source: [source] · [date]</div>
    </div>
  </div>
</div>
```

### No-signal contact block (gap box only)

```html
<div class="gap-box">
  <strong>No signals fired this sweep</strong>
  [Contact name] · [Org name] · Last checked: [date] ·
  Next scheduled sweep: [date]
</div>
```

Only include this block for contacts that were actively swept and returned
nothing. Do not list contacts that were not swept this session.

---

## Layer tags for Lark reports

```html
<div class="layer-tag tag-score3">Score 3</div>
<div class="layer-tag tag-score2">Score 2</div>
<div class="layer-tag tag-score1">Score 1</div>
```

Add these CSS rules to the report template for Lark:

```css
.tag-score3 { background: var(--alert-red); color: #f5f4ef; }
.tag-score2 { background: var(--amber); color: #f5f4ef; }
.tag-score1 { background: #3d6b4f; color: #f5f4ef; }
```

---

## Lark note — always include, never skip

The Lark note (green banner at top of report) must explain:
- How many contacts were swept this session
- Any coverage gaps that affected signal quality this sweep
- Confidence asymmetry if first sweep of a contact
- Any signals that were Speculative and should not drive outreach alone

Example:
```
Lark — 47 contacts swept this week. 3 Score-3 contacts identified —
all three have confirmed signals from primary sources and are ready for
outreach. 12 contacts were first-sweep baselines; confidence will improve
as signal history accumulates. LinkedIn verification unavailable for 2
signals this sweep — Apify credits low. Those signals are labeled
Speculative and should not drive outreach without manual confirmation.
```

---

## Compound score display in reports

Always show the score visibly on each contact block:

```html
<div class="comp-count">Score [N] · [N] signals</div>
```

And in the Slack summary, always lead with score tier, not signal type.
The team should see "Score-3" before they see "new CFO."

---

## Language rules

**Use:**
- "This suggests" · "The pattern indicates" · "Based on the data"
- "Worth moving on" · "The window is open" · "A natural conversation starter"
- "This may indicate" · "Unverified — confirm before outreach"

**Avoid:**
- "This proves" · "They are definitely" · "This confirms that"
- "Without a doubt" · "Clearly they are"
- "We saw" · "We noticed" · "We detected"
- Generic outreach angles not tied to the specific signal

---

## Confidence in outreach recommendations

Only recommend outreach when:

| Score | Minimum certainty | Action |
|---|---|---|
| 3 | At least 1 Confirmed signal | Recommend senior outreach immediately |
| 2 | At least 1 Confirmed or Inferred signal | Recommend researched outreach within 2 weeks |
| 1 | Any signal, any tier | Recommend soft touch only — monitor |

**Never recommend outreach based on a Speculative signal alone.**
Flag it, watch it, and wait for confirmation.

---

## No action available?

If a contact fired a signal but no clear outreach angle exists:
```
No outreach angle identified. File for context — monitor next sweep
for confirming signal before acting.
```

---

## File naming

```
lark/outputs/YYYY-MM-DD-lark-weekly.html     ← standard weekly
lark/outputs/YYYY-MM-DD-lark-[org-slug].html ← single contact deep dive
```

---

## HTML delivery

In Claude Code → write directly to `outputs/YYYY-MM-DD-lark-weekly.html`
In Claude Project → produce as artifact typed as `text/html`
Never output raw HTML as an inline code block.
