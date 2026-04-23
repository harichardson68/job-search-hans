# Automated Performance Engineering Job Search System

A Python-based automated job search pipeline built for a senior performance engineer targeting **LoadRunner/VuGen/LRE**, **AI Engineering (entry-level)**, and **COBOL/Mainframe** roles. Runs daily via Windows Task Scheduler and delivers a scored, filtered, deduplicated HTML email digest with AI-generated cover letters.

---

## What It Does

- **Multi-source job aggregation** — pulls from RemoteOK, Serper (Google Jobs), Adzuna, USAJobs, Google Custom Search, and Wellfound
- **3-track scoring engine** — independently scores each job against Performance Engineering, AI Engineering, and COBOL/Mainframe keyword sets
- **Strict relevance filtering** — title must match required keywords; non-US locations, blocked aggregator sites, sketchy companies, and state-restricted remote roles are all filtered out
- **Deduplication** — cross-source dedup by title+company within each run, plus persistent `seen_jobs.json` to prevent repeat sends across days
- **AI cover letter generation** — uses Claude (Anthropic) to write a tailored cover letter per job using a full resume context block
- **HTML email digest** — sends a formatted daily digest showing top 10 jobs with score, matched keywords, source, and cover letter

---

## Architecture

```
Sources (6)                  Filtering Pipeline              Output
──────────                   ──────────────────              ──────
RemoteOK        ──┐          is_us_remote()     ─┐
Serper          ──┤          is_relevant_title() ─┤          seen_jobs.json
Adzuna          ──┼──► raw ──is_blocked_site()  ─┼──► scored ──► top 10 ──► Gmail HTML digest
USAJobs         ──┤   jobs   is_blocked_company()─┤   jobs          │
Google Jobs     ──┤          score_job()          ─┤                 └──► cover letters (Claude)
Wellfound       ──┘          deduplication        ─┘
```

---

## Scoring Weights

| Signal | Points |
|---|---|
| LoadRunner/VuGen/LRE in **title** | +50 |
| LoadRunner/VuGen/LRE in **description** | +50 |
| Performance Engineering keywords (high) | +35 |
| AI Engineering keywords (high) | +20 |
| Bonus/supporting keywords | +5–15 each |
| COBOL/Mainframe keywords | +2–10 |

**Minimum score thresholds:** Performance Engineering ≥ 30 pts · AI Engineering ≥ 40 pts · COBOL ≥ 10 pts

---

## Job Tracks

| Track | Priority | Notes |
|---|---|---|
| Performance Engineering (LoadRunner) | Highest | Senior titles allowed if LoadRunner mentioned |
| AI Engineering | Second | Entry/mid level only; senior filtered unless exact LR match |
| COBOL/Mainframe | Floor | Last-resort fallback |

---

## Setup

### 1. Install dependencies
```bash
pip install requests feedparser python-dateutil anthropic
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys and Gmail credentials
```

Then load the `.env` in your environment before running, or use a library like `python-dotenv`.

### 3. Run manually
```bash
python job_search.py
```

### 4. Schedule daily (Windows Task Scheduler)
- Action: `python C:\path\to\job_search.py`
- Trigger: Daily at your preferred time
- Log output goes to `job_search_run.log` automatically

---

## API Keys Required

| Service | Purpose | Cost |
|---|---|---|
| [Anthropic](https://console.anthropic.com) | Cover letter generation | Pay per use |
| [Serper](https://serper.dev) | Google Jobs search | Free tier (2,500/mo) |
| [Adzuna](https://developer.adzuna.com) | Job board API | Free tier (1,000/day) |
| [USAJobs](https://developer.usajobs.gov) | Federal jobs | Free (registration required) |
| [Google Custom Search](https://developers.google.com/custom-search) | Backup search | Free tier (100/day) |
| Gmail App Password | Email delivery | Free |

---

## Key Design Decisions

**Why not just use LinkedIn?** LinkedIn's API is gated. This system uses multiple free APIs and Google search to cast a wide net without scraping.

**Why a scoring engine instead of simple keyword match?** A senior performance engineer's ideal role (LoadRunner + cloud + AI hybrid) is rare. Scoring lets the system surface "great match / not perfect" jobs rather than returning nothing or everything.

**Why persistent seen_jobs.json?** Running daily means the same postings appear repeatedly. Tracking sent URLs prevents email fatigue and keeps the digest focused on genuinely new opportunities.

---

## Output Files

| File | Purpose |
|---|---|
| `job_search_run.log` | Full run log with debug output |
| `seen_jobs.json` | Persistent store of already-sent job URLs |
| `job_results.json` | Full structured output of current run |

---

## About

Built by **Hans Richardson** — Senior Performance/QA Test Engineer with 28 years of experience, specializing in LoadRunner/VuGen/LRE. This project is part of a broader AI engineering portfolio demonstrating agentic Python tooling, multi-source data pipelines, and LLM integration.

- [LinkedIn](https://linkedin.com/in/hans-richardson)
