#!/usr/bin/env python3
"""
lark_enrich.py — Lark Enrichment Run Launcher
===============================================
Triggers an on-demand enrichment run on a provided list of orgs.
This is a parallel mode to the monthly sweep — it does NOT search for
signals. It takes orgs you have already decided need enrichment and
tells Lark to fill in what we know about each one, answering Aaron's
five advisor prep questions.

USAGE:
    python3 lark_enrich.py --orgs orgs.txt          # plain text, one org per line
    python3 lark_enrich.py --orgs pilot.xlsx         # HubSpot Excel export (preferred)
    python3 lark_enrich.py --orgs pilot.csv          # HubSpot CSV export
    python3 lark_enrich.py --orgs pilot.xlsx --advisor "Will Gilmore"
    python3 lark_enrich.py --orgs pilot.xlsx --date 2026-06-22
    python3 lark_enrich.py --orgs pilot.xlsx --no-launch  # print prompt only

WHAT GETS PASSED TO LARK:
    For Excel/CSV inputs: the full contact row for each org — all columns,
    all values. Lark receives everything Farther already knows (GS asset
    figures, contact names, titles, campaign history, city/state, email
    domains) and uses it as a starting point for enrichment, filling gaps
    and adding anything relevant it finds.

    For plain text inputs: org name only (no pre-existing context).

OUTPUT:
    outputs/YYYY-MM-DD-lark-enrichment.csv          <- HubSpot write-back
    outputs/YYYY-MM-DD-lark-enrichment-report.html  <- call-prep report
    EnrichmentProfileUpdate/[org-slug]-profile.md   <- created or updated

HOW IT DIFFERS FROM THE MONTHLY SWEEP:
    lark_launch.py -> signal scan of the world -> match -> enrich -> report
    lark_enrich.py -> provided list -> enrich -> call-prep report (no signal scan)

REQUIREMENTS:
    pip install python-dotenv pandas openpyxl
    contact_data/contacts.csv must exist
"""

import os
import sys
from typing import Optional
import argparse
import subprocess
from datetime import datetime

# ── SETUP ─────────────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TODAY = datetime.now().strftime("%Y-%m-%d")


# ── NOISE FILTER ──────────────────────────────────────────────────────────────

# Values that appear in the company column but are not org names.
NOISE_TITLES = {
    "ceo", "cfo", "coo", "director", "executive director", "president",
    "president/ceo", "president & ceo", "president and ceo", "vp", "svp",
    "board member", "chair", "treasurer", "secretary", "trustee",
    "manager", "hotel manager", "nurse practitioner", "marketing and brand manager",
    "board chair", "vice president", "vp/innovation technology",
    "nan", "none", "n/a", "na", ""
}

# Shared blocklist for alignment detection — values that are clearly not org names
# Used by both _looks_like_org (noise filter) and _detect_column_offset (alignment)
NOISE_VALUES = {
    "ceo", "cfo", "coo", "cdo", "cto", "president", "president/ceo",
    "president & ceo", "president and ceo", "vp", "svp", "evp",
    "executive director", "director", "associate director",
    "deputy director", "managing director", "board member", "chair",
    "board chair", "vice chair", "treasurer", "secretary", "trustee",
    "manager", "hotel manager", "nurse practitioner", "controller",
    "chief operating officer", "chief financial officer",
    "chief executive officer", "chief development officer",
    "chief engagement officer", "chief curator",
    "annual giving and stewardship",
    "marketing and brand manager", "vp/innovation technology",
    "philanthropy officer", "development coordinator",
    "development director", "associate vice president",
    "nan", "none", "n/a", "na", "",
}

ORG_INDICATORS = {
    "foundation", "fund", "institute", "association", "society",
    "center", "centre", "school", "college", "university", "hospital",
    "health", "clinic", "church", "temple", "museum", "gallery",
    "inc", "llc", "corp", "ltd", "co", "organization", "organisation",
    "project", "initiative", "coalition", "alliance", "network",
    "services", "service", "trust", "council", "committee", "board",
    "academy", "program", "programme", "agency", "bureau", "office",
    "department", "division", "group", "team", "community",
    "tree", "house", "refuge", "outlook", "matters", "path", "bridge",
    "circle", "haven", "light", "rise", "reach", "roots", "wings",
    "voices", "table", "door", "garden", "place", "village",
}

