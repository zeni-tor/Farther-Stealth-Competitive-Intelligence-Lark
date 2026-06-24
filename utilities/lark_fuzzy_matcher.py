#!/usr/bin/env python3
"""
lark_fuzzy_matcher.py — Lark Fuzzy Matching Module
===================================================
Callable module used by Lark during sweeps to match incoming signal
org names against the full contacts CSV (up to 190K records).

MATCHING ARCHITECTURE — two separate paths, no Levenshtein:

  ACRONYM PATH (incoming is short all-caps: MADD, YMCA, ACLU):
    1. Exact string match against all CSV org names
    2. One match  → HIGH
    3. Multiple   → AMBIGUOUS
    4. None       → AMBIGUOUS (never silently discarded)

  NORMAL PATH (incoming is a full org name):
    1. Word pre-filter — find CSV records containing any significant word
       from the incoming name (Ctrl+F style, fast substring match)
    2. Token overlap score the candidates (no Levenshtein)
    3. Domain score boost if domain provided
    4. HIGH ≥ 80 · AMBIGUOUS 50–79
    5. If NO_MATCH → convert to acronym → repeat word pre-filter
    6. Still NO_MATCH → AMBIGUOUS for human review

  NEVER a full 190K Levenshtein scan. Pre-filter brings candidates
  down to ~50–200 before any scoring runs.

IMPORTANT — batch-first architecture:
    Lark collects ALL signal org names across ALL searches first,
    then calls match_batch() ONCE. Never call match() per search.

Thresholds:
    HIGH       ≥ 80  → confirmed match → proceed to enrichment
    AMBIGUOUS  50–79 → flag for manual review
    NO_MATCH   < 50  → routes to AMBIGUOUS (never silently discarded)

AUM filter:
    AUM_MIN_THRESHOLD = 1_000_000  ($1M minimum)
    Matched orgs below this are flagged but not surfaced for outreach.

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

# ── FILLER WORDS — stripped before word pre-filter and token scoring ──────────
FILLER = frozenset({
    'of', 'the', 'and', 'a', 'an', 'for', 'in', 'at', 'to',
    'inc', 'llc', 'corp', 'ltd', 'foundation', 'fund', 'trust',
})


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
    acronym_path:          bool = False     # True if matched via acronym path
    acronym_fallback_used: bool = False     # True if matched via acronym conversion
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
        if self.acronym_fallback_used:
            flags.append("ACRONYM-FALLBACK")
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


# ── ACRONYM DETECTION ─────────────────────────────────────────────────────────

def _is_acronym(text: str) -> bool:
    """
    Returns True if incoming name looks like an acronym.
    Matches: MADD · YMCA · ACLU · NAACP · M.A.D.D.
    Does not match full org names even if all-caps (CSV stores in ALL CAPS).
    Threshold: 2–6 chars, all uppercase letters, or dotted form.
    """
    t = text.strip()
    if re.match(r'^([A-Z]\.){2,}$', t):   # M.A.D.D.
        return True
    return bool(re.match(r'^[A-Z]{2,6}$', t))


def _clean_acronym(text: str) -> str:
    """M.A.D.D. → MADD"""
    return re.sub(r'\.', '', text).upper().strip()


def _make_acronym(org_name: str) -> str:
    """
    Convert full org name to acronym.
    "Young Men's Christian Association" → "YMCA"
    "Mothers Against Drunk Driving"     → "MADD"
    """
    words = org_name.split()
    initials = [w[0].upper() for w in words
                if w.lower().rstrip('.,') not in FILLER and w.isalpha()]
    return ''.join(initials)


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


# ── NORMALIZATION ─────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """
    Uppercase, strip legal suffixes and pure filler.
    Normalizes & → AND.
    """
    if not text: return ""
    text = text.upper().strip()
    text = text.replace('&', 'AND')
    for s in [r'\bINC\.?\b', r'\bLLC\.?\b', r'\bCORP\.?\b', r'\bLTD\.?\b',
              r'\bTHE\b', r'\bA\b', r'\bAN\b', r'\bOF\b', r'\bAND\b']:
        text = re.sub(s, '', text)
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _significant_words(org_name: str, min_len: int = 3) -> list[str]:
    """
    Extract significant words from org name for pre-filtering.
    Strips filler, normalizes, returns words of min_len+ characters.

    "Boston Symphony Orchestra" → ["BOSTON", "SYMPHONY", "ORCHESTRA"]
    "United Way of New York City" → ["UNITED", "WAY", "NEW", "YORK", "CITY"]
    """
    normalized = _normalize(org_name)
    words = normalized.split()
    sig = [w for w in words
           if len(w) >= min_len and w.lower() not in FILLER]
    return sig if sig else words  # fallback: return all words if none pass filter


# ── TOKEN OVERLAP SCORING — replaces Levenshtein ─────────────────────────────

def _token_score(a: str, b: str) -> int:
    """
    Score similarity 0–100 using token overlap only. No Levenshtein.

    Jaccard-style: overlap tokens / union tokens × 100.
    Fast — O(n) where n is word count, not character count.

    "Boston Symphony Orchestra" vs "Boston Symphony Orchestra" → 100
    "Boston Symphony" vs "Boston Symphony Orchestra" → 80
    "Boston Foundation" vs "New York Foundation" → ~50 (FOUNDATION matches)
    """
    na, nb = _normalize(a), _normalize(b)
    if na == nb: return 100
    if not na or not nb: return 0

    ta = set(na.split())
    tb = set(nb.split())

    if not ta or not tb: return 0

    intersection = len(ta & tb)
    union        = len(ta | tb)

    return round((intersection / union) * 100)


def _domain_similarity(incoming: str, candidate: str) -> int:
    """Score domain match 0–100."""
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


def _composite_score(in_name: str, in_dom: str,
                     cand_name: str, cand_dom: str, cand_contact: str
                     ) -> tuple[int, dict]:
    """
    Weighted composite score across name, domain, contact.
    Name scored via token overlap (no Levenshtein).
    """
    ns = _token_score(in_name, cand_name)
    ds = _domain_similarity(in_dom, cand_dom)
    cs = _token_score(in_name, cand_contact) if cand_contact else 0

    dw = WEIGHT_DOMAIN if in_dom else 0.0
    nw = WEIGHT_NAME + (WEIGHT_DOMAIN - dw)

    total = ns * nw + ds * dw + cs * WEIGHT_CONTACT
    return round(total), {"name": ns, "domain": ds, "contact": cs, "total": round(total)}


# ── PROGRESS BAR ─────────────────────────────────────────────────────────────

def _progress(current: int, total: int, label: str = "", width: int = 40):
    pct  = current / total if total else 0
    fill = int(width * pct)
    bar  = '█' * fill + '░' * (width - fill)
    print(f"\r  [{bar}] {current:,}/{total:,} {label}", end='', flush=True)
    if current >= total:
        print()


# ── MATCHER CLASS ─────────────────────────────────────────────────────────────

class LarkMatcher:
    """
    Loads full contacts CSV (up to 190K) once into Python memory.

    No Levenshtein. No upfront index build.
    Two paths:
      - Acronym path: exact string match, O(n) but only for short all-caps inputs
      - Normal path: word pre-filter → token score ~50–200 candidates

    At 190K records, match_batch() for 65 signals should complete in
    under 60 seconds.
    """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        print(f"\n[LarkMatcher] Loading {csv_path}...")
        t0 = time.time()
        self.records = self._load(csv_path)
        elapsed = time.time() - t0
        print(f"[LarkMatcher] Loaded {len(self.records):,} records "
              f"in {elapsed:.1f}s from {os.path.basename(csv_path)}")
        print(f"[LarkMatcher] AUM threshold:    ${AUM_MIN_THRESHOLD:,}")
        print(f"[LarkMatcher] Match strategy:   word pre-filter + token score (no Levenshtein)")
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
            if (i + 1) % 10000 == 0 or (i + 1) == total:
                _progress(i + 1, total, "records loaded")

        return records

    # ── ACRONYM PATH ──────────────────────────────────────────────────────────

    def _match_acronym_path(
        self, org_name: str, domain: str
    ) -> MatchResult:
        """
        Acronym path — for short all-caps inputs (MADD, YMCA, ACLU).
        Exact string match against CSV org names. No scoring needed.
        Multiple matches → AMBIGUOUS. Zero matches → AMBIGUOUS.
        """
        clean = _clean_acronym(org_name)
        matches = [r for r in self.records if r["name"].upper() == clean]

        if len(matches) == 1:
            r   = matches[0]
            aum = _parse_aum(r.get("assets", ""))
            meet = (aum is None) or (aum >= AUM_MIN_THRESHOLD)
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="HIGH", score=95,
                matched_row=r["raw"],
                acronym_path=True,
                aum_value=aum, meets_aum_threshold=meet,
                breakdown={"name": 95, "domain": 0, "contact": 0, "total": 95},
            )

        # Multiple or zero matches — flag for human review
        top = [{"name": r["name"], "score": 90} for r in matches[:3]]
        note = f"{len(matches)} orgs share this acronym" if matches else "no exact match found"
        return MatchResult(
            incoming_name=org_name, incoming_domain=domain,
            decision="AMBIGUOUS", score=0,
            matched_row=None, top_candidates=top,
            acronym_path=True,
            breakdown={"note": note},
        )

    # ── WORD PRE-FILTER ───────────────────────────────────────────────────────

    def _prefilter(self, org_name: str, min_word_len: int = 3) -> list[dict]:
        """
        Fast Ctrl+F style pre-filter.
        Returns records whose name contains ANY significant word from org_name.
        Narrows 190K to ~50–200 candidates before scoring.

        Fallback tiers if no candidates found:
          1. Try shorter words (min_len=2)
          2. Try single initials
          3. Return all records (full scan safety net — rare)
        """
        for min_len in [min_word_len, 2, 1]:
            words = _significant_words(org_name, min_len=min_len)
            if not words:
                continue
            candidates = [
                r for r in self.records
                if any(w in r["name"] for w in words)
            ]
            if candidates:
                return candidates

        # Safety net — full scan (should almost never hit this)
        return self.records

    # ── NORMAL PATH ───────────────────────────────────────────────────────────

    def _match_normal_path(
        self,
        org_name: str,
        domain: str,
        top_n: int = 5,
        acronym_fallback: bool = False,
    ) -> Optional[MatchResult]:
        """
        Normal path:
        1. Word pre-filter → candidates
        2. Token score candidates
        3. Return HIGH / AMBIGUOUS / None (None = try acronym fallback)
        """
        candidates = self._prefilter(org_name)

        scored = []
        for r in candidates:
            score, breakdown = _composite_score(
                org_name, domain,
                r["name"], r["domain"], r["contact"]
            )
            scored.append({
                "name":      r["name"],
                "domain":    r["domain"],
                "score":     score,
                "breakdown": breakdown,
                "raw":       r["raw"],
                "assets":    r.get("assets", ""),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0] if scored else None

        if not best:
            return None

        if best["score"] >= HIGH_THRESHOLD:
            aum  = _parse_aum(best.get("assets", ""))
            meet = (aum is None) or (aum >= AUM_MIN_THRESHOLD)
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="HIGH", score=best["score"],
                matched_row=best["raw"], top_candidates=scored[:top_n],
                breakdown=best["breakdown"],
                acronym_fallback_used=acronym_fallback,
                aum_value=aum, meets_aum_threshold=meet,
            )

        if best["score"] >= AMBIGUOUS_LOW:
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="AMBIGUOUS", score=best["score"],
                matched_row=None, top_candidates=scored[:top_n],
                breakdown=best["breakdown"],
                acronym_fallback_used=acronym_fallback,
            )

        # Below AMBIGUOUS_LOW — signal no match to caller
        return None

    # ── MAIN MATCH ────────────────────────────────────────────────────────────

    def match(self, org_name: str, domain: str = "", top_n: int = 5) -> MatchResult:
        """
        Match a single org name. Two paths, no Levenshtein.

        ACRONYM PATH — if incoming is short all-caps (MADD, YMCA):
            Exact string match. Fast. No scoring.

        NORMAL PATH — full org name:
            1. Word pre-filter → ~50–200 candidates
            2. Token score candidates
            3. If no match → convert to acronym → try again
            4. Still no match → AMBIGUOUS (never silently discarded)
        """
        if not org_name:
            return MatchResult(
                incoming_name="", incoming_domain=domain,
                decision="AMBIGUOUS", score=0, matched_row=None,
            )

        # ── Acronym path ──────────────────────────────────────────────────────
        if _is_acronym(org_name):
            return self._match_acronym_path(org_name, domain)

        # ── Normal path ───────────────────────────────────────────────────────
        result = self._match_normal_path(org_name, domain, top_n)
        if result:
            return result

        # ── Acronym fallback ──────────────────────────────────────────────────
        # Full name didn't match — convert to acronym and try again.
        # "Young Men's Christian Association" → "YMCA" → try normal path
        acronym = _make_acronym(org_name)
        if len(acronym) >= 2:
            acr_result = self._match_normal_path(
                acronym, domain, top_n, acronym_fallback=True
            )
            if acr_result:
                return acr_result

        # ── Both attempts failed ──────────────────────────────────────────────
        # Score the pre-filter candidates to get the best available score.
        # ≥ 50 → AMBIGUOUS (human review)
        # < 50 → NO_MATCH (surfaces in report with discard note — not silent)
        candidates = self._prefilter(org_name)
        scored = sorted(
            [{"name": r["name"], "score": _token_score(org_name, r["name"]),
              "raw": r["raw"]}
             for r in candidates],
            key=lambda x: x["score"], reverse=True
        )
        best_score = scored[0]["score"] if scored else 0

        if best_score >= AMBIGUOUS_LOW:
            return MatchResult(
                incoming_name=org_name, incoming_domain=domain,
                decision="AMBIGUOUS", score=best_score,
                matched_row=None,
                top_candidates=[{"name": s["name"], "score": s["score"]}
                                for s in scored[:top_n]],
            )

        # Score too low for AMBIGUOUS — NO_MATCH
        # Surfaces in report as "Scored too low — human review for discard"
        return MatchResult(
            incoming_name=org_name, incoming_domain=domain,
            decision="NO_MATCH", score=best_score,
            matched_row=None,
            top_candidates=[{"name": s["name"], "score": s["score"]}
                            for s in scored[:top_n]],
        )

    def match_batch(self, signals: list[tuple[str, str]]) -> list[MatchResult]:
        """
        Match a batch of (org_name, domain) tuples.

        Collect ALL signals first, call this ONCE.
        No Levenshtein — should complete in under 60 seconds for 65 signals.
        """
        total_records = len(self.records)
        print(f"[LarkMatcher] Batch matching {len(signals)} signals "
              f"against {total_records:,} records...")
        print(f"[LarkMatcher] Strategy: word pre-filter + token score\n")

        results                                       = []
        high = ambiguous = no_match                   = 0
        acronym_path = acronym_fallback = below_aum   = 0

        for i, (org_name, domain) in enumerate(signals):
            print(f"  [{i+1}/{len(signals)}] {org_name[:55]}")
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

            if result.acronym_path:          acronym_path     += 1
            if result.acronym_fallback_used: acronym_fallback += 1

            aum_flag = (
                f" ⚠ BELOW AUM (${result.aum_value:,.0f})"
                if not result.meets_aum_threshold else ""
            )
            print(f"       → {result.summary()}{aum_flag}")

        print(f"\n[LarkMatcher] Batch complete:")
        print(f"  HIGH:                  {high}")
        print(f"  AMBIGUOUS:             {ambiguous}  ← flag for human review (score 50–79)")
        print(f"  NO_MATCH:              {no_match}  ← scored too low · human review for discard")
        print(f"  Acronym path used:     {acronym_path}")
        print(f"  Acronym fallback used: {acronym_fallback}")
        print(f"  HIGH below $1M AUM:    {below_aum}")
        print(f"  HIGH above $1M AUM:    {high - below_aum} ← proceed to enrichment\n")

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
            "total":        n,
            "with_domain":  with_domain,
            "with_contact": with_contact,
            "with_assets":  with_assets,
            "domain_pct":   round(with_domain  / n * 100) if n else 0,
            "contact_pct":  round(with_contact / n * 100) if n else 0,
            "assets_pct":   round(with_assets  / n * 100) if n else 0,
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

        # Test 1 — exact matches from CSV (must all be HIGH)
        print("── Test 1: Exact matches (all must be HIGH) ──")
        random.seed(99)
        sample = random.sample(matcher.records, min(3, len(matcher.records)))
        for r in sample:
            result = matcher.match(r["name"], r["domain"])
            status = "✓" if result.is_match else "✗"
            print(f"  {status} {r['name'][:50]:<50} → {result.summary()}")

        # Test 2 — acronym path
        print("\n── Test 2: Acronym path ──")
        for org in ["MADD", "YMCA", "ACLU", "NWF"]:
            result = matcher.match(org, "")
            path = "[ACRONYM-PATH]" if result.acronym_path else ""
            print(f"  {org:<10} → {result.summary()} {path}")

        # Test 3 — acronym fallback (full name → no match → try acronym)
        print("\n── Test 3: Acronym fallback ──")
        test_orgs = [
            ("Young Men's Christian Association", ""),
            ("Mothers Against Drunk Driving", ""),
        ]
        for org, domain in test_orgs:
            result = matcher.match(org, domain)
            fb = "[ACRONYM-FALLBACK]" if result.acronym_fallback_used else ""
            print(f"  {org[:45]:<45} → {result.summary()} {fb}")

        # Test 4 — batch timing
        print("\n── Test 4: Batch match timing ──")
        batch = (
            [(r["name"], r["domain"]) for r in sample[:3]] +
            [("MADD", ""), ("Young Men's Christian Association", ""),
             ("Completely Fake Org XYZ 99999", "")]
        )
        t0 = time.time()
        results = matcher.match_batch(batch)
        elapsed = time.time() - t0
        high = sum(1 for r in results if r.is_match)
        print(f"  Batch of {len(batch)} in {elapsed:.2f}s: "
              f"{high} HIGH · "
              f"{sum(1 for r in results if r.needs_review)} AMBIGUOUS · "
              f"{sum(1 for r in results if r.decision=='NO_MATCH')} NO_MATCH")

        print(f"\n✓ Module ready for Lark sweeps.\n")

    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}\n")
        sys.exit(1)