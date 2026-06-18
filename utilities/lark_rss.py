#!/usr/bin/env python3
"""
lark_rss.py — Lark Layer A · GlobeNewswire RSS Feed Parser
===========================================================
Fetches the GlobeNewswire Directors & Officers and Mergers & Acquisitions
Atom feeds. Filters entries for nonprofit signals within the lookback window.
Returns (org_name, domain) tuples ready for match_batch().

This is the most date-reliable source in Lark's pipeline. Every entry
carries a <published> timestamp — no date guessing, no after: unreliability.

FEEDS:
    Directors & Officers (subjectcode 11) — SIG-001, SIG-002, SIG-005
    Mergers & Acquisitions (subjectcode 27) — SIG-008

COST: Free. No API key. No account. No rate limits documented.

ARCHITECTURE — Phase 1 Layer A:
    feed_results = fetch_gnw_signals(lookback_days=30)
    all_signals.extend(feed_results.to_signal_tuples())

WHY THIS CLOSES THE JANM GAP:
    The Japanese American National Museum "Our Promise" campaign close
    was announced March 24, 2026 — 85 days before Lark's June 17 sweep.
    GlobeNewswire RSS would have surfaced this in real-time on March 24.
    A monthly sweep running April 17 would have caught it within the
    30-60 day SIG-003 action window. Web search did not surface it until
    the window had passed.

SIGNAL COVERAGE:
    SIG-001 — New CFO / Finance Director (Directors & Officers feed)
    SIG-002 — New CEO / Executive Director (Directors & Officers feed)
    SIG-005 — New IC Chair / CIO (Directors & Officers feed)
    SIG-008 — Merger or Restructuring (M&A feed)

DEPENDENCIES:
    feedparser — pip install feedparser
"""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import feedparser
except ImportError:
    raise ImportError(
        "feedparser is required: pip install feedparser"
    )

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── FEED URLS ─────────────────────────────────────────────────────────────────

FEEDS = {
    "directors_officers": (
        "https://www.globenewswire.com/AtomFeed/subjectcode/"
        "11-Directors%20And%20Officers/feedTitle/"
        "GlobeNewswire%20-%20Directors%20And%20Officers"
    ),
    "mergers_acquisitions": (
        "https://www.globenewswire.com/AtomFeed/subjectcode/"
        "27-Mergers%20and%20Acquisitions/feedTitle/"
        "GlobeNewswire%20-%20Mergers%20and%20Acquisitions"
    ),
}

# ── NONPROFIT KEYWORD FILTER ──────────────────────────────────────────────────
# Entry summary or title must contain at least one of these to pass through.
# Intentionally broad — the fuzzy matcher decides if the org is in pipeline.

NONPROFIT_KEYWORDS = [
    "foundation", "endowment", "nonprofit", "non-profit",
    "charitable", "charity", "501(c)", "501c",
    "community fund", "united way", "ymca", "ywca",
    "community foundation", "family foundation", "private foundation",
    "public charity", "philanthropy", "philanthropic",
    "institute", "association", "society", "alliance",
    "council", "federation", "league", "coalition",
    "museum", "arts center", "cultural center",
    "hospital foundation", "health foundation", "medical foundation",
    "university foundation", "college foundation", "school foundation",
    "church foundation", "faith foundation", "religious foundation",
]

# ── SIGNAL TITLE KEYWORDS ─────────────────────────────────────────────────────
# Leadership and financial event terms that suggest a Lark signal.
# Used to tag signal_type on each entry.

LEADERSHIP_KEYWORDS = [
    "chief financial officer", "cfo", "finance director",
    "director of finance", "vp finance", "vice president finance",
    "vice president of finance", "controller",
    "chief executive officer", "ceo", "executive director",
    "president and ceo", "president & ceo",
    "chief investment officer", "cio", "director of investments",
    "investment committee",
    "names", "named", "appoints", "appointed", "joins as",
    "hire", "hired", "welcomes", "announces appointment",
]

