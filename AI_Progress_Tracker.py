# Hans Richardson - AI Engineering Progress Tracker
# Updated: June 12, 2026 (evening)
# Share this file at the start of each Claude session for instant context!

# ─────────────────────────────────────────────────────────────
# PERSONAL PROFILE
# ─────────────────────────────────────────────────────────────
NAME            = "Hans Richardson"
EMAIL           = "harichardson68@gmail.com"
LOCATION        = "Lee's Summit, MO (Remote)"
LINKEDIN        = "linkedin.com/in/hans-richardson"
CURRENT_JOB     = "Amazon Warehouse Associate (Dec 2025 - Present) — actively seeking Performance Engineering / AI Engineering roles"
CLEARANCE       = "Public Trust (active — held continuously since USDA contract 2021-2025)"
EXPERIENCE      = "24+ years IT (14 specialized in Performance Test Engineering — LoadRunner/VuGen/LRE)"
CORE_SKILL      = "LoadRunner/VuGen/LRE - 14 years expert"
EDUCATION       = "B.S. Computer Information Systems + B.A. Marketing"

# ─────────────────────────────────────────────────────────────
# GITHUB
# ─────────────────────────────────────────────────────────────
GITHUB = {
    "username": "harichardson68",
    "repos": [
        {
            "name": "job-agent",
            "url": "github.com/harichardson68/job-agent",
            "description": "FLAGSHIP AI PROJECT — autonomous agentic job search. Claude decides each action in an observe-plan-act loop (NOT a fixed pipeline). Built June 2026.",
            "topics": ["python", "agentic-ai", "claude-api", "llm-tool-use", "ai-agents", "observability"],
            "architecture": {
                "agent.py": "the loop — plan -> act -> observe -> repeat until stop()",
                "core/state.py": "run state: history, accumulated jobs, dedup, 15-iter safety cap",
                "core/planner.py": "calls Claude for next action (forced JSON, fail-safe to stop)",
                "core/logger.py": "streaming THINK/ACT/SEE reasoning trace -> console + GUI + logs/",
                "tools/registry.py": "ONE dict generates the planner menu AND the function lookup",
                "tools/search.py": "Adzuna + Serper, classify_location() (US-remote OR KC ~30min)",
                "tools/score.py": "2-layer dedup (across-run + cross-source) -> tiered scoring -> rank",
                "tools/analyze_fit.py": "LLM fit tiers (Excellent->Weak) + gap-flagging, top-5 cost cap",
                "tools/cover_letter.py": "on-demand, chosen roles only",
                "tools/email_results.py": "HTML digest — act from anywhere",
                "config/": "goals.py, salary_config.py (LR $110k/$55hr hard, AI $90k/$45hr soft), watch_vectors.py (OPM/Oracle Federal HR 2.0 intel)",
            },
            "key_design": [
                "Registry = single source of truth: add a tool in one place, menu + loop both get it",
                "Planner is tool-agnostic — reads the generated menu, zero changes per new tool",
                "Fail-safe by default: bad JSON / unknown tool / tool error -> safe stop, never crash/loop forever",
                "Dev/prod TEST MODE toggle (Agent Hub): Haiku planner + 4-iter cap + skip fit = cheap iteration; default OFF",
                "Track-aware AI seniority filter: drops Staff/Principal/Lead AI, lets borderline through to fit analysis",
                "Cross-source dedup: company-gated + 75% title-ratio (catches 'Agentic AI Engineer' vs '...Platform Engineer', avoids false-merging 'AI Engineer' vs 'Senior AI Platform Engineer')",
                "Human-in-the-loop by deliberate choice — NOT unsupervised self-modification",
            ],
            "status": "Working end-to-end, live in Agent Hub via 'Run Agent' button. README written. Pushed public June 12, 2026.",
            "portfolio_role": "CENTERPIECE of AI portfolio. The agentic loop pipeline (job_search.py) and FLAPBOARD are supporting projects.",
            "built_with": "Claude.ai as architect/PM + Claude Code (CLI) as file-level executor",
        },
        {
            "name": "job-search-hans",
            "url": "github.com/harichardson68/job-search-hans",
            "description": "Automated performance engineering job search pipeline (deterministic — fixed sequence each run). Houses agent_hub.py which now calls job-agent's run_agent().",
            "topics": ["python", "job-search", "performance-testing", "loadrunner", "automation", "claude-api"],
        },
        {
            "name": "job-search-evan",
            "url": "github.com/harichardson68/job-search-evan",
            "description": "Automated cybersecurity job search pipeline for Evan",
            "topics": ["python", "job-search", "cybersecurity", "automation", "claude-api"],
        },
        {
            "name": "FLAPBOARD",
            "url": "github.com/harichardson68/FLAPBOARD",
            "live_url": "https://flapboard.onrender.com",
            "description": "Flask-based flight price comparison app with Solari split-flap aesthetic (amber on navy). Full auth, real flight pricing via Sky Scrapper API, saved searches with price-drop email alerts, airport lookup modal. Live on Render.",
            "stack": "Flask 3.0 app factory, SQLite/SQLAlchemy, Flask-Login, Flask-WTF CSRF, Flask-Migrate, Flask-Limiter, Werkzeug PBKDF2, Sky Scrapper RapidAPI, SMTP alerts",
            "tests": "11 integration tests passing",
            "completed": [
                "Sky Scrapper RapidAPI integration with SkyId caching + realistic mock fallback",
                "Graceful degradation — is_live flag shows live/estimated banner in UI",
                "SavedSearch model — origin, destination, date, alert_threshold, last_price, last_checked",
                "Price-drop email alerts (alerts.py — reuses job_search.py SMTP pattern)",
                "/run-checks endpoint protected by ALERT_SECRET — ready for cron-job.org",
                "Airport lookup modal — 70 US airports, type city name OR IATA code, instant filter",
                "Dashboard redesign matching Render aesthetic — centered card, / where to? heading",
                "Flask-Migrate wired in — db init/migrate/upgrade working",
                "Date picker color fix for dark theme",
                "All deployed to Render with env vars",
            ],
            "next_steps": [
                "Set up cron-job.org to hit /run-checks?secret=ALERT_SECRET daily",
                "Test full alert email flow with live data (quota resets June 1)",
                "Fix skyid_cache.json persistence on Render (ephemeral — wipes on redeploy)",
                "Swap SQLite → Postgres on Render (accounts wipe on redeploy until done)",
                "Flask-Limiter on /auth/login and /auth/register (5/min per IP)",
                "Password reset flow",
                "Custom 404/500 error pages",
                "Input validation on origin/destination fields",
                "Update footer — still says Amadeus API coming soon",
                "Round trip toggle",
            ],
            "api_quota_note": "Sky Scrapper RapidAPI free tier = 20 req/month hard limit. Quota resets June 1. Mock fallback covers demos until then.",
            "portfolio_role": "Second agentic project — travel-planning agent applying agentic loop pattern to a new domain. Demonstrates: REST API integration, graceful degradation, persistent user data, email automation, scheduled background jobs.",
        },
    ],
    "created": "April 23, 2026",
}

