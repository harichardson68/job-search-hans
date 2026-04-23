"""
update_scoring.py — Hans Richardson Job Search
================================================
Runs at midnight via Windows Task Scheduler.

Sequence:
  1. git pull          — sync latest code + data from GitHub
  2. Check Gmail       — read replies to today's job search email
  3. Parse decisions   — map reply codes to job_decisions.json
  4. Apply auto-fixes  — update job_search.py + scoring_weights.json
  5. Write summary     — overnight_summary.json (shown in tomorrow's email)
  6. git commit+push   — send everything back to GitHub

Decision codes (user replies with these):
  1 = applied
  2 = bad_link
  3 = too_senior
  4 = salary_too_low
  5 = not_interested
  6 = already_seen
  7 = search_page
  8 = other (followed by reason text)
"""

import os
import sys
import json
import re
import subprocess
import imaplib
import email
from email.header import decode_header
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# ─── SETUP ───────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS", "")

DECISIONS_FILE       = os.path.join(SCRIPT_DIR, "job_decisions.json")
TODAY_JOBS_FILE      = os.path.join(SCRIPT_DIR, "today_jobs.json")
WEIGHTS_FILE         = os.path.join(SCRIPT_DIR, "scoring_weights.json")
JOB_SEARCH_FILE      = os.path.join(SCRIPT_DIR, "job_search.py")
SUMMARY_FILE         = os.path.join(SCRIPT_DIR, "overnight_summary.json")
BACKUP_FILE          = os.path.join(SCRIPT_DIR, "job_search.py.bak")

TODAY = date.today().isoformat()

DECISION_CODES = {
    "1": "applied",
    "2": "bad_link",
    "3": "too_senior",
    "4": "salary_too_low",
    "5": "not_interested",
    "6": "already_seen",
    "7": "search_page",
    "8": "other",
}

print(f"\n{'='*55}")
print(f"  Hans Update Scoring — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*55}\n")

# ─── STEP 1: GIT PULL ────────────────────────────────────────
def git_pull():
    print("[GIT] Pulling latest from GitHub...")
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=SCRIPT_DIR,
            capture_output=True, text=True
        )
        print(f"   {result.stdout.strip() or 'Already up to date.'}")
        if result.returncode != 0:
            print(f"   [WARN] git pull issue: {result.stderr.strip()}")
    except Exception as e:
        print(f"   [WARN] git pull failed: {e}")

