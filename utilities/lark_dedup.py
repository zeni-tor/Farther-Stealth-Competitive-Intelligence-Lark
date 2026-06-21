#!/usr/bin/env python3
"""
lark_dedup.py — Lark Signal Deduplicator
=========================================
Deduplicates all_signals[] before match_batch() is called.

match_batch() does not deduplicate internally — this step is required.
Running the same org through the matcher twice wastes time at 190K records
and can produce duplicate findings in the report.

Deduplication key: org_name, case-insensitive and whitespace-stripped.
When duplicates exist, the first occurrence is kept. Domain from the first
occurrence is preserved — if a later occurrence has a domain and the first
doesn't, the first still wins (sources are consistent within a sweep).

USAGE:
    from utilities.lark_dedup import dedup_signals

    all_signals = dedup_signals(all_signals)  # always call before match_batch()
    results = matcher.match_batch(all_signals)

CALL ORDER — always:
    ALL channels run → all_signals[] collected → dedup_signals() → match_batch()

INPUT:
    List of (org_name, domain) tuples. Domain may be empty string.

OUTPUT:
    Deduplicated list of (org_name, domain) tuples, order preserved.

Self-test:
    python utilities/lark_dedup.py
"""

from typing import Optional


def dedup_signals(
    signals: list[tuple[str, str]],
    verbose: bool = False,
) -> list[tuple[str, str]]:
    """
    Deduplicate a list of (org_name, domain) signal tuples.

    Dedup key is org_name lowercased and stripped. First occurrence wins.
    Empty org names are dropped entirely — they cannot be matched.

    Args:
        signals: List of (org_name, domain) tuples from all channels combined.
        verbose: If True, prints count of duplicates removed.

    Returns:
        Deduplicated list, original order preserved.

    Example:
        signals = [
            ("Boston Foundation", "tbf.org"),
            ("Boston Foundation", ""),          # duplicate — dropped
            ("MADD", ""),
            ("", "orphan.org"),                 # blank org name — dropped
            ("Community Foundation", "cf.org"),
        ]
        dedup_signals(signals)
        # → [("Boston Foundation", "tbf.org"), ("MADD", ""), ("Community Foundation", "cf.org")]
    """
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    dropped_blank = 0
    dropped_dupe  = 0

    for org_name, domain in signals:
        # Drop blank org names — unfixable, matcher requires a name
        if not org_name or not org_name.strip():
            dropped_blank += 1
            continue

        key = org_name.lower().strip()

        if key in seen:
            dropped_dupe += 1
            continue

        seen.add(key)
        deduped.append((org_name, domain))

    if verbose:
        total_dropped = dropped_blank + dropped_dupe
        print(f"[dedup] {len(signals)} in → {len(deduped)} out "
              f"({dropped_dupe} duplicates · {dropped_blank} blank names dropped)")

    return deduped


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🪶  lark_dedup.py — self-test\n")

    test_cases = [
        # (description, input, expected_length, expected_first_name)
        (
            "Basic dedup — exact duplicate",
            [("Boston Foundation", "tbf.org"), ("Boston Foundation", "")],
            1, "Boston Foundation"
        ),
        (
            "Case-insensitive dedup",
            [("BOSTON FOUNDATION", "tbf.org"), ("Boston Foundation", "")],
            1, "BOSTON FOUNDATION"
        ),
        (
            "Whitespace normalization",
            [("Boston Foundation", "tbf.org"), ("Boston Foundation  ", "")],
            1, "Boston Foundation"
        ),
        (
            "Blank org name dropped",
            [("", "orphan.org"), ("Boston Foundation", "tbf.org")],
            1, "Boston Foundation"
        ),
        (
            "Order preserved — first occurrence wins",
            [
                ("Community Foundation", "cf1.org"),
                ("Boston Foundation", "tbf.org"),
                ("Community Foundation", "cf2.org"),  # duplicate
            ],
            2, "Community Foundation"
        ),
        (
            "Mixed channels — realistic sweep input",
            [
                ("Denver Foundation", "denverfoundation.org"),    # Ch1
                ("Candid", "candid.org"),                          # Ch1
                ("MADD", ""),                                      # Ch1
                ("Denver Foundation", "denverfoundation.org"),    # Ch2 duplicate
                ("Pittsburgh Foundation", "pittsburghfoundation.org"),  # Ch2
                ("Candid", ""),                                    # Ch3 duplicate
                ("", "noop.org"),                                  # blank — drop
                ("YMCA of Metropolitan Chicago", "ymcachicago.org"),
            ],
            5, "Denver Foundation"
        ),
    ]

    all_passed = True
    for desc, signals, expected_len, expected_first in test_cases:
        result = dedup_signals(signals, verbose=False)
        passed = (len(result) == expected_len and
                  (not result or result[0][0] == expected_first))
        status = "✓" if passed else "✗"
        if not passed:
            all_passed = False
        print(f"  {status} {desc}")
        if not passed:
            print(f"    Expected: len={expected_len}, first='{expected_first}'")
            print(f"    Got:      len={len(result)}, first='{result[0][0] if result else 'EMPTY'}'")

    print()

    # Verbose output test
    print("  Verbose output example:")
    sample = [
        ("Boston Foundation", "tbf.org"),
        ("Boston Foundation", ""),
        ("MADD", ""),
        ("", "blank.org"),
        ("Denver Foundation", "denverfoundation.org"),
    ]
    dedup_signals(sample, verbose=True)

    print()
    if all_passed:
        print("✓ lark_dedup.py self-test passed.\n")
    else:
        print("✗ lark_dedup.py self-test FAILED — check output above.\n")
        raise SystemExit(1)
