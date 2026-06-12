# hubspot-properties.md — Lark · HubSpot Custom Property Definitions

> This file defines every custom property Lark writes to HubSpot.
> All properties live on the Company object unless noted.
> Assume these are net new — verify against existing schema before creating.
> Last updated: 2026-06-12

---

## MCP connection

HUBSPOT_MCP_KEY: [PENDING]
MCP_SERVER: https://mcp.hubspot.com/anthropic
OBJECT_TYPE: companies

> When the MCP key is available: replace [PENDING] above, test a single
> company read, confirm write-back works on one record before running
> a full sweep.

---

## Setup instructions (for HubSpot admin)

All properties below should be created under:
Settings → Properties → Company properties → Create property

Group them under a new property group called **"Lark Intelligence"**
so they are visually separated from native HubSpot properties and
easy to find / filter in views and reports.

---

## Property definitions

### Core signal properties

| Internal name | Display label | Field type | Options / notes |
|---|---|---|---|
| `lark_signal_type` | Lark — Signal type | Single-line text | SIG-001 through SIG-010 · e.g. `SIG-001` |
| `lark_signal_date` | Lark — Signal detected | Date picker | Date Lark detected the signal |
| `lark_signal_source` | Lark — Signal source | Single-line text | URL or source reference |
| `lark_signals_active` | Lark — All active signals | Multi-line text | Comma-separated e.g. `SIG-001, SIG-003` |

### Scoring properties

| Internal name | Display label | Field type | Options / notes |
|---|---|---|---|
| `lark_compound_score` | Lark — Compound score | Number | 0, 1, 2, or 3 |
| `lark_score_updated` | Lark — Score last updated | Date picker | Date score was last recalculated |
| `lark_action_window` | Lark — Action window | Single-line text | e.g. `Move within 60 days · expires 2026-08-12` |

### Status property

| Internal name | Display label | Field type | Options |
|---|---|---|---|
| `lark_contact_status` | Lark — Contact status | Dropdown select | Cold · Signal Detected · Reviewed · Active Outreach |

> Note: this is a Lark-specific status field, separate from HubSpot's
> native Lifecycle Stage and Lead Status fields. Do not overwrite those.
> Lark writes only to lark_contact_status.

### Enrichment properties

| Internal name | Display label | Field type | Options / notes |
|---|---|---|---|
| `lark_aum_estimated` | Lark — Estimated AUM ($) | Number | Dollar figure — no commas |
| `lark_aum_source` | Lark — AUM source | Single-line text | e.g. `IRS 990 · tax year 2023` |
| `lark_incumbent_advisor` | Lark — Incumbent advisor | Single-line text | Advisor firm name if found |
| `lark_incumbent_source` | Lark — Advisor source | Single-line text | How advisor was identified |

### Operational properties

| Internal name | Display label | Field type | Options / notes |
|---|---|---|---|
| `lark_last_sweep` | Lark — Last swept | Date picker | Date of most recent Lark sweep |
| `lark_notes` | Lark — Intelligence notes | Multi-line text | Enrichment notes, open threads |
| `lark_propublica_ein` | Lark — EIN (ProPublica) | Single-line text | EIN for ProPublica/990 lookups |

---

## What Lark writes per sweep event

When a signal fires and a match is confirmed, Lark writes:

```
lark_signal_type        ← most recent signal code
lark_signal_date        ← today's date
lark_signal_source      ← URL of source
lark_signals_active     ← append to existing (do not overwrite)
lark_compound_score     ← recalculated after stacking
lark_score_updated      ← today's date
lark_action_window      ← window string + expiry date
lark_contact_status     ← Signal Detected (if was Cold)
lark_last_sweep         ← today's date
lark_notes              ← enrichment summary
lark_aum_estimated      ← if ProPublica returns data
lark_aum_source         ← if AUM written
lark_incumbent_advisor  ← if found in 990 or web
lark_propublica_ein     ← if EIN found
```

When no signal fires, Lark writes only:
```
lark_last_sweep         ← today's date
```

---

## If properties already exist

Before creating any property above, check Settings → Properties →
Company properties and search for "lark_". If any already exist:
- Do not duplicate
- Note the existing internal name and update this file accordingly
- If the field type differs from what's defined here, flag for review
  before Lark writes to it

---

## Phase 2 additions (after test cohort validation)

These properties are not needed for Phase 1 but should be created
before expanding to the full 65K list:

| Internal name | Display label | Field type | Notes |
|---|---|---|---|
| `lark_window_expires` | Lark — Window expires | Date picker | For aging alerts in report |
| `lark_outreach_angle` | Lark — Outreach angle | Multi-line text | Lark-suggested first message angle |
| `lark_score_history` | Lark — Score history | Multi-line text | Timestamped score log |
