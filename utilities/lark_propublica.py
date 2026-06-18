#!/usr/bin/env python3
"""
lark_propublica.py — Lark ProPublica Nonprofit Explorer Enrichment
===================================================================
Enriches HIGH fuzzy matcher results with 990 data from the ProPublica
Nonprofit Explorer API. Free, no key required, structured JSON.

USAGE — Phase 3 enrichment only:
    Never call during Phase 1 (search) or Phase 2 (match).
    Only call on HIGH matches where meets_aum_threshold=True.

    from utilities.lark_propublica import enrich_batch

    high_matches = [r for r in results if r.is_match and r.meets_aum_threshold]
    enriched = enrich_batch(high_matches)

API ENDPOINTS:
    Search:  https://projects.propublica.org/nonprofits/api/v2/search.json?q=[name]
    By EIN:  https://projects.propublica.org/nonprofits/api/v2/organizations/[EIN].json

IMPORTANT — 990 DATA LAG:
    ProPublica data is 12–18 months behind real time.
    Always state the tax year when citing AUM figures.
    Never present 990 AUM as current — label as "IRS 990 · tax year [year]"

OFFICER TABLE:
    The officer compensation table contains departure dates in the format
    "Until MM/DD/YY" — this can corroborate SIG-001/SIG-002 timing.
    Example: CFO listed "Until 03/31/26" confirms a Q1 2026 departure.

COST: Free. No key. No rate limit documented — use polite delays.
"""

import os
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

PROPUBLICA_BASE   = "https://projects.propublica.org/nonprofits/api/v2"
SEARCH_ENDPOINT   = f"{PROPUBLICA_BASE}/search.json"
ORG_ENDPOINT      = f"{PROPUBLICA_BASE}/organizations"
REQUEST_DELAY_S   = 1.0   # polite delay between API calls
REQUEST_TIMEOUT_S = 15

# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class OfficerEntry:
    """A single officer from a 990 filing's compensation table."""
    name:        str
    title:       str
    compensation: Optional[int]
    until_date:  Optional[str]   # "Until MM/DD/YY" if departure date present
    is_departed: bool = False    # True if "Until" date found

    def summary(self) -> str:
        dep = f" · departed {self.until_date}" if self.is_departed else ""
        comp = f" · ${self.compensation:,}" if self.compensation else ""
        return f"{self.name} · {self.title}{comp}{dep}"


@dataclass
class ProPublicaResult:
    """Enrichment data for a single HIGH match from ProPublica."""
    # Input
    incoming_name:    str
    matched_org_name: str

    # 990 identity
    ein:              Optional[str]  = None
    org_name_990:     Optional[str]  = None
    city:             Optional[str]  = None
    state:            Optional[str]  = None
    ntee_code:        Optional[str]  = None

    # Financial
    total_assets:     Optional[int]  = None
    total_revenue:    Optional[int]  = None
    total_income:     Optional[int]  = None
    tax_year:         Optional[int]  = None

    # Officers
    officers:         list[OfficerEntry] = field(default_factory=list)
    departed_officers: list[OfficerEntry] = field(default_factory=list)

    # Status
    found:            bool = False
    error:            Optional[str] = None
    source:           str = "ProPublica Nonprofit Explorer"

    @property
    def aum_display(self) -> str:
        if self.total_assets is None:
            return "Not found"
        return f"${self.total_assets:,} (IRS 990 · tax year {self.tax_year or 'unknown'})"

    @property
    def aum_range(self) -> str:
        if self.total_assets is None:
            return "Unknown"
        a = self.total_assets
        if a >= 50_000_000:  return ">$50M · full institutional mandate"
        if a >= 25_000_000:  return ">$25M · OCIO conversation relevant"
        if a >= 10_000_000:  return ">$10M · institutional-grade advisor warranted"
        if a >=  5_000_000:  return ">$5M · first-time professional management"
        if a >=  1_000_000:  return ">$1M · AUM threshold met"
        return "<$1M · below AUM threshold"

    def summary(self) -> str:
        lines = [f"ProPublica: {self.matched_org_name}"]
        if not self.found:
            lines.append(f"  Not found — {self.error or 'no result'}")
            return "\n".join(lines)
        lines.append(f"  EIN:       {self.ein}")
        lines.append(f"  AUM:       {self.aum_display}")
        lines.append(f"  Range:     {self.aum_range}")
        lines.append(f"  NTEE:      {self.ntee_code}")
        lines.append(f"  Location:  {self.city}, {self.state}")
        if self.departed_officers:
            lines.append(f"  Departed officers ({len(self.departed_officers)}):")
            for o in self.departed_officers:
                lines.append(f"    - {o.summary()}")
        return "\n".join(lines)


# ── HTTP HELPER ───────────────────────────────────────────────────────────────

