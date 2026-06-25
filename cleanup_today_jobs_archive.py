"""
One-time cleanup: moves legacy date-keyed today_jobs_YYYY-MM-DD.json files
older than RETENTION_DAYS into an archive_today_jobs/ subfolder inside
json_files/, so that folder isn't cluttered with 50+ daily files.

NOTE: job_search.py now does this automatically at the end of every run
(rotate_legacy_today_jobs_archives()), so this script is mostly redundant
going forward. Kept around for ad-hoc manual cleanup if you ever want it.

Does NOT touch:
  - today_jobs_run_*.json   (token-sync source — review_decisions.py reads these)
  - today_jobs.json         (latest snapshot, no date suffix)
  - job_decisions.json      (permanent K-Means training dataset)

Files are MOVED, not deleted, in case a late form response ever needs one.

Run this once from C:\\Users\\haric\\Jobsearch\\:
    python cleanup_today_jobs_archive.py
"""

import os
import re
import shutil
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(SCRIPT_DIR, "json_files")
ARCHIVE_DIR = os.path.join(JSON_DIR, "archive_today_jobs")
RETENTION_DAYS = 30  # keep this many days of legacy archives in json_files/ directly

DATE_PATTERN = re.compile(r"^today_jobs_(\d{4}-\d{2}-\d{2})\.json$")

def main():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

    moved = 0
    kept = 0
    skipped = []

    for fname in os.listdir(JSON_DIR):
        match = DATE_PATTERN.match(fname)
        if not match:
            continue  # not a legacy date-keyed archive (e.g. today_jobs_run_*.json) — leave alone

        date_str = match.group(1)
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            skipped.append(fname)
            continue

        src = os.path.join(JSON_DIR, fname)
        if file_date < cutoff:
            dst = os.path.join(ARCHIVE_DIR, fname)
            shutil.move(src, dst)
            moved += 1
        else:
            kept += 1

    print(f"Moved {moved} file(s) older than {RETENTION_DAYS} days to {ARCHIVE_DIR}")
    print(f"Kept {kept} file(s) from the last {RETENTION_DAYS} days in place")
    if skipped:
        print(f"Skipped {len(skipped)} file(s) with unparseable dates: {skipped}")

if __name__ == "__main__":
    main()
