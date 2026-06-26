# signals.md — Lark Standing Trigger Signals

> Lark reads this at the start of every sweep and before running Channel 8
> (signal cross-check).
> Lark writes to this file when a signal pattern is confirmed, refined, or retired.
> Humans may review but should not overwrite confirmed entries.
> Last updated: 2026-06-24

---

## How Channel 8 uses this file

At the end of every sweep, after Channels 1–7 have run, Lark:
1. Reads all Active signals in this file
2. Cross-references every finding from this sweep against each signal's known
   characteristics and sources
3. If a new finding matches a standing signal → escalates to the appropriate tier
   and notes "consistent with standing signal"
4. If a contact shows 2+ signals firing simultaneously → applies compound scoring
   and flags as Score-2 or Score-3
5. If a new signal type is emerging across 2+ contacts → creates a new entry
   below as Watching

---

## Active Signals — High Tier

### ⚑ SIG-001 — New CFO or Finance Director
**Signal type:** Leadership change
**Tier:** High
**Action window:** Move within 60–90 days of appointment
**Confidence:** High — directly owns the investment advisor relationship

**Why it fires:**
New CFOs almost always conduct a quiet market review within their first 90 days
to establish credibility with the board. The investment advisor relationship is
one of the first financial partnerships they scrutinize. Even when the incumbent
is performing well, a new CFO wants the relationship to be their choice, not
inherited.

**Strongest form of this signal:**
- CFO hired from outside the organization (not internal promotion)
- Job posting language included "investment oversight" or "endowment management"
- Organization has not changed advisors in 3+ years (incumbent entrenchment
  creates more motivation to reset)

**Sources to check every sweep:**
- LinkedIn: `"[org name]" "CFO" OR "Chief Financial Officer" OR "Finance Director"
  "joins" OR "named" OR "appointed" 2026`
- Org website: staff/leadership page for changes
- Press releases: `"[org name]" "CFO" OR "finance director" 2026`

**What to check on the profile:**
- When was the last advisor change (if known)?
- Does the new CFO have a financial advisory background themselves?
- Is there a capital campaign or AUM event in the same window? (Score-2 or 3)

**New iterations logged:**
- 2026-02-11 · MADD (Irving TX) · Kevin Byrne as CFO · Source: madd.org · ACTION WINDOW EXPIRED May 12, 2026
- 2026-06-17 (validation) · Historic Macon Foundation (Macon GA) · Stefanie Joyner Director of Finance And Operations · Source: LinkedIn Ch5 · Inferred · Compound with SIG-002 (Emily Hopkins ED) → Score-2 · window through Aug 1 2026
- 2026-06-17 (validation) · NSABP Foundation Inc (Pittsburgh PA) · Pedro Barelli CFO · Source: LinkedIn Ch5 · Inferred · ACTIVE — verify hire date · AUM $97.9M
- 2026-06-17 (validation) · International Tennis Hall of Fame (Newport RI) · Mary L. Contadino VP Finance · Source: LinkedIn Ch5 · Inferred · verify hire date and whether VP is top finance role · AUM $94.1M
- 2026-06-17 (validation) · Urban Edge Housing Corporation (Boston MA) · Claire Sokolowski Director of Finance · Source: LinkedIn Ch5 · Inferred · verify hire date and investable assets vs. real estate · AUM $74.7M CSV
- 2026-06-17 (validation) · Boston Senior Home Care Inc (Boston MA) · Todd Spencer CFO · Source: LinkedIn Ch5 · Inferred · verify hire date · AUM $21.0M
- 2026-06-17 (validation) · Kids In Need Foundation (Little Canada MN) · Martin Christian Boye Director Finance And Accounting · Source: LinkedIn Ch5 · Inferred · verify hire date · AUM $19.5M
- 2026-06-17 (validation) · DT Institute (Arlington VA) · Dicky Dooradi VP Finance And Operations · Source: LinkedIn Ch5 · Inferred · verify hire date · AUM $2.5M
- 2026-06-17 (validation) · EFI Foundation (Washington DC) · Lin Yuan Director Energy Finance · Source: LinkedIn Ch5 · Inferred · verify whether role is org finance vs. program finance · AUM $2.7M

