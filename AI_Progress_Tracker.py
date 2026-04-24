# Hans Richardson - AI Engineering Progress Tracker
# Updated: April 24, 2026 (evening)
# Share this file at the start of each Claude session for instant context!

# ─────────────────────────────────────────────────────────────
# PERSONAL PROFILE
# ─────────────────────────────────────────────────────────────
NAME            = "Hans Richardson"
EMAIL           = "harichardson68@gmail.com"
LOCATION        = "Lee's Summit, MO (Remote)"
LINKEDIN        = "linkedin.com/in/hans-richardson"
CURRENT_JOB     = "Amazon Warehouse (Dec 2025 - Present)"
CLEARANCE       = "Public Trust (held during USDA contract 2021-2025)"
EXPERIENCE      = "28+ years Performance/QA Test Engineering"
CORE_SKILL      = "LoadRunner/VuGen/LRE - 14 years expert"
EDUCATION       = "Bachelor of Science in Computer Information Systems"

# ─────────────────────────────────────────────────────────────
# GITHUB
# ─────────────────────────────────────────────────────────────
GITHUB = {
    "username": "harichardson68",
    "repos": [
        {
            "name": "job-search-hans",
            "url": "github.com/harichardson68/job-search-hans",
            "description": "Automated performance engineering job search pipeline",
            "topics": ["python", "job-search", "performance-testing", "loadrunner", "automation", "claude-api"],
        },
        {
            "name": "job-search-evan",
            "url": "github.com/harichardson68/job-search-evan",
            "description": "Automated cybersecurity job search pipeline for Evan",
            "topics": ["python", "job-search", "cybersecurity", "automation", "claude-api"],
        },
    ],
    "created": "April 23, 2026",
}

