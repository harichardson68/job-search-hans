"""
review_decisions.py — Hans Richardson Job Search
=================================================
Runs every Monday and Thursday at 10:00 AM via Windows Task Scheduler.

Replaces weekly_review.py. Reads decisions directly from job_decisions.json
(no more needs_review.json) and surfaces "other" decisions you haven't
reviewed yet, so we can pattern-match them into job_search.py improvements.

Workflow per run:
  1. git pull (abort + email + log on failure)
  2. Read job_decisions.json across all dates
  3. Filter entries: decision == "other" AND reviewed != true
  4. Map free-text reasons to categories via REASON_CATEGORY_MAP
  5. Send HTML digest grouped by category
  6. Mark each surfaced entry with reviewed: true + reviewed_date
  7. git add/commit/push the updated job_decisions.json

Logging:
  - review_decisions_run.log   (overwrite each run, full per-run trace)
  - jobsearch_errors.log       (append, shared with job_search.py for
                                persistent error history across runs)
"""

import os
import sys
import json
import smtplib
import subprocess
import traceback
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# ─── PATHS & ENV ─────────────────────────────────────────────
SCRIPT_DIR         = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASS     = os.environ.get("GMAIL_APP_PASS", "")
EMAIL_TO           = os.environ.get("EMAIL_TO", GMAIL_ADDRESS)

DECISIONS_FILE     = os.path.join(SCRIPT_DIR, "job_decisions.json")
RUN_LOG_FILE       = os.path.join(SCRIPT_DIR, "review_decisions_run.log")
ERROR_LOG_FILE     = os.path.join(SCRIPT_DIR, "jobsearch_errors.log")

TODAY              = date.today().isoformat()
SCRIPT_NAME        = "review_decisions.py"

# ─── LOGGING SETUP (same DualLogger pattern as job_search.py) ─
class DualLogger:
    """Writes to both console and per-run log file simultaneously."""
    def __init__(self, log_path):
        self.console = sys.__stdout__
        try:
            self.logfile = open(log_path, "w", encoding="utf-8")
            self._has_log = True
        except Exception as e:
            self.logfile = None
            self._has_log = False
            self.console.write(f"[WARN] Could not open log file: {e}\n")
    def write(self, message):
        self.console.write(message)
        if self._has_log:
            self.logfile.write(message)
            self.logfile.flush()
    def flush(self):
        self.console.flush()
        if self._has_log and self.logfile:
            self.logfile.flush()

sys.stdout = DualLogger(RUN_LOG_FILE)


def log_error(message):
    """Append a timestamped error to the shared persistent error log."""
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] [{SCRIPT_NAME}] {message}\n")
    except Exception as e:
        print(f"[WARN] Could not write to {ERROR_LOG_FILE}: {e}")


print(f"\n{'='*60}")
print(f"  Review Decisions Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")


# ─── REASON → CATEGORY MAPPING ───────────────────────────────
# Seeded from 4/23/2026 decision data.
# Order matters: first match wins. Add new patterns at the top
# as they emerge from review cycles.
REASON_CATEGORY_MAP = [
    ("clearance",        "clearance"),    # "Secret clearance", "TS clearance", etc.
    ("domain suspended", "bad_link"),
    ("job not found",    "bad_link"),
    ("404",              "bad_link"),
    ("dead link",        "bad_link"),
    ("page not found",   "bad_link"),
    ("not remote",       "onsite"),
    ("on site",          "onsite"),
    ("on-site",          "onsite"),
    ("onsite",           "onsite"),
    ("hybrid",           "onsite"),
    ("jmeter",           "jmeter_only"),
    ("not in us",        "not_in_us"),
    ("not in united",    "not_in_us"),
    ("overseas",         "not_in_us"),
    ("too senior",       "too_senior"),
    ("salary",           "salary"),
    ("pay too low",      "salary"),
]

# Display config for each category in the email
CATEGORY_CONFIG = {
    "other":        {"label": "Other / Unclassified",      "color": "#6c5ce7"},
    "bad_link":     {"label": "Dead Links / Bad URLs",     "color": "#c0392b"},
    "clearance":    {"label": "Clearance Required",        "color": "#d35400"},
    "onsite":       {"label": "Onsite / Not Remote",       "color": "#e17055"},
    "not_in_us":    {"label": "Not in United States",      "color": "#0984e3"},
    "jmeter_only":  {"label": "JMeter-Only (No LoadRunner)","color": "#00b894"},
    "too_senior":   {"label": "Too Senior",                "color": "#fdcb6e"},
    "salary":       {"label": "Salary Too Low",            "color": "#a29bfe"},
    "unknown":      {"label": "Uncategorized",             "color": "#636e72"},
}