---

### ⚑ SIG-002 — New CEO or Executive Director
**Signal type:** Leadership change
**Tier:** High
**Action window:** Move within 90–180 days of appointment
**Confidence:** High — triggers broad vendor review across the organization

**Why it fires:**
Incoming leaders review all significant vendor relationships in their first 6
months. Investment advisors are high-visibility relationships — they appear in
board materials, carry fee implications, and reflect on the ED's fiduciary
judgment. A new ED inheriting a relationship they didn't choose has every
incentive to validate or replace it.

**Strongest form of this signal:**
- ED hired from outside the organization
- Announcement language includes "strategic reset," "new direction," or
  "transformation"
- Previous ED had a long tenure (10+ years) — long tenures entrench vendors

**Sources to check every sweep:**
- LinkedIn: `"[org name]" "executive director" OR "CEO" "joins" OR "named"
  OR "appointed" 2026`
- Org website: leadership page, news/press section
- Local nonprofit news: `"[org name]" "new executive director" 2026`
- GuideStar / Candid: leadership changes sometimes reflected in filings

**What to check on the profile:**
- How long was the previous ED in the role?
- Does the new ED have a finance or operations background?
- Is there a CFO change in the same window? (Score-3 if both)

**New iterations logged:**
- 2026-06-01 · The Autism Community in Action / TACA (Irvine CA) · Mike Le ED (external hire, JD/MBA) · Source: PRNewswire Jun 1, 2026 · Confirmed · AUM $1.95M (near floor) · ACTIVE — window through ~Dec 1, 2026
- 2026-06-01 · Candid (New York NY) · John Brothers Interim P&CEO · board member transition · Source: candid.org May 27, 2026 · Confirmed · AUM $106.9M · ACTIVE — window through ~Nov 28, 2026 · monitor for permanent hire
- 2026-05-29 · Unleashing Potential (St. Louis MO) · Darlene Sowell retired (17-yr tenure) · Bridget Jones interim Jun 4 · ACTIVE — window open through ~Nov 25, 2026 · monitor for permanent hire
- 2026-02-02 · Historic Macon Foundation (Macon GA) · Emily Hopkins named ED · Source: maconchamber.com · ACTIVE — window closes Aug 1, 2026 · URGENT — Score-2 compound with SIG-001 (Stefanie Joyner Dir Finance)
- 2025-09-16 · ActionAid USA (Washington DC) · Niranjali Amerasinghe new ED · ACTION WINDOW EXPIRED Mar 14, 2026
- 2025-02-05 · Joni and Friends (Agoura Hills CA) · Pastor Shawn Thornton new President · ACTION WINDOW EXPIRED Aug 4, 2025
- 2025-02-19 · Teen Cancer America (Santa Monica CA) · Shannon Sullivan new CEO · ACTION WINDOW EXPIRED Aug 18, 2025

---

### ⚑ SIG-003 — Capital Campaign Close
**Signal type:** Financial event
**Tier:** High
**Action window:** Move immediately — window is 30–60 days post-announcement
**Confidence:** High — creates direct capability mismatch with incumbent advisor

**Why it fires:**
Campaign completion brings a sudden, often transformational inflow of assets.
An organization that closed a $20M campaign when their endowment was $3M now
has a materially different investment problem. The incumbent advisor was sized
for the old endowment — boards and finance committees instinctively ask "do
we have the right advisor for this?"

**Strongest form of this signal:**
- Campaign goal exceeded (oversubscribed campaigns create more urgency)
- Campaign was for endowment growth specifically (not capital/facilities)
- Organization has never managed assets at this scale before

**Sources to check every sweep:**
- Org website: campaign pages, news announcements
- Press releases: `"[org name]" "campaign" "goal" OR "raised" OR "complete"
  OR "close" 2026`
- Local news: `"[org name]" capital campaign complete 2026`
- Nonprofit news outlets: philanthropy.com, nonprofitquarterly.org,
  Chronicle of Philanthropy

**What to check on the profile:**
- What was the campaign goal? What did they raise?
- Is there a leadership change in the same window? (Score-3)
- What is the estimated pre-campaign endowment size?

