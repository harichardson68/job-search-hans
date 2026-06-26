"""
Automated Job Search Script for Hans Richardson - Performance Engineer
Searches: RemoteOK, Remotive, Working Nomads, Serper (Google Jobs), Adzuna, USAJobs, Wellfound, Amazon Jobs
Targets: LoadRunner, JMeter, NeoLoad, Performance Engineer, AI/Agentic, COBOL (Remote)

SETUP:
    pip install requests feedparser python-dateutil anthropic python-dotenv

OPTIONAL API KEYS (free tiers available):
    - Adzuna: https://developer.adzuna.com/  (free, ~1000 calls/day)
    - USAJobs: https://developer.usajobs.gov/ (free, requires registration)
    - Serper: https://serper.dev (free, 2,500 searches/month)
    - Claude: https://console.anthropic.com (for cover letters & fit analysis)
"""

import requests
import feedparser
import json
import re
import os
import time
import hashlib
import urllib.parse
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
import logging
import sys
from dotenv import load_dotenv

# Load .env file from same directory as this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR   = os.path.join(SCRIPT_DIR, "json_files")  # all pipeline data .json files live here
os.makedirs(JSON_DIR, exist_ok=True)
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

# ─── RAG SETUP (ChromaDB + sentence-transformers) ────────────
CHROMA_DIR      = os.path.join(SCRIPT_DIR, "chroma_db")
DECISIONS_FILE  = os.path.join(JSON_DIR, "job_decisions.json")
RAG_ENABLED     = True
RAG_TOP_K       = 3

# ─── JOB DECISION TOKEN SYNC ──────────────────────────────────
# Per-run, per-job opaque tokens that get baked directly into a
# pre-filled Google Form link in the email, instead of relying on
# Hans typing in a date + job number by hand. This fixes two real bugs
# found in the old (date_str, job_number) matching scheme:
#   1. Same-day reruns overwrote today_jobs_{date}.json, silently
#      orphaning/misrouting any pending decision from an earlier run.
#   2. review_decisions.py derived "date_str" from the FORM SUBMISSION
#      timestamp, not the email's date -- so any decision submitted a
#      day (or more) after the email was sent could resolve to the
#      wrong job entirely, not just fail to match.
# A token is unique per (run_id, job_number) regardless of how many
# times the script runs per day or how late the response comes in.
FORM_BASE_URL         = "https://docs.google.com/forms/d/e/1FAIpQLScWITASM6c25lmv7f6RrGAyUizh6Dz7UIijfTBg7WBSUlJ6Cg/viewform"
FORM_ENTRY_JOB_NUMBER = "1727644971"   # "Job Number" field entry ID
FORM_ENTRY_JOB_TOKEN  = "1012235280"   # "Job Token" field entry ID
RUN_ARCHIVE_PREFIX    = "today_jobs_run_"  # one file per run, never overwritten

# Legacy date-keyed archives (today_jobs_YYYY-MM-DD.json) pile up forever
# with no cleanup. They're only kept for backward compat with any decision
# email sent before the token system existed -- once that buffer has long
# passed, they're just clutter in the main Jobsearch folder. Rotate (move,
# never delete) anything older than the retention window into a subfolder
# once per run, so the folder stays readable without losing any history.
LEGACY_ARCHIVE_RETENTION_DAYS = 30
LEGACY_ARCHIVE_SUBFOLDER      = "archive_today_jobs"
LEGACY_ARCHIVE_PATTERN        = re.compile(r"^today_jobs_(\d{4}-\d{2}-\d{2})\.json$")


def rotate_legacy_today_jobs_archives():
    """Move legacy date-keyed today_jobs_YYYY-MM-DD.json files older than
    LEGACY_ARCHIVE_RETENTION_DAYS into archive_today_jobs/. Never touches
    today_jobs_run_*.json (token-sync source) or today_jobs.json (latest
    snapshot). Moves rather than deletes -- cheap to keep, expensive to
    regret. Wrapped in try/except by the caller so a filesystem hiccup
    here never breaks the actual job search run."""
    archive_dir = os.path.join(JSON_DIR, LEGACY_ARCHIVE_SUBFOLDER)
    cutoff = datetime.now() - timedelta(days=LEGACY_ARCHIVE_RETENTION_DAYS)

    moved = 0
    for fname in os.listdir(JSON_DIR):
        match = LEGACY_ARCHIVE_PATTERN.match(fname)
        if not match:
            continue
        try:
            file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            os.makedirs(archive_dir, exist_ok=True)
            _shutil.move(os.path.join(JSON_DIR, fname), os.path.join(archive_dir, fname))
            moved += 1

    if moved:
        print(f"[OK] Rotated {moved} legacy today_jobs archive(s) older than "
              f"{LEGACY_ARCHIVE_RETENTION_DAYS} days into {LEGACY_ARCHIVE_SUBFOLDER}/")


def generate_run_id():
    """One run_id per job_search.py execution -- includes seconds so
    multiple runs in the same day (or same minute) still get distinct
    archive files instead of overwriting each other."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_job_token(run_id, job_number):
    """Short, opaque, globally-unique token for one job in one run.
    Deliberately not human-readable -- nothing meaningful to mis-type,
    and if it ever does get garbled in transit, the lookup just fails
    to match (loud, logged) rather than silently resolving to the
    wrong job."""
    raw = f"{run_id}:{job_number}"
    return hashlib.sha256(raw.encode()).hexdigest()[:10]


def build_decision_link(run_id, job_number):
    """Pre-filled Google Form URL carrying both the job number and the
    token, so Hans doesn't have to type either one by hand."""
    token = make_job_token(run_id, job_number)
    params = {
        f"entry.{FORM_ENTRY_JOB_NUMBER}": str(job_number),
        f"entry.{FORM_ENTRY_JOB_TOKEN}":  token,
        "usp": "pp_url",
    }
    return f"{FORM_BASE_URL}?{urllib.parse.urlencode(params)}"

class JobRAG:
    """
    Lightweight RAG layer over job_decisions.json.
    Embeds past decisions into ChromaDB on each run,
    ready for similarity retrieval once enough data exists.
    """
    def __init__(self):
        self._client     = None
        self._collection = None
        self._model      = None
        self._ready      = False

    def _init(self):
        if self._ready:
            return True
        try:
            from sentence_transformers import SentenceTransformer
            import chromadb
            self._model      = SentenceTransformer("all-MiniLM-L6-v2")
            self._client     = chromadb.PersistentClient(path=CHROMA_DIR)
            self._collection = self._client.get_or_create_collection(
                name="job_decisions",
                metadata={"hnsw:space": "cosine"},
            )
            self._ready = True
            return True
        except Exception as e:
            print(f"   [WARN] RAG init failed: {e}")
            return False

    def ingest_decisions(self):
        """
        Upsert all decisions from job_decisions.json into ChromaDB.
        Called once per nightly run after email is sent.
        """
        if not RAG_ENABLED or not self._init():
            return
        try:
            if not os.path.exists(DECISIONS_FILE):
                return
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                all_decisions = json.load(f)

            ids, docs, metas = [], [], []
            for date_str, entries in all_decisions.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    job_id = entry.get("job_id", "")
                    if not job_id:
                        continue
                    text = " ".join(filter(None, [
                        entry.get("title", ""),
                        entry.get("track", ""),
                        " ".join(entry.get("matched_keywords", [])),
                    ]))
                    if not text.strip():
                        continue
                    ids.append(job_id)
                    docs.append(text[:500])
                    metas.append({
                        "title":    entry.get("title", "")[:100],
                        "decision": entry.get("decision", "unknown"),
                        "reason":   entry.get("reason", "") or "",
                        "track":    entry.get("track", "") or "",
                        "score":    str(entry.get("score", 0)),
                        "date":     date_str,
                    })

            if ids:
                self._collection.upsert(ids=ids, documents=docs, metadatas=metas)
                print(f"   [RAG] Upserted {len(ids)} decisions into ChromaDB")
                print(f"   [RAG] Total in ChromaDB: {self._collection.count()}")
        except Exception as e:
            print(f"   [WARN] RAG ingest failed: {e}")

    def retrieve_similar(self, job, top_k=RAG_TOP_K):
        """
        Returns a plain-text summary of the most similar past decisions.
        Returns empty string if not enough data or RAG disabled.
        """
        if not RAG_ENABLED or not self._init():
            return ""
        try:
            count = self._collection.count()
            if count < 20:
                return ""  # not enough data yet
            query_text = " ".join(filter(None, [
                job.get("title", ""),
                job.get("track", ""),
                " ".join(job.get("matched_keywords", [])),
            ]))
            if not query_text.strip():
                return ""
            results = self._collection.query(
                query_texts=[query_text],
                n_results=min(top_k, count),
                include=["metadatas", "distances"],
            )
            if not results or not results["metadatas"]:
                return ""
            lines = ["Similar past decisions:"]
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                similarity = round((1 - dist) * 100)
                reason = f" ({meta['reason']})" if meta.get("reason") else ""
                lines.append(f"  - [{similarity}% match] {meta['title']} → {meta['decision']}{reason}")
            return "\n".join(lines)
        except Exception as e:
            print(f"   [WARN] RAG retrieval failed: {e}")
            return ""

# Singleton
job_rag = JobRAG()

# ─── LOGGING SETUP ───────────────────────────────────────────
# Logs to both console AND job_search.log (overwrites each run)
import os as _os
LOG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "job_search_run.log")

class DualLogger:
    """Writes to both console and log file simultaneously."""
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

# Redirect all print() output to both console and log file
sys.stdout = DualLogger(LOG_FILE)

# Log run start with timestamp
print(f"\n{'='*60}")
print(f"  Job Search Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}")

# ─── ERROR LOGGING + FAILURE ALERT ───────────────────────────
# Persistent error log shared with review_decisions.py (append mode)
ERROR_LOG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "jobsearch_errors.log")
SCRIPT_NAME = "job_search.py"

# Wire up Python's logging module -- WITHOUT this, every logging.info()/
# logging.exception() call in this file (the [FIT-OK]/[FIT-SKIP]/[FIT-WARN]/
# [FIT-ERROR] diagnostic lines) is silently dropped: the root logger
# defaults to WARNING level with no handler, so .info() never reaches
# anywhere and even .exception() only hits a stderr "last resort" handler
# that isn't captured in the run log. This makes them real, writing to a
# dedicated file alongside jobsearch_errors.log.
FIT_DEBUG_LOG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fit_analysis_debug.log")
logging.basicConfig(
    filename=FIT_DEBUG_LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def log_error(message):
    """Append a timestamped error to the shared persistent error log."""
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] [{SCRIPT_NAME}] {message}\n")
    except Exception as e:
        print(f"[WARN] Could not write to {ERROR_LOG_FILE}: {e}")

def send_failure_alert(reason_short, error_detail):
    """Send a fatal-error alert email when something prevents the run."""
    import smtplib as _smtplib
    from email.mime.multipart import MIMEMultipart as _MM
    from email.mime.text import MIMEText as _MT
    try:
        gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
        gmail_pass = os.environ.get("GMAIL_APP_PASS", "")
        email_to   = os.environ.get("EMAIL_TO", gmail_addr)
        if not (gmail_addr and gmail_pass):
            print("[WARN] Email creds missing — cannot send failure alert.")
            return
        today_iso = datetime.now().strftime("%Y-%m-%d")
        subject = f"[ALERT] {SCRIPT_NAME} aborted — {reason_short} — {today_iso}"
        body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<div style="background:#c0392b;color:white;padding:16px 20px;border-radius:6px;">
  <h2 style="margin:0;font-size:18px;">Run Aborted: {SCRIPT_NAME}</h2>
  <p style="margin:6px 0 0;font-size:12px;opacity:0.9;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
<div style="padding:16px 20px;background:#fff5f5;border:1px solid #f5c6cb;border-top:none;border-radius:0 0 6px 6px;">
  <p style="margin:0 0 8px;"><strong>Reason:</strong> {reason_short}</p>
  <p style="margin:0 0 8px;"><strong>Detail:</strong></p>
  <pre style="background:#f8f9fa;padding:10px;border-radius:4px;font-size:11px;white-space:pre-wrap;">{error_detail}</pre>
  <p style="margin:12px 0 0;font-size:12px;color:#555;">See <code>jobsearch_errors.log</code> for the full persistent error history.</p>
