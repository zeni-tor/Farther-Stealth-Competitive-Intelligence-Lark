#!/usr/bin/env python3
"""
lark_newsapi.py — Lark Layer B · Currents API Structured News Search
=====================================================================
Queries the Currents API for nonprofit leadership and financial event news
within a reliable date window. Solves the unreliable after: operator problem
in Claude's web_search() tool.

ROLE IN PIPELINE:
    Layer A (GlobeNewswire RSS) — press releases, date-reliable
    Layer B (Currents API)      — broader news coverage, date-reliable  ← this
    Layer C (web_search)        — long tail, org sites, niche sources

    Currents runs BEFORE web_search. web_search fills gaps Currents misses.
    Do not run both on identical queries — Currents handles the broad sweep.

SETUP:
    1. Sign up free at: currentsapi.services/en/register
    2. No credit card required
    3. Add key to .env: CURRENTS_API_KEY=your_key_here
    4. Free tier: 1,000 requests/day · commercial use permitted
    5. Lark uses ~25 requests per monthly sweep

API ENDPOINT:
    https://api.currentsapi.services/v1/search
    Parameters: keywords, query (Boolean), language, country, start_date, end_date

COST: Free tier covers Lark's monthly sweep volume (~25 req/sweep).

SIGNAL COVERAGE:
    SIG-001 — New CFO / Finance Director
    SIG-002 — New CEO / Executive Director
    SIG-003 — Capital Campaign Close
    SIG-004 — Large Gift or Bequest
    SIG-006 — Capital Campaign Launch

    SIG-005, SIG-007, SIG-008, SIG-009, SIG-010 are better served by
    LinkedIn (Apify), ProPublica (990), or targeted web_search queries.
"""

import os
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

CURRENTS_SEARCH_URL = "https://api.currentsapi.services/v1/search"
REQUEST_DELAY_S     = 0.5    # polite delay between queries
REQUEST_TIMEOUT_S   = 20
MAX_RESULTS_PER_QUERY = 100  # Currents free tier allows up to 300


# ── QUERY DEFINITIONS ─────────────────────────────────────────────────────────

def _build_queries(start_date: str, end_date: str) -> list[dict]:
    """
    Returns list of Currents API query dicts for Lark's signal coverage.

    Query design principles (from research session 2026-06-17):
    - Boolean syntax with AND/OR/NOT and quotes
    - country=US and language=en on every query
    - start_date / end_date enforced at API level — reliable, not after: guessing
    - Currents handles broad sweep; web_search fills long tail
    - Do not duplicate queries already well-served by Layer A (GlobeNewswire RSS)
    """
    base = {
        "language": "en",
        "country":  "US",
        "start_date": start_date,
        "end_date":   end_date,
        "page_size":  str(MAX_RESULTS_PER_QUERY),
    }

    return [
        # ── SIG-001 · CFO / Finance Director ─────────────────────────────
        {
            **base,
            "_label":       "SIG-001 · CFO — foundation/endowment anchor",
            "_signal_type": "SIG-001",
            "query": (
                '(foundation OR endowment) AND '
                '("chief financial officer" OR "director of finance") AND '
                '(named OR appointed OR announces)'
            ),
        },
        {
            **base,
            "_label":       "SIG-001 · CFO — 501c3 anchor",
            "_signal_type": "SIG-001",
            "query": (
                '"501(c)(3)" AND '
                '("chief financial officer" OR "director of finance") AND '
                '(named OR appointed)'
            ),
        },

        # ── SIG-002 · CEO / Executive Director ───────────────────────────
        {
            **base,
            "_label":       "SIG-002 · ED/CEO — foundation/endowment anchor",
            "_signal_type": "SIG-002",
            "query": (
                '(foundation OR endowment) AND '
                '("executive director" OR "president and CEO") AND '
                '(named OR appointed OR announces)'
            ),
        },
        {
            **base,
            "_label":       "SIG-002 · ED/CEO — nonprofit anchor",
            "_signal_type": "SIG-002",
            "query": (
                '"501(c)(3)" AND '
                '("executive director" OR "president and CEO") AND '
                '(named OR appointed)'
            ),
        },

        # ── SIG-003 · Capital Campaign Close ─────────────────────────────
        {
            **base,
            "_label":       "SIG-003 · Campaign close",
            "_signal_type": "SIG-003",
            "query": (
                'nonprofit AND '
                '("capital campaign" OR "fundraising campaign") AND '
                '(surpasses OR exceeds OR "raised" OR "goal met" OR completes)'
            ),
        },

        # ── SIG-004 · Large Gift or Bequest ──────────────────────────────
        {
            **base,
            "_label":       "SIG-004 · Large gift",
            "_signal_type": "SIG-004",
            "query": (
                '(foundation OR endowment OR nonprofit) AND '
                '("transformative gift" OR "major gift" OR bequest OR "largest gift") AND '
                'million'
            ),
        },

        # ── SIG-006 · Campaign Launch ─────────────────────────────────────
        {
            **base,
            "_label":       "SIG-006 · Campaign launch",
            "_signal_type": "SIG-006",
            "query": (
                '(foundation OR nonprofit) AND '
                '("capital campaign" OR "announces campaign" OR "campaign launch") AND '
                'million'
            ),
        },
    ]


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class NewsSignal:
    """A single signal extracted from a Currents API article."""
    org_name:     str
    domain:       str
    title:        str
    description:  str
    published:    str           # ISO date string from API
    url:          str
    signal_type:  str
    query_label:  str
    source:       str = "Currents API — Layer B"

    def to_signal_tuple(self) -> tuple[str, str]:
        return (self.org_name, self.domain)

    def summary_line(self) -> str:
        return f"{self.signal_type} | {self.org_name} | {self.published[:10]} | {self.title[:70]}"


