"""
cleanup_backfilled_stubs.py — One-shot cleanup for job_decisions.json
=====================================================================
Deletes the 15 backfilled stub records that were created when Amazon
jobs were not yet being written to today_jobs_YYYY-MM-DD.json
(4/24 - 5/04 window). Those records have:

  - "backfilled": true
  - empty job_id, url, score, matched_keywords
  - title like "[no metadata — job A1 on 2026-04-24]"

Because they have no metadata, they're useless for K-Means training
and just inflate the decision count toward the 200-record threshold.

SAFETY:
  1. Writes a timestamped backup BEFORE touching anything.
  2. Dry-run mode by default — shows what WOULD be deleted, deletes nothing.
  3. Pass --apply to actually delete.

USAGE:
  python cleanup_backfilled_stubs.py             # dry run (default)
  python cleanup_backfilled_stubs.py --apply     # actually delete
"""

import json
import os
import sys
import shutil
from datetime import datetime

SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
DECISIONS_FILE = os.path.join(SCRIPT_DIR, "job_decisions.json")


def is_backfilled_stub(record):
    """
    A record qualifies as a deletable backfilled stub if:
      - The "backfilled" flag is True, OR
      - It looks like a stub: empty job_id AND title starts with "[no metadata"

    Both conditions are checked so we catch stubs even if the flag is missing.
    """
    if not isinstance(record, dict):
        return False
    if record.get("backfilled") is True:
        return True
    if (not record.get("job_id")
            and str(record.get("title", "")).startswith("[no metadata")):
        return True
    return False


def main(apply_changes=False):
    mode = "APPLY" if apply_changes else "DRY RUN"
    print(f"\n{'='*60}")
    print(f"  Backfilled Stub Cleanup — {mode}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if not os.path.exists(DECISIONS_FILE):
        print(f"[ERROR] {DECISIONS_FILE} not found.")
        return 1

    # Load
    with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Inventory before
    total_before = sum(len(v) for v in data.values() if isinstance(v, list))
    print(f"[INFO] Records before: {total_before}")
    print(f"[INFO] Date keys: {len(data)}\n")

    # Find stubs
    to_delete = []   # list of (date_key, index, record)
    for date_key, items in data.items():
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items):
            if is_backfilled_stub(item):
                to_delete.append((date_key, idx, item))

    if not to_delete:
        print("[OK] No backfilled stubs found. Nothing to do.")
        return 0

    print(f"[FOUND] {len(to_delete)} backfilled stub(s):\n")
    print(f"  {'Date':<12} {'Number':<8} {'Title'}")
    print(f"  {'-'*12} {'-'*8} {'-'*40}")
    for date_key, idx, item in to_delete:
        num   = str(item.get("number", ""))
        title = str(item.get("title", ""))[:50]
        print(f"  {date_key:<12} {num:<8} {title}")
    print()

    if not apply_changes:
        print(f"[DRY RUN] Would delete {len(to_delete)} record(s).")
        print(f"[DRY RUN] No changes written.")
        print(f"[DRY RUN] Re-run with --apply to actually delete.\n")
        return 0

    # APPLY mode: backup first
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        SCRIPT_DIR, f"job_decisions.json.bak-cleanup-{timestamp}"
    )
    shutil.copy2(DECISIONS_FILE, backup_path)
    print(f"[BACKUP] Saved backup to:\n  {backup_path}\n")

    # Delete in reverse-index order per date so indices stay valid
    by_date_reverse = {}
    for date_key, idx, _item in to_delete:
        by_date_reverse.setdefault(date_key, []).append(idx)
    for date_key in by_date_reverse:
        by_date_reverse[date_key].sort(reverse=True)

    deleted_count = 0
    for date_key, indices in by_date_reverse.items():
        for idx in indices:
            try:
                del data[date_key][idx]
                deleted_count += 1
            except (KeyError, IndexError) as e:
                print(f"[WARN] Could not delete {date_key}[{idx}]: {e}")

    # Prune any date keys that are now empty lists (purely cosmetic)
    empty_dates = [d for d, items in data.items()
                   if isinstance(items, list) and len(items) == 0]
    for d in empty_dates:
        del data[d]
    if empty_dates:
        print(f"[INFO] Removed {len(empty_dates)} now-empty date key(s): "
              f"{', '.join(empty_dates)}")

    # Write back
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Inventory after
    total_after = sum(len(v) for v in data.values() if isinstance(v, list))
    print(f"\n[OK] Deleted {deleted_count} stub record(s)")
    print(f"[OK] Records after: {total_after} (was {total_before})")
    print(f"[OK] Backup preserved at: {backup_path}\n")
    print(f"[NEXT] git add job_decisions.json && "
          f"git commit -m 'Remove backfilled stub records' && git push")
    return 0


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    sys.exit(main(apply_changes=apply))