# ─────────────────────────────────────────────────────────────
# JOB SEARCH SYSTEM - UPDATED April 23, 2026
# ─────────────────────────────────────────────────────────────
JOB_SEARCH_SYSTEM = {
    "script": "job_search.py",
    "location": "C:/Users/haric/Jobsearch/",
    "language": "Python",
    "sources": 6,
    "source_list": [
        "RemoteOK", "Google Jobs (Serper)", "Adzuna", "USAJobs",
        "Google Custom Search", "Wellfound"
    ],
    "dead_sources_removed": [
        "Indeed RSS (shut down 2024)",
        "LinkedIn RSS (shut down 2023)",
        "Jooble (premium pay wall - replaced with Serper)",
        "Remotive (too few results)", "WeWorkRemotely (non-English listings)",
        "Himalayas (no dates)", "Jobicy (low quality)", "SimplyHired (aggregator)",
        "ZipRecruiter (search pages only)", "Ashby (function broken)",
        "Jobvite (function broken)", "Glassdoor (function broken)",
        "ClearanceJobs (function broken)", "Arc.dev (category pages only)",
        "Greenhouse (403 blocks)", "Lever (403 blocks)", "Dice (403 blocks)",
    ],
    "schedule": "Daily at 12:00 PM via Windows Task Scheduler",
    "midnight_update": "Daily at 12:00 AM via Windows Task Scheduler (update_scoring.py)",
    "amazon_jobs_spotlight": {
        "function":        "search_amazon_jobs()",
        "source":          "amazon.jobs via Serper site: targeting",
        "max_results":     5,
        "freshness_days":  10,
        "numbering":       "A1-A5 (separate from regular 1-10)",
        "min_score":       15,
        "email_section":   "Amazon Jobs Spotlight — orange branded section below top 10",
        "decision_loop":   "Fully integrated — submit A1-A5 via same Google Form",
        "internal_reminder": "Link to internal.amazon.jobs in every email",
    },
    "email_notifications": "harichardson68@gmail.com",
    "freshness_filter": "5 days (120 hours)",
    "max_jobs_per_email": 10,
    "duplicate_tracking": "seen_jobs.json - never sends same job twice",
    "cover_letters": "AI-generated via Claude API (prompt engineering agent)",
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
        "midnight_script": "update_scoring.py",
        "decisions": [
            "Applied", "Bad Link", "Onsite / Not Remote", "Too Senior",
            "Salary Too Low", "Not Interested", "Already Seen / Duplicate",
            "Search Page Listing", "Not in United States", "Other"
        ],
        "auto_handled": [
            "Applied → boosts matched keywords in scoring_weights.json",
            "Bad Link → auto-blocks domain in BLOCKED_JOB_SITES",
            "Not in United States + reason → auto-adds location to NON_US_LOCATIONS",
            "Other + 'bad location - X' → auto-adds X to NON_US_LOCATIONS",
            "Other + 'bad company - X' → auto-adds X to blocked_companies",
        ],
        "needs_manual_review": [
            "Other reasons that don't match auto-detect patterns",
            "These appear in overnight_summary.json and tomorrow's email header",
        ],
        "midnight_sequence": [
            "1. git pull — sync latest from GitHub",
            "2. Read Google Sheet — get today's form submissions",
            "3. Write job_decisions.json — save all decisions",
            "4. Apply auto-fixes — patch job_search.py + scoring_weights.json",
            "5. Write overnight_summary.json — shown in tomorrow's email header",
            "6. git commit + push — everything to GitHub",
        ],
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
    "apis_enabled": ["Google Sheets API", "Google Custom Search API"],
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
    "file": "Hans-Richardson-Performance_Engineer.docx",
    "generator": "generate_resume.js",
    "command": "cd C:/Users/haric/Jobsearch && node generate_resume.js",
    "pages": 2,
    "last_updated": "April 10, 2026",
    "ats_score": "91%",
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
        "Unsupervised Learning",
        "Neural Networks and Deep Learning",
        "Generative AI and LLMs",
    ],
    "key_insights": [
        "Supervised = labeled data, Unsupervised = unlabeled data",
        "Performance testing IS model training - same iterative process!",
        "Threshold = SLA target (28 years of experience applies!)",
        "MLOps/AI Test Engineer roles are realistic targets for Hans",
        "Performance testing background is a COMPETITIVE ADVANTAGE in AI",
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
    "Agentic Systems": {"level": "Practical", "evidence": "Self-improving feedback loop: email → Google Form → Google Sheets → midnight script → auto-patches job_search.py → git commit", "date": "April 23, 2026"},
    "Git / GitHub": {"level": "Practical", "evidence": "Two public repos with portfolio-grade READMEs, automated nightly commits from update scripts", "date": "April 23, 2026"},
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
    {
        "question": "Tell me about your AI engineering experience",
        "answer": """Built two fully autonomous job search pipelines using Python and the Claude API.
Each system aggregates jobs from 6-8 sources daily, scores them with a multi-track weighted
classification engine, generates AI cover letters, and emails a digest. A human-in-the-loop
feedback system via Google Forms feeds a midnight script that reads decisions, auto-patches
the source code, updates scoring weights, and commits everything to GitHub — fully autonomous.
Also built a 5-tab multi-agent hub using the Claude API for job analysis, Python tutoring,
AI coaching, LR-to-JMeter translation, and ATS resume scoring."""
    },
    {
        "question": "What's the most complex AI agent you've built?",
        "answer": """An autonomous self-improving job search pipeline. It runs daily, sends an email
digest, captures user decisions via Google Forms, and a midnight update script reads those
decisions from Google Sheets, automatically patches filtering logic (blocking bad locations,
sites, companies), updates scoring weights, and commits changes to GitHub. The system literally
rewrites parts of its own source code based on human feedback, with Git as the audit trail.
Built entirely in Python with Anthropic SDK, Google Sheets API, SMTP, and subprocess Git calls."""
    },
    {
        "question": "How does your performance testing background apply to AI?",
        "answer": """Testing AI model inference endpoints is the same as load testing web services.
My observability stack (AppDynamics, Splunk, Grafana, Prometheus) maps directly to ML monitoring.
Model training = performance tuning - same iterative process I've done for 28 years.
I bring performance engineering expertise that most AI engineers simply don't have."""
    },
    {
        "question": "Do you have startup experience?",
        "answer": """I run a side business (H&G Lighting) giving me direct early-stage exposure.
My AI engineering work is self-directed and entrepreneurial — designed, built, and deployed
production-grade autonomous systems without a team or infrastructure, which mirrors the
scrappy, figure-it-out culture of early-stage startups."""
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
            "JobSearch_Scheduler    — 12:00 PM daily  — job_search.py (Hans)",
            "EvanJobSearch          — 1:00 PM daily   — evan_job_search.py",
            "HansJobSearchUpdate    — 12:00 AM daily  — update_scoring.py",
            "EvanJobSearch_Update   — 12:30 AM daily  — update_scoring_evan.py",
            "WeeklyJobReview        — 10:00 AM Monday — weekly_review.py",
            "EvanWeeklyReview       — 10:30 AM Monday — weekly_review_evan.py",
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
            "28 years of performance engineering IS AI engineering vocabulary — just different names",
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
        "update_scoring.py          - Midnight update script (reads Google Sheet, patches code, commits to Git)",
        "weekly_review.py           - Monday 10AM weekly review email script",
        "agent_hub.py               - 5-tab AI Agent Hub",
        "generate_resume.js         - Resume generator (run: node generate_resume.js)",
        "run_job_search.bat         - Noon Task Scheduler batch file",
        "run_update_scoring.bat     - Midnight Task Scheduler batch file",
        "run_weekly_review.bat      - Monday 10AM Task Scheduler batch file",
        ".env                       - API keys and credentials (NEVER commit to Git)",
        "google_credentials.json   - Google service account key (NEVER commit to Git)",
        "seen_jobs.json             - Hans's duplicate tracker",
        "today_jobs.json            - Today's job batch (for midnight script)",
        "job_decisions.json         - All-time decision history",
        "needs_review.json          - Accumulates items needing manual review (cleared weekly)",
        "scoring_weights.json       - Auto-updated scoring weights",
        "overnight_summary.json     - Last midnight run summary",
        "job_search_run.log         - Hans's debug log",
        "job_results.json           - Latest results",
        "AI_Progress_Tracker.py     - This file!",
    ],
    "C:/Users/haric/Evan Jobsearch/": [
        "evan_job_search.py          - Evan's cybersecurity job search script",
        "update_scoring_evan.py      - Evan's midnight update script",
        "weekly_review_evan.py       - Monday 10:30AM weekly review email script (sends to Hans)",
        "run_evan_job_search.bat     - Noon Task Scheduler batch file",
        "run_update_scoring_evan.bat - Midnight Task Scheduler batch file",
        "run_weekly_review_evan.bat  - Monday 10:30AM Task Scheduler batch file",
        ".env                        - API keys + REVIEW_EMAIL=harichardson68@gmail.com",
        "google_credentials.json    - Google service account key (NEVER commit to Git)",
        "evan_seen_jobs.json         - Evan's duplicate tracker",
        "evan_today_jobs.json        - Today's job batch (for midnight script)",
        "evan_job_decisions.json     - All-time decision history",
        "evan_needs_review.json      - Accumulates items needing manual review (cleared weekly)",
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

WEEKLY WORKFLOW (every Monday):
================================
- 10:00 AM: Hans weekly review email arrives (needs_review.json items, grouped by category)
- 10:30 AM: Evan weekly review email arrives (goes to Hans's email)
- Review items → bring patterns to Claude for code fixes
- File is auto-cleared after each weekly email send

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
