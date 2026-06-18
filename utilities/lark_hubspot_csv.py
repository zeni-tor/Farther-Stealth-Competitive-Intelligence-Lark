#!/usr/bin/env python3
"""
lark_hubspot_csv.py — Lark HubSpot Write-Back CSV Generator
============================================================
Generates the staged HubSpot import CSV after every sweep.
When the MCP key is configured, this transitions to direct MCP write-back.
Until then, the CSV is the import artifact.

PROPERTY DEFINITIONS: data/hubspot-properties.md
OBJECT TYPE: Company

COLUMN ORDER (matches HubSpot bulk import format):
    Org Name (CSV match) | All lark_* custom properties

USAGE — Phase 4:
    from utilities.lark_hubspot_csv import write_hubspot_csv

    records = build_records(sweep_results)
    path = write_hubspot_csv(records, date="2026-07-17", output_dir="outputs/")

TWO RECORD TYPES:
    Signal records  — org fired a signal, full property set written
    Sweep records   — org swept with no signal, lark_last_sweep only

OUTPUT:
    outputs/YYYY-MM-DD-lark-hubspot-writeback.csv
"""

import os
import csv
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── COLUMN DEFINITIONS ────────────────────────────────────────────────────────
# Must match HubSpot internal property names exactly.
# See data/hubspot-properties.md for full definitions.

SIGNAL_COLUMNS = [
    "Org Name",
    "lark_signal_type",
    "lark_signal_date",
    "lark_signal_source",
    "lark_signals_active",
    "lark_compound_score",
    "lark_score_updated",
    "lark_action_window",
    "lark_contact_status",
    "lark_aum_estimated",
    "lark_aum_source",
    "lark_incumbent_advisor",
    "lark_incumbent_source",
    "lark_last_sweep",
    "lark_notes",
    "lark_propublica_ein",
]

SWEEP_ONLY_COLUMNS = [
    "Org Name",
    "lark_last_sweep",
]


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class SignalRecord:
    """A full signal write-back record for HubSpot."""
    # Required
    org_name:           str          # CSV matched org name
    signal_type:        str          # SIG-001 through SIG-010
    signal_date:        str          # ISO date (YYYY-MM-DD)
    signal_source:      str          # URL
    compound_score:     int          # 1, 2, or 3
    action_window:      str          # "Move within 60–90 days · expires YYYY-MM-DD"
    last_sweep:         str          # ISO date (YYYY-MM-DD)

    # Optional enrichment
    signals_active:     str  = ""    # comma-separated e.g. "SIG-001, SIG-003"
    score_updated:      str  = ""    # ISO date
    contact_status:     str  = "Signal Detected"
    aum_estimated:      Optional[int]  = None
    aum_source:         str  = ""    # "IRS 990 · tax year 2023"
    incumbent_advisor:  str  = ""
    incumbent_source:   str  = ""
    notes:              str  = ""
    propublica_ein:     str  = ""

    def to_row(self) -> dict:
        return {
            "Org Name":              self.org_name,
            "lark_signal_type":      self.signal_type,
            "lark_signal_date":      self.signal_date,
            "lark_signal_source":    self.signal_source,
            "lark_signals_active":   self.signals_active,
            "lark_compound_score":   str(self.compound_score),
            "lark_score_updated":    self.score_updated or self.last_sweep,
            "lark_action_window":    self.action_window,
            "lark_contact_status":   self.contact_status,
            "lark_aum_estimated":    str(self.aum_estimated) if self.aum_estimated else "",
            "lark_aum_source":       self.aum_source,
            "lark_incumbent_advisor": self.incumbent_advisor,
            "lark_incumbent_source": self.incumbent_source,
            "lark_last_sweep":       self.last_sweep,
            "lark_notes":            self.notes,
            "lark_propublica_ein":   self.propublica_ein,
        }


@dataclass
class SweepRecord:
    """A minimal sweep-only record — org was swept, no signal fired."""
    org_name:   str   # CSV matched org name
    last_sweep: str   # ISO date (YYYY-MM-DD)

    def to_row(self) -> dict:
        return {
            "Org Name":        self.org_name,
            "lark_last_sweep": self.last_sweep,
        }


