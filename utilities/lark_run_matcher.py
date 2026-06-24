#!/usr/bin/env python3
"""
lark_run_matcher.py — Lark Phase 2 · Standalone Match Runner
=============================================================
Runs match_batch() as a standalone script to force foreground execution
in Claude Code. The Bash tool backgrounds long-running inline python3 -c
commands automatically — running a script file blocks until completion.

USAGE — Lark calls this during Phase 2:
    python3 utilities/lark_run_matcher.py

INPUT:
    /tmp/lark_signals.json — written by Lark at end of Phase 1

    NEW FORMAT (full metadata per signal):
    [
      {
        "org_name":     "MADD",
        "domain":       "madd.org",
        "signal_type":  "SIG-001",
        "channel":      "Ch1",
        "source_url":   "https://madd.org/press-release/...",
        "finding_text": "Kevin Byrne named CFO February 11, 2026",
        "signal_date":  "2026-02-11",
        "confidence":   "Confirmed"
      },
      ...
    ]

    LEGACY FORMAT (still supported — tuples from old sweeps):
    [["MADD", "madd.org"], ...]

OUTPUT:
    /tmp/lark_results.json — read by Lark at start of Phase 3
    Each result includes the original signal metadata + match decision.

SIGNALS:
    Prints progress to stdout throughout — Claude Code reads this directly.
    Final line is always: MATCH_BATCH_COMPLETE: N HIGH · N AMBIGUOUS · N NO_MATCH
    Lark waits for that line before proceeding to Phase 3.

CRITICAL:
    This script must always run in the foreground.
    Never call with & or nohup.
    Claude Code must wait for MATCH_BATCH_COMPLETE before Phase 3.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.lark_fuzzy_matcher import LarkMatcher
from utilities.lark_dedup import dedup_signals

# ── PATHS ─────────────────────────────────────────────────────────────────────

SIGNALS_FILE  = "/tmp/lark_signals.json"
RESULTS_FILE  = "/tmp/lark_results.json"
CONTACTS_CSV  = "contact_data/contacts.csv"


# ── LOAD SIGNALS ──────────────────────────────────────────────────────────────

print("[Phase 2] lark_run_matcher.py — starting")
print(f"[Phase 2] Reading signals from {SIGNALS_FILE}")

# Clear any stale flag from a previous run
if os.path.exists('/tmp/lark_match_complete.flag'):
    os.remove('/tmp/lark_match_complete.flag')
    print("[Phase 2] Cleared stale completion flag from previous run")

if not os.path.exists(SIGNALS_FILE):
    print(f"ERROR: {SIGNALS_FILE} not found.")
    print("       Lark must write all_signals to /tmp/lark_signals.json before calling this script.")
    sys.exit(1)

with open(SIGNALS_FILE) as f:
    raw = json.load(f)

# ── HANDLE BOTH FORMATS ───────────────────────────────────────────────────────
# New format: list of dicts with full metadata
# Legacy format: list of [org_name, domain] tuples

signal_meta: list[dict] = []

for item in raw:
    if isinstance(item, dict):
        # New format — full metadata
        signal_meta.append({
            "org_name":     item.get("org_name", ""),
            "domain":       item.get("domain", ""),
            "signal_type":  item.get("signal_type", ""),
            "channel":      item.get("channel", ""),
            "source_url":   item.get("source_url", ""),
            "finding_text": item.get("finding_text", ""),
            "signal_date":  item.get("signal_date", ""),
            "confidence":   item.get("confidence", ""),
        })
    elif isinstance(item, (list, tuple)) and len(item) >= 2:
        # Legacy format — tuples
        signal_meta.append({
            "org_name":     item[0],
            "domain":       item[1],
            "signal_type":  "",
            "channel":      "",
            "source_url":   "",
            "finding_text": "",
            "signal_date":  "",
            "confidence":   "",
        })

has_metadata = any(s["signal_type"] for s in signal_meta)
if has_metadata:
    print(f"[Phase 2] Signal format: FULL METADATA ✓ — signal types will carry through to report")
else:
    print(f"[Phase 2] Signal format: LEGACY (tuples) — signal types unknown, report will flag gap")

print(f"[Phase 2] Signals loaded: {len(signal_meta)}")

# Dedup by org_name
tuples_for_dedup = [(s["org_name"], s["domain"]) for s in signal_meta]
deduped_tuples   = dedup_signals(tuples_for_dedup, verbose=True)

# Rebuild signal_meta in deduped order
seen = set()
deduped_meta = []
for s in signal_meta:
    key = s["org_name"].lower().strip()
    if key not in seen and key:
        seen.add(key)
        deduped_meta.append(s)

signal_meta = deduped_meta
print(f"[Phase 2] Signals after dedup: {len(signal_meta)}")
print()


# ── LOAD MATCHER ──────────────────────────────────────────────────────────────

print(f"[Phase 2] Loading matcher from {CONTACTS_CSV}")
print(f"[Phase 2] This will take 15–25 minutes for 190K records in Claude Code — do not interrupt")
print()

if not os.path.exists(CONTACTS_CSV):
    print(f"ERROR: {CONTACTS_CSV} not found.")
    print(f"       Expected at: {os.path.abspath(CONTACTS_CSV)}")
    sys.exit(1)

t0      = time.time()
matcher = LarkMatcher(CONTACTS_CSV)
print()


# ── RUN MATCH_BATCH ───────────────────────────────────────────────────────────

match_tuples = [(s["org_name"], s["domain"]) for s in signal_meta]

print(f"[Phase 2] Running match_batch() — ONE call for all {len(match_tuples)} signals")
print(f"[Phase 2] Do not run any other commands until MATCH_BATCH_COMPLETE prints")
print()

results = matcher.match_batch(match_tuples)
elapsed = time.time() - t0


# ── SERIALIZE RESULTS — carry signal metadata through ─────────────────────────

def serialize_result(r, meta: dict) -> dict:
    """
    Convert a MatchResult + signal metadata to a JSON-serializable dict.
    Signal metadata (type, source, date, confidence) carries through
    from Phase 1 so Phase 4 can score and report accurately.
    """
    return {
        # Match result
        "incoming_name":         r.incoming_name,
        "incoming_domain":       r.incoming_domain,
        "decision":              r.decision,
        "score":                 r.score,
        "matched_row":           r.matched_row,
        "aum_value":             r.aum_value,
        "meets_aum_threshold":   r.meets_aum_threshold,
        "acronym_path":          r.acronym_path,
        "acronym_fallback_used": r.acronym_fallback_used,
        "breakdown":             r.breakdown,
        "top_candidates":        [
            {"name": c.get("name", ""), "score": c.get("score", 0)}
            for c in (r.top_candidates or [])[:3]
        ],
        # Signal metadata from Phase 1
        "signal_type":           meta.get("signal_type", ""),
        "channel":               meta.get("channel", ""),
        "source_url":            meta.get("source_url", ""),
        "finding_text":          meta.get("finding_text", ""),
        "signal_date":           meta.get("signal_date", ""),
        "confidence":            meta.get("confidence", ""),
    }

serialized = [
    serialize_result(r, signal_meta[i])
    for i, r in enumerate(results)
]

with open(RESULTS_FILE, "w") as f:
    json.dump(serialized, f, indent=2)

print()
print(f"[Phase 2] Results written to {RESULTS_FILE}")
print(f"[Phase 2] Signal metadata carried: {'YES ✓' if has_metadata else 'NO — legacy format'}")


# ── SUMMARY ───────────────────────────────────────────────────────────────────

high      = [r for r in results if r.decision == "HIGH"]
above_aum = [r for r in high if r.meets_aum_threshold]
below_aum = [r for r in high if not r.meets_aum_threshold]
ambig     = [r for r in results if r.decision == "AMBIGUOUS"]
no_match  = [r for r in results if r.decision == "NO_MATCH"]

print()
print(f"[Phase 2] ─────────────────────────────────────────────")
print(f"[Phase 2] Total signals:       {len(results)}")
print(f"[Phase 2] HIGH:                {len(high)}")
print(f"[Phase 2]   Above AUM ($1M+):  {len(above_aum)}  ← proceed to Phase 3")
print(f"[Phase 2]   Below AUM:         {len(below_aum)}  ← do not enrich")
print(f"[Phase 2] AMBIGUOUS:           {len(ambig)}  ← flag for manual review (score 50–79)")
print(f"[Phase 2] NO_MATCH:            {len(no_match)}  ← scored too low · human review for discard")
print(f"[Phase 2] Elapsed:             {elapsed:.0f}s")
print(f"[Phase 2] ─────────────────────────────────────────────")
print()

if above_aum:
    print(f"[Phase 2] HIGH matches proceeding to Phase 3:")
    for i, r in enumerate(results):
        if r.decision == "HIGH" and r.meets_aum_threshold:
            name     = r.matched_row.get("Org Name", "?") if r.matched_row else "?"
            aum      = f"${r.aum_value:,.0f}" if r.aum_value else "AUM unknown"
            sig_type = signal_meta[i].get("signal_type", "") or "type unknown"
            print(f"  {name:<50} score={r.score}  {aum}  [{sig_type}]")
    print()

if ambig:
    print(f"[Phase 2] AMBIGUOUS — manual review required:")
    for i, r in enumerate(results):
        if r.decision == "AMBIGUOUS":
            top      = r.top_candidates[0]["name"] if r.top_candidates else "?"
            sig_type = signal_meta[i].get("signal_type", "") or "type unknown"
            print(f"  {r.incoming_name:<40} score={r.score}  best: {top}  [{sig_type}]")
    print()

if no_match:
    print(f"[Phase 2] NO_MATCH — scored too low · human review for discard:")
    for i, r in enumerate(results):
        if r.decision == "NO_MATCH":
            top = r.top_candidates[0]["name"] if r.top_candidates else "?"
            print(f"  {r.incoming_name:<40} score={r.score}  best: {top}")
    print()

# ── COMPLETION SIGNAL ─────────────────────────────────────────────────────────
# Writes to both stdout AND a flag file.
# If the process was backgrounded, Lark polls /tmp/lark_match_complete.flag
# rather than waiting on stdout. Both are written — whichever Lark sees first.

completion_msg = f"MATCH_BATCH_COMPLETE: {len(high)} HIGH · {len(ambig)} AMBIGUOUS · {len(no_match)} NO_MATCH"

print(completion_msg)

with open('/tmp/lark_match_complete.flag', 'w') as f:
    f.write(completion_msg)

print("[Phase 2] Completion flag written to /tmp/lark_match_complete.flag")