def categorize_reason(reason_text):
    """Map a free-text reason to a category code. Returns 'other' if no match."""
    if not reason_text:
        return "other"
    r = str(reason_text).lower()
    for keyword, category in REASON_CATEGORY_MAP:
        if keyword in r:
            return category
    return "other"


# ─── GIT OPERATIONS ──────────────────────────────────────────
def git_pull_or_abort():
    """
    Pull latest from GitHub before running. If pull fails, send an alert
    email and abort the run — we don't want to operate on stale code or
    create divergent state.
    """
    print("[GIT] Pulling latest from GitHub...")
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "unknown error").strip()
            raise RuntimeError(f"git pull returned {result.returncode}: {err}")
        print(f"   [OK] {result.stdout.strip() or 'Up to date.'}")
        return True
    except Exception as e:
        msg = f"git pull failed: {e}"
        print(f"   [FATAL] {msg}")
        log_error(msg)
        send_failure_alert("git pull failed", str(e))
        return False


def git_commit_push():
    """Commit and push the updated job_decisions.json after a successful send."""
    print("[GIT] Committing and pushing updated job_decisions.json...")
    try:
        subprocess.run(["git", "add", "-A"], cwd=SCRIPT_DIR, check=True)
        commit_msg = f"Review decisions sent — items marked reviewed — {TODAY}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=SCRIPT_DIR, capture_output=True, text=True
        )
        if "nothing to commit" in (result.stdout + result.stderr).lower():
            print("   [INFO] Nothing to commit")
            return
        subprocess.run(["git", "push"], cwd=SCRIPT_DIR, check=True)
        print(f"   [OK] Pushed: '{commit_msg}'")
    except subprocess.CalledProcessError as e:
        msg = f"git commit/push failed: {e}"
        print(f"   [ERROR] {msg}")
        log_error(msg)


# ─── DATA LOAD / FILTER / SAVE ───────────────────────────────
def load_decisions():
    """Load the full job_decisions.json file."""
    if not os.path.exists(DECISIONS_FILE):
        print(f"[WARN] {DECISIONS_FILE} does not exist yet — nothing to review.")
        return {}
    try:
        with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        msg = f"Could not load {DECISIONS_FILE}: {e}"
        print(f"[ERROR] {msg}")
        log_error(msg)
        return {}


def collect_pending_items(decisions_data):
    """
    Walk the decisions file and return a flat list of (date_key, item_index, item)
    for entries that are decision=='other' AND not yet reviewed.

    Returns the index so we can write reviewed:true back into the right slot.
    """
    pending = []
    for date_key, day_items in decisions_data.items():
        if not isinstance(day_items, list):
            continue
        for idx, item in enumerate(day_items):
            if not isinstance(item, dict):
                continue
            if item.get("decision") != "other":
                continue
            if item.get("reviewed") is True:
                continue
            # Tag with date so the email shows when it was decided
            enriched = dict(item)
            enriched["_date"] = date_key
            enriched["_category"] = categorize_reason(item.get("reason"))
            pending.append((date_key, idx, enriched))
    return pending


def group_by_category(pending_items):
    """Group pending items by their derived category."""
    groups = {}
    for _date_key, _idx, item in pending_items:
        cat = item.get("_category", "other")
        groups.setdefault(cat, []).append(item)
    return groups


def mark_items_reviewed(decisions_data, pending_items):
    """
    Mutate decisions_data in place — set reviewed:true and reviewed_date
    on each pending item, then save back to disk.
    """
    count = 0
    for date_key, idx, _item in pending_items:
        try:
            decisions_data[date_key][idx]["reviewed"] = True
            decisions_data[date_key][idx]["reviewed_date"] = TODAY
            count += 1
        except (KeyError, IndexError) as e:
            print(f"[WARN] Could not flag entry {date_key}[{idx}]: {e}")

    try:
        with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(decisions_data, f, indent=2)
        print(f"[OK] Marked {count} entry/entries as reviewed in job_decisions.json")
    except Exception as e:
        msg = f"Could not save {DECISIONS_FILE}: {e}"
        print(f"[ERROR] {msg}")
        log_error(msg)


