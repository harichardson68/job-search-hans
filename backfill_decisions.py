"""
backfill_decisions.py — ONE-TIME RUN
=====================================
Reads ALL rows from the Google Sheet and merges them into
job_decisions.json. Run this once to recover all 83 past decisions.

For dates where today_jobs.json is available (today only), full
job metadata is matched. For all past dates, bare-bones records
are saved — date, job number, decision, reason. This is sufficient
for K-Means training data.

After running this once, delete this file. update_scoring.py
handles everything going forward.

RUN:
    cd C:\\Users\\haric\\Jobsearch
    python backfill_decisions.py
"""

import os
import json
from datetime import datetime, date
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

SHEET_ID         = "1nv9XmVWJUvJ08t6ldjJFYhZ25MfTLhUAAph3CrSzlmE"
SHEET_RANGE      = "Form Responses 1!A:D"
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "google_credentials.json")
DECISIONS_FILE   = os.path.join(SCRIPT_DIR, "job_decisions.json")
TODAY_JOBS_FILE  = os.path.join(SCRIPT_DIR, "today_jobs.json")
TODAY            = date.today().isoformat()

DECISION_MAP = {
    "applied":                  "applied",
    "bad link":                 "bad_link",
    "onsite / not remote":      "onsite",
    "onsite":                   "onsite",
    "too senior":               "too_senior",
    "salary too low":           "salary_too_low",
    "not interested":           "not_interested",
    "already seen / duplicate": "already_seen",
    "already seen":             "already_seen",
    "search page listing":      "search_page",
    "search page":              "search_page",
    "not in united states":     "not_in_us",
    "other":                    "other",
}

print(f"\n{'='*55}")
print(f"  Backfill Decisions — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*55}\n")


def parse_sheet_date(ts):
    """Parse M/D/YYYY HH:MM:SS or similar into YYYY-MM-DD."""
    if not ts:
        return None
    ts = str(ts).strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_job_num(raw):
    """
    Normalize job number — strip spaces, uppercase.
    Returns int (1-10) or str (A1-A5) or None if invalid.
    """
    s = str(raw).strip().upper()
    if s.startswith("A"):
        # Amazon job — must be A1-A5
        try:
            n = int(s[1:])
            if 1 <= n <= 5:
                return s  # "A1" .. "A5"
        except ValueError:
            pass
        return None
    else:
        try:
            n = int(s)
            if 1 <= n <= 10:
                return n
        except ValueError:
            pass
        return None


def read_all_sheet_rows():
    """Read every row from the sheet, return list of parsed dicts."""
    rows_out = []
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        result  = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=SHEET_RANGE
        ).execute()
        rows = result.get("values", [])
        if not rows or len(rows) < 2:
            print("[INFO] No rows found in sheet")
            return rows_out

        print(f"[SHEET] {len(rows)-1} total rows found\n")

        skipped = 0
        for row in rows[1:]:
            timestamp  = row[0] if len(row) > 0 else ""
            job_number = row[1] if len(row) > 1 else ""
            decision   = row[2] if len(row) > 2 else ""
            reason     = row[3] if len(row) > 3 else ""

            row_date = parse_sheet_date(timestamp)
            if not row_date:
                print(f"   [SKIP] Unparseable timestamp: '{timestamp}'")
                skipped += 1
                continue

            job_num = parse_job_num(job_number)
            if job_num is None:
                print(f"   [SKIP] Invalid job number: '{job_number}' on {row_date}")
                skipped += 1
                continue

            decision_key = DECISION_MAP.get(decision.lower().strip(), "other")
            rows_out.append({
                "date":     row_date,
                "job_num":  job_num,
                "decision": decision_key,
                "reason":   reason.strip() if reason else None,
                "raw":      decision.strip(),
            })

        print(f"[OK] Parsed {len(rows_out)} valid rows, skipped {skipped}\n")
    except Exception as e:
        print(f"[ERROR] Sheet read failed: {e}")
    return rows_out


