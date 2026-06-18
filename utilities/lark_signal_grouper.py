#!/usr/bin/env python3
"""
lark_scorer.py — Lark Compound Scoring Utility
===============================================
Calculates compound scores for matched contacts after Phase 2.
Groups signals by org, stacks them, and returns scored contact dicts
ready for report generation and HubSpot write-back.

SCORING REFERENCE (from data/signals.md):
    Score 3 — 2+ High signals, or High + Medium + Contextual
    Score 2 — 1 High + 1 Medium, or 2+ Medium signals
    Score 1 — Single signal, any tier

SIGNAL TIERS (from data/signals.md):
    High:        SIG-001, SIG-002, SIG-003, SIG-004
    Medium:      SIG-005, SIG-006, SIG-007, SIG-008
    Contextual:  SIG-009, SIG-010

USAGE — Phase 4:
    from utilities.lark_scorer import score_contacts, ScoredContact

    # all_signals: list of (org_name, signal_type, source, date, match_result)
    scored = score_contacts(all_signals)

    score3 = [c for c in scored if c.compound_score == 3]
    score1 = [c for c in scored if c.compound_score == 1]
"""

from dataclasses import dataclass, field
from typing import Optional


# ── SIGNAL TIER MAPPING ───────────────────────────────────────────────────────

SIGNAL_TIERS: dict[str, str] = {
    "SIG-001": "High",
    "SIG-002": "High",
    "SIG-003": "High",
    "SIG-004": "High",
    "SIG-005": "Medium",
    "SIG-006": "Medium",
    "SIG-007": "Medium",
    "SIG-008": "Medium",
    "SIG-009": "Contextual",
    "SIG-010": "Contextual",
}

SIGNAL_NAMES: dict[str, str] = {
    "SIG-001": "New CFO / Finance Director",
    "SIG-002": "New CEO / Executive Director",
    "SIG-003": "Capital Campaign Close",
    "SIG-004": "Large Gift or Bequest",
    "SIG-005": "New Investment Committee Chair",
    "SIG-006": "Capital Campaign Launch",
    "SIG-007": "AUM Threshold Crossed",
    "SIG-008": "Merger or Restructuring",
    "SIG-009": "New Strategic Plan",
    "SIG-010": "First-Time Endowment",
}

ACTION_WINDOWS: dict[str, str] = {
    "SIG-001": "Move within 60–90 days of appointment",
    "SIG-002": "Move within 90–180 days of appointment",
    "SIG-003": "Move immediately — 30–60 days post-announcement",
    "SIG-004": "Move within days — rivals see the same press release",
    "SIG-005": "Move within 60–90 days of appointment",
    "SIG-006": "Move within 30–60 days of announcement",
    "SIG-007": "Use as confirmation only — do not outreach on 990 alone",
    "SIG-008": "Move immediately — chaos window is short",
    "SIG-009": "Soft outreach only — confirm endowment language first",
    "SIG-010": "Move immediately — no incumbent to displace",
}


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class SignalFire:
    """A single signal that fired for a given org."""
    signal_type:  str          # SIG-001 through SIG-010
    signal_name:  str
    tier:         str          # High / Medium / Contextual
    source:       str          # URL
    date:         str          # ISO date
    confidence:   str          # Confirmed / Inferred / Speculative
    finding_text: str = ""


@dataclass
class ScoredContact:
    """A matched contact with all fired signals and a compound score."""
    org_name:       str
    matched_name:   str          # CSV matched name
    fuzzy_score:    int          # fuzzy matcher score 0–100
    aum_value:      Optional[float]
    meets_aum:      bool

    signals:        list[SignalFire] = field(default_factory=list)
    compound_score: int = 0
    primary_signal: Optional[SignalFire] = None   # highest-tier signal
    action_window:  str = ""
    score_reason:   str = ""     # human-readable explanation

    def high_signals(self)        -> list[SignalFire]:
        return [s for s in self.signals if s.tier == "High"]

    def medium_signals(self)      -> list[SignalFire]:
        return [s for s in self.signals if s.tier == "Medium"]

    def contextual_signals(self)  -> list[SignalFire]:
        return [s for s in self.signals if s.tier == "Contextual"]

    def signal_type_list(self) -> str:
        return ", ".join(s.signal_type for s in self.signals)

    def summary(self) -> str:
        return (
            f"Score {self.compound_score} | {self.matched_name} | "
            f"Signals: {self.signal_type_list()} | "
            f"Reason: {self.score_reason}"
        )


# ── SCORING LOGIC ─────────────────────────────────────────────────────────────