MERGER_KEYWORDS = [
    "merger", "merges", "merge", "merged",
    "affiliation", "affiliates", "consolidation", "consolidates",
    "acquisition", "acquires", "acquired",
    "plans to combine", "joining forces", "strategic combination",
]

CAMPAIGN_KEYWORDS = [
    "capital campaign", "campaign goal", "fundraising campaign",
    "surpasses", "exceeds", "raises $", "raised $",
    "campaign close", "campaign completion",
    "endowment campaign", "transformative gift", "major gift",
]


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class RSSSignal:
    """A single signal extracted from a GlobeNewswire feed entry."""
    org_name:     str
    domain:       str
    title:        str           # feed entry title
    summary:      str           # feed entry summary/description
    published:    datetime      # parsed pubDate — reliable
    url:          str           # link to full press release
    feed_name:    str           # "directors_officers" or "mergers_acquisitions"
    signal_type:  str           # SIG-001 / SIG-002 / SIG-005 / SIG-008 / UNKNOWN
    source:       str = "GlobeNewswire RSS — Layer A"

    def to_signal_tuple(self) -> tuple[str, str]:
        return (self.org_name, self.domain)

    def summary_line(self) -> str:
        age = (datetime.now(timezone.utc) - self.published).days
        return (
            f"{self.signal_type} | {self.org_name} | "
            f"{self.published.strftime('%Y-%m-%d')} ({age}d ago) | "
            f"{self.title[:80]}"
        )


@dataclass
class RSSFeedResult:
    """Full result of an RSS sweep across all GlobeNewswire feeds."""
    signals:          list[RSSSignal] = field(default_factory=list)
    feeds_fetched:    int = 0
    entries_reviewed: int = 0
    entries_filtered: int = 0
    errors:           list[str] = field(default_factory=list)
    fetch_duration_s: float = 0.0

    def to_signal_tuples(self) -> list[tuple[str, str]]:
        """Returns (org_name, domain) list for match_batch() input."""
        return [s.to_signal_tuple() for s in self.signals]

    def summary(self) -> str:
        lines = [
            f"[Layer A — GlobeNewswire RSS]",
            f"  Feeds fetched:    {self.feeds_fetched}",
            f"  Entries reviewed: {self.entries_reviewed}",
            f"  Passed filter:    {self.entries_filtered}",
            f"  Signals extracted:{len(self.signals)}",
            f"  Fetch time:       {self.fetch_duration_s:.1f}s",
        ]
        if self.errors:
            lines.append(f"  Errors:           {len(self.errors)}")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


# ── ORG NAME EXTRACTION ───────────────────────────────────────────────────────

def _extract_org_name(entry: dict) -> str:
    """
    Extract the org/company name from a GlobeNewswire feed entry.

    GlobeNewswire entries typically have the issuing org name in:
    - entry.get("gnw_company") or entry.get("company") — structured field
    - The title, formatted as "[ORG NAME] Announces/Names/Appoints..."
    - The source/author field

    Falls back to the first capitalized phrase before a verb in the title.
    Returns empty string if extraction fails — entry is skipped.
    """
    # Structured company field (feedparser parses GNW namespace)
    for key in ("gnw_company", "company", "dc_creator", "author"):
        val = entry.get(key, "")
        if val and len(val) > 3:
            return val.strip()

    # Title parsing: "ORG NAME Announces..." → take words before first verb
    title = entry.get("title", "")
    if title:
        # Split on common announcement verbs
        for verb in [
            " Announces ", " Names ", " Appoints ", " Welcomes ",
            " Hires ", " Elects ", " Promotes ", " Named ",
        ]:
            if verb in title:
                candidate = title.split(verb)[0].strip()
                if 3 < len(candidate) < 120:
                    return candidate

        # Fallback: first sentence subject (before first comma or period)
        first = re.split(r'[,.]', title)[0].strip()
        if 3 < len(first) < 120:
            return first

    return ""


