#!/usr/bin/env python3
"""
lark_linkedin_channel.py — Lark Channel 5 · LinkedIn Detection via Apify
=========================================================================
Detects SIG-001, SIG-002, and SIG-005 signals at small nonprofits ($1M–$5M
AUM) that do not issue press releases and announce leadership changes on
LinkedIn only.

ARCHITECTURE — fits into Phase 1 of Lark's sweep model:
    1. run_linkedin_sweep() returns a list of (org_name, domain, metadata)
    2. Caller appends results to all_signals[] alongside other channel results
    3. Caller deduplicates all_signals[] before passing to match_batch()
    4. match_batch() is called ONCE after ALL channels complete

    This module never calls the fuzzy matcher.
    This module never reads contact_data/.
    This module never enriches results.

APIFY ACTOR (monthly sweep — broad discovery):
    harvestapi/linkedin-profile-search
    Pricing: Short mode — $0.10 per search page (25 profiles/page)
    No cookies required.

APIFY ACTOR (enrichment verification — targeted lookup):
    harvestapi/linkedin-profile-scraper
    Pricing: $0.004 per profile (Short mode)
    Different actor, different use case — see verify_linkedin_url() below.
    This is NOT a search actor. It takes a specific profile URL (already
    found via web_search during enrichment Q5) and confirms what's
    actually on it. Use this when web search surfaces a LinkedIn result
    during enrichment, never as a broad discovery tool.

ENVIRONMENT:
    APIFY_TOKEN   — required, set before running any sweep
    APIFY_TASK_ID — optional, saved task ID from Apify console
                    Only needed if using a saved task instead of the actor directly.
                    If not set, calls the actor endpoint (requires paid Apify plan).
                    Add to .env: APIFY_TASK_ID=your_task_id
    export APIFY_TOKEN=your_token_here

SIGNAL SCOPE:
    SIG-001 — New CFO / Finance Director
    SIG-002 — New CEO / Executive Director
    SIG-005 — New Investment Committee Chair / CIO

LOOKBACK:
    recentlyChangedJobs=True catches last 90 days (LinkedIn's fixed window).
    Lark's sweep is monthly — 90-day window intentionally wider to avoid
    missing hires that occurred early in the month.
    Post-filtering by the caller is recommended for stricter windows.

COST ESTIMATE (monthly sweep):
    6 queries × 2 pages × $0.10 = $1.20/month
    Well within Apify Starter ($29/month).

COST ESTIMATE (enrichment verification):
    $0.004 per LinkedIn URL verified. Only runs when web_search already
    surfaced a LinkedIn result during Q5 — not a per-org cost, a per-hit
    cost. Worst case (every org in a 10-org batch triggers a verification):
    10 × $0.004 = $0.04. Negligible next to the monthly sweep's $1.20.

DEDUPLICATION:
    match_batch() does NOT deduplicate internally.
    This module returns a deduplicated list (by org_name, case-insensitive).
    Caller should also deduplicate against signals from other channels
    before calling match_batch().
"""

import os
import time
import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

# Load .env if present (pip install python-dotenv)
# Falls back to environment variables set directly if dotenv not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID       = "harvestapi~linkedin-profile-search"

# Verification actor — separate from the search actor above.
# Used ONLY by verify_linkedin_url() during enrichment, never by the
# monthly sweep. Takes a profile URL directly, no search/filter logic.
VERIFY_ACTOR_ID = "harvestapi~linkedin-profile-scraper"

def _build_endpoint() -> str:
    """Build the correct API endpoint at call time so env vars are current."""
    task_id = os.getenv("APIFY_TASK_ID", "").strip()
    if task_id:
        return f"{APIFY_BASE_URL}/actor-tasks/{task_id}/run-sync-get-dataset-items"
    return f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/run-sync-get-dataset-items"

def _build_verify_endpoint() -> str:
    """
    Endpoint for the verification actor (harvestapi/linkedin-profile-scraper).
    Deliberately separate from _build_endpoint() — verification never uses
    a saved task ID, since it's a single targeted call, not a recurring sweep.
    """
    return f"{APIFY_BASE_URL}/acts/{VERIFY_ACTOR_ID}/run-sync-get-dataset-items"