# ─── EMAIL: SUCCESS DIGEST ───────────────────────────────────
def build_email(pending_items, groups):
    """Build the HTML review digest."""
    total = len(pending_items)

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;color:#333;">
<div style="background:#1F3864;color:white;padding:20px 24px;border-radius:8px 8px 0 0;margin-bottom:0;">
  <h2 style="margin:0;font-size:20px;">Job Search Decision Review</h2>
  <p style="margin:6px 0 0;font-size:13px;opacity:0.85;">Run date {TODAY} &nbsp;|&nbsp; {total} unreviewed "Other" decision(s)</p>
</div>

<div style="background:#f0f4ff;border:1px solid #c5d0e8;border-top:none;padding:14px 24px;margin-bottom:20px;border-radius:0 0 8px 8px;">
  <p style="margin:0;font-size:13px;color:#444;">
    These are the decisions where you marked "Other" with a free-text reason.
    Use the patterns here to drive job_search.py filter improvements with Claude.
    <strong>After this email is sent, each entry below will be flagged reviewed:true in job_decisions.json (data is preserved for K-Means).</strong>
  </p>
</div>"""

    if total == 0:
        html += """
<div style="background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;padding:20px;text-align:center;">
  <p style="margin:0;color:#155724;font-size:16px;font-weight:bold;">No new "Other" decisions to review!</p>
  <p style="margin:8px 0 0;color:#155724;font-size:13px;">All decisions have been categorized or already reviewed. Nice and clean.</p>
</div>"""
    else:
        # Summary table
        html += """<table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
  <tr style="background:#f8f9fa;">
    <th style="text-align:left;padding:8px 12px;font-size:12px;color:#555;border-bottom:2px solid #dee2e6;">Category</th>
    <th style="text-align:right;padding:8px 12px;font-size:12px;color:#555;border-bottom:2px solid #dee2e6;">Count</th>
  </tr>"""
        for cat, cat_items in sorted(groups.items(), key=lambda x: -len(x[1])):
            cfg = CATEGORY_CONFIG.get(cat, CATEGORY_CONFIG["unknown"])
            html += f"""
  <tr>
    <td style="padding:8px 12px;font-size:13px;border-bottom:1px solid #f0f0f0;">
      <span style="display:inline-block;width:10px;height:10px;background:{cfg['color']};border-radius:50%;margin-right:6px;"></span>
      {cfg['label']}
    </td>
    <td style="text-align:right;padding:8px 12px;font-size:13px;font-weight:bold;border-bottom:1px solid #f0f0f0;">{len(cat_items)}</td>
  </tr>"""
        html += "</table>"

        # Detail sections by category
        for cat, cat_items in sorted(groups.items(), key=lambda x: -len(x[1])):
            cfg = CATEGORY_CONFIG.get(cat, CATEGORY_CONFIG["unknown"])
            html += f"""
<div style="margin-bottom:24px;">
  <h3 style="color:{cfg['color']};border-bottom:2px solid {cfg['color']};padding-bottom:6px;font-size:15px;margin-bottom:12px;">
    {cfg['label']} ({len(cat_items)})
  </h3>"""
            for item in cat_items:
                title   = item.get("title", "Unknown Job")
                reason  = item.get("reason", "No reason provided")
                track   = item.get("track", "")
                url     = item.get("url", "")
                dt      = item.get("_date", "")
                job_id  = item.get("job_id", "")
                source  = item.get("source", "")

                html += f"""
  <div style="background:#f9f9f9;border:1px solid #e0e0e0;border-left:4px solid {cfg['color']};border-radius:4px;padding:12px 14px;margin-bottom:10px;">
    <p style="margin:0 0 4px;font-weight:bold;font-size:13px;color:#222;">{title}</p>
    <p style="margin:0 0 4px;font-size:12px;color:#666;">
      Track: {track} &nbsp;|&nbsp; Source: {source} &nbsp;|&nbsp; Decided: {dt} &nbsp;|&nbsp;
      <span style="font-family:monospace;font-size:11px;">ID: {job_id}</span>
    </p>
    <p style="margin:0 0 6px;font-size:12px;color:#444;"><strong>Reason:</strong> {reason}</p>
    {f'<a href="{url}" style="font-size:11px;color:#1F3864;">View Job →</a>' if url else ''}
  </div>"""
            html += "</div>"

    html += f"""
