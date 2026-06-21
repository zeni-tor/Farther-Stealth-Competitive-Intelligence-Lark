#!/usr/bin/env python3
"""
lark_fuzzy_matcher.py — Lark Fuzzy Matching Module
===================================================
Callable module used by Lark during sweeps to match incoming signal
org names against the full contacts CSV (up to 100K records).

IMPORTANT — batch-first architecture:
    Lark collects ALL signal org names across ALL searches first,
    then calls match_batch() ONCE. Never call match() per search.

    # Correct usage:
    matcher = LarkMatcher("contact_data/contacts.csv")

    # PHASE 1 — collect all signals during searches
    all_signals = [
        ("Boston Foundation", "tbf.org"),
        ("MADD", ""),
        ("United Way NYC", ""),
    ]

    # PHASE 2 — batch match once after all searches complete
    results = matcher.match_batch(all_signals)

    # PHASE 3 — enrich HIGH matches above AUM threshold only
    for r in results:
        if r.is_match and r.meets_aum_threshold:
            enrich(r.matched_row)

Thresholds (validated 2026-06-16 against real data):
    HIGH       ≥ 80  → auto-match, proceed to enrichment
    AMBIGUOUS  50–79 → flag for manual review
    NO_MATCH   < 50  → discard

AUM filter:
    AUM_MIN_THRESHOLD = 1_000_000  ($1M minimum)
    Matched orgs below this are flagged but not surfaced for outreach.

Abbreviation handling:
    Short all-caps inputs (≤6 chars) detected as abbreviations.
    Acronym index built at load time — O(1) lookup per signal.
    No match found → AMBIGUOUS (never silently discarded).

Scale:
    Designed for up to 100K records.
    All matching runs in Python memory — never in Claude context.
    At 100K records, match_batch() takes ~3–5 min for 14 signals.
    Progress bar prints during load and matching.

Column names (from contacts CSV):
    COL_NAME    = "Org Name"
    COL_DOMAIN  = "Web Address"
    COL_CONTACT = "Principal Officer"
    COL_ASSETS  = "Total Assets"
"""

import csv
import re
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

# ── THRESHOLDS ────────────────────────────────────────────────────────────────
HIGH_THRESHOLD    = 80
AMBIGUOUS_LOW     = 50
AUM_MIN_THRESHOLD = 1_000_000   # $1M

# ── WEIGHTS ───────────────────────────────────────────────────────────────────
WEIGHT_NAME    = 0.60
WEIGHT_DOMAIN  = 0.25
WEIGHT_CONTACT = 0.15

# ── CSV COLUMN NAMES ──────────────────────────────────────────────────────────
COL_NAME    = "Org Name"
COL_DOMAIN  = "Web Address"
COL_CONTACT = "Principal Officer"
COL_ASSETS  = "Total Assets"


# ── RESULT DATACLASS ──────────────────────────────────────────────────────────

@dataclass
class MatchResult:
    """Result of a single fuzzy match attempt."""
    incoming_name:         str
    incoming_domain:       str
    decision:              str              # HIGH / AMBIGUOUS / NO_MATCH
    score:                 int              # composite score 0–100
    matched_row:           Optional[dict]   # full CSV row if HIGH
    top_candidates:        list = field(default_factory=list)
    breakdown:             Optional[dict] = None
    abbreviation_detected: bool = False
    acronym_match:         bool = False
    aum_value:             Optional[float] = None
    meets_aum_threshold:   bool = True

    @property
    def is_match(self) -> bool:
        return self.decision == "HIGH"

    @property
    def needs_review(self) -> bool:
        return self.decision == "AMBIGUOUS"

    def summary(self) -> str:
        flags = []
        if self.abbreviation_detected:
            flags.append("ABBREV")
        if self.acronym_match:
            flags.append("ACRONYM")
        if not self.meets_aum_threshold:
            flags.append(
                f"BELOW AUM ${self.aum_value:,.0f}"
                if self.aum_value else "BELOW AUM"
            )
        flag_str = f" [{', '.join(flags)}]" if flags else ""

        if self.decision == "HIGH":
            name = self.matched_row.get(COL_NAME, "?") if self.matched_row else "?"
            return f"HIGH ({self.score}) → {name}{flag_str}"
        elif self.decision == "AMBIGUOUS":
            top = self.top_candidates[0]["name"] if self.top_candidates else "?"
            return f"AMBIGUOUS ({self.score}) → best: {top}{flag_str}"
        else:
            return f"NO_MATCH ({self.score}){flag_str}"