def _looks_like_org(value: str) -> bool:
    v = value.strip()
    if not v or v.lower() in NOISE_TITLES:
        return False

    tokens = v.split()

    if len(tokens) == 1:
        if len(v) < 5:
            return False
        if v.isupper() and len(v) < 10:
            return False

    if v.isupper() and len(tokens) <= 2:
        lower_tokens = [t.lower().rstrip(".,") for t in tokens]
        if not any(t in ORG_INDICATORS for t in lower_tokens):
            return False

    lower_tokens = [t.lower().rstrip(".,") for t in tokens]
    has_org_indicator = any(t in ORG_INDICATORS for t in lower_tokens)

    if len(tokens) == 2 and not has_org_indicator:
        if all(t[0].isupper() for t in tokens if t):
            return False

    return True


# ── COLUMN MAPS ───────────────────────────────────────────────────────────────

COMPANY_COL_CANDIDATES = [
    "associated company (primary)",
    "associated company",
    "company (primary)",
    "company",
    "organization",
    "organisation",
]

ADVISOR_COL_CANDIDATES = [
    "contact owner",
    "owner",
    "advisor",
    "adviser",
    "assigned to",
]


def _find_col(headers: list, candidates: list) -> Optional[int]:
    lower_headers = [str(h).strip().lower() for h in headers]
    for candidate in candidates:
        for i, h in enumerate(lower_headers):
            if h == candidate:
                return i
    return None


def _clean_val(v) -> str:
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "nat") else s




# ── SPREADSHEET PARSER (CSV + XLSX) ───────────────────────────────────────────

def _parse_spreadsheet(df_raw_fn, path: str, advisor_filter: Optional[str]) -> list:
    """
    Shared parsing logic for CSV and Excel inputs.

    df_raw_fn: callable(nrows) -> DataFrame with no header parsing
    Returns list of dicts — one per unique org — with ALL columns preserved.
    Multiple contacts at the same org are merged into a contacts[] list
    so Lark sees every person Farther has on file for that org.
    """
    # ── Detect header row ──────────────────────────────────────────────────
    raw = df_raw_fn(nrows=10)
    header_row_idx = None
    for i, row in raw.iterrows():
        row_lower = [str(v).strip().lower() for v in row]
        if any(c in row_lower for c in COMPANY_COL_CANDIDATES):
            header_row_idx = i
            break

    if header_row_idx is None:
        print(f"ERROR: Could not find a company column in {path}")
        print(f"       Expected one of: {COMPANY_COL_CANDIDATES}")
        sys.exit(1)

    # ── Load full file with detected header ────────────────────────────────
    df = df_raw_fn(nrows=None)
    headers_raw = df.iloc[header_row_idx].tolist()
    headers = [str(h).strip() for h in headers_raw]
    df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
    df.columns = headers

    # ── Find key columns ───────────────────────────────────────────────────
    company_col = _find_col(headers, COMPANY_COL_CANDIDATES)
    advisor_col  = _find_col(headers, ADVISOR_COL_CANDIDATES)

    if company_col is None:
        print("ERROR: No company column found after header detection.")
        sys.exit(1)

    company_col_name = headers[company_col]

    # ── Apply advisor filter ───────────────────────────────────────────────
    if advisor_filter:
        if advisor_col is not None:
            advisor_col_name = headers[advisor_col]
            mask = df[advisor_col_name].astype(str).str.lower().str.contains(
                advisor_filter.lower(), na=False
            )
            df = df[mask]
            if df.empty:
                print(f"WARNING: No rows matched advisor filter '{advisor_filter}'")
                print(f"         Check spelling or omit --advisor to include all rows.")
        else:
            print("WARNING: --advisor filter set but no advisor column found. Ignoring.")

    # ── Group rows by org ──────────────────────────────────────────────────
    # Each unique org gets one dict. Multiple contacts collapse into contacts[].
    orgs: dict[str, dict] = {}   # keyed by lowercased org name

    for _, row in df.iterrows():
        raw_company = _clean_val(row.get(company_col_name, ""))
        if not raw_company or not _looks_like_org(raw_company):
            continue

        key = raw_company.lower()

        # Build contact record from this row
        contact = {}
        for col in headers:
            val = _clean_val(row.get(col, ""))
            if val and col.lower() not in [company_col_name.lower()]:
                contact[col] = val

        if key not in orgs:
            # First time seeing this org — initialise the org record
            org_record = {"org_name": raw_company, "contacts": []}

            # Promote any org-level fields we can identify from this first row
            # (city, state, GS fields — same for all contacts at this org)
            for col in headers:
                col_lower = col.lower()
                val = _clean_val(row.get(col, ""))
                if not val:
                    continue
                if col_lower in ("city", "state"):
                    org_record[col] = val
                elif col_lower.startswith("gs"):
                    org_record[col] = val
                elif col_lower in ("associated company ids (primary)",):
                    org_record[col] = val

            orgs[key] = org_record

        # Add contact to the org
        # Pull out the fields that are contact-specific
        contact_record = {}
        CONTACT_FIELDS = {
            "full name", "first name", "last name", "email",
            "phone number", "title", "decision maker?",
            "campaign", "tier", "contact owner", "email msg",
        }
        for col in headers:
            val = _clean_val(row.get(col, ""))
            if val and col.lower() in CONTACT_FIELDS:
                contact_record[col] = val

        if contact_record:
            orgs[key]["contacts"].append(contact_record)

    return list(orgs.values())