<div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:12px 16px;margin-top:8px;">
  <p style="margin:0 0 4px;font-weight:bold;color:#1b5e20;font-size:12px;">Data Retention</p>
  <p style="margin:0;font-size:11px;color:#2e7d32;">
    <strong>job_decisions.json</strong> — surfaced entries flagged reviewed:true (data preserved permanently) ✓<br>
    <strong>K-Means milestone:</strong> after ~200+ total decisions (4-6 weeks), run analyze_decisions.py to discover hidden job patterns.
  </p>
</div>

<hr style="margin:16px 0;border:none;border-top:1px solid #eee;"/>
<p style="font-size:11px;color:#aaa;text-align:center;">
  Hans Richardson Job Search Decision Review &nbsp;·&nbsp; Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;·&nbsp; Mon + Thu cadence
</p>
</body></html>"""

    return html


def send_review_email(html, total):
    """Send the digest email with full job_decisions.json attached as backup."""
    if total == 0:
        subject = f"Decision Review — Nothing new to review — {TODAY}"
    else:
        subject = f"Decision Review — {total} 'Other' item(s) to review — {TODAY}"

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"]    = f"Job Search Review <{GMAIL_ADDRESS}>"
        msg["To"]      = EMAIL_TO

        msg.attach(MIMEText(html, "html"))

        # Attach full job_decisions.json as disaster-recovery backup
        if os.path.exists(DECISIONS_FILE):
            with open(DECISIONS_FILE, "rb") as f:
                attachment = MIMEBase("application", "octet-stream")
                attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename=job_decisions_{TODAY}.json"
            )
            msg.attach(attachment)
            print(f"   [OK] Attached job_decisions_{TODAY}.json (backup)")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, EMAIL_TO, msg.as_string())
        print(f"[OK] Review email sent to {EMAIL_TO}")
        return True
    except Exception as e:
        msg = f"Email send failed: {e}"
        print(f"[ERROR] {msg}")
        log_error(msg)
        return False


# ─── EMAIL: FAILURE ALERT ────────────────────────────────────
def send_failure_alert(reason_short, error_detail):
    """Send a fatal-error alert email when something prevents the run from completing."""
    try:
        subject = f"[ALERT] {SCRIPT_NAME} aborted — {reason_short} — {TODAY}"
        body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<div style="background:#c0392b;color:white;padding:16px 20px;border-radius:6px;">
  <h2 style="margin:0;font-size:18px;">Run Aborted: {SCRIPT_NAME}</h2>
  <p style="margin:6px 0 0;font-size:12px;opacity:0.9;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
<div style="padding:16px 20px;background:#fff5f5;border:1px solid #f5c6cb;border-top:none;border-radius:0 0 6px 6px;">
  <p style="margin:0 0 8px;"><strong>Reason:</strong> {reason_short}</p>
  <p style="margin:0 0 8px;"><strong>Detail:</strong></p>
  <pre style="background:#f8f9fa;padding:10px;border-radius:4px;font-size:11px;white-space:pre-wrap;">{error_detail}</pre>
  <p style="margin:12px 0 0;font-size:12px;color:#555;">
    See <code>jobsearch_errors.log</code> for the full persistent error history.
  </p>
</div>
</body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Job Search Alert <{GMAIL_ADDRESS}>"
        msg["To"]      = EMAIL_TO
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, EMAIL_TO, msg.as_string())
        print(f"[OK] Failure alert email sent to {EMAIL_TO}")
    except Exception as e:
        # If even the alert email fails, at least log it
        log_error(f"Could not send failure alert email: {e}")
        print(f"[ERROR] Could not send failure alert: {e}")


# ─── MAIN ────────────────────────────────────────────────────
def main():
    # 1. Pull latest from GitHub before doing anything
    if not git_pull_or_abort():
        print("[ABORT] Run halted due to git pull failure.")
        return

    # 2. Load and filter
    decisions_data = load_decisions()
    pending = collect_pending_items(decisions_data)
    print(f"[OK] Found {len(pending)} unreviewed 'Other' decision(s) in job_decisions.json")

    # 3. Group + build + send
    groups = group_by_category(pending)
    html = build_email(pending, groups)
    sent = send_review_email(html, len(pending))

    # 4. Mark reviewed + push only on successful send
    if sent and pending:
        mark_items_reviewed(decisions_data, pending)
        git_commit_push()
    elif sent:
        print("[INFO] Empty digest sent — nothing to flag, nothing to push.")

    print(f"\n[DONE] Review run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        print(f"\n[FATAL] {tb}")
        log_error(f"FATAL unhandled exception: {e}\n{tb}")
        send_failure_alert("unhandled exception", tb)
