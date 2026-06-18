#!/usr/bin/env python3
"""
lark_profile.py — Lark Prospect Profile Manager
================================================
Creates and updates org profiles in profiles/ from _template.md.
Offloads profile file I/O from Lark's context — Lark provides structured
data, this utility handles file read/write and section updates.

PROFILE FILES:
    profiles/[org-slug]-profile.md
    Created on first HIGH match signal. Updated on subsequent sweeps.
    Lark owns profile files — humans may review but should not overwrite.

TEMPLATE:
    profiles/_template.md — blank profile, read-only

USAGE — Phase 4:
    from utilities.lark_profile import upsert_profile, ProfileUpdate

    update = ProfileUpdate(
        org_name="Candid",
        org_slug="candid",
        signal_type="SIG-002",
        signal_date="2026-06-17",
        ...
    )
    path = upsert_profile(update, profiles_dir="profiles/")
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── SLUG GENERATION ───────────────────────────────────────────────────────────

def _slugify(org_name: str) -> str:
    """
    Convert org name to a safe filename slug.
    "Japanese American National Museum (JANM)" → "japanese-american-national-museum"
    """
    slug = org_name.lower()
    slug = re.sub(r'\(.*?\)', '', slug)           # remove parenthetical
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)      # remove special chars
    slug = re.sub(r'\s+', '-', slug.strip())       # spaces to hyphens
    slug = re.sub(r'-+', '-', slug)                # collapse hyphens
    slug = slug.strip('-')
    return slug[:60]                               # cap length


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class ProfileUpdate:
    """All data needed to create or update a profile."""
    # Identity (required)
    org_name:       str
    org_slug:       str  = ""   # auto-generated from org_name if blank

    # Signal
    signal_type:    str  = ""
    signal_date:    str  = ""   # ISO date
    signal_source:  str  = ""
    finding_text:   str  = ""
    confidence:     str  = ""   # Confirmed / Inferred / Speculative
    compound_score: int  = 0
    action_window:  str  = ""
    outreach_angle: str  = ""

    # Identity fields (optional — fill what's available)
    website:        str  = ""
    linkedin:       str  = ""
    hq:             str  = ""   # City, State
    ein:            str  = ""
    org_type:       str  = ""

    # HubSpot
    hubspot_id:     str  = ""
    contact_name:   str  = ""
    contact_title:  str  = ""
    contact_email:  str  = ""

    # Financial
    aum_estimated:  str  = ""   # "$12.5M · IRS 990 · tax year 2023"
    endowment_status: str = ""  # Established / First-time / None known / Unknown
    current_advisor: str = ""
    aum_threshold:  str  = ""   # "Yes — $10M+" etc.

    # Leadership
    ceo_ed:         str  = ""
    cfo:            str  = ""
    board_chair:    str  = ""
    ic_chair:       str  = ""

    # Notes
    open_threads:   list[str] = field(default_factory=list)
    sweep_notes:    str = ""

    def __post_init__(self):
        if not self.org_slug:
            self.org_slug = _slugify(self.org_name)


# ── TEMPLATE READER ───────────────────────────────────────────────────────────

def _read_template(template_path: str) -> str:
    """Read the _template.md file."""
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Profile template not found: {template_path}\n"
            f"Expected at: {os.path.abspath(template_path)}"
        )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


# ── PROFILE BUILDER ───────────────────────────────────────────────────────────

def _build_new_profile(update: ProfileUpdate, template: str) -> str:
    """
    Build a new profile from the template, substituting known values.
    Unknown fields are left as template placeholders.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    profile = template

    # Header
    profile = profile.replace("[ORG NAME]", update.org_name)

    # Dates
    profile = profile.replace("[ISO date]", today)

    # Identity section
    if update.website:
        profile = _replace_field(profile, "WEBSITE:", update.website)
    if update.linkedin:
        profile = _replace_field(profile, "LINKEDIN:", update.linkedin)
    if update.hq:
        profile = _replace_field(profile, "HQ:", update.hq)
    if update.ein:
        profile = _replace_field(profile, "EIN:", update.ein)
    if update.org_type:
        profile = _replace_field(profile, "ORG TYPE:", update.org_type)

    # HubSpot
    if update.hubspot_id:
        profile = _replace_field(profile, "HUBSPOT COMPANY ID:", update.hubspot_id)
    if update.contact_name:
        profile = _replace_field(profile, "CONTACT NAME:", update.contact_name)

    # Financial
    if update.aum_estimated:
        profile = _replace_field(profile, "EST. AUM:", update.aum_estimated)
    if update.endowment_status:
        profile = _replace_field(profile, "ENDOWMENT STATUS:", update.endowment_status)
    if update.aum_threshold:
        profile = _replace_field(profile, "AUM THRESHOLD MET:", update.aum_threshold)

    # Leadership
    if update.ceo_ed:
        profile = _replace_field(profile, "ED / CEO:", update.ceo_ed)
    if update.cfo:
        profile = _replace_field(profile, "CFO / FINANCE DIRECTOR:", update.cfo)

    # Compound score
    if update.compound_score:
        profile = _replace_field(profile, "CURRENT SCORE:", str(update.compound_score))
        profile = _replace_field(profile, "SCORE LAST UPDATED:", today)
    if update.action_window:
        profile = _replace_field(profile, "ACTION WINDOW:", update.action_window)
    if update.outreach_angle:
        profile = _replace_field(profile, "RECOMMENDED ACTION:", update.outreach_angle)

    # Signal timeline entry
    if update.signal_type and update.signal_date:
        signal_line = (
            f"{update.signal_date} | {update.signal_type} | "
            f"{_signal_name(update.signal_type)} | "
            f"{update.finding_text[:100]} | {update.signal_source}"
        )
        profile = profile.replace(
            "[No signals fired yet]",
            signal_line
        )

    # Signals contributing
    if update.signal_type:
        sig_entry = f"- [{update.signal_type} — {_signal_name(update.signal_type)} — {update.confidence}]"
        profile = profile.replace(
            "- [SIG-00X — signal name — Confirmed/Inferred/Speculative]",
            sig_entry
        )

    # Open threads — replace the default thread with real ones
    if update.open_threads:
        threads = "\n".join(f"- [ ] {t}" for t in update.open_threads)
        # Remove the default placeholder threads and replace with real ones
        profile = re.sub(
            r'- \[ \] Pull most recent 990.*?- \[ \] Confirm AUM and endowment status\n?',
            threads + "\n",
            profile,
            flags=re.DOTALL
        )

    return profile