def parse_excel_file(path: str, advisor_filter: Optional[str] = None) -> list:
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas + openpyxl required.  pip install pandas openpyxl")
        sys.exit(1)
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    def loader(nrows):
        return pd.read_excel(path, header=None, dtype=str, nrows=nrows)

    return _parse_spreadsheet(loader, path, advisor_filter)


def parse_csv_file(path: str, advisor_filter: Optional[str] = None) -> list:
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required.  pip install pandas")
        sys.exit(1)
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    def loader(nrows):
        return pd.read_csv(path, header=None, dtype=str, nrows=nrows)

    return _parse_spreadsheet(loader, path, advisor_filter)


# ── PLAIN TEXT PARSER ─────────────────────────────────────────────────────────

def parse_org_file(path: str) -> list:
    """
    Parse a plain-text org list. Returns list of minimal org dicts
    (org_name only — no pre-existing context).
    """
    if not os.path.exists(path):
        print(f"ERROR: Org file not found: {path}")
        sys.exit(1)

    orgs = []
    seen = set()
    with open(path) as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                parts = [p.strip() for p in line.split("|", 1)]
                name   = parts[0]
                domain = parts[1] if len(parts) > 1 else ""
            elif "\t" in line:
                parts  = line.split("\t", 1)
                name   = parts[0].strip()
                domain = parts[1].strip() if len(parts) > 1 else ""
            else:
                name   = line
                domain = ""

            if name and name.lower() not in seen:
                seen.add(name.lower())
                rec = {"org_name": name, "contacts": []}
                if domain:
                    rec["domain"] = domain
                orgs.append(rec)

    return orgs


# ── INPUT ROUTER ──────────────────────────────────────────────────────────────

def parse_input(path: str, advisor_filter: Optional[str] = None) -> list:
    ext = path.lower()
    if ext.endswith(".xlsx") or ext.endswith(".xls"):
        return parse_excel_file(path, advisor_filter)
    elif ext.endswith(".csv"):
        return parse_csv_file(path, advisor_filter)
    else:
        if advisor_filter:
            print("WARNING: --advisor filter only supported for CSV/Excel. Ignoring.")
        return parse_org_file(path)


# ── FORMAT ORG CONTEXT BLOCK ──────────────────────────────────────────────────

def _fmt_org_block(org: dict) -> str:
    """
    Format one org's full context as a readable block for the prompt.
    Lark gets everything — it decides what's useful.
    """
    lines = [f"  Org: {org['org_name']}"]

    # Org-level fields (city, state, GS figures, HubSpot IDs)
    skip = {"org_name", "contacts"}
    for k, v in org.items():
        if k in skip or not v:
            continue
        lines.append(f"  {k}: {v}")

    # Contacts
    contacts = org.get("contacts", [])
    if contacts:
        lines.append(f"  Contacts on file ({len(contacts)}):")
        for c in contacts:
            parts = []
            for field in ("Full Name", "Title", "Email", "Phone Number",
                          "Decision Maker?", "Campaign", "Tier", "Contact owner"):
                val = c.get(field, "")
                if val:
                    label = field if field not in ("Full Name",) else ""
                    parts.append(f"{field}: {val}" if label else val)
            lines.append("    · " + "  |  ".join(parts))

    return "\n".join(lines)


