#!/usr/bin/env python3
"""
lark_report.py — Lark HTML Report Generator
============================================
Generates the weekly HTML report and Slack preview from structured sweep data.
Offloads the most token-intensive step in Phase 4 from Lark's context.

TOKEN SAVINGS:
    Report generation was previously done by Lark constructing HTML inline.
    At ~600 lines of HTML per report, this consumed significant context.
    This utility takes structured data dicts and outputs the full HTML.
    Lark's only job: populate the data structures, call generate_report().

USAGE — Phase 4:
    from utilities.lark_report import generate_report, SweepData, ContactResult

    sweep = SweepData(
        date="2026-07-17",
        sweep_num=3,
        lookback_start="2026-06-17",
        lookback_end="2026-07-17",
        searches_run=28,
        signals_batched=31,
        records_searched=190406,
        high_matches=4,
        ambiguous=8,
        no_match=19,
    )

    # Add Score-1 contacts, Noted contacts, AMBIGUOUS entries
    sweep.add_score1(ContactResult(...))
    sweep.add_noted(ContactResult(...))
    sweep.add_ambiguous(AmbiguousEntry(...))

    path = generate_report(sweep, output_dir="outputs/")
    print(f"Report written to: {path}")

OUTPUT:
    outputs/YYYY-MM-DD-lark-weekly.html
"""

import os
import html as html_lib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class EnrichmentData:
    """ProPublica 990 enrichment fields for a contact card."""
    ein:          Optional[str] = None
    total_assets: Optional[int] = None
    tax_year:     Optional[int] = None
    ntee_code:    Optional[str] = None
    total_revenue: Optional[int] = None
    aum_note:     Optional[str] = None

    def aum_display(self) -> str:
        if self.total_assets is None:
            return "Not found"
        return f"${self.total_assets:,}"

    def aum_range(self) -> str:
        if self.total_assets is None:
            return "Unknown"
        a = self.total_assets
        if a >= 50_000_000: return ">$50M · institutional mandate"
        if a >= 25_000_000: return ">$25M · OCIO conversation relevant"
        if a >= 10_000_000: return ">$10M · institutional-grade advisor"
        if a >=  5_000_000: return ">$5M · first professional management"
        return ">$1M · AUM threshold met"


@dataclass
class HubSpotWriteback:
    """HubSpot property fields staged for write-back."""
    org_name_csv:    str = ""
    signal_type:     str = ""
    signal_date:     str = ""
    signal_source:   str = ""
    compound_score:  int = 0
    score_updated:   str = ""
    action_window:   str = ""
    contact_status:  str = "Signal Detected"
    aum_estimated:   Optional[int] = None
    aum_source:      str = ""
    propublica_ein:  Optional[str] = None
    last_sweep:      str = ""
    notes:           str = ""


@dataclass
class ContactResult:
    """A single confirmed HIGH match contact with signal data."""
    # Identity
    org_name:       str
    city_state:     str
    org_type:       str          # from NTEE / description
    score:          int
    compound_score: int          # 1, 2, or 3

    # Signal
    signal_type:    str          # SIG-001 through SIG-010
    signal_name:    str          # "New CFO / Finance Director"
    signal_date:    str          # ISO date
    signal_source:  str          # URL
    signal_source_label: str     # "candid.org · May 27, 2026"
    confidence:     str          # "Confirmed" / "Inferred" / "Speculative"
    priority:       str          # "High" / "Medium" / "Contextual"
    finding_text:   str          # 2-3 sentence finding description

    # Action
    outreach_angle: str          # 1 sentence
    action_window:  str          # "Move within 90–180 days · expires [date]"

    # Enrichment
    enrichment:     Optional[EnrichmentData] = None
    hubspot:        Optional[HubSpotWriteback] = None

    # Noted fields (window-expired contacts)
    is_noted:       bool = False
    window_expired: bool = False
    watch_for:      str = ""     # follow-on signals to watch


@dataclass
class AmbiguousEntry:
    """An AMBIGUOUS fuzzy match requiring manual review."""
    org_name:       str
    score:          int
    signal_type:    str
    signal_name:    str
    signal_date:    str
    in_window:      bool
    priority_flag:  bool         # True = high-priority ambiguous (e.g. score 74+)
    review_text:    str          # full review instructions
    source:         str = ""


@dataclass
class DiscardedEntry:
    """A low-score NO_MATCH or confirmed false positive."""
    org_name:        str
    reason:          str
    score:           int  = 0
    best_candidate:  str  = ""
    is_no_match:     bool = False   # True = scored too low · human review for discard


@dataclass
class ChannelResult:
    """Summary of a single channel's sweep results."""
    channel_num: str             # "Ch 1"
    signals:     str             # "SIG-001, SIG-002, SIG-005"
    status:      str             # "Active" / "Deferred"
    result:      str             # one line result description
    fired:        bool = False
    deferred:    bool = False


