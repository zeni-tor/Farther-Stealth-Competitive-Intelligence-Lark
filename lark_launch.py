#!/usr/bin/env python3
"""
lark_launch.py — Lark Sweep Launcher
=====================================
Runs APIs that are blocked inside Claude Code (Cloudflare restriction),
saves results to preflight/, then launches Claude Code with the sweep prompt.

WHY THIS EXISTS:
    Currents API and GlobeNewswire RSS are blocked inside Claude Code because
    Anthropic's server IPs are flagged by Cloudflare. Running them from your
    local machine (personal IP) works fine. This script does the local work
    first, then hands off to Claude Code.

USAGE:
    python3 lark_launch.py                    # 30-day lookback from today
    python3 lark_launch.py --days 30          # explicit lookback
    python3 lark_launch.py --no-launch        # preflight only, don't open Claude Code

OUTPUT:
    preflight/currents-YYYY-MM-DD.json        # Currents API signals
    preflight/rss-YYYY-MM-DD.json             # GlobeNewswire RSS signals

Lark reads these files during Phase 1 before running web searches.
If a preflight file exists for today's date, Lark skips the API call.

REQUIREMENTS:
    pip install feedparser python-dotenv
    CURRENTS_API_KEY in .env
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta

# ── SETUP ─────────────────────────────────────────────────────────────────────

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PREFLIGHT_DIR = "preflight"
TODAY         = datetime.now().strftime("%Y-%m-%d")


def ensure_preflight_dir():
    os.makedirs(PREFLIGHT_DIR, exist_ok=True)


def preflight_path(source: str, today: str) -> str:
    return os.path.join(PREFLIGHT_DIR, f"{source}-{today}.json")


# ── CURRENTS API ──────────────────────────────────────────────────────────────

def run_currents(lookback_days: int, today: str) -> int:
    """
    Run Currents API sweep from local machine and save to preflight/.
    Returns number of signals collected.
    today: sweep date string YYYY-MM-DD — used for file naming and cutoff.
    """
    output_path = preflight_path("currents", today)

    if os.path.exists(output_path):
        print(f"[Currents] Preflight file already exists: {output_path}")
        with open(output_path) as f:
            existing = json.load(f)
        print(f"[Currents] {len(existing)} signals loaded from cache")
        return len(existing)

    key = os.environ.get("CURRENTS_API_KEY", "")
    if not key:
        print("[Currents] ERROR: CURRENTS_API_KEY not set in .env — skipping")
        return 0

    print(f"[Currents] Running Layer B sweep · lookback {lookback_days} days · as-of {today}...")

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from utilities.lark_newsapi import run_currents_sweep

        result = run_currents_sweep(lookback_days=lookback_days, verbose=True, as_of=today)

        # Convert to full signal dicts (new metadata format)
        signals = []
        for sig in result.signals:
            signals.append({
                "org_name":     sig.org_name,
                "domain":       sig.domain,
                "signal_type":  sig.signal_type,
                "channel":      "Ch-B-Currents",
                "source_url":   sig.url,
                "finding_text": sig.title,
                "signal_date":  sig.published[:10] if sig.published else "",
                "confidence":   "Inferred",
            })

        with open(output_path, "w") as f:
            json.dump(signals, f, indent=2)

        print(f"[Currents] {len(signals)} signals saved → {output_path}")
        return len(signals)

    except Exception as e:
        print(f"[Currents] ERROR: {e}")
        return 0


# ── GLOBENEWSWIRE RSS ─────────────────────────────────────────────────────────

def run_rss(lookback_days: int, today: str) -> int:
    """
    Run GlobeNewswire RSS sweep from local machine and save to preflight/.
    Returns number of signals collected.
    today: sweep date string YYYY-MM-DD — used for file naming and cutoff.
    """
    output_path = preflight_path("rss", today)

    if os.path.exists(output_path):
        print(f"[RSS] Preflight file already exists: {output_path}")
        with open(output_path) as f:
            existing = json.load(f)
        print(f"[RSS] {len(existing)} signals loaded from cache")
        return len(existing)

    try:
        from utilities.lark_rss import fetch_gnw_signals
    except ImportError as e:
        print(f"[RSS] ERROR: {e}")
        print("[RSS] Run: pip install feedparser")
        return 0

    print(f"[RSS] Running Layer A sweep · lookback {lookback_days} days · as-of {today}...")

    try:
        result = fetch_gnw_signals(lookback_days=lookback_days, verbose=True, as_of=today)

        # Convert to full signal dicts
        signals = []
        for sig in result.signals:
            signals.append({
                "org_name":     sig.org_name,
                "domain":       sig.domain,
                "signal_type":  sig.signal_type,
                "channel":      "Ch-A-RSS",
                "source_url":   sig.url,
                "finding_text": sig.title,
                "signal_date":  sig.published.strftime("%Y-%m-%d") if sig.published else "",
                "confidence":   "Confirmed",  # GlobeNewswire press releases are confirmed
            })

        with open(output_path, "w") as f:
            json.dump(signals, f, indent=2)

        print(f"[RSS] {len(signals)} signals saved → {output_path}")
        return len(signals)

    except Exception as e:
        print(f"[RSS] ERROR: {e}")
        return 0


# ── BUILD SWEEP PROMPT ────────────────────────────────────────────────────────

def build_sweep_prompt(lookback_days: int, today: str) -> str:
    lookback_start = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    currents_file = preflight_path("currents", today)
    rss_file      = preflight_path("rss", today)

    preflight_note = ""
    if os.path.exists(currents_file) or os.path.exists(rss_file):
        files = []
        if os.path.exists(rss_file):
            files.append(f"preflight/rss-{today}.json (Layer A — GlobeNewswire RSS)")
        if os.path.exists(currents_file):
            files.append(f"preflight/currents-{today}.json (Layer B — Currents API)")
        preflight_note = (
            f"\nPreflight data is available — read these files and add signals to "
            f"all_signals[] before running other channels:\n"
            + "\n".join(f"  {f}" for f in files)
            + "\nDo NOT call the Currents API or GlobeNewswire RSS directly — "
            f"use the preflight files instead.\n"
        )

    return f"""Run a full signal sweep. All channels active including Channel 5 (LinkedIn/Apify).