**New iterations logged:**
[None yet — log confirmed fires here with date, org, and source]

---

### ⚑ SIG-004 — Large Gift or Bequest Announced
**Signal type:** Financial event
**Tier:** High
**Action window:** Move within days — rivals see the same press release
**Confidence:** High — public, timely, unambiguous trigger

**Why it fires:**
A named major gift (typically $1M+) is a public signal that the investment
conversation is imminent. The gift announcement often precedes formal receipt
by weeks or months — that gap is the outreach window. The org is in the
"we just announced this" moment, before the incumbent advisor has re-entrenched.

**Threshold guidance:**
- $500K–$1M: worth a soft touch if paired with another signal
- $1M–$5M: standalone High signal for most contacts in the pipeline
- $5M+: treat as Score-3 regardless of other signals — move immediately

**Sources to check every sweep:**
- Press releases: `"[org name]" "gift" OR "donation" OR "bequest" OR "pledge"
  "$" 2026`
- Local news: `"[org name]" million gift 2026`
- Chronicle of Philanthropy, Inside Philanthropy
- Org website: news, donor recognition pages

**What to check on the profile:**
- Is the gift restricted or unrestricted? (Unrestricted = more likely to flow
  to endowment)
- Is there a leadership change in the same window?
- Is the org in a capital campaign? (Gift may be campaign-related)

**New iterations logged:**
- 2026-05-14 · Fiver Children's Foundation (New York NY) · Annual benefit raised $1.5M vs. $1.2M goal (25% over) · Source: GlobeNewswire Jun 18, 2026 · ACTIVE — window closes ~Jul 22, 2026

---

## Active Signals — Medium Tier

### ⚑ SIG-005 — New Investment Committee Chair
**Signal type:** Governance change
**Tier:** Medium
**Action window:** Move within 60–90 days of appointment
**Confidence:** Medium — personal fiduciary accountability creates review motivation

**Why it fires:**
A new investment committee chair has personal accountability for the advisor
relationship — their name is on the governance decisions. New chairs frequently
call a market review not because the incumbent is failing, but as a governance
demonstration to the rest of the board. It's a political and fiduciary move
as much as a performance one.

**Sources to check every sweep:**
- Org website: board listing, committee structure pages
- Board meeting minutes (public orgs and government-adjacent foundations)
- LinkedIn: `"[org name]" "investment committee" "chair" OR "chairman"
  "named" OR "appointed" 2026`

**New iterations logged:**
[None yet]

---

### ⚑ SIG-006 — Capital Campaign Launch
**Signal type:** Financial event
**Tier:** Medium
**Action window:** Move within 30–60 days of announcement
**Confidence:** Medium — signals incoming asset growth, entry point is capability

**Why it fires:**
A campaign launch signals the org will receive significant multi-year inflows.
The outreach angle is forward-looking: does their current advisor have the
capability to manage a growing, more complex endowment? This is a capability
conversation, not a performance conversation — and it's easier to win.

**Sources to check every sweep:**
- Org website: campaign pages, news section
- Press releases: `"[org name]" "capital campaign" OR "campaign launch"
  OR "announces campaign" 2026`
- Local news

**New iterations logged:**
[None yet]

---

### ⚑ SIG-007 — AUM Threshold Crossed
**Signal type:** Financial growth
**Tier:** Medium (confirmation layer — best paired with a fresher signal)
**Action window:** Use as confirmation; do not outreach on 990 data alone
**Confidence:** Medium — 990 data runs 12–18 months behind real time

**Why it fires:**
Endowment growth beyond key thresholds ($5M, $10M, $25M, $50M) often outpaces
the incumbent advisor's capabilities or fee model. A boutique community advisor
managing a $2M endowment is not the right fit for a $15M endowment. The
mismatch creates a natural opening — but 990 latency means this signal
confirms a past state, not a present one.

**Threshold guidance:**
- Crossing $5M: first-time professional management needed
- Crossing $10M: institutional-grade advisor conversation warranted
- Crossing $25M: OCIO conversation becomes relevant
- Crossing $50M: full institutional mandate, RFP-level process likely

