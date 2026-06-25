"""
One-time migration: moves all job-search-pipeline JSON DATA files into a
new json_files/ subfolder, so the main Jobsearch folder only has scripts,
logs, and config in it.

Run this ONLY after job_search.py, review_decisions.py, analyze_decisions.py,
and update_scoring.py have all been updated to read/write json_files/ instead
of the script folder directly (Claude did this on 2026-06-25 -- if you're
running this against a different/older set of scripts, stop and check first).

Moves (if present):
    job_decisions.json
    google_credentials.json
    today_jobs.json
    seen_jobs.json
    job_results.json
    scoring_weights.json
    overnight_summary.json
    today_jobs_YYYY-MM-DD.json      (all legacy date-keyed archives)
    today_jobs_run_*.json           (all run-scoped token-sync archives)
    cluster_analysis_*.json         (any existing K-Means output files)
    archive_today_jobs/             (folder -- merged into json_files/archive_today_jobs/)

Deliberately SKIPPED -- left exactly where they are:
    package.json, package-lock.json   (npm needs these in the project root)
    .env, .gitignore                  (config, not pipeline data)
    *.py, *.bat, *.xml, *.log, *.md   (code/docs/logs, out of scope)
    node_modules/, chroma_db/, logs/  (other directories, out of scope)

Safe to re-run: anything already moved (or never existed) is silently
skipped on a second pass. Moves, never deletes -- nothing here is
destructive.

Run from C:\\Users\\haric\\Jobsearch\\:
    python migrate_to_json_files.py
"""

import os
import re
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(SCRIPT_DIR, "json_files")

# Exact filenames to move, if present
SINGLE_FILES = [
    "job_decisions.json",
    "google_credentials.json",
    "today_jobs.json",
    "seen_jobs.json",
    "job_results.json",
    "scoring_weights.json",
    "overnight_summary.json",
]

# Filename patterns to move (all matches), checked against everything in SCRIPT_DIR
PATTERNS = [
    re.compile(r"^today_jobs_\d{4}-\d{2}-\d{2}\.json$"),   # legacy date-keyed archives
    re.compile(r"^today_jobs_run_.*\.json$"),               # run-scoped token-sync archives
    re.compile(r"^cluster_analysis_.*\.json$"),              # K-Means output, if any exist yet
]

OLD_ARCHIVE_SUBFOLDER = os.path.join(SCRIPT_DIR, "archive_today_jobs")
NEW_ARCHIVE_SUBFOLDER = os.path.join(JSON_DIR, "archive_today_jobs")


def move_one(fname, moved_list, skipped_list):
    src = os.path.join(SCRIPT_DIR, fname)
    dst = os.path.join(JSON_DIR, fname)
    if not os.path.isfile(src):
        return  # already moved or never existed -- nothing to do
    if os.path.exists(dst):
        skipped_list.append(f"{fname} (already exists in json_files/, left source in place -- check manually)")
        return
    shutil.move(src, dst)
    moved_list.append(fname)


def main():
    os.makedirs(JSON_DIR, exist_ok=True)
    moved = []
    skipped = []

    for fname in SINGLE_FILES:
        move_one(fname, moved, skipped)

    for fname in list(os.listdir(SCRIPT_DIR)):
        if any(p.match(fname) for p in PATTERNS):
            move_one(fname, moved, skipped)

    # Merge the existing archive_today_jobs/ folder into json_files/archive_today_jobs/
    if os.path.isdir(OLD_ARCHIVE_SUBFOLDER):
        os.makedirs(NEW_ARCHIVE_SUBFOLDER, exist_ok=True)
        for fname in os.listdir(OLD_ARCHIVE_SUBFOLDER):
            src = os.path.join(OLD_ARCHIVE_SUBFOLDER, fname)
            dst = os.path.join(NEW_ARCHIVE_SUBFOLDER, fname)
            if os.path.exists(dst):
                skipped.append(f"archive_today_jobs/{fname} (already exists in json_files/archive_today_jobs/)")
                continue
            shutil.move(src, dst)
            moved.append(f"archive_today_jobs/{fname}")
        # Remove the now-empty old folder
        try:
            os.rmdir(OLD_ARCHIVE_SUBFOLDER)
        except OSError:
            pass  # not empty for some reason -- leave it, not worth failing the run over

    print(f"Moved {len(moved)} file(s)/item(s) into {JSON_DIR}")
    if skipped:
        print(f"\nSkipped {len(skipped)} item(s) -- review these manually:")
        for s in skipped:
            print(f"  - {s}")
    if not moved and not skipped:
        print("Nothing to move -- migration already complete, or nothing matched.")


if __name__ == "__main__":
    main()