# ── BUILD ENRICHMENT PROMPT ───────────────────────────────────────────────────

def build_enrichment_prompt(orgs: list, today: str) -> str:
    org_blocks = "\n\n".join(_fmt_org_block(o) for o in orgs)

    has_gs = any(
        any(k.lower().startswith("gs") for k in o)
        for o in orgs
    )

    gs_note = ""
    if has_gs:
        gs_note = """
GS fields note: where GS - Total Assets and GS_Investments_Securities_Sync
are present, treat them as Farther internal estimates (label accordingly).
Cross-reference against ProPublica 990. Use GS figures as a starting point,
990 as the authoritative source. Note any divergence.
"""

    return f"""Run an enrichment run on the following org list.

MODE: ENRICHMENT RUN — this is NOT a signal sweep.
Do NOT search for signals. Do NOT run signal channels Ch1–Ch8.
Do NOT score contacts. Do NOT set action windows or lark_contact_status.

Today's date: {today}

Read skills/enrichment-run.md before starting.
Read honesty.md before any output.
{gs_note}
Each org below includes everything Farther already has on file.
The data comes from a HubSpot export and column alignment may be off —
headers and data rows don't always line up perfectly in these exports.
Use the full row context (email domains, phone numbers, titles, GS figures)
to infer which value is the actual org name if it's ambiguous.
Use this as your starting point. Fill gaps. Add anything relevant you find.
The goal is a call-prep card that answers Aaron's five advisor questions
in plain English — not a data dump.

Org list ({len(orgs)} orgs):

{org_blocks}

─────────────────────────────────────────────

Instructions:

Phase A — Research (answer the five advisor questions per org)
  Do NOT run the fuzzy matcher. Do NOT write to /tmp/lark_signals.json.
  Do NOT run lark_run_matcher.py. These are known contacts — trust the list.
  See skills/enrichment-run.md Phase A for full instructions.
  Use the pre-existing context above as a starting point for each org.
  Pull TWO years of 990 data from ProPublica where available.
  Fetch each org's website. Run all six targeted news searches.
  Add anything relevant you find beyond the five questions.

Phase B — Profile
  Call upsert_enrichment_profile() for each org.
  Do NOT overwrite existing signal timeline or compound score.

Phase C — HubSpot CSV
  Write enrichment fields only to outputs/{today}-lark-enrichment.csv.
  Do NOT write lark_signal_type, lark_compound_score, lark_action_window,
  or lark_contact_status.

Phase D — Report
  Generate outputs/{today}-lark-enrichment-report.html.
  One call-prep card per org. Plain English. Human voice.
  See skills/enrichment-run.md Phase D for card format.

Do NOT read contact_data/contacts.csv directly.
Do NOT run a monthly sweep.
Ask if anything is unclear before starting."""


# ── LAUNCH CLAUDE CODE ────────────────────────────────────────────────────────