@dataclass
class CoverageGap:
    """A known coverage gap to note in the report."""
    text: str


@dataclass
class SweepData:
    """All data needed to generate a full Lark sweep report."""
    # Header
    date:              str       # "2026-07-17"
    sweep_num:         int
    lookback_start:    str       # "2026-06-17"
    lookback_end:      str       # "2026-07-17"

    # Stats
    searches_run:      int
    signals_batched:   int
    records_searched:  int
    high_matches:      int
    ambiguous:         int
    no_match:          int
    false_positives:   int = 0

    # Contacts
    score3_contacts:   list[ContactResult]   = field(default_factory=list)
    score2_contacts:   list[ContactResult]   = field(default_factory=list)
    score1_contacts:   list[ContactResult]   = field(default_factory=list)
    noted_contacts:    list[ContactResult]   = field(default_factory=list)
    ambiguous_entries: list[AmbiguousEntry]  = field(default_factory=list)
    discarded_entries: list[DiscardedEntry]  = field(default_factory=list)
    channel_results:   list[ChannelResult]   = field(default_factory=list)
    coverage_gaps:     list[CoverageGap]     = field(default_factory=list)

    # Write-back
    hubspot_status:    str = "STAGED — MCP key pending"
    hubspot_queued:    int = 0

    # Transparency note
    transparency_note: str = ""

    def add_score3(self, c: ContactResult):
        c.compound_score = 3; self.score3_contacts.append(c)

    def add_score2(self, c: ContactResult):
        c.compound_score = 2; self.score2_contacts.append(c)

    def add_score1(self, c: ContactResult):
        c.compound_score = 1; self.score1_contacts.append(c)

    def add_noted(self, c: ContactResult):
        c.is_noted = True; self.noted_contacts.append(c)

    def add_ambiguous(self, a: AmbiguousEntry):
        self.ambiguous_entries.append(a)

    def score1_count(self) -> int:
        return len(self.score1_contacts)

    def score2_count(self) -> int:
        return len(self.score2_contacts)

    def score3_count(self) -> int:
        return len(self.score3_contacts)


# ── HTML HELPERS ──────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    """HTML-escape a string."""
    return html_lib.escape(str(text or ""))


def _confidence_badge(confidence: str) -> str:
    cls = {"Confirmed": "c-confirmed", "Inferred": "c-inferred"}.get(
        confidence, "c-speculative"
    )
    return f'<div class="cert-badge {cls}">{_e(confidence)}</div>'


def _priority_badge(priority: str) -> str:
    cls = {"High": "p-high", "Medium": "p-medium"}.get(priority, "p-ctx")
    return f'<div class="p-badge {cls}">{_e(priority)}</div>'


def _score_tag(score: int) -> str:
    cls = {3: "tag-score3", 2: "tag-score2", 1: "tag-score1"}.get(score, "tag-score1")
    return f'<span class="card-score-tag {cls}">Score {score}</span>'


# ── SECTION BUILDERS ──────────────────────────────────────────────────────────

def _build_slack_preview(s: SweepData) -> str:
    """Build the Slack preview block."""
    rows = []

    rows.append(f'<div><span class="s-bold">🪶 Lark · Monthly Brief · {_e(s.date)}</span></div>')
    rows.append(f'<div><span class="s-dim">Sweep {s.sweep_num} · {s.signals_batched} signals batched · {s.records_searched:,} contacts · 30-day lookback</span></div>')
    rows.append('<hr class="slack-divider">')

    if s.score3_contacts:
        rows.append('<div><span class="s-bold">Score-3 — senior outreach immediately</span></div>')
        for c in s.score3_contacts:
            rows.append(f'<div>🔴 <span class="s-bold">{_e(c.org_name)}</span> — {_e(c.city_state)} · Est. AUM ${_e(str(c.enrichment.aum_display() if c.enrichment else "?"))}</div>')
            rows.append(f'<div><span class="s-amber">{_e(c.signal_type)}</span> — {_e(c.finding_text[:120])} · <span class="s-dim">{_e(c.signal_source_label)}</span></div>')
            rows.append(f'<div><span class="s-dim">Angle: {_e(c.outreach_angle[:120])}</span></div>')
        rows.append('<hr class="slack-divider">')

    if s.score1_contacts or s.score2_contacts:
        rows.append('<div><span class="s-bold">Score-1 contacts — soft touch recommended</span></div>')
        for c in (s.score2_contacts + s.score1_contacts):
            rows.append(f'<div>🟢 <span class="s-bold">{_e(c.org_name)}</span> — {_e(c.city_state)}</div>')
            rows.append(f'<div><span class="s-green">{_e(c.signal_type)}</span> — {_e(c.finding_text[:120])} · <span class="s-dim">{_e(c.signal_source_label)}</span></div>')
            rows.append(f'<div><span class="s-dim">Window: {_e(c.action_window)}</span></div>')
        rows.append('<hr class="slack-divider">')

    if s.noted_contacts:
        rows.append('<div><span class="s-bold">High match · Noted — window passed · monitor for follow-on</span></div>')
        for c in s.noted_contacts:
            aum = c.enrichment.aum_display() if c.enrichment else "?"
            rows.append(f'<div>🔵 <span class="s-bold">{_e(c.org_name)}</span> — {_e(c.city_state)} · AUM {_e(str(aum))} · Score {c.score}</div>')
            rows.append(f'<div><span class="s-blue">{_e(c.signal_type)}</span> — {_e(c.finding_text[:100])} · <span class="s-dim">{_e(c.signal_source_label)}</span></div>')
            if c.watch_for:
                rows.append(f'<div><span class="s-noted">Do not outreach now. Watch for: {_e(c.watch_for)}</span></div>')
        rows.append('<hr class="slack-divider">')

    if s.ambiguous_entries:
        rows.append('<div><span class="s-bold">Ambiguous — manual review required</span></div>')
        for a in s.ambiguous_entries:
            flag = " · Signal in window ✓" if a.in_window else ""
            rows.append(f'<div>🟡 <span class="s-bold">{_e(a.org_name)}</span> — Score {a.score} · {_e(a.signal_type)} ({_e(a.signal_date)}){_e(flag)}</div>')
        rows.append('<hr class="slack-divider">')

    gaps = [g.text for g in s.coverage_gaps]
    if gaps:
        rows.append(f'<div><span class="s-dim">Coverage gap: {_e(" · ".join(gaps[:2]))}</span></div>')

    rows.append(f'<div><span class="s-dim">HubSpot write-back: {_e(s.hubspot_status)} · {s.hubspot_queued} records queued</span></div>')
    next_sweep = "Next sweep: see schedule"
    rows.append(f'<div><span class="s-dim">Full report attached · {next_sweep} · Questions: mention @Lark</span></div>')

    return "\n    ".join(rows)