# ─────────────────────────────────────────────────────────────
# JOB SEARCH SYSTEM - UPDATED May 20, 2026
# ─────────────────────────────────────────────────────────────
JOB_SEARCH_SYSTEM = {
    "script": "job_search.py",
    "location": "C:/Users/haric/Jobsearch/",
    "language": "Python",
    "sources": 7,
    "source_list": [
        "RemoteOK", "Remotive", "Google Jobs (Serper)", "Adzuna",
        "USAJobs", "Wellfound", "Amazon Jobs Spotlight"
    ],
    "source_changes_2026_05_20": [
        "Added Remotive API (free, no key, software-dev category)",
        "Narrowed Adzuna to LoadRunner-only queries (5 instead of 10)",
        "Added Glassdoor SRCH_IL filter (kills aggregator search pages)",
        "Added 14 new Serper queries (Himalayas + BuiltIn site-targets, AI-lane: AI QA, LLM eval, AI reliability, AI SDET, AI observability)",
        "Bumped daily cap from Top 10 to Top 15",
        "Added dual K-Means thresholds: 100 exploratory + 300 production",
    ],
    "removed_sources": [
        "Google Custom Search API (removed 2026-05-07 — 403 on every query, redundant with Serper)",
        "JSearch (added 2026-05-07, dormant — no JSEARCH_API_KEY in .env; skipped every run)",
    ],
    "dead_sources_removed": [
        "Indeed RSS (shut down 2024)",
        "LinkedIn RSS (shut down 2023)",
        "Jooble (premium pay wall - replaced with Serper)",
        "WeWorkRemotely (non-English listings)",
        "Jobicy (low quality)", "SimplyHired (aggregator)",
        "ZipRecruiter (search pages only)", "Ashby (function broken)",
        "Jobvite (function broken)", "Glassdoor (function broken)",
        "ClearanceJobs (function broken)", "Arc.dev (category pages only)",
        "Greenhouse direct (403 blocks — now targeted via Serper site: instead)",
        "Lever direct (403 blocks — now via Serper site:)",
        "Dice direct (403 blocks — now via Serper site:)",
        "pitchmeai, Data Annotation, JobLeads, Arbeitnow (low signal)",
    ],
    "schedule": "Daily at 12:00 PM via Windows Task Scheduler",
    "midnight_update": "Daily at 12:00 AM via Windows Task Scheduler (update_scoring.py)",
    "amazon_jobs_spotlight": {
        "function":        "search_amazon_jobs()",
        "source":          "amazon.jobs via Serper site: targeting",
        "max_results":     5,
        "freshness_days":  10,
        "numbering":       "A1-A5 (separate from regular 1-15)",
        "min_score":       15,
        "email_section":   "Amazon Jobs Spotlight — orange branded section below top 15",
        "decision_loop":   "Fully integrated — submit A1-A5 via same Google Form",
        "internal_reminder": "Link to internal.amazon.jobs in every email",
        "non_us_filter":   "_is_non_us_amazon_posting() catches Toronto, Luxembourg, etc.",
    },
    "email_notifications": "harichardson68@gmail.com",
    "freshness_filter": "5 days (120 hours) for regular jobs, 10 days for Amazon",
    "max_jobs_per_email": 15,
    "duplicate_tracking": "seen_jobs.json - never sends same job twice",
    "cover_letters": "AI-generated via Claude API (claude-sonnet-4-6, prompt engineering agent)",
    "api_keys_location": ".env file (never committed to Git)",
    "job_tracks": [
        "Performance Engineering (LoadRunner focus - Senior OK only if LR mentioned)",
        "AI Engineering (entry to mid - Senior EXCLUDED - min 40 pts)",
        "COBOL/Mainframe (last resort - min 10 pts)"
    ],
    "scoring": {
        "loadrunner_in_title": 50,
        "loadrunner_in_description": 50,
        "performance_keywords": 35,
        "ai_title_keywords": 20,
        "qa_performance_hybrid": 20,
        "ai_description_keywords": 20,
        "bonus_keyword": 3,
        "cobol_title": 2,
        "cobol_description": 2,
    },
    "min_scores": {
        "Performance Engineering": 30,
        "AI Engineering": 40,
        "COBOL/Mainframe": 10,
    },
    "decision_feedback_system": {
        "form": "Hans Job Search Decisions (Google Forms)",
        "form_url": "https://docs.google.com/forms/d/1gLcCAhFvOpDWFgCGbu1r9Xubl9o7RVGQbyHwWYJPHIw/viewform",
        "sheet_id": "1nv9XmVWJUvJ08t6ldjJFYhZ25MfTLhUAAph3CrSzlmE",
        "form_validation_regex": "^([1-9]|1[0-5]|A[1-5])$",
        "form_validation_note": "Updated 2026-05-20 from 1-10 to 1-15 to support Top 15 daily cap",
        "decisions": [
            "Applied", "Bad Link", "Onsite / Not Remote", "Too Senior",
            "Salary Too Low", "Not Interested", "Already Seen / Duplicate",
            "Search Page Listing", "Not in United States", "Other"
        ],
        "two_script_architecture": {
            "note": "Two scripts both read the Google Sheet; their unique roles differ.",
            "update_scoring.py": {
                "schedule": "Daily 12:00 AM via Task Scheduler",
                "primary_role": "AUTO-PATCH job_search.py source code based on feedback",
                "sequence": [
                    "1. git pull",
                    "2. Read Google Sheet (all dates)",
                    "3. Write today's entries to job_decisions.json",
                    "4. Regex-patch job_search.py:",
                    "   - Append new locations to NON_US_LOCATIONS array",
                    "   - Append new sites to BLOCKED_JOB_SITES array",
                    "   - Append new companies to blocked_companies array",
                    "5. Update scoring_weights.json",
                    "6. Write overnight_summary.json (shown in next day's email)",
                    "7. git commit + push",
                ],
                "auto_handled_patterns": [
                    "Applied → boost matched keywords in scoring_weights.json",
                    "Bad Link → auto-block domain in BLOCKED_JOB_SITES",
                    "Not in United States + reason → auto-add to NON_US_LOCATIONS",
                    "Other + 'bad location - X' → auto-add X to NON_US_LOCATIONS",
                    "Other + 'bad company - X' → auto-add X to blocked_companies",
                ],
                "deprecated_path": "write_needs_review() function still exists but needs_review.json was deleted; if no 'other' regex match fires, the function silently regenerates orphan file. Slated for surgical removal a different evening.",
            },
            "review_decisions.py": {
                "schedule": "Mon + Thu 10:00 AM via Task Scheduler",
                "primary_role": "Surface unreviewed 'Other' decisions for pattern recognition",
                "sequence": [
                    "1. git pull",
                    "2. Sync Google Form responses → job_decisions.json (matches by date+job_number)",
                    "3. Filter: decision == 'other' AND reviewed != true",
                    "4. Group by REASON_CATEGORY_MAP (clearance/onsite/jmeter_only/etc.)",
                    "5. Send HTML digest grouped by category",
                    "6. Mark each surfaced entry reviewed:true + reviewed_date",
                    "7. git commit + push",
                ],
                "renamed_from": "weekly_review.py (renamed 2026-04-30, frequency changed Mon→Mon+Thu)",
                "replaces": "needs_review.json file (deleted; review state now lives inside job_decisions.json via reviewed: true flag)",
                "supports_amazon": "Yes — normalise_job_number() handles both 1-15 and A1-A5",
            },
        },
    },
}

# ─────────────────────────────────────────────────────────────
# EVAN'S JOB SEARCH SYSTEM - UPDATED April 23, 2026
# ─────────────────────────────────────────────────────────────
EVAN_JOB_SEARCH_SYSTEM = {
    "script": "evan_job_search.py",
    "location": "C:/Users/haric/Evan Jobsearch/",
    "language": "Python",
    "purpose": "Automated cybersecurity job search for son Evan Richardson",
    "evan_profile": {
        "name": "Evan A. Richardson",
        "email": "evanrichardson03@gmail.com",
        "location": "Lee's Summit, MO",
        "education": "B.S. Cybersecurity: Cyber Operations, UCM 2025 - 4.0 GPA, ABET-accredited",
        "certifications": "Security+, AWS, Public Trust clearance (DHS/USCIS)",
        "hobbies": "CTF, Hack The Box, Taekwondo Black Belt",
    },
    "sources": 8,
    "source_list": [
        "RemoteOK", "Google Jobs (Serper)", "USAJobs", "Greenhouse",
        "Lever", "Google Custom Search", "Dice", "Wellfound"
    ],
    "target_tracks": [
        "SOC Analyst", "Cybersecurity Analyst", "MDR Analyst",
        "Vulnerability Management", "Incident Response / DFIR",
        "Junior Penetration Tester", "Security Internship"
    ],
    "markets": "Remote (US only) + KC Metro hybrid/onsite",
    "schedule": "Daily at 1:00 PM via Windows Task Scheduler",
    "midnight_update": "Daily at 12:30 AM via Windows Task Scheduler (update_scoring_evan.py)",
    "freshness_filter": "72 hours (3 days)",
    "max_jobs_per_email": 10,
    "cover_letters": "AI-generated via Claude API",
    "target_email": "evanrichardson03@gmail.com",
    "decision_feedback_system": {
        "form": "Evan Job Search Decisions (Google Forms)",
        "form_url": "https://docs.google.com/forms/d/14_Jt5xRxZsjo3KgHM4V4wUuhGQ_soPQk8vFw8cVT9ds/viewform",
        "sheet_id": "16NA3xPpvdV3nh1-FdWsfjGxCZ0OnvvmBAg6P2PQaaJs",
        "midnight_script": "update_scoring_evan.py",
    },
    "known_issues": [
        "USAJobs: federal titles non-standard (IT Specialist vs SOC Analyst)",
        "The Muse: removed - API returning 0 for Entry Level IT category",
    ],
}

# ─────────────────────────────────────────────────────────────
# TASK SCHEDULER - ALL TASKS
# ─────────────────────────────────────────────────────────────
TASK_SCHEDULER = {
    "Hans_noon":     {"task": "JobSearch_Scheduler",    "time": "12:00 PM", "script": "job_search.py"},
    "Evan_noon":     {"task": "EvanJobSearch",          "time": "1:00 PM",  "script": "evan_job_search.py"},
    "Hans_midnight": {"task": "HansJobSearchUpdate",    "time": "12:00 AM", "script": "update_scoring.py"},
    "Evan_midnight": {"task": "EvanJobSearch_Update",   "time": "12:30 AM", "script": "update_scoring_evan.py"},
}

# ─────────────────────────────────────────────────────────────
# GOOGLE INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────
GOOGLE_INFRASTRUCTURE = {
    "project": "My Project 67638 (optimum-habitat-304315)",
    "service_account": "job-search-reader@optimum-habitat-304315.iam.gserviceaccount.com",
    "credentials_file": "google_credentials.json (in both job search folders, never committed to Git)",
    "apis_enabled": ["Google Sheets API"],  # Google Custom Search API removed 2026-05-07
    "hans_sheet": "Job Search Decisions - https://docs.google.com/spreadsheets/d/1nv9XmVWJUvJ08t6ldjJFYhZ25MfTLhUAAph3CrSzlmE",
    "evan_sheet": "Job Search Decisions (Evan) - https://docs.google.com/spreadsheets/d/16NA3xPpvdV3nh1-FdWsfjGxCZ0OnvvmBAg6P2PQaaJs",
}

AGENT_HUB = {
    "file": "agent_hub.py",
    "location": "C:/Users/haric/Jobsearch/",
    "language": "Python",
    "powered_by": "Claude API (claude-sonnet-4-6)",
    "tabs": [
        {"name": "Claudio - Job Search Agent", "purpose": "Review jobs, cover letters, run searches"},
        {"name": "PyCoach - Python Tutor", "purpose": "Learn Python in performance engineering context"},
        {"name": "AImentor - AI Study Coach", "purpose": "Study AI/ML concepts, interview prep"},
        {"name": "JMentor - LR to JMeter", "purpose": "Translate LoadRunner expertise to JMeter"},
        {"name": "ATSmax - Resume Scorer", "purpose": "Score resume against job postings"},
    ],
}