def launch_claude(prompt: str, prompt_file: str):
    print("\n" + "─" * 72)
    print("🪶  Lark · Enrichment Run Launcher")
    print("─" * 72)
    print(f"\n✓ Full enrichment prompt written to: {prompt_file}")
    print("\nPaste this into Claude Code:\n")
    print("─" * 72)
    print(f"Read {prompt_file} and follow the instructions.")
    print("─" * 72 + "\n")
    try:
        subprocess.Popen(["claude"], cwd=os.getcwd())
        print("✓ Claude Code launched.")
        print("  Paste the one-liner above — Lark reads the rest from the prompt file.")
    except FileNotFoundError:
        print("  'claude' command not found — open Claude Code manually")
        print(f"  and paste: Read {prompt_file} and follow the instructions.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def _interactive_mode() -> tuple:
    """
    Prompt the user to choose a file when lark_enrich.py is run with no arguments.
    Scans inputs/ for Excel, CSV, and text files and presents them as a numbered
    list. Returns (filepath, advisor_filter).
    """
    print("\n🪶  Lark · Enrichment Run Launcher")
    print("─" * 48)

    # Scan inputs/ for candidate files
    inputs_dir = os.path.join(os.getcwd(), "inputs")
    candidates = []
    if os.path.isdir(inputs_dir):
        for f in sorted(os.listdir(inputs_dir)):
            if f.lower().endswith((".xlsx", ".xls", ".csv", ".txt")) and not f.startswith("."):
                candidates.append(os.path.join(inputs_dir, f))

    if not candidates:
        print("\n   No files found in inputs/")
        print("   Drop a HubSpot Excel export (.xlsx), CSV (.csv), or org list (.txt)")
        print("   into the inputs/ folder, then run again.\n")
        print("   Or pass a file directly:  python3 lark_enrich.py --orgs path/to/file.xlsx\n")
        sys.exit(0)

    print("\n   Files available in inputs/:\n")
    for i, path in enumerate(candidates, 1):
        fname = os.path.basename(path)
        size  = os.path.getsize(path)
        size_str = f"{size/1024:.0f}KB" if size > 1024 else f"{size}B"
        print(f"   [{i}] {fname}  ({size_str})")

    print(f"\n   [{len(candidates)+1}] Enter a different path")
    print()

    while True:
        choice = input("   Select file (number or path): ").strip()
        if not choice:
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(candidates):
                filepath = candidates[idx - 1]
                break
            elif idx == len(candidates) + 1:
                filepath = input("   Path to file: ").strip()
                if not os.path.exists(filepath):
                    print(f"   File not found: {filepath}")
                    continue
                break
        else:
            # Treat as a direct path
            if os.path.exists(choice):
                filepath = choice
                break
            print(f"   File not found: {choice}")

    # Ask for advisor filter if Excel or CSV
    advisor = None
    if filepath.lower().endswith((".xlsx", ".xls", ".csv")):
        advisor_input = input("\n   Filter by advisor name? (press Enter to include all): ").strip()
        if advisor_input:
            advisor = advisor_input

    return filepath, advisor


def main():
    parser = argparse.ArgumentParser(
        description="Lark Enrichment Run Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run with no arguments for interactive mode."
    )
    parser.add_argument(
        "--orgs", type=str, default=None,
        help="Org list: plain text (.txt), HubSpot Excel (.xlsx), or CSV (.csv)"
    )
    parser.add_argument(
        "--advisor", type=str, default=None,
        help="Filter by contact owner name (Excel/CSV only, partial match)"
    )
    parser.add_argument(
        "--date", type=str, default=TODAY,
        help="Run date YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--no-launch", action="store_true",
        help="Print prompt only — do not launch Claude Code"
    )
    args = parser.parse_args()

    # ── Interactive mode when run with no arguments ────────────────────────
    if args.orgs is None:
        filepath, advisor = _interactive_mode()
        args.orgs   = filepath
        if advisor and args.advisor is None:
            args.advisor = advisor

    today = args.date
    ext   = args.orgs.lower()
    fmt   = "Excel" if ext.endswith((".xlsx", ".xls")) else "CSV" if ext.endswith(".csv") else "text"

    print(f"\n🪶  Lark · Enrichment Run Launcher")
    print(f"   Date:    {today}")
    print(f"   Input:   {args.orgs} ({fmt})")
    if args.advisor:
        print(f"   Advisor: {args.advisor}")

    orgs = parse_input(args.orgs, args.advisor)

    if not orgs:
        print("\nERROR: No orgs found. Check file format.")
        sys.exit(1)

    print(f"\n   {len(orgs)} org(s) ready for enrichment:\n")
    for o in orgs:
        n_contacts = len(o.get("contacts", []))
        has_gs = any(k.lower().startswith("gs") for k in o)
        tags = []
        if n_contacts:
            tags.append(f"{n_contacts} contact{'s' if n_contacts > 1 else ''}")
        if has_gs:
            tags.append("GS assets")
        tag_str = f"  [{', '.join(tags)}]" if tags else ""
        print(f"  → {o['org_name']}{tag_str}")
    print()

    prompt = build_enrichment_prompt(orgs, today)

    # Write prompt to inputs/ so Lark can read it directly
    os.makedirs("inputs", exist_ok=True)
    input_slug = os.path.splitext(os.path.basename(args.orgs))[0].lower()
    input_slug = input_slug.replace(" ", "-")
    prompt_file = os.path.join("inputs", f"enrichment-prompt-{today}-{input_slug}.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)

    if args.no_launch:
        print("─" * 72)
        print(f"✓ Prompt written to: {prompt_file}")
        print(f"\nWhen ready, open Claude Code and paste:")
        print(f"  Read {prompt_file} and follow the instructions.")
        print("─" * 72)
    else:
        launch_claude(prompt, prompt_file)


if __name__ == "__main__":
    main()