# ── ABBREVIATION DETECTION ────────────────────────────────────────────────────

# Explicitly known 5–6 char nonprofit acronyms that the vowel heuristic
# below would misclassify. Add to this list as new cases surface in sweeps.
_KNOWN_ACRONYMS_5_6: frozenset = frozenset({
    'NAACP', 'ASPCA', 'PFLAG', 'UNICEF', 'UNHCR', 'AIPAC',
})

_VOWELS = frozenset('AEIOU')


def _vowel_run_count(text: str) -> int:
    """Count separated vowel groups — a rough proxy for syllable count.

    Real English words tend to have 2+ separated vowel groups (CANDID → A,I).
    Acronyms tend to have 0–1 (YMCA → A only; NAACP → AA together = 1 run).
    """
    runs, in_vowel = 0, False
    for c in text.upper():
        if c in _VOWELS:
            if not in_vowel:
                runs += 1
                in_vowel = True
        else:
            in_vowel = False
    return runs


def _is_abbreviation(text: str) -> bool:
    """
    Detect if incoming org name looks like an abbreviation or acronym.

    Tiers:
    1. Dotted form (M.A.D.D.) — always abbreviation.
    2. 2–4 all-caps chars (YMCA, MADD, ACLU) — always abbreviation.
    3. 5–6 all-caps chars — check known nonprofit acronym list first,
       then fall back to vowel heuristic: 1 vowel run → acronym,
       2+ vowel runs → real word, not an abbreviation.

    Known edge case: vowel digraphs (FAITH → AI = 1 run) are
    misclassified as acronyms. Acceptable — 5-char bare ALL CAPS
    signals are vanishingly rare in practice (press releases use
    title case full names, not bare acronyms).
    """
    t = text.strip()
    if re.match(r'^([A-Z]\.){2,}$', t):      # M.A.D.D.
        return True
    if not re.match(r'^[A-Z]{2,6}$', t):     # must be 2–6 all-caps letters
        return False
    if len(t) <= 4:                           # YMCA · MADD · ACLU · AARP
        return True
    if t in _KNOWN_ACRONYMS_5_6:             # NAACP · ASPCA · PFLAG
        return True
    return _vowel_run_count(t) < 2           # CANDID=2 runs → word; NAACP=1 → acronym


def _make_acronym(org_name: str) -> str:
    """
    Generate acronym from org name.
    "Mothers Against Drunk Driving" → "MADD"
    "United Way of New York City"   → "UWNYC"
    """
    filler = {'of', 'the', 'and', 'a', 'an', 'for', 'in', 'at', 'to',
              'inc', 'llc', 'corp', 'ltd', 'foundation', 'fund', 'trust'}
    words = org_name.split()
    initials = [w[0].upper() for w in words
                if w.lower().rstrip('.,') not in filler and w.isalpha()]
    return ''.join(initials)


def _clean_acronym(text: str) -> str:
    """Normalize acronym for lookup. M.A.D.D. → MADD"""
    return re.sub(r'\.', '', text).upper().strip()


# ── AUM PARSING ───────────────────────────────────────────────────────────────

def _parse_aum(raw: str) -> Optional[float]:
    """
    Parse Total Assets to float.
    Handles: "1,234,567" / "$1.2M" / "1200000" / "" / "N/A"
    """
    if not raw or raw.strip().lower() in ('', 'n/a', 'none', '-', '—'):
        return None
    try:
        cleaned = re.sub(r'[$,\s]', '', raw.strip())
        if cleaned.upper().endswith('M'):
            return float(cleaned[:-1]) * 1_000_000
        if cleaned.upper().endswith('K'):
            return float(cleaned[:-1]) * 1_000
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


# ── FUZZY MATCHING FUNCTIONS ──────────────────────────────────────────────────