Today's date: {today}
Lookback window: past {lookback_days} days ({lookback_start} – {today})
{preflight_note}
Use contact_data/contacts.csv. Load the fuzzy matcher once, run all
searches first (including LinkedIn via Apify), then run Phase 2 by
writing all_signals to /tmp/lark_signals.json and running
python3 utilities/lark_run_matcher.py as a standalone script.
Wait for MATCH_BATCH_COMPLETE to print before proceeding to Phase 3.
Do not use inline python3 -c for match_batch().
Each signal in all_signals[] must be a dict with keys: org_name, domain,
signal_type, channel, source_url, finding_text, signal_date, confidence.
Deduplicate all_signals[] before calling match_batch().
Do not read the contact list directly.
Ask if anything is unclear before starting."""


# ── LAUNCH CLAUDE CODE ────────────────────────────────────────────────────────

def launch_claude(prompt: str):
    """Launch Claude Code — prints the prompt for easy copy-paste."""
    print("\n" + "─" * 72)
    print("🪶  Lark · Preflight complete. Launching Claude Code...")
    print("─" * 72)
    print("\nSweep prompt (copy and paste into Claude Code):\n")
    print("─" * 72)
    print(prompt)
    print("─" * 72 + "\n")

    # Try to launch Claude Code
    try:
        subprocess.Popen(["claude"], cwd=os.getcwd())
        print("✓ Claude Code launched.")
        print("  Paste the prompt above into the Claude Code terminal.")
    except FileNotFoundError:
        print("  'claude' command not found — open Claude Code manually")
        print("  and paste the prompt above.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lark Sweep Launcher")
    parser.add_argument("--days",      type=int, default=30,   help="Lookback window in days (default: 30)")
    parser.add_argument("--date",      type=str, default=TODAY, help="Today's date YYYY-MM-DD (default: today)")
    parser.add_argument("--no-launch", action="store_true",    help="Run preflight only, don't launch Claude Code")
    parser.add_argument("--no-rss",    action="store_true",    help="Skip GlobeNewswire RSS")
    parser.add_argument("--no-currents", action="store_true",  help="Skip Currents API")
    args = parser.parse_args()

    today = args.date

    print(f"\n🪶  Lark · Sweep Launcher")
    print(f"   Date:     {today}")
    print(f"   Lookback: {args.days} days")
    print(f"   Preflight dir: {PREFLIGHT_DIR}/\n")

    ensure_preflight_dir()

    total_signals = 0

    # ── Layer A — GlobeNewswire RSS ───────────────────────────────────────────
    if not args.no_rss:
        n = run_rss(args.days, today)
        total_signals += n
        print()
    else:
        print("[RSS] Skipped (--no-rss)\n")

    # ── Layer B — Currents API ────────────────────────────────────────────────
    if not args.no_currents:
        n = run_currents(args.days, today)
        total_signals += n
        print()
    else:
        print("[Currents] Skipped (--no-currents)\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"─" * 72)
    print(f"Preflight complete · {total_signals} signals collected")

    rss_file      = preflight_path("rss", today)
    currents_file = preflight_path("currents", today)

    if os.path.exists(rss_file):
        print(f"  ✓ {rss_file}")
    if os.path.exists(currents_file):
        print(f"  ✓ {currents_file}")
    print()

    # ── Build sweep prompt ────────────────────────────────────────────────────
    prompt = build_sweep_prompt(args.days, today)

    # ── Launch Claude Code ────────────────────────────────────────────────────
    if args.no_launch:
        print("Preflight only — Claude Code not launched (--no-launch)")
        print("\nSweep prompt:\n")
        print(prompt)
    else:
        launch_claude(prompt)


if __name__ == "__main__":
    main()