def _get_json(url: str) -> tuple[Optional[dict], Optional[str]]:
    """
    GET a URL and return parsed JSON. Returns (data, error).
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Lark/1.0 Farther Institutional (nonprofit research)"}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {url}"
    except urllib.error.URLError as e:
        return None, f"Network error: {e.reason}"
    except (json.JSONDecodeError, Exception) as e:
        return None, f"Parse error: {e}"


# ── OFFICER TABLE PARSER ──────────────────────────────────────────────────────

def _parse_officers(filings: list[dict]) -> list[OfficerEntry]:
    """
    Extract officer entries from the most recent 990 filing(s).
    Looks for departure dates in the format "Until MM/DD/YY".

    ProPublica organizes officers under filing["principal_officers"]
    or filing["compensation"]. The exact structure varies by filing type.
    """
    officers = []
    if not filings:
        return officers

    # Use the most recent filing
    latest = filings[0]

    # Try principal_officers first (Form 990 Part VII)
    raw_officers = (
        latest.get("principal_officers") or
        latest.get("compensation") or
        []
    )

    for entry in raw_officers:
        if not isinstance(entry, dict):
            continue

        name  = (entry.get("name") or entry.get("person_name") or "").strip()
        title = (entry.get("title") or entry.get("titleTxt") or "").strip()
        if not name:
            continue

        # Compensation — may be string or int
        comp_raw = entry.get("compensation") or entry.get("reportable_comp") or 0
        try:
            compensation = int(str(comp_raw).replace(",", "").replace("$", ""))
        except (ValueError, TypeError):
            compensation = None

        # Departure date — "Until MM/DD/YY" pattern in title or a dedicated field
        until_date  = None
        is_departed = False

        # Check dedicated field
        until_raw = entry.get("until") or entry.get("termination_date") or ""
        if until_raw:
            until_date  = until_raw.strip()
            is_departed = True

        # Check if "Until" appears in the title string
        if not is_departed and "until" in title.lower():
            import re
            match = re.search(r'until\s+([\d/]+)', title, re.IGNORECASE)
            if match:
                until_date  = match.group(1)
                is_departed = True

        officers.append(OfficerEntry(
            name=name,
            title=title,
            compensation=compensation,
            until_date=until_date,
            is_departed=is_departed,
        ))

    return officers


# ── SINGLE ORG ENRICHMENT ─────────────────────────────────────────────────────

def enrich_org(
    org_name: str,
    matched_name: str,
    ein: Optional[str] = None,
    verbose: bool = True,
) -> ProPublicaResult:
    """
    Enrich a single org with ProPublica 990 data.

    Args:
        org_name:     Incoming signal org name (as found in news source)
        matched_name: CSV matched org name (from fuzzy matcher matched_row)
        ein:          EIN if already known — skips search step
        verbose:      Print progress

    Returns:
        ProPublicaResult with 990 data and parsed officer table
    """
    result = ProPublicaResult(
        incoming_name=org_name,
        matched_org_name=matched_name,
    )

    # Step 1 — find EIN if not provided
    if not ein:
        search_name = matched_name or org_name
        query = urllib.parse.urlencode({"q": search_name})
        url   = f"{SEARCH_ENDPOINT}?{query}"

        if verbose:
            print(f"  [ProPublica] Searching: {search_name[:50]}")

        data, error = _get_json(url)
        if error:
            result.error = error
            return result

        organizations = (data or {}).get("organizations", [])
        if not organizations:
            result.error = "No results found"
            return result

        # Take the first result — best match by ProPublica's own ranking
        org = organizations[0]
        ein = str(org.get("ein", "")).strip()
        if not ein:
            result.error = "EIN not in search result"
            return result

        time.sleep(REQUEST_DELAY_S)

    # Step 2 — fetch full org record by EIN
    url = f"{ORG_ENDPOINT}/{ein}.json"

    if verbose:
        print(f"  [ProPublica] Fetching EIN: {ein}")

    data, error = _get_json(url)
    if error:
        result.error = error
        return result

    org_data = (data or {}).get("organization", {})
    filings  = (data or {}).get("filings_with_data", [])

    if not org_data:
        result.error = "Organization record empty"
        return result

    # Populate identity fields
    result.ein          = str(ein)
    result.org_name_990 = org_data.get("name", "")
    result.city         = org_data.get("city", "")
    result.state        = org_data.get("state", "")
    result.ntee_code    = org_data.get("ntee_code", "")
    result.found        = True

    # Financial fields from most recent filing
    if filings:
        latest = filings[0]
        result.total_assets  = latest.get("totassetsend") or latest.get("total_assets")
        result.total_revenue = latest.get("totrevenue") or latest.get("total_revenue")
        result.total_income  = latest.get("totfuncexpns") or latest.get("total_income")
        result.tax_year      = latest.get("tax_prd_yr") or latest.get("taxyear")

        # Normalize types
        for field_name in ("total_assets", "total_revenue", "total_income"):
            val = getattr(result, field_name)
            if val is not None:
                try:
                    setattr(result, field_name, int(float(str(val).replace(",", ""))))
                except (ValueError, TypeError):
                    setattr(result, field_name, None)

    # Parse officer table
    result.officers = _parse_officers(filings)
    result.departed_officers = [o for o in result.officers if o.is_departed]

    if verbose:
        print(f"  [ProPublica] Found: {result.org_name_990} · {result.aum_display}")
        if result.departed_officers:
            print(f"  [ProPublica] Departed officers: {len(result.departed_officers)}")
            for o in result.departed_officers:
                print(f"    → {o.summary()}")

    return result


# ── BATCH ENRICHMENT ──────────────────────────────────────────────────────────

def enrich_batch(
    match_results: list,
    verbose: bool = True,
) -> list[ProPublicaResult]:
    """
    Enrich a batch of fuzzy matcher HIGH results with ProPublica data.

    Args:
        match_results: List of MatchResult objects (from lark_fuzzy_matcher)
                       where result.is_match=True and result.meets_aum_threshold=True
        verbose:       Print progress

    Returns:
        List of ProPublicaResult — one per input match result

    Usage:
        from utilities.lark_propublica import enrich_batch

        high_matches = [r for r in results if r.is_match and r.meets_aum_threshold]
        enriched = enrich_batch(high_matches)

        for pr in enriched:
            print(pr.summary())
    """
    if not match_results:
        return []

    if verbose:
        print(f"\n[ProPublica] Enriching {len(match_results)} HIGH matches...")

    enriched = []

    for i, match in enumerate(match_results):
        # Extract org names from the MatchResult
        incoming_name = match.incoming_name
        matched_name  = ""
        if match.matched_row:
            matched_name = match.matched_row.get("Org Name", "") or incoming_name

        if verbose:
            print(f"\n  [{i+1}/{len(match_results)}] {matched_name[:50]}")

        result = enrich_org(
            org_name=incoming_name,
            matched_name=matched_name,
            verbose=verbose,
        )
        enriched.append(result)

        # Polite delay between orgs
        if i < len(match_results) - 1:
            time.sleep(REQUEST_DELAY_S)

    if verbose:
        found     = sum(1 for r in enriched if r.found)
        not_found = sum(1 for r in enriched if not r.found)
        departed  = sum(len(r.departed_officers) for r in enriched)
        print(f"\n[ProPublica] Batch complete:")
        print(f"  Found:            {found}")
        print(f"  Not found:        {not_found}")
        print(f"  Departed officers:{departed} (potential SIG-001/002 corroboration)")

    return enriched


# ── WRITE-BACK DICT ───────────────────────────────────────────────────────────

def to_hubspot_fields(pr: "ProPublicaResult") -> dict:
    """
    Convert a ProPublicaResult to HubSpot write-back field dict.
    Maps to properties defined in data/hubspot-properties.md.
    """
    if not pr.found:
        return {}

    return {
        "lark_aum_estimated":  pr.total_assets,
        "lark_aum_source":     f"IRS 990 · tax year {pr.tax_year}" if pr.tax_year else "IRS 990",
        "lark_propublica_ein": pr.ein,
        "lark_notes":          _build_notes(pr),
    }


def _build_notes(pr: "ProPublicaResult") -> str:
    parts = [f"ProPublica 990 · EIN {pr.ein} · tax year {pr.tax_year}"]
    parts.append(f"AUM: ${pr.total_assets:,}" if pr.total_assets else "AUM: not found")
    parts.append(f"NTEE: {pr.ntee_code}" if pr.ntee_code else "")
    if pr.departed_officers:
        parts.append("Departed officers: " + "; ".join(
            o.summary() for o in pr.departed_officers
        ))
    return " · ".join(p for p in parts if p)


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: enriches a known nonprofit (Candid, EIN 13-1837418)
    and prints the result. No API key needed.

    Run from Lark/ directory:
        python utilities/lark_propublica.py
    """
    print("\n🪶  lark_propublica.py — self-test")
    print("   Testing with: Candid · EIN 13-1837418\n")

    result = enrich_org(
        org_name="Candid",
        matched_name="CANDID",
        ein="13-1837418",
        verbose=True,
    )

    print(f"\n{result.summary()}")

    fields = to_hubspot_fields(result)
    if fields:
        print(f"\nHubSpot fields:")
        for k, v in fields.items():
            print(f"  {k}: {v}")

    print(f"\n✓ lark_propublica.py ready. Use enrich_batch() in Phase 3.\n")