</div></body></html>"""
        msg = _MM("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Job Search Alert <{gmail_addr}>"
        msg["To"]      = email_to
        msg.attach(_MT(body, "html"))
        with _smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_addr, gmail_pass)
            server.sendmail(gmail_addr, email_to, msg.as_string())
        print(f"[OK] Failure alert email sent to {email_to}")
    except Exception as e:
        log_error(f"Could not send failure alert email: {e}")
        print(f"[ERROR] Could not send failure alert: {e}")

# ─── LOG SNAPSHOTS (mobile-accessible via GitHub) ────────────
import shutil as _shutil
LOGS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logs")
LOG_RETENTION_DAYS = 14

def snapshot_and_prune_logs(retention_days=LOG_RETENTION_DAYS):
    """
    Copy live logs to dated snapshots in logs/, then prune snapshots
    older than retention_days. Run logs are snapshotted every day
    (proof of run); error log only snapshotted when non-empty (signal).
    Called near end of run, before git_commit_push().
    Returns (snapshotted, pruned) counts. Never raises.
    """
    snapshotted = 0
    pruned = 0
    try:
        _os.makedirs(LOGS_DIR, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")

        # Run log: snapshot every day (even if empty — proves the run happened)
        if _os.path.exists(LOG_FILE):
            try:
                # Flush any pending writes from the DualLogger before copying
                if hasattr(sys.stdout, "logfile") and sys.stdout.logfile:
                    sys.stdout.logfile.flush()
            except Exception:
                pass
            dst = _os.path.join(LOGS_DIR, f"job_search_{today}.log")
            _shutil.copy2(LOG_FILE, dst)
            snapshotted += 1

        # Error log: snapshot ONLY if non-empty (presence = signal something went wrong)
        if _os.path.exists(ERROR_LOG_FILE) and _os.path.getsize(ERROR_LOG_FILE) > 0:
            dst = _os.path.join(LOGS_DIR, f"jobsearch_errors_{today}.log")
            _shutil.copy2(ERROR_LOG_FILE, dst)
            snapshotted += 1

        # Prune snapshots older than retention_days
        cutoff = datetime.now() - timedelta(days=retention_days)
        for fname in _os.listdir(LOGS_DIR):
            if not fname.endswith(".log"):
                continue
            # Filename pattern: <prefix>_YYYY-MM-DD.log
            try:
                date_str = fname.rsplit(".", 1)[0].rsplit("_", 1)[-1]
                snap_date = datetime.strptime(date_str, "%Y-%m-%d")
                if snap_date < cutoff:
                    _os.remove(_os.path.join(LOGS_DIR, fname))
                    pruned += 1
            except (ValueError, IndexError):
                continue
    except Exception as e:
        # Non-critical — never abort a run because of snapshot issues
        print(f"[WARN] Log snapshot failed: {e}")
        try:
            log_error(f"Log snapshot failed: {e}")
        except Exception:
            pass

    return snapshotted, pruned


# ─── GIT PULL AT START (abort if it fails) ───────────────────
import subprocess as _subprocess
SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))

def git_pull_or_abort():
    """Pull latest before running. Abort + alert + log on failure."""
    print("[GIT] Pulling latest from GitHub...")
    try:
        result = _subprocess.run(
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
    """Commit and push at end of run so all local changes go to GitHub."""
    print("\n[GIT] Committing and pushing local changes...")
    try:
        _subprocess.run(["git", "add", "-A"], cwd=SCRIPT_DIR, check=True)
        today_iso = datetime.now().strftime("%Y-%m-%d")
        commit_msg = f"Nightly job search run — {today_iso}"
        result = _subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=SCRIPT_DIR, capture_output=True, text=True
        )
        if "nothing to commit" in (result.stdout + result.stderr).lower():
            print("   [INFO] Nothing to commit")
            return
        _subprocess.run(["git", "push"], cwd=SCRIPT_DIR, check=True)
        print(f"   [OK] Pushed: '{commit_msg}'")
    except _subprocess.CalledProcessError as e:
        msg = f"git commit/push failed: {e}"
        print(f"   [ERROR] {msg}")
        log_error(msg)

# Pull before doing anything else — abort the whole run if it fails
if not git_pull_or_abort():
    print("[ABORT] Run halted due to git pull failure.")
    sys.exit(1)

#
# FRESHNESS FILTER (5 days)
#
MAX_AGE_HOURS = 120  # 5 days
DEBUG_MODE = True   # Set to False once confirmed working
GENERATE_COVER_LETTERS = False  # Set to False to disable cover letter generation

# ─── PIPELINE FUNNEL INSTRUMENTATION ─────────────────────────
# Tracks where jobs get filtered out at each stage of the pipeline.
# Counts are surfaced in the daily digest email so we can diagnose
# dry spells at a glance (which stage killed the most candidates?).
class FunnelCounter:
    """
    Tracks job counts at each filter stage globally across all sources.
    Stages mirror the actual filter order used by the source functions:
      raw → recency → title → level → score → us_remote → blocked → kept
    Plus post-aggregation stages:
      → minscore → cross_dedup → seen_dedup → fit_hard_disqualify → final
    """
    def __init__(self):
        # Per-stage cumulative counts
        self.stages = {
            "raw": 0,           # Raw candidates from all sources (pre-filter)
            "after_recency": 0, # Survived is_recent() check
            "after_title": 0,   # Survived is_relevant_title() check
            "after_level": 0,   # Survived get_job_track level_ok check
            "after_score": 0,   # Survived score > 0 check
            "after_us": 0,      # Survived is_us_remote() check
            "after_blocked": 0, # Survived blocked-site/company check
            "kept_by_sources": 0,  # Total returned by all sources (before main() filters)
            "after_minscore": 0,   # Survived per-track min score thresholds
            "after_cobol_hybrid": 0,  # Survived COBOL hybrid pay-tier filter ($55/hr rule)
            "after_pay_floor": 0,  # Survived Track 4 pay-floor filter (other tracks pass through)
            "after_cross_dedup": 0,  # Survived cross-source dedup
            "after_seen_dedup": 0,   # Survived seen_jobs.json dedup
            "after_fit_hard_disqualify": 0,  # Survived AI-track fit-eval hard disqualify drop
            "final": 0,            # Made it to the email
        }
        # Per-source raw count for context (not used in main funnel, but useful)
        self.by_source = {}

    def add_raw(self, source, n=1):
        self.stages["raw"] += n
        self.by_source[source] = self.by_source.get(source, 0) + n

    def record(self, stage, n=1):
        """Record n jobs surviving a given stage."""
        if stage in self.stages:
            self.stages[stage] += n

    def set_stage(self, stage, n):
        """Set a stage count directly (used for post-aggregation stages
        where we know the exact survivor count from len(list))."""
        if stage in self.stages:
            self.stages[stage] = n

    def biggest_drop(self):
        """
        Return (stage_name, dropped_count, pct_of_prior_stage) for the
        single biggest drop in the funnel. Returns (None, 0, 0) if no drops.
        """
        order = [
            ("raw",              "Raw candidates"),
            ("after_recency",    "Recency filter"),
            ("after_title",      "Title filter"),
            ("after_level",      "Level filter"),
            ("after_score",      "Score filter"),
            ("after_us",         "US/remote filter"),
            ("after_blocked",    "Blocked site/company filter"),
            ("after_minscore",   "Min score threshold"),
            ("after_cobol_hybrid", "COBOL hybrid pay-tier ($55/hr)"),
            ("after_pay_floor",  "Track 4 pay floor"),
            ("after_cross_dedup", "Cross-source dedup"),
            ("after_seen_dedup",  "Already-seen dedup"),
            ("after_fit_hard_disqualify", "AI fit hard-disqualify"),
            ("final",            "Final"),
        ]
        biggest_label = None
        biggest_drop = 0
        biggest_pct = 0.0
        for i in range(1, len(order)):
            prior_key, _ = order[i - 1]
            this_key, this_label = order[i]
            prior = self.stages.get(prior_key, 0)
            current = self.stages.get(this_key, 0)
            dropped = prior - current
            if prior > 0 and dropped > biggest_drop:
                biggest_drop = dropped
                biggest_label = this_label
                biggest_pct = (dropped / prior) * 100
        return biggest_label, biggest_drop, biggest_pct

    def summary_dict(self):
        """Return a dict suitable for passing to send_email() for rendering."""
        return {
            "stages": dict(self.stages),
            "by_source": dict(self.by_source),
            "biggest_drop": self.biggest_drop(),
        }

# Global singleton — sources and main() both write to this
funnel = FunnelCounter()


NON_US_LOCATIONS = [
    "india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
    "chennai", "pune", "kolkata", "noida", "gurugram", "gurgaon",
    " ind ", "united kingdom", "london", "canada", "toronto",
    "australia", "sydney", "melbourne", "germany", "berlin",
    "france", "paris", "brazil", "philippines", "manila",
    "pakistan", "singapore", "china", "japan", "tokyo",
    "poland", "ukraine", "romania", "latam", "latin america", "apac", "emea",
    "canadian and listed in french",
    "great britian",
    "europe",
    "philippines and too senior",
    "native to portugal",
    "columbia",
]

# Job site URL blacklist - sites that are hard to apply on or are middlemen
BLOCKED_JOB_SITES = [
    "jobgether.com", "jobgether",
    "kuubik.com", "kuubik",
    "jobtogether.com",
    "jobisjob.com",
    "jobleads.com", "jobleads",
    "pangian.com", "pangian",
    "dailyremote.com", "dailyremote",
    "rocketship.com", "remoterocketship.com", "rocketship",
    "devitjobs.com", "devitjobs",
    "novaedge.com", "novaedge",
    "twine.net", "twine",
    "applytojob.com", "applytojob",
    "dataannotation.tech", "dataannotation",
    "pitchmeai.com", "pitchmeai",
    "jobflarely.liveblog365.com", "jobflarely", "liveblog365.com",
    "remotelyusajobs.com", "remotely-usa-jobs",
    "remotefront.com", "remotefront",  # email-wall aggregator (magic-link login)
    "jobsearcher.com",
    "hireza.com", "hireza",
    "remotejobsanywhere.com", "remotejobsanyworldwide",
    "synergisticit.com", "synergisticit",
    "whatjobs.com", "whatjobs",
    "trovit.com", "travajo.com", "travajo",
    "trabajo.org", "trabajo",
    "talents.vaia.com", "vaia.com", "vaia",
    "naukri.com", "naukri",
    "jobright.ai", "jobright",
    "remotica.totalh.net", "totalh.net", "remotica",
    "smartworking.com", "smartworking", "smart-working-solutions", "smart-working",
    "jobera.com", "jobera",
    "workingnomads.com", "workingnomads",
    "facebook.com", "facebook",
    "remote.co", "remote.co/job",
    "jaabz.com", "jaabz",
    "remotepeople", "remote people",
    "motorsportjobs.com", "motorsportjobs",
    "motorsport", "racing jobs",
    "linkedin.com/posts", "twitter.com", "x.com",
    "mtu aero", "aero engines",
    "veritosolutions.com", "verito",
    "remote-jobs-anywhere", "remotejobsanywhere",
    "calance.com",

    "energyjobline.com", "energyjobline",
    "lockedinai.com", "lockedinai",
    # Social/forum sites — not job postings
    "reddit.com", "reddit",
    "bebee.com", "bebee",
    "weworkremotely.com",
    "himalayas.app", "himalayas",
    "zippia.com", "zippia",
    "builtin.com", "builtinkc.com",
    "wellfound.com/jobs?", "wellfound.com/l/",
    "salary.com", "payscale.com", "levels.fyi",
    "glassdoor.com/Salaries",
    # Aggregators slipping through Serper
    "jooble.org", "jooble.com", "jooble",
    "indeed.com/jobs", "indeed.com/q-", "indeed.com/l-",
    "indeed.com/m/", "indeed.com/rc/",
    "indeed.com/career-advice", "indeed.com/hire",
    "indeed.com/companies", "indeed.com/salaries",
    "in.indeed.com",  # Indian Indeed
    "ca.indeed.com",  # Canadian Indeed
    # Social media — not job postings
    "instagram.com", "instagram",
    "twitter.com", "x.com",
    "facebook.com/jobs",
    "tiktok.com",
    "remotive.com", "remotive.io", "remotive",
    "ziprecruiter.com/candidate/",
    "ziprecruiter.com/c/",
    "ziprecruiter.com/jobs/",
    "ziprecruiter.com/job/",
    "ziprecruiter.com",
    # Salary/guide pages — not job listings
    "agentic-engineering-jobs.com/agentic-engineer-salaries",
    "agentic-engineering-jobs.com/salaries",
    "levels.fyi", "salary.com", "payscale.com",
    "glassdoor.com/Salaries", "glassdoor.com/salaries",
    "flexjobs.zya.me",  # Suspended domain
    # Overseas job boards — not US positions
    "pt.talent.com",        # Portugal Talent.com
    "es.talent.com",        # Spain Talent.com
    "fr.talent.com",        # France Talent.com
    "de.talent.com",        # Germany Talent.com
    "uk.talent.com",        # UK Talent.com
    "au.talent.com",        # Australia Talent.com
    "ca.talent.com",        # Canada Talent.com
    "in.talent.com",        # India Talent.com
    "us.talent.com",        # US Talent.com (aggregator - unreliable direct links)
    "justjoin.it",          # Polish job board
    "pracuj.pl",            # Polish job board
    "nofluffjobs.com",      # Polish/European job board
    "eurojobs.com",         # European job board
    "eu.indeed.com",        # European Indeed
    "uk.indeed.com",        # UK Indeed
    "au.indeed.com",        # Australian Indeed
    "careers-page.com",     # Unvetted overseas aggregator
    "community.n8n.io",     # n8n forum posts — not job listings
    "remotejobsfinder.co",  # Overseas listings slipping through (e.g. /mex/)

    # Arc.dev — search results pages, not direct job postings
    "arc.dev/remote-jobs/", "arc.dev/remote-jobs",

    # BuiltIn regional subdomains (builtin.com + builtinkc.com already blocked)
    "builtincolorado.com", "builtinnyc.com", "builtinchicago.com",
    "builtinboston.com", "builtinaustin.com", "builtinla.com",
    "builtinseattle.com", "builtinsf.com",

    # Indeed international subdomains
    "hk.indeed.com",    # Hong Kong
    "mx.indeed.com",    # Mexico
    "br.indeed.com",    # Brazil
    "fr.indeed.com",    # France
    "de.indeed.com",    # Germany
    "sg.indeed.com",    # Singapore
    "ph.indeed.com",    # Philippines

    # MeetFrank — European job board
    "meetfrank.com", "meetfrank",

    # Aggregators slipping through noon run (2026-05-08)
    "tallo.com", "tallo",
    "virtualvocations.com", "virtualvocations",
    "theladders.com", "theladders",
    "edtech.com/jobs", "edtech.com",
    "pairedrecruiting.com", "pairedrecruiting",
    "aidoos.com",
    "www.linkedin.com",
    "wfhforgeon.byethost7.com",
    "hstn.me", 
    "remotepulse.likesyou.org",
]

def is_blocked_site(url):
    """Returns True if the job URL is from a blocked middleman site."""
    url_lower = str(url).lower()
    return any(site in url_lower for site in BLOCKED_JOB_SITES)

# ── False-positive domain/path filter (added 2026-05-07) ──────────────
# Catches training sites, spam aggregators, and services pages that score
# high on keywords but are not actual job postings.
BLOCKED_FP_DOMAINS = {
    # Training / course event sites — not job postings
    "ishatrainingsolutions.org",
    "udemy.com",
    "coursera.org",
    "pluralsight.com",
    "learnquest.com",
    "globalknowledge.com",
    "new-horizons.com",
    "newhorizons.com",
    "trainingcamp.com",
    "simplilearn.com",
    "intellipaat.com",
    # Sketchy aggregator / spam domains
    "2kool4u.net",
    "jobisite.com",
    "jobomas.com",
    "jobrapido.com",
    # Staffing services pages (not listings)
    "cortance.com",
}

BLOCKED_FP_PATHS = {
    # URL path segments that indicate a non-job page
    "/events/",
    "/event/",
    "/services/hire-",
    "/services/hire_",
    "/courses/",
    "/course/",
    "/training/",
    "/webinar/",
    "/workshop/",
    "/certification/",
    "/learning/",
    "/bootcamp/",
    "/tutorial/",
    "/blog/",          # blog posts sometimes match keywords
    "/salary/",
    "/salaries/",
}

def is_false_positive_url(url: str) -> tuple:
    """
    Returns (True, reason_str) if URL looks like a course/training/services
    page rather than an actual job posting. Returns (False, '') if clean.
    """
    if not url:
        return False, ""
    url_lower = url.lower()
    for domain in BLOCKED_FP_DOMAINS:
        if domain in url_lower:
            return True, f"fp_domain:{domain}"
    for path in BLOCKED_FP_PATHS:
        if path in url_lower:
            return True, f"fp_path:{path}"
    return False, ""

# ─── KC METRO LOCAL FILTER (for hybrid/on-site jobs within commuting range) ──
# A hybrid/on-site job is only viable for Hans if the office is within
# Kansas City metro commuting distance. is_us_remote() only handles the
# remote/non-US gate; this pair of helpers adds the local-hybrid path so
# main()/passes_filters() can keep BOTH: fully-remote-anywhere AND
# hybrid/on-site-in-KC. Hybrid/on-site elsewhere should be rejected.

KC_METRO_LOCATIONS = {
    # MO side
    "lee's summit", "lees summit", "kansas city, mo", "kansas city mo",
    "independence, mo", "blue springs", "liberty, mo", "grandview, mo",
    "raytown", "north kansas city", "gladstone, mo", "belton, mo",
    "platte city", "parkville", "kearney, mo",
    # KS side
    "overland park", "olathe", "lenexa", "shawnee, ks", "leawood",
    "prairie village", "merriam", "mission, ks", "roeland park",
    "kansas city, ks", "kansas city ks", "bonner springs", "gardner, ks",
    "spring hill, ks", "de soto, ks", "edwardsville, ks",
    # Generic KC references
    "kansas city metro", "kc metro", "greater kansas city",
}

# ─── PAY FLOOR PARSING (Track 4: Remote Income Floor) ─────────
# Strict filter per Hans's explicit choice: if pay can't be parsed from the
# listing text at all, OR it parses below the floor, the job is dropped.
# Real tradeoff acknowledged: a lot of legitimate remote QA postings don't
# list pay at all, so this WILL cut the candidate pool down hard. Flagged
# to Hans — if the pool ends up too thin after a few runs, loosening this
# to a soft filter (show pay-unknown jobs too) is a one-line change.
# 2026-06-26: Tiered per Hans's explicit instruction — remote and KC-metro
# hybrid/onsite no longer share one floor. Applies to non-COBOL Gap Track
# only; COBOL keeps its existing $30/hr-remote / $55/hr-hybrid rule
# (handled separately, earlier in main(), before this floor ever runs).
REMOTE_FLOOR_MIN_HOURLY  = 25.0   # non-COBOL Gap Track, fully remote
GAP_HYBRID_MIN_HOURLY    = 30.0   # non-COBOL Gap Track, KC-metro hybrid/onsite
REMOTE_FLOOR_MIN_ANNUAL  = REMOTE_FLOOR_MIN_HOURLY * 2080  # ~$52,000/yr equivalent

def _parse_pay_to_hourly(text):
    """
    Try to extract an hourly-rate-equivalent number from free-text pay info
    (salary field, title, or description). Returns a float (highest
    plausible hourly rate found) or None if nothing parseable.

    Handles:
      - Explicit hourly: "$28/hr", "$28 per hour", "$28-32/hour"
      - Annual salary, converted to hourly equivalent at 2080 hrs/yr:
        "$65,000/year", "$60K-$70K", "$65,000 annually"
    Deliberately conservative: if a range is given, uses the HIGH end,
    since "floor" filtering should give the benefit of the doubt on
    ranges rather than reject a $28-38/hr posting outright.
    """
    if not text:
        return None
    t = text.lower().replace(",", "")

    # Hourly patterns: $XX/hr, $XX per hour, $XX-$YY/hour, $XX/hour
    hourly_matches = re.findall(
        r"\$\s?(\d+(?:\.\d+)?)\s*(?:-|to)?\s*\$?\s?(\d+(?:\.\d+)?)?\s*/?\s*(?:hr|hour|per hour|/hr|/hour)",
        t,
    )
    hourly_candidates = []
    for low, high in hourly_matches:
        vals = [float(v) for v in (low, high) if v]
        if vals:
            hourly_candidates.append(max(vals))
    if hourly_candidates:
        return max(hourly_candidates)

    # Annual patterns: require an explicit salary/year qualifier nearby so we
    # don't mistake a signing bonus, referral bonus, or unrelated dollar
    # figure for the actual pay rate. Window-based: look for "$XXk"-style
    # numbers that have a qualifier word within ~25 chars on either side.
    annual_qualifiers = r"(?:salary|/\s?yr|/\s?year|per year|annually|annual|base pay|base salary|compensation)"
    annual_matches = re.findall(
        r"\$\s?(\d+(?:\.\d+)?)\s*k?\s*(?:-|to)?\s*\$?\s?(\d+(?:\.\d+)?)?\s*k?\s*"
        rf"(?:[^.$]{{0,25}}{annual_qualifiers})",
        t,
    )
    annual_candidates = []
    for low, high in annual_matches:
        for v in (low, high):
            if not v:
                continue
            val = float(v)
            # Heuristic: if the raw number is small (e.g. "65" meaning "65k"),
            # and the original text had a 'k' suffix nearby, scale it up.
            # Simpler/safer approach: if value < 1000, assume it's already
            # in thousands (typical "$65k" / "$65,000" shorthand written as
            # "65"); otherwise treat as already a full annual figure.
            if val < 1000:
                val *= 1000
            annual_candidates.append(val)
    if annual_candidates:
        best_annual = max(annual_candidates)
        # Sanity bound: ignore clearly bogus parses (e.g. > $500k or < $10k
        # for what's supposed to be an entry-level QA role; likely a parse
        # artifact, not real pay data).
        if 10_000 <= best_annual <= 500_000:
            return best_annual / 2080.0

    return None


def meets_pay_floor(job, min_hourly=None):
    """
    Returns True only if a pay figure can be parsed from the job's salary
    field, title, or description, AND that figure meets or exceeds the
    floor. Strict per Hans's choice — no parseable pay = rejected.

    min_hourly overrides the default $25/hr remote floor — pass
    GAP_HYBRID_MIN_HOURLY for KC-metro hybrid/onsite non-COBOL jobs, which
    have a higher $30/hr bar per Hans's explicit instruction.
    """
    floor = min_hourly if min_hourly is not None else REMOTE_FLOOR_MIN_HOURLY
    # Fast-path rejection: explicit low hourly rate signals
    haystack = (
        (job.get("salary", "") or "") + " " +
        (job.get("title", "") or "") + " " +
        (job.get("description", "") or "")
    ).lower()
    if any(sig in haystack for sig in REMOTE_FLOOR_LOW_PAY_SIGNALS):
        return False

    for field in (job.get("salary", ""), job.get("title", ""), job.get("description", "")):
        hourly = _parse_pay_to_hourly(field)
        if hourly is not None:
            return hourly >= floor
    # Nothing parseable anywhere — strict filter means reject.
    return False


def is_kc_metro_local(title, description, location=""):
    """Return True if the job's location/text suggests a Kansas City metro
    office location (within commute range of Lee's Summit, MO)."""
    haystack = (location + " " + title + " " + description).lower()
    return any(kc in haystack for kc in KC_METRO_LOCATIONS)

# Phrases indicating the role requires on-site or hybrid presence
ONSITE_HYBRID_SIGNALS = [
    "hybrid", "on-site", "onsite", "on site", "in-office", "in office",
    "days in office", "days in the office", "days per week in",
    "days a week in", "in-person", "in person required",
    "must be located in", "must reside in", "must be based in",
    "must live in", "must be local", "local candidates only",
    "no remote", "not remote", "fully on-site", "fully onsite",
    "relocation required", "relocation assistance",
]

def is_onsite_or_hybrid(title, description, location=""):
    """Return True if the job appears to be on-site or hybrid (i.e. it
    requires physical presence at the office)."""
    haystack = (location + " " + title + " " + description).lower()
    return any(sig in haystack for sig in ONSITE_HYBRID_SIGNALS)


def is_us_remote(title, description, location=""):
    # Check location field first - if it contains a non-US location, reject immediately.
    # EXCEPTION: Canada in the location field is handled later, after we check
    # the description for "US/Canada" / "North America" eligibility signals.
    loc_lower = location.lower().strip()
    canada_in_location = False
    canada_location_terms = {"canada", "toronto", "vancouver", "montreal",
                             "ontario", "british columbia", "alberta",
                             "calgary", "edmonton", "ottawa", "winnipeg",
                             "quebec", "halifax"}
    if loc_lower:
        for non_us in NON_US_LOCATIONS:
            term = non_us.strip()
            if term in loc_lower:
                if term in canada_location_terms:
                    canada_in_location = True  # defer decision
                    continue
                return False
    # Also check title and description for strong non-US indicators
    check = (title + " " + description).lower()

    # ─── CANADA HANDLING ────────────────────────────────────
    # PASS 1: US-eligible signals — keep these even if Canada is mentioned.
    # Many "Remote, Canada" postings are actually US/Canada or North America
    # eligible. If we see explicit US eligibility, allow through.
    us_eligible_signals = [
        "us/canada", "us / canada", "u.s./canada", "us and canada",
        "us or canada", "us, canada", "canada/us", "canada / us",
        "canada and us", "canada or us", "canada, us",
        "north america", "north american", "americas remote",
        "remote (americas)", "remote, americas",
        "na remote", "remote (na)", "remote na ",
        "remote - us/canada", "remote (us/canada)",
        "remote in us or canada", "remote in the us or canada",
        "open to us and canada", "open to candidates in us and canada",
        "us-based or canada-based", "based in the us or canada",
        "eligible to work in the us", "eligible to work in the united states",
        "authorized to work in the us", "authorized to work in the united states",
    ]
    _us_eligible_override = False
    for signal in us_eligible_signals:
        if signal in check:
            # Found explicit US eligibility — short-circuit all later Canada rejects.
            _us_eligible_override = True
            break

    # PASS 2: Canada-only hard reject — explicit Canada-restrictive language.
    # These always reject, regardless of any US-eligible signal above.
    canada_only_signals = [
        "canada only", "canada-only", "canadian residents only",
        "must reside in canada", "must be located in canada",
        "must be a canadian", "canadian citizens only",
        "open only to canadian", "canada-based candidates only",
        "must be based in canada", "remote (canada only)",
        "remote, canada only", "remote - canada only",
        "this role is open to canadian", "only open to canadian residents",
        "work authorization in canada required",
    ]
    for signal in canada_only_signals:
        if signal in check:
            return False

    # Strong indicators - if these appear anywhere, reject
    strong_indicators = [
        # Multi-country job titles — not US only (added 2026-05-08)
        "us/uk", "uk/ca", "us/uk/ca", "us/uk/ca/de",
        "remote (us/uk)", "(us/uk)", "remote (us/india)",
        # India
        "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
        "chennai", "pune", "kolkata", "noida", "gurugram", "gurgaon",
        "india only", "india based", "based in india", "location: india",
        "india remote", "remote, india", "remote - india", "engineering - india",
        "india (remote)", "remote india",
        "karnataka", "maharashtra", "tamil nadu",
        "cochin", "coimbatore", "kochi", "kolkata", "indore",
        "jaipur", "ahmedabad", "chandigarh", "bhopal", "lucknow",
        "smartworking", "smart working", "smart-working solutions", "smart working solutions",
        "verito solutions", "verito",
        # UK
        "remote in uk", "united kingdom", "london, uk", "location: uk",
        # Other
        "remote in australia", "remote in germany", "remote in europe",
        "remote in india", "europe, remote", "europe remote",
        "available from: europe", "offer is available from: europe",
        "remote jobs anywhere worldwide", "worldwide remote",
        "principal ai engineer (europe", "europe only",
        "emea remote", "apac remote", "latam remote",
        # Southeast Asia / Middle East
        "ho chi minh", "hanoi", "vietnam", "jakarta", "indonesia",
        "kuala lumpur", "malaysia", "bangkok", "thailand",
        "dubai", "abu dhabi", "uae", "united arab emirates",
        "cairo", "egypt", "nairobi", "kenya", "lagos", "nigeria",
        "remote (emea)", "remote(emea)", "emea only", "(emea)",
        "teraleads", "ruby labs", "rubylabs",
        "latin america", "latam", "south america",
        "colombia", "argentina", "brazil", "mexico", "chile",
        "remote people", "globally distributed",
        # Europe cities/countries slipping through
        "lisbon", "portugal", "krakow", "kraków", "warsaw", "warszawa",
        "prague", "budapest", "bucharest", "sofia", "zagreb",
        "amsterdam", "berlin", "munich", "frankfurt", "hamburg",
        "paris", "lyon", "madrid", "barcelona", "rome", "milan",
        "stockholm", "oslo", "copenhagen", "helsinki", "dublin",
        "zurich", "geneva", "brussels", "vienna", "athens",
        # Australia
        "brisbane", "perth", "adelaide", "auckland", "wellington",
        # Job board language indicators
        "emprego",      # Portuguese for "job"
        "emploi",       # French for "job"
        "arbeit",       # German for "work"
        "offre d'emploi",  # French job posting
    ]
    # Detect semicolon-separated multi-country locations (e.g. "EMEA; India; Poland; Ukraine")
    if re.search(r'(emea|apac|latam|india|ukraine|poland|albania|romania)[^a-z]*;', check):
        return False
    for indicator in strong_indicators:
        if indicator in check:
            return False

    # PASS 3: Canada signals — only reject if no US-eligible override.
    if not _us_eligible_override:
        # Canada was in the location field but we deferred — now reject it.
        if canada_in_location:
            return False
        canada_signals = [
            # Canada-specific remote phrasing
            "remote in canada", "canada remote", "location: canada",
            "based in canada", "remote, canada", "remote - canada",
            "remote (canada)", "(canada)", "in canada",
            # Canada provinces & major cities
            "toronto", "vancouver", "montreal", "calgary", "edmonton",
            "ottawa", "winnipeg", "quebec", "halifax", "saskatoon",
            "regina", "victoria",
            "ontario", "british columbia", "alberta",
            "markham, on", "markham, ontario", " on,", ", on ",
            "qualcomm canada",
        ]
        for signal in canada_signals:
            if signal in check:
                return False
    # Detect state-restricted remote jobs (remote but must live in specific state)
    # List of all US states to detect restrictions (excluding Missouri - Hans is there!)
    us_states = [
        "alabama", "alaska", "arizona", "arkansas", "california",
        "colorado", "connecticut", "delaware", "florida", "georgia",
        "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas",
        "kentucky", "louisiana", "maine", "maryland", "massachusetts",
        "michigan", "minnesota", "mississippi", "montana", "nebraska",
        "nevada", "new hampshire", "new jersey", "new mexico", "new york",
        "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
        "pennsylvania", "rhode island", "south carolina", "south dakota",
        "tennessee", "texas", "utah", "vermont", "virginia",
        "washington", "west virginia", "wisconsin", "wyoming",
        # Abbreviations (excluding MO)
        " al ", " ak ", " az ", " ar ", " ca ", " co ", " ct ", " de ",
        " fl ", " ga ", " hi ", " id ", " il ", " in ", " ia ", " ks ",
        " ky ", " la ", " me ", " md ", " ma ", " mi ", " mn ", " ms ",
        " mt ", " ne ", " nv ", " nh ", " nj ", " nm ", " ny ", " nc ",
        " nd ", " oh ", " ok ", " or ", " pa ", " ri ", " sc ", " sd ",
        " tn ", " tx ", " ut ", " vt ", " va ", " wa ", " wv ", " wi ", " wy ",
        # Major non-MO cities
        "bellevue", "seattle", "new york", "atlanta", "dallas", "austin",
        "chicago", "boston", "denver", "phoenix", "los angeles", "san francisco",
        "miami", "orlando", "charlotte", "houston", "philadelphia",
    ]

    # Patterns that indicate state restrictions
    state_restriction_patterns = [
        r"must (live|reside|be located|be based) in",
        r"must be (a resident|located) (in|within)",
        r"residents? of .{0,30} only",
        r"only (open|available) to .{0,30} residents?",
        r"(w2|w-2).{0,30}(local|locals only|face.to.face|f2f)",
        r"locals? (only|preferred).{0,20}(no relocation|no relo)",
        r"need only locals",
        r"local candidates? only",
        r"face.to.face.{0,30}interview",
        r"in.person.{0,30}interview.{0,30}required",
        r"may only be hired in.{0,100}location",
        r"hired in the following location.{0,50}(az|nc|tx|ca|fl|ny)",
        r"remote.{0,10}(az|nc|tx).{0,10}(and|or).{0,10}(az|nc|tx)",
        r"only be hired in the following location",
        r"available in the following (state|location|region)",
        r"limited to the following (state|location)",
        r"hiring in.{0,30}(az|tx|nc|ca|fl|ny|wa|co|ga|il|oh|pa|va|ma)",
    ]

    for pattern in state_restriction_patterns:
        if re.search(pattern, check):
            # Check if Missouri is the ONLY state mentioned - if so allow it!
            mo_mentioned = "missouri" in check or " mo " in check or "lee's summit" in check or "kansas city" in check
            other_state_mentioned = any(state in check for state in us_states)
            if not mo_mentioned or other_state_mentioned:
                return False

    # Check for remote + specific state (not Missouri)
    remote_state_pattern = r"remote.{0,30}(" + "|".join(us_states[:40]) + r")"
    if re.search(remote_state_pattern, check):
        # Allow if Missouri is mentioned
        if "missouri" not in check and " mo " not in check:
            return False

    # Block jobs with onsite city in the TITLE (e.g. "SDET - Seattle, WA")
    onsite_city_pattern = r"[-–|,]\s*(seattle|chicago|boston|austin|dallas|denver|phoenix|atlanta|alpharetta|houston|new york|san francisco|los angeles|philadelphia|charlotte|orlando|miami|bellevue|portland|minneapolis|pittsburgh|raleigh|nashville|detroit|baltimore|st\. louis|cleveland|columbus|indianapolis|louisville|memphis|richmond|norfolk|sacramento|san diego|san jose|las vegas|tampa|jacksonville|hartford|providence|buffalo|rochester|albany|newark|jersey city|ann arbor|birmingham|boise|cincinnati|salt lake city|tucson|albuquerque|omaha|tulsa|oklahoma city|el paso|fresno|long beach|mesa|colorado springs|virginia beach|arlington|bakersfield|honolulu|anaheim|aurora|santa ana)\s*,\s*[a-z]{2}"
    if re.search(onsite_city_pattern, title.lower()):
        # Only block if no "remote" in title
        if "remote" not in title.lower():
            return False

    # Detect closed/expired jobs
    closed_indicators = [
        "no longer accepting", "position filled", "job closed",
        "no longer available", "expired", "this job is closed",
    ]
    for indicator in closed_indicators:
        if indicator in check:
            return False

    # Block jobs requiring security clearance Hans doesn't hold
    clearance_indicators = [
        "top secret", "ts/sci", "ts clearance", "secret clearance required",
        "active secret", "active top secret", "dod secret", "dod clearance",
        "security clearance required", "clearance required", "must have clearance",
        "must hold clearance", "clearance: secret", "clearance: top secret",
        "polygraph", "sci clearance",
    ]
    for indicator in clearance_indicators:
        if indicator in check:
            return False

    return True

def is_blocked_company(title, description, company=""):
    """Block specific companies regardless of URL."""
    blocked_companies = [
        "dataannotation", "data annotation",
        "pitchmeai", "pitch me ai",
        "synergisticit", "synergistic it",
        "appen ", "clickworker", "telus international",
        "outlier ai", "scale ai",
        "silicon valley bank", "svb ", "first citizens bank", "first-citizens bank", "first-citizens",
        # India/offshore body shops
        "berry virtual", "legal soft", "legalsoft",
        "softratech", "innovative information technologi",
        "mastech", "igate", "hexaware", "nisum", "coforge",
        # Middle East / other overseas
        "teraleads", "ruby labs", "rubylabs",
        # Global hiring platforms (never US-only)
        "deel.com", " deel ", "letsdeel",
    ]
    check = (title + " " + description + " " + company).lower()
    return any(co in check for co in blocked_companies)

def parse_relative_date(date_str):
    """Handle relative dates like '1 day ago', '3 days ago', '2 hours ago'"""
    s = str(date_str).lower().strip()
    now = datetime.now(timezone.utc)
    # Match patterns like "1 day ago", "3 days ago", "2 hours ago", "5 minutes ago"
    match = re.match(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == "second":
            return now - timedelta(seconds=amount)
        elif unit == "minute":
            return now - timedelta(minutes=amount)
        elif unit == "hour":
            return now - timedelta(hours=amount)
        elif unit == "day":
            return now - timedelta(days=amount)
        elif unit == "week":
            return now - timedelta(weeks=amount)
        elif unit == "month":
            return now - timedelta(days=amount*30)
        elif unit == "year":
            return now - timedelta(days=amount*365)
    # Match "today" or "just now"
    if s in ["today", "just now", "moments ago"]:
        return now
    # Match "yesterday"
    if s == "yesterday":
        return now - timedelta(days=1)
    return None

def is_recent(date_str):
    # If no date provided - EXCLUDE the job
    if not date_str or str(date_str).strip() == "":
        return False
    try:
        date_str_str = str(date_str).strip()
        # Try relative date first (e.g. "1 day ago")
        posted = parse_relative_date(date_str_str)
        # If not relative, try standard date parsing
        if posted is None:
            posted = dateparser.parse(date_str_str)
        if posted is None:
            return False
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - posted
        if age.total_seconds() < 0:
            return False
        return age <= timedelta(hours=MAX_AGE_HOURS)
    except Exception:
        return False

#
# CONFIGURATION
#
ADZUNA_APP_ID   = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY  = os.environ.get("ADZUNA_APP_KEY", "")
USAJOBS_API_KEY = os.environ.get("USAJOBS_API_KEY", "")
USAJOBS_EMAIL   = os.environ.get("USAJOBS_EMAIL", "")
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")   # optional, not currently used
CLAUDE_API_KEY  = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")

#  Email notifications
GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS", "")
EMAIL_TO       = os.environ.get("EMAIL_TO", GMAIL_ADDRESS)

# ─── FIT ANALYSIS (Claude-powered per-job blurb + gate) ──────
# Set to False to disable per-job fit blurbs in email digest.
# Fit analysis now runs on ALL AI-track jobs that pass filters (not just
# top 15) BEFORE the top-15 cut, because fit tier is now part of the sort
# key — a job can't be correctly ranked into the top 15 until we know
# whether it's a real chance or a pipe dream. Uses Haiku (cheap, fast,
# not latency-sensitive — this runs behind the scenes, not in real time)
# rather than Sonnet, since this is a 5-bucket classification task, not
# creative writing. Cover letters stay on Sonnet.
GENERATE_FIT_ANALYSIS   = True
FIT_ANALYSIS_MODEL      = "claude-haiku-4-5-20251001"
FIT_ANALYSIS_TRACKS     = {"AI Engineering", "QA Automation", "Gap Track"}  # tracks that get fit-eval/gating; Performance Engineering excluded (keyword match there IS reliable fit signal already)
HARD_DISQUALIFY_TERMS   = [
    # If these appear in the fit_reason/description signal, drop silently —
    # no realistic chance, not worth a slot in the digest at all.
    "phd required", "phd preferred", "publication required",
    "published research", "research scientist", "train models from scratch",
    "build models from scratch", "novel model architecture",
    "pure ml research", "applied scientist",
]

SEARCH_KEYWORDS = [
    # Track 1: Performance Engineering (core)
    "LoadRunner", "performance engineer", "performance tester",
    "JMeter", "NeoLoad", "load testing", "performance testing",
    # Track 3: AI Engineering (entry level)
    "entry level AI engineer", "junior AI engineer", "associate AI engineer",
    "AI engineer entry", "machine learning engineer entry",
    # Track 3: Agentic AI / AI Developer roles
    "agentic AI developer", "agentic AI engineer", "AI agent developer",
    "AI developer", "LLM developer", "AI application developer",
]

CANDIDATE = {
    "name": "Hans Richardson",
    "location": "Lee's Summit, MO (Remote)",
    "linkedin": "linkedin.com/in/hans-richardson",
    "years_exp": 24,
    "top_skills": ["LoadRunner", "VuGen", "LRE", "JMeter", "NeoLoad",
                   "AppDynamics", "Splunk", "Prometheus", "Grafana",
                   "AWS", "Kubernetes", "REST API", "SQL", "Python",
                   "Selenium", "Test Automation", "AI Engineering",
                   "Performance Engineering", "Workload Modeling",
                   "Scalability Testing", "SLA Compliance"],
}

OUTPUT_FILE    = os.path.join(JSON_DIR, "job_results.json")
SEEN_JOBS_FILE = os.path.join(JSON_DIR, "seen_jobs.json")

def load_seen_jobs():
    """Load previously seen job URLs."""
    try:
        if os.path.exists(SEEN_JOBS_FILE):
            with open(SEEN_JOBS_FILE, "r") as f:
                data = json.load(f)
                return set(data.get("urls", []))
    except Exception:
        pass
    return set()

def save_seen_jobs(seen_urls):
    """Save seen job URLs so we never send duplicates."""
    try:
        # Keep only last 1000 URLs to prevent file growing too large
        url_list = list(seen_urls)[-1000:]
        with open(SEEN_JOBS_FILE, "w") as f:
            json.dump({"urls": url_list, "last_updated": datetime.now().isoformat()}, f, indent=2)
    except Exception as e:
        print(f"[WARN] Could not save seen jobs: {e}")

# Level filters
AI_ENGINEERING_LEVEL_FILTER = ["entry", "junior", "associate", "entry-level", "mid", "intermediate", "mid-level"]
QA_AUTOMATION_LEVEL_FILTER  = ["entry", "junior", "associate", "mid", "intermediate", "entry-level", "mid-level"]
GENERAL_QA_LEVEL_FILTER     = ["entry", "junior", "associate", "mid", "intermediate", "entry-level", "mid-level", ""]

#
# RELEVANCE SCORING - Tracks
#
PERF_HIGH_KEYWORDS = [
    "loadrunner", "vugen", "lre", "neoload", "performance engineer",
    "performance tester", "load testing", "performance testing",
    "workload model", "jmeter", "blazemeter"
]
PERF_BONUS_KEYWORDS = [
    "appdynamics", "splunk", "grafana", "prometheus", "aws",
    "kubernetes", "scalability", "sla", "rest api", "microservices",
    "observability", "bottleneck", "throughput", "latency"
]
QA_HIGH_KEYWORDS = [
    # Only QA Performance hybrid keywords
    "qa performance engineer", "performance qa engineer",
    "performance quality engineer", "qa performance testing",
]
QA_BONUS_KEYWORDS = [
    "python", "java", "javascript", "ci/cd", "jenkins", "github actions",
    "api testing", "regression testing", "agile", "jira", "postman"
]

# COBOL/Mainframe track keywords
COBOL_HIGH_KEYWORDS = [
    "cobol", "cics", "mainframe", "jcl", "vsam", "db2 mainframe",
    "ibm mainframe", "mvs", "zos", "z/os", "cobol developer",
    "mainframe developer", "cobol programmer", "cics developer",
]
COBOL_BONUS_KEYWORDS = [
    "db2", "ims", "natural", "assembler", "racf", "tso", "ispf",
    "cobol modernization", "legacy systems", "ibm z", "batch processing",
    "rexx", "sdsf", "endevor", "changeman"
]
AI_HIGH_KEYWORDS = [
    "ai engineer", "machine learning engineer", "ml engineer",
    "generative ai", "llm", "large language model", "deep learning",
    "artificial intelligence engineer", "ai developer",
    # Prompt Engineering — Hans's sweet spot
    "prompt engineer", "prompt engineering", "prompt developer",
    "llm prompt", "ai prompt", "generative ai engineer",
    # Agent / Agentic roles
    "ai agent", "agentic ai", "ai agent developer", "agent engineer",
    "llm application", "llm app developer", "llm developer",
    "ai application developer", "ai application engineer",
    # AI Automation / Integration
    "ai automation engineer", "ai integration engineer",
    "ai solutions engineer", "ai workflow", "ai pipeline",
    "langchain developer", "langchain engineer",
    "openai developer", "claude developer", "anthropic",
    # AI + Performance hybrid roles
    "ai performance engineer", "ml performance engineer",
    "ai test engineer", "ai quality engineer", "ai qa engineer",
    "mlops engineer", "llm engineer", "ai reliability engineer",
    "performance ai", "ai testing", "ai qa", "quality engineer ai",
]
# ── AI classification split (fix for QA/other-track jobs getting stolen
# into AI Engineering just for mentioning an AI buzzword in passing) ──
# GENERIC/BARE terms are single words or short generic phrases that show
# up constantly as throwaway tech-stack mentions in job descriptions that
# AREN'T about AI engineering at all (e.g. "QA Engineer" posting that
# mentions "our platform uses LLM-based RAG retrieval" as one line of
# product description). These only count toward AI track classification
# if they appear in the TITLE — a real AI role's title says so.
AI_GENERIC_TERMS = {
    "llm", "generative ai", "deep learning", "large language model", "anthropic",
}
# SPECIFIC PHRASES are distinctive enough (multi-word, role-specific) that
# they essentially never appear as a passing buzzword in an unrelated
# job's description — if a posting says "prompt engineer" or "mlops
# engineer" or "ai agent" anywhere, the role really is about that. Safe
# to keep as full-text (title OR description) triggers.
AI_SPECIFIC_PHRASES = [kw for kw in AI_HIGH_KEYWORDS if kw not in AI_GENERIC_TERMS]
AI_BONUS_KEYWORDS = [
    "python", "tensorflow", "pytorch", "openai", "langchain", "hugging face",
    "prompt engineering", "rag", "vector database", "nlp", "api integration",
    "anthropic", "claude api", "openai api", "gemini", "mistral",
    "fine tuning", "fine-tuning", "embeddings", "semantic search",
    "agentic", "multi-agent", "agent framework", "tool use",
    "chain of thought", "few shot", "zero shot", "context window",
    "llm ops", "llmops", "model evaluation", "ai observability",
]
HIGH_VALUE_KEYWORDS = PERF_HIGH_KEYWORDS + QA_HIGH_KEYWORDS + AI_HIGH_KEYWORDS + COBOL_HIGH_KEYWORDS
BONUS_KEYWORDS      = PERF_BONUS_KEYWORDS + QA_BONUS_KEYWORDS + AI_BONUS_KEYWORDS + COBOL_BONUS_KEYWORDS

# ─── TRACK 4: REMOTE INCOME FLOOR ─────────────────────────────
# Purpose is different from the other 3 tracks: this is NOT about career
# direction, it's about getting Hans out of in-person warehouse work onto
# something remote that pays at least $30/hr, broad enough to include
# "will train" postings. Kept entirely separate from QA Automation/SDET
# (that track's strict title list is untouched) — this is intentionally
# wider and lower-bar.
# 2026-06-26: Widened beyond manual QA/automation to general remote IT
# support/sysadmin/helpdesk roles per Hans's request — manual QA testing
# itself had become its own grind, and his actual IT background covers
# this broader set directly.
REMOTE_FLOOR_TITLE_KEYWORDS = [
    # Generic/manual QA — explicitly broader than SDET_TITLE_KEYWORDS
    "qa tester", "qa analyst", "qa specialist", "quality assurance tester",
    "quality assurance analyst", "quality assurance specialist",
    "manual qa", "manual tester", "software tester", "test analyst",
    "qa engineer", "quality engineer", "test engineer",
    # Automation tool-specific (tool exposure = realistic entry point)
    "selenium", "cypress tester", "automation tester", "automation analyst",
    "api tester", "api testing", "postman tester",
    # Remote/entry framing common in "will train" postings
    "remote qa", "work from home qa", "wfh qa", "entry level qa",
    "junior qa", "associate qa", "qa trainee",
    "no experience qa", "will train qa", "training provided qa",
    # 2026-06-26: General remote IT — added per Hans's request to widen
    # this track beyond manual QA/testing grind into broader IT support/
    # admin work, leveraging his 24+ years general IT background.
    "help desk", "helpdesk", "service desk", "desktop support",
    "it support", "it support specialist", "it support technician",
    "it support analyst", "remote it support", "technical support specialist",
    "technical support analyst", "technical support representative",
    "technical support engineer", "systems administrator",
    "system administrator", "sysadmin", "network administrator",
    "it technician", "it analyst", "it specialist", "it generalist",
    "computer support specialist", "end user support", "end-user support",
    "noc analyst", "noc technician", "network operations center",
]
REMOTE_FLOOR_HIGH_KEYWORDS = [
    "manual testing", "test cases", "test case design", "bug tracking",
    "regression testing", "functional testing", "uat", "user acceptance testing",
    "selenium", "cypress", "postman", "api testing", "test plans",
    "defect tracking", "black box testing", "exploratory testing",
    # General IT support/admin signals
    "active directory", "windows server", "network troubleshooting",
    "ticketing system", "remote desktop support", "hardware troubleshooting",
    "software installation", "vpn troubleshooting", "office 365", "azure ad",
    "printer support", "password reset", "incident management",
    "tier 1 support", "tier 2 support", "tier 1 it", "tier 2 it",
]
REMOTE_FLOOR_BONUS_KEYWORDS = [
    "jira", "testrail", "zephyr", "qtest", "agile", "scrum",
    "sql", "python", "javascript", "ci/cd", "jenkins", "github actions",
    "will train", "training provided", "no experience necessary",
    "no prior experience required", "entry level welcome",
    # General IT support tools/certs
    "itil", "comptia", "comptia a+", "network+", "security+",
    "servicenow", "zendesk", "freshservice", "remedy",
]
# Phrases that signal pay is well below even the lower ($25/hr remote)
# floor, even before we try to parse exact numbers — fast-path rejection.
# 2026-06-26: Trimmed from $15-29 down to $15-24 — $25-29/hr now needs to
# go through the real floor comparison in meets_pay_floor(), since $25/hr
# is a valid remote rate post-tiering (it was uniformly rejected when the
# floor was a flat $30/hr).
REMOTE_FLOOR_LOW_PAY_SIGNALS = [
    "$15/hr", "$16/hr", "$17/hr", "$18/hr", "$19/hr", "$20/hr",
    "$21/hr", "$22/hr", "$23/hr", "$24/hr",
]

#
# STRICT TITLE FILTER
#
REQUIRED_TITLE_KEYWORDS = [
    # Performance engineering
    "performance engineer", "performance test", "performance tester",
    "performance analyst", "performance specialist",
    "loadrunner", "load runner", "vugen", "lre",
    "load test", "load engineer",
    "sr. performance", "sr performance", "senior performance",
    "staff performance",
    # QA Performance hybrid only - no general QA
    "qa performance engineer", "performance qa engineer",
    # SDET (entry-level path)
    "sdet", "junior sdet", "entry level sdet", "entry-level sdet",
    "associate sdet", "software engineer in test",
    "junior software engineer in test", "junior test engineer",
    # AI engineering
    "ai engineer", "ml engineer", "machine learning engineer",
    "artificial intelligence engineer", "ai developer",
    "junior ai", "entry level ai", "associate ai",
    "mid level ai", "intermediate ai",
    # Prompt Engineering — Hans's sweet spot
    "prompt engineer", "prompt developer", "prompt specialist",
    "generative ai engineer", "gen ai engineer",
    # Agent / LLM Application roles
    "ai agent", "agent engineer", "llm developer", "llm engineer",
    "llm application", "ai application engineer", "ai application developer",
    "langchain", "agentic",
    # Agentic AI / AI Developer explicit phrases
    "agentic ai developer", "agentic ai engineer", "ai agent developer",
    # AI Automation / Integration
    "ai automation", "ai integration engineer", "ai solutions engineer",
    "ai workflow", "ai pipeline engineer",
    # AI + Performance hybrid
    "ai performance", "ml performance", "ai test engineer",
    "ai quality engineer", "ai qa engineer", "ai qa",
    "mlops", "ai reliability",
    # COBOL/Mainframe
    "cobol", "cics", "mainframe developer", "mainframe programmer",
    "cobol developer", "cobol programmer", "cics developer",
    "mainframe engineer", "legacy developer", "z/os developer",
]

# Titles to EXCLUDE even if they match required keywords
EXCLUDED_TITLE_TERMS = [
    "engineering manager", "manager of engineering", "director of engineering",
    "vp of engineering", "head of engineering", "vp engineering",
    "engineering director", "director of ai", "head of ai",
    "manager, ai", "ai manager", "ml manager",
    "manager of ai", "manager of ml", "manager of machine learning",
    "chief", "cto", "cio", "president", "vice president",
    "supplier", "supply chain", "procurement", "vendor performance",
    "manufacturing", "mechanical", "hardware", "electrical",
    "civil engineer", "structural", "chemical engineer",
    "gas turbine", "turbine engineer", "turbine performance",
    "nascar", "motorsport", "race car", "racing engineer",
    "automotive performance", "vehicle performance", "engine performance",
    "aero engine", "aero engines", "aerospace engineer", "aeronautical", "mechanical performance",
    "petroleum engineer", "mining engineer", "nuclear engineer",
    "jet engine", "propulsion engineer",
    "environmental engineer", "geotechnical", "acoustics engineer",
    "working nomads", "workingnomads.com",
    "field engineer", "sales engineer", "solutions engineer",
    "pre-sales", "presales", "customer success engineer",
    "platform engineer", "infrastructure engineer", "devops engineer",
    "site reliability engineer", "sre ", "cloud engineer",
    "capacity and performance", "capacity engineer", "capacity planning engineer",
    "senior ai/ml", "senior machine learning", "senior ml ",
    "principal engineer", "principal ai", "principal ml",
    "staff ai", "staff ml", "staff machine learning",
    "freelance", "part-time", "part time", "8-20 hrs", "8-20hrs",
    "contract to hire via", "gig ", "temporary staffing",
    "outsource", "outsourcing", "outstaffing",
    "kuubik", "upwork", "fiverr", "toptal", "guru.com",
    "/mo", "/mp", "per month usd", "usd/month",
    # Indian job market terms
    "fresher", "freshers", "fresher job", "fresher role",
    # People manager titles (not IC roles)
    "software development manager", "sdm,", "sdm ", " sdm,",
    "software dev manager", "development manager",
    "engineering lead manager", "group engineering manager",
    "technical program manager", "tpm ", "tpm,",
    "program manager", "product manager",
    # Hard language requirements Hans doesn't have
    "golang is must", "golang required", "must know golang",
    "rust required", "rust is must", "ruby required", "ruby is must",
]

def is_relevant_title(title):
    """Returns True only if the job title contains a required technical keyword
    AND does not contain an excluded management term."""
    t = title.lower()
    # Reject titles that are search result pages not individual jobs
    search_page_patterns = [
        r"\d+\s+(remote|jobs|vacancies|openings|positions)",
        r"jobs in remote",
        r"vacancies in (april|may|june|july|august|september|october|november|december|january|february|march|\d{4})",
        r"now hiring",
        r"employment in",
        r"\$\d+.*jobs",
        r"work from home.*jobs",
        r"flexible remote.*jobs",
        r"\d+,\d+ .* jobs",
        r"latin america",
        r"latam",
        r"south america",
        # Career guides and blog articles
        r"how to become",
        r"complete guide",
        r"career guide",
        r"what is a.*engineer",
        r"salary guide",
        r"salaries \d{4}",
        r"developer salaries",
        r"engineer salaries",
        r"best.*jobs in \d{4}",
        r"top \d+.*jobs",
        # Job application form pages
        r"^job application for ",
        r"^apply (now|for|to) ",
        r"hiring\] ",
    ]
    for pattern in search_page_patterns:
        if re.search(pattern, t):
            return False
    # First check it has a required keyword — EITHER the existing strict
    # list (Performance/AI/COBOL/SDET) OR the broader Remote Floor list
    # (Track 4 — manual QA/automation/will-train, intentionally wider).
    has_required = any(kw in t for kw in REQUIRED_TITLE_KEYWORDS)
    has_remote_floor = any(kw in t for kw in REMOTE_FLOOR_TITLE_KEYWORDS)
    if not (has_required or has_remote_floor):
        return False
    # Then make sure it is not a management role — shared exclusion list
    # applies to every track, including Remote Floor (e.g. "QA Manager"
    # should be rejected here too).
    if any(excl in t for excl in EXCLUDED_TITLE_TERMS):
        return False
    return True


# SDET title keywords — explicit list for accurate detection
SDET_TITLE_KEYWORDS = [
    "sdet", "software engineer in test", "software development engineer in test",
    "test automation engineer", "automation test engineer",
]

def get_job_track(title, description):
    """Identify which track a job belongs to and check level requirements.
    Returns (track_name, level_ok, level_signal).

    level_signal is a short diagnostic string describing WHICH specific
    rule produced the level_ok value — e.g. "title:senior-keyword",
    "desc:10+ years pattern", "desc:senior_desc_signal:lead a team",
    or "none:no-seniority-signal-found" when level_ok=True because
    nothing disqualifying was detected (as opposed to something
    explicitly confirming entry/mid level). This exists so
    job_decisions.json can persist WHY a job passed or failed seniority
    screening — without it, a "too_senior" decision from Hans can never
    be checked against what the filter actually saw, since the original
    job description text isn't otherwise stored anywhere."""
    text = (title + " " + description).lower()
    t = title.lower()

    # FIX: generic/bare AI terms (llm, generative ai, deep learning, etc.)
    # only count if they're in the TITLE — otherwise a QA/other-track job
    # whose description mentions "LLM observability" or "uses generative AI
    # features" in passing gets wrongly classified as AI Engineering,
    # stealing a career-track slot and never reaching its real track.
    # Specific multi-word phrases (prompt engineer, ai agent, mlops
    # engineer, etc.) are distinctive enough to stay as full-text triggers.
    is_ai = any(kw in t for kw in AI_GENERIC_TERMS) or any(kw in text for kw in AI_SPECIFIC_PHRASES)
    is_sdet = any(kw in t for kw in SDET_TITLE_KEYWORDS)
    is_qa = any(kw in text for kw in QA_HIGH_KEYWORDS)

    if is_ai:
        senior_title_kws = ["senior", "sr.", "sr ", "lead ", "principal", "staff ", "director", "head of", "vp "]
        matched_senior_kw = next((s for s in senior_title_kws if s in t), None)
        if matched_senior_kw:
            return "AI Engineering", False, f"title:senior-keyword:{matched_senior_kw.strip()}"

        # Check description for experience requirements
        full_text = text

        # Block if requires 3+ years for agent/LLM roles (tighter than general AI)
        is_agent_role = any(kw in text for kw in [
            "ai agent", "agentic", "llm engineer", "llm developer",
            "prompt engineer", "langchain", "llm application"
        ])
        exp_threshold = 3 if is_agent_role else 5

        exp_patterns = [
            r"(\d+)\+\s*years?\s*(of\s*)?(experience|exp)",
            r"minimum\s*(of\s*)?(\d+)\s*years?",
            r"at least\s*(\d+)\s*years?",
            r"(\d+)\s*to\s*(\d+)\s*years?\s*(of\s*)?(experience|exp)",
            r"(\d+)\s*-\s*(\d+)\s*years?\s*(of\s*)?(experience|exp)",
            r"(\d+)\s*years?\s*(of\s*)?(relevant|related|professional|hands.on)",
        ]
        for pattern in exp_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                try:
                    first_num = next((x for x in match if x and x.isdigit()), None)
                    if first_num and int(first_num) >= exp_threshold:
                        return "AI Engineering", False, f"desc:experience-pattern:{first_num}+years (threshold {exp_threshold})"
                except Exception:
                    pass

        # Allow if explicitly entry/mid OR if no strong seniority signal in description
        entry_mid_signals = [
            "entry level", "entry-level", "junior", "associate", "new grad",
            "recent graduate", "0-2 years", "0-3 years", "1-3 years",
            "mid level", "mid-level", "intermediate", "2-4 years", "3-5 years",
            "no experience required", "training provided",
        ]
        senior_desc_signals = [
            # Original (kept)
            "extensive experience", "proven track record", "expert level",
            "deep expertise", "seasoned", "7+ years", "8+ years", "10+ years",
            "subject matter expert", "sme ", "advanced degree required",
            "5+ years", "6+ years", "significant experience",
            # Added — additional year-count phrasings the regex misses
            "9+ years", "12+ years", "15+ years", "20+ years",
            "a decade", "over a decade", "decade of experience", "decade plus",
            "ten years", "fifteen years", "twenty years",
            # Added — seniority-by-responsibility phrasings (implied senior)
            "lead a team", "lead the team", "leading a team", "team lead",
            "mentor junior", "mentor engineers", "mentor the team",
            "manage engineers", "managing engineers", "manage a team",
            "own the architecture", "set technical direction", "drive technical strategy",
            "principal level", "principal-level", "staff level", "staff-level",
            "distinguished engineer", "fellow engineer",
            # Added — seniority-by-credential phrasings
            "phd required", "phd preferred", "ph.d. required", "ph.d. preferred",
            "doctorate required", "masters required", "master's required",
            # Added — seniority-by-narrative phrasings
            "highly experienced", "veteran engineer", "battle-tested",
            "thought leader", "recognized expert", "deep domain knowledge",
        ]
        matched_entry_mid = [sig for sig in entry_mid_signals if sig in full_text]
        matched_senior_desc = [sig for sig in senior_desc_signals if sig in full_text]
        has_entry_mid = bool(matched_entry_mid)
        has_senior_desc = bool(matched_senior_desc)

        if has_senior_desc and not has_entry_mid:
            return "AI Engineering", False, f"desc:senior_desc_signal:{matched_senior_desc[0]}"

        if has_entry_mid:
            return "AI Engineering", True, f"desc:entry_mid_signal:{matched_entry_mid[0]}"
        return "AI Engineering", True, "none:no-seniority-signal-found"

    if is_sdet:
        # FIXED: was falling through to QA branch. Now correctly returns.
        level_ok = any(lvl in t for lvl in ["junior", "entry", "associate", "entry-level"])
        if level_ok:
            return "QA Automation", True, "title:explicit-junior-keyword"
        # If no level signal in title, allow it through (mid-level SDET is fine)
        senior_kws = ["senior", "sr.", "sr ", "lead ", "principal", "staff "]
        matched_senior_kw = next((s for s in senior_kws if s in t), None)
        if matched_senior_kw:
            return "QA Automation", False, f"title:senior-keyword:{matched_senior_kw.strip()}"
        return "QA Automation", True, "none:no-seniority-signal-found"

    if is_qa:
        matched_level_kw = next((lvl for lvl in QA_AUTOMATION_LEVEL_FILTER if lvl in t), None)
        if matched_level_kw:
            return "QA Automation", True, f"title:explicit-level-keyword:{matched_level_kw}"
        senior_kws = ["senior", "lead", "principal", "staff", "director"]
        matched_senior_kw = next((s for s in senior_kws if s in t), None)
        if matched_senior_kw:
            return "QA Automation", False, f"title:senior-keyword:{matched_senior_kw}"
        return "QA Automation", True, "none:no-seniority-signal-found"

    # ── Track 4: Remote Income Floor ────────────────────────────
    # Checked AFTER AI/SDET/QA-hybrid (those are higher-priority, more
    # specific matches and should never get reclassified down into this
    # broader bucket). This track exists for relief, not career direction —
    # broad manual QA / automation-tool / will-train postings, PLUS COBOL
    # (Hans has the experience; COBOL was previously falling through to
    # Performance Engineering with no real track of its own). Senior-only
    # roles are excluded here too (this track is meant to be an accessible
    # entry point, not a senior IC role) — except COBOL, where Hans's
    # actual 24+ years includes COBOL/CICS depth, so seniority isn't a
    # disqualifier for that subset.
    is_cobol = any(kw in text for kw in COBOL_HIGH_KEYWORDS)
    is_remote_floor = any(kw in t for kw in REMOTE_FLOOR_TITLE_KEYWORDS) or \
                       any(kw in text for kw in REMOTE_FLOOR_HIGH_KEYWORDS)
    if is_cobol:
        # No seniority exclusion for COBOL — Hans's background covers it.
        return "Gap Track", True, "none:cobol-seniority-exempt"
    if is_remote_floor:
        senior_kws = ["senior", "sr.", "sr ", "lead ", "principal", "staff ", "director", "manager"]
        matched_senior_kw = next((s for s in senior_kws if s in t), None)
        if matched_senior_kw:
            return "Gap Track", False, f"title:senior-keyword:{matched_senior_kw.strip()}"
        return "Gap Track", True, "none:no-seniority-signal-found"

    # Performance Engineering - Senior OK only if LoadRunner/VuGen/LRE mentioned
    senior_kws = ["senior", "sr.", "sr ", "lead", "principal", "staff", "director", "head of", "vp"]
    matched_senior_kw = next((s for s in senior_kws if s in t), None)
    has_loadrunner = any(kw in text for kw in ["loadrunner", "vugen", "lre", "load runner", "vuser"])
    if matched_senior_kw and not has_loadrunner:
        return "Performance Engineering", False, f"title:senior-keyword:{matched_senior_kw.strip()}-no-loadrunner"  # Senior but no LoadRunner = skip
    if matched_senior_kw and has_loadrunner:
        return "Performance Engineering", True, f"none:senior-but-loadrunner-present"
    return "Performance Engineering", True, "none:no-seniority-signal-found"


# LoadRunner-specific terms get highest priority
LOADRUNNER_PRIORITY = ["loadrunner", "vugen", "lre", "vuser", "lr enterprise"]

# AI/Hybrid roles that deserve priority scoring when in title
AI_TITLE_PRIORITY = [
    # Prompt Engineering — highest priority for Hans
    "prompt engineer", "prompt developer", "prompt specialist",
    "generative ai engineer", "gen ai engineer",
    # Agent / LLM Application
    "ai agent", "agent engineer", "llm developer", "llm engineer",
    "llm application", "ai application engineer", "langchain",
    # Agentic AI / AI Developer roles
    "agentic ai developer", "agentic ai engineer", "ai agent developer",
    "ai developer", "ai application developer", "agentic",
    # AI Automation / Integration
    "ai automation engineer", "ai integration engineer", "ai solutions engineer",
    # AI + Performance hybrid
    "mlops", "ai engineer", "ml engineer", "machine learning engineer",
    "ai test engineer", "ai quality engineer", "ai performance",
    "ai automation", "ai reliability",
]

def score_job(title, description):
    text = (title + " " + description).lower()
    t = title.lower()
    score = 0
    matched = []

    # LoadRunner in the job TITLE gets massive bonus
    if any(kw in t for kw in LOADRUNNER_PRIORITY):
        score += 50
        matched.append("LoadRunner-in-title")

    # AI/hybrid roles in title get a good boost
    for kw in AI_TITLE_PRIORITY:
        if kw in t:
            score += 20
            matched.append(f"AI-title:{kw}")
            break  # only count once

    # NOTE: COBOL-specific scoring removed from here — COBOL jobs always
    # classify into "Gap Track" before get_job_track() ever
    # falls through to Performance Engineering (see is_cobol check), so
    # the old "COBOL = 2pts, last resort" weights below were dead code:
    # they could never actually run for an actual COBOL job. Proper COBOL
    # scoring now lives in the Remote Income Floor section below, sized
    # to actually clear that track's 20pt threshold.

    # LoadRunner anywhere in description = high priority
    for kw in LOADRUNNER_PRIORITY:
        if kw in text and kw + "-in-title" not in matched:
            score += 50
            matched.append(kw)

    # JMeter-only penalty: if JMeter mentioned but NO LoadRunner → not Hans's primary strength
    has_jmeter = "jmeter" in text
    has_loadrunner = any(kw in text for kw in LOADRUNNER_PRIORITY)
    if has_jmeter and not has_loadrunner:
        score -= 30
        matched.append("jmeter-only-penalty")

    # Performance keywords = 35 pts
    for kw in PERF_HIGH_KEYWORDS:
        if kw in text and kw not in matched:
            score += 35
            matched.append(kw)
    # QA Performance hybrid = 20 pts (only if also has performance keywords)
    qa_perf_keywords = ["qa performance engineer", "performance qa", "performance quality"]
    for kw in qa_perf_keywords:
        if kw in text and kw not in matched:
            score += 20
            matched.append(kw)
    # AI keywords = 20 pts (title already scored above). Same generic/
    # specific split as classification: generic bare terms only score if
    # in the title (avoid inflating score from a passing description
    # mention); specific phrases still score from anywhere in the text.
    for kw in AI_GENERIC_TERMS:
        if kw in t and kw not in matched:
            score += 20
            matched.append(kw)
    for kw in AI_SPECIFIC_PHRASES:
        if kw in text and kw not in matched:
            score += 20
            matched.append(kw)
    # Bonus keywords = 3 pts
    for kw in PERF_BONUS_KEYWORDS + QA_BONUS_KEYWORDS + AI_BONUS_KEYWORDS:
        if kw in text and kw not in matched:
            score += 3
            matched.append(kw)

    # ── Track 4: Remote Income Floor scoring ─────────────────────
    # Separate, modest point values — this track's purpose is "realistic
    # and pays the floor," not "maximize keyword density." 25pts in title
    # is enough to clear the per-track MIN_SCORES threshold on its own.
    for kw in REMOTE_FLOOR_TITLE_KEYWORDS:
        if kw in t and kw not in matched:
            score += 25
            matched.append(f"remote-floor-title:{kw}")
            break  # only count once, same pattern as AI_TITLE_PRIORITY
    for kw in REMOTE_FLOOR_HIGH_KEYWORDS:
        if kw in text and kw not in matched:
            score += 15
            matched.append(kw)
    for kw in REMOTE_FLOOR_BONUS_KEYWORDS:
        if kw in text and kw not in matched:
            score += 3
            matched.append(kw)

    # COBOL scoring (within Remote Income Floor) — sized to actually clear
    # that track's 20pt threshold on a title match alone, same pattern as
    # REMOTE_FLOOR_TITLE_KEYWORDS above. 25 in title mirrors the rest of
    # the track; 10 in description (anywhere) gives partial credit even
    # without a title hit, since COBOL/CICS/mainframe terms are specific
    # enough not to need the generic/specific split treatment AI needed.
    if any(kw in t for kw in ["cobol", "cics", "mainframe", "jcl", "vsam", "z/os", "zos", "mvs"]) and \
       not any(m.startswith("remote-floor-title:") for m in matched):
        score += 25
        matched.append("cobol-title-match")
    for kw in COBOL_HIGH_KEYWORDS + COBOL_BONUS_KEYWORDS:
        if kw in text and kw not in matched:
            score += 10
            matched.append(kw)

    # ── Strip internal bookkeeping tags before returning ─────────
    # AI-title:<kw>, remote-floor-title:<kw>, and cobol-title-match are
    # sentinel entries used only to prevent double-counting within this
    # function (e.g. "don't also award the description-level COBOL bonus
    # if we already scored a title match"). They were never meant to be
    # real, displayable keywords — but matched_keywords feeds the email's
    # "Matched Skills" line AND the free cover letter templates directly,
    # so a raw sentinel like "cobol-title-match" was leaking into actual
    # cover letter text as if it were a skill. Strip them all here, once,
    # so every call site (there are 9+) gets clean data automatically.
    display_keywords = [
        m for m in matched
        if not m.startswith("AI-title:")
        and not m.startswith("remote-floor-title:")
        and m != "cobol-title-match"
        and m != "jmeter-only-penalty"
    ]
    return score, list(set(display_keywords))


def passes_filters(title, desc, posted, location, url_job, company, source_name, salary=""):
    """
    Run a candidate through every filter stage and record the funnel count
    at each stage it survives. Returns:
      (passed: bool, score: int, matched: list, track: str, level_signal: str)
    The job has already been counted in funnel.add_raw() before this is called.

    level_signal is "" for any rejection that happens BEFORE classification
    runs (recency/title stages) — there's nothing meaningful to report yet.
    Once get_job_track() has run, level_signal carries its diagnostic
    string through every subsequent return point, pass or fail, so the
    eventual job_decisions.json record can show WHY level_ok came out the
    way it did (see get_job_track's docstring for the full rationale).

    salary is optional — defaults to "" for sources that don't pass it.
    Pay-floor checking (Track 4 only) falls back to scanning title+description
    for pay info if salary isn't supplied; it never raises on a missing salary.

    Uses short-circuit evaluation: as soon as a filter rejects, returns False
    without checking later stages.
    """
    # Stage: recency
    if not is_recent(posted):
        return False, 0, [], "", ""
    funnel.record("after_recency")

    # Stage: title
    if not is_relevant_title(title):
        return False, 0, [], "", ""
    funnel.record("after_title")

    # Stage: level (track + level_ok)
    track, level_ok, level_signal = get_job_track(title, desc)
    if not level_ok:
        return False, 0, [], "", level_signal
    funnel.record("after_level")

    # Stage: score
    score, matched = score_job(title, desc)
    if score <= 0:
        return False, 0, [], "", level_signal
    funnel.record("after_score")

    # Stage: US/remote (with KC-metro local-hybrid carve-out)
    # Accept if: (1) fully remote-US-eligible, OR
    #            (2) on-site/hybrid AND within KC metro commuting range
    # Reject hybrid/on-site jobs outside KC metro.
    # EXCEPTION: Track 4 (Remote Income Floor) gets NO hybrid/onsite
    # carve-out at all, even for KC metro — the entire point of this track
    # is "no commute, work from home, save gas, save the body." A KC-local
    # hybrid QA role doesn't satisfy that goal even though it would for
    # the other tracks.
    # SUB-EXCEPTION (COBOL): Hans is willing to do KC-metro hybrid/onsite
    # COBOL work IF it pays $55+/hr — but pay text isn't available at this
    # stage (salary field is populated post-aggregation in main()). So
    # COBOL jobs get the standard KC-metro carve-out treatment HERE (same
    # as Performance/AI/QA — don't reject yet), and the real $55/hr-based
    # accept/reject decision for hybrid COBOL jobs happens in main(),
    # where job["salary"] actually exists.
    # 2026-06-26: Removed the "Gap Track gets NO hybrid carve-out" rule
    # above per Hans's request — he's now fine with KC-metro hybrid for
    # this track too (not just COBOL), since the broader general-IT
    # postings added to this track are often local/hybrid. Gap Track now
    # gets the SAME standard KC-metro carve-out as every other track.
    is_cobol_job = any(kw in (title + " " + desc).lower() for kw in COBOL_HIGH_KEYWORDS)
    if not is_us_remote(title, desc, location):
        # Failed remote check — last chance: is it KC-local hybrid/on-site?
        if is_onsite_or_hybrid(title, desc, location) and is_kc_metro_local(title, desc, location):
            pass  # KC-local hybrid/on-site is acceptable (final $/hr-based
                   # decision for COBOL happens later in main())
        else:
            return False, score, matched, track, level_signal
    funnel.record("after_us")

    # NOTE: pay-floor checking for Track 4 (Remote Income Floor) happens
    # post-aggregation in main(), not here — salary text isn't extracted
    # from the raw source APIs until after passes_filters() runs and the
    # job dict is built (same point MIN_SCORES per-track thresholds are
    # applied). Doing it here would mean checking against title+description
    # only, missing each source's actual salary field.

    # Stage: blocked site/company
    if is_blocked_site(url_job) or is_blocked_company(title, desc, company):
        return False, score, matched, track, level_signal
    funnel.record("after_blocked")

    # NOTE: kept_by_sources is set in main() via funnel.set_stage()
    # using len(all_jobs) after aggregation, so we don't double-count here.
    return True, score, matched, track, level_signal


#
# SOURCE 1: RemoteOK (free public API)
#
def search_remoteok():
    print("[SEARCH] Searching RemoteOK...")
    jobs = []
    try:
        headers = {"User-Agent": "JobSearchBot/1.0 (personal use)"}
        resp = requests.get("https://remoteok.com/api", headers=headers, timeout=15)
        data = resp.json()
        for item in data[1:]:  # first item is metadata
            title  = item.get("position", "")
            desc   = item.get("description", "")
            posted = item.get("date", "")
            url_job = item.get("url", "")
            company = item.get("company", "N/A")

            funnel.add_raw("RemoteOK")
            # Debug breadcrumb (preserve existing log style)
            if DEBUG_MODE and title:
                score_quick, _ = score_job(title, desc)
                track_quick, level_ok_quick, level_signal_quick = get_job_track(title, desc)
                if score_quick == 0:
                    print(f"   [DEBUG] RemoteOK FILTERED-score: {title[:60]}")
                elif not level_ok_quick:
                    print(f"   [DEBUG] RemoteOK FILTERED-level ({level_signal_quick}): {title[:60]}")
                elif not is_recent(posted):
                    print(f"   [DEBUG] RemoteOK FILTERED-date: {title[:60]}")
                elif not is_relevant_title(title):
                    print(f"   [DEBUG] RemoteOK FILTERED-title: {title[:60]}")

            passed, score, matched, track, level_signal = passes_filters(
                title, desc, posted, "", url_job, company, "RemoteOK"
            )
            if passed:
                jobs.append({
                    "source": "RemoteOK",
                    "title": title,
                    "company": company,
                    "url": url_job,
                    "posted": posted,
                    "description": desc[:500],
                    "score": score,
                    "matched_keywords": matched,
                    "track": track,
                    "level_signal": level_signal,
                })
        print(f"   [OK] RemoteOK: {len(jobs)} relevant jobs found")
    except Exception as e:
        print(f"   [ERROR] RemoteOK error: {e}")
        log_error(f"RemoteOK error: {e}")
    return jobs

#
# SOURCE 1b: Remotive API (free, no key required)
# https://remotive.com/api/remote-jobs
#
def search_remotive():
    print("[SEARCH] Searching Remotive...")
    jobs = []
    try:
        headers = {"User-Agent": "JobSearchBot/1.0 (personal use)"}
        # Pull software-dev category — covers AI/ML, QA, and perf roles.
        resp = requests.get(
            "https://remotive.com/api/remote-jobs?category=software-dev",
            headers=headers, timeout=15
        )
        data = resp.json()
        items = data.get("jobs", [])
        if DEBUG_MODE:
            print(f"   [DEBUG] Remotive: {len(items)} raw results, status {resp.status_code}")

        for item in items:
            title   = item.get("title", "")
            desc    = item.get("description", "")
            url_job = item.get("url", "")
            posted  = item.get("publication_date", "")
            company = item.get("company_name", "N/A")
            location = (item.get("candidate_required_location", "") or "").lower()

            # Remotive is remote-only by design, but some jobs restrict
            # to specific regions. Keep only worldwide or US-friendly.
            if location and not any(loc in location for loc in
                                    ["worldwide", "anywhere", "usa", "us only",
                                     "united states", "americas", "north america"]):
                if DEBUG_MODE:
                    print(f"   [DEBUG] Remotive FILTERED-region ({location[:30]}): {title[:50]}")
                continue

            funnel.add_raw("Remotive")

            # Debug breadcrumb matching RemoteOK style
            if DEBUG_MODE and title:
                score_quick, _ = score_job(title, desc)
                track_quick, level_ok_quick, level_signal_quick = get_job_track(title, desc)
                if score_quick == 0:
                    print(f"   [DEBUG] Remotive FILTERED-score: {title[:60]}")
                elif not level_ok_quick:
                    print(f"   [DEBUG] Remotive FILTERED-level ({level_signal_quick}): {title[:60]}")
                elif not is_recent(posted):
                    print(f"   [DEBUG] Remotive FILTERED-date: {title[:60]}")
                elif not is_relevant_title(title):
                    print(f"   [DEBUG] Remotive FILTERED-title: {title[:60]}")

            passed, score, matched, track, level_signal = passes_filters(
                title, desc, posted, location, url_job, company, "Remotive"
            )
            if passed:
                jobs.append({
                    "source": "Remotive",
                    "title": title,
                    "company": company,
                    "url": url_job,
                    "posted": posted,
                    "description": desc[:500],
                    "score": score,
                    "matched_keywords": matched,
                    "track": track,
                    "level_signal": level_signal,
                })
        print(f"   [OK] Remotive: {len(jobs)} relevant jobs found")
    except Exception as e:
        print(f"   [ERROR] Remotive error: {e}")
        log_error(f"Remotive error: {e}")
    return jobs

#
# SOURCE 2b: Working Nomads (free public JSON, no auth)
# Endpoint: https://www.workingnomads.co/api/exposed_jobs/
# Curated remote jobs; we filter to Development/SysAdmin/Data categories
# which map to LoadRunner/Performance (Tier 1) and AI/Perf hybrid (Tier 2).
#
def search_working_nomads():
    print("[SEARCH] Searching Working Nomads...")
    jobs = []
    try:
        headers = {"User-Agent": "JobSearchBot/1.0 (personal use)"}
        resp = requests.get(
            "https://www.workingnomads.co/api/exposed_jobs/",
            headers=headers, timeout=20
        )
        # API returns a flat JSON list
        items = resp.json() if resp.status_code == 200 else []
        if not isinstance(items, list):
            items = []
        if DEBUG_MODE:
            print(f"   [DEBUG] Working Nomads: {len(items)} raw results, status {resp.status_code}")

        for item in items:
            title    = item.get("title", "") or ""
            desc     = item.get("description", "") or ""
            url_job  = item.get("url", "") or ""
            posted   = item.get("pub_date") or item.get("publication_date") or ""
            company  = item.get("company_name", "") or "N/A"
            location = (item.get("location", "") or "").lower()
            tags     = " ".join(item.get("tags", []) or []).lower() if isinstance(item.get("tags"), list) else ""

            # Region gate — Working Nomads tags some jobs to specific regions.
            # Allow worldwide/anywhere/USA/Americas; reject obvious non-US restrictions.
            if location and not any(loc in location for loc in
                                    ["worldwide", "anywhere", "usa", "us only",
                                     "united states", "americas", "north america",
                                     "remote"]):
                # Check tags too — sometimes region is in tags not location field
                if not any(loc in tags for loc in
                           ["worldwide", "anywhere", "usa", "united states",
                            "americas", "north america"]):
                    if DEBUG_MODE:
                        print(f"   [DEBUG] WorkingNomads FILTERED-region ({location[:30]}): {title[:50]}")
                    continue

            funnel.add_raw("WorkingNomads")

            if DEBUG_MODE and title:
                score_quick, _ = score_job(title, desc)
                track_quick, level_ok_quick, level_signal_quick = get_job_track(title, desc)
                if score_quick == 0:
                    print(f"   [DEBUG] WorkingNomads FILTERED-score: {title[:60]}")
                elif not level_ok_quick:
                    print(f"   [DEBUG] WorkingNomads FILTERED-level ({level_signal_quick}): {title[:60]}")
                elif not is_recent(posted):
                    print(f"   [DEBUG] WorkingNomads FILTERED-date: {title[:60]}")
                elif not is_relevant_title(title):
                    print(f"   [DEBUG] WorkingNomads FILTERED-title: {title[:60]}")

            passed, score, matched, track, level_signal = passes_filters(
                title, desc, posted, location, url_job, company, "WorkingNomads"
            )
            if passed:
                jobs.append({
                    "source": "WorkingNomads",
                    "title": title,
                    "company": company,
                    "url": url_job,
                    "posted": posted,
                    "description": desc[:500],
                    "score": score,
                    "matched_keywords": matched,
                    "track": track,
                    "level_signal": level_signal,
                    "salary": "",
                })
        print(f"   [OK] Working Nomads: {len(jobs)} relevant jobs found")
    except Exception as e:
        print(f"   [ERROR] Working Nomads error: {e}")
        log_error(f"Working Nomads error: {e}")
    return jobs

#
# SOURCE 2: Serper.dev Google Jobs API (2,500 free searches/month - direct apply links!)
# Sign up free at: https://serper.dev
#
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

def search_serper_jobs():
    print("[SEARCH] Searching Google Jobs via Serper...")
    jobs = []
    if not SERPER_API_KEY:
        print("   [WARN] Serper skipped - SERPER_API_KEY not set in environment")
        return jobs

    queries = [
        # LoadRunner/VuGen — direct ATS board targeting
        'site:boards.greenhouse.io "loadrunner" "remote"',
        'site:boards.greenhouse.io "performance engineer" "loadrunner"',
        'site:jobs.lever.co "loadrunner" "remote"',
        'site:jobs.lever.co "performance engineer" "loadrunner"',
        'site:jobs.ashbyhq.com "loadrunner" OR "vugen" "remote"',
        'site:myworkdayjobs.com "loadrunner" "performance engineer"',
        'site:myworkdayjobs.com "performance tester" "loadrunner"',
        'site:taleo.net "loadrunner" "performance engineer"',
        'site:jobs.icims.com "loadrunner" "performance engineer"',
        'site:jobs.jobvite.com "loadrunner" "performance engineer"',
        'site:dice.com/job-detail "loadrunner" remote',
        'site:dice.com/job-detail "vugen" remote',
        'site:dice.com/job-detail "performance test engineer" remote',
        'site:roberthalf.com "loadrunner" "performance" "remote"',
        # LRE / Performance Center specific
        '"LRE" OR "LoadRunner Enterprise" "performance engineer" remote',
        '"performance center" "loadrunner" remote',
        # Broader performance engineering with LR filter
        '"performance test engineer" "loadrunner" remote',
        '"performance engineer" "loadrunner" OR "vugen" remote',
        '"load test engineer" "loadrunner" remote',
        '"sr performance engineer" OR "senior performance engineer" "loadrunner" remote',
        # Prompt Engineering — Hans's sweet spot
        'site:boards.greenhouse.io "prompt engineer" "remote"',
        'site:jobs.lever.co "prompt engineer" "remote"',
        'site:jobs.ashbyhq.com "prompt engineer" "remote"',
        'site:myworkdayjobs.com "prompt engineer" remote',
        'site:dice.com/job-detail "prompt engineer" remote',
        '"prompt engineer" remote "generative ai"',
        '"prompt engineer" remote "llm"',
        '"prompt engineering" remote entry level OR mid level',
        # AI Agent / LLM Application roles
        'site:boards.greenhouse.io "ai agent" OR "llm developer" "remote"',
        'site:jobs.lever.co "llm engineer" OR "ai agent" "remote"',
        '"llm application developer" remote',
        '"ai agent developer" remote',
        '"agentic ai" engineer remote',
        '"langchain developer" OR "langchain engineer" remote',
        # AI Automation / Integration
        'site:boards.greenhouse.io "ai automation engineer" "remote"',
        'site:jobs.lever.co "ai integration engineer" "remote"',
        '"ai automation engineer" remote',
        '"ai integration engineer" remote',
        '"ai solutions engineer" remote entry level OR mid',
        '"generative ai engineer" remote',
        # AI/MLOps — direct ATS targeting
        'site:boards.greenhouse.io "mlops engineer" "remote"',
        'site:boards.greenhouse.io "ai engineer" "remote"',
        'site:jobs.lever.co "mlops engineer" "remote"',
        'site:jobs.lever.co "ai test engineer" "remote"',
        'site:jobs.lever.co "llm engineer" "remote"',
        'site:jobs.ashbyhq.com "ai engineer" "remote"',
        'site:myworkdayjobs.com "mlops engineer" remote',
        'site:dice.com/job-detail "mlops engineer" remote',
        'site:dice.com/job-detail "ai performance engineer" remote',
        # COBOL — direct targeting
        'site:dice.com/job-detail "cobol" "remote"',
        'site:boards.greenhouse.io "cobol" "remote"',
        'site:myworkdayjobs.com "cobol developer" remote',
        '"cobol developer" remote "w2"',
        '"mainframe developer" "cobol" remote',
        # Himalayas + BuiltIn
        'site:himalayas.app "loadrunner" OR "performance engineer" remote',
        'site:himalayas.app "ai engineer" OR "llm" remote',
        'site:builtin.com/job "ai engineer" OR "performance engineer" remote',
        'site:builtin.com/job "ai qa" OR "ai test" remote',
        # AI lane targeting — performance-engineer-bridges-to-AI
        '"AI QA engineer" OR "AI test engineer" remote',
        '"LLM evaluation engineer" remote',
        '"AI reliability engineer" remote',
        '"AI observability" engineer remote',
        '"LLM observability" engineer remote',
        '"AI SDET" remote',
        '"AI workflow engineer" remote',
        'site:jobs.lever.co "ai sdet" OR "llm test" "remote"',
        'site:boards.greenhouse.io "ai eval" OR "model evaluation" "remote"',
        'site:jobs.ashbyhq.com "ai qa" OR "ai test" "remote"',
    ]
    seen = set()
    for query in queries:
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "gl": "us",
                "hl": "en",
                "num": 10,
                "tbs": "qdr:w"
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 400:
                if DEBUG_MODE:
                    print(f"   [DEBUG] Serper '{query}': rate limited (400), skipping")
                time.sleep(3)
                continue
            data = resp.json()
            if DEBUG_MODE:
                print(f"   [DEBUG] Serper '{query}': {len(data.get('jobs', []))} jobs, {len(data.get('organic', []))} organic, status {resp.status_code}")
            # Check both jobs and organic results
            all_results = data.get("jobs", []) + data.get("organic", [])
            for item in all_results:
                title    = item.get("title", "")
                company  = (
                    item.get("company_name")
                    or item.get("company")
                    or item.get("source")
                    or ""
                )
                if not company:
                    # Best-effort: many aggregator/ATS titles follow the
                    # "Title - Company - Location" convention (Dice, etc.)
                    parts = [p.strip() for p in title.split(" - ") if p.strip()]
                    if len(parts) >= 2:
                        company = parts[1]
                if not company:
                    company = "N/A"
                desc     = item.get("description", item.get("snippet", ""))
                url_job  = item.get("applyLink", "") or item.get("link", "") or item.get("url", "")
                posted   = item.get("date", item.get("publishedDate", ""))
                # Skip search results pages - we want direct job postings only
                search_page_indicators = [
                    "jobs?q=", "job-search?", "jobs-search?", "/jobs/search",
                    "/jobs?", "q=ai+ml", "search?q=", "find-jobs",
                    "indeed.com/jobs", "indeed.com/q-", "linkedin.com/jobs/search",
                    "glassdoor.com/Job/jobs", "glassdoor.com/Job/remote",
                    "srch_il", "glassdoor.com/job/united-states",
                    "glassdoor.com/job/us-", "-jobs-srch_",
                    "monster.com/jobs/search",
                    "ziprecruiter.com/Jobs/", "ziprecruiter.com/jobs-search",
                    "naukri.com/loadrunner", "naukri.com/cobol", "naukri.com/",
                    "dice.com/jobs/q-", "dice.com/jobs?",
                    "jobs-in-remote", "jobs-in-usa", "job-vacancies",
                    "vacancies-in", "/remote-jobs?", "remote-jobs-in",
                    # Aggregator/listing pages (not single postings) —
                    # added after 2026-06-19 review found these scoring
                    # as top "matches" with cover letters generated for them
                    "/jobs/united-states", "/jobs/remote", "/jobs/usa",
                    "hire-remotely", "/hire-talent", "/talent/hire",
                ]
                if any(indicator in url_job.lower() for indicator in search_page_indicators):
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Serper FILTERED-searchpage: {title[:50]}")
                    continue
                # Title-based aggregator detection — catches listing pages
                # whose URL doesn't match a known pattern but whose title
                # gives it away (e.g. "578+ Agentic AI Jobs in United States",
                # "Hire the 64 Best Remote AI Automation...")
                _agg_title = title.lower()
                _looks_like_listing = (
                    re.match(r"^\d+\+?\s+.*\bjobs?\b", _agg_title)
                    or re.search(r"\bhire the \d+\b", _agg_title)
                    or re.search(r"\bbest remote\b.*\bjobs?\b", _agg_title)
                )
                if _looks_like_listing:
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Serper FILTERED-listing-title: {title[:50]}")
                    continue
                fp, fp_reason = is_false_positive_url(url_job)
                if fp:
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Serper FILTERED-{fp_reason}: {title[:50]}")
                    continue
                # Non-US filter — catch UK/EU/overseas roles that slip past
                non_us_reason = _is_non_us_serper_posting(title, desc, url_job)
                if non_us_reason:
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Serper FILTERED-non-US ({non_us_reason}): {title[:50]}")
                    continue
                location = item.get("location", "").lower()
                if url_job in seen:
                    continue
                seen.add(url_job)
                if "remote" not in location and "remote" not in (title + desc).lower():
                    continue

                # Pre-pipeline filters survived — count as raw candidate for funnel
                funnel.add_raw("Google Jobs (Serper)")
                passed, score, matched, track, level_signal = passes_filters(
                    title, desc, posted, location, url_job, company, "Google Jobs"
                )
                if passed:
                    jobs.append({
                        "source": "Google Jobs",
                        "title": title,
                        "company": company,
                        "url": url_job,
                        "posted": posted,
                        "description": desc[:500],
                        "score": score,
                        "matched_keywords": matched,
                        "track": track,
                        "level_signal": level_signal,
                        "salary": item.get("salary", ""),
                    })
        except Exception as e:
            print(f"   [ERROR] Serper error ({query}): {e}")
            log_error(f"Serper error ({query}): {e}")
        time.sleep(1.2)  # Rate limit: stay under Serper's burst threshold
    print(f"   [OK] Google Jobs: {len(jobs)} relevant jobs found")
    return jobs


#
# AMAZON JOBS SPOTLIGHT — Top 5 Amazon-specific postings (10 day window)
#
AMAZON_MAX_AGE_DAYS = 10

# Non-US location markers — if any appear in the title/snippet of an
# Amazon posting, we skip it.
AMAZON_NON_US_MARKERS = [
    "adci", "adci -", "- adci",
    # Europe
    "london", "dublin", "berlin", "munich", "madrid", "barcelona",
    "paris", "amsterdam", "luxembourg", "milan", "rome", "warsaw",
    "prague", "stockholm", "copenhagen", "zurich", "vienna",
    # Asia / Pacific
    "tokyo", "osaka", "bengaluru", "bangalore", "hyderabad", "chennai",
    "mumbai", "delhi", "pune", "gurgaon", "noida", "singapore",
    "sydney", "melbourne", "auckland", "shanghai", "beijing",
    "seoul", "manila", "jakarta", "ho chi minh", "hanoi",
    # Middle East / Africa
    "dubai", "abu dhabi", "riyadh", "doha", "tel aviv", "cape town",
    "johannesburg", "cairo", "nairobi",
    # Americas (non-US)
    "toronto", "vancouver", "montreal", "ottawa", "mexico city",
    "são paulo", "sao paulo", "rio de janeiro", "buenos aires",
    "santiago", "bogota", "bogotá", "lima",
    # Country-only mentions that reliably mean non-US
    "united kingdom", " uk ", "(uk)", "ireland", "germany", "france",
    "spain", "italy", "netherlands", "poland", "sweden", "denmark",
    "switzerland", "austria", "japan", "india", "china", "korea",
    "australia", "canada", "brazil", "mexico", "argentina",
]

def _is_non_us_amazon_posting(title, description):
    """Return True if title or snippet contains a non-US location marker."""
    blob = f" {title} {description} ".lower()
    for marker in AMAZON_NON_US_MARKERS:
        if marker in blob:
            return marker
    return None


#
# SERPER NON-US FILTER
#
SERPER_EXTRA_NON_US_CITIES = [
    # UK (beyond London/Dublin which Amazon list already has)
    "newcastle upon tyne", "newcastle", "manchester", "birmingham",
    "leeds", "liverpool", "sheffield", "nottingham", "bristol",
    "edinburgh", "glasgow", "cardiff", "belfast",
    # Ireland (beyond Dublin)
    "cork", "galway",
    # Germany (beyond Berlin/Munich/Frankfurt — Amazon list has these)
    "münchen", "cologne", "köln", "stuttgart", "düsseldorf", "dusseldorf",
    # France (beyond Paris)
    "lyon", "marseille", "toulouse", "nantes",
    # Spain / Portugal (beyond Madrid/Barcelona)
    "valencia", "seville", "lisbon", "porto",
    # Netherlands / Belgium (beyond Amsterdam)
    "rotterdam", "the hague", "utrecht", "brussels", "antwerp",
    # Italy / Nordics / EU (mostly already covered, plus a few)
    "turin", "naples", "gothenburg", "oslo", "helsinki",
    "krakow", "geneva", "athens",
    # Country-only — extra UK regions
    "england", "scotland", "wales", "northern ireland",
]

SERPER_NON_US_TLDS = (
    ".co.uk", ".uk", ".de", ".fr", ".es", ".it", ".nl",
    ".ie", ".eu", ".ch", ".se", ".dk", ".no", ".fi",
    ".pl", ".at", ".be", ".pt", ".cz", ".gr",
    ".com.au", ".co.nz", ".co.in", ".in", ".sg", ".com.sg",
    ".ca", ".com.br", ".mx", ".com.mx",
)

SERPER_URL_SLUG_MARKERS = (
    "-united-kingdom", "-england-", "-scotland-", "-wales-",
    "-germany-", "-france-", "-spain-", "-netherlands-",
    "-canada-", "-australia-", "-india-", "-singapore-",
    "-ireland-",
)


def _is_non_us_serper_posting(title, description, url):
    """
    Return a reason string if a Serper result is non-US, else None.
    """
    blob = f" {title} {description} ".lower()
    url_lower = (url or "").lower()

    # 1. Reuse Amazon marker list (covers most major non-US cities/countries)
    for marker in AMAZON_NON_US_MARKERS:
        if marker in blob:
            return f"city/country {marker.strip()}"

    # 2. Extra UK/EU cities Amazon list didn't cover
    for marker in SERPER_EXTRA_NON_US_CITIES:
        if marker in blob:
            return f"city {marker}"

    # 3. URL domain TLD check
    if "://" in url_lower:
        try:
            domain_part = url_lower.split("/")[2]
        except IndexError:
            domain_part = url_lower
    else:
        domain_part = url_lower.split("/")[0]
    for tld in SERPER_NON_US_TLDS:
        if domain_part.endswith(tld):
            return f"tld {tld}"

    # 4. URL slug check (aggregators encoding location in path)
    for marker in SERPER_URL_SLUG_MARKERS:
        if marker in url_lower:
            return f"urlslug {marker.strip('-')}"

    return None


def search_amazon_jobs():
    """Search amazon.jobs specifically for performance and AI roles."""
    print("[SEARCH] Searching Amazon Jobs spotlight...")
    jobs = []
    if not SERPER_API_KEY:
        print("   [WARN] Serper key not set — Amazon Jobs skipped")
        return jobs

    queries = [
        'site:amazon.jobs "performance engineer" OR "performance test"',
        'site:amazon.jobs "loadrunner" OR "vugen"',
        'site:amazon.jobs "prompt engineer" OR "ai engineer"',
        'site:amazon.jobs "mlops" OR "llm engineer"',
        'site:amazon.jobs "ai automation" OR "agentic"',
    ]

    seen = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=AMAZON_MAX_AGE_DAYS)

    for query in queries:
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "gl": "us",
                "hl": "en",
                "num": 10,
                "tbs": "qdr:m"  # Last month — wider window than regular search
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            all_results = data.get("jobs", []) + data.get("organic", [])

            for item in all_results:
                title   = item.get("title", "")
                desc    = item.get("description", item.get("snippet", ""))
                url_job = item.get("applyLink", "") or item.get("link", "") or item.get("url", "")
                posted  = item.get("date", item.get("publishedDate", ""))
                company = item.get("company", item.get("source", "Amazon"))

                # Must be from amazon.jobs
                if "amazon.jobs" not in url_job.lower():
                    continue
                if url_job in seen:
                    continue
                seen.add(url_job)

                # Skip overseas postings
                non_us_hit = _is_non_us_amazon_posting(title, desc)
                if non_us_hit:
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Amazon FILTERED-non-US ({non_us_hit}): {title[:60]}")
                    continue

                # Apply 10-day freshness filter.
                # Looser-fix design (2026-06-19): a missing or unparseable
                # date does NOT exclude the job (Amazon spotlight recall
                # matters more than strict filtering), but it IS tracked via
                # age_verified so the email can flag it instead of silently
                # claiming "Recent" for an unknown-age posting.
                age_verified = False
                if posted:
                    try:
                        parsed = parse_relative_date(str(posted))
                        if parsed is None:
                            parsed = dateparser.parse(str(posted))
                        if parsed:
                            if parsed.tzinfo is None:
                                parsed = parsed.replace(tzinfo=timezone.utc)
                            if parsed < cutoff:
                                continue
                            age_verified = True
                    except Exception:
                        pass  # If can't parse date, include it but flag as unverified

                score, matched = score_job(title, desc)
                track, level_ok, level_signal = get_job_track(title, desc)

                # Lower score threshold for Amazon — worth seeing even at lower scores
                if score >= 15 and level_ok and is_relevant_title(title) and not is_blocked_company(title, desc, company):
                    jobs.append({
                        "source":           "Amazon Jobs",
                        "title":            title,
                        "company":          "Amazon",
                        "url":              url_job,
                        "posted":           posted,
                        "age_verified":     age_verified,
                        "description":      desc[:500],
                        "score":            score,
                        "matched_keywords": matched,
                        "track":            track,
                        "level_ok":         level_ok,
                        "level_signal":     level_signal,
                        "salary":           item.get("salary", ""),
                    })
        except Exception as e:
            print(f"   [ERROR] Amazon Jobs search error ({query}): {e}")
            log_error(f"Amazon Jobs error ({query}): {e}")
        time.sleep(1.2)

    # Deduplicate and sort — also check against seen_jobs.json to avoid repeat sends
    seen_urls = set()
    previously_seen = load_seen_jobs()  # Load persistent seen jobs
    deduped = []
    skipped_dupes = 0
    for job in sorted(jobs, key=lambda x: x["score"], reverse=True):
        if job["url"] not in seen_urls and job["url"] not in previously_seen:
            seen_urls.add(job["url"])
            deduped.append(job)
        else:
            skipped_dupes += 1
    if skipped_dupes > 0:
        print(f"   [OK] Skipped {skipped_dupes} Amazon jobs already seen previously")

    top5 = deduped[:5]
    # Save Amazon job URLs to seen_jobs so they won't repeat tomorrow
    if top5:
        updated_seen = previously_seen | {job["url"] for job in top5}
        save_seen_jobs(updated_seen)
    print(f"   [OK] Amazon Jobs: {len(top5)} relevant jobs found (10-day window)")
    return top5


#
# SOURCE 3: Adzuna
#
def search_adzuna():
    print("[SEARCH] Searching Adzuna...")
    jobs = []
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("   [WARN] Adzuna skipped — ADZUNA_APP_ID/KEY not set in environment")
        return jobs

    # Narrowed to LoadRunner/LRE/VuGen-specific queries only (2026-05-20).
    queries = [
        "loadrunner performance engineer",
        "loadrunner",
        "vugen",
        "loadrunner enterprise",
        "performance center loadrunner",
    ]

    # Require LoadRunner/LRE/VuGen signal in description to pass
    LR_SIGNALS = [
        "loadrunner", "load runner", "vugen", "vu gen",
        "lre", "loadrunner enterprise", "performance center",
        "lr scripting", "vuser", "v-user",
    ]

    seen = set()
    for query in queries:
        try:
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 20,
                "what": query,
                "full_time": 1,
                "sort_by": "date",
                "content-type": "application/json",
            }
            url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            items = data.get("results", [])
            if DEBUG_MODE:
                print(f"   [DEBUG] Adzuna '{query}': {len(items)} raw results, status {resp.status_code}")
                if resp.status_code != 200:
                    print(f"   [DEBUG] Adzuna error: {resp.text[:200]}")
            for item in items:
                title   = item.get("title", "")
                desc    = item.get("description", "")
                url_job = item.get("redirect_url", "")
                posted  = item.get("created", "")
                company = item.get("company", {}).get("display_name", "N/A")
                combined = (title + " " + desc).lower()

                if url_job in seen:
                    continue
                seen.add(url_job)

                adzuna_remote_signals = ["remote", "work from home", "wfh",
                                         "telecommute", "anywhere",
                                         "distributed", "virtual",
                                         "home-based", "home based"]
                if not any(sig in combined for sig in adzuna_remote_signals):
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Adzuna FILTERED-not-remote: {title[:50]}")
                    continue

                # Adzuna-specific: For Performance Engineering track, prefer
                # LR signal, but allow senior perf roles with observability
                # stack to pass through.
                track_quick, _, _ = get_job_track(title, desc)
                if track_quick == "Performance Engineering":
                    has_lr = any(sig in combined for sig in LR_SIGNALS)
                    perf_stack_signals = ["appdynamics", "dynatrace", "splunk",
                                          "grafana", "prometheus",
                                          "new relic", "datadog",
                                          "observability"]
                    has_stack = any(sig in combined for sig in perf_stack_signals)
                    is_senior_perf = any(s in title.lower() for s in
                                         ["senior", "sr ", "sr.", "staff",
                                          "lead", "principal"])
                    if not has_lr and not (is_senior_perf and has_stack):
                        if DEBUG_MODE:
                            print(f"   [DEBUG] Adzuna FILTERED-no-LR-no-stack: {title[:50]}")
                        continue

                # Debug breadcrumb for stale jobs
                if DEBUG_MODE and not is_recent(posted):
                    print(f"   [DEBUG] Adzuna FILTERED-stale: {title[:50]} [{posted[:10]}]")

                # Count as raw and run full pipeline
                funnel.add_raw("Adzuna")
                passed, score, matched, track, level_signal = passes_filters(
                    title, desc, posted, "", url_job, company, "Adzuna"
                )
                if passed:
                    jobs.append({
                        "source": "Adzuna",
                        "title": title,
                        "company": company,
                        "url": url_job,
                        "posted": posted,
                        "description": desc[:500],
                        "score": score,
                        "matched_keywords": matched,
                        "track": track,
                        "level_signal": level_signal,
                        "salary": "",
                    })
        except Exception as e:
            print(f"   [ERROR] Adzuna error ({query}): {e}")
            log_error(f"Adzuna error ({query}): {e}")
        time.sleep(1)
    print(f"   [OK] Adzuna: {len(jobs)} relevant jobs found")
    return jobs