def load_today_jobs():
    """Load today_jobs.json for metadata matching on today's jobs."""
    try:
        if os.path.exists(TODAY_JOBS_FILE):
            with open(TODAY_JOBS_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") == TODAY:
                return {str(j.get("number_display", j["number"])): j
                        for j in data.get("jobs", [])}
    except Exception as e:
        print(f"[WARN] Could not load today_jobs.json: {e}")
    return {}


def build_decisions(sheet_rows, today_jobs):
    """
    Merge sheet rows into job_decisions.json structure.

    - Loads existing job_decisions.json
    - For each sheet row:
        * If date already has this job number with a real decision → skip
        * If today + today_jobs available → full metadata record
        * Otherwise → bare-bones record (enough for K-Means)
    - Writes result back to job_decisions.json
    """
    # Load existing
    all_decisions = {}
    if os.path.exists(DECISIONS_FILE):
        with open(DECISIONS_FILE, "r") as f:
            all_decisions = json.load(f)

    # Build a lookup of already-recorded decisions to avoid overwriting
    # {date: {job_num_str: decision_str}}
    existing = {}
    for d, entries in all_decisions.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            num = str(entry.get("number", ""))
            dec = entry.get("decision", "")
            existing.setdefault(d, {})[num] = dec

    # Group sheet rows by date
    by_date = {}
    for row in sheet_rows:
        by_date.setdefault(row["date"], []).append(row)

    new_count      = 0
    updated_count  = 0
    skipped_count  = 0

    for date_str, rows in sorted(by_date.items()):
        if date_str not in all_decisions:
            all_decisions[date_str] = []

        day_entries = all_decisions[date_str]
        # Build index for fast lookup
        entry_index = {str(e.get("number", "")): i
                       for i, e in enumerate(day_entries)}

        for row in rows:
            job_num_str = str(row["job_num"])
            dec         = row["decision"]
            reason      = row["reason"]

            existing_dec = existing.get(date_str, {}).get(job_num_str, "")

            if existing_dec and existing_dec not in ("no_response", "", None):
                # Already has a real decision — don't overwrite
                skipped_count += 1
                continue

            if job_num_str in entry_index:
                # Update existing no_response entry
                idx = entry_index[job_num_str]
                day_entries[idx]["decision"]     = dec
                day_entries[idx]["reason"]       = reason
                day_entries[idx]["raw_decision"] = row["raw"]
                updated_count += 1
                print(f"   [UPDATE] {date_str} Job {job_num_str}: {dec}" +
                      (f" — {reason}" if reason else ""))
            else:
                # No existing entry — create bare-bones record
                # Try to match today's metadata if it's today
                meta = {}
                if date_str == TODAY and job_num_str in today_jobs:
                    j    = today_jobs[job_num_str]
                    meta = {
                        "job_id":           j.get("job_id", ""),
                        "title":            j.get("title", ""),
                        "company":          j.get("company", ""),
                        "track":            j.get("track", ""),
                        "score":            j.get("score", 0),
                        "url":              j.get("url", ""),
                        "matched_keywords": j.get("matched_keywords", []),
                        "source":           j.get("source", ""),
                    }
                else:
                    meta = {
                        "job_id":           "",
                        "title":            f"[no metadata — job {job_num_str} on {date_str}]",
                        "company":          "N/A",
                        "track":            "",
                        "score":            0,
                        "url":              "",
                        "matched_keywords": [],
                        "source":           "",
                    }

                record = {
                    **meta,
                    "number":       row["job_num"],
                    "decision":     dec,
                    "reason":       reason,
                    "raw_decision": row["raw"],
                    "timestamp":    f"{date_str} 00:00",
                    "backfilled":   True,
                }
                day_entries.append(record)
                new_count += 1
                print(f"   [NEW]    {date_str} Job {job_num_str}: {dec}" +
                      (f" — {reason}" if reason else ""))

    # Save
    with open(DECISIONS_FILE, "w") as f:
        json.dump(all_decisions, f, indent=2)

    print(f"\n[OK] Done — {new_count} new records added, "
          f"{updated_count} updated, {skipped_count} already existed")

    # Print summary by date
    print(f"\n{'─'*45}")
    print(f"  job_decisions.json now contains:")
    print(f"{'─'*45}")
    total = 0
    for d in sorted(all_decisions.keys()):
        entries = all_decisions[d]
        if isinstance(entries, list):
            print(f"  {d}: {len(entries)} entries")
            total += len(entries)
    print(f"{'─'*45}")
    print(f"  TOTAL: {total} decisions ({total}/300 toward K-Means)")


if __name__ == "__main__":
    sheet_rows  = read_all_sheet_rows()
    today_jobs  = load_today_jobs()
    build_decisions(sheet_rows, today_jobs)
    print(f"\n[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[NOTE] Delete this file after running — update_scoring.py handles everything going forward.")