def _compute_score(signals: list[SignalFire]) -> tuple[int, str]:
    """
    Compute compound score from a list of signals.
    Returns (score, reason_string).

    Scoring rules (from signals.md):
        Score 3: 2+ High, or High + Medium + Contextual
        Score 2: 1 High + 1 Medium, or 2+ Medium
        Score 1: Single signal, any tier
    """
    high  = sum(1 for s in signals if s.tier == "High")
    med   = sum(1 for s in signals if s.tier == "Medium")
    ctx   = sum(1 for s in signals if s.tier == "Contextual")
    total = len(signals)

    if total == 0:
        return 0, "No signals"

    # Score 3
    if high >= 2:
        return 3, f"{high} High signals"
    if high >= 1 and med >= 1 and ctx >= 1:
        return 3, "High + Medium + Contextual"
    if high >= 1 and med >= 2:
        return 3, f"High + {med} Medium signals"

    # Score 2
    if high >= 1 and med >= 1:
        return 2, "High + Medium"
    if med >= 2:
        return 2, f"{med} Medium signals"

    # Score 1
    return 1, f"Single {signals[0].tier} signal ({signals[0].signal_type})"


def _primary_signal(signals: list[SignalFire]) -> Optional[SignalFire]:
    """Return the highest-tier, most actionable signal."""
    tier_order = {"High": 0, "Medium": 1, "Contextual": 2}
    if not signals:
        return None
    return min(signals, key=lambda s: tier_order.get(s.tier, 99))


def _action_window(signals: list[SignalFire]) -> str:
    """Return the action window for the primary (most urgent) signal."""
    primary = _primary_signal(signals)
    if not primary:
        return ""
    return ACTION_WINDOWS.get(primary.signal_type, "")


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def score_contacts(
    signal_fires: list[tuple],
    verbose: bool = True,
) -> list[ScoredContact]:
    """
    Group signals by org and compute compound scores.

    Args:
        signal_fires: List of tuples:
            (org_name, matched_name, fuzzy_score, aum_value, meets_aum,
             signal_type, source, date, confidence, finding_text)

        verbose: Print score summary

    Returns:
        List of ScoredContact, sorted by compound_score descending.

    Usage:
        scored = score_contacts([
            ("Candid", "CANDID", 92, 100177752, True,
             "SIG-002", "https://...", "2026-06-01", "Confirmed",
             "John Brothers named Interim P&CEO..."),
        ])
        for c in scored:
            print(c.summary())
    """
    # Group by matched_name
    orgs: dict[str, ScoredContact] = {}

    for item in signal_fires:
        (
            org_name, matched_name, fuzzy_score,
            aum_value, meets_aum,
            signal_type, source, date, confidence, finding_text
        ) = item

        key = matched_name.lower().strip()

        if key not in orgs:
            orgs[key] = ScoredContact(
                org_name=org_name,
                matched_name=matched_name,
                fuzzy_score=fuzzy_score,
                aum_value=aum_value,
                meets_aum=meets_aum,
            )

        fire = SignalFire(
            signal_type=signal_type,
            signal_name=SIGNAL_NAMES.get(signal_type, signal_type),
            tier=SIGNAL_TIERS.get(signal_type, "Unknown"),
            source=source,
            date=date,
            confidence=confidence,
            finding_text=finding_text,
        )
        orgs[key].signals.append(fire)

    # Score each org
    results = []
    for contact in orgs.values():
        score, reason            = _compute_score(contact.signals)
        contact.compound_score   = score
        contact.score_reason     = reason
        contact.primary_signal   = _primary_signal(contact.signals)
        contact.action_window    = _action_window(contact.signals)
        results.append(contact)

    # Sort: Score 3 first, then by fuzzy_score within each tier
    results.sort(key=lambda c: (-c.compound_score, -c.fuzzy_score))

    if verbose:
        score3 = sum(1 for c in results if c.compound_score == 3)
        score2 = sum(1 for c in results if c.compound_score == 2)
        score1 = sum(1 for c in results if c.compound_score == 1)
        print(f"\n[Scorer] {len(results)} contacts scored:")
        print(f"  Score-3: {score3} · Score-2: {score2} · Score-1: {score1}")
        for c in results:
            print(f"  {c.summary()}")

    return results


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🪶  lark_scorer.py — self-test\n")

    test_fires = [
        # Candid — SIG-002 only → Score 1
        ("Candid", "CANDID", 92, 100177752, True,
         "SIG-002", "https://candid.org/press", "2026-06-01", "Confirmed",
         "John Brothers named Interim P&CEO."),

        # Sample org — SIG-001 + SIG-003 → Score 3 (2 High)
        ("Sample Foundation", "SAMPLE FOUNDATION", 88, 15000000, True,
         "SIG-001", "https://samplefoundation.org", "2026-06-10", "Confirmed",
         "New CFO hired."),
        ("Sample Foundation", "SAMPLE FOUNDATION", 88, 15000000, True,
         "SIG-003", "https://samplefoundation.org/campaign", "2026-06-05", "Confirmed",
         "Campaign closed at $20M."),

        # Another org — SIG-007 only → Score 1 (Medium)
        ("Another Endowment", "ANOTHER ENDOWMENT FUND", 81, 8000000, True,
         "SIG-007", "https://propublica.org", "2026-01-01", "Inferred",
         "AUM crossed $5M threshold."),
    ]

    results = score_contacts(test_fires)

    assert results[0].compound_score == 3, "Sample Foundation should be Score-3"
    assert results[0].matched_name == "SAMPLE FOUNDATION"
    assert results[1].compound_score == 1

    print(f"\n✓ lark_scorer.py self-test passed.\n")