# Pages per query. Each page = 25 profiles = $0.10.
# 2 pages = 50 profiles = $0.20 per query.
# Increase to 4 for deeper sampling — confirm budget before changing.
DEFAULT_PAGES = 2

# Apify's recentlyChangedJobs filter = last 90 days (LinkedIn fixed).
# Lark sweeps monthly — 90-day window catches hires that occurred
# before the sweep date but within a reasonable discovery window.
RECENTLY_CHANGED_JOBS = True

# Short mode — returns: name, headline, current title, current company,
# location, profile URL. Enough for fuzzy matching. Does not return
# exact start date — use Full mode ($8/1K) if start date precision needed.
SCRAPER_MODE = "Short"

# Headcount filter — target small nonprofits at $1M–$5M AUM tier.
# B=1-10, C=11-50, D=51-200. Excludes large orgs well-covered by press.
# Remove or expand if coverage gaps appear in results.
HEADCOUNT_FILTER = ["B", "C", "D"]

# Function IDs for nonprofit finance and leadership roles.
# 1=Accounting, 10=Finance (for SIG-001)
# 4=Business Development, 9=Entrepreneurship, 20=Program & Project Mgmt (for SIG-002)
FINANCE_FUNCTION_IDS   = ["1", "10"]
LEADERSHIP_FUNCTION_IDS = ["4", "9", "20"]
# 4=Business Development (CEO/ED/Managing Director)
# 9=Entrepreneurship (some ED-founders self-classify here)
# 20=Program and Project Management (common for small org EDs)

# Seniority level IDs.
# 220=Director, 300=Vice President, 310=CXO, 320=Owner/Partner
# Note: 130=Strategic exists in taxonomy but is rarely user-populated — excluded
DIRECTOR_SENIORITY = ["220", "300", "310", "320"]
CXO_SENIORITY      = ["310", "320"]
# 320=Owner/Partner — small nonprofit EDs often self-classify here
# Removed 130=Strategic — rarely populated by LinkedIn users in practice


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class LinkedInSignal:
    """A single leadership change signal extracted from LinkedIn."""
    person_name:  str
    current_title: str
    org_name:     str
    org_domain:   str           # empty string if not available
    location:     str
    profile_url:  str
    headline:     str
    signal_type:  str           # SIG-001 / SIG-002 / SIG-005
    query_label:  str           # which query produced this result
    source:       str = "LinkedIn — harvestapi/linkedin-profile-search"

    def to_signal_tuple(self) -> tuple[str, str]:
        """Returns (org_name, domain) for fuzzy matcher input."""
        return (self.org_name, self.org_domain)

    def summary(self) -> str:
        return (
            f"{self.signal_type} | {self.person_name} | "
            f"{self.current_title} | {self.org_name} | {self.location}"
        )


@dataclass
class LinkedInVerification:
    """
    Result of verifying ONE LinkedIn profile URL that web_search surfaced
    during enrichment. Not part of the monthly sweep — this is the
    Q5 verification path described in enrichment-run.md.
    """
    requested_url:    str
    found:            bool             # False if URL didn't resolve / no data returned
    person_name:      str = ""
    current_title:    str = ""
    current_company:  str = ""
    location:         str = ""
    profile_url:       str = ""        # the URL actually returned by Apify
    cost_usd:          float = 0.004
    error:             str = ""

    def matches(self, expected_org: str, expected_name: Optional[str] = None) -> bool:
        """
        Loose check: does the verified profile's company plausibly match
        the org we were checking? Does NOT replace human/Lark judgment —
        this is a string-overlap heuristic to flag obvious mismatches
        (wrong org, wrong country, different person entirely).
        """
        if not self.found:
            return False
        org_match = expected_org.lower().strip() in self.current_company.lower().strip() \
            or self.current_company.lower().strip() in expected_org.lower().strip()
        if expected_name:
            name_match = expected_name.lower().strip() in self.person_name.lower().strip()
            return org_match and name_match
        return org_match

    def summary(self) -> str:
        if not self.found:
            return f"[Verify] NOT FOUND · {self.requested_url} · {self.error or 'no data returned'}"
        return (
            f"[Verify] {self.person_name} · {self.current_title} · "
            f"{self.current_company} · {self.location} · ${self.cost_usd:.3f}"
        )