def _levenshtein(s1: str, s2: str) -> int:
    s1, s2 = s1.strip(), s2.strip()    # inputs already uppercase from _normalize
    if s1 == s2: return 0
    if not s1: return len(s2)
    if not s2: return len(s1)
    rows, cols = len(s1) + 1, len(s2) + 1
    dist = [[0] * cols for _ in range(rows)]
    for i in range(rows): dist[i][0] = i
    for j in range(cols): dist[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dist[i][j] = min(
                dist[i-1][j] + 1,
                dist[i][j-1] + 1,
                dist[i-1][j-1] + cost
            )
    return dist[-1][-1]


def _normalize(text: str) -> str:
    """
    Uppercase and strip noise tokens before scoring.

    Converts the incoming signal name to uppercase so it matches the CSV,
    which is already stored in ALL CAPS (IRS/NTEE format). This is simpler
    than lowercasing the CSV to meet the signal — the data is already there.

    Strips only legal suffixes and pure filler — words that carry zero
    identity information. Keeps all meaningful words (FOUNDATION, NATIONAL,
    AMERICAN, COMMUNITY, etc.) so similar-sector orgs with different names
    are correctly distinguished.

    Normalises ampersand to AND so 'Boys & Girls' and 'Boys and Girls'
    score identically.
    """
    if not text: return ""
    text = text.upper().strip()
    text = text.replace('&', 'AND')                          # & → AND
    for s in [r'\bINC\.?\b', r'\bLLC\.?\b', r'\bCORP\.?\b', r'\bLTD\.?\b',
              r'\bTHE\b', r'\bA\b', r'\bAN\b', r'\bOF\b', r'\bAND\b']:
        text = re.sub(s, '', text)
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _name_similarity(a: str, b: str) -> int:
    if not a or not b: return 0
    na, nb = _normalize(a), _normalize(b)
    if na == nb: return 100
    ta, tb = set(na.split()), set(nb.split())
    token = (len(ta & tb) * 2 / (len(ta) + len(tb))) * 100 if ta and tb else 0
    ml = max(len(na), len(nb))
    edit = max(0, 100 - (_levenshtein(na, nb) / ml * 100)) if ml else 100
    return round(token * 0.6 + edit * 0.4)


def _domain_similarity(incoming: str, candidate: str) -> int:
    if not incoming or not candidate: return 0
    def clean(d):
        d = d.lower().strip()
        d = re.sub(r'^https?://', '', d)
        d = re.sub(r'^www\.', '', d)
        return d.split('/')[0]
    ci, cc = clean(incoming), clean(candidate)
    if ci == cc: return 100
    if ci.rsplit('.', 1)[0] == cc.rsplit('.', 1)[0]: return 60
    return 0


def _composite_score(in_name, in_dom, cand_name, cand_dom, cand_contact):
    ns = _name_similarity(in_name, cand_name)
    ds = _domain_similarity(in_dom, cand_dom)
    cs = _name_similarity(in_name, cand_contact) if cand_contact else 0
    dw = WEIGHT_DOMAIN if in_dom else 0.0
    nw = WEIGHT_NAME + (WEIGHT_DOMAIN - dw)
    total = ns * nw + ds * dw + cs * WEIGHT_CONTACT
    return round(total), {"name": ns, "domain": ds, "contact": cs, "total": round(total)}


# ── PROGRESS BAR ─────────────────────────────────────────────────────────────

def _progress(current: int, total: int, label: str = "", width: int = 40):
    """Print an inline progress bar."""
    pct  = current / total if total else 0
    fill = int(width * pct)
    bar  = '█' * fill + '░' * (width - fill)
    print(f"\r  [{bar}] {current:,}/{total:,} {label}", end='', flush=True)
    if current >= total:
        print()


# ── MATCHER CLASS ─────────────────────────────────────────────────────────────

class LarkMatcher:
    """
    Loads full contacts CSV (up to 100K) once into Python memory.
    Provides batch fuzzy matching with abbreviation detection,
    acronym expansion, and AUM filtering.

    The CSV never enters Claude's context — only matched rows surface.
    Always use match_batch() — never call match() per search result.
    """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        print(f"\n[LarkMatcher] Loading {csv_path}...")
        t0 = time.time()
        self.records = self._load(csv_path)
        elapsed = time.time() - t0
        print(f"[LarkMatcher] Loaded {len(self.records):,} records "
              f"in {elapsed:.1f}s from {os.path.basename(csv_path)}")
        print(f"[LarkMatcher] Building acronym index...")
        self._acronym_index = self._build_acronym_index()
        print(f"[LarkMatcher] Acronym index: {len(self._acronym_index):,} entries")
        print(f"[LarkMatcher] AUM threshold: ${AUM_MIN_THRESHOLD:,}")
        print(f"[LarkMatcher] Ready.\n")

    def _load(self, path: str) -> list[dict]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Contacts CSV not found: '{path}'\n"
                f"Expected at: {os.path.abspath(path)}"
            )
        records = []
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for col in [COL_NAME, COL_DOMAIN, COL_CONTACT, COL_ASSETS]:
                if col and col not in headers:
                    print(f"  WARNING: Column '{col}' not found. "
                          f"Available: {', '.join(headers)}")
            # Count rows for progress bar
            rows = list(reader)

        total = len(rows)
        for i, row in enumerate(rows):
            name = row.get(COL_NAME, "").strip()
            if name:
                records.append({
                    "name":    name,
                    "domain":  row.get(COL_DOMAIN, "").strip(),
                    "contact": row.get(COL_CONTACT, "").strip(),
                    "assets":  row.get(COL_ASSETS, "").strip(),
                    "raw":     dict(row),
                })
            if (i + 1) % 5000 == 0 or (i + 1) == total:
                _progress(i + 1, total, "records loaded")

        return records

    def _build_acronym_index(self) -> dict[str, list[dict]]:
        """Pre-compute acronyms for all records. O(n) at load, O(1) at match."""
        index: dict[str, list[dict]] = {}
        total = len(self.records)
        for i, r in enumerate(self.records):
            acr = _make_acronym(r["name"])
            if len(acr) >= 2:
                if acr not in index:
                    index[acr] = []
                index[acr].append(r)
            if (i + 1) % 5000 == 0 or (i + 1) == total:
                _progress(i + 1, total, "acronyms indexed")
        return index

    def _check_abbreviation(self, org_name: str):
        """Returns (is_abbrev, acronym_matched, matched_record_or_None)"""
        if not _is_abbreviation(org_name):
            return False, False, None
        clean = _clean_acronym(org_name)
        matches = self._acronym_index.get(clean, [])
        if len(matches) == 1:
            return True, True, matches[0]
        elif len(matches) > 1:
            return True, True, None    # ambiguous — multiple orgs share acronym
        else:
            return True, False, None   # abbreviation, no match found

    def match(self, org_name: str, domain: str = "", top_n: int = 5) -> MatchResult:
        """
        Match a single org name. For sweep usage always prefer match_batch().
        """
        if not org_name:
            return MatchResult(
                incoming_name="", incoming_domain=domain,
                decision="NO_MATCH", score=0, matched_row=None,
            )

        # Step 1 — abbreviation check (O(1) via acronym index)
        is_abbrev, acronym_hit, acronym_record = self._check_abbreviation(org_name)
        if is_abbrev:
            if acronym_record:
                aum  = _parse_aum(acronym_record.get("assets", ""))
                meet = (aum is None) or (aum >= AUM_MIN_THRESHOLD)
                return MatchResult(
                    incoming_name=org_name, incoming_domain=domain,
                    decision="HIGH", score=95,
                    matched_row=acronym_record["raw"],
                    abbreviation_detected=True, acronym_match=True,
                    aum_value=aum, meets_aum_threshold=meet,
                    breakdown={"name":95,"domain":0,"contact":0,"total":95},
                )
            else:
                # Abbreviation + no match → always AMBIGUOUS, never discard
                return MatchResult(
                    incoming_name=org_name, incoming_domain=domain,
                    decision="AMBIGUOUS", score=0, matched_row=None,
                    abbreviation_detected=True, acronym_match=False,
                )

        # Step 2 — full fuzzy scoring
        scored = []
        for r in self.records:
            score, breakdown = _composite_score(
                org_name, domain,
                r["name"], r["domain"], r["contact"]
            )
            scored.append({
                "name": r["name"], "domain": r["domain"],
                "score": score, "breakdown": breakdown,
                "raw": r["raw"], "assets": r.get("assets", ""),
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0] if scored else None

        if not best:
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="NO_MATCH", score=0, matched_row=None,
            )

        if best["score"] >= HIGH_THRESHOLD:
            aum  = _parse_aum(best.get("assets", ""))
            meet = (aum is None) or (aum >= AUM_MIN_THRESHOLD)
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="HIGH", score=best["score"],
                matched_row=best["raw"], top_candidates=scored[:top_n],
                breakdown=best["breakdown"],
                aum_value=aum, meets_aum_threshold=meet,
            )
        elif best["score"] >= AMBIGUOUS_LOW:
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="AMBIGUOUS", score=best["score"],
                matched_row=None, top_candidates=scored[:top_n],
                breakdown=best["breakdown"],
            )
        else:
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="NO_MATCH", score=best["score"],
                matched_row=None, top_candidates=scored[:top_n],
                breakdown=best["breakdown"],
            )

    def match_batch(self, signals: list[tuple[str, str]]) -> list[MatchResult]:
        """
        Match a batch of (org_name, domain) tuples.

        THIS IS THE CORRECT WAY TO USE LARK MATCHER.
        Collect ALL signal org names across ALL searches first.
        Then call this ONCE after all searches complete.
        Never call match() per individual search result.

        At 100K records: ~3–5 minutes for a typical 14-signal batch.
        Progress prints during matching so you know it's running.
        """
        total_records = len(self.records)
        print(f"[LarkMatcher] Batch matching {len(signals)} signals "
              f"against {total_records:,} records...")
        if total_records > 10_000:
            print(f"[LarkMatcher] Large dataset — "
                  f"estimated {len(signals) * total_records / 500_000:.1f} min\n")

        results   = []
        high = ambiguous = no_match = abbrevs = below_aum = 0

        for i, (org_name, domain) in enumerate(signals):
            print(f"  [{i+1}/{len(signals)}] Matching: {org_name[:50]}")
            result = self.match(org_name, domain)
            results.append(result)

            if result.decision == "HIGH":
                high += 1
                if not result.meets_aum_threshold:
                    below_aum += 1
            elif result.decision == "AMBIGUOUS":
                ambiguous += 1
            else:
                no_match += 1
            if result.abbreviation_detected:
                abbrevs += 1

            aum_flag = (
                f" ⚠ BELOW AUM (${result.aum_value:,.0f})"
                if not result.meets_aum_threshold else ""
            )
            print(f"       → {result.summary()}{aum_flag}")

        print(f"\n[LarkMatcher] Batch complete:")
        print(f"  HIGH: {high} · AMBIGUOUS: {ambiguous} · NO_MATCH: {no_match}")
        print(f"  Abbreviations detected: {abbrevs}")
        print(f"  HIGH matches below $1M AUM: {below_aum}")
        print(f"  HIGH matches above $1M AUM: {high - below_aum} "
              f"← proceed to enrichment\n")

        return results

    @property
    def record_count(self) -> int:
        return len(self.records)

    def stats(self) -> dict:
        with_domain  = sum(1 for r in self.records if r["domain"])
        with_contact = sum(1 for r in self.records if r["contact"])
        with_assets  = sum(1 for r in self.records if r.get("assets"))
        n = len(self.records)
        return {
            "total":       n,
            "with_domain": with_domain,
            "with_contact":with_contact,
            "with_assets": with_assets,
            "domain_pct":  round(with_domain  / n * 100) if n else 0,
            "contact_pct": round(with_contact / n * 100) if n else 0,
            "assets_pct":  round(with_assets  / n * 100) if n else 0,
        }


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import random

    csv_path = sys.argv[1] if len(sys.argv) > 1 \
               else "contact_data/contacts.csv"

    print(f"\n🪶  LarkMatcher — self-test")
    print(f"   CSV: {csv_path}")

    try:
        matcher = LarkMatcher(csv_path)
        stats   = matcher.stats()
        print(f"  Records:      {stats['total']:,}")
        print(f"  With domain:  {stats['with_domain']:,} ({stats['domain_pct']}%)")
        print(f"  With contact: {stats['with_contact']:,} ({stats['contact_pct']}%)")
        print(f"  With assets:  {stats['with_assets']:,} ({stats['assets_pct']}%)")
        print(f"  AUM threshold: ${AUM_MIN_THRESHOLD:,}\n")

        # Test 1 — exact matches
        print("── Test 1: Exact matches (all must be HIGH) ──")
        random.seed(99)
        sample = random.sample(matcher.records, min(3, len(matcher.records)))
        for r in sample:
            result = matcher.match(r["name"], r["domain"])
            status = "✓" if result.is_match else "✗"
            print(f"  {status} {r['name'][:50]:<50} → {result.summary()}")

        # Test 2 — abbreviation detection
        print("\n── Test 2: Abbreviation handling ──")
        for org in ["MADD", "YMCA", "MDA", "NWF", "UWNYC"]:
            result = matcher.match(org, "")
            flags  = "ABBREV" if result.abbreviation_detected else ""
            if result.acronym_match: flags += " ACRONYM-MATCH"
            print(f"  {org:<10} → {result.summary():<40} {flags}")

        # Test 3 — batch
        print("\n── Test 3: Batch matching ──")
        batch = [(r["name"], r["domain"]) for r in sample[:2]] + \
                [("MADD", ""), ("YMCA", ""), ("Completely Fake Org", "")]
        results = matcher.match_batch(batch)
        high = sum(1 for r in results if r.is_match)
        print(f"  Batch of {len(batch)}: {high} HIGH · "
              f"{sum(1 for r in results if r.needs_review)} AMBIGUOUS · "
              f"{sum(1 for r in results if r.decision=='NO_MATCH')} NO_MATCH")

        print(f"\n✓ Module ready for Lark sweeps.\n")

    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}\n")
        sys.exit(1)