def _replace_field(profile: str, field_prefix: str, value: str) -> str:
    """
    Replace a template field value.
    "WEBSITE:" → "WEBSITE: https://example.org"
    Handles both blank and placeholder values.
    """
    pattern = rf'^({re.escape(field_prefix)})\s*.*$'
    replacement = rf'\1 {value}'
    return re.sub(pattern, replacement, profile, flags=re.MULTILINE)


def _signal_name(signal_type: str) -> str:
    names = {
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
    return names.get(signal_type, signal_type)


# ── PROFILE UPDATER ───────────────────────────────────────────────────────────

def _append_signal_to_timeline(profile: str, update: ProfileUpdate) -> str:
    """
    Append a new signal entry to the Signal timeline section of an existing profile.
    """
    if not update.signal_type or not update.signal_date:
        return profile

    new_entry = (
        f"{update.signal_date} | {update.signal_type} | "
        f"{_signal_name(update.signal_type)} | "
        f"{update.finding_text[:100]} | {update.signal_source}"
    )

    # Find the signal timeline section and prepend the new entry
    timeline_marker = "## Signal timeline"
    if timeline_marker in profile:
        lines         = profile.split("\n")
        insert_after  = None
        for i, line in enumerate(lines):
            if "Signal timeline" in line:
                # Find the first non-header, non-blank, non-format line after the section
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip() and not lines[j].startswith(">") and not lines[j].startswith("#"):
                        insert_after = j
                        break
                break

        if insert_after:
            lines.insert(insert_after, new_entry)
            return "\n".join(lines)

    return profile


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def upsert_profile(
    update:        ProfileUpdate,
    profiles_dir:  str = "profiles/",
    template_path: str = "profiles/_template.md",
    verbose:       bool = True,
) -> str:
    """
    Create or update a prospect profile.

    If the profile already exists: appends the new signal to the timeline
    and updates the compound score and action window.

    If the profile doesn't exist: creates it from _template.md with
    all available fields populated.

    Args:
        update:        ProfileUpdate with signal and identity data
        profiles_dir:  Directory where profile files live (default: profiles/)
        template_path: Path to _template.md (default: profiles/_template.md)
        verbose:       Print progress

    Returns:
        Path to the profile file (created or updated)
    """
    os.makedirs(profiles_dir, exist_ok=True)

    filename = f"{update.org_slug}-profile.md"
    filepath = os.path.join(profiles_dir, filename)
    today    = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(filepath):
        # UPDATE existing profile
        with open(filepath, "r", encoding="utf-8") as f:
            profile = f.read()

        # Update Last updated date
        profile = re.sub(
            r'Last updated:.*$',
            f'Last updated: {today}',
            profile,
            flags=re.MULTILINE
        )

        # Append new signal to timeline
        if update.signal_type:
            profile = _append_signal_to_timeline(profile, update)

        # Update score if higher
        if update.compound_score > 0:
            profile = _replace_field(profile, "CURRENT SCORE:", str(update.compound_score))
            profile = _replace_field(profile, "SCORE LAST UPDATED:", today)

        if update.action_window:
            profile = _replace_field(profile, "ACTION WINDOW:", update.action_window)

        # Update leadership if provided
        if update.cfo:
            profile = _replace_field(profile, "CFO / FINANCE DIRECTOR:", update.cfo)
        if update.ceo_ed:
            profile = _replace_field(profile, "ED / CEO:", update.ceo_ed)

        # Append notes
        if update.sweep_notes:
            notes_entry = f"\n- [{today} sweep] {update.sweep_notes}"
            if "## What Lark currently knows" in profile:
                profile = profile.replace(
                    "[No sweep completed yet]",
                    f"[{today}] {update.sweep_notes}"
                )

        action = "Updated"

    else:
        # CREATE new profile from template
        template = _read_template(template_path)
        profile  = _build_new_profile(update, template)
        action   = "Created"

    # Write profile
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(profile)

    if verbose:
        print(f"[Profile] {action}: {filepath}")

    return filepath


def profile_exists(org_slug: str, profiles_dir: str = "profiles/") -> bool:
    """Check if a profile already exists for this org."""
    return os.path.exists(os.path.join(profiles_dir, f"{org_slug}-profile.md"))


def get_profile_path(org_slug: str, profiles_dir: str = "profiles/") -> str:
    """Return the expected profile path for an org."""
    return os.path.join(profiles_dir, f"{org_slug}-profile.md")


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: creates a sample profile in /tmp.
    Does not require profiles/_template.md — uses a minimal inline template.
    Run from Lark/ directory:
        python utilities/lark_profile.py
    """
    import tempfile
    print("\n🪶  lark_profile.py — self-test\n")

    # Minimal template for testing
    minimal_template = """# [ORG NAME] — Prospect Profile
Last updated: [ISO date]

## Identity
ORG NAME:
WEBSITE:
HQ:
EIN:

## Financial profile
EST. AUM:
ENDOWMENT STATUS:
AUM THRESHOLD MET:
CURRENT SCORE:
SCORE LAST UPDATED:
ACTION WINDOW:

## Leadership
ED / CEO:
CFO / FINANCE DIRECTOR:

## Signal timeline
> Most recent first.
[No signals fired yet]

## Open threads
- [ ] Pull most recent 990 from ProPublica
- [ ] Confirm current investment advisor (990 Schedule D or press)
- [ ] Check LinkedIn for leadership changes
- [ ] Check org website for campaign or strategic plan announcements
- [ ] Confirm AUM and endowment status
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = os.path.join(tmpdir, "_template.md")
        with open(template_path, "w") as f:
            f.write(minimal_template)

        update = ProfileUpdate(
            org_name="Candid",
            hq="New York, NY",
            ein="13-1837418",
            signal_type="SIG-002",
            signal_date="2026-06-17",
            signal_source="https://candid.org/press",
            finding_text="John Brothers named Interim P&CEO effective June 1, 2026.",
            confidence="Confirmed",
            compound_score=1,
            action_window="Move within 90–180 days · expires 2026-11-28",
            aum_estimated="$100M · IRS 990 · tax year 2023",
        )

        path = upsert_profile(
            update,
            profiles_dir=tmpdir,
            template_path=template_path,
            verbose=True,
        )

        with open(path) as f:
            content = f.read()

        assert "Candid" in content
        assert "SIG-002" in content
        assert "2026-06-17" in content
        print(f"\n  Profile excerpt:\n")
        print("\n".join(content.split("\n")[:20]))

    print(f"\n✓ lark_profile.py self-test passed.\n")