@dataclass
class NewsSweepResult:
    """Full result of a Currents API sweep."""
    signals:          list[NewsSignal] = field(default_factory=list)
    queries_run:      int = 0
    articles_reviewed: int = 0
    duplicates_removed: int = 0
    errors:           list[str] = field(default_factory=list)

    def to_signal_tuples(self) -> list[tuple[str, str]]:
        return [s.to_signal_tuple() for s in self.signals]

    def summary(self) -> str:
        lines = [
            f"[Layer B — Currents API]",
            f"  Queries run:       {self.queries_run}",
            f"  Articles reviewed: {self.articles_reviewed}",
            f"  Signals extracted: {len(self.signals)}",
            f"  Duplicates removed:{self.duplicates_removed}",
        ]
        if self.errors:
            lines.append(f"  Errors:            {len(self.errors)}")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


# ── ORG NAME EXTRACTOR ────────────────────────────────────────────────────────

def _extract_org_name_from_article(title: str, description: str) -> str:
    """
    Extract the org name from a news article title/description.

    For press releases, the org name typically appears:
    - Before "Announces", "Names", "Appoints" in the title
    - After "at [Org]" or "of [Org]" in a hire announcement
    - As the first named entity in the description

    This is intentionally simple — the fuzzy matcher handles ambiguity.
    Better to return a slightly noisy name than to miss a match.
    """
    import re

    # Pattern: "[Org] Announces/Names/Appoints..."
    for verb in ["Announces", "Names", "Appoints", "Welcomes", "Elects", "Hires"]:
        if verb in title:
            candidate = title.split(verb)[0].strip().rstrip(" -–—")
            if 3 < len(candidate) < 100:
                return candidate

    # Pattern: "...as [Title] of/at [Org]"
    match = re.search(
        r'(?:of|at|for|with)\s+([A-Z][^,\.]{5,80}?)(?:\s*[,\.]|$)',
        title
    )
    if match:
        candidate = match.group(1).strip()
        if 5 < len(candidate) < 100:
            return candidate

    # Fallback: first capitalized phrase in title before a comma
    first = re.split(r'[,\-–—]', title)[0].strip()
    if 5 < len(first) < 80:
        return first

    return ""


def _extract_domain_from_url(url: str) -> str:
    """Extract domain from article URL."""
    import re
    if not url:
        return ""
    clean = re.sub(r'^https?://(www\.)?', '', url).split('/')[0]
    return clean.lower().strip()


# ── API CALLER ────────────────────────────────────────────────────────────────

def _call_currents(query_params: dict, api_key: str) -> tuple[list[dict], Optional[str]]:
    """
    Call the Currents API search endpoint.
    Returns (articles, error_or_None).
    """
    # Remove internal _label and _signal_type keys
    params = {k: v for k, v in query_params.items() if not k.startswith("_")}
    params["apiKey"] = api_key

    url = CURRENTS_SEARCH_URL + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            url,
            headers={"Authorization": api_key}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "ok":
                return data.get("news", []), None
            else:
                return [], f"API error: {data.get('message', 'unknown')}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return [], f"HTTP {e.code}: {body}"
    except urllib.error.URLError as e:
        return [], f"Network error: {e.reason}"
    except Exception as e:
        return [], f"Unexpected error: {e}"