#
# SOURCE 5: USAJobs API
#
def search_usajobs():
    print("[SEARCH] Searching USAJobs...")
    jobs = []
    if not USAJOBS_API_KEY or not USAJOBS_EMAIL:
        print("   [WARN] USAJobs skipped — USAJOBS_API_KEY/EMAIL not set in environment")
        return jobs
    queries = [
        "performance engineer", "loadrunner", "performance tester",
        "cobol", "mainframe developer", "software test engineer",
        "load testing"
    ]
    for query in queries:
        url = "https://data.usajobs.gov/api/search"
        headers = {
            "Authorization-Key": USAJOBS_API_KEY,
            "User-Agent": USAJOBS_EMAIL,
            "Host": "data.usajobs.gov",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        params = {
            "Keyword": query,
            "RemoteIndicator": "True",
            "ResultsPerPage": 25,
            "SortField": "OpenDate",
            "SortDirection": "Desc"
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            data = resp.json()
            items = data.get("SearchResult", {}).get("SearchResultItems", [])
            if DEBUG_MODE:
                print(f"   [DEBUG] USAJobs '{query}': {len(items)} raw results, status {resp.status_code}")
                if resp.status_code != 200:
                    print(f"   [DEBUG] USAJobs error response: {resp.text[:200]}")
            for item in items:
                mv = item.get("MatchedObjectDescriptor", {})
                title = mv.get("PositionTitle", "")
                desc  = mv.get("QualificationSummary", "") + " " + mv.get("UserArea", {}).get("Details", {}).get("JobSummary", "")
                posted = mv.get("PublicationStartDate", "")
                url_job = mv.get("PositionURI", "")
                company = mv.get("OrganizationName", "Federal Agency")
                # FIXED: pull location from USAJobs response (was empty string)
                location = mv.get("PositionLocationDisplay", "") or ""

                funnel.add_raw("USAJobs")
                passed, score, matched, track, level_signal = passes_filters(
                    title, desc, posted, location, url_job, company, "USAJobs"
                )
                if passed:
                    jobs.append({
                        "source": "USAJobs",
                        "title": title,
                        "company": company,
                        "url": url_job,
                        "posted": posted,
                        "description": desc[:500],
                        "score": score,
                        "matched_keywords": matched,
                        "track": track,
                        "level_signal": level_signal,
                        "salary": mv.get("PositionRemuneration", [{}])[0].get("MinimumRange", "")
                              + " - " + mv.get("PositionRemuneration", [{}])[0].get("MaximumRange", ""),
                    })
        except Exception as e:
            print(f"   [ERROR] USAJobs error ({query}): {e}")
            log_error(f"USAJobs error ({query}): {e}")
    seen = set()
    unique = []
    for j in jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
    print(f"   [OK] USAJobs: {len(unique)} relevant jobs found")
    return unique


#
# SOURCE 14c: Wellfound (startup jobs, direct links)
#
def search_wellfound():
    print("[SEARCH] Searching Wellfound...")
    jobs = []
    if not SERPER_API_KEY:
        print("   [WARN] Wellfound skipped - SERPER_API_KEY needed")
        return jobs
    queries = [
        "site:wellfound.com loadrunner performance engineer remote",
        "site:wellfound.com performance test engineer remote",
        "site:wellfound.com ai engineer entry level remote",
        "site:wellfound.com mlops engineer remote",
    ]
    seen = set()
    for query in queries:
        try:
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
            payload = {"q": query, "gl": "us", "hl": "en", "num": 10}
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            data = resp.json()
            for item in data.get("organic", []):
                title   = item.get("title", "").replace(" | Wellfound", "").replace(" - Wellfound", "").strip()
                desc    = item.get("snippet", "")
                url_job = item.get("link", "")
                posted  = item.get("date", "")
                if not any(x in url_job for x in ["wellfound.com/jobs/", "angel.co/jobs/"]):
                    continue
                if url_job in seen:
                    continue
                seen.add(url_job)

                funnel.add_raw("Wellfound")
                passed, score, matched, track, level_signal = passes_filters(
                    title, desc, posted, "", url_job, "", "Wellfound"
                )
                if passed:
                    jobs.append({
                        "source": "Wellfound",
                        "title": title,
                        "company": "N/A",
                        "url": url_job,
                        "posted": posted,
                        "description": desc[:500],
                        "score": score,
                        "matched_keywords": matched,
                        "track": track,
                        "level_signal": level_signal,
                    })
        except Exception as e:
            print(f"   [ERROR] Wellfound error ({query}): {e}")
            log_error(f"Wellfound error ({query}): {e}")
    print(f"   [OK] Wellfound: {len(jobs)} relevant jobs found")
    return jobs


#
# COVER LETTER GENERATOR
#
RESUME_FULL = """
Name: Hans Richardson
Title: Senior Performance Engineer | AI Automation & Prompt Engineering
Location: Lee's Summit, MO (Kansas City Metro — Remote or KC-area)
LinkedIn: linkedin.com/in/hans-richardson
Email: harichardson68@gmail.com
Clearance: Active Public Trust (USDA contract)

TOTAL EXPERIENCE: 24+ years IT, 14 years LoadRunner/VuGen/LRE specialist;
actively building AI engineering skills through hands-on Python/Claude API
work and IBM's Generative AI Engineering certification.

POSITIONING:
Performance/QA engineer bridging into AI Systems and Agent Engineering.
Differentiator: I bring 24+ years of reliability, evaluation, and
observability discipline to AI systems — the exact capabilities most
AI engineers lack. Performance testing AI APIs and model inference
endpoints is the same engineering as load testing web services;
monitoring model latency, throughput, and SLA compliance is the same
work I've done for two decades on production systems. Dual-track search:
(1) LoadRunner/Performance Engineering, (2) AI Systems / Agent / Workflow
Engineering / AI Reliability / LLM Evaluation.

EXPERIENCE:
- Sr. Performance/QA Test Engineer (Contract), USDA, Jan 2021 - Sep 2025
  * 14 years LoadRunner/VuGen/LRE expert
  * Led AWS/Kubernetes migration performance testing
  * Integrated AppDynamics, Splunk, Prometheus, Grafana for full-stack observability
  * Increased system throughput 40%, reduced defect resolution time 35%
  * Authored federal-grade documentation (Green Doc / RSO artifacts);
    audit-ready traceability and compliance reporting
  * Developed test plans and managed defects in Jira/Confluence (Agile/Scrum)
  * SLA compliance: <5s transactions, <2s services

- Programmer/Software Engineer, Sprint/Embarq/CenturyLink, 1999-2017
  * LoadRunner performance specialist for 9 years
  * Scaled telecom-grade systems to 12,000+ transactions per minute
  * SAP CRM, ERP, BRIM performance testing
  * Agile/Scrum ceremonies and sprint planning

- Early Career: COBOL/CICS Programmer, Yellow Freight
  * Mainframe development on enterprise-scale logistics systems
  * Foundation of structured, modular engineering discipline carried
    forward into every system since

AI ENGINEERING PROJECTS (hands-on):
- Multi-source automated job-search pipeline in Python integrating the
  Anthropic Claude API for per-job fit analysis and tailored cover-letter
  generation. Production deployment via Windows Task Scheduler with Gmail
  digest delivery, structured decision logging, and continuous-improvement
  feedback loop. Demonstrates prompt engineering, API integration,
  evaluation framework design, and observability instrumentation.
- RAG (Retrieval-Augmented Generation) layer over decision history using
  ChromaDB and sentence-transformers (all-MiniLM-L6-v2 embeddings) —
  semantic search infrastructure ready for similarity-based decision support.
- FLAPBOARD: Flask web application (Solari split-flap UI) with SQLAlchemy
  persistence, Flask-Login authentication, and CSRF protection — deployed
  on Render.

SKILLS:
- Performance: LoadRunner/VuGen/LRE (14 yrs expert), JMeter, NeoLoad,
  workload modeling, SLA compliance, capacity planning
- Observability/Monitoring: AppDynamics, Splunk, Grafana, Prometheus,
  AWS X-Ray — directly applicable to AI/ML observability and LLM monitoring
- AI/GenAI: Anthropic Claude API, prompt engineering, RAG architectures,
  semantic search, vector databases (ChromaDB), sentence-transformers,
  embeddings, LLM evaluation frameworks, model evaluation, AI observability,
  agent/agentic concepts, tool-use prompting, few-shot/chain-of-thought
- Cloud/DevOps: AWS, Kubernetes, CI/CD, Git, GitHub Actions
- QA: Test automation, regression testing, integration testing, API testing,
  defect tracking, federal documentation standards
- Programming: Python (production — built multi-API pipeline with Claude
  integration, RAG, structured logging), SQL, JavaScript, COBOL
- Methodologies: Agile/Scrum, Waterfall, federal contract delivery

EDUCATION:
- BS Computer Information Science, Park University, 1996
- BA Marketing, Park University, 1992

CERTIFICATIONS:
- HP LoadRunner Training (HP, 2010)
- JMeter Performance Testing (Coursera, 2025)
- AWS Cloud Practitioner (Udemy, 2025)
- AI Engineer Bootcamp (Udemy, 2025)
- IBM Generative AI Engineering Professional Certificate (Coursera, 2025-2026)
"""

def build_optimized_prompt(job):
    """Prompt engineering agent - builds the best possible prompt for this specific job."""
    title    = job.get("title", "")
    company  = job.get("company", "")
    desc     = job.get("description", "")
    keywords = ", ".join(job.get("matched_keywords", []))
    track    = job.get("track", "Performance Engineering")

    # Extract key requirements from job description
    desc_lower = desc.lower()

    requirements = []
    if "loadrunner" in desc_lower or "vugen" in desc_lower:
        requirements.append("LoadRunner/VuGen expertise is explicitly required")
    if "aws" in desc_lower or "kubernetes" in desc_lower:
        requirements.append("Cloud/AWS/Kubernetes experience is mentioned")
    if "agile" in desc_lower or "scrum" in desc_lower:
        requirements.append("Agile/Scrum methodology is required")
    if "splunk" in desc_lower or "appdynamics" in desc_lower:
        requirements.append("Monitoring/observability tools experience is needed")
    if "federal" in desc_lower or "government" in desc_lower or "clearance" in desc_lower:
        requirements.append("Federal/government experience is a plus")
    if "sla" in desc_lower:
        requirements.append("SLA compliance experience is required")
    if "selenium" in desc_lower:
        requirements.append("Selenium automation experience is needed")
    if "python" in desc_lower:
        requirements.append("Python skills are mentioned")
    if "entry" in desc_lower or "junior" in desc_lower:
        requirements.append("This is an entry/junior level position")

    req_str = "\n".join(f"- {r}" for r in requirements) if requirements else "- General technical role"

    prompt = f"""You are an expert career coach and cover letter writer specializing in tech/engineering roles.

Write a highly tailored, professional cover letter for Hans Richardson applying to this specific job.

JOB DETAILS:
- Title: {title}
- Company: {company}
- Track: {track}
- Matched Keywords: {keywords}
- Job Description: {desc}

KEY REQUIREMENTS DETECTED IN THIS JOB POSTING:
{req_str}

HANS'S BACKGROUND:
{RESUME_FULL}

COVER LETTER INSTRUCTIONS:
1. Opening paragraph: Reference the specific role and company by name. Lead with Hans's strongest matching qualification for THIS specific job.
2. Middle paragraph: Pull 2-3 specific achievements from his resume that directly match the job requirements detected above. Use real numbers (40% throughput increase, 35% defect reduction, 12,000 TPS, etc.)
3. Closing paragraph: Express enthusiasm for remote work, availability, and call to action.
4. Tone: Confident, specific, not generic. Sound like a human wrote it for this exact job.
5. Length: 150-200 words maximum.
6. Do NOT start with "I am writing to express my interest"
7. Do NOT use phrases like "I would be a great fit" or "passionate about"
8. Mirror the language and keywords used in the job posting where natural.
9. If it's a federal/government role, mention USDA experience prominently.
10. If it's entry-level AI or junior SDET, acknowledge the career transition positively.
11. If it's an MLOps, AI Test Engineer, or LLM Engineer role, emphasize how Hans's performance testing background is a DIRECT advantage:
    - Performance testing AI APIs and model inference endpoints = same as load testing web services
    - Monitoring model latency, throughput, and SLA compliance = exact same skills from LoadRunner
    - His observability stack (AppDynamics, Splunk, Grafana, Prometheus) directly applies to ML monitoring
    - Frame it as: "I bring proven performance engineering expertise that most AI engineers lack"
12. If it's a Performance Engineering role, lead with LoadRunner expertise and specific metrics.
13. If it's an AI Performance Engineering role, emphasize both LoadRunner expertise AND AI engineering skills together.
14. If it's a COBOL/Mainframe role, lead with Hans's early career COBOL/CICS programming experience.
    Emphasize: Started career as COBOL/CICS programmer, understands enterprise mainframe systems,
    brings rare combination of mainframe programming AND modern IT/performance testing expertise,
    24+ years of IT experience makes him immediately productive with minimal ramp-up time.

Write only the cover letter text, no subject line or extra commentary."""

    return prompt


def _call_claude_api(prompt, max_tokens=1000, model="claude-sonnet-4-6"):
    """Shared Claude API call helper. Returns text on success, None on failure.
    model defaults to Sonnet (cover letters); pass FIT_ANALYSIS_MODEL for
    cheaper classification-style calls like fit analysis."""
    if not CLAUDE_API_KEY:
        return None
    try:
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"].strip()
        else:
            print(f"   [WARN] Claude API error {resp.status_code}: {resp.text[:200]}")
            log_error(f"Claude API error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"   [WARN] Claude API failed: {e}")
        log_error(f"Claude API failed: {e}")
        return None


def generate_cover_letter_claude(job):
    """Generate tailored cover letter using Claude API with optimized prompt."""
    prompt = build_optimized_prompt(job)
    result = _call_claude_api(prompt, max_tokens=1000)
    if result:
        return result
    print(f"   [WARN] Claude cover letter failed, using template")
    return generate_cover_letter_template(job)


def generate_cover_letter_template(job):
    """Fallback template-based cover letter — Performance/career-track flavor.
    Used when Claude API fails for Performance/AI Engineering jobs."""
    skills_str = ", ".join(job["matched_keywords"][:5]) if job["matched_keywords"] else "LoadRunner, JMeter, NeoLoad"
    return f"""Dear Hiring Manager,

With 24+ years of IT experience and 14 years of hands-on LoadRunner/performance testing expertise in {skills_str}, I am confident I would be a strong fit for the {job["title"]} role at {job["company"]}.

In my recent role as Sr. Performance Test Engineer at the USDA, I led performance testing for AWS/Kubernetes migrations, integrating AppDynamics, Splunk, and Prometheus to ensure SLA compliance. I increased throughput by 40% and reduced defect resolution time by 35%. Earlier in my career at Sprint/CenturyLink, I spent 9 years as a LoadRunner specialist, scaling systems to 12,000+ transactions per minute.

I am available immediately for remote work and would welcome the opportunity to discuss how my background aligns with your team's needs.

Best regards,
Hans Richardson
Lee's Summit, MO | linkedin.com/in/hans-richardson
"""


def generate_cover_letter_qa_template(job):
    """
    Free, no-API-call template for income-track QA/testing jobs (Track 4:
    Remote Income Floor, plus QA Automation). These jobs get volume over
    precision — a solid generic pitch beats spending Sonnet tokens on
    career-direction-quality tailoring for a relief-track role.
    """
    skills_str = ", ".join(job["matched_keywords"][:5]) if job.get("matched_keywords") else "manual testing, test case design, defect tracking"
    return f"""Dear Hiring Manager,

I'm writing to apply for the {job["title"]} role at {job["company"]}. With over 24 years of IT experience spanning software testing, quality assurance, and production support, I bring a steady, detail-oriented approach to {skills_str} that translates directly to this role.

Throughout my career — including as a Senior Performance Test Engineer and earlier hands-on QA and development work — I've built test plans, tracked defects, and worked closely with development teams to ensure releases meet quality standards before they reach production. I'm comfortable picking up new tools quickly and have a strong track record of reliability and follow-through.

I'm available immediately for remote work and would welcome the opportunity to bring that same reliability to your team.

Best regards,
Hans Richardson
Lee's Summit, MO | linkedin.com/in/hans-richardson
"""


def generate_cover_letter_cobol_template(job):
    """
    Free, no-API-call template for income-track COBOL/mainframe jobs
    (folded into Track 4: Remote Income Floor). Leads with early-career
    COBOL/CICS experience — the actual differentiator for these roles.
    """
    skills_str = ", ".join(job["matched_keywords"][:5]) if job.get("matched_keywords") else "COBOL, CICS, mainframe systems"
    return f"""Dear Hiring Manager,

I'm writing to apply for the {job["title"]} role at {job["company"]}. I began my IT career as a COBOL/CICS programmer on enterprise mainframe systems, and that early foundation in {skills_str} has stayed with me through 24+ years in IT.

While much of my recent work has been in performance testing and modern systems, I understand mainframe environments and enterprise batch/transaction processing at a level that most newer developers simply haven't been exposed to. That combination — solid COBOL/CICS fundamentals plus decades of broader production IT experience — means I can step in productively with minimal ramp-up time.

I'm available immediately for remote work (or hybrid/onsite in the Kansas City metro area, depending on the role) and would welcome the chance to discuss how my background fits your team's needs.

Best regards,
Hans Richardson
Lee's Summit, MO | linkedin.com/in/hans-richardson
"""


def generate_cover_letter(job):
    """
    Generate cover letter. Routing:
      - Income tracks (QA Automation, Remote Income Floor) ALWAYS use a
        free template — never call the API for these, regardless of
        GENERATE_COVER_LETTERS. Volume-over-precision track; Sonnet tokens
        are better spent on career-direction roles. COBOL jobs (folded
        into Remote Income Floor) get their own COBOL-flavored template
        rather than the generic QA one, since the pitch is different.
      - Career tracks (Performance Engineering, AI Engineering) use Claude
        (Sonnet) if available, falling back to the Performance-flavored
        template if the API call fails or GENERATE_COVER_LETTERS is off.
    """
    track = job.get("track", "")
    if track in {"QA Automation", "Gap Track"}:
        is_cobol = any(
            kw in (job.get("title", "") + " " + job.get("description", "")).lower()
            for kw in COBOL_HIGH_KEYWORDS
        )
        if is_cobol:
            return generate_cover_letter_cobol_template(job)
        return generate_cover_letter_qa_template(job)
    # FIXED: removed broken `if OPENAI_API_KEY: return generate_cover_letter_claude()`
    # OpenAI key is not currently wired up; only Claude or template.
    if CLAUDE_API_KEY:
        return generate_cover_letter_claude(job)
    return generate_cover_letter_template(job)


#
# FIT ANALYSIS (Claude-powered per-job "why this fits" blurb)
#
FIT_TIER_RANK = {
    "Excellent Fit": 4,
    "Strong Fit": 3,
    "Decent Fit": 2,
    "Stretch Fit": 1,
    "Weak Fit": 0,
}

def generate_fit_analysis(job):
    """
    Classify a job's real fit for Hans using Claude (Haiku — cheap/fast,
    this is a 5-bucket classification task, not creative writing, and
    runs behind the scenes so latency doesn't matter).

    Returns a dict:
        {
          "tier": "Excellent Fit"|"Strong Fit"|"Decent Fit"|"Stretch Fit"|"Weak Fit"|"",
          "display": "<one-line markdown blurb for the email>",
          "hard_disqualified": bool,
        }
    Returns tier="" / display="" on failure or if disabled, so callers can
    treat that as "unknown — don't gate on it."

    Hard disqualification (PhD/publication/research-scientist/train-models-
    from-scratch asks) is checked against the raw description text directly,
    not just the LLM's own "Weak Fit" call — belt and suspenders, since a
    real disqualifier should never end up shown, even if the model is
    lenient. A job that hits HARD_DISQUALIFY_TERMS is dropped silently;
    Stretch Fit (credential/title mismatch but real overlap) is demoted and
    shown with the reason; everything else (Excellent/Strong/Decent) is
    shown normally.

    Logs skip/fallback/error reasons to job_search_run.log so missing
    recommendations in the digest can be diagnosed after the fact.
    """
    job_id = job.get("id") or job.get("url", "unknown")
    title  = job.get("title", "")
    source = job.get("source", "unknown")
    empty_result = {"tier": "", "display": "", "hard_disqualified": False}

    if not GENERATE_FIT_ANALYSIS:
        logging.info(f"[FIT-SKIP] id={job_id} title={title!r} reason=feature_disabled")
        return empty_result
    if not CLAUDE_API_KEY:
        logging.info(f"[FIT-SKIP] id={job_id} title={title!r} reason=no_api_key")
        return empty_result

    company  = job.get("company", "")
    desc     = job.get("description", "")[:600]
    keywords = ", ".join(job.get("matched_keywords", []))
    track    = job.get("track", "")
    score    = job.get("score", 0)

    # Belt-and-suspenders hard disqualifier check directly on description text
    # (case-insensitive), independent of what the LLM decides — a real
    # disqualifier should never slip through to "shown" just because the
    # model was lenient on a given call.
    full_text_lower = (title + " " + job.get("description", "")).lower()
    hard_disqualified = any(term in full_text_lower for term in HARD_DISQUALIFY_TERMS)

    # Soft fallback for missing company (don't skip — internships and Serper
    # organic results often have N/A company; let Claude infer from title/desc)
    if not company or company.strip().upper() in ("N/A", "NONE", ""):
        logging.info(
            f"[FIT-FALLBACK] id={job_id} title={title!r} source={source} "
            f"reason=missing_company"
        )
        company = "(not parsed — infer from title/description)"

    is_income_track = track in {"QA Automation", "Gap Track"}

    if is_income_track:
        prompt = f"""You are evaluating a job match for Hans Richardson — but for a DIFFERENT
purpose than his career-direction search. This is his "Gap Track"
track: the goal is NOT career advancement, it's getting him out of in-person
warehouse work onto something remote that pays at least $30/hr. Breadth and
realism matter more than career fit here.

CANDIDATE SNAPSHOT:
- 24+ years IT experience, including QA/testing-adjacent work throughout his career
- Technically capable, comfortable learning new tools quickly
- Based in Lee's Summit, MO — remote-only for this track (commute is the whole
  point of avoiding); COBOL/mainframe roles are the one exception where
  KC-metro hybrid/onsite is acceptable if pay is $55+/hr
- Goal: remote, $30+/hr floor, realistic for him to get hired and ramp quickly
  — NOT "is this the ideal next career step"

JOB POSTING:
Title: {title}
Company: {company}
Track: {track} (matched at {score} pts)
Matched keywords: {keywords}
Description: {desc}

TASK:
Classify into ONE of five tiers and return a single short line. Judge on
"can Hans realistically get and do this job" — NOT on career advancement,
prestige, or long-term direction.

TIERS:
- Excellent Fit: Clear match — Hans's background or transferable skills line up directly, remote (or COBOL hybrid/onsite at $55+/hr), no real barrier to getting hired.
- Strong Fit: Good match with one minor gap (e.g. a specific tool he hasn't used, but the role type is squarely accessible).
- Decent Fit: Realistic to apply and get traction — adjacent skills, "will train" language, or generalist QA/testing work he could ramp into quickly.
- Stretch Fit: Possible but a real reach — meaningfully more specialized/senior than this track is meant for, though not disqualifying.
- Weak Fit: Hard disqualifier — requires years of specific tool/certification experience Hans doesn't have and wouldn't be considered for, or the role is clearly senior/specialized beyond this track's accessible-entry-point purpose. (Pay floor and remote requirements are already enforced before this job reached you — don't re-judge those.) Return "Weak Fit" only — no explanation.

OUTPUT FORMAT (exactly one line, no preamble):
**<Tier>** — <15-25 word sentence>. Bold 1-2 positive keywords with *asterisks* and 1-2 friction keywords with _underscores_.

EXAMPLES:
**Excellent Fit** — *Remote* manual QA role, *will train* on their tools; straightforward to land and start.
**Strong Fit** — *Selenium* automation testing remote role; minor gap in _Cypress_ but transferable skill.
**Decent Fit** — Generalist *QA Analyst* role, broad responsibilities; realistic ramp-up with his testing background.
**Stretch Fit** — Role wants 3+ years _dedicated automation framework_ ownership; possible but a real reach for this track.
**Weak Fit**

Return ONLY the one line. No headers, no bullets, no follow-up text."""
    else:
        prompt = f"""You are evaluating a job match for Hans Richardson.

CANDIDATE SNAPSHOT:
- 24+ years IT, 14 years LoadRunner/VuGen/LRE (Senior Performance Engineer)
- Active Public Trust clearance (USDA contract)
- Based in Lee's Summit, MO — seeking remote or KC-area
- Building AI engineering skills: IBM GenAI cert, Claude API projects, agentic loop in progress
- Observability stack: AppDynamics, Splunk, Grafana, Prometheus
- Dual-track search: (1) LoadRunner/Performance roles, (2) AI Systems/Agent/Workflow Engineering

JOB POSTING:
Title: {title}
Company: {company}
Track: {track} (matched at {score} pts)
Matched keywords: {keywords}
Description: {desc}

TASK:
Classify into ONE of five tiers and return a single short line.

TIERS:
- Excellent Fit: Bullseye — core skills match, remote-US or KC-area, right seniority, no major friction.
- Strong Fit: Clear match on core skills with minor friction (one small gap, slight seniority mismatch).
- Decent Fit: Partial match — adjacent skills or moderate friction, but realistic to apply.
- Stretch Fit: Reach role — title/credential pattern mismatch but real day-to-day overlap with Hans's actual strengths (e.g. observability, reliability, performance-testing-adjacent work). Still realistic enough that Hans might choose to apply.
- Weak Fit: Hard disqualifier present — PhD/publication required, must have trained/built production ML models from scratch, dedicated ML research role, or other major mismatch (wrong geography, wrong stack). Return "Weak Fit" only — no explanation.

OUTPUT FORMAT (exactly one line, no preamble):
**<Tier>** — <15-25 word sentence>. Bold 1-2 positive keywords with *asterisks* and 1-2 friction keywords with _underscores_.

EXAMPLES:
**Excellent Fit** — Remote US *Senior LoadRunner* role with *observability* depth needed; clean match on stack and seniority.
**Strong Fit** — *Performance engineering* + *AI reliability* framing fits well; minor _hands-on ML_ gap but bridgeable.
**Decent Fit** — *QA/SDET* angle works, but title leans _ML pipeline_; apply if JD mentions eval or monitoring.
**Stretch Fit** — *Agent engineering* target aligns with portfolio direction, but _production LLM_ experience still in progress.
**Weak Fit**

Return ONLY the one line. No headers, no bullets, no follow-up text."""

    try:
        result = _call_claude_api(prompt, max_tokens=80, model=FIT_ANALYSIS_MODEL)
    except Exception as e:
        print(f"   [WARN] Fit analysis exception for {title!r} ({source}): {type(e).__name__}: {e}")
        logging.exception(
            f"[FIT-ERROR] id={job_id} title={title!r} source={source} "
            f"error={type(e).__name__}: {e}"
        )
        return {"tier": "", "display": "", "hard_disqualified": hard_disqualified}

    if not result or not result.strip():
        print(f"   [WARN] Fit analysis returned empty for: {title!r} ({source}) — raw response: {result!r}")
        logging.info(f"[FIT-SKIP] id={job_id} title={title!r} reason=empty_response")
        return {"tier": "", "display": "", "hard_disqualified": hard_disqualified}

    # Parse tier out of the leading **<Tier>** marker
    tier = ""
    m = re.match(r"\*\*(Excellent Fit|Strong Fit|Decent Fit|Stretch Fit|Weak Fit)\*\*", result.strip())
    if m:
        tier = m.group(1)
    else:
        print(f"   [WARN] Fit analysis tier unparsed for {title!r} — raw response: {result[:100]!r}")
        logging.info(f"[FIT-WARN] id={job_id} title={title!r} unparsed tier from: {result[:60]!r}")

    if tier == "Weak Fit":
        hard_disqualified = True

    logging.info(f"[FIT-OK] id={job_id} title={title!r} source={source} score={score} tier={tier or 'unparsed'}")
    return {"tier": tier, "display": result, "hard_disqualified": hard_disqualified}


#
# MAIN
#
def main():
    print("\n" + "="*55)
    print("  Hans Richardson  Automated Job Search")
    print("  Target: LoadRunner / Performance Engineer (Remote)")
    print("="*55 + "\n")

    all_jobs = []
    all_jobs += search_remoteok()
    all_jobs += search_remotive()
    all_jobs += search_working_nomads()
    all_jobs += search_serper_jobs()
    all_jobs += search_adzuna()
    all_jobs += search_usajobs()
    all_jobs += search_wellfound()

    # Sort by score descending
    all_jobs.sort(key=lambda x: x["score"], reverse=True)
    funnel.set_stage("kept_by_sources", len(all_jobs))

    # Apply minimum score thresholds per track
    MIN_SCORES = {
        "Performance Engineering": 30,  # Lower threshold - core specialty
        "AI Engineering": 40,           # Lowered from 51 - catching real jobs
        "QA Automation": 30,            # SDET / QA hybrid
        "COBOL/Mainframe": 10,          # Last resort - low threshold
        "Gap Track": 20,      # Modest bar — relief track, breadth over precision
    }
    filtered_by_score = []
    for job in all_jobs:
        track = job.get("track", "Performance Engineering")
        min_score = MIN_SCORES.get(track, 30)
        if job["score"] >= min_score:
            filtered_by_score.append(job)
        elif DEBUG_MODE:
            print(f"   [DEBUG] FILTERED-minscore ({track} needs {min_score}pts): {job['title'][:50]} [{job['score']}pts]")
    removed = len(all_jobs) - len(filtered_by_score)
    if removed > 0:
        print(f"[OK] Removed {removed} jobs below minimum score thresholds")
    all_jobs = filtered_by_score
    funnel.set_stage("after_minscore", len(all_jobs))

    # ── COBOL hybrid pay-tier filter (within Track 4) ───────────
    # Hans's explicit rule, COBOL only: KC-metro hybrid/onsite is
    # acceptable IF pay parses to $55+/hr. Below that (but still $30+/hr),
    # the job must be fully remote — same standard as the rest of Track 4.
    # Below $30/hr entirely, dropped by the general pay-floor filter below
    # regardless of hybrid/remote. Non-COBOL Remote Floor jobs are
    # untouched here — they already got hard-rejected for being
    # hybrid/onsite back in passes_filters().
    COBOL_HYBRID_MIN_HOURLY = 55.0
    cobol_hybrid_filtered = []
    cobol_hybrid_dropped = 0
    for job in all_jobs:
        if job.get("track") != "Gap Track":
            cobol_hybrid_filtered.append(job)
            continue
        is_cobol = any(kw in (job.get("title","") + " " + job.get("description","")).lower()
                        for kw in COBOL_HIGH_KEYWORDS)
        if not is_cobol:
            cobol_hybrid_filtered.append(job)
            continue
        job_is_hybrid = is_onsite_or_hybrid(job.get("title",""), job.get("description",""), job.get("location",""))
        if not job_is_hybrid:
            # Fully remote COBOL job — no pay-tier hybrid question applies,
            # falls through to the standard $30/hr floor check below.
            cobol_hybrid_filtered.append(job)
            continue
        # Hybrid/onsite COBOL job — only acceptable at $55+/hr.
        hourly = _parse_pay_to_hourly(job.get("salary","")) or _parse_pay_to_hourly(job.get("description",""))
        if hourly is not None and hourly >= COBOL_HYBRID_MIN_HOURLY:
            cobol_hybrid_filtered.append(job)
        else:
            cobol_hybrid_dropped += 1
            if DEBUG_MODE:
                print(f"   [DEBUG] FILTERED-cobol-hybrid (hybrid/onsite needs \u2265${COBOL_HYBRID_MIN_HOURLY:.0f}/hr): {job['title'][:50]} | parsed: {hourly}")
    if cobol_hybrid_dropped > 0:
        print(f"[OK] Removed {cobol_hybrid_dropped} hybrid/onsite COBOL job(s) below ${COBOL_HYBRID_MIN_HOURLY:.0f}/hr threshold")
    all_jobs = cobol_hybrid_filtered
    funnel.set_stage("after_cobol_hybrid", len(all_jobs))

    # ── Pay floor filter (Track 4 only) ─────────────────────────
    # Strict per Hans's choice: drop if pay can't be parsed at all, or
    # parses below the floor. Runs here (post-aggregation) because this is
    # the first point where job["salary"] is actually populated from each
    # source's raw API response — passes_filters() runs before that field
    # exists. Real tradeoff: many legit remote QA postings list no pay at
    # all, so this will cut the pool down hard. If it's too thin after a
    # few runs, this is the one line to relax (drop the `else reject`).
    # 2026-06-26: Floor is now tiered per Hans's explicit instruction —
    # $25/hr for remote, $30/hr for KC-metro hybrid/onsite. COBOL keeps
    # its existing flat $30/hr floor here (unchanged); a hybrid COBOL job
    # reaching this point has already cleared the separate $55/hr hybrid
    # check above, so $30 is always satisfied trivially for it.
    COBOL_REMOTE_FLOOR_MIN_HOURLY = 30.0
    pay_filtered = []
    pay_dropped_count = 0
    for job in all_jobs:
        if job.get("track") == "Gap Track":
            is_cobol = any(kw in (job.get("title","") + " " + job.get("description","")).lower()
                            for kw in COBOL_HIGH_KEYWORDS)
            if is_cobol:
                floor = COBOL_REMOTE_FLOOR_MIN_HOURLY
            else:
                is_hybrid = is_onsite_or_hybrid(job.get("title",""), job.get("description",""), job.get("location",""))
                floor = GAP_HYBRID_MIN_HOURLY if is_hybrid else REMOTE_FLOOR_MIN_HOURLY
            if meets_pay_floor(job, min_hourly=floor):
                pay_filtered.append(job)
            else:
                pay_dropped_count += 1
                if DEBUG_MODE:
                    print(f"   [DEBUG] FILTERED-payfloor (no parseable \u2265${floor:.0f}/hr pay): {job['title'][:50]} | salary text: {job.get('salary','')[:40]!r}")
        else:
            pay_filtered.append(job)
    if pay_dropped_count > 0:
        print(f"[OK] Removed {pay_dropped_count} Remote Income Floor job(s) below their pay floor (${REMOTE_FLOOR_MIN_HOURLY:.0f}/hr remote, ${GAP_HYBRID_MIN_HOURLY:.0f}/hr KC-hybrid, ${COBOL_REMOTE_FLOOR_MIN_HOURLY:.0f}/hr COBOL) or with unparseable pay")
    all_jobs = pay_filtered
    funnel.set_stage("after_pay_floor", len(all_jobs))

    # Deduplicate within this run by title + company AND by title alone
    seen_title_company = set()
    seen_titles_only = set()
    deduped_jobs = []
    for job in all_jobs:
        title_norm = job.get("title", "").lower().strip()[:60]
        company_norm = job.get("company", "").lower().strip()[:40]
        key = (title_norm, company_norm)
        title_key = title_norm[:45]
        if key not in seen_title_company and title_key not in seen_titles_only and key != ("", ""):
            seen_title_company.add(key)
            seen_titles_only.add(title_key)
            deduped_jobs.append(job)
        elif DEBUG_MODE:
            print(f"   [DEBUG] Cross-source duplicate removed: {job.get('title','')[:50]} @ {job.get('company','')[:30]} ({job.get('source','')})")
    cross_dupes = len(all_jobs) - len(deduped_jobs)
    if cross_dupes > 0:
        print(f"[OK] Removed {cross_dupes} cross-source duplicate jobs (same job on multiple sites)")
    all_jobs = deduped_jobs
    funnel.set_stage("after_cross_dedup", len(all_jobs))

    # Remove jobs already seen in previous runs
    seen_urls = load_seen_jobs()
    new_jobs = [j for j in all_jobs if j.get("url", "") not in seen_urls]
    duplicate_count = len(all_jobs) - len(new_jobs)
    if duplicate_count > 0:
        print(f"[OK] Removed {duplicate_count} duplicate jobs already sent previously")
    all_jobs = new_jobs
    funnel.set_stage("after_seen_dedup", len(all_jobs))
    funnel.set_stage("final", len(all_jobs))

    print(f"\n{'='*55}")
    print(f"[STATS] Total relevant jobs found: {len(all_jobs)}")

    # ── FIT EVAL PASS (AI track only) — BEFORE the top-15 cut ──────────
    # Why before: the keyword score has no idea what "Weak Fit" or "hard
    # disqualifier" means. If we cut to top-15 by score first and THEN
    # eval, a real Stretch/Decent fit sitting at #18 by score never gets
    # seen, while a high-keyword-score Weak Fit occupies a slot it doesn't
    # deserve. So: eval every AI-track survivor, drop hard disqualifiers,
    # then re-sort with fit tier as the PRIMARY key (score as tiebreaker)
    # before slicing to the top 15. Non-AI tracks are untouched — their
    # keyword score IS a reliable fit signal already (e.g. LoadRunner match
    # = real fit), so we don't spend API calls there.
    if GENERATE_FIT_ANALYSIS and not CLAUDE_API_KEY:
        print("   [WARN] GENERATE_FIT_ANALYSIS is on but no Claude API key was found "
              "(checked CLAUDE_API_KEY and ANTHROPIC_API_KEY env vars) — every fit "
              "evaluation this run will silently return empty. Check .env.")

    fit_evaluated = 0
    fit_succeeded = 0
    hard_dropped = []
    for job in all_jobs:
        track = job.get("track", "")
        if GENERATE_FIT_ANALYSIS and track in FIT_ANALYSIS_TRACKS:
            fit_result = generate_fit_analysis(job)
            fit_evaluated += 1
            if fit_result["display"]:
                fit_succeeded += 1
        else:
            fit_result = {"tier": "", "display": "", "hard_disqualified": False}
        job["fit_tier"] = fit_result["tier"]
        job["fit_analysis"] = fit_result["display"]
        job["fit_hard_disqualified"] = fit_result["hard_disqualified"]

    if fit_evaluated:
        print(f"[OK] Ran fit evaluation on {fit_evaluated} AI-track job(s) "
              f"({fit_succeeded} succeeded, {fit_evaluated - fit_succeeded} empty/failed)")

    pre_drop_count = len(all_jobs)
    survivors = []
    for job in all_jobs:
        if job.get("fit_hard_disqualified"):
            hard_dropped.append(job)
        else:
            survivors.append(job)
    all_jobs = survivors
    if hard_dropped:
        print(f"[OK] Dropped {len(hard_dropped)} job(s) with hard fit disqualifiers (not shown — not realistic chances):")
        for j in hard_dropped[:10]:
            print(f"   [DROPPED] {j['title'][:60]} @ {j.get('company','')[:30]}")
    funnel.set_stage("after_fit_hard_disqualify", len(all_jobs))

    # Re-sort: fit tier primary (jobs with no fit tier, e.g. non-AI tracks,
    # default to rank 2 = "Decent" so they sit with their existing score
    # order rather than being pushed artificially high or low), score
    # secondary as tiebreaker within each tier.
    def _sort_key(job):
        tier = job.get("fit_tier", "")
        tier_rank = FIT_TIER_RANK.get(tier, 2)
        return (tier_rank, job.get("score", 0))
    all_jobs.sort(key=_sort_key, reverse=True)
    funnel.set_stage("final", len(all_jobs))

    top_jobs = all_jobs  # kept for backward-compat references below; real split happens next

    # ── DUAL POOL SPLIT ──────────────────────────────────────────
    # Two separate pools with separate caps and separate purposes:
    #   Pool A (Performance + AI) — career-direction tracks, 10 slots.
    #   Pool B (QA Automation + Remote Income Floor, incl. COBOL) —
    #     relief/income tracks, 15 slots. Broader bar, bigger cap, since
    #     volume matters more than precision here.
    # Each pool is sorted and capped independently — Remote Income Floor
    # jobs never compete against Performance/AI jobs for a slot, and
    # vice versa.
    CAREER_TRACKS = {"Performance Engineering", "AI Engineering"}
    INCOME_TRACKS = {"QA Automation", "Gap Track"}

    pool_career = [j for j in all_jobs if j.get("track") in CAREER_TRACKS]
    pool_income = [j for j in all_jobs if j.get("track") in INCOME_TRACKS]
    pool_other  = [j for j in all_jobs if j.get("track") not in CAREER_TRACKS and j.get("track") not in INCOME_TRACKS]
    if pool_other:
        # Shouldn't normally happen (every track should map to one of the
        # two pools above) — log it so an unmapped track doesn't silently
        # vanish from the digest.
        print(f"[WARN] {len(pool_other)} job(s) had an unmapped track and were added to the career pool by default:")
        for j in pool_other[:5]:
            print(f"   [UNMAPPED] track={j.get('track')!r} {j['title'][:50]}")
        pool_career += pool_other

    pool_career.sort(key=_sort_key, reverse=True)
    pool_income.sort(key=_sort_key, reverse=True)

    # ── Split normal vs. Stretch Fit BEFORE capping ──────────────
    # Each pool gets its OWN normal cap and its OWN stretch cap, so a
    # surplus of Stretch Fit jobs can never crowd out normal-tier jobs
    # (or vice versa) — they're independent buckets, not one pool that
    # Stretch Fit competes within. Symmetric across both pools per Hans's
    # spec: 10 normal + 5 Stretch Fit each.
    # 2026-06-26: Stretch caps zeroed per Hans — too much reach-role noise
    # right now. fit_tier classification still runs underneath, so set
    # these back to 5 later to restore the demoted Stretch Fit section
    # with no other code changes needed.
    CAREER_NORMAL_CAP  = 10
    CAREER_STRETCH_CAP = 0
    GAP_NORMAL_CAP      = 10
    GAP_STRETCH_CAP     = 0

    career_pool_normal  = [j for j in pool_career if j.get("fit_tier") != "Stretch Fit"]
    career_pool_stretch = [j for j in pool_career if j.get("fit_tier") == "Stretch Fit"]
    gap_pool_normal     = [j for j in pool_income if j.get("fit_tier") != "Stretch Fit"]
    gap_pool_stretch    = [j for j in pool_income if j.get("fit_tier") == "Stretch Fit"]

    career_normal  = career_pool_normal[:CAREER_NORMAL_CAP]
    career_stretch = career_pool_stretch[:CAREER_STRETCH_CAP]
    income_normal  = gap_pool_normal[:GAP_NORMAL_CAP]
    income_stretch = gap_pool_stretch[:GAP_STRETCH_CAP]

    # Log anything dropped purely for being over-cap, so a surplus day
    # doesn't silently vanish without a trace in the console/log.
    for label, pool, cap in [
        ("career normal", career_pool_normal, CAREER_NORMAL_CAP),
        ("career stretch", career_pool_stretch, CAREER_STRETCH_CAP),
        ("gap normal", gap_pool_normal, GAP_NORMAL_CAP),
        ("gap stretch", gap_pool_stretch, GAP_STRETCH_CAP),
    ]:
        if len(pool) > cap:
            print(f"[OK] {label}: {len(pool)} candidates exceeded cap of {cap} — top {cap} kept, {len(pool) - cap} dropped")

    career_jobs = career_normal + career_stretch
    income_jobs = income_normal + income_stretch
    top_jobs = career_jobs + income_jobs
    funnel.set_stage("final", len(top_jobs))

    # ── Display numbering (single source of truth) ──────────────
    # Computed ONCE here and stored on each job as job["display_number"],
    # then reused by BOTH the email renderer and the today_jobs.json
    # persistence step below. Previously these were computed independently
    # in two places (send_email's local enumerate() calls vs. today_jobs.json's
    # flat enumerate(top_jobs, 1)), which silently drifted out of sync once
    # the dual-pool numbering scheme was added — a decision submitted via
    # the form referencing a gap-track number had no match in
    # today_jobs.json at all, since that file was still numbering
    # everything 1..N flat. Computing the number once, here, and threading
    # it through everywhere else, closes that gap structurally instead of
    # needing the two call sites to be kept manually in sync.
    # Prefix scheme: career = "1".."10" / "S1".."S5"; gap/income track =
    # "G1".."G10" / "GS1".."GS5" (renamed from the earlier "R"/"RS" prefix
    # per Hans's request).
    for i, j in enumerate(career_normal, 1):
        j["display_number"] = str(i)
    for i, j in enumerate(career_stretch, 1):
        j["display_number"] = f"S{i}"
    for i, j in enumerate(income_normal, 1):
        j["display_number"] = f"G{i}"
    for i, j in enumerate(income_stretch, 1):
        j["display_number"] = f"GS{i}"

    # Split top_jobs into normal vs. demoted Stretch Fit section for email.
    # Stretch Fit = title/credential mismatch but real overlap — still
    # worth a glance, just not mixed in with the strong matches. Applied
    # within EACH pool separately so Stretch Fit demotion doesn't bleed
    # career-track jobs into the income-track section or vice versa.
    normal_jobs = [j for j in top_jobs if j.get("fit_tier") != "Stretch Fit"]
    stretch_jobs = [j for j in top_jobs if j.get("fit_tier") == "Stretch Fit"]

    if len(all_jobs) == 0:
        print(f"[STATS] No matching jobs found today.")
    else:
        print(f"[STATS] Found {len(all_jobs)} jobs total")
        print(f"[STATS] Pool A (Performance/AI): sending top {len(career_jobs)} of {len(pool_career)} candidates")
        print(f"[STATS] Pool B (QA Automation/Remote Income Floor incl. COBOL): sending top {len(income_jobs)} of {len(pool_income)} candidates")
    if stretch_jobs:
        print(f"[STATS] {len(stretch_jobs)} of those are Stretch Fit — will show in demoted section")

    print(f"{'='*55}\n")
    print(f"[STATS] Generating cover letters for {len(top_jobs)} job{'s' if len(top_jobs) != 1 else ''}...\n")
    for i, job in enumerate(top_jobs, 1):
        track = job.get("track", "")
        is_income_track = track in {"QA Automation", "Gap Track"}
        if is_income_track:
            # Income-track jobs always use the free template — never gated
            # by GENERATE_COVER_LETTERS, since templates cost nothing and
            # the flag only guards Sonnet API calls.
            job["cover_letter"] = generate_cover_letter(job)
        elif GENERATE_COVER_LETTERS:
            job["cover_letter"] = generate_cover_letter(job)
        else:
            job["cover_letter"] = ""
        # fit_analysis was already generated above (pre-sort) for AI-track
        # jobs; non-AI-track jobs simply have fit_analysis == "" and that's fine.
        print(f"  [{i:02d}] Score:{job['score']:3d} | Tier:{job.get('fit_tier') or '—':<13} | {job['source']:<10} | {job['title'][:50]}")
        print(f"        {job['company']} | {job['url'][:60]}")
        if job.get("fit_analysis"):
            print(f"        [FIT] {job['fit_analysis'][:120]}...")
        print()

    # Save newly seen job URLs
    if top_jobs:
        seen_urls.update(j.get("url", "") for j in top_jobs)
        save_seen_jobs(seen_urls)
        unsent = len(all_jobs) - len(top_jobs)
        if unsent > 0:
            print(f"[OK] Saved {len(top_jobs)} sent job URLs to seen_jobs.json")
            print(f"[OK] {unsent} additional jobs will appear in tomorrow's report")
        else:
            print(f"[OK] Saved {len(top_jobs)} job URLs to seen_jobs.json")

    # Save results
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_found": len(all_jobs),
        "top_jobs": top_jobs,
        "all_jobs": all_jobs
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[OK] Results saved to: {OUTPUT_FILE}")

    # Search Amazon jobs separately
    amazon_jobs = search_amazon_jobs()

    # Generate fit analysis for Amazon Spotlight jobs (gap fix:
    # Amazon jobs were on a separate path and never reached the main
    # fit-analysis loop above). Scoped to FIT_ANALYSIS_TRACKS same as the
    # regular pipeline — only AI-track Amazon postings get evaluated.
    if amazon_jobs and GENERATE_FIT_ANALYSIS:
        ai_amazon_jobs = [aj for aj in amazon_jobs if aj.get("track", "") in FIT_ANALYSIS_TRACKS]
        if ai_amazon_jobs:
            print(f"[STATS] Generating fit analysis for {len(ai_amazon_jobs)} AI-track Amazon Spotlight job(s)...")
        for aj in amazon_jobs:
            if aj.get("track", "") in FIT_ANALYSIS_TRACKS:
                fit_result = generate_fit_analysis(aj)
            else:
                fit_result = {"tier": "", "display": "", "hard_disqualified": False}
            aj["fit_tier"] = fit_result["tier"]
            aj["fit_analysis"] = fit_result["display"]
            aj["fit_hard_disqualified"] = fit_result["hard_disqualified"]
            if aj.get("fit_analysis"):
                print(f"        [FIT-AMZ] {aj['fit_analysis'][:120]}...")
        # Drop hard-disqualified Amazon jobs too — same standard applies.
        amazon_dropped = [aj for aj in amazon_jobs if aj.get("fit_hard_disqualified")]
        if amazon_dropped:
            amazon_jobs = [aj for aj in amazon_jobs if not aj.get("fit_hard_disqualified")]
            print(f"[OK] Dropped {len(amazon_dropped)} Amazon job(s) with hard fit disqualifiers")

    # Send email notification always — even if no jobs found
    send_email(top_jobs, amazon_jobs, funnel_summary=funnel.summary_dict())

    # Print top 3 with cover letters
    print("="*55)
    print("TOP 3 MATCHES WITH COVER LETTERS")
    print("="*55)
    for job in top_jobs[:3]:
        print(f"\n[TOP] [{job['score']} pts] {job['title']}")
        print(f"   Company : {job['company']}")
        print(f"   Source  : {job['source']}")
        print(f"   URL     : {job['url']}")
        print(f"   Keywords: {', '.join(job['matched_keywords'])}")
        if job.get("fit_analysis"):
            print(f"\n--- FIT ANALYSIS ---")
            print(job["fit_analysis"])
        print(f"\n--- COVER LETTER ---")
        print(job["cover_letter"])
        print("-"*40)


KMEANS_THRESHOLD     = 300  # target decision count before K-Means production training is meaningful
KMEANS_EXPLORATORY   = 100  # earlier milestone for exploratory K-Means

def get_decision_stats():
    """
    Reads job_decisions.json and returns a dict with:
      - total: total decision count
      - by_status: breakdown by decision status
      - pct: progress toward KMEANS_THRESHOLD (capped at 100)
    Returns None if file doesn't exist or can't be read.
    """
    decisions_file = os.path.join(JSON_DIR, "job_decisions.json")
    try:
        if not os.path.exists(decisions_file):
            return None
        with open(decisions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return None
        by_status = {}
        total = 0
        for date_key, entries in data.items():
            # Handle date-keyed array structure: {"2026-04-23": [{...}, ...]}
            if isinstance(entries, list):
                for record in entries:
                    if not isinstance(record, dict):
                        continue
                    status = record.get("decision") or record.get("status") or "unknown"
                    by_status[status] = by_status.get(status, 0) + 1
                    total += 1
            elif isinstance(entries, dict):
                # Legacy flat structure fallback
                status = entries.get("decision") or entries.get("status") or "unknown"
                by_status[status] = by_status.get(status, 0) + 1
                total += 1
        if total == 0:
            return None
        pct      = min(100, int((total / KMEANS_THRESHOLD) * 100))
        pct_expl = min(100, int((total / KMEANS_EXPLORATORY) * 100))
        return {
            "total":     total,
            "by_status": by_status,
            "pct":       pct,
            "pct_expl":  pct_expl,
        }
    except Exception as e:
        print(f"   [WARN] Could not read decision stats: {e}")
        return None


def send_email(top_jobs, amazon_jobs=None, funnel_summary=None):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    print("\n[EMAIL] Sending email notification...")
    # One run_id for this entire execution -- threaded through every job's
    # decision-link token AND the run-scoped archive file below, so same-day
    # reruns and late/backlogged form responses both resolve correctly.
    run_id = generate_run_id()
    today = datetime.now().strftime("%B %d, %Y")
    count = len(top_jobs)
    subject = f"Job Search Results - {count} Top Matches - {today}" if count > 0 else f"Job Search Ran - No Matches Found - {today}"

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;color:#333;">
    <h2 style="color:#1F3864;">Daily Job Search Results</h2>
    <p>Hi Hans, here are your top matches for <strong>{today}</strong>.</p>
    <div style="background:#f0f4ff;border:1px solid #c5d0e8;border-radius:8px;padding:12px 16px;margin:12px 0 16px;font-size:12px;color:#444;">
      <strong>Submit decisions:</strong> Use the form link at the bottom of this email.<br>
      Career Track jobs are numbered <strong>1–10</strong> &nbsp;|&nbsp;
      Gap Track jobs are numbered <strong>G1–G10</strong> &nbsp;|&nbsp;
      Amazon Spotlight jobs are numbered <strong>A1–A5</strong>
    </div>"""

    if count == 0:
        # Build a one-line diagnostic hint from funnel data, if available
        diagnostic_hint = ""
        if funnel_summary:
            biggest_label, biggest_drop_n, biggest_pct = funnel_summary.get("biggest_drop", (None, 0, 0))
            raw_count = funnel_summary.get("stages", {}).get("raw", 0)
            if biggest_drop_n > 0 and biggest_label:
                diagnostic_hint = (
                    f'<p style="margin:8px 0 0;color:#c62828;font-size:12px;">'
                    f'📉 <strong>Biggest drop:</strong> {biggest_label} removed '
                    f'{biggest_drop_n} of {raw_count} raw candidates ({biggest_pct:.0f}%). '
                    f'See Pipeline Funnel below for the full breakdown.'
                    f'</p>'
                )
        html += f"""<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:16px;margin:16px 0;">
        <p style="margin:0;color:#f57f17;font-weight:bold;">No matching jobs found today.</p>
        <p style="margin:8px 0 0;color:#555;">The script ran successfully but found no new jobs matching your criteria posted in the last 5 days that you haven't already seen. Check back tomorrow!</p>
        {diagnostic_hint}
        </div>"""
    html += "<hr/>"

    # Hard-disqualified (Weak Fit) jobs are already dropped upstream in
    # main() before send_email() is ever called — no need to re-check text
    # here.
    #
    # ── Dual pool rendering ──────────────────────────────────────
    # Pool A (Performance + AI, career-direction) and Pool B (QA
    # Automation + Remote Income Floor incl. COBOL, relief/income) are
    # rendered as two separate sections, each with its own normal/Stretch
    # Fit split — so a Performance Stretch Fit never gets mixed in with a
    # Remote Income Floor Stretch Fit, and the numbering inside each
    # section makes sense on its own.
    CAREER_TRACKS = {"Performance Engineering", "AI Engineering"}
    INCOME_TRACKS = {"QA Automation", "Gap Track"}
    career_section_jobs = [j for j in top_jobs if j.get("track") in CAREER_TRACKS]
    income_section_jobs = [j for j in top_jobs if j.get("track") in INCOME_TRACKS]

    def _render_job_card(job, number_label, accent="#1F3864", bg="#f0f7ff", border="#ddd", card_bg="#fff"):
        keywords = ", ".join(job["matched_keywords"][:6])
        cover    = job.get("cover_letter", "").replace("\n", "<br>")
        fit      = job.get("fit_analysis", "").replace("\n", "<br>")
        salary   = f"<p><strong>Salary:</strong> {job['salary']}</p>" if job.get("salary","").strip(" -") else ""
        track    = job.get("track", "")
        fit_block = ""
        if fit:
            fit_block = f"""
            <div style="background:{bg};border-left:3px solid {accent};padding:10px 14px;margin:8px 0 12px;border-radius:0 4px 4px 0;">
              <p style="margin:0 0 4px;font-size:12px;font-weight:bold;color:{accent};">🎯 FIT ANALYSIS</p>
              <p style="margin:0;font-size:13px;color:#444;line-height:1.4;">{fit}</p>
            </div>"""
        return f"""<div style="border:1px solid {border};border-radius:8px;padding:16px;margin-bottom:24px;background:{card_bg};">
            <h3 style="color:{accent};margin:0 0 4px;">{number_label} - {job["title"]}
            <span style="font-size:12px;background:#e8f0fe;color:{accent};padding:2px 8px;border-radius:10px;">{track}</span></h3>
            <p><strong>Company:</strong> {job["company"]} | <strong>Source:</strong> {job["source"]} | <strong>Score:</strong> {job["score"]} pts</p>
            <p><strong>Posted:</strong> <span style="color:#e65100;font-weight:500;">{job.get("posted","Unknown")[:10] if job.get("posted") else "Date unknown - verify before applying!"}</span> | <strong>Track:</strong> {job.get("track","N/A")}</p>
            {salary}
            <p><strong>Matched Skills:</strong> {keywords}</p>
            {fit_block}
            <p>
                {f"<a href='{job.get('url', '')}' style='background:{accent};color:#fff;padding:8px 16px;border-radius:4px;text-decoration:none;'>View and Apply</a>"}
                <a href="{build_decision_link(run_id, number_label)}" style="margin-left:10px;color:{accent};font-size:13px;text-decoration:none;border-bottom:1px solid {accent};">&#10003; Submit Decision</a>
            </p>
            <hr style="border:none;border-top:1px solid #eee;margin:12px 0"/>
            <p><strong>Cover Letter:</strong></p>
            <div style="background:#f9f9f9;padding:12px;border-radius:4px;font-size:14px;">{cover}</div>
        </div>"""

    def _render_stretch_card(job, number_label):
        keywords = ", ".join(job["matched_keywords"][:6])
        cover    = job.get("cover_letter", "").replace("\n", "<br>")
        fit      = job.get("fit_analysis", "").replace("\n", "<br>")
        track    = job.get("track", "")
        fit_block = ""
        if fit:
            fit_block = f"""
                <div style="background:#fffaf0;border-left:3px solid #d9a441;padding:8px 12px;margin:6px 0 10px;border-radius:0 4px 4px 0;">
                  <p style="margin:0;font-size:12px;color:#5c4413;line-height:1.4;">🎯 {fit}</p>
                </div>"""
        return f"""
  <div style="border:1px solid #e8d4a4;border-radius:6px;padding:12px 14px;margin-bottom:12px;background:#fffdf7;">
    <p style="margin:0 0 4px;font-weight:bold;font-size:13px;color:#5c4413;">{number_label} — {job["title"]}
    <span style="font-size:11px;background:#f3e3bd;color:#5c4413;padding:2px 6px;border-radius:8px;margin-left:6px;">{track}</span></p>
    <p style="margin:0 0 6px;font-size:12px;color:#777;"><strong>{job["company"]}</strong> | {job["source"]} | {job["score"]} pts</p>
    <p style="margin:0 0 8px;font-size:12px;color:#777;"><strong>Matched:</strong> {keywords}</p>
    {fit_block}
    <a href="{job.get('url','')}" style="background:#d9a441;color:#fff;padding:6px 14px;border-radius:4px;text-decoration:none;font-size:12px;">View and Apply</a>
    <a href="{build_decision_link(run_id, number_label)}" style="margin-left:8px;color:#5c4413;font-size:12px;text-decoration:none;border-bottom:1px solid #5c4413;">&#10003; Submit Decision</a>
    <details style="margin-top:8px;">
      <summary style="font-size:11px;color:#999;cursor:pointer;">Cover letter draft</summary>
      <div style="background:#f9f9f9;padding:10px;border-radius:4px;font-size:13px;margin-top:6px;">{cover}</div>
    </details>
  </div>"""

    def _render_pool_section(jobs, heading, intro, accent, bg):
        """Renders one full pool's section: header/intro, normal job cards,
        then a demoted Stretch Fit sub-section (only if any exist). Uses
        each job's pre-computed display_number (set once in main(), single
        source of truth shared with today_jobs.json persistence) rather
        than recomputing a number here."""
        if not jobs:
            return ""
        normal = [j for j in jobs if j.get("fit_tier") != "Stretch Fit"]
        stretch = [j for j in jobs if j.get("fit_tier") == "Stretch Fit"]
        section_html = f"""
<div style="margin:28px 0 8px;">
  <h2 style="color:{accent};margin:0 0 4px;font-size:18px;border-bottom:2px solid {accent};padding-bottom:6px;">{heading}</h2>
  <p style="margin:6px 0 16px;font-size:12px;color:#666;">{intro}</p>
</div>"""
        for job in normal:
            section_html += _render_job_card(job, job.get("display_number", "?"), accent=accent, bg=bg)
        if stretch:
            section_html += f"""
<div style="background:#fff9ed;border:2px dashed #d9a441;border-radius:8px;padding:16px;margin:16px 0 24px;">
  <h3 style="color:#7a5b16;margin:0 0 4px;font-size:15px;">⚠️ Stretch Fits ({len(stretch)})</h3>
  <p style="margin:0 0 12px;font-size:12px;color:#7a5b16;">Title/credential pattern doesn't fully match, but there's real overlap with your actual strengths. Worth a quick look — your call.</p>"""
            for job in stretch:
                section_html += _render_stretch_card(job, job.get("display_number", "?"))
            section_html += "</div>"
        return section_html

    html += _render_pool_section(
        career_section_jobs,
        "🎯 Performance & AI Engineering — Career Track",
        "Your core direction: Performance Engineering and AI Systems/Agent roles. Numbered 1–10 (Stretch Fit: S1–S5).",
        accent="#1F3864", bg="#f0f7ff",
    )
    html += _render_pool_section(
        income_section_jobs,
        "💼 QA, Testing & Gap Track",
        "Remote $25+/hr OR KC-metro hybrid/onsite $30+/hr (COBOL: $30+/hr remote, $55+/hr hybrid/onsite). Broad — manual QA, automation tooling, general IT support/helpdesk/sysadmin, will-train postings, and COBOL/mainframe. Numbered G1–G10.",
        accent="#8a6d1a", bg="#fff8e7",
    )

    # ── Amazon Jobs Spotlight ─────────────────────────────────
    if amazon_jobs:
        html += """
<div style="background:#f0f7ff;border:2px solid #FF9900;border-radius:8px;padding:16px;margin:24px 0 8px;">
  <h2 style="color:#232F3E;margin:0 0 4px;font-size:17px;">Amazon Jobs Spotlight</h2>
  <p style="margin:0 0 12px;font-size:12px;color:#555;">Top Amazon postings (last 10 days) — you are an internal employee, use your advantage!<br>
  Search the Job ID in the <strong>A to Z app</strong> to find internal-only postings not listed here.</p>"""

        for i, job in enumerate(amazon_jobs, 1):
            keywords = ", ".join(job["matched_keywords"][:5])
            salary   = f"<span style='color:#232F3E;'> | <strong>Salary:</strong> {job['salary']}</span>" if job.get("salary","").strip(" -") else ""
            age_verified = job.get("age_verified", False)
            raw_posted   = job.get("posted", "")
            if raw_posted and age_verified:
                posted      = raw_posted[:10]
                posted_warn = ""
            else:
                # Don't claim "Recent" for a date we never actually verified —
                # this is the gap that let a 30+ day-old posting through on
                # 2026-06-19. Flag it instead so Hans can eyeball it himself.
                posted      = "Unknown"
                posted_warn = (
                    ' <span style="color:#c0392b;font-weight:bold;">⚠ age unverified — check listing</span>'
                )
            # Extract Job ID from URL (e.g. amazon.jobs/en/jobs/1234567/title)
            job_url  = job.get("url", "")
            id_match = re.search(r"/jobs/(\d+)", job_url)
            job_id   = id_match.group(1) if id_match else "N/A"
            fit_amz  = job.get("fit_analysis", "")
            fit_html = (
                f'<p style="margin:6px 0 8px;font-size:12px;color:#1a3a5c;background:#fff8e7;'
                f'border-left:3px solid #FF9900;padding:6px 10px;border-radius:3px;">'
                f'<strong>Fit:</strong> {fit_amz}</p>'
            ) if fit_amz else ""
            html += f"""
  <div style="border:1px solid #FFD700;border-radius:6px;padding:12px 14px;margin-bottom:12px;background:#fff;">
    <p style="margin:0 0 4px;font-weight:bold;font-size:13px;color:#232F3E;">#{i} — {job["title"]}</p>
    <p style="margin:0 0 6px;">
      <span style="background:#FF9900;color:#232F3E;padding:3px 10px;border-radius:4px;font-size:13px;font-weight:bold;font-family:monospace;">Job ID: {job_id}</span>
      <span style="font-size:11px;color:#888;margin-left:8px;">← Search this in A to Z app</span>
    </p>
    <p style="margin:0 0 4px;font-size:12px;color:#555;">
      <strong>Track:</strong> {job.get("track","")} &nbsp;|&nbsp;
      <strong>Score:</strong> {job["score"]} pts &nbsp;|&nbsp;
      <strong>Posted:</strong> {posted}{posted_warn}{salary}
    </p>
    <p style="margin:0 0 8px;font-size:12px;color:#555;"><strong>Matched:</strong> {keywords}</p>
    {fit_html}
    <a href="{job_url}" style="background:#FF9900;color:#232F3E;padding:7px 14px;border-radius:4px;text-decoration:none;font-size:12px;font-weight:bold;">View on Amazon Jobs</a>
    <a href="{build_decision_link(run_id, f'A{i}')}" style="margin-left:8px;color:#232F3E;font-size:12px;text-decoration:none;border-bottom:1px solid #232F3E;">&#10003; Submit Decision</a>
  </div>"""

        html += "</div>"

    html += f"""
<div style="background:#eaf3ff;border:1px solid #b5d4f4;border-radius:8px;padding:14px 18px;margin:16px 0 20px;">
  <p style="margin:0 0 10px;font-weight:bold;color:#1a3a5c;font-size:13px;">SUBMIT YOUR DECISIONS</p>
  <p style="margin:0 0 12px;font-size:12px;color:#555;">Each job above has its own <strong>Submit Decision</strong> link that pre-fills the job number and a tracking token for you. Prefer to fill it out manually instead? Use the blank form:</p>
  <p style="margin:0 0 12px;">
    <a href="{FORM_BASE_URL}" style="background:#1a3a5c;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;font-size:13px;font-weight:bold;">Open Blank Form</a>
  </p>
  <p style="margin:8px 0 6px;font-size:12px;color:#555;">You can submit one job at a time or all at once, anytime before midnight.</p>
  <p style="margin:6px 0 4px;font-size:12px;color:#888;"><strong>Decision options:</strong> Applied &nbsp;|&nbsp; Bad Link/Job Not Available &nbsp;|&nbsp; Onsite/Not Remote &nbsp;|&nbsp; Too Senior &nbsp;|&nbsp; Salary Too Low &nbsp;|&nbsp; Not Interested &nbsp;|&nbsp; Already Seen/Duplicate &nbsp;|&nbsp; Search Page Listing &nbsp;|&nbsp; Not in United States &nbsp;|&nbsp; Other</p>
  <p style="margin:4px 0 0;font-size:11px;color:#aaa;"><em>Unanswered jobs are treated as neutral — no action taken.</em></p>
</div>
<hr/>"""

    # ── K-Means Decision Tracker ──────────────────────────────
    stats = get_decision_stats()
    if stats:
        total       = stats["total"]
        pct         = stats["pct"]
        pct_expl    = stats["pct_expl"]
        remaining_p = max(0, KMEANS_THRESHOLD - total)
        remaining_e = max(0, KMEANS_EXPLORATORY - total)
        # Build breakdown rows
        status_rows = ""
        status_labels = {
            "applied":          ("✅", "#2e7d32"),
            "skipped":          ("⏭️", "#555"),
            "skip":             ("⏭️", "#555"),
            "too_senior":       ("🔺", "#e65100"),
            "too_junior":       ("🔻", "#1565c0"),
            "location_mismatch":("📍", "#6a1b9a"),
            "salary_too_low":   ("💰", "#795548"),
            "broken_link":      ("🔗", "#b71c1c"),
            "duplicate":        ("♻️", "#37474f"),
            "not_interested":   ("👎", "#555"),
            "needs_review":     ("🔍", "#f57f17"),
            "other":            ("❓", "#888"),
        }
        for status, cnt in sorted(stats["by_status"].items(), key=lambda x: -x[1]):
            icon, color = status_labels.get(status.lower(), ("•", "#555"))
            status_rows += f"""<span style="display:inline-block;margin:2px 8px 2px 0;font-size:11px;color:{color};">
                {icon} <strong>{status}</strong>: {cnt}</span>"""

        # Exploratory bar: green when reached, blue/orange while in progress
        if total >= KMEANS_EXPLORATORY:
            expl_color = "#4caf50"   # green — milestone hit
            expl_label = f"✅ Exploratory ready ({KMEANS_EXPLORATORY})"
        else:
            expl_color = "#1F3864"
            expl_label = f"<strong>{remaining_e}</strong> to exploratory ({KMEANS_EXPLORATORY})"

        # Production bar color graduates by progress
        prod_color = "#4caf50" if pct >= 75 else "#ff9800" if pct >= 40 else "#1F3864"

        html += f"""
<div style="background:#f8f9ff;border:1px solid #c5d0e8;border-radius:8px;padding:14px 18px;margin:16px 0 20px;">
  <p style="margin:0 0 6px;font-weight:bold;color:#1a3a5c;font-size:13px;">📊 K-MEANS TRAINING PROGRESS</p>
  <p style="margin:0 0 4px;font-size:12px;color:#444;">
    <strong>{total}</strong> total decisions
  </p>

  <p style="margin:8px 0 2px;font-size:11px;color:#444;">
    {expl_label} &nbsp;|&nbsp; <strong>{pct_expl}%</strong>
  </p>
  <div style="background:#e0e0e0;border-radius:4px;height:8px;width:100%;margin:0 0 8px;">
    <div style="background:{expl_color};width:{pct_expl}%;height:8px;border-radius:4px;"></div>
  </div>

  <p style="margin:6px 0 2px;font-size:11px;color:#444;">
    <strong>{remaining_p}</strong> to production ({KMEANS_THRESHOLD}) &nbsp;|&nbsp; <strong>{pct}%</strong>
  </p>
  <div style="background:#e0e0e0;border-radius:4px;height:8px;width:100%;margin:0 0 10px;">
    <div style="background:{prod_color};width:{pct}%;height:8px;border-radius:4px;"></div>
  </div>

  <div style="margin-top:6px;">{status_rows}</div>
</div>"""
    else:
        html += """
<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:10px 16px;margin:16px 0 20px;">
  <p style="margin:0;font-size:12px;color:#f57f17;">📊 K-Means tracker: no decisions recorded yet — start submitting decisions via the form above!</p>
</div>"""

    # ── Pipeline Funnel section ─────────────────────────────
    if funnel_summary:
        stages = funnel_summary.get("stages", {})
        biggest = funnel_summary.get("biggest_drop", (None, 0, 0))

        raw = stages.get("raw", 0)
        final = stages.get("final", 0)
        survival_pct = (final / raw * 100) if raw > 0 else 0

        # Build stage rows
        stage_order = [
            ("raw",              "Raw candidates"),
            ("after_recency",    "After recency filter"),
            ("after_title",      "After title filter"),
            ("after_level",      "After level filter"),
            ("after_score",      "After score filter"),
            ("after_us",         "After US/remote filter"),
            ("after_blocked",    "After blocked-site filter"),
            ("kept_by_sources",  "Kept by sources"),
            ("after_minscore",   "After min-score threshold"),
            ("after_cobol_hybrid", "After COBOL hybrid pay-tier filter"),
            ("after_pay_floor",  "After Track 4 pay-floor filter"),
            ("after_cross_dedup", "After cross-source dedup"),
            ("after_seen_dedup",  "After already-seen dedup"),
            ("after_fit_hard_disqualify", "After AI fit hard-disqualify"),
            ("final",            "→ Final email"),
        ]
        rows_html = ""
        for key, label in stage_order:
            count = stages.get(key, 0)
            pct = (count / raw * 100) if raw > 0 else 0
            is_final = (key == "final")
            row_style = "font-weight:bold;color:#1a3a5c;" if is_final else "color:#444;"
            rows_html += (
                f'<tr>'
                f'<td style="padding:2px 8px 2px 0;font-size:11px;{row_style}">{label}</td>'
                f'<td style="padding:2px 8px 2px 0;font-size:11px;text-align:right;{row_style}">{count}</td>'
                f'<td style="padding:2px 0;font-size:11px;text-align:right;color:#888;">{pct:.1f}%</td>'
                f'</tr>'
            )

        # Biggest-drop diagnostic line
        biggest_label, biggest_drop_n, biggest_pct = biggest
        if biggest_drop_n > 0 and biggest_label:
            biggest_html = (
                f'<p style="margin:8px 0 0;font-size:11px;color:#c62828;">'
                f'📉 <strong>Biggest drop:</strong> {biggest_label} removed '
                f'{biggest_drop_n} jobs ({biggest_pct:.0f}% of prior stage)'
                f'</p>'
            )
        else:
            biggest_html = ""

        # Per-source raw context (optional small print)
        by_source = funnel_summary.get("by_source", {})
        source_html = ""
        if by_source:
            source_parts = [f"{s}: {n}" for s, n in sorted(by_source.items(), key=lambda x: -x[1])]
            source_html = (
                f'<p style="margin:6px 0 0;font-size:10px;color:#888;">'
                f'Raw by source: {" &nbsp;|&nbsp; ".join(source_parts)}'
                f'</p>'
            )

        html += f"""
<div style="background:#f8f9ff;border:1px solid #c5d0e8;border-radius:8px;padding:14px 18px;margin:16px 0 20px;">
  <p style="margin:0 0 6px;font-weight:bold;color:#1a3a5c;font-size:13px;">📊 PIPELINE FUNNEL</p>
  <p style="margin:0 0 10px;font-size:12px;color:#444;">
    <strong>{raw}</strong> raw → <strong>{final}</strong> final match{'es' if final != 1 else ''}
    &nbsp;({survival_pct:.1f}% survival rate)
  </p>
  <table style="width:100%;border-collapse:collapse;margin-top:4px;">
    {rows_html}
  </table>
  {biggest_html}
  {source_html}
</div>"""

    html += """<hr/><p style="font-size:12px;color:#888;">Sent automatically by your Job Search Script.</p></body></html>"""

    # ── Save today's batch for overnight script ───────────────
    import hashlib
    def _job_id(job):
        raw = f"{job.get('title','')}{job.get('company','')}{job.get('url','')}"
        return hashlib.md5(raw.encode()).hexdigest()[:10]

    today_key  = datetime.now().strftime("%Y-%m-%d")
    batch_file = os.path.join(JSON_DIR, "today_jobs.json")
    try:
        # Regular jobs use their pre-computed display_number (set once in
        # the dual-pool split above) — career jobs get "1".."10"/"S1".. and
        # income jobs get "R1".."R15"/"RS1".. This is the SAME number the
        # email shows, so a form submission referencing "R3" will actually
        # match a "R3" entry here. "number" stores the raw string/int form;
        # "number_display" is kept for backward-compat with anything that
        # reads it as display text.
        regular_batch = [
            {
                "job_id":           _job_id(j),
                "number":           j.get("display_number", str(idx)),
                "number_display":   j.get("display_number", str(idx)),
                "token":            make_job_token(run_id, j.get("display_number", str(idx))),
                "run_id":           run_id,
                "title":            j.get("title", ""),
                "company":          j.get("company", ""),
                "track":            j.get("track", ""),
                "score":            j.get("score", 0),
                "url":              j.get("url", ""),
                "matched_keywords": j.get("matched_keywords", []),
                "source":           j.get("source", ""),
                "is_amazon":        False,
                "fit_tier":         j.get("fit_tier", ""),
                "fit_analysis":     j.get("fit_analysis", ""),
                "level_signal":     j.get("level_signal", ""),
            }
            for idx, j in enumerate(top_jobs, 1)
        ]
        # Amazon jobs numbered A1-AN
        amazon_batch = [
            {
                "job_id":           _job_id(j),
                "number":           f"A{idx}",
                "number_display":   f"A{idx}",
                "token":            make_job_token(run_id, f"A{idx}"),
                "run_id":           run_id,
                "title":            j.get("title", ""),
                "company":          "Amazon",
                "track":            j.get("track", ""),
                "score":            j.get("score", 0),
                "url":              j.get("url", ""),
                "matched_keywords": j.get("matched_keywords", []),
                "source":           "Amazon Jobs",
                "is_amazon":        True,
                "fit_tier":         j.get("fit_tier", ""),
                "fit_analysis":     j.get("fit_analysis", ""),
                "level_signal":     j.get("level_signal", ""),
            }
            for idx, j in enumerate(amazon_jobs or [], 1)
        ]
        batch = {
            "date": today_key,
            "run_id": run_id,
            "jobs": regular_batch + amazon_batch,
        }
        with open(batch_file, "w") as f:
            json.dump(batch, f, indent=2)
        print(f"   [OK] Saved {len(regular_batch)} regular + {len(amazon_batch)} Amazon jobs to today_jobs.json")
        # Archive a dated copy so backfills always have full metadata
        # (legacy, date-keyed -- kept for backward compat with any
        # already-sent emails that predate the token system; gets
        # overwritten on same-day reruns, same as before)
        archive_file = os.path.join(
            JSON_DIR,
            f"today_jobs_{today_key}.json"
        )
        with open(archive_file, "w") as f:
            json.dump(batch, f, indent=2)
        print(f"   [OK] Archived to today_jobs_{today_key}.json")

        # Run-scoped archive -- NEVER overwritten, regardless of how many
        # times the script runs today or how long a response sits
        # unanswered. This is what the token-based sync reads from.
        run_archive_file = os.path.join(
            JSON_DIR,
            f"{RUN_ARCHIVE_PREFIX}{run_id}.json"
        )
        with open(run_archive_file, "w") as f:
            json.dump(batch, f, indent=2)
        print(f"   [OK] Archived to {RUN_ARCHIVE_PREFIX}{run_id}.json (token sync source)")

        # ── Write Amazon jobs to job_decisions.json ───────────
        # FIXED 4/30 gap: Amazon Spotlight jobs (A1–A5) were not being
        # persisted to job_decisions.json. Now they are, so decisions.py
        # has a complete record to work from.
        if amazon_batch:
            _persist_amazon_to_decisions(amazon_batch, today_key)

    except Exception as e:
        print(f"   [WARN] Could not save today_jobs.json: {e}")
        log_error(f"today_jobs.json save failed: {e}")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Job Search <{GMAIL_ADDRESS}>"
        msg["To"]      = EMAIL_TO
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, EMAIL_TO, msg.as_string())
        print(f"   Email sent to {EMAIL_TO}")
    except Exception as e:
        print(f"   Email failed: {e}")
        log_error(f"Email send failed: {e}")


def _persist_amazon_to_decisions(amazon_batch, today_key):
    """
    Write Amazon Spotlight jobs into job_decisions.json with a 'pending' decision.
    This closes the 4/30 gap where Amazon jobs (A1–A5) weren't being persisted
    for the decisions/review pipeline.

    Mirrors the structure decisions.py expects: date-keyed array of dicts with
    job_id, title, company, track, score, url, matched_keywords, source, and
    a default decision='pending' / reviewed=false so review_decisions.py can
    pick them up if they're never explicitly decided on.
    """
    try:
        # Load existing decisions
        if os.path.exists(DECISIONS_FILE):
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                decisions = json.load(f)
        else:
            decisions = {}

        if today_key not in decisions:
            decisions[today_key] = []

        # Build set of existing job_ids for today to avoid duplicates
        existing_ids = {entry.get("job_id") for entry in decisions[today_key]
                        if isinstance(entry, dict)}

        added = 0
        for job in amazon_batch:
            jid = job.get("job_id", "")
            if not jid or jid in existing_ids:
                continue
            decisions[today_key].append({
                "job_id":           jid,
                "number":           job.get("number"),
                "number_display":   job.get("number_display"),
                "title":            job.get("title", ""),
                "company":          job.get("company", "Amazon"),
                "track":            job.get("track", ""),
                "score":            job.get("score", 0),
                "url":              job.get("url", ""),
                "matched_keywords": job.get("matched_keywords", []),
                "source":           job.get("source", "Amazon Jobs"),
                "is_amazon":        True,
                "fit_tier":         job.get("fit_tier", ""),
                "fit_analysis":     job.get("fit_analysis", ""),
                "decision":         "pending",
                "reason":           "",
                "detection_method": "auto",
                "confidence":       1.0,
                "notes":            "",
                "reviewed":         False,
                "reviewed_date":    "",
                "recorded_at":      datetime.now().isoformat(),
            })
            existing_ids.add(jid)
            added += 1

        if added > 0:
            with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(decisions, f, indent=2)
            print(f"   [OK] Persisted {added} Amazon jobs to job_decisions.json")
    except Exception as e:
        print(f"   [WARN] Could not persist Amazon jobs to decisions: {e}")
        log_error(f"Amazon decisions persist failed: {e}")

    # Tidy up the legacy date-keyed archive pile once per run. Never
    # fatal -- a rotation failure shouldn't take down an otherwise-good run.
    try:
        rotate_legacy_today_jobs_archives()
    except Exception as e:
        print(f"   [WARN] Legacy archive rotation failed: {e}")
        log_error(f"Legacy archive rotation failed: {e}")


if __name__ == "__main__":
    try:
        main()
        # Snapshot logs to logs/ folder (14-day rolling retention).
        print("\n[LOGS] Snapshotting run logs...")
        snap_count, prune_count = snapshot_and_prune_logs()
        print(f"   [OK] Snapshotted {snap_count} log file(s), pruned {prune_count} old snapshot(s)")
        # Push all local changes to GitHub at end of every run.
        git_commit_push()
        # Ingest latest decisions into ChromaDB for RAG
        print("\n[RAG] Ingesting decisions into ChromaDB...")
        job_rag.ingest_decisions()
    except Exception as e:
        import traceback as _tb
        tb = _tb.format_exc()
        print(f"\n[FATAL] {tb}")
        log_error(f"FATAL unhandled exception: {e}\n{tb}")
        send_failure_alert("unhandled exception", tb)