def _build_contact_card(c: ContactResult) -> str:
    """Build a full Score-1/2/3 contact card."""
    enrich_html = ""
    if c.enrichment:
        e = c.enrichment
        enrich_html = f"""
      <div class="enrich-box">
        <strong>Enrichment · ProPublica 990</strong>
        <div class="enrich-grid">
          <div class="enrich-item"><label>EIN</label><span>{_e(e.ein or "—")}</span></div>
          <div class="enrich-item"><label>Total Assets</label><span>{_e(e.aum_display())}</span></div>
          <div class="enrich-item"><label>990 Tax Year</label><span>{_e(str(e.tax_year or "—"))}</span></div>
          <div class="enrich-item"><label>NTEE Code</label><span>{_e(e.ntee_code or "—")}</span></div>
          <div class="enrich-item"><label>Revenue</label><span>{_e(f"${e.total_revenue:,}" if e.total_revenue else "—")}</span></div>
          <div class="enrich-item"><label>AUM Range</label><span>{_e(e.aum_range())}</span></div>
        </div>
        {f'<p style="margin-top:10px;font-size:12px;color:#5a5852;"><strong>AUM note:</strong> {_e(e.aum_note)}</p>' if e.aum_note else ""}
      </div>"""

    hubspot_html = ""
    if c.hubspot:
        h = c.hubspot
        hubspot_html = f"""
      <div class="hubspot-box">
        <strong>HubSpot write-back · STAGED (MCP key pending)</strong>
        <div class="prop-row"><span class="prop-name">Org Name (CSV):</span> <span class="prop-val">{_e(h.org_name_csv)}</span></div>
        <div class="prop-row"><span class="prop-name">lark_signal_type:</span> <span class="prop-val">{_e(h.signal_type)}</span></div>
        <div class="prop-row"><span class="prop-name">lark_signal_date:</span> <span class="prop-val">{_e(h.signal_date)}</span></div>
        <div class="prop-row"><span class="prop-name">lark_compound_score:</span> <span class="prop-val">{h.compound_score}</span></div>
        <div class="prop-row"><span class="prop-name">lark_action_window:</span> <span class="prop-val">{_e(h.action_window)}</span></div>
        <div class="prop-row"><span class="prop-name">lark_contact_status:</span> <span class="prop-val">{_e(h.contact_status)}</span></div>
        {f'<div class="prop-row"><span class="prop-name">lark_aum_estimated:</span> <span class="prop-val">{h.aum_estimated:,}</span></div>' if h.aum_estimated else ""}
        <div class="prop-row"><span class="prop-name">lark_last_sweep:</span> <span class="prop-val">{_e(h.last_sweep)}</span></div>
        <div class="prop-row"><span class="prop-name">lark_notes:</span> <span class="prop-val">{_e(h.notes)}</span></div>
      </div>"""

    return f"""
  <div class="card">
    <div class="card-header">
      {_score_tag(c.compound_score)}
      <div class="card-org">
        <div class="card-org-name">{_e(c.org_name)}</div>
        <div class="card-org-sub">{_e(c.city_state)} · {_e(c.org_type)}</div>
      </div>
    </div>
    <div class="card-body">
      <div class="finding">
        <div class="finding-badges">
          {_confidence_badge(c.confidence)}
          {_priority_badge(c.priority)}
        </div>
        <div class="finding-content">
          <div class="finding-title">{_e(c.signal_type)} — {_e(c.signal_name)}</div>
          <div class="finding-desc">{_e(c.finding_text)}</div>
          <div class="finding-source">Source: <a href="{_e(c.signal_source)}">{_e(c.signal_source_label)}</a></div>
        </div>
      </div>
      <div class="action-box">
        <strong>Outreach angle</strong>
        <p>{_e(c.outreach_angle)}</p>
        <div class="action-window">Window: {_e(c.action_window)}</div>
      </div>
      {enrich_html}
      {hubspot_html}
    </div>
  </div>"""


