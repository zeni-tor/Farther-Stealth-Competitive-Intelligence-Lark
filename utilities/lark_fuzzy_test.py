#!/usr/bin/env python3
"""
Lark Fuzzy Matcher — Local Test Script
=======================================
Tests the fuzzy matching logic against a real HubSpot CSV export
before deploying to HubSpot's custom coded action environment.

Usage:
    python lark_fuzzy_test.py

Requirements:
    Python 3.8+ · No external libraries needed · pure standard library

How to run:
    1. Export your HubSpot companies to CSV:
       HubSpot → Companies → Export → select columns below
    2. Place the CSV in the same folder as this script
    3. Set CSV_FILE below to match your filename
    4. Edit INCOMING_SIGNALS with the org names you want to test
    5. Run: python lark_fuzzy_test.py
    6. Review output in the terminal and in results_YYYY-MM-DD.csv
"""

import csv
import re
import os
import sys
from datetime import date


# ── CONFIGURATION ─────────────────────────────────────────────────────────────

# Path to your HubSpot CSV export
# Place the CSV in the same folder as this script, or use a full path
CSV_FILE = "hubspot_export.csv"

# Column names in your HubSpot CSV export
# Adjust these to match your actual column headers exactly
COL_COMPANY_NAME = "Company name"       # required
COL_DOMAIN       = "Company Domain Name" # optional — leave blank if not in CSV
COL_CONTACT_NAME = "Associated Contact" # optional — leave blank if not in CSV

# Incoming signal org names to test
# These simulate what Lark would receive from a press release or LinkedIn post
# Add as many as you want — one per line
INCOMING_SIGNALS = [
    # Format: ("org name from signal", "domain from signal or blank")
    ("Hawaii Community Foundation", "hcf.org"),
    ("Boston Foundation", "tbf.org"),
    ("Chicago Community Trust", ""),
    ("New York Community Trust", "nyct.org"),
    ("Denver Art Museum Foundation", ""),
    ("University of Hawaii Foundation", "uhfoundation.org"),
    ("Silicon Valley Community Foundation", "siliconvalleycf.org"),
    # Add your own test cases here:
    # ("Org name as it appeared in the signal", "domain or blank"),
]

# Confidence thresholds — must match hubspot-fuzzy-matcher.md
HIGH_THRESHOLD = 80    # Score >= 80 → HIGH match
AMBIGUOUS_LOW  = 50    # Score 50–79 → AMBIGUOUS
                       # Score < 50  → NO MATCH

# Matching surface weights — must match hubspot-fuzzy-matcher.md
WEIGHT_NAME    = 0.60
WEIGHT_DOMAIN  = 0.25
WEIGHT_CONTACT = 0.15

# How many top candidates to show in results (doesn't affect scoring)
TOP_N = 5


# ── FUZZY MATCHING FUNCTIONS ──────────────────────────────────────────────────
# Identical to the HubSpot custom coded action — pure standard library only.