# ─────────────────────────────────────────────────────────────
# RESUME STATUS
# ─────────────────────────────────────────────────────────────
RESUME = {
    "file": "Hans-Richardson-Performance_AI_Engineer.docx (+ PDF version)",
    "pages": 3,
    "last_updated": "June 12, 2026",
    "ats_score": "91%+",
    "june_2026_update": "Reworked to feature job-agent (agentic loop) as flagship. Summary leads with 'building production AI agents + reliability/observability mindset'. Projects section rewritten around the loop/registry/observability/eval layer. Certs regrouped (AI/ML, Performance, Cloud & Foundations) with IBM track as umbrella. Plain human voice, no buzzword salad. Both .docx and .pdf generated.",
    "two_versions_note": "Current version leans AI. A LoadRunner-leading variant may be worth making for performance-track applications.",
}

# ─────────────────────────────────────────────────────────────
# AI COURSES COMPLETED
# ─────────────────────────────────────────────────────────────
COURSES_COMPLETED = [
    "Introduction to Artificial Intelligence (AI) - Coursera",
    "Generative AI: Introduction and Applications - Coursera",
    "Generative AI: Prompt Engineering Basics - Coursera",
    "Python for Data Science, AI & Development - Coursera",
    "Master JMeter on Live Apps Performance Testing - Coursera 2025",
    "Introduction to Selenium - Coursera 2025",
    "Ultimate AWS Certified Cloud Practitioner - Udemy 2025",
    "AI Engineer Course: Complete AI Engineer Bootcamp - Udemy 2025",
    "HP LoadRunner Training - HP 2010",
    "API Performance Testing SOAP/REST - Udemy 2023",
]

COURSES_IN_PROGRESS = [
    "IBM Generative AI Engineering Professional Certificate - Coursera (in progress)",
    "Pathstream Amazon Operations Leadership Certificate - Career Choice (May-September 2026, free via Amazon Career Choice — parallel hedge while AI engineering pivot and IT contract search continue)",
]

# ─────────────────────────────────────────────────────────────
# IBM AI ENGINEERING COURSE PROGRESS
# ─────────────────────────────────────────────────────────────
IBM_COURSE_PROGRESS = {
    "course": "IBM Generative AI Engineering Professional Certificate",
    "modules_completed": [
        {
            "module": "Regression Models",
            "status": "COMPLETED March 29, 2026",
            "topics_mastered": [
                "Simple Linear Regression", "Multiple Linear Regression",
                "Polynomial Regression", "Logistic Regression (binary classification)",
                "Logarithmic Regression (diminishing returns)",
                "OLS - minimizes MSE", "Cost function and log-loss",
                "Overfitting vs Underfitting", "Feature Engineering",
                "Model Validation - 80/20 split", "Threshold probability",
                "Weights, Normalization, Boolean", "Random Forest",
            ]
        }
    ],
    "modules_next": [
        "Building Supervised Learning Models",
        "Unsupervised Learning (K-Means — RELEVANT NOW: your job_decisions.json hits 100-record exploratory milestone soon)",
        "Neural Networks and Deep Learning",
        "Generative AI and LLMs",
    ],
    "key_insights": [
        "Supervised = labeled data, Unsupervised = unlabeled data",
        "Performance testing IS model training - same iterative process!",
        "Threshold = SLA target (24+ years of experience applies!)",
        "MLOps/AI Test Engineer roles are realistic targets for Hans",
        "Performance testing background is a COMPETITIVE ADVANTAGE in AI",
        "Exploratory K-Means at 100 records = data audit before committing to 300; matches the smoke-test-before-load-test pattern from performance engineering",
    ]
}

# ─────────────────────────────────────────────────────────────
# AI ENGINEERING SKILLS - HANDS ON
# ─────────────────────────────────────────────────────────────
AI_SKILLS_HANDS_ON = {
    "Claude API": {"level": "Practical", "evidence": "Agent hub, cover letters, job search systems, autonomous midnight update pipeline", "date": "April 23, 2026"},
    "Prompt Engineering": {"level": "Practical", "evidence": "Job analysis agent, MLOps-specific prompts, cybersecurity cover letters, cover letter generator", "date": "April 23, 2026"},
    "Multi-Agent Architecture": {"level": "Practical", "evidence": "5-tab Agent Hub", "date": "March 29, 2026"},
    "REST API Integration": {"level": "Practical", "evidence": "6 job board APIs, Serper, Adzuna, USAJobs, Gmail SMTP, Google Sheets API, Google Custom Search", "date": "April 23, 2026"},
    "Python Automation": {"level": "Practical - Growing", "evidence": "job_search.py + evan_job_search.py + update_scoring.py - all production systems running daily", "date": "April 23, 2026"},
    "Agentic Systems (TRUE agentic loop)": {"level": "Practical - Strong", "evidence": "job-agent: Claude as decision-maker in observe-plan-act loop, tool registry, planner, streaming reasoning traces, 2-layer dedup, LLM fit-tiering. Ran live with unprompted query/track pivots. THIS is the real thing, not just a feedback loop.", "date": "June 12, 2026"},
    "LLM Tool-Use / Orchestration": {"level": "Practical", "evidence": "job-agent registry pattern — one dict generates planner menu + function lookup; planner returns structured JSON tool calls Claude chooses each iteration", "date": "June 12, 2026"},
    "AI Evaluation / Fit-Scoring": {"level": "Practical", "evidence": "analyze_fit.py — LLM tiers each match Excellent->Weak with honest single-gap callout; track-aware seniority capping; the perf-engineer eval crossover", "date": "June 12, 2026"},
    "Reasoning-Trace Observability": {"level": "Practical", "evidence": "logger.py — THINK/ACT/SEE trace streamed live + saved per run; the trace IS the portfolio artifact", "date": "June 12, 2026"},
    "Agentic Systems (legacy feedback loop)": {"level": "Practical", "evidence": "Self-improving loop: email -> Google Form -> Google Sheets -> midnight script -> auto-patches job_search.py -> git commit", "date": "April 23, 2026"},
    "Git / GitHub": {"level": "Practical", "evidence": "Two public repos with portfolio-grade READMEs, automated nightly commits from update scripts", "date": "April 23, 2026"},
    "RAG / Vector Search": {"level": "Practical", "evidence": "ChromaDB + sentence-transformers (all-MiniLM-L6-v2) wired into job_search.py — 92 decisions ingested, chroma_db folder live on disk", "date": "May 07, 2026"},
    "ChromaDB": {"level": "Practical", "evidence": "Local persistent vector store, upsert/query pipeline built and running nightly", "date": "May 07, 2026"},
    "K-Means (in progress)": {"level": "Conceptual + Implementation planned", "evidence": "71/100 exploratory decisions (71%), 71/300 production decisions (24%) after 2026-05-20 stub cleanup. Dual-threshold architecture: exploratory milestone at 100 (audit if data has clustering signal), production milestone at 300 (train supervised classifier to auto-skip predicted-rejects). analyze_decisions.py to be drafted near 80 records.", "date": "May 20, 2026"},
    "Google Sheets API": {"level": "Practical", "evidence": "Service account auth, reads form submissions to drive autonomous scoring updates", "date": "April 23, 2026"},
    "Debugging & Troubleshooting": {"level": "Practical", "evidence": "Fixed dead APIs, date parsing, email crashes, location filtering, score inflation, secret scanning blocks", "date": "April 23, 2026"},
    "Linear/Logistic Regression": {"level": "Conceptual + IBM Course", "evidence": "Completed regression module", "date": "March 29, 2026"},
    "Classification & Decision Trees": {"level": "Conceptual + IBM Course", "evidence": "OvO/OvA strategy, pruning, node concepts, information gain, midpoints method — quiz passed", "date": "April 19, 2026"},
    "SVM / Support Vector Machines": {"level": "Conceptual + IBM Course", "evidence": "Hyperplane, margin maximization, soft margin, C parameter, kerneling, epsilon — quiz passed", "date": "April 19, 2026"},
    "K-Nearest Neighbors": {"level": "Conceptual + IBM Course", "evidence": "Lazy learning, feature vs label distinction, feature scaling, K hyperparameter tuning — quiz passed", "date": "April 19, 2026"},
    "Random Forests": {"level": "Conceptual", "evidence": "Ensemble learning, bagging, feature importance, out-of-bag error", "date": "April 19, 2026"},
    "Filter Pipeline Design": {"level": "Practical", "evidence": "Built 15+ filter stages for job quality control across 2 scripts", "date": "April 23, 2026"},
    "Weighted Scoring / Classification": {"level": "Practical", "evidence": "Multi-track scoring algorithm with per-track thresholds — essentially a hand-coded classifier", "date": "April 23, 2026"},
}