def _build_noted_card(c: ContactResult) -> str:
    """Build a HIGH MATCH · NOTED card."""
    enrich_items = ""
    if c.enrichment:
        e = c.enrichment
        enrich_items = f"""
        <div class="noted-enrich-item"><label>Match score</label><span>{c.score}</span></div>
        <div class="noted-enrich-item"><label>AUM</label><span>{e.aum_display()}</span></div>
        <div class="noted-enrich-item"><label>EIN</label><span>{_e(e.ein or "—")}</span></div>
        <div class="noted-enrich-item"><label>NTEE</label><span>{_e(e.ntee_code or "—")}</span></div>"""

    window_pill = ""
    if c.window_expired:
        window_pill = '<div class="noted-window-expired">Window Expired</div>'

    return f"""
  <div class="noted-v2">
    <div class="noted-v2-header">
      <div class="noted-match-tag">
        <div class="tag-high-badge">HIGH · Score {c.score}</div>
        <div class="tag-noted-badge">NOTED</div>
      </div>
      <div class="noted-v2-org">
        <div class="noted-v2-name">{_e(c.org_name)}</div>
        <div class="noted-v2-sub">{_e(c.city_state)} · {_e(c.org_type)}</div>
      </div>
    </div>
    <div class="noted-v2-body">
      <div class="noted-signal-row">
        <div class="noted-signal-label">{_e(c.signal_type)} — {_e(c.signal_name)}</div>
        {window_pill}
      </div>
      <div class="noted-detail-text">{_e(c.finding_text)}</div>
      {f'<div class="noted-watchfor"><strong>Watch for next sweep</strong>{_e(c.watch_for)}</div>' if c.watch_for else ""}
      <div class="noted-enrich">{enrich_items}</div>
    </div>
  </div>"""


def _build_ambiguous_card(a: AmbiguousEntry) -> str:
    """Build an AMBIGUOUS review card."""
    border = ' style="border-left: 4px solid var(--green);"' if a.priority_flag else ""
    in_window = " · Signal in window ✓" if a.in_window else ""
    return f"""
  <div class="ambig-card"{border}>
    <div class="ambig-header">
      <span class="ambig-score-tag">AMBIGUOUS · Score {a.score}</span>
      <div class="ambig-org">{_e(a.org_name)}{_e(in_window)}</div>
    </div>
    <div class="ambig-signal">{_e(a.signal_type)} — {_e(a.signal_name)} · {_e(a.signal_date)}</div>
    <div class="review-box">
      {_e(a.review_text)}
    </div>
  </div>"""


# ── MAIN REPORT GENERATOR ─────────────────────────────────────────────────────