def _extract_domain(entry: dict) -> str:
    """Extract domain from the entry link or source URL."""
    link = entry.get("link", "")
    if link:
        # GlobeNewswire links: https://www.globenewswire.com/news-release/...
        # We want the issuer's domain if available, not GNW's own domain
        # Sometimes available in entry tags or source
        pass

    # Try source URL
    source = entry.get("source", {})
    if isinstance(source, dict):
        href = source.get("href", "")
        if href and "globenewswire" not in href:
            href = re.sub(r'^https?://(www\.)?', '', href).split('/')[0]
            return href.lower().strip()

    return ""  # domain often not available in GNW entries — fuzzy match on name


def _classify_signal(title: str, summary: str) -> str:
    """
    Classify the signal type based on title and summary keywords.
    Returns SIG code or UNKNOWN.
    """
    text = (title + " " + summary).lower()

    # SIG-008 — Merger (check first — merger entries mention leaders too)
    if any(kw in text for kw in MERGER_KEYWORDS):
        return "SIG-008"

    # SIG-003/SIG-004 — Campaign / Gift
    if any(kw in text for kw in CAMPAIGN_KEYWORDS):
        if "capital campaign" in text:
            return "SIG-003"
        return "SIG-004"

    # SIG-005 — Investment Committee / CIO
    if any(kw in text for kw in [
        "chief investment officer", "cio", "director of investments",
        "investment committee", "investment chair",
    ]):
        return "SIG-005"

    # SIG-001 — CFO / Finance Director
    if any(kw in text for kw in [
        "chief financial officer", "cfo", "finance director",
        "director of finance", "vp finance", "vice president finance",
        "vice president of finance",
    ]):
        return "SIG-001"

    # SIG-002 — CEO / Executive Director
    if any(kw in text for kw in [
        "chief executive officer", "ceo", "executive director",
        "president and ceo", "president & ceo", "president/ceo",
    ]):
        return "SIG-002"

    return "UNKNOWN"


def _is_nonprofit_entry(title: str, summary: str) -> bool:
    """
    Returns True if the entry contains a nonprofit-context keyword.
    Intentionally permissive — the fuzzy matcher handles false positives.
    Only hard-discards entries with zero nonprofit signal.
    """
    text = (title + " " + summary).lower()
    return any(kw in text for kw in NONPROFIT_KEYWORDS)