# ── DEDUPLICATION ─────────────────────────────────────────────────────────────

def _deduplicate_signals(signals: list[NewsSignal]) -> tuple[list[NewsSignal], int]:
    """Deduplicate by org_name (case-insensitive). Keeps first occurrence."""
    seen: dict[str, NewsSignal] = {}
    for sig in signals:
        key = sig.org_name.lower().strip()
        if key and key not in seen:
            seen[key] = sig
    deduped = list(seen.values())
    return deduped, len(signals) - len(deduped)


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def run_currents_sweep(
    lookback_days: int = 30,
    api_key: Optional[str] = None,
    verbose: bool = True,
) -> NewsSweepResult:
    """
    Run Layer B news search via Currents API.

    Args:
        lookback_days: Days to look back from today (default 30).
        api_key:       Currents API key. Defaults to CURRENTS_API_KEY env var.
        verbose:       Print progress to stdout.

    Returns:
        NewsSweepResult with .to_signal_tuples() for match_batch() input.

    Usage in sweep (Phase 1, Layer B):
        from utilities.lark_newsapi import run_currents_sweep

        news_result = run_currents_sweep(lookback_days=30)
        all_signals.extend(news_result.to_signal_tuples())
    """
    key = api_key or os.environ.get("CURRENTS_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "CURRENTS_API_KEY not set. "
            "Sign up free at currentsapi.services/en/register "
            "and add to .env: CURRENTS_API_KEY=your_key_here"
        )

    # Build date range
    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    end_str   = end.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    queries = _build_queries(start_str, end_str)
    result  = NewsSweepResult()
    all_raw: list[NewsSignal] = []

    for i, query in enumerate(queries):
        label       = query["_label"]
        signal_type = query["_signal_type"]

        if verbose:
            print(f"\n[Layer B] Query {i+1}/{len(queries)}: {label}")

        articles, error = _call_currents(query, key)
        result.queries_run      += 1
        result.articles_reviewed += len(articles)

        if error:
            result.errors.append(f"Query '{label}': {error}")
            if verbose:
                print(f"  ERROR: {error}")
            continue

        if verbose:
            print(f"  Articles returned: {len(articles)}")

        for article in articles:
            title       = article.get("title", "")
            description = article.get("description", "") or ""
            url         = article.get("url", "")
            published   = article.get("published", "")

            org_name = _extract_org_name_from_article(title, description)
            if not org_name:
                continue

            domain = _extract_domain_from_url(url)

            all_raw.append(NewsSignal(
                org_name=org_name,
                domain=domain,
                title=title,
                description=description[:300],
                published=published,
                url=url,
                signal_type=signal_type,
                query_label=label,
            ))

        if i < len(queries) - 1:
            time.sleep(REQUEST_DELAY_S)

    # Deduplicate within Layer B
    deduped, removed          = _deduplicate_signals(all_raw)
    result.signals            = deduped
    result.duplicates_removed = removed

    if verbose:
        print(f"\n{result.summary()}")
        if result.signals:
            print("\n  Signals (deduplicated):")
            for sig in result.signals[:10]:
                print(f"    {sig.summary_line()}")
            if len(result.signals) > 10:
                print(f"    ... and {len(result.signals) - 10} more")

    return result


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: runs one SIG-001 query and prints results.
    Requires CURRENTS_API_KEY in .env.

    Run from Lark/ directory:
        python utilities/lark_newsapi.py
    """
    import sys

    print("\n🪶  lark_newsapi.py — self-test")
    print("   API: Currents API · Layer B")
    print("   Test: SIG-001 CFO query · past 30 days\n")

    key = os.environ.get("CURRENTS_API_KEY", "")
    if not key:
        print("ERROR: CURRENTS_API_KEY not set.")
        print("  Sign up free: currentsapi.services/en/register")
        print("  Add to .env: CURRENTS_API_KEY=your_key_here")
        sys.exit(1)

    print(f"  Key found: {key[:8]}...{key[-4:]}")
    print("  Running single test query (SIG-001 · foundation/endowment)...\n")

    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=30)

    queries  = _build_queries(
        start.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        end.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    )
    test_query = {**queries[0], "page_size": "10"}

    articles, error = _call_currents(test_query, key)

    if error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print(f"  Articles returned: {len(articles)}")
    for a in articles[:5]:
        print(f"  — {a.get('title', '')[:80]}")
        print(f"    {a.get('published', '')[:10]} · {a.get('url', '')[:60]}")

    print(f"\n✓ Currents API connection confirmed. Run full sweep with run_currents_sweep().\n")