**Sources to check every sweep:**
- IRS 990: Schedule D (endowment funds), Part X (balance sheet)
- ProPublica Nonprofit Explorer, Candid/GuideStar
- Note: always state the 990 tax year when citing AUM figures

**New iterations logged:**
[None yet]

---

### ⚑ SIG-008 — Merger or Organizational Restructuring
**Signal type:** Governance change
**Tier:** Medium
**Action window:** Move immediately — chaos window is short
**Confidence:** Medium — creates forced advisor review, but timeline is uncertain

**Why it fires:**
Mergers create governance chaos: two boards, two investment committees, and
often two existing advisors. The merged org almost always ends up doing a
clean sweep to avoid the political problem of choosing one incumbent over the
other. The window is during the transition, before a new governance structure
settles.

**Sources to check every sweep:**
- Press releases: `"[org name]" "merger" OR "merge" OR "consolidation"
  OR "affiliation" 2026`
- Nonprofit news: NonProfit Times, Nonprofit Quarterly
- State charity registration databases (for formal merger filings)

**New iterations logged:**
[None yet]

---

## Contextual Signals (Weak standalone — use as confirmation only)

### ⚑ SIG-009 — New Strategic Plan Published
**Signal type:** Governance event
**Tier:** Contextual
**Action window:** Soft outreach only — confirm endowment language before acting
**Confidence:** Low standalone · Medium when paired with AUM or leadership signal

**Why it fires (conditionally):**
Strategic plans that include explicit endowment growth targets signal the org
knows their current financial setup may not be adequate. Language like "grow
endowment to $X by [year]" or "build a permanent endowment" is the tell.
Plans without investment language are not a signal.

**Sources:** Org website · Annual report · Press announcing new strategic plan

**New iterations logged:**
[None yet]

---

### ⚑ SIG-010 — First-Time Endowment Established
**Signal type:** Financial event
**Tier:** Contextual (High if confirmed)
**Action window:** Move immediately — no incumbent to displace
**Confidence:** Medium — often confirmed only via 990 lag

**Why it fires:**
First-time endowment = first-time advisor search. There is no incumbent
relationship to overcome. The org is starting from zero and needs guidance
on everything — IPS, asset allocation, spending policy, governance. This is
Farther's cleanest entry point if the org is the right size.

**Sources:** IRS 990 (first appearance of endowment assets on Schedule D) ·
Press releases · Org website announcement

**New iterations logged:**
[None yet]

---

## Watching (Emerging Patterns — Not Yet Confirmed)

> Add entries here when a signal type appears across 2+ contacts in the same
> sweep but doesn't yet match a confirmed signal definition above.

[None yet — Lark adds entries here as patterns emerge across the pipeline]

---

## Retired Signals

> Signal types that proved too slow, too noisy, or not actionable for Farther's
> pipeline. Documented so they are not re-added without justification.

[None yet]

---

## Compound Scoring Reference

| Score | Signals present | Recommended action |
|---|---|---|
| 3 | 2+ High signals, or High + Medium + Contextual | Senior personalized outreach immediately |
| 2 | 1 High + 1 Medium, or 2+ Medium signals | Researched outreach within 2 weeks |
| 1 | Single signal, any tier | Soft touch — monitor closely next sweep |

Score-3 contacts are the highest priority output Lark produces.
Flag these prominently in both Slack and the HTML report.

---

## Instructions to Lark
- Read this file at the start of every sweep before running Channel 8
- After Channel 8 runs: update "New iterations logged" for any active signal
  that fired this sweep
- When a new signal type is confirmed across 2+ contacts: add a new Active
  Signal entry
- When a Watching entry reaches Medium+ confidence: move it to Active Signals
- When a signal type proves not actionable: move it to Retired with a note
- Never hand this file to a human to write — Lark owns it

**Channel 9 — RFP Intelligence:**
After Channels 1–8 and after Channel 8 cross-check, run the RFP Intelligence
channel per `skills/rfp-intelligence.md`. RFP findings are NOT scored as
SIG-001 through SIG-010 signals. They are stored in `HistoricalRFPData/`
and reported in a separate HTML report. A pipeline match is noted on the
org's profile but does not trigger automatic outreach.
Update `rfp_intelligence_sector_rotation` in memory.md after each sweep.