def levenshtein(s1, s2):
    """Calculate edit distance between two strings."""
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    rows = len(s1) + 1
    cols = len(s2) + 1
    dist = [[0] * cols for _ in range(rows)]

    for i in range(rows):
        dist[i][0] = i
    for j in range(cols):
        dist[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dist[i][j] = min(
                dist[i - 1][j] + 1,
                dist[i][j - 1] + 1,
                dist[i - 1][j - 1] + cost
            )
    return dist[-1][-1]


def normalize(text):
    """
    Normalize org name for comparison.
    Strips legal suffixes, punctuation, and common filler words.
    'Hawaii Community Foundation, Inc.' → 'hawaii community'
    """
    if not text:
        return ""
    text = text.lower().strip()
    suffixes = [
        r'\binc\.?\b', r'\bllc\.?\b', r'\bcorp\.?\b', r'\bltd\.?\b',
        r'\bfoundation\b', r'\bfund\b', r'\btrust\b', r'\bassociation\b',
        r'\bsociety\b', r'\borganization\b', r'\borganisation\b',
        r'\bcharity\b', r'\bcharitable\b', r'\bthe\b', r'\bof\b',
        r'\bcommunity\b', r'\bnational\b', r'\bamerican\b',
    ]
    for s in suffixes:
        text = re.sub(s, '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def similarity_score(a, b):
    """
    Return similarity 0–100 between two strings.
    Combines token overlap and edit distance.
    """
    if not a or not b:
        return 0

    na, nb = normalize(a), normalize(b)

    if na == nb:
        return 100

    # Token overlap
    tokens_a = set(na.split())
    tokens_b = set(nb.split())
    if tokens_a and tokens_b:
        overlap = len(tokens_a & tokens_b)
        token_score = (overlap * 2 / (len(tokens_a) + len(tokens_b))) * 100
    else:
        token_score = 0

    # Edit distance
    max_len = max(len(na), len(nb))
    if max_len == 0:
        edit_score = 100
    else:
        edit_score = max(0, 100 - (levenshtein(na, nb) / max_len * 100))

    return round(token_score * 0.6 + edit_score * 0.4)


def domain_score(incoming, candidate):
    """
    Score domain match 0–100.
    Exact match after stripping www = 100.
    Same root (different TLD) = 60.
    Either missing = 0 (neutral).
    """
    if not incoming or not candidate:
        return 0

    def clean(d):
        d = d.lower().strip()
        d = re.sub(r'^https?://', '', d)
        d = re.sub(r'^www\.', '', d)
        return d.split('/')[0]

    ci = clean(incoming)
    cc = clean(candidate)

    if ci == cc:
        return 100

    ri = ci.rsplit('.', 1)[0]
    rc = cc.rsplit('.', 1)[0]
    if ri == rc:
        return 60

    return 0


def composite_score(incoming_name, incoming_domain,
                    candidate_name, candidate_domain, candidate_contact):
    """
    Compute weighted composite score across three surfaces.
    Returns (score 0–100, breakdown dict).
    """
    name_s    = similarity_score(incoming_name, candidate_name)
    domain_s  = domain_score(incoming_domain, candidate_domain)
    contact_s = similarity_score(incoming_name, candidate_contact) \
                if candidate_contact else 0

    dw = WEIGHT_DOMAIN if incoming_domain else 0.0
    nw = WEIGHT_NAME + (WEIGHT_DOMAIN - dw)

    total = name_s * nw + domain_s * dw + contact_s * WEIGHT_CONTACT

    return round(total), {
        "name":    name_s,
        "domain":  domain_s,
        "contact": contact_s,
        "total":   round(total),
    }


def route(score):
    """Return routing decision string based on score."""
    if score >= HIGH_THRESHOLD:
        return "HIGH"
    elif score >= AMBIGUOUS_LOW:
        return "AMBIGUOUS"
    else:
        return "NO MATCH"


# ── CSV LOADER ────────────────────────────────────────────────────────────────

def load_csv(filepath):
    """
    Load HubSpot CSV export into a list of dicts.
    Handles common HubSpot CSV quirks (BOM, quoted fields, etc.)
    """
    records = []

    if not os.path.exists(filepath):
        print(f"\n  ERROR: CSV file not found: '{filepath}'")
        print(f"  Place your HubSpot export in the same folder as this script")
        print(f"  and update CSV_FILE at the top of the script.\n")
        sys.exit(1)

    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Warn about missing expected columns
        for col, label in [
            (COL_COMPANY_NAME, "Company name"),
            (COL_DOMAIN,       "Domain"),
            (COL_CONTACT_NAME, "Contact name"),
        ]:
            if col and col not in (headers or []):
                print(f"  WARNING: Column '{col}' not found in CSV.")
                print(f"  Available columns: {', '.join(headers or [])}")
                print(f"  Update the COL_* settings at the top of this script.\n")

        for row in reader:
            records.append({
                "name":    row.get(COL_COMPANY_NAME, "").strip(),
                "domain":  row.get(COL_DOMAIN, "").strip()  if COL_DOMAIN  else "",
                "contact": row.get(COL_CONTACT_NAME, "").strip() if COL_CONTACT_NAME else "",
            })

    # Filter out blank names
    records = [r for r in records if r["name"]]
    return records


# ── RESULTS DISPLAY ───────────────────────────────────────────────────────────

COLORS = {
    "HIGH":      "\033[92m",  # green
    "AMBIGUOUS": "\033[93m",  # yellow
    "NO MATCH":  "\033[91m",  # red
    "RESET":     "\033[0m",
    "BOLD":      "\033[1m",
    "DIM":       "\033[2m",
}

def color(text, key):
    """Wrap text in ANSI color codes."""
    return f"{COLORS.get(key, '')}{text}{COLORS['RESET']}"


def print_result(incoming_name, incoming_domain, candidates, top_n):
    """Print formatted match results for one incoming signal."""

    scored = []
    for c in candidates:
        score, breakdown = composite_score(
            incoming_name, incoming_domain,
            c["name"], c["domain"], c["contact"]
        )
        scored.append({**c, "score": score, "breakdown": breakdown})

    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0] if scored else None

    decision = route(best["score"]) if best else "NO MATCH"

    print("\n" + "─" * 72)
    print(color(f"  INCOMING: {incoming_name}", "BOLD") +
          (f"  [{incoming_domain}]" if incoming_domain else ""))
    print(f"  DECISION: {color(decision, decision)}" +
          (f"   ← score {best['score']}" if best else ""))

    if best:
        print(f"\n  {'RANK':<5} {'SCORE':<7} {'DECISION':<12} "
              f"{'COMPANY NAME':<35} {'DOMAIN':<20} BREAKDOWN")
        print(f"  {'─'*4} {'─'*6} {'─'*11} {'─'*34} {'─'*19} {'─'*30}")

        for i, c in enumerate(scored[:top_n], 1):
            d = route(c["score"])
            row_color = d
            breakdown = (
                f"name={c['breakdown']['name']} "
                f"domain={c['breakdown']['domain']} "
                f"contact={c['breakdown']['contact']}"
            )
            print(color(
                f"  {i:<5} {c['score']:<7} {d:<12} "
                f"{c['name'][:34]:<35} {c['domain'][:19]:<20} {breakdown}",
                row_color
            ))

    return best, decision, scored[:top_n]


# ── CSV RESULTS EXPORT ────────────────────────────────────────────────────────

def export_results(results, output_path):
    """Export all match results to a CSV for review in Excel."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Incoming org name",
            "Incoming domain",
            "Decision",
            "Best match name",
            "Best match domain",
            "Best match score",
            "Name score",
            "Domain score",
            "Contact score",
            "Rank 2 name",
            "Rank 2 score",
            "Rank 3 name",
            "Rank 3 score",
        ])

        for r in results:
            best   = r["best"]
            top    = r["top_candidates"]
            writer.writerow([
                r["incoming_name"],
                r["incoming_domain"],
                r["decision"],
                best["name"]                    if best else "",
                best["domain"]                  if best else "",
                best["score"]                   if best else "",
                best["breakdown"]["name"]        if best else "",
                best["breakdown"]["domain"]      if best else "",
                best["breakdown"]["contact"]     if best else "",
                top[1]["name"]  if len(top) > 1 else "",
                top[1]["score"] if len(top) > 1 else "",
                top[2]["name"]  if len(top) > 2 else "",
                top[2]["score"] if len(top) > 2 else "",
            ])

    print(f"\n  Results exported to: {output_path}")


# ── SUMMARY ───────────────────────────────────────────────────────────────────

def print_summary(results):
    """Print a summary table of all decisions."""
    high     = sum(1 for r in results if r["decision"] == "HIGH")
    ambig    = sum(1 for r in results if r["decision"] == "AMBIGUOUS")
    no_match = sum(1 for r in results if r["decision"] == "NO MATCH")
    total    = len(results)

    print("\n" + "═" * 72)
    print(color("  SUMMARY", "BOLD"))
    print("═" * 72)
    print(f"  Total signals tested:  {total}")
    print(color(f"  HIGH confidence:       {high}  ({high/total*100:.0f}%)", "HIGH"))
    print(color(f"  AMBIGUOUS:             {ambig}  ({ambig/total*100:.0f}%)", "AMBIGUOUS"))
    print(color(f"  NO MATCH:              {no_match}  ({no_match/total*100:.0f}%)", "NO MATCH"))
    print(f"\n  Thresholds used:  HIGH ≥ {HIGH_THRESHOLD}  ·  AMBIGUOUS ≥ {AMBIGUOUS_LOW}")
    print(f"  Adjust HIGH_THRESHOLD and AMBIGUOUS_LOW at the top of this")
    print(f"  script to tune results, then re-run.")
    print("═" * 72 + "\n")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(color("\n🪶  Lark Fuzzy Matcher — Local Test", "BOLD"))
    print(f"   CSV: {CSV_FILE}")
    print(f"   Thresholds: HIGH ≥ {HIGH_THRESHOLD} · AMBIGUOUS ≥ {AMBIGUOUS_LOW}\n")

    # Load CSV
    print(f"  Loading records from '{CSV_FILE}'...")
    records = load_csv(CSV_FILE)
    print(f"  Loaded {len(records):,} company records.\n")

    if not records:
        print("  No records loaded — check CSV_FILE and column name settings.")
        sys.exit(1)

    # Run each incoming signal
    all_results = []
    for incoming_name, incoming_domain in INCOMING_SIGNALS:
        best, decision, top = print_result(
            incoming_name, incoming_domain, records, TOP_N
        )
        all_results.append({
            "incoming_name":   incoming_name,
            "incoming_domain": incoming_domain,
            "decision":        decision,
            "best":            best,
            "top_candidates":  top,
        })

    # Summary
    print_summary(all_results)

    # Export to CSV
    output_file = f"lark_match_results_{date.today().isoformat()}.csv"
    export_results(all_results, output_file)


if __name__ == "__main__":
    main()