def generate_report(sweep: SweepData, output_dir: str = "outputs/") -> str:
    """
    Generate the full HTML report from a SweepData object.

    Args:
        sweep:      Populated SweepData with all contacts and channel results
        output_dir: Directory to write the HTML file (default: outputs/)

    Returns:
        Path to the generated HTML file
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{sweep.date}-lark-monthly.html"
    filepath = os.path.join(output_dir, filename)

    score1_display  = sweep.score1_count()
    score2_display  = sweep.score2_count()
    score3_display  = sweep.score3_count()

    # Build contact sections
    score3_html = "\n".join(_build_contact_card(c) for c in sweep.score3_contacts)
    score2_html = "\n".join(_build_contact_card(c) for c in sweep.score2_contacts)
    score1_html = "\n".join(_build_contact_card(c) for c in sweep.score1_contacts)
    noted_html  = "\n".join(_build_noted_card(c)   for c in sweep.noted_contacts)
    ambig_html  = "\n".join(_build_ambiguous_card(a) for a in sweep.ambiguous_entries)

    discarded_html = ""
    if sweep.discarded_entries:
        items = "\n".join(
            f"<p><strong>{_e(d.org_name)}</strong> — {_e(d.reason)}</p>"
            for d in sweep.discarded_entries
        )
        discarded_html = f"""
  <div class="section-header">
    <span class="section-tag" style="background:#888;">Discarded</span>
    <span class="section-title">False positives — confirmed wrong org · No pipeline match</span>
  </div>
  <div style="background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:14px 18px;margin-bottom:20px;font-size:13px;">
    {items}
  </div>"""

    channel_rows = ""
    for ch in sweep.channel_results:
        result_cls = "ch-fire" if ch.fired else ("ch-deferred" if ch.deferred else "ch-none")
        channel_rows += f"""
      <tr>
        <td>{_e(ch.channel_num)}</td>
        <td>{_e(ch.signals)}</td>
        <td>{_e(ch.status)}</td>
        <td class="{result_cls}">{_e(ch.result)}</td>
      </tr>"""

    gap_items = "".join(
        f"<li>{_e(g.text)}</li>" for g in sweep.coverage_gaps
    )

    transparency = sweep.transparency_note or (
        f"{sweep.searches_run}+ searches across Channels 1–5, 7–8. "
        f"{sweep.signals_batched} org names batched against {sweep.records_searched:,} CSV records. "
        f"Result: {sweep.high_matches} HIGH · {sweep.ambiguous} AMBIGUOUS · {sweep.no_match} NO_MATCH. "
        f"HubSpot write-back: {sweep.hubspot_status} · {sweep.hubspot_queued} records queued."
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lark · Monthly Brief · {_e(sweep.date)}</title>
<style>
  :root {{
    --bg: #f5f4ef; --surface: #ffffff; --dark: #1a1916;
    --mid: #5a5852; --light: #a8a49e; --border: #e2e0d8;
    --green: #3d6b4f; --amber: #c8861a; --alert-red: #8b2222;
    --tag-ambiguous: #5a5852; --score1-bg: #3d6b4f; --info-blue: #2b5278;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg); color: var(--dark); line-height: 1.55; font-size: 14px; }}
  .masthead {{ background: var(--dark); color: var(--bg); padding: 28px 40px 24px;
    border-bottom: 3px solid var(--green); }}
  .masthead-eyebrow {{ font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--light); margin-bottom: 6px; }}
  .masthead-title {{ font-size: 26px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 4px; }}
  .masthead-sub {{ font-size: 13px; color: var(--light); }}
  .stats-bar {{ background: var(--dark); border-top: 1px solid rgba(255,255,255,0.08);
    padding: 12px 40px; display: flex; gap: 32px; flex-wrap: wrap; }}
  .stat-item {{ display: flex; flex-direction: column; gap: 2px; }}
  .stat-label {{ font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--light); }}
  .stat-value {{ font-size: 18px; font-weight: 700; color: var(--bg); }}
  .stat-value.green {{ color: #6bcf8f; }} .stat-value.amber {{ color: #f0b84a; }} .stat-value.dim {{ color: var(--light); }}
  .lark-note {{ background: #edf7f0; border-left: 4px solid var(--green); margin: 24px 40px 0;
    padding: 14px 18px; font-size: 12.5px; color: #2d4a38; border-radius: 0 4px 4px 0; }}
  .lark-note strong {{ font-weight: 600; }}
  .slack-preview {{ background: #1a1d21; border-radius: 8px; padding: 22px 26px; margin-bottom: 32px;
    font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12.5px; color: #d1d2d3; line-height: 1.85; }}
  .slack-header {{ font-size: 11px; color: #5a5a62; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
  .slack-channel {{ color: #4a9eda; }} .slack-bot {{ color: #7c8b9a; }}
  .slack-preview .s-bold {{ color: #fff; font-weight: 500; }} .slack-preview .s-green {{ color: #4CAF7A; }}
  .slack-preview .s-amber {{ color: #e8a44a; }} .slack-preview .s-blue {{ color: #6ab0e8; }}
  .slack-preview .s-dim {{ color: #5a5a62; }} .slack-preview .s-noted {{ color: #7c8b9a; }}
  .slack-divider {{ border: none; border-top: 1px solid #2e3238; margin: 10px 0; }}
  .main {{ max-width: 900px; margin: 0 auto; padding: 24px 40px 60px; }}
  .section-header {{ display: flex; align-items: center; gap: 12px; margin: 32px 0 16px;
    padding-bottom: 10px; border-bottom: 2px solid var(--border); }}
  .section-tag {{ padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; color: #fff; }}
  .tag-score1 {{ background: var(--score1-bg); }} .tag-score2 {{ background: var(--amber); }}
  .tag-score3 {{ background: var(--alert-red); }} .tag-ambig {{ background: var(--tag-ambiguous); }}
  .tag-high-noted {{ background: var(--info-blue); }}
  .section-title {{ font-size: 16px; font-weight: 600; color: var(--dark); }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    margin-bottom: 20px; overflow: hidden; }}
  .card-header {{ padding: 16px 20px 12px; border-bottom: 1px solid var(--border);
    display: flex; align-items: flex-start; gap: 14px; }}
  .card-score-tag {{ padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: 700;
    letter-spacing: 0.06em; white-space: nowrap; color: #fff; margin-top: 2px; }}
  .card-org {{ flex: 1; }} .card-org-name {{ font-size: 18px; font-weight: 700; letter-spacing: -0.01em; }}
  .card-org-sub {{ font-size: 12.5px; color: var(--mid); margin-top: 2px; }}
  .card-body {{ padding: 16px 20px; }}
  .finding {{ display: flex; gap: 12px; margin-bottom: 14px; padding: 14px;
    background: #fafaf7; border: 1px solid var(--border); border-radius: 4px; }}
  .finding-badges {{ display: flex; flex-direction: column; gap: 6px; min-width: 82px; }}
  .cert-badge {{ padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; text-align: center; }}
  .c-confirmed {{ background: #d4edda; color: #1a5c30; }} .c-inferred {{ background: #fff3cd; color: #7a5010; }}
  .c-speculative {{ background: #f8d7da; color: #6b1a1a; }}
  .p-badge {{ padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; text-align: center; }}
  .p-high {{ background: #fde8e8; color: #8b2222; }} .p-medium {{ background: #fdf3e0; color: #7a5010; }}
  .p-ctx {{ background: #e8edf5; color: #2b5278; }}
  .finding-content {{ flex: 1; }} .finding-title {{ font-size: 14px; font-weight: 700; margin-bottom: 6px; }}
  .finding-desc {{ font-size: 13px; color: var(--dark); line-height: 1.6; margin-bottom: 8px; }}
  .finding-source {{ font-size: 11.5px; color: var(--mid); font-style: italic; }}
  .finding-source a {{ color: var(--info-blue); text-decoration: none; }}
  .action-box {{ background: #edf7f0; border: 1px solid #b8dfc6; border-radius: 4px;
    padding: 12px 16px; margin-bottom: 14px; }}
  .action-box strong {{ font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--green); display: block; margin-bottom: 4px; }}
  .action-box p {{ font-size: 13px; color: var(--dark); }}
  .action-window {{ font-size: 12px; color: var(--mid); margin-top: 4px; }}
  .enrich-box {{ background: #f0f4fa; border: 1px solid #c5d4e8; border-radius: 4px;
    padding: 12px 16px; margin-bottom: 14px; font-size: 12.5px; }}
  .enrich-box strong {{ font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--info-blue); display: block; margin-bottom: 6px; }}
  .enrich-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px,1fr)); gap: 6px 16px; }}
  .enrich-item label {{ display: block; font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--mid); }}
  .enrich-item span {{ font-weight: 600; font-size: 13px; }}
  .hubspot-box {{ background: #fff8ee; border: 1px solid #f0d4a0; border-radius: 4px;
    padding: 12px 16px; font-size: 12.5px; }}
  .hubspot-box strong {{ font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--amber); display: block; margin-bottom: 6px; }}
  .prop-row {{ margin-bottom: 3px; }}
  .prop-name {{ font-family: 'SF Mono','Fira Code',monospace; font-size: 11px; color: var(--mid); }}
  .prop-val {{ font-size: 12px; color: var(--dark); font-weight: 600; }}
  .noted-v2 {{ background: var(--surface); border: 1px solid #c5d4e8;
    border-left: 4px solid var(--info-blue); border-radius: 0 6px 6px 0; margin-bottom: 16px; overflow: hidden; }}
  .noted-v2-header {{ padding: 14px 20px 12px; border-bottom: 1px solid #e8eef6;
    display: flex; align-items: flex-start; gap: 12px; background: #f4f7fb; }}
  .noted-match-tag {{ display: flex; flex-direction: column; gap: 4px; flex-shrink: 0; }}
  .tag-high-badge {{ padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 700;
    background: #dde8f5; color: var(--info-blue); white-space: nowrap; text-align: center; }}
  .tag-noted-badge {{ padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 700;
    background: #e8edf5; color: var(--info-blue); white-space: nowrap; text-align: center;
    border: 1px solid #c5d4e8; }}
  .noted-v2-org {{ flex: 1; }} .noted-v2-name {{ font-size: 17px; font-weight: 700; margin-bottom: 2px; }}
  .noted-v2-sub {{ font-size: 12px; color: var(--mid); }}
  .noted-v2-body {{ padding: 14px 20px; }}
  .noted-signal-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .noted-signal-label {{ font-size: 13px; font-weight: 700; color: var(--dark); }}
  .noted-window-expired {{ font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
    padding: 2px 7px; border-radius: 3px; background: #fde8e8; color: #8b2222; }}
  .noted-detail-text {{ font-size: 13px; color: var(--mid); line-height: 1.65; margin-bottom: 12px; }}
  .noted-watchfor {{ background: #f0f4fa; border: 1px solid #c5d4e8; border-radius: 4px;
    padding: 10px 14px; font-size: 12.5px; margin-bottom: 10px; }}
  .noted-watchfor strong {{ font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--info-blue); display: block; margin-bottom: 5px; }}
  .noted-enrich {{ display: flex; gap: 20px; flex-wrap: wrap; padding-top: 12px; border-top: 1px solid #e8eef6; }}
  .noted-enrich-item label {{ display: block; font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--mid); }}
  .noted-enrich-item span {{ font-weight: 600; font-size: 13px; color: var(--dark); }}
  .ambig-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    padding: 16px 20px; margin-bottom: 14px; }}
  .ambig-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .ambig-score-tag {{ padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: 700;
    background: #e8e6e0; color: var(--mid); letter-spacing: 0.06em; }}
  .ambig-org {{ font-size: 15px; font-weight: 700; }}
  .ambig-signal {{ font-size: 12.5px; color: var(--mid); margin-bottom: 10px; }}
  .review-box {{ background: #f9f8f4; border: 1px solid var(--border); border-radius: 4px;
    padding: 12px 14px; font-size: 12.5px; white-space: pre-line; }}
  .channel-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px; }}
  .channel-table th {{ text-align: left; font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--mid); padding: 8px 12px; border-bottom: 2px solid var(--border);
    background: #f9f8f4; }}
  .channel-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  .channel-table tr:last-child td {{ border-bottom: none; }}
  .ch-fire {{ color: var(--green); font-weight: 700; }} .ch-none {{ color: var(--light); }}
  .ch-deferred {{ color: var(--amber); font-style: italic; }}
  .gap-section {{ background: #fff8ee; border: 1px solid #f0d4a0; border-radius: 6px;
    padding: 16px 20px; margin-top: 24px; }}
  .gap-section h3 {{ font-size: 13px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--amber); margin-bottom: 10px; }}
  .gap-section ul {{ list-style: none; padding: 0; }}
  .gap-section li {{ font-size: 13px; color: var(--dark); padding: 3px 0 3px 16px; position: relative; }}
  .gap-section li::before {{ content: '—'; position: absolute; left: 0; color: var(--amber); }}
  .footer {{ background: var(--dark); color: var(--light); padding: 18px 40px; font-size: 11.5px;
    border-top: 1px solid rgba(255,255,255,0.08); margin-top: 40px; display: flex;
    justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
</style>
</head>
<body>

<div class="masthead">
  <div class="masthead-eyebrow">Farther Institutional · Prospect Intelligence</div>
  <div class="masthead-title">🪶 Lark · Monthly Brief</div>
  <div class="masthead-sub">Sweep {_e(str(sweep.sweep_num))} · {_e(sweep.date)} · Lookback: {_e(sweep.lookback_start)} – {_e(sweep.lookback_end)} (30 days)</div>
</div>

<div class="stats-bar">
  <div class="stat-item"><div class="stat-label">Sweep</div><div class="stat-value dim">{sweep.sweep_num}</div></div>
  <div class="stat-item"><div class="stat-label">Searches run</div><div class="stat-value dim">{sweep.searches_run}+</div></div>
  <div class="stat-item"><div class="stat-label">Signals batched</div><div class="stat-value dim">{sweep.signals_batched}</div></div>
  <div class="stat-item"><div class="stat-label">HIGH matches</div><div class="stat-value green">{sweep.high_matches}</div></div>
  <div class="stat-item"><div class="stat-label">AMBIGUOUS</div><div class="stat-value amber">{sweep.ambiguous}</div></div>
  <div class="stat-item"><div class="stat-label">NO_MATCH</div><div class="stat-value dim">{sweep.no_match}</div></div>
  <div class="stat-item"><div class="stat-label">Score-1</div><div class="stat-value green">{score1_display}</div></div>
  <div class="stat-item"><div class="stat-label">Score-2 / Score-3</div><div class="stat-value dim">{score2_display} / {score3_display}</div></div>
  <div class="stat-item"><div class="stat-label">HubSpot write-back</div><div class="stat-value amber">STAGED</div></div>
</div>

<div style="padding: 0 40px;">
  <div class="lark-note">
    <strong>Lark · Sweep log</strong> — {_e(transparency)}
  </div>
</div>

<div class="main">

  <div style="font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:var(--mid);margin-bottom:10px;display:flex;align-items:center;gap:12px;">Slack summary — delivered to #institutional-intel<span style="flex:1;height:1px;background:var(--border);display:block;"></span></div>
  <div class="slack-preview">
    <div class="slack-header">
      <span class="slack-channel">#institutional-intel</span>
      <span class="slack-bot">Lark · {_e(sweep.date)} at 8:00 AM HST</span>
    </div>
    {_build_slack_preview(sweep)}
  </div>

  {"" if not (sweep.score3_contacts) else f'''
  <div class="section-header">
    <span class="section-tag tag-score3">Score 3</span>
    <span class="section-title">Senior outreach immediately</span>
  </div>
  {score3_html}'''}

  {"" if not (sweep.score2_contacts) else f'''
  <div class="section-header">
    <span class="section-tag tag-score2">Score 2</span>
    <span class="section-title">Researched outreach within 2 weeks</span>
  </div>
  {score2_html}'''}

  {"" if not (sweep.score1_contacts) else f'''
  <div class="section-header">
    <span class="section-tag tag-score1">Score 1</span>
    <span class="section-title">Signal detected · Soft touch recommended</span>
  </div>
  {score1_html}'''}

  {"" if not (sweep.noted_contacts) else f'''
  <div class="section-header">
    <span class="tag-high-noted" style="padding:4px 12px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#fff;background:var(--info-blue);">High Match · Noted</span>
    <span class="section-title">Confirmed pipeline contact · Signal fired · Action window passed · Monitor</span>
  </div>
  {noted_html}'''}

  {"" if not (sweep.ambiguous_entries) else f'''
  <div class="section-header">
    <span class="section-tag tag-ambig">Ambiguous</span>
    <span class="section-title">Manual review required · Do not outreach without confirming match</span>
  </div>
  {ambig_html}'''}

  {discarded_html}

  {"" if not (sweep.channel_results) else f'''
  <div class="section-header">
    <span class="section-tag" style="background:var(--mid);">Channels</span>
    <span class="section-title">Signal channel summary · Sweep {sweep.sweep_num}</span>
  </div>
  <table class="channel-table">
    <thead>
      <tr><th>Channel</th><th>Signals</th><th>Status</th><th>Result</th></tr>
    </thead>
    <tbody>{channel_rows}</tbody>
  </table>'''}

  {"" if not (sweep.coverage_gaps) else f'''
  <div class="gap-section">
    <h3>Coverage gaps — this sweep</h3>
    <ul>{gap_items}</ul>
  </div>'''}

</div>

<div class="footer">
  <div>Lark · Prospect Intelligence Agent · Farther Institutional</div>
  <div>Sweep {sweep.sweep_num} · Generated {_e(sweep.date)}</div>
  <div>HubSpot write-back: {_e(sweep.hubspot_status)}</div>
</div>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: generates a sample report with dummy data.
    Run from Lark/ directory:
        python utilities/lark_report.py
    """
    print("\n🪶  lark_report.py — self-test\n")

    sweep = SweepData(
        date="2026-07-17",
        sweep_num=3,
        lookback_start="2026-06-17",
        lookback_end="2026-07-17",
        searches_run=28,
        signals_batched=19,
        records_searched=190406,
        high_matches=3,
        ambiguous=7,
        no_match=9,
        hubspot_queued=2,
    )

    sweep.add_score1(ContactResult(
        org_name="Sample Community Foundation",
        city_state="Portland, OR",
        org_type="Community Foundation (NTEE T20)",
        score=88,
        compound_score=1,
        signal_type="SIG-001",
        signal_name="New CFO / Finance Director",
        signal_date="2026-07-10",
        signal_source="https://samplefoundation.org/news",
        signal_source_label="samplefoundation.org · July 10, 2026",
        confidence="Confirmed",
        priority="High",
        finding_text="Sample Community Foundation announced Jane Doe as Chief Financial Officer effective July 1, 2026. Doe joins from Pacific Northwest Consulting Group.",
        outreach_angle="A new CFO in the first 90 days almost always takes a quiet look at the advisor relationship — this is exactly the window.",
        action_window="Move within 60–90 days · expires approximately October 9, 2026",
        enrichment=EnrichmentData(
            ein="93-1234567",
            total_assets=12500000,
            tax_year=2023,
            ntee_code="T20",
        ),
    ))

    sweep.add_noted(ContactResult(
        org_name="Example Arts Museum",
        city_state="Seattle, WA",
        org_type="Arts & Culture (NTEE A50)",
        score=85,
        compound_score=0,
        signal_type="SIG-003",
        signal_name="Capital Campaign Close",
        signal_date="2026-04-15",
        signal_source="https://examplemuseum.org/campaign",
        signal_source_label="examplemuseum.org · April 15, 2026",
        confidence="Confirmed",
        priority="High",
        finding_text="Example Arts Museum closed its $45M campaign on April 15, 2026, raising $52M — 16% oversubscribed. Action window (30–60 days) expired approximately June 14.",
        outreach_angle="",
        action_window="Expired",
        window_expired=True,
        watch_for="New CFO appointment · Investment advisor change · New campaign launch",
        enrichment=EnrichmentData(ein="91-9876543", total_assets=28000000, tax_year=2023, ntee_code="A50"),
    ))

    sweep.coverage_gaps = [
        CoverageGap("LinkedIn not scanned — Apify pending self-test"),
        CoverageGap("HubSpot write-back staged — MCP key pending"),
    ]

    path = generate_report(sweep, output_dir="/mnt/user-data/outputs/")
    print(f"✓ Report generated: {path}\n")