# ─── STEP 2: LOAD TODAY'S JOBS ───────────────────────────────
def load_today_jobs():
    try:
        if os.path.exists(TODAY_JOBS_FILE):
            with open(TODAY_JOBS_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") == TODAY:
                return {j["number"]: j for j in data.get("jobs", [])}
            else:
                print(f"   [WARN] today_jobs.json is from {data.get('date')} not today — skipping decisions")
                return {}
    except Exception as e:
        print(f"   [WARN] Could not load today_jobs.json: {e}")
    return {}

# ─── STEP 3: CHECK GMAIL FOR REPLIES ─────────────────────────
def check_gmail_replies(today_jobs):
    """
    Connects to Gmail via IMAP, finds replies to today's job search email,
    parses decision codes, returns dict of {job_number: {decision, reason}}.
    """
    decisions = {}
    if not GMAIL_ADDRESS or not GMAIL_APP_PASS:
        print("   [WARN] Gmail credentials not set — skipping reply check")
        return decisions

    print("[GMAIL] Checking for reply decisions...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        mail.select("inbox")

        # Search for emails received today with "Job Search Results" in subject
        today_str = date.today().strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{today_str}" SUBJECT "Job Search Results")')

        if status != "OK" or not messages[0]:
            print("   [INFO] No job search reply emails found today")
            mail.logout()
            return decisions

        email_ids = messages[0].split()
        print(f"   Found {len(email_ids)} related email(s)")

        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            # Parse lines like "Job 1: 1" or "Job 3: 8 bad location - brussels"
            for line in body.splitlines():
                line = line.strip()
                match = re.match(r"(?i)job\s+(\d+)\s*:\s*(\d)(.*)$", line)
                if match:
                    job_num  = int(match.group(1))
                    code     = match.group(2).strip()
                    extra    = match.group(3).strip()
                    decision = DECISION_CODES.get(code, "unknown")
                    reason   = extra if decision == "other" and extra else None
                    decisions[job_num] = {"decision": decision, "reason": reason}
                    print(f"   Job {job_num}: {decision}" + (f" — {reason}" if reason else ""))

        mail.logout()
    except Exception as e:
        print(f"   [ERROR] Gmail check failed: {e}")

    return decisions

# ─── STEP 4: WRITE JOB DECISIONS ─────────────────────────────
def save_decisions(today_jobs, decisions):
    try:
        if os.path.exists(DECISIONS_FILE):
            with open(DECISIONS_FILE, "r") as f:
                all_decisions = json.load(f)
        else:
            all_decisions = {}

        today_entries = []
        for job_num, job in today_jobs.items():
            dec = decisions.get(job_num, {})
            entry = {
                "job_id":           job.get("job_id", ""),
                "number":           job_num,
                "title":            job.get("title", ""),
                "company":          job.get("company", ""),
                "track":            job.get("track", ""),
                "score":            job.get("score", 0),
                "url":              job.get("url", ""),
                "matched_keywords": job.get("matched_keywords", []),
                "source":           job.get("source", ""),
                "decision":         dec.get("decision", "no_response"),
                "reason":           dec.get("reason", None),
                "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            today_entries.append(entry)

        all_decisions[TODAY] = today_entries
        with open(DECISIONS_FILE, "w") as f:
            json.dump(all_decisions, f, indent=2)
        print(f"[OK] Saved {len(today_entries)} decisions to job_decisions.json")
        return today_entries
    except Exception as e:
        print(f"[ERROR] Could not save decisions: {e}")
        return []

# ─── STEP 5: LOAD SCORING WEIGHTS ────────────────────────────
def load_weights():
    defaults = {
        "loadrunner_title_bonus":    50,
        "loadrunner_desc_bonus":     50,
        "performance_high_score":    35,
        "ai_engineering_score":      20,
        "cobol_score":                2,
        "boosted_keywords":          [],
        "downweighted_keywords":     [],
        "auto_blocked_sites":        [],
        "auto_blocked_companies":    [],
        "auto_blocked_locations":    [],
        "applied_tracks":            {},
        "skipped_tracks":            {},
        "total_applied":              0,
        "total_skipped":              0,
        "last_updated":              "",
    }
    try:
        if os.path.exists(WEIGHTS_FILE):
            with open(WEIGHTS_FILE, "r") as f:
                saved = json.load(f)
            defaults.update(saved)
    except Exception:
        pass
    return defaults

def save_weights(weights):
    weights["last_updated"] = datetime.now().isoformat()
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=2)
    print(f"[OK] Updated scoring_weights.json")

# ─── STEP 6: APPLY FEEDBACK TO WEIGHTS ───────────────────────
def apply_feedback(entries, weights):
    auto_handled  = []
    needs_review  = []

    for entry in entries:
        decision = entry.get("decision", "no_response")
        reason   = entry.get("reason", "") or ""
        keywords = entry.get("matched_keywords", [])
        track    = entry.get("track", "")
        company  = entry.get("company", "").lower().strip()
        url      = entry.get("url", "").lower().strip()

        if decision == "applied":
            weights["total_applied"] += 1
            weights["applied_tracks"][track] = weights["applied_tracks"].get(track, 0) + 1
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in weights["boosted_keywords"]:
                    weights["boosted_keywords"].append(kw_lower)
                    auto_handled.append(f"Boosted keyword: '{kw_lower}'")

        elif decision in ("not_interested", "too_senior", "salary_too_low", "already_seen", "search_page"):
            weights["total_skipped"] += 1
            weights["skipped_tracks"][track] = weights["skipped_tracks"].get(track, 0) + 1

        elif decision == "bad_link":
            weights["total_skipped"] += 1
            # Extract domain from URL and auto-block it
            domain_match = re.search(r"https?://([^/]+)", url)
            if domain_match:
                domain = domain_match.group(1)
                if domain not in weights["auto_blocked_sites"]:
                    weights["auto_blocked_sites"].append(domain)
                    auto_handled.append(f"Auto-blocked site: '{domain}'")

        elif decision == "other" and reason:
            reason_lower = reason.lower()

            # Detect location patterns: "bad location - brussels" or "overseas - india"
            loc_match = re.search(r"(?:bad location|overseas|wrong location|location)[:\s\-]+(.+)", reason_lower)
            if loc_match:
                location = loc_match.group(1).strip().rstrip(".")
                if location and location not in weights["auto_blocked_locations"]:
                    weights["auto_blocked_locations"].append(location)
                    auto_handled.append(f"Auto-blocked location: '{location}'")
            # Detect company patterns: "bad company - xyz"
            elif re.search(r"(?:bad company|sketchy|scam|body shop)[:\s\-]+(.+)", reason_lower):
                co_match = re.search(r"(?:bad company|sketchy|scam|body shop)[:\s\-]+(.+)", reason_lower)
                if co_match:
                    co = co_match.group(1).strip()
                    if co not in weights["auto_blocked_companies"]:
                        weights["auto_blocked_companies"].append(co)
                        auto_handled.append(f"Auto-blocked company: '{co}'")
            else:
                # Can't auto-handle — flag for manual review
                needs_review.append(f"Job '{entry.get('title','?')}': {reason}")

        elif decision == "no_response":
            pass  # Neutral — no action

    return auto_handled, needs_review

# ─── STEP 7: PATCH JOB_SEARCH.PY ─────────────────────────────
def patch_job_search(weights):
    """Surgically update the blocklists in job_search.py based on weights."""
    if not os.path.exists(JOB_SEARCH_FILE):
        print(f"   [WARN] {JOB_SEARCH_FILE} not found — skipping patch")
        return False

    # Backup first
    import shutil
    shutil.copy2(JOB_SEARCH_FILE, BACKUP_FILE)

    with open(JOB_SEARCH_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False

    # ── Auto-blocked locations → NON_US_LOCATIONS ────────────
    for loc in weights.get("auto_blocked_locations", []):
        if f'"{loc}"' not in content and f"'{loc}'" not in content:
            # Find the NON_US_LOCATIONS list and append before closing bracket
            pattern = r'(NON_US_LOCATIONS\s*=\s*\[.*?)(]\s*\n)'
            def add_location(m):
                return m.group(1) + f'    "{loc}",\n' + m.group(2)
            new_content = re.sub(pattern, add_location, content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                changed = True
                print(f"   [PATCH] Added '{loc}' to NON_US_LOCATIONS")

    # ── Auto-blocked sites → BLOCKED_JOB_SITES ───────────────
    for site in weights.get("auto_blocked_sites", []):
        if f'"{site}"' not in content:
            pattern = r'(BLOCKED_JOB_SITES\s*=\s*\[.*?)(]\s*\n)'
            def add_site(m):
                return m.group(1) + f'    "{site}",\n' + m.group(2)
            new_content = re.sub(pattern, add_site, content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                changed = True
                print(f"   [PATCH] Added '{site}' to BLOCKED_JOB_SITES")

    # ── Auto-blocked companies → blocked_companies ────────────
    for co in weights.get("auto_blocked_companies", []):
        if f'"{co}"' not in content:
            pattern = r'(blocked_companies\s*=\s*\[.*?)(]\s*\n)'
            def add_company(m):
                return m.group(1) + f'    "{co}",\n' + m.group(2)
            new_content = re.sub(pattern, add_company, content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                changed = True
                print(f"   [PATCH] Added '{co}' to blocked_companies")

    if changed:
        with open(JOB_SEARCH_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] job_search.py patched successfully")
    else:
        print(f"[OK] No patches needed for job_search.py")

    return changed

# ─── STEP 8: WRITE OVERNIGHT SUMMARY ─────────────────────────
def write_summary(entries, auto_handled, needs_review, git_committed):
    decisions_received = sum(1 for e in entries if e.get("decision") != "no_response")
    no_response        = sum(1 for e in entries if e.get("decision") == "no_response")
    summary = {
        "date":               TODAY,
        "jobs_sent":          len(entries),
        "decisions_received": decisions_received,
        "no_response":        no_response,
        "auto_handled":       auto_handled,
        "needs_review":       needs_review,
        "git_committed":      "Yes" if git_committed else "No",
        "generated_at":       datetime.now().isoformat(),
    }
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Overnight summary written")
    return summary

# ─── STEP 9: GIT COMMIT + PUSH ───────────────────────────────
def git_commit_push(auto_handled, needs_review):
    print("[GIT] Committing and pushing updates...")
    try:
        subprocess.run(["git", "add", "."], cwd=SCRIPT_DIR, check=True)
        changes_summary = f"{len(auto_handled)} auto-fixes" if auto_handled else "decisions recorded"
        commit_msg = f"Auto-update {TODAY}: {changes_summary}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=SCRIPT_DIR, capture_output=True, text=True
        )
        if "nothing to commit" in result.stdout:
            print("   [INFO] Nothing to commit — no changes detected")
            return False
        subprocess.run(["git", "push"], cwd=SCRIPT_DIR, check=True)
        print(f"   [OK] Pushed: '{commit_msg}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   [ERROR] Git operation failed: {e}")
        return False

# ─── MAIN ────────────────────────────────────────────────────
def main():
    # 1. Sync from GitHub
    git_pull()

    # 2. Load today's sent jobs
    today_jobs = load_today_jobs()
    if not today_jobs:
        print("[INFO] No jobs found for today — nothing to process")
        write_summary([], [], [], False)
        return

    print(f"[OK] Loaded {len(today_jobs)} jobs from today_jobs.json")

    # 3. Check Gmail for replies
    decisions = check_gmail_replies(today_jobs)
    print(f"[OK] Parsed {len(decisions)} decision(s) from email replies")

    # 4. Save decisions to job_decisions.json
    entries = save_decisions(today_jobs, decisions)

    # 5. Load scoring weights
    weights = load_weights()

    # 6. Apply feedback
    auto_handled, needs_review = apply_feedback(entries, weights)
    print(f"[OK] Auto-handled: {len(auto_handled)} | Needs review: {len(needs_review)}")
    for item in auto_handled:
        print(f"   ✓ {item}")
    for item in needs_review:
        print(f"   ⚠ {item}")

    # 7. Save updated weights
    save_weights(weights)

    # 8. Patch job_search.py
    patch_job_search(weights)

    # 9. Write overnight summary
    git_committed = git_commit_push(auto_handled, needs_review)
    write_summary(entries, auto_handled, needs_review, git_committed)

    print(f"\n[DONE] Update scoring completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n[FATAL] Unhandled exception:")
        print(traceback.format_exc())