# ─────────────────────────────────────────────────────────────
# PERFORMANCE ENGINEERING → AI/ML VOCABULARY TRANSLATION
# ─────────────────────────────────────────────────────────────
PERF_TO_AI_VOCABULARY = {
    "Tuning LoadRunner thresholds":         "Hyperparameter optimization",
    "Iterative script tuning until stable": "Gradient descent / iterative optimization",
    "Adjusting think times and pacing":     "Model parameter tuning",
    "Correlation and parameterization":     "Feature extraction and transformation",
    "Filtering bad/noisy test results":     "Data cleaning / preprocessing",
    "Workload modeling":                    "Data distribution modeling / sampling",
    "Baseline vs load test comparison":     "Model validation / benchmarking",
    "Identifying outlier transactions":     "Anomaly detection",
    "Deduplication of results":             "Data normalization / deduplication",
    "Categorizing jobs by track":           "Multi-class classification",
    "Scoring jobs by keyword weight":       "Feature weighting / scoring model",
    "Blocking bad job sites":               "Pruning / noise reduction",
    "Title/description filtering":          "Natural language feature extraction",
    "Monitoring with Splunk/AppDynamics":   "ML observability / model monitoring",
    "SLA compliance targets":               "Decision boundaries / acceptance thresholds",
    "Root cause analysis of bottlenecks":   "Root cause analysis / anomaly attribution",
    "Throughput and latency measurement":   "Model inference performance metrics",
    "End-to-end transaction validation":    "Pipeline integrity testing",
    "Multi-protocol VuGen scripting":       "Multi-modal data pipeline development",
    "Scalability testing":                  "Model scalability / load testing AI endpoints",
    "SLA enforcement under load":           "Production ML SLA compliance",
    "AWS/Kubernetes performance testing":   "Cloud-native AI infrastructure testing",
    "Job search scoring algorithm":         "Weighted classification model",
    "Multi-source job aggregation":         "Data pipeline / ETL with filtering",
    "Cover letter prompt engineering":      "Prompt engineering / LLM output optimization",
    "Agent Hub with Claude API":            "Multi-agent architecture / agentic AI",
    "API rate limit handling":              "Distributed systems / resilience engineering",
    "Seen jobs deduplication":              "State management / data persistence",
    "Human feedback loop via Google Forms": "RLHF - Reinforcement Learning from Human Feedback",
    "Auto-patching job_search.py at midnight": "Self-improving agentic system / autonomous code evolution",
    "Git commit history of scoring changes": "Audit trail / model versioning",
}

INTERVIEW_TALKING_POINTS = [
    # ── job-agent stories (June 2026) — lead with these, they're the strongest ──
    {
        "question": "Tell me about the most interesting thing you've built with AI / What's a real agentic system you've built?",
        "answer": """I built an autonomous agentic job search where Claude — not a fixed
script — decides each action in an observe-plan-act loop. Each iteration the planner sends Claude
the goal, a summary of what's happened, and a menu of tools; Claude returns a structured decision
about which tool to call and why. The loop runs it, folds the result into state, logs the reasoning,
and repeats until Claude decides it has enough. The key difference from a normal pipeline: it ADAPTS.
In a live run it searched LoadRunner roles, got nothing, and pivoted to broader performance queries
on its own — a fixed pipeline would've just returned zero. The architecture is a tool registry that's
the single source of truth (one dict generates both the planner's menu and the function lookup, so
adding a tool is one entry), a forced-JSON planner that fails safe to 'stop' on any error, and a
streaming THINK/ACT/SEE reasoning trace that's the real observability artifact."""
    },
    {
        "question": "Tell me about a hard technical problem you debugged",
        "answer": """My agent's Adzuna search kept returning zero results while another source
returned plenty for the same query. I diagnosed it methodically — confirmed the API was healthy and
keys were valid, then inspected the actual requests. Root cause: Adzuna AND-matches every word in the
query against the job's body text, and the planner was appending 'remote' — but remote postings rarely
write 'remote' in the description, they put it in location metadata. So 'loadrunner remote' required
both words present and matched almost nothing. The fix was a layered one: strip location words from the
query before the API call AND steer the planner away from adding them — because location belongs in a
separate filter, not the search text. It's the kind of bug where the obvious answer (bad keys, rate
limit) is wrong and you have to actually read what the system is doing."""
    },
    {
        "question": "Tell me about a time you caught a mistake before it caused damage / How do you think about AI safety in practice?",
        "answer": """While fixing deduplication in my agent, the proposed fix passed the obvious
test — it correctly merged two postings of the same job. But I caught that it would also FALSE-merge
genuinely different roles: a generic 'AI Engineer' would collapse into 'Senior AI Platform Engineer'
because one title's words were a subset of the other. A false merge silently loses a real job — worse
than a duplicate. I tightened it to require a 75% word-overlap ratio, which catches the real duplicate
but keeps distinct roles separate, and verified it against both cases. More broadly, I deliberately did
NOT build self-modifying logic into the agent — it could rewrite its own scoring from patterns in past
decisions, but unsupervised self-modification is hard to debug and prone to silent drift. I kept a
human approving each change with a full audit trail. Knowing when NOT to automate is part of the
engineering."""
    },
    {
        "question": "How does your performance engineering background apply to AI?",
        "answer": """Directly — AI systems are non-deterministic systems that need to prove they
hold up, which is exactly what I've done for 14 years. My agent has a full observability layer:
streaming reasoning traces, per-run logs, latency and cost awareness — that's performance-engineering
instinct applied to LLM systems. The evaluation layer (tiered fit-scoring, honest gap analysis, the
discipline of asking 'does this actually hold up' instead of trusting the happy path) is eval thinking
I've done my whole career. I even built a dev/prod 'test mode' that swaps to a cheaper model and trims
the loop so I could iterate cheaply and reserve full-cost runs for verification — measure cheap, spend
deliberately. My observability stack (AppDynamics, Splunk, Grafana, Prometheus) maps straight to ML/LLM
monitoring. I bring reliability and eval discipline most people pivoting into AI simply don't have."""
    },
    {
        "question": "How do you work / what's your engineering process?",
        "answer": """For the agent I used a two-tool workflow: I acted as architect and PM —
making design decisions, holding the big-picture context, catching judgment calls — while using an
agentic coding CLI (Claude Code) as the file-level executor. The interesting part is the division of
labor: the executor is fast and good at finding bugs, but it makes locally-reasonable mistakes that
miss broader context. I caught several before they shipped — the false-merge dedup fix, an over-rated
job fit score — by reviewing its output against the design intent before committing. That's the same
discipline as code review, and it's how a lot of AI-augmented engineering actually works now: the human
holds judgment and architecture, the tool does the labor."""
    },
    # ── earlier talking points (pre-job-agent) ──
    {
        "question": "Tell me about your broader AI engineering portfolio",
        "answer": """Beyond the agentic system, I built a production deterministic job-search
pipeline (Python + Claude API) that aggregates 7-8 sources daily, scores with a multi-track weighted
classifier, generates AI cover letters, and emails a digest — with a human-in-the-loop feedback system
via Google Forms feeding a nightly script that auto-patches filter logic and commits to GitHub. I also
built a 5-assistant desktop hub (Agent Hub) on the Claude API, and FLAPBOARD, a live Flask app with
real flight pricing and price-drop email alerts. The agentic loop is the centerpiece; these show range."""
    },
    {
        "question": "How does your performance testing background apply to AI? (short version)",
        "answer": """Testing AI inference endpoints is the same as load testing web services.
My observability stack maps directly to ML monitoring, and iterative model tuning is the same loop I've
run for 24+ years in performance engineering. I bring expertise most AI engineers don't have."""
    },
    {
        "question": "Do you have startup experience?",
        "answer": """I run a side business (H&G Lighting) giving me direct early-stage exposure.
My AI work is self-directed and entrepreneurial — I designed, built, and deployed production-grade
autonomous systems solo, without a team or infrastructure, which mirrors the scrappy, figure-it-out
culture of early-stage startups."""
    },
]

# ─────────────────────────────────────────────────────────────
# TARGET COMPANIES TO WATCH
# ─────────────────────────────────────────────────────────────
TARGET_COMPANIES = [
    {
        "name": "Elios Talent",
        "why": "Legit US staffing firm, Houston TX, PE-backed, Technology & AI specialty",
        "action": "Monitor LinkedIn for AI QA Engineer postings",
    }
]

# ─────────────────────────────────────────────────────────────
# PERFORMANCE TESTING CREDENTIALS
# ─────────────────────────────────────────────────────────────
PERFORMANCE_CREDENTIALS = {
    "LoadRunner": "14 years expert - VuGen, LRE, scripting, correlation, C language",
    "JMeter": "Trained - Coursera 2025, building proficiency",
    "NeoLoad": "Trained - building proficiency",
    "Selenium": "Introduction course completed",
    "Protocols": "Web HTTP/HTML, TruClient, REST, SAP Web/GUI, Citrix",
    "Monitoring": "AppDynamics, Splunk, Grafana, Prometheus, SiteScope, AWS X-Ray",
    "Cloud": "AWS, Kubernetes",
    "Federal": "USDA 2021-2025, Public Trust clearance",
    "Telecom": "Sprint/CenturyLink 1999-2017, 18 years",
    "Authentication": "LDAP, SAML, SSO troubleshooting experience"
}