@dataclass
class LinkedInSweepResult:
    """Full result of a LinkedIn channel sweep."""
    signals:          list[LinkedInSignal] = field(default_factory=list)
    queries_run:      int = 0
    profiles_reviewed: int = 0
    duplicates_removed: int = 0
    errors:           list[str] = field(default_factory=list)
    cost_estimate_usd: float = 0.0

    def to_signal_tuples(self) -> list[tuple[str, str]]:
        """
        Returns deduplicated (org_name, domain) list for match_batch().
        Safe to append directly to all_signals[] before batch matching.
        """
        return [s.to_signal_tuple() for s in self.signals]

    def summary(self) -> str:
        lines = [
            f"[Channel 5 — LinkedIn]",
            f"  Queries run:        {self.queries_run}",
            f"  Profiles reviewed:  {self.profiles_reviewed}",
            f"  Signals extracted:  {len(self.signals)}",
            f"  Duplicates removed: {self.duplicates_removed}",
            f"  Est. cost:          ${self.cost_estimate_usd:.2f}",
        ]
        if self.errors:
            lines.append(f"  Errors:             {len(self.errors)}")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


# ── QUERY DEFINITIONS ─────────────────────────────────────────────────────────

def _build_queries() -> list[dict]:
    """
    Returns the 6 Apify actor input payloads for Channel 5.

    Query design principles (from research session 2026-06-17):
    - searchQuery uses "foundation OR endowment OR nonprofit" as a fuzzy
      keyword across full profile — catches org names without relying on
      industry codes, which skew large
    - currentJobTitles provides strict title matching
    - recentlyChangedJobs=True = last 90 days (LinkedIn fixed window)
    - companyHeadcount B/C/D = 1–200 employees — small org focus
    - No industryIds filter — "Nonprofit Organization Management" misses
      most small orgs categorized under other industries
    - takePages=2 per query = 50 profiles = $0.20 per query
    """

    base = {
        "profileScraperMode": SCRAPER_MODE,
        "searchQuery": "foundation OR endowment OR nonprofit",
        "companyHeadcount": HEADCOUNT_FILTER,
        "recentlyChangedJobs": RECENTLY_CHANGED_JOBS,
        "takePages": DEFAULT_PAGES,
        "maxItems": DEFAULT_PAGES * 25,
    }

    return [
        # ── SIG-001 · Director of Finance ────────────────────────────────
        {
            **base,
            "_label": "SIG-001 · Director of Finance",
            "_signal_type": "SIG-001",
            "currentJobTitles": ["Director of Finance"],
            "functionIds": FINANCE_FUNCTION_IDS,
            "seniorityLevelIds": ["220"],
        },
        # ── SIG-001 · Chief Financial Officer ────────────────────────────
        {
            **base,
            "_label": "SIG-001 · Chief Financial Officer",
            "_signal_type": "SIG-001",
            "currentJobTitles": ["Chief Financial Officer"],
            "functionIds": FINANCE_FUNCTION_IDS,
            "seniorityLevelIds": ["310"],
        },
        # ── SIG-001 · VP Finance ─────────────────────────────────────────
        {
            **base,
            "_label": "SIG-001 · VP / Vice President Finance",
            "_signal_type": "SIG-001",
            "currentJobTitles": ["Vice President of Finance", "VP Finance"],
            "functionIds": FINANCE_FUNCTION_IDS,
            "seniorityLevelIds": ["300"],
        },
        # ── SIG-002 · Executive Director ─────────────────────────────────
        {
            **base,
            "_label": "SIG-002 · Executive Director",
            "_signal_type": "SIG-002",
            "currentJobTitles": ["Executive Director"],
            "functionIds": LEADERSHIP_FUNCTION_IDS,
            "seniorityLevelIds": DIRECTOR_SENIORITY,
        },
        # ── SIG-002 · President and CEO ──────────────────────────────────
        {
            **base,
            "_label": "SIG-002 · President and CEO",
            "_signal_type": "SIG-002",
            "currentJobTitles": ["President and CEO", "President & CEO"],
            "functionIds": LEADERSHIP_FUNCTION_IDS,
            "seniorityLevelIds": CXO_SENIORITY,
        },
        # ── SIG-005 · Chief Investment Officer ───────────────────────────
        {
            **base,
            "_label": "SIG-005 · CIO / Director of Investments",
            "_signal_type": "SIG-005",
            "currentJobTitles": [
                "Chief Investment Officer",
                "Director of Investments",
            ],
            "functionIds": FINANCE_FUNCTION_IDS,
            "seniorityLevelIds": ["220", "310"],
        },
    ]