# ── CSV WRITERS ───────────────────────────────────────────────────────────────

def write_hubspot_csv(
    signal_records: list[SignalRecord],
    sweep_records:  list[SweepRecord],
    date:           str,
    output_dir:     str = "outputs/",
    verbose:        bool = True,
) -> str:
    """
    Write the HubSpot import CSV.

    Generates two files:
    - YYYY-MM-DD-lark-hubspot-writeback.csv    — signal records (full property set)
    - YYYY-MM-DD-lark-hubspot-sweep-only.csv   — sweep-only records (last_sweep only)

    Args:
        signal_records: List of SignalRecord — orgs with active signals
        sweep_records:  List of SweepRecord  — orgs swept, no signal
        date:           ISO date string for filename
        output_dir:     Output directory (default: outputs/)
        verbose:        Print summary

    Returns:
        Path to the signal records CSV (primary file)
    """
    os.makedirs(output_dir, exist_ok=True)

    # Signal records CSV
    signal_path = os.path.join(output_dir, f"{date}-lark-hubspot-writeback.csv")
    if signal_records:
        with open(signal_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SIGNAL_COLUMNS)
            writer.writeheader()
            for r in signal_records:
                writer.writerow(r.to_row())
    else:
        # Write empty file with headers
        with open(signal_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SIGNAL_COLUMNS)
            writer.writeheader()

    # Sweep-only records CSV
    sweep_path = os.path.join(output_dir, f"{date}-lark-hubspot-sweep-only.csv")
    if sweep_records:
        with open(sweep_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SWEEP_ONLY_COLUMNS)
            writer.writeheader()
            for r in sweep_records:
                writer.writerow(r.to_row())

    if verbose:
        print(f"\n[HubSpot CSV]")
        print(f"  Signal records:   {len(signal_records)} → {signal_path}")
        print(f"  Sweep-only:       {len(sweep_records)} → {sweep_path}")
        print(f"  Status:           STAGED — import when MCP key is configured")

    return signal_path


# ── HELPERS ───────────────────────────────────────────────────────────────────

def today_iso() -> str:
    """Return today's date as ISO string."""
    return datetime.now().strftime("%Y-%m-%d")


def from_propublica(pr_result) -> tuple[Optional[int], str, str]:
    """
    Extract AUM fields from a ProPublicaResult.
    Returns (aum_estimated, aum_source, propublica_ein).
    """
    if not pr_result or not pr_result.found:
        return None, "", ""
    aum_source = f"IRS 990 · tax year {pr_result.tax_year}" if pr_result.tax_year else "IRS 990"
    return pr_result.total_assets, aum_source, pr_result.ein or ""


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: writes sample CSV files.
    Run from Lark/ directory:
        python utilities/lark_hubspot_csv.py
    """
    print("\n🪶  lark_hubspot_csv.py — self-test\n")

    today = today_iso()

    signals = [
        SignalRecord(
            org_name="CANDID",
            signal_type="SIG-002",
            signal_date=today,
            signal_source="https://candid.org/press/candid-announces-interim-president",
            compound_score=1,
            action_window="Move within 90–180 days · expires 2026-11-28",
            last_sweep=today,
            signals_active="SIG-002",
            score_updated=today,
            aum_estimated=100177752,
            aum_source="IRS 990 · tax year 2023",
            propublica_ein="13-1837418",
            notes="John Brothers (ex-T. Rowe Price Foundation) named Interim P&CEO effective 2026-06-01.",
        ),
    ]

    sweeps = [
        SweepRecord(org_name="EAU CLAIRE COMMUNITY FOUNDATION", last_sweep=today),
    ]

    path = write_hubspot_csv(
        signal_records=signals,
        sweep_records=sweeps,
        date=today,
        output_dir="/mnt/user-data/outputs/",
    )
    print(f"\n✓ lark_hubspot_csv.py ready. Primary file: {path}\n")