# ─────────────────────────────────────────────────────────────
# SESSION NOTES
# ─────────────────────────────────────────────────────────────
SESSION_NOTES = [
    {
        "date": "June 6-12, 2026",
        "title": "BUILT job-agent — the agentic loop (AI portfolio centerpiece)",
        "summary": "Designed and built a complete autonomous agentic job search from scratch, in a new separate repo, distinct from the job_search.py pipeline. Claude makes each decision in an observe-plan-act loop. Built with Claude.ai as architect/PM + Claude Code (CLI) as executor.",
        "what_got_built": [
            "core/state.py (spine), core/logger.py (THINK/ACT/SEE trace), core/planner.py (Claude picks next tool, forced JSON, fail-safe)",
            "tools/registry.py (ONE dict -> menu + function lookup), search.py (Adzuna+Serper, classify_location), score.py (2-layer dedup + tiered scoring), analyze_fit.py (LLM tiers + gap-flagging), cover_letter.py, email_results.py",
            "config/: goals.py, salary_config.py (LR $110k/$55hr HARD floor, AI $90k/$45hr SOFT floor), watch_vectors.py (OPM/Oracle Federal HR 2.0 $395.8M contract intel as first vector)",
            "agent.py loop wired into Agent Hub 'Run Agent' button — streams real trace into Claudio's window",
            "TEST MODE toggle: Haiku planner + 4-iter cap + skip fit for cheap dev iteration (default OFF = full Sonnet/prod)",
        ],
        "real_bugs_debugged": [
            "Adzuna returned 0: it AND-matches every query word vs body text, so 'loadrunner remote' = 0. Fixed: strip location words before sending + registry steer. 'remote' belongs in classify_location, not the query.",
            "Serper company-parsing: put 'ONLY W2' as a company. Fixed parser to strip employment-type junk, empty-string fallback not 'N/A'.",
            "Dedup false-merge risk: first fix (word-subset) would merge 'AI Engineer' into 'Senior AI Platform Engineer'. Caught it before commit. Final: company-gated + 75% title-ratio.",
            "Track-aware AI seniority: 'senior' is GOOD on LoadRunner track, BAD on AI track. Drops Staff/Principal/Lead AI, lets borderline Senior AI through to fit analysis.",
        ],
        "key_lessons": [
            "Agentic = Claude decides the SEQUENCE; hardcoded scoring is correct (policy, not intelligence). Intelligence in decisions, consistency in policies.",
            "Human-in-the-loop by deliberate choice — parked unsupervised self-modification (Option 3). Knowing NOT to build it is the senior judgment.",
            "Two-tool workflow: Claude.ai = architect (context, judgment, catches false-merges), Claude Code = executor (file-level, fast). Caught multiple judgment errors by reviewing Claude Code output before commit.",
            "Cross-source dedup logic proven but rarely WITNESSED (Adzuna returns so little it rarely overlaps Serper). Across-run dedup fires reliably (seen-before N).",
        ],
        "shipped": "Pushed public to github.com/harichardson68/job-agent June 12 with portfolio-grade README. Resume reworked to feature it. .env/.claude/last_run.json/cl_debug.txt correctly gitignored.",
        "next": [
            "Remote/headless execution (cloud-triggered, emails results) — run_agent() is already GUI-independent",
            "Outcome-driven LEARNING LOOP: logged decisions feed scoring refinements a HUMAN approves (the K-Means/pattern-recognition idea, matured — pattern engine vs the propose-approve loop are decoupled, don't gate one on the other)",
            "Liveness check on top picks (FlairTech-type: live-looking snippet, dead page — only a fetch catches it)",
            "AWS Bedrock + Lambda = the clear next SKILL target (job postings for agentic-platform roles in Hans's niche all want it)",
            "Possible LoadRunner-leading resume variant for performance-track apps",
        ],
    },
    {
        "date": "May 29, 2026",
        "accomplishments": [
            # FLAPBOARD — Sky Scrapper API integration
            "Investigated Kiwi Tequila API — discovered invitation-only lockdown (no new registrations)",
            "Investigated Amadeus self-service — discovered decommissioning July 17, 2026",
            "Selected Sky Scrapper API on RapidAPI (free tier, 20 req/month) as replacement",
            "Built skyscrapper_flights.py — full Sky Scrapper integration with:",
            "  - SkyId caching (skyid_cache.json) — each airport costs 1 API call ever",
            "  - 30 pre-seeded US airports (seeds turned out to have wrong entityIds — removed)",
            "  - Realistic mock fallback seeded by route (consistent prices, not random)",
            "  - is_live flag — True=real Skyscanner data, False=mock fallback",
            "  - Graceful degradation — falls back silently on any API failure",
            "  - Windows-compatible strftime (_fmt_dt helper — no %-d or %-I)",
            "Debugged SkyId field mapping — API returns skyId/entityId nested under navigation.relevantFlightParams not top level",
            "Hit 429 Too Many Requests during debugging — exhausted 20 free calls for May",
            "Mock fallback confirmed working perfectly — MCI→LAX realistic prices + booking URLs",
            # FLAPBOARD — saved searches + alerts
            "Added SavedSearch model to models.py (user_id, origin, destination, depart_date, return_date, adults, alert_threshold, last_price, last_checked, created_at)",
            "Built alerts.py — SMTP email alerts reusing job_search.py pattern, HTML styled in amber/navy FLAPBOARD theme",
            "Added /save-search POST route — saves with duplicate check",
            "Added /delete-search/<int:search_id> POST route — first_or_404 + user ownership check",
            "Added /run-checks GET route — protected by ALERT_SECRET env var, ready for cron-job.org",
            "Updated results.html — new field names (airline_code, airline, depart_at, arrive_at, duration_h, duration_m), live/mock banner, Book/Search button with Skyscanner deep link, Save Search panel",
            # FLAPBOARD — dashboard redesign
            "Rebuilt dashboard.html — matching Render aesthetic: / where to? heading, centered card layout",
            "Replaced simple Lookup button with full airport lookup modal:",
            "  - 70 US airports, type city name OR IATA code",
            "  - Instant filter as you type, click to select",
            "  - Closes on Escape or overlay click",
            "  - Zero API calls — pure client-side JS",
            "Fixed date picker visibility — color-scheme: dark + filter: brightness(0) invert(1)",
            # Flask setup
            "Wired Flask-Migrate into __init__.py (migrate = Migrate(), migrate.init_app(app, db))",
            "Fixed Alembic not detecting SavedSearch — added from app import models in env.py and __init__.py",
            "Used db.create_all() direct approach to create saved_search table (bypassed Alembic)",
            "pip install requests flask-migrate python-dotenv in venv",
            "pip freeze > requirements.txt — fixed Render ModuleNotFoundError: flask_migrate",
            # Deployment
            "Fixed duplicate flash messages — removed flash block from dashboard.html (base.html handles globally)",
            "All changes deployed to Render successfully",
            "Confirmed Save Search end-to-end: search → save → dashboard shows saved search with threshold badge",
            "Confirmed Delete working: ✕ button removes row with confirmation dialog",
        ],
        "concepts_learned": [
            "Flight pricing APIs in 2026 are in chaos — Kiwi locked down, Amadeus self-service shutting down July 2026",
            "RapidAPI free tiers often advertise 100/month but actual limit may be 20 — always check pricing page",
            "SkyId vs IATA — Skyscanner uses internal entity IDs nested under navigation.relevantFlightParams",
            "Windows strftime doesn't support %-d or %-I (Linux-only) — use .day and .lstrip('0') instead",
            "Flask-Migrate requires models to be imported before Alembic scans — add to env.py and __init__.py",
            "Render free tier has ephemeral storage — flat files (skyid_cache.json, SQLite) wipe on redeploy",
            "Graceful degradation pattern — is_live flag lets UI adapt without crashing",
            "Dynamic route /delete-search/<int:search_id> vs static /save-search — save doesn't need ID (DB assigns it), delete does",
            "color-scheme: dark makes browser date picker use dark theme; filter: brightness(0) invert(1) makes icon white",
        ],
        "next_session_priorities": [
            "1. June 1 — quota resets, test live Sky Scrapper pricing end-to-end",
            "2. Commit skyid_cache.json to GitHub after first successful live search",
            "3. Set up cron-job.org to hit /run-checks daily",
            "4. Set MAIL_PASSWORD in Render env vars (new Gmail app password created today)",
            "5. Fix footer — still says Amadeus API coming soon",
            "6. Flask-Limiter on /auth/login and /auth/register",
            "7. Password reset flow",
            "8. Swap SQLite → Postgres on Render",
        ],
        "flapboard_status": "Live at flapboard.onrender.com — mock pricing, saved searches, airport lookup modal all working",
    },
    {
        "date": "May 20, 2026",
        "accomplishments": [
            # Source expansion + filter improvements
            "Added Remotive API as new source (free, no key, software-dev category; 19 raw / 0 keepers on debut run — earning two-week trial)",
            "Narrowed Adzuna from 10 broad performance queries to 5 LoadRunner-only queries (was returning ~180 raw / 0 keepers/run)",
            "Added Glassdoor SRCH_IL searchpage pattern to URL filter (kills aggregator URLs like glassdoor.com/Job/*-jobs-SRCH_IL...)",
            "Added 4 new site-targeted Serper queries: himalayas.app, builtin.com/job (each targeting both LR and AI lanes)",
            "Added 10 new AI-lane Serper queries: AI QA, AI test, LLM evaluation, AI reliability, AI observability, LLM observability, AI SDET, AI workflow, ai eval, model evaluation",
            "Targeting rationale: AI-lane queries match performance-engineer-bridges-to-AI roles where 14-yr LoadRunner + observability stack is the actual moat",
            # Capacity bump
            "Bumped daily email cap from Top 10 to Top 15 to accelerate K-Means timeline (raw pool grew with new sources so the cap meant 5 keepers today vs ~3 morning baseline)",
            "Updated Google Form regex from ^([1-9]|10|A[1-5])$ to ^([1-9]|1[0-5]|A[1-5])$ to accept 1-15",
            # K-Means architecture: dual threshold
            "Added KMEANS_EXPLORATORY = 100 constant alongside KMEANS_THRESHOLD = 300",
            "Updated get_decision_stats() to return both pct and pct_expl",
            "Rewrote email K-Means tracker block to show two stacked progress bars (exploratory turns green at 100, production turns green at 300)",
            "Rationale: Catch dataset-quality problems early at 100 records (cheap fix) rather than 300 (expensive fix). Exploratory K-Means audits whether the features carry signal before grinding to production threshold.",
            # job_decisions.json cleanup (one-shot)
            "Built cleanup_backfilled_stubs.py — dry-run by default, --apply to delete, auto-creates timestamped backup before deletion",
            "Discovered 72 of 143 records (50%) were backfilled stubs from 4/24-5/05 window — empty job_id/url/score/matched_keywords because today_jobs_*.json archives didn't exist for those dates",
            "Deleted 72 stubs after dry-run verification. Decision count now 71 (real records only). Backup preserved at job_decisions.json.bak-cleanup-20260520_193836",
            "Confirmed gap: backfill archive issue was fixed between 5/05 and 5/09. After 5/09 every Amazon spotlight (A1-A5) and regular job has full metadata in archive files.",
            # Verified
            "First post-change run delivered 5 keepers + 1 Amazon spotlight (vs. 4+1 morning baseline)",
            "Top picks included AI Observability & Agent Engineering @ $230K base — proof of concept for AI-lane targeting (would not have surfaced without tonight's new queries)",
            "Pipeline funnel: 362 raw → 5 final, 1.4% survival rate. Biggest drop: recency filter at 194 jobs (54% of prior stage). After-score-filter only barely smaller than after-level-filter (70 vs 71) — level filter is the limiter, not score.",
            "Raw by source: Serper 227 / RemoteOK 99 / Remotive 16 / Wellfound 16 / USAJobs 4. Adzuna 0 (narrowed queries returned zero — expected and acceptable; 2-week trial).",
            # Documentation
            "Rewrote AI_Progress_Tracker.py — accurate as of 2026-05-20 (this update)",
            "Documented true two-script architecture: update_scoring.py owns auto-patching; review_decisions.py owns Mon+Thu 'other' digest",
        ],
        "concepts_learned": [
            "schema.org/JobPosting exists as a metadata standard but isn't enforced — job sites self-report 'remote' status and game it. That's why your filter pipeline is defense-in-depth rather than a single metadata check.",
            "Features (job metadata) vs labels (your form decision) — the form is the LABEL the K-Means/classifier predicts; the features come from the job's title/description/score/source/track that job_search.py already collects.",
            "Exploratory K-Means at 100 is a data audit, not a model — answers 'do the features carry signal?' If yes, keep collecting to 300 for a supervised classifier. If no, fix features (likely cheap: more derived columns from existing text).",
            "Worst-case audit outcome isn't 'lose 100 records' — it's 'add 4-5 derived feature columns and re-cluster'. Schema is sound; foundational restart unlikely.",
            "Regex character classes don't span numbers — [1-15] doesn't mean 1 through 15, it means '1', '1-1', or '4'. Multi-digit ranges need digit-position decomposition: 10-15 = 1[0-5]",
            "Remotive ToS requires attribution + link-back; personal email digest use is fine, third-party republishing isn't",
            "Adzuna and RemoteOK are broad-software-dev sources — they produce raw volume but rarely keep through tight LoadRunner/AI-lane filters. Their value is the occasional rare match, not consistent flow. Same evaluation rubric applies to Remotive going forward.",
            "stub records (no job_id, no metadata) pollute K-Means training data even if you count them toward thresholds; better to delete and let true count drive timeline honesty",
        ],
        "decisions_milestone": {
            "total_after_cleanup": 71,
            "exploratory_target":  100,
            "exploratory_pct":     71,
            "production_target":   300,
            "production_pct":      24,
            "removed_today":       72,
            "estimated_days_to_exploratory": "5-6 weeks at current 4-5 decisions/day pace",
        },
        "next_session_priorities": [
            "1. Monitor first week of post-change runs — watch Remotive keep rate, AI-lane query keep rate, Adzuna (likely still zero)",
            "2. Update README.md on GitHub to match this tracker (currently still references Remotive removed, 7 sources, Top 10, single K-Means threshold)",
            "3. Surgical cleanup of update_scoring.py — remove write_needs_review() / NEEDS_REVIEW_FILE references so it cannot regenerate orphan file (different evening; touches nightly Task Scheduler script)",
            "4. Consider archiving backfill_decisions.py and cleanup_backfilled_stubs.py to an archive/ folder (one-shots, completed)",
            "5. Draft analyze_decisions.py skeleton when decision count hits ~80 (currently 71, ~9 records away)",
            "6. Continue IBM course — Unsupervised Learning module (K-Means specifically — relevant timing)",
        ],
    },
    {
        "date": "April 24, 2026",
        "accomplishments": [
            # Morning verification
            "Verified overnight system worked correctly — job_decisions.json, scoring_weights.json, overnight_summary.json all populated",
            "Confirmed 10 decisions recorded from April 23 Google Form submissions",
            "Confirmed scoring_weights.json updated: 12 boosted keywords, applied_tracks, skipped_tracks recorded",
            "Identified 5 needs_review items from first real run — all 5 were 'Other' reasons needing manual fix",
            # job_search.py fixes
            "Fixed ZipRecruiter — added all ZipRecruiter URL patterns to BLOCKED_JOB_SITES (fully blocked)",
            "Fixed suspended domains — added flexjobs.zya.me to BLOCKED_JOB_SITES",
            "Fixed salary/guide page detection — added 'salaries 2026', 'developer salaries', 'engineer salaries' to is_relevant_title() search_page_patterns",
            "Fixed secret clearance detection — added 13 clearance indicators to is_us_remote() (top secret, ts/sci, polygraph, etc.)",
            "Fixed JMeter-only penalty — added -30pts when JMeter mentioned but LoadRunner NOT mentioned",
            "Fixed onsite city detection — expanded list to 40+ cities including Alpharetta, GA",
            "Added salary/guide page URL blocking to BLOCKED_JOB_SITES",
            # needs_review.json system
            "Built needs_review.json persistent storage system",
            "Updated update_scoring.py to write structured items to needs_review.json (full job details + status)",
            "Updated update_scoring_evan.py with same system (evan_needs_review.json)",
            "Added pending count to overnight_summary.json so email header shows total items awaiting review",
            # Weekly review system
            "Built weekly_review.py — Monday 10AM script for Hans",
            "Built weekly_review_evan.py — Monday 10:30AM script for Evan",
            "Weekly review email: groups items by category with color coding, count table, suggested actions",
            "After sending, clears all pending items (marks as 'reviewed'), commits to GitHub",
            "Added REVIEW_EMAIL to Evan's .env — weekly review goes to Hans, not Evan",
            "Created run_weekly_review.bat and run_weekly_review_evan.bat",
            "Added WeeklyJobReview Task Scheduler task (Monday 10:00 AM)",
            "Added EvanWeeklyReview Task Scheduler task (Monday 10:30 AM)",
            # GitHub portfolio
            "Created harichardson68 profile repo — GitHub profile README now live at github.com/harichardson68",
            "Profile README: What I Build, Featured Projects, Stack table, Background, Performance→AI Bridge table, Connect badges",
            "Created HR avatar — AI futuristic blue styling with circuit decorations",
            "Uploaded avatar to GitHub profile",
            "Created repo thumbnail SVGs for both job-search-hans and job-search-evan",
            "Added GitHub to LinkedIn contact info and Featured section",
            "Added both repos to LinkedIn Featured section with descriptions",
            "Added Bio, Location, LinkedIn to GitHub profile settings",
            # Amazon Jobs spotlight
            "Built search_amazon_jobs() function — searches amazon.jobs via Serper with site: targeting",
            "Amazon jobs use 10-day freshness window (vs 5 days for regular jobs)",
            "Amazon jobs numbered A1-A5 in email and today_jobs.json — separate from regular 1-10",
            "Amazon Spotlight section added to email — orange branding, internal.amazon.jobs reminder link",
            "Amazon jobs fully wired into decision loop — submit A1-A5 decisions via same Google Form",
            "Updated update_scoring.py — handles both int (1-10) and string (A1-A5) job numbers",
            "Updated load_today_jobs() to use number_display key for A1-A5 support",
            "Email header updated: 'Regular jobs 1-10 | Amazon Spotlight A1-A5'",
            "Added description hint to Google Form Job Number question: Enter 1-10 or A1-A5",
            # Resume and portfolio
            "Updated resume with GitHub link, self-improving feedback loop bullet, updated AI skills",
            "GitHub profile README live at github.com/harichardson68",
            "HR avatar uploaded — AI futuristic blue styling",
            "Repo thumbnails created for both job-search-hans and job-search-evan",
            "Added both repos to LinkedIn Featured section",
        ],
        "concepts_learned": [
            "GitHub profile README lives in a special repo named exactly the same as your username",
            "needs_review.json accumulates over time — weekly review clears it, Git shows full history",
            "JMeter-only penalty (-30pts) prevents JMeter-focused jobs from outscoring LoadRunner jobs",
            "Clearance detection must be in is_us_remote() so it runs on full description text",
            "Weekly review + auto-clear pattern keeps needs_review.json manageable without manual cleanup",
            "REVIEW_EMAIL env var separates weekly review recipient from daily email recipient",
            "GitHub social preview images show when repo links are shared on LinkedIn/Slack",
        ],
        "task_scheduler_full_list": [
            "JobSearch_Scheduler    — 12:00 PM daily       — job_search.py (Hans)",
            "EvanJobSearch          — 1:00 PM daily        — evan_job_search.py",
            "HansJobSearchUpdate    — 12:00 AM daily       — update_scoring.py",
            "EvanJobSearch_Update   — 12:30 AM daily       — update_scoring_evan.py",
            "ReviewDecisions        — 10:00 AM Mon+Thu     — review_decisions.py (renamed from WeeklyJobReview)",
            "ReviewDecisionsEvan    — 10:30 AM Mon+Thu     — review_decisions_evan.py (renamed from EvanWeeklyReview)",
        ],
        "next_session_priorities": [
            "1. Test Evan's job search end to end — confirm email arrives, form works",
            "2. Test weekly_review.py manually — run it and confirm email format",
            "3. Continue IBM course — K-Means clustering and unsupervised learning",
            "4. Consider adding architecture diagram image to repo READMEs",
            "5. Monitor first real week of needs_review.json accumulation",
            "6. Consider adding 'Too Junior' as a decision option to forms",
            "7. Verify Amazon Jobs spotlight appearing correctly in email",
        ],
        "future_milestones": [
            {
                "milestone": "K-Means clustering analysis on job_decisions.json",
                "when": "After 4-6 weeks of decision data (target: early June 2026)",
                "what": "Build analyze_decisions.py — clusters Applied vs Skipped jobs to discover hidden patterns",
                "why": "Finds keyword combinations and job patterns that predict 'Applied' — feeds back into scoring_weights.json",
                "data_requirement": "Minimum 200-300 decisions for meaningful clustering",
                "note": "job_decisions.json is NEVER cleared — it is the permanent training dataset",
            }
        ]
    },
    {
        "date": "May 07, 2026",
        "accomplishments": [
            # False positive filtering
            "Added BLOCKED_FP_DOMAINS and BLOCKED_FP_PATHS to job_search.py",
            "Added is_false_positive_url() helper — catches training sites, spam domains, services pages",
            "Blocked ishatrainingsolutions.org, 2kool4u.net, cortance.com and 20+ others",
            "Blocked URL paths: /events/, /courses/, /services/hire-, /training/, /blog/, /salary/",
            "Wired false positive check into Serper result loop",
            # Location filtering improvements
            "Added india remote, remote - india, engineering - india, remote india variants to strong_indicators",
            "Added community.n8n.io (forum posts) and remotejobsfinder.co (overseas) to BLOCKED_JOB_SITES",
            # Google Custom Search removed
            "Removed search_google_jobs() function entirely — 403 on every query, redundant with Serper",
            "Removed GOOGLE_API_KEY and GOOGLE_CX constants",
            # JSearch added
            "Added search_jsearch() — JSearch via RapidAPI, real-time Google for Jobs aggregation",
            "8 targeted queries: LoadRunner, VuGen, LRE, AI automation, prompt engineering, COBOL",
            "JSEARCH_API_KEY added to .env (free tier 200 req/month)",
            # K-Means decision tracker
            "Added get_decision_stats() to job_search.py",
            "Added K-Means progress bar to nightly email with decision breakdown by type",
            "Fixed get_decision_stats() for date-keyed array structure",
            # Google Sheet backfill
            "Discovered update_scoring.py was only processing TODAY rows — discarding all past submissions",
            "Added parse_sheet_date() helper handling all Google Sheets timestamp formats",
            "Rewrote read_google_sheet() to return all rows grouped by date",
            "Rewrote save_decisions() with backfill logic for past no_response entries",
            "Built and ran backfill_decisions.py — recovered 72 new records from Google Sheet",
            "job_decisions.json grew from 10 records (1 date) to 92 records (14 dates)",
            # today_jobs archiving
            "Added today_jobs_YYYY-MM-DD.json daily archive to job_search.py",
            "Ensures future backfills always have full job metadata",
            # Google Form improvements
            "Added regex validation to Job Number field: ^([1-9]|10|A[1-5])$",
            "Set Job Number field as Required",
            "Fixed bad historical entries (1a, 1A, A2 with trailing space) directly in sheet",
            # RAG implementation
            "Installed chromadb and sentence-transformers via pip",
            "Built JobRAG class with _init(), ingest_decisions(), retrieve_similar()",
            "Wired RAG ingest into end of nightly run",
            "First successful run: 20 decisions upserted into ChromaDB",
            "chroma_db folder created in Jobsearch directory",
            # README
            "Fully rewrote README.md — reflects current sources, RAG, ChromaDB, false positive filtering",
            "Updated architecture diagram, tech stack, features, roadmap",
            # GitHub traffic
            "Checked GitHub traffic — 265 clones, 144 unique cloners (mostly bots), 5 real human visitors",
        ],
        "concepts_learned": [
            "RAG = retrieval augmented generation — past decisions as context for future scoring",
            "ChromaDB stores vector embeddings locally — no cloud, no cost, git-trackable folder",
            "sentence-transformers all-MiniLM-L6-v2 = 80MB free embedding model, runs on CPU",
            "Location filtering is always rules-based — data quality problem, not a learning problem",
            "K-Means solves subjective pattern recognition, not data quality issues",
            "Google Sheets timestamp format is M/D/YYYY H:MM:SS — not zero-padded",
            "MinGW pip resolves to Strawberry Perl pip — must use python -m pip on Windows",
            "GitHub clones metric includes automated bots — visitor count is more meaningful",
            "update_scoring.py was silently discarding all past form submissions — today-only filter bug",
            "backfill_decisions.py bare-bones records skip RAG ingest (no job_id) — future records will be full",
        ],
        "decisions_milestone": {
            "total": 92,
            "target": 300,
            "pct": 31,
            "chroma_db_count": 20,
            "note": "20 in ChromaDB because backfilled records lack job_id — will grow with new nightly runs"
        },
        "next_session_priorities": [
            "1. Monitor tonight scheduled run — verify K-Means tracker shows in email",
            "2. Add JSEARCH_API_KEY to .env and test JSearch source",
            "3. Wire retrieve_similar() into cover letter prompt when GENERATE_COVER_LETTERS=True",
            "4. Update profile README at github.com/harichardson68 to mention RAG",
            "5. Continue IBM course — K-Means and unsupervised learning (relevant now!)",
            "6. Consider analyze_decisions.py when decision count reaches 150+",
        ]
    },
    {
        "date": "April 23, 2026",
        "accomplishments": [
            # GitHub setup
            "Created GitHub account (harichardson68)",
            "Created two public portfolio repos: job-search-hans and job-search-evan",
            "Sanitized both scripts — all API keys moved to .env files using os.environ.get()",
            "Added python-dotenv loader to both scripts",
            "Added portfolio-grade README.md to both repos with architecture diagrams and scoring tables",
            "Added .gitignore to both repos (excludes .env, google_credentials.json, runtime JSON files)",
            "Resolved GitHub secret scanning blocks — used orphan branch technique to rewrite history",
            "Downloaded GitHub mobile app for remote code management",
            # Decision feedback system
            "Designed and built complete human-in-the-loop feedback system",
            "Created Google Form for Hans (Hans Job Search Decisions) with 10 decision options",
            "Created Google Form for Evan (Evan Job Search Decisions) — copy of Hans's",
            "Linked both forms to Google Sheets (separate sheets per person)",
            "Set up Google Cloud Console — enabled Sheets API, created service account job-search-reader",
            "Downloaded google_credentials.json — placed in both job search folders",
            "Shared both Google Sheets with service account (Viewer access)",
            "Built update_scoring.py — midnight script for Hans",
            "Built update_scoring_evan.py — midnight script for Evan",
            "Midnight script sequence: git pull → read Google Sheet → write job_decisions.json → auto-patch job_search.py → update scoring_weights.json → write overnight_summary.json → git commit + push",
            "Added Submit Job Decisions button to both email templates linking to respective Google Forms",
            "Added overnight summary block to both email templates (shows auto-handled + needs review)",
            "Added today_jobs.json saving to both job search scripts (batch file for midnight script)",
            "Added generate_job_id() hash function to both scripts for stable job identification",
            "Added run_update_scoring.bat and run_update_scoring_evan.bat batch files",
            "Added two midnight Task Scheduler tasks: HansJobSearchUpdate (12:00AM) and EvanJobSearch_Update (12:30AM)",
            # Testing
            "Successfully ran job_search.py — found 19 jobs, sent email with Submit Decisions button",
            "Successfully submitted 10 decisions via Google Form",
            "Successfully ran update_scoring.py — read all 10 decisions from Google Sheet",
            "Confirmed job_decisions.json, scoring_weights.json, overnight_summary.json all created correctly",
            "Fixed timestamp format bug — Google Sheets uses M/D/YYYY not MM/DD/YYYY",
            "Fixed DECISION_MAP to handle Search Page (without Listing) alias",
            "Added Onsite / Not Remote as new decision option to both forms",
            "Published both Google Forms so they accept responses",
            # Issues identified from first test run
            "ZipRecruiter aggregator URLs slipping through — needs BLOCKED_JOB_SITES update",
            "Salary page (LangChain Developer Salaries 2026) scored as job — needs search page filter",
            "Alpharetta GA onsite job slipping through — location filter gap",
            "5 needs_review items: Secret clearance, Domain Suspended, JMeter-only job, Job Not Found, Onsite",
        ],
        "concepts_learned": [
            "GitHub secret scanning blocks pushes with hardcoded API keys even in deleted files",
            "Orphan branch technique rewrites git history completely — only solution for secret-in-history",
            "Google Forms timestamps use M/D/YYYY format not MM/DD/YYYY — must match exactly",
            "Google Forms creates extra columns when options are added after initial creation — delete them",
            "Service accounts need Viewer access to Google Sheet — separate from Forms ownership",
            "RLHF pattern: human feedback → automated scoring updates → self-improving system",
            "Git becomes audit trail of AI system learning over time — portfolio differentiator",
            "python-dotenv load_dotenv() must use abspath(__file__) to find .env in same folder as script",
        ],
        "needs_review_items": [
            "Secret clearance — Performance Analyst job at ASM Research requires clearance",
            "Domain Suspended — Flexjobs generative AI engineer link is dead",
            "More of a JMeter job — JMeter Performance Test Engineer, no LoadRunner mentioned",
            "Job Not Found — Prompt Engineer at Gregory Group link returning 404",
            "On site, Not remote — AI/ML Engineer at Cloudious is Alpharetta GA onsite",
        ],
        "next_session_priorities": [
            "1. Add ZipRecruiter to BLOCKED_JOB_SITES more aggressively",
            "2. Add salary/guide page detection to search page filter",
            "3. Review and address the 5 needs_review items from first run",
            "4. Test Evan's job search script end to end",
            "5. Continue IBM course — Random Forests, ensemble methods",
            "6. Consider portfolio README updates with agentic loop architecture diagram",
        ]
    },
    {
        "date": "April 19, 2026",
        "accomplishments": [
            "Analyzed job_search.log — identified 4 jobs only, cover letters blank, Reddit/BeBee slipping through",
            "Blocked Reddit, BeBee, WeWorkRemotely, Instagram, TikTok, Facebook Jobs URLs",
            "Blocked in.indeed.com (India) and ca.indeed.com (Canada) direct links",
            "Added onsite city detection — regex catches 'Job Title - Seattle, WA' style titles",
            "Fixed Adzuna — removed invalid 'where: remote' param causing 0 raw results every run",
            "Added GENERATE_COVER_LETTERS toggle to job_search.py",
            "Lowered AI Engineering min score 51 → 40pts",
            "Added prompt engineer, AI agent, agentic AI, LLM developer to AI keywords/scoring",
            "Removed Greenhouse, Lever, Dice — all returning 403",
            "Updated resume title: Senior Performance Engineer | AI Automation & Prompt Engineering",
            "Added PERF_TO_AI_VOCABULARY — 25+ performance engineering concepts mapped to AI/ML terms",
            "Added INTERVIEW_TRANSLATION_EXAMPLES — 5 Q&A scenarios with right/wrong answers",
        ],
        "concepts_learned": [
            "Decision tree nodes = decision points (what get_job_track() builds manually)",
            "Google Custom Search API requires both API key AND CX from same Google project",
            "Adzuna 'where: remote' is invalid — must filter remote in code after fetch",
            "24+ years of enterprise IT (14 in performance engineering) IS AI engineering vocabulary — just different names",
        ],
        "next_steps": [
            "Set up GitHub repo — completed April 23",
            "Create feedback.json template — completed April 23 as job_decisions.json",
        ]
    },
    {
        "date": "April 16, 2026",
        "accomplishments": [
            "Built complete automated cybersecurity job search system for Evan (evan_job_search.py)",
            "10 job sources initially, trimmed to 8 working sources",
            "Built comprehensive filter stack: 30+ senior exclusions, 50+ blocked cities/countries",
            "Added non-English posting filter, stale/closed job detection, sketchy job filter",
            "Rewrote score_job() - title hits full points (cap 100), desc hits 40% (cap 60)",
        ],
    },
    {
        "date": "April 10, 2026",
        "accomplishments": [
            "Removed QA track entirely - Performance/AI/COBOL only",
            "Added COBOL/Mainframe as third track (last resort)",
            "Rebuilt scoring: LR title/desc=50, Perf=35, AI/QA=20, COBOL=2",
            "Added minimum score thresholds per track",
            "Added Senior Performance filter - requires LoadRunner mention",
        ],
    },
    {
        "date": "March 29, 2026",
        "accomplishments": [
            "Built 17-source automated job search system",
            "Built 5-tab Agent Hub with Claude API",
            "Built prompt engineering cover letter generator",
            "Updated resume to 2 pages, ATS 91%",
            "Completed IBM regression module",
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# FILES IN BOTH JOB SEARCH FOLDERS
# ─────────────────────────────────────────────────────────────
FILE_INVENTORY = {
    "C:/Users/haric/Jobsearch/": [
        "job_search.py              - Hans's job search script (Performance/AI/COBOL)",
        "update_scoring.py          - Midnight update script (auto-patches job_search.py, updates scoring_weights.json, commits to Git)",
        "review_decisions.py        - Mon+Thu 10AM review script (surfaces 'other' decisions for pattern recognition)",
        "agent_hub.py               - 5-tab AI Agent Hub",
        "generate_resume.js         - Resume generator (run: node generate_resume.js)",
        "AI_Progress_Tracker.py     - This file!",
        "cleanup_backfilled_stubs.py - One-shot stub deletion tool (used 2026-05-20, --dry-run/--apply, can stay or archive)",
        "backfill_decisions.py      - One-shot from 2026-05-07 to recover form responses from Google Sheet (completed, can archive)",
        "run_job_search.bat         - Noon Task Scheduler batch file",
        "run_update_scoring.bat     - Midnight Task Scheduler batch file",
        "review_decisions.bat       - Mon+Thu 10AM Task Scheduler batch file",
        ".env                       - API keys and credentials (NEVER commit to Git)",
        "google_credentials.json    - Google service account key (NEVER commit to Git)",
        "seen_jobs.json             - Hans's duplicate tracker",
        "today_jobs.json            - Today's job batch (15 regular + 5 Amazon spotlight)",
        "today_jobs_YYYY-MM-DD.json - Daily archive (rolling 14-day retention; supports retroactive decision sync)",
        "job_decisions.json         - All-time decision history (71 records after 2026-05-20 stub cleanup)",
        "job_decisions.json.bak-cleanup-20260520_193836 - Pre-cleanup backup (72 stubs preserved here)",
        "scoring_weights.json       - Auto-updated scoring weights",
        "overnight_summary.json     - Last midnight run summary",
        "job_search_run.log         - Hans's debug log (overwrites each run)",
        "review_decisions_run.log   - review_decisions.py run log",
        "jobsearch_errors.log       - Persistent error log shared across scripts (append mode)",
        "job_results.json           - Latest results",
        "logs/                      - Snapshot folder for historical run logs",
        "chroma_db/                 - ChromaDB persistent vector store for RAG",
    ],
    "C:/Users/haric/Evan Jobsearch/": [
        "evan_job_search.py          - Evan's cybersecurity job search script",
        "update_scoring_evan.py      - Evan's midnight update script",
        "review_decisions_evan.py    - Mon+Thu review script for Evan (sends to Hans)",
        "run_evan_job_search.bat     - Noon Task Scheduler batch file",
        "run_update_scoring_evan.bat - Midnight Task Scheduler batch file",
        "review_decisions_evan.bat   - Mon+Thu Task Scheduler batch file",
        ".env                        - API keys + REVIEW_EMAIL=harichardson68@gmail.com",
        "google_credentials.json     - Google service account key (NEVER commit to Git)",
        "evan_seen_jobs.json         - Evan's duplicate tracker",
        "evan_today_jobs.json        - Today's job batch",
        "evan_job_decisions.json     - All-time decision history",
        "evan_scoring_weights.json   - Auto-updated scoring weights",
        "evan_overnight_summary.json - Last midnight run summary",
        "evan_job_search.log         - Evan's debug log",
    ],
}

INSTRUCTIONS = """
HOW TO USE THIS TRACKER:
========================
1. Upload this file at the start of each Claude session
2. Say: "Here is my AI progress tracker. I want to continue working on [topic]"
3. After each session update SESSION_NOTES

DAILY WORKFLOW:
===============
- 12:00 PM: Hans job search email arrives
- 1:00 PM:  Evan job search email arrives
- Anytime:  Click "Submit Job Decisions" in email → fill Google Form
- 12:00 AM: Hans midnight script auto-runs (update_scoring.py)
- 12:30 AM: Evan midnight script auto-runs (update_scoring_evan.py)
- Next noon: Smarter email with overnight summary at top

WEEKLY WORKFLOW (every Monday and Thursday):
============================================
- 10:00 AM: Hans review_decisions.py email arrives (unreviewed 'Other' items grouped by category)
- 10:30 AM: Evan review_decisions_evan.py email arrives (sends to Hans)
- Review items → bring patterns to Claude for code fixes
- Each surfaced item auto-flagged reviewed:true in job_decisions.json (data preserved permanently for K-Means)

REMOTE WORKFLOW (from phone):
==============================
- Chat with Claude on Claude.ai
- Edit code on github.com (GitHub mobile app)
- Midnight script does git pull automatically — picks up your changes
- Submit decisions via Google Form link in email

FOR INTERVIEW PREP:
===================
"Here is my tracker. Interview me for an AI QA Engineer role and critique my answers"

GITHUB:
=======
- Profile:          github.com/harichardson68
- Hans job search:  github.com/harichardson68/job-search-hans
- Evan job search:  github.com/harichardson68/job-search-evan

GOOGLE FORMS:
=============
- Hans decisions: https://docs.google.com/forms/d/1gLcCAhFvOpDWFgCGbu1r9Xubl9o7RVGQbyHwWYJPHIw/viewform
- Evan decisions: https://docs.google.com/forms/d/14_Jt5xRxZsjo3KgHM4V4wUuhGQ_soPQk8vFw8cVT9ds/viewform
"""