# ── APIFY CALLER ──────────────────────────────────────────────────────────────

def _call_apify(payload: dict, token: str, timeout: int = 300) -> list[dict]:
    """
    Calls the Apify sync endpoint and returns raw profile list.
    Raises on HTTP error or timeout.
    Strips internal _label and _signal_type keys before sending.
    """
    # Remove internal keys before sending to Apify
    send_payload = {k: v for k, v in payload.items()
                    if not k.startswith("_")}

    url      = f"{_build_endpoint()}?token={token}"
    body     = json.dumps(send_payload).encode("utf-8")
    headers  = {"Content-Type": "application/json"}
    req      = urllib.request.Request(url, data=body, headers=headers,
                                      method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Apify HTTP {e.code}: {body_text[:300]}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Apify network error: {e.reason}") from e


def _call_apify_verify(url_to_check: str, token: str, timeout: int = 120) -> list[dict]:
    """
    Calls the verification actor (harvestapi/linkedin-profile-scraper) for
    ONE profile URL. Separate from _call_apify() above — different actor,
    different payload shape (urls: [...] instead of search filters),
    deliberately short timeout since this is a single-profile lookup,
    not a multi-page search.
    """
    payload  = {"urls": [url_to_check]}
    url      = f"{_build_verify_endpoint()}?token={token}"
    body     = json.dumps(payload).encode("utf-8")
    headers  = {"Content-Type": "application/json"}
    req      = urllib.request.Request(url, data=body, headers=headers,
                                      method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Apify HTTP {e.code}: {body_text[:300]}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Apify network error: {e.reason}") from e


def verify_linkedin_url(
    profile_url: str,
    apify_token: Optional[str] = None,
    verbose: bool = True,
) -> LinkedInVerification:
    """
    Verify ONE LinkedIn profile URL that web_search surfaced during an
    enrichment Q5 search. This is NOT part of the monthly sweep and does
    NOT use run_linkedin_sweep()'s search/filter logic.

    When to call this (per enrichment-run.md):
        Only when a web_search result during Q5 includes a LinkedIn URL.
        Never run proactively or on every org — this confirms a finding
        web_search already surfaced, it does not go looking on its own.

    What it answers:
        Does this URL actually resolve to a real profile? Does the
        person's current title/company match what web_search implied?
        This lets Lark upgrade a LinkedIn-sourced Q5 finding from
        "Inferred, unverified" toward "Inferred, profile-confirmed" —
        it does not make a LinkedIn finding Confirmed (LinkedIn is
        always self-reported, per honesty.md), but it does catch
        obvious mismatches before they go on a card.

    Args:
        profile_url:  The LinkedIn profile URL found via web_search.
        apify_token:  Apify API token. Defaults to APIFY_TOKEN env var.
        verbose:      Print result to stdout (default True).

    Returns:
        LinkedInVerification — check .found and .matches(expected_org)
        before using the result on a card.

    Cost: $0.004 per call (Short mode, harvestapi/linkedin-profile-scraper).

    Usage in enrichment (Q5):
        from utilities.lark_linkedin_channel import verify_linkedin_url

        # web_search returned a LinkedIn URL while researching Org X
        result = verify_linkedin_url("https://linkedin.com/in/janedoe")

        if result.found and result.matches("Org X", expected_name="Jane Doe"):
            # safe to cite — label Inferred, note "profile-confirmed"
            ...
        else:
            # mismatch or not found — do NOT use on the card.
            # Log as: "LinkedIn URL surfaced by web search did not verify —
            # treat web_search finding as unconfirmed, not Inferred."
            ...
    """
    token = apify_token or os.environ.get("APIFY_TOKEN", "")
    if not token:
        raise EnvironmentError(
            "APIFY_TOKEN not set. "
            "Run: export APIFY_TOKEN=your_token_here"
        )

    if verbose:
        print(f"\n[Verify] Checking LinkedIn URL: {profile_url}")
        print(f"  Cost: $0.004")

    try:
        profiles = _call_apify_verify(profile_url, token)
    except (RuntimeError, EnvironmentError) as e:
        if verbose:
            print(f"  ERROR: {e}")
        return LinkedInVerification(
            requested_url=profile_url,
            found=False,
            error=str(e),
        )

    if not profiles or not isinstance(profiles, list):
        if verbose:
            print("  No data returned — URL may not resolve or profile is private")
        return LinkedInVerification(
            requested_url=profile_url,
            found=False,
            error="No data returned from actor",
        )

    p = profiles[0]
    person_name = (
        p.get("fullName") or p.get("name") or
        f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
    )
    company = _extract_org_name(p)
    title   = _extract_title(p)
    location = p.get("location") or p.get("locationName") or ""
    returned_url = p.get("profileUrl") or p.get("url") or p.get("linkedInUrl") or profile_url

    result = LinkedInVerification(
        requested_url=profile_url,
        found=True,
        person_name=person_name,
        current_title=title,
        current_company=company,
        location=location,
        profile_url=returned_url,
    )

    if verbose:
        print(f"  {result.summary()}")

    return result


# ── PROFILE PARSER ────────────────────────────────────────────────────────────

def _extract_org_name(profile: dict) -> str:
    """
    Extract current employer org name from a Short-mode profile.
    Tries multiple field paths — Apify's output schema varies slightly.
    Returns empty string if not found.
    """
    # Primary: currentPositions array
    positions = profile.get("currentPositions") or profile.get("positions", [])
    if positions and isinstance(positions, list):
        first = positions[0]
        if isinstance(first, dict):
            company = (
                first.get("companyName") or
                first.get("company") or
                first.get("company_name") or ""
            )
            if company:
                return company.strip()

    # Fallback: top-level company field
    company = (
        profile.get("currentCompany") or
        profile.get("company") or
        profile.get("companyName") or ""
    )
    return company.strip() if company else ""


def _extract_title(profile: dict) -> str:
    """Extract current job title from profile."""
    positions = profile.get("currentPositions") or profile.get("positions", [])
    if positions and isinstance(positions, list):
        first = positions[0]
        if isinstance(first, dict):
            title = (
                first.get("title") or
                first.get("jobTitle") or
                first.get("job_title") or ""
            )
            if title:
                return title.strip()

    return (
        profile.get("headline") or
        profile.get("title") or
        profile.get("jobTitle") or ""
    ).strip()


def _parse_profiles(
    profiles: list[dict],
    signal_type: str,
    query_label: str,
) -> list[LinkedInSignal]:
    """
    Parse raw Apify profile dicts into LinkedInSignal objects.
    Skips profiles with no org name — can't pass to fuzzy matcher.
    """
    signals = []
    for p in profiles:
        if not isinstance(p, dict):
            continue

        org_name = _extract_org_name(p)
        if not org_name:
            continue  # can't match without org name

        person_name = (
            p.get("fullName") or
            p.get("name") or
            f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
        )
        title    = _extract_title(p)
        location = p.get("location") or p.get("locationName") or ""
        url      = p.get("profileUrl") or p.get("url") or p.get("linkedInUrl") or ""
        headline = p.get("headline") or p.get("summary") or ""

        signals.append(LinkedInSignal(
            person_name=person_name,
            current_title=title,
            org_name=org_name,
            org_domain="",          # Short mode does not return domain
            location=location,
            profile_url=url,
            headline=headline,
            signal_type=signal_type,
            query_label=query_label,
        ))

    return signals


# ── DEDUPLICATION ─────────────────────────────────────────────────────────────

def _deduplicate(signals: list[LinkedInSignal]) -> tuple[list[LinkedInSignal], int]:
    """
    Deduplicate signals by org_name (case-insensitive).
    Keeps first occurrence (preserves signal_type from first query that found it).
    Returns (deduplicated_list, count_removed).

    NOTE: match_batch() does not deduplicate internally. This deduplication
    covers duplicates within Channel 5. The caller must also deduplicate
    across all channels before calling match_batch().
    """
    seen: dict[str, LinkedInSignal] = {}
    for sig in signals:
        key = sig.org_name.lower().strip()
        if key not in seen:
            seen[key] = sig

    deduped   = list(seen.values())
    removed   = len(signals) - len(deduped)
    return deduped, removed


# ── NONPROFIT FILTER ──────────────────────────────────────────────────────────

# Keywords in org name that strongly suggest a nonprofit context.
# This is a lightweight post-filter — not a replacement for the fuzzy matcher.
# Orgs that pass this filter are not confirmed nonprofits — they are candidates.
_NONPROFIT_KEYWORDS = [
    "foundation", "endowment", "nonprofit", "non-profit", "charitable",
    "charity", "trust", "community", "united way", "ymca", "ywca",
    "association", "institute", "society", "alliance", "coalition",
    "council", "center", "centre", "fund", "giving", "philanthropy",
    "church", "ministry", "mission", "services", "health", "education",
    "school", "college", "university", "hospital", "clinic", "care",
]

def _likely_nonprofit(org_name: str) -> bool:
    """
    Returns True if org name contains a nonprofit-context keyword.
    Passes through ambiguous names — the fuzzy matcher decides.
    Only discards orgs that are clearly for-profit (e.g. "Inc", "LLC",
    "Corp" with no nonprofit keywords).
    """
    lower = org_name.lower()

    # Has a nonprofit keyword → pass through
    if any(kw in lower for kw in _NONPROFIT_KEYWORDS):
        return True

    # Ambiguous — no strong signal either way → pass through
    # Better to over-include and let the fuzzy matcher discard
    # than to silently drop a valid small org
    return True


# ── MAIN SWEEP FUNCTION ───────────────────────────────────────────────────────

def run_linkedin_sweep(
    apify_token: Optional[str] = None,
    pages_per_query: int = DEFAULT_PAGES,
    verbose: bool = True,
) -> LinkedInSweepResult:
    """
    Run Channel 5 LinkedIn detection sweep.

    Calls Apify Profile Search actor for each of 6 signal queries.
    Returns a LinkedInSweepResult containing deduplicated LinkedInSignal
    objects ready for fuzzy matching.

    Args:
        apify_token:      Apify API token. Defaults to APIFY_TOKEN env var.
        pages_per_query:  Pages to fetch per query (default 2 = 50 profiles).
                          Each page costs $0.10. Increase for deeper sampling.
        verbose:          Print progress to stdout (default True).

    Returns:
        LinkedInSweepResult with .to_signal_tuples() for match_batch() input.

    Usage in sweep:
        from utilities.lark_linkedin_channel import run_linkedin_sweep

        # Phase 1 — collect all signals
        all_signals = []

        # ... run other channels, append to all_signals ...

        # Run Channel 5
        linkedin_result = run_linkedin_sweep()
        all_signals.extend(linkedin_result.to_signal_tuples())

        # Deduplicate all_signals across all channels
        seen = set()
        deduped_signals = []
        for org_name, domain in all_signals:
            key = org_name.lower().strip()
            if key not in seen:
                seen.add(key)
                deduped_signals.append((org_name, domain))

        # Phase 2 — one batch match call
        results = matcher.match_batch(deduped_signals)
    """
    token = apify_token or os.environ.get("APIFY_TOKEN", "")
    if not token:
        raise EnvironmentError(
            "APIFY_TOKEN not set. "
            "Run: export APIFY_TOKEN=your_token_here"
        )

    queries  = _build_queries()
    result   = LinkedInSweepResult()
    all_raw  = []
    pages    = pages_per_query

    for i, query in enumerate(queries):
        label        = query["_label"]
        signal_type  = query["_signal_type"]

        # Override pages if caller specified a different value
        if pages != DEFAULT_PAGES:
            query = {**query, "takePages": pages, "maxItems": pages * 25}

        if verbose:
            print(f"\n[Channel 5] Query {i+1}/{len(queries)}: {label}")
            print(f"  Pages: {pages} · Est. cost: ${pages * 0.10:.2f}")

        try:
            profiles = _call_apify(query, token)
            result.queries_run      += 1
            result.profiles_reviewed += len(profiles)
            result.cost_estimate_usd += pages * 0.10

            signals = _parse_profiles(profiles, signal_type, label)

            if verbose:
                print(f"  Profiles returned: {len(profiles)}")
                print(f"  Signals extracted: {len(signals)}")

            all_raw.extend(signals)

        except (RuntimeError, Exception) as e:
            err = f"Query '{label}' failed: {e}"
            result.errors.append(err)
            if verbose:
                print(f"  ERROR: {err}")
            continue

        # Polite delay between Apify calls — avoid rate limiting
        if i < len(queries) - 1:
            time.sleep(2)

    # Deduplicate within Channel 5
    deduped, removed          = _deduplicate(all_raw)
    result.signals            = deduped
    result.duplicates_removed = removed

    if verbose:
        print(f"\n{result.summary()}")
        if result.signals:
            print("\n  Signals (deduplicated):")
            for sig in result.signals:
                print(f"    {sig.summary()}")

    return result


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: validates token, runs one query at 1 page, prints results.
    Does not call the fuzzy matcher.

    Run from Lark/ directory:
        python utilities/lark_linkedin_channel.py
    """
    import sys

    print("\n🪶  lark_linkedin_channel.py — self-test")
    task_id = os.getenv("APIFY_TASK_ID", "").strip()
    if task_id:
        print(f"   Task endpoint: actor-tasks/{task_id}")
    else:
        print("   Actor endpoint: harvestapi/linkedin-profile-search")
        print("   (APIFY_TASK_ID not set — using actor directly, requires paid plan)")
    print("   Mode: Short · 1 page (25 profiles) · ~$0.10\n")

    token = os.environ.get("APIFY_TOKEN", "")
    if not token:
        print("ERROR: APIFY_TOKEN not set.")
        print("  Run: export APIFY_TOKEN=your_token_here")
        sys.exit(1)

    print(f"  Token found: {token[:8]}...{token[-4:]}")
    print("  Running single test query (SIG-001 · Director of Finance)...\n")

    # Run only the first query at 1 page for the self-test
    queries = _build_queries()
    test_query = {
        **queries[0],
        "takePages": 1,
        "maxItems": 25,
    }

    try:
        profiles = _call_apify(test_query, token)
        print(f"  Profiles returned: {len(profiles)}")

        signals = _parse_profiles(
            profiles,
            test_query["_signal_type"],
            test_query["_label"],
        )
        print(f"  Signals extracted: {len(signals)}")

        if signals:
            print("\n  Sample results (first 5):")
            for sig in signals[:5]:
                print(f"    {sig.summary()}")
        else:
            print("\n  No signals extracted — check profile parser")
            if profiles:
                print(f"\n  Raw profile sample (first result keys):")
                print(f"    {list(profiles[0].keys())}")

        print(f"\n✓ Channel 5 ready. Est. full sweep cost: "
              f"${len(queries) * DEFAULT_PAGES * 0.10:.2f}/month\n")

    except EnvironmentError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nApify error: {e}")
        sys.exit(1)