def _parse_published(entry: dict) -> Optional[datetime]:
    """Parse the published/updated timestamp to a timezone-aware datetime."""
    # feedparser normalizes published_parsed to a time.struct_time in UTC
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass

    # Fallback: parse published string directly
    raw = entry.get("published", "") or entry.get("updated", "")
    if raw:
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ]:
            try:
                return datetime.strptime(raw.strip(), fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    return None


# ── FEED FETCHER ──────────────────────────────────────────────────────────────

def _fetch_feed(
    feed_name: str,
    url: str,
    lookback_days: int,
    verbose: bool,
) -> tuple[list[RSSSignal], int, Optional[str]]:
    """
    Fetch and parse a single GlobeNewswire Atom feed.
    Returns (signals, entries_reviewed, error_or_None).
    """
    if verbose:
        print(f"[Layer A] Fetching: {feed_name}")

    try:
        feed = feedparser.parse(url)
    except Exception as e:
        return [], 0, f"feedparser error on {feed_name}: {e}"

    if feed.bozo and not feed.entries:
        err = str(feed.bozo_exception) if feed.bozo_exception else "unknown parse error"
        return [], 0, f"Feed parse failed ({feed_name}): {err}"

    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    signals: list[RSSSignal] = []
    entries_reviewed = 0

    for entry in feed.entries:
        entries_reviewed += 1

        # Date filter — discard outside lookback window
        published = _parse_published(entry)
        if published is None:
            continue  # skip undated entries
        if published < cutoff:
            continue  # outside lookback window

        title   = entry.get("title", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        link    = entry.get("link", "")

        # Nonprofit filter
        if not _is_nonprofit_entry(title, summary):
            continue

        # Org name extraction
        org_name = _extract_org_name(entry)
        if not org_name:
            continue  # can't match without org name

        domain      = _extract_domain(entry)
        signal_type = _classify_signal(title, summary)

        signals.append(RSSSignal(
            org_name=org_name,
            domain=domain,
            title=title,
            summary=summary[:500],
            published=published,
            url=link,
            feed_name=feed_name,
            signal_type=signal_type,
        ))

    if verbose:
        print(f"  Entries reviewed: {entries_reviewed}")
        print(f"  Signals found:    {len(signals)}")

    return signals, entries_reviewed, None


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def fetch_gnw_signals(
    lookback_days: int = 30,
    feeds: Optional[list[str]] = None,
    verbose: bool = True,
) -> RSSFeedResult:
    """
    Fetch GlobeNewswire RSS feeds and return nonprofit signals.

    Args:
        lookback_days:  Days to look back from today (default 30).
                        Entries older than this are discarded.
        feeds:          List of feed names to fetch. Defaults to all feeds.
                        Options: "directors_officers", "mergers_acquisitions"
        verbose:        Print progress to stdout (default True).

    Returns:
        RSSFeedResult with .to_signal_tuples() for match_batch() input.

    Usage in sweep (Phase 1, Layer A):
        from utilities.lark_rss import fetch_gnw_signals

        rss_result = fetch_gnw_signals(lookback_days=30)
        all_signals.extend(rss_result.to_signal_tuples())
        # Then continue with other channels before calling match_batch()

    Why 30 days even though the feed is live:
        Lark sweeps monthly. The RSS feed is date-ordered so even in
        a monthly sweep, setting lookback_days=30 ensures we catch
        everything from the past month without re-processing old entries.
        For a real-time setup, lower this to 7 or 1.
    """
    active_feeds = feeds or list(FEEDS.keys())
    result       = RSSFeedResult()
    t0           = time.time()

    for feed_name in active_feeds:
        if feed_name not in FEEDS:
            result.errors.append(f"Unknown feed name: {feed_name}")
            continue

        url = FEEDS[feed_name]
        signals, reviewed, error = _fetch_feed(
            feed_name, url, lookback_days, verbose
        )

        result.feeds_fetched    += 1
        result.entries_reviewed += reviewed
        result.entries_filtered += len(signals)
        result.signals.extend(signals)

        if error:
            result.errors.append(error)

        # Polite delay between feed fetches
        if len(active_feeds) > 1:
            time.sleep(1)

    result.fetch_duration_s = time.time() - t0

    if verbose:
        print(f"\n{result.summary()}")
        if result.signals:
            print("\n  Signals (in-window):")
            for sig in result.signals:
                print(f"    {sig.summary_line()}")

    return result


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Self-test: fetches both feeds, prints all signals within the past 30 days.
    No fuzzy matcher called. No Apify. No API key needed.

    Run from Lark/ directory:
        python utilities/lark_rss.py

    To test a different lookback window:
        python utilities/lark_rss.py --days 7
    """
    import sys

    days = 30
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except (IndexError, ValueError):
            pass

    print(f"\n🪶  lark_rss.py — self-test")
    print(f"   Feeds: Directors & Officers · Mergers & Acquisitions")
    print(f"   Lookback: {days} days\n")

    result = fetch_gnw_signals(lookback_days=days, verbose=True)

    if not result.signals:
        print(f"\n  No nonprofit signals found in past {days} days.")
        print(f"  This may mean:")
        print(f"    - No nonprofit press releases in this window (low volume is normal)")
        print(f"    - Feed returned entries outside the lookback window")
        print(f"    - Org name extraction failed on relevant entries")
        if result.errors:
            print(f"  Errors: {result.errors}")
    else:
        tuples = result.to_signal_tuples()
        print(f"\n  Signal tuples ready for match_batch():")
        for org, domain in tuples:
            print(f"    ({org!r}, {domain!r})")

    print(f"\n✓ lark_rss.py ready. Add to Phase 1 Layer A.\n")
