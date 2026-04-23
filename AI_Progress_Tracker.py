# Hans Richardson - AI Engineering Progress Tracker
# Updated: April 19, 2026
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

# ─────────────────────────────────────────────────────────────
# JOB SEARCH SYSTEM - UPDATED April 4, 2026
# ─────────────────────────────────────────────────────────────
JOB_SEARCH_SYSTEM = {
    "script": "job_search.py",
    "location": "C:/Users/haric/Jobsearch/",
    "language": "Python",
    "sources": 9,
    "source_list": [
        "RemoteOK", "Google Jobs (Serper)", "Adzuna", "USAJobs",
        "Greenhouse", "Lever", "Google Custom Search", "Dice", "Wellfound"
    ],
    "dead_sources_removed": [
        "Indeed RSS (shut down 2024)",
        "LinkedIn RSS (shut down 2023)",
        "Jooble (premium pay wall - replaced with Serper)",
        "Remotive (too few results)", "WeWorkRemotely (non-English listings)",
        "Himalayas (no dates)", "Jobicy (low quality)", "SimplyHired (aggregator)",
        "ZipRecruiter (search pages only)", "Ashby (function broken)",
        "Jobvite (function broken)", "Glassdoor (function broken)",
        "ClearanceJobs (function broken)", "Arc.dev (category pages only)"
    ],
    "schedule": "Daily at 12:00 PM via Windows Task Scheduler",
    "email_notifications": "harichardson68@gmail.com",
    "freshness_filter": "5 days (120 hours)",
    "max_jobs_per_email": 10,
    "duplicate_tracking": "seen_jobs.json - never sends same job twice",
    "cover_letters": "AI-generated via Claude API (prompt engineering agent)",
    "ats_score": "91% against real LoadRunner contract posting",
    "api_keys_configured": [
        "Adzuna (aa7dfcd9 / 399ba411244302c8d4a5d29412795599)",
        "USAJobs (2be6pbkBb5I3ZMCJpYwGafeJPuYFxce5SHJU+ebnRMs=)",
        "Google Custom Search (AIzaSyC7xZX0by_wiDXhZ1fL9d9PikIKFGfi9CU / cx: a0cb76d963a4143f8)",
        "Anthropic Claude API (sk-ant-api03-FOM2Fsxz9zOy...)",
        "Gmail SMTP (harichardson68@gmail.com / App Password: futh pais gkjo ytbp)",
        "Serper Google Jobs (0b225829be39ec4de88df62e6e77bbeaf00bcf45)"
    ],
    "job_tracks": [
        "Performance Engineering (LoadRunner focus - Senior OK only if LR mentioned)",
        "AI Engineering (entry to mid - Senior EXCLUDED - min 51 pts)",
        "COBOL/Mainframe (last resort - min 10 pts)"
    ],
    "exclusions": [
        "Engineering Manager, Director, VP, Head of Engineering",
        "Chief, CTO, CIO, President, Vice President",
        "Supplier, Supply Chain, Procurement, Manufacturing",
        "Mechanical, Hardware, Electrical, Civil Engineer",
        "Field Engineer, Sales Engineer, Pre-Sales",
        "Freelance, Part-time, 8-20 hrs, Outsource",
        "Platform Engineer, Infrastructure Engineer, DevOps Engineer",
        "Site Reliability Engineer, Cloud Engineer",
        "Senior AI Engineer (AI track only)",
        "Senior Performance Engineer (unless LoadRunner mentioned)",
    ],
    "blocked_companies": [
        "DataAnnotation", "PitchmeAI", "SynergisticIT",
        "Appen", "Clickworker", "Telus International",
        "Outlier AI", "Scale AI"
    ],
    "blocked_sites": [
        "jobgether.com", "kuubik.com", "jobtogether.com", "jobisjob.com",
        "jobleads.com", "pangian.com", "dailyremote.com", "remoterocketship.com",
        "devitjobs.com", "novaedge.com", "twine.net", "applytojob.com",
        "dataannotation.tech", "pitchmeai.com", "jobflarely/liveblog365.com",
        "remotelyusajobs.com", "hireza.com", "synergisticit.com", "trabajo.org",
        "naukri.com", "jobright.ai", "energyjobline.com", "lockedinai.com",
        "whatjobs.com", "trovit.com", "travajo.com", "talents.vaia.com"
    ],
    "location_filters": [
        "India, Bangalore, Bengaluru, Mumbai, Delhi, Hyderabad, Chennai, Pune",
        "UK, Canada, Australia, Germany, France, Brazil, Philippines, Pakistan",
        "Singapore, China, Japan, Poland, Ukraine, LATAM, APAC, EMEA",
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
        "AI Engineering": 51,
        "COBOL/Mainframe": 10,
    },
    "fixes_applied": [
        "Replaced Jooble with Serper Google Jobs (direct links, no premium wall)",
        "Fixed Serper 404 error - correct endpoint URL",
        "Fixed relative date parsing - 1 day ago, 3 hours ago now work",
        "Added strict date filter - no date = excluded (no more old jobs)",
        "Added non-US location filter (is_us_remote function)",
        "Added Supplier/Manufacturing/Hardware title exclusions",
        "Added Freelance/Part-time/Outsource/Kuubik exclusions",
        "Added Senior exclusion for AI Engineering track only",
        "Added AI QA Engineer to all search queries",
        "Added AI title priority scoring (+20 pts)",
        "Updated cover letter prompt for MLOps/AI Test/LLM roles",
        "Fixed WWR non-English job filter",
        "Fixed email button KeyError crash",
        "Increased max jobs per email from 10 to 50",
        "Increased freshness window to 1 week (168 hours)",
    ]
}

# ─────────────────────────────────────────────────────────────
# EVAN'S JOB SEARCH SYSTEM - BUILT April 16, 2026
# ─────────────────────────────────────────────────────────────
EVAN_JOB_SEARCH_SYSTEM = {
    "script": "evan_job_search.py",
    "location": "C:/Users/haric/Jobsearch/",
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
    "sources": 10,
    "source_list": [
        "RemoteOK", "Google Jobs (Serper - no LinkedIn)",
        "Dice", "USAJobs", "Greenhouse", "Lever",
        "Wellfound", "ClearanceJobs", "Adzuna", "The Muse"
    ],
    "target_tracks": [
        "SOC Analyst", "Cybersecurity Analyst", "MDR Analyst",
        "Vulnerability Management", "Incident Response / DFIR",
        "Junior Penetration Tester", "Security Internship"
    ],
    "markets": "Remote (US only) + KC Metro hybrid/onsite",
    "freshness_filter": "72 hours (3 days) general / 48 hours Adzuna",
    "seen_jobs_expiry": "3 days (auto-prune)",
    "max_jobs_per_email": 10,
    "cover_letters": "AI-generated via Claude API (disabled during testing)",
    "target_email": "harichardson68@gmail.com (temp - switch to Evan when ready)",
    "scoring": {
        "title_hit": "Full points (capped at 100)",
        "description_hit": "40% of points (capped at 60)",
        "max_score": 160,
        "min_score": 20,
    },
    "filters_active": [
        "Senior title exclusions (30+ variants)",
        "Non-US location filter (50+ cities/countries)",
        "Non-KC onsite city block (45+ cities)",
        "Non-English posting filter (Tagalog, Indonesian, French, etc.)",
        "Stale/closed job filter (reposted, no longer accepting, 2+ months ago)",
        "Sketchy job filter (contract bench, C2C, corp-to-corp)",
        "Blocked companies (Crossing Hurdles, body shops, fake companies)",
        "Search page / careers homepage filter",
        "Experience filter (3+ years = excluded unless intern/entry level)",
        "LinkedIn completely removed (unreliable closed job data)",
    ],
    "known_issues": [
        "USAJobs: 8 raw results but 0 passing filters - federal titles non-standard",
        "The Muse: API returning 0 for Entry Level IT category",
        "Adzuna: Some stale jobs slip through (48hr filter helps)",
    ],
    "api_keys": [
        "Adzuna (aa7dfcd9 / 399ba411244302c8d4a5d29412795599) - shared with Hans",
        "USAJobs (2be6pbkBb5I3ZMCJpYwGafeJPuYFxce5SHJU+ebnRMs=)",
        "Serper (0b225829be39ec4de88df62e6e77bbeaf00bcf45) - shared with Hans",
        "Anthropic Claude API - shared with Hans (disabled during testing)",
        "Gmail SMTP (harichardson68@gmail.com / futh pais gkjo ytbp)",
    ],
}


AGENT_HUB = {
    "file": "agent_hub.py",
    "location": "C:/Users/haric/Jobsearch/",
    "language": "Python",
    "powered_by": "Claude API (claude-sonnet-4-20250514)",
    "tabs": [
        {"name": "Claudio - Job Search Agent", "purpose": "Review jobs, cover letters, run searches"},
        {"name": "PyCoach - Python Tutor", "purpose": "Learn Python in performance engineering context"},
        {"name": "AImentor - AI Study Coach", "purpose": "Study AI/ML concepts, interview prep"},
        {"name": "JMentor - LR to JMeter", "purpose": "Translate LoadRunner expertise to JMeter"},
        {"name": "ATSmax - Resume Scorer", "purpose": "Score resume against job postings"},
    ],
    "pending": ["AI Skills Tracker agent tab - to be built next session"]
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
    "Claude API": {"level": "Practical", "evidence": "Agent hub, cover letters, learning agents, Evan job search, cover letter generation", "date": "April 19, 2026"},
    "Prompt Engineering": {"level": "Practical", "evidence": "Job analysis agent, MLOps-specific prompts, cybersecurity cover letters, cover letter generator", "date": "April 19, 2026"},
    "Multi-Agent Architecture": {"level": "Practical", "evidence": "5-tab Agent Hub", "date": "March 29, 2026"},
    "REST API Integration": {"level": "Practical", "evidence": "6 job board APIs, Serper, Adzuna, USAJobs, Gmail SMTP, Google Custom Search", "date": "April 19, 2026"},
    "Python Automation": {"level": "Practical - Growing", "evidence": "job_search.py + evan_job_search.py - both production systems running daily", "date": "April 19, 2026"},
    "Debugging & Troubleshooting": {"level": "Practical", "evidence": "Fixed dead APIs, date parsing, email crashes, location filtering, score inflation, Adzuna params, Google API keys", "date": "April 19, 2026"},
    "Linear/Logistic Regression": {"level": "Conceptual + IBM Course", "evidence": "Completed regression module", "date": "March 29, 2026"},
    "Classification & Decision Trees": {"level": "Conceptual + IBM Course", "evidence": "OvO/OvA strategy, pruning, node concepts, information gain, midpoints method — quiz passed", "date": "April 19, 2026"},
    "SVM / Support Vector Machines": {"level": "Conceptual + IBM Course", "evidence": "Hyperplane, margin maximization, soft margin, C parameter, kerneling, epsilon — quiz passed", "date": "April 19, 2026"},
    "K-Nearest Neighbors": {"level": "Conceptual + IBM Course", "evidence": "Lazy learning, feature vs label distinction, feature scaling, K hyperparameter tuning — quiz passed", "date": "April 19, 2026"},
    "Random Forests": {"level": "Conceptual", "evidence": "Ensemble learning, bagging, feature importance, out-of-bag error — LoadRunner parallel understood", "date": "April 19, 2026"},
    "Bias-Variance Tradeoff": {"level": "Conceptual", "evidence": "Underfitting vs overfitting, high bias = too simple, high variance = spaghetti code", "date": "April 19, 2026"},
    "Filter Pipeline Design": {"level": "Practical", "evidence": "Built 15+ filter stages for job quality control across 2 scripts", "date": "April 19, 2026"},
    "Weighted Scoring / Classification": {"level": "Practical", "evidence": "Multi-track scoring algorithm with per-track thresholds — essentially a hand-coded classifier", "date": "April 19, 2026"},
}

# ─────────────────────────────────────────────────────────────
# INTERVIEW TALKING POINTS
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# PERFORMANCE ENGINEERING → AI/ML VOCABULARY TRANSLATION
# ─────────────────────────────────────────────────────────────
# KEY INSIGHT: 28 years of performance engineering maps directly
# to AI/ML concepts. In interviews, use BOTH terms together.
# Example: "I performed iterative threshold tuning — essentially
# hyperparameter optimization — to stabilize system performance."
# ─────────────────────────────────────────────────────────────
PERF_TO_AI_VOCABULARY = {
    # Tuning & Optimization
    "Tuning LoadRunner thresholds":         "Hyperparameter optimization",
    "Iterative script tuning until stable": "Gradient descent / iterative optimization",
    "Adjusting think times and pacing":     "Model parameter tuning",
    "Correlation and parameterization":     "Feature extraction and transformation",

    # Data & Classification
    "Filtering bad/noisy test results":     "Data cleaning / preprocessing",
    "Workload modeling":                    "Data distribution modeling / sampling",
    "Baseline vs load test comparison":     "Model validation / benchmarking",
    "Identifying outlier transactions":     "Anomaly detection",
    "Deduplication of results":             "Data normalization / deduplication",
    "Categorizing jobs by track":           "Multi-class classification",
    "Scoring jobs by keyword weight":       "Feature weighting / scoring model",
    "Blocking bad job sites":               "Pruning / noise reduction",
    "Title/description filtering":          "Natural language feature extraction",

    # Monitoring & Observability
    "Monitoring with Splunk/AppDynamics":   "ML observability / model monitoring",
    "SLA compliance targets":               "Decision boundaries / acceptance thresholds",
    "Root cause analysis of bottlenecks":   "Root cause analysis / anomaly attribution",
    "Throughput and latency measurement":   "Model inference performance metrics",
    "End-to-end transaction validation":    "Pipeline integrity testing",

    # System Design
    "Multi-protocol VuGen scripting":       "Multi-modal data pipeline development",
    "Scalability testing":                  "Model scalability / load testing AI endpoints",
    "SLA enforcement under load":           "Production ML SLA compliance",
    "AWS/Kubernetes performance testing":   "Cloud-native AI infrastructure testing",

    # AI-Specific (built today)
    "Job search scoring algorithm":         "Weighted classification model",
    "Multi-source job aggregation":         "Data pipeline / ETL with filtering",
    "Cover letter prompt engineering":      "Prompt engineering / LLM output optimization",
    "Agent Hub with Claude API":            "Multi-agent architecture / agentic AI",
    "API rate limit handling":              "Distributed systems / resilience engineering",
    "Seen jobs deduplication":              "State management / data persistence",
}

INTERVIEW_TRANSLATION_EXAMPLES = [
    {
        "question": "Do you have experience with data preprocessing?",
        "wrong_answer": "I don't have ML experience",
        "right_answer": "Yes — in performance engineering I spent significant time cleaning and "
                       "normalizing test result data, filtering outliers, and standardizing "
                       "transaction names across test runs. That's data preprocessing — I just "
                       "called it result analysis."
    },
    {
        "question": "Have you done any hyperparameter tuning?",
        "wrong_answer": "Not in an AI context",
        "right_answer": "Extensively — tuning think times, pacing, thread counts, and correlation "
                       "parameters in LoadRunner scripts to achieve stable, reproducible results "
                       "is hyperparameter optimization. I've done that iteratively for 14 years."
    },
    {
        "question": "Do you understand model validation?",
        "wrong_answer": "I haven't trained ML models",
        "right_answer": "Yes — comparing baseline performance against load test results to validate "
                       "system behavior under stress is the same concept. You establish a baseline "
                       "(training data), test against new conditions (validation set), and measure "
                       "deviation. I've been doing that across every performance engagement."
    },
    {
        "question": "Tell me about your experience with anomaly detection",
        "wrong_answer": "I haven't worked on anomaly detection systems",
        "right_answer": "Performance engineering is essentially applied anomaly detection — "
                       "identifying transactions that deviate from baseline behavior, finding "
                       "memory leaks, CPU spikes, and latency outliers using Splunk, AppDynamics, "
                       "and Grafana. I built alerting thresholds around statistical deviation "
                       "from normal — that's anomaly detection."
    },
    {
        "question": "What do you know about MLOps?",
        "wrong_answer": "I'm learning MLOps now",
        "right_answer": "My entire career has been the performance engineering equivalent of MLOps — "
                       "ensuring systems perform reliably in production, monitoring SLA compliance, "
                       "automating test pipelines, and integrating observability tools. MLOps applies "
                       "those same disciplines to ML model deployment and monitoring. The tools are "
                       "different but the engineering mindset is identical."
    },
]

INTERVIEW_TALKING_POINTS = [
    {
        "question": "Tell me about your AI engineering experience",
        "answer": """Built a fully automated 18-source job search system using Python and the Claude API.
Includes a prompt engineering agent that generates custom cover letters, a 5-agent desktop hub,
18 API integrations, duplicate tracking, non-US location filtering, and automated scheduling.
Iteratively debugged and improved the system based on real-world results."""
    },
    {
        "question": "How does your performance testing background apply to AI?",
        "answer": """Testing AI model inference endpoints is the same as load testing web services.
My observability stack (AppDynamics, Splunk, Grafana, Prometheus) maps directly to ML monitoring.
Model training = performance tuning - same iterative process I've done for 28 years.
I bring performance engineering expertise that most AI engineers simply don't have."""
    },
    {
        "question": "Why are you a good fit for an AI QA Engineer role?",
        "answer": """AI QA Engineer is the perfect intersection of my two skill sets.
28 years of QA and performance testing - I know how to test systems thoroughly.
Now actively building AI skills through IBM certification and hands-on projects.
Most candidates have QA OR AI experience. I'm building both simultaneously."""
    },
    {
        "question": "Tell me about a time you debugged a complex system",
        "answer": """My job search system returned zero results. Added debug logging, discovered
Indeed/LinkedIn RSS were dead, Serper had wrong endpoint, date strings like '1 day ago'
were crashing the parser. Fixed each issue systematically. System went from 0 to delivering
quality matches - same root cause analysis I used in LoadRunner for 14 years."""
    },
    {
        "question": "What AI projects have you built?",
        "answer": """1. AI-Powered Job Search System - 18 sources, prompt engineering, cover letters,
duplicate tracking, location filtering, automated scheduling. Production system running daily.
2. Agent Hub - 5 specialized Claude AI agents: job search, Python tutor, AI coach,
LR-to-JMeter translator, ATS resume scorer."""
    }
]

# ─────────────────────────────────────────────────────────────
# TARGET COMPANIES TO WATCH
# ─────────────────────────────────────────────────────────────
TARGET_COMPANIES = [
    {
        "name": "Elios Talent",
        "why": "Legit US staffing firm, Houston TX, PE-backed, Technology & AI specialty",
        "action": "Monitor LinkedIn for AI QA Engineer postings",
        "note": "They post roles for their clients - good gateway to AI QA positions"
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
        "date": "April 19, 2026",
        "accomplishments": [
            # Hans job_search.py fixes
            "Analyzed job_search.log — identified 4 jobs only, cover letters blank, Reddit/BeBee slipping through",
            "Blocked Reddit, BeBee, WeWorkRemotely, Instagram, TikTok, Facebook Jobs URLs",
            "Blocked in.indeed.com (India) and ca.indeed.com (Canada) direct links",
            "Added onsite city detection — regex catches 'Job Title - Seattle, WA' style titles",
            "Fixed Adzuna — removed invalid 'where: remote' param causing 0 raw results every run",
            "Adzuna now returning 20 raw results per query correctly",
            "Added GENERATE_COVER_LETTERS toggle to job_search.py",
            "Lowered AI Engineering min score 51 → 40pts",
            "Added prompt engineer, AI agent, agentic AI, LLM developer to AI keywords/scoring",
            "Added AI_TITLE_PRIORITY with prompt engineer at top",
            "Expanded Serper queries with site-targeted prompt/agent/LLM/MLOps queries",
            "Tightened AI Agent experience filter — agent/LLM/prompt roles blocked at 3+ years (was 5)",
            "Added 5+ years, 6+ years, significant experience to senior description signals",
            "Removed Greenhouse, Lever, Dice — all returning 403 (server blocks automated access)",
            "Expanded Google Custom Search queries to include Prompt Engineer, AI Agent, LLM, MLOps",
            "Added debug output to Google Custom Search, Adzuna, USAJobs, Greenhouse, Lever",
            "Fixed log file — renamed to job_search_run.log, removed fallback logic",
            "Fixed run_job_search.bat — removed >> log redirect, Python handles logging internally",
            "Discovered Google Custom Search API key was from wrong/deleted project",
            "Created new Google API key in correct project (My Project 67638 / optimum-habitat-304315)",
            "Custom Search API enabled in correct project — key: AIzaSyAcSmHNqL5VS3cGtDkzfvOH2jzVMjbpzBE",
            "CX confirmed correct: a0cb76d963a4143f8",
            # Evan job_search.py fixes
            "Updated Evan script — cover letters on, email to evanrichardson03@gmail.com",
            "Added salary/cert/aggregator page filters to Evan script",
            "Added Tier 2, lead, l3 SOC to Evan excluded titles",
            "Added KC Metro industry expansion — healthcare, banking, govt, utilities, energy",
            "Fixed Serper rate limiting with 1.2s sleep between queries",
            # Resume
            "Updated resume title: Senior Performance Engineer | AI Automation & Prompt Engineering",
            "Rewrote professional summary to lead with AI pivot story",
            "Updated AI project bullets — correct source count, multi-agent architecture, prompt engineering",
            # Tracker
            "Added PERF_TO_AI_VOCABULARY — 25+ performance engineering concepts mapped to AI/ML terms",
            "Added INTERVIEW_TRANSLATION_EXAMPLES — 5 Q&A scenarios with right/wrong answers",
        ],
        "concepts_learned": [
            "Decision tree nodes = decision points (what get_job_track() builds manually)",
            "Pruning = removing branches that add noise not value (what we do removing bad sources)",
            "OvO (One vs One) classification strategy — N*(N-1)/2 binary classifiers, majority vote",
            "Classification threshold = SLA target — same concept different domain",
            "Confusion matrix = log file analysis — misclassified jobs are classification errors",
            "Hyperparameter tuning = LoadRunner threshold tuning — same iterative process",
            "Data preprocessing = filtering bad test results — same concept different name",
            "ML observability = Splunk/AppDynamics monitoring — same discipline",
            "28 years of performance engineering IS AI engineering vocabulary — just different names",
            "Google Custom Search API requires both API key AND CX from same Google project",
            "Adzuna 'where: remote' is invalid — must filter remote in code after fetch",
            "Greenhouse/Lever block server-side API access — Serper already covers these via Google",
        ],
        "next_steps": [
            # Job Search
            "Google Custom Search still 403 — quota hit today (93/100), resets midnight Pacific",
            "Upwork.com now blocked at URL level in job_search.py",
            "Applied to Herbalife Prompt Engineer role — awaiting response",
            "Delete seen_jobs.json before next run for fresh results",
            "Set up GitHub repo — jobsearch-ai — next priority project",
            # IBM Course Progress
            "Completed: Decision Trees, Regression Trees, SVM, K-NN modules",
            "Quiz results: 4/5 correct SVM/KNN quiz (missed OvO voting scheme wording)",
            "All decision tree and regression tree quizzes 100%",
            "Continue IBM course — Random Forests and ensemble learning next",
            # Concepts learned afternoon session
            "K-NN = lazy learner — memorizes ALL training data, no formula, looks up at prediction time",
            "K-NN uses FEATURES to find similar jobs, LABELS to make the decision",
            "Feature scaling critical for K-NN — normalize so score doesn't dominate recency",
            "Random Forest = 500 decision trees with unique data/features, majority vote wins",
            "Random Forest parallel = LoadRunner running 500 scripts with varied pacing/think time/data",
            "Ensemble learning = combining weak models into one strong model",
            "Feature importance = Random Forest tells you which features drove decisions most",
            "Out of bag error = built-in validation, no separate test set needed",
            "Bias = average gap between predicted and actual values",
            "High bias = underfitting = too simple, fails even on training data",
            "High variance = overfitting = spaghetti code, memorizes training data",
            "Epsilon (ε) in SVR = tolerance zone around prediction = SLA tolerance analogy",
            "Information gain = criteria for best node split in decision tree",
            "Midpoints method = how regression trees find candidate splits",
            "Agentic loop roadmap saved — 5 phases designed and stored in tracker",
            "GitHub + feedback.json = minimum viable agentic loop infrastructure",
            # Key insights
            "Key insight: 28 years of performance engineering = AI/ML vocabulary all along",
            "Key insight: Random Forest = parallel load testing for decisions",
            "Key insight: K-NN labeled data stored in feedback.json = the model IS the data",
            "Key insight: intermediate ML course is right level — understanding concepts not memorizing math",
            "Key insight: AI engineers today direct AI to write code, not write from scratch",
        ],
        "next_session_priorities": [
            "1. Check Google Custom Search working (quota resets daily)",
            "2. Set up GitHub repo and push both scripts",
            "3. Create feedback.json template — start Phase 1 agentic loop",
            "4. Continue IBM course — Random Forests, ensemble methods",
            "5. Update resume bullets with AI/ML vocabulary translations",
            "6. Monitor Herbalife application",
        ]
    },
    {
        "date": "March 29, 2026",
        "accomplishments": [
            "Built 17-source automated job search system",
            "Built 5-tab Agent Hub with Claude API",
            "Built prompt engineering cover letter generator",
            "Updated resume to 2 pages, ATS 91%",
            "Completed IBM regression module",
            "Added AI + Performance hybrid job track",
        ],
        "next_steps": ["Add Anthropic API credits", "Continue IBM course", "Run daily at noon"]
    },
    {
        "date": "April 1, 2026",
        "accomplishments": [
            "Diagnosed zero results - Indeed/LinkedIn RSS were dead",
            "Added Jooble, Remotive, WeWorkRemotely",
            "Fixed USAJobs headers, added duplicate tracker",
            "System went from 0 to 10 results",
            "Applied to 10 job matches",
        ],
        "next_steps": ["Monitor daily results", "Build AI Skills Tracker tab", "Continue IBM course"]
    },
    {
        "date": "April 10, 2026",
        "accomplishments": [
            "Removed QA track entirely - Performance/AI/COBOL only",
            "Added COBOL/Mainframe as third track (last resort)",
            "Rebuilt scoring: LR title/desc=50, Perf=35, AI/QA=20, COBOL=2",
            "Added minimum score thresholds per track",
            "Added Senior Performance filter - requires LoadRunner mention",
            "Added company name blocking (DataAnnotation, PitchmeAI etc.)",
            "Added non-US location strong indicators (Canada, Europe, India states)",
            "Added state restriction filter - excludes state-specific remote",
            "Missouri exception - MO/KC jobs always allowed",
            "Added closed job detection (no longer accepting)",
            "Added search page filter for Serper organic results",
            "Blocked 10+ more bad sites (Naukri, Hireza, Jobright, etc.)",
            "Fixed Ashby/Jobvite/Glassdoor/ClearanceJobs missing function crashes",
            "Added dual logging (console + overwrite log file)",
            "Added Wellfound as new source",
            "Removed Arc.dev (category pages only)",
            "Updated resume summary with integrated testing emphasis",
            "Added Integration & API Performance Testing to Core Competencies",
            "Added integrated testing bullets to USDA and CenturyLink sections",
            "Added filtering pipeline bullet to Projects section",
        ],
        "next_steps": [
            "Delete seen_jobs.json for fresh results tomorrow",
            "Monitor email for cleaner results",
            "Continue IBM supervised learning module",
            "Turn DEBUG_MODE = False once confirmed working",
        ]
    },
    {
        "date": "April 16, 2026",
        "accomplishments": [
            "Built complete automated cybersecurity job search system for Evan (evan_job_search.py)",
            "10 job sources: RemoteOK, Serper, Dice, USAJobs, Greenhouse, Lever, Wellfound, ClearanceJobs, Adzuna, The Muse",
            "Removed LinkedIn entirely - closed jobs not detectable from Serper snippets",
            "Added Adzuna as LinkedIn replacement - 23 jobs per run, real structured data with dates",
            "Added The Muse source (no API key required, entry level focus)",
            "Built comprehensive filter stack: 30+ senior exclusions, 50+ blocked cities/countries",
            "Added non-English posting filter (Tagalog, Indonesian, French, etc.)",
            "Added stale/closed job detection from snippet text",
            "Added sketchy job filter (contract bench, C2C, body shops)",
            "Added blocked companies list (Crossing Hurdles, Asistente Virtual, etc.)",
            "Rewrote score_job() - title hits full points (cap 100), desc hits 40% (cap 60)",
            "Added clean_title() to strip Job Application for / Apply for prefixes",
            "Added seen_jobs 3-day expiry with auto-pruning (was growing unbounded)",
            "Added GENERATE_COVER_LETTERS toggle (disabled - API credits depleted)",
            "Reduced MAX_JOBS_EMAIL from 15 to 10",
            "Changed freshness from 5 days to 3 days",
            "Fixed SEEN_JOBS_FILE missing from config (was crashing silently)",
            "Added top-level try/except with full traceback for crash diagnosis",
            "Added posted date to log output for freshness visibility",
            "Added is_recent() max_hours parameter for per-source freshness control",
            "USAJobs: loosened title filter to score-based, added federal title keywords",
            "Added cover letter generation for Evan using his real resume/certs/clearance",
            "Script delivers clean top 10 jobs to harichardson68@gmail.com (temp)",
        ],
        "concepts_learned": [
            "LinkedIn organic snippets don't include closed/hybrid/location status - unfilterable",
            "Adzuna /where=remote param invalid - must search broadly and filter locally",
            "Serper /jobs endpoint requires paid plan - organic only on free tier",
            "Federal job titles are non-standard (IT Specialist vs SOC Analyst) - need score-based filter",
            "Score inflation from keyword stacking - title/desc separation + caps solve it",
            "seen_jobs.json needs expiry or grows forever - dict format with dates solves it",
        ],
        "next_steps": [
            "Fix USAJobs - add debug output to see why 8 raw results score 0",
            "Fix The Muse - API returning 0 for Entry Level IT",
            "Add Adzuna 48hr freshness validation on next run",
            "Add API credits to console.anthropic.com to re-enable cover letters",
            "Switch TARGET_EMAIL to Evan's actual email when ready",
            "Set up Windows Task Scheduler for daily automated runs",
            "Build similar system for Hans's job search with updated sources",
        ]
    },
    {
        "date": "April 4, 2026",
        "accomplishments": [
            "Replaced Jooble with Serper Google Jobs (no premium wall, direct links)",
            "Fixed Serper 404 error - wrong endpoint",
            "Fixed relative date parsing (1 day ago, 3 hours ago)",
            "Added strict date filter - no more 11 month old jobs",
            "Added non-US location filter (India, UK, LATAM etc.)",
            "Added Supplier/Manufacturing/Hardware/Freelance/Outsource/Kuubik exclusions",
            "Added Senior exclusion for AI Engineering track only",
            "Added AI QA Engineer to all search queries and scoring",
            "Added AI title priority scoring (+20 pts for MLOps/AI Test/LLM)",
            "Updated cover letter prompt specifically for MLOps/AI Test roles",
            "Fixed WWR non-English job filter",
            "Fixed email button crash",
            "Increased to 50 jobs per email",
            "1 week freshness window",
            "Researched Elios Talent - confirmed legit US firm",
            "Added AI QA Engineer interview talking point",
            "Added LinkedIn manual search recommendation",
        ],
        "concepts_learned": [
            "Relative date strings need custom parsing",
            "Job aggregators wrap URLs - need direct links",
            "Non-US remote jobs slip through without explicit filtering",
            "AI QA Engineer = perfect intersection of QA + AI skills",
            "Senior AI roles excluded - entry/mid AI is right target now",
            "LinkedIn blocks scraping - manual check needed for key companies",
        ],
        "next_steps": [
            "Run updated script - verify Serper returns results",
            "Check LinkedIn manually for AI QA Engineer at Elios Talent",
            "Turn DEBUG_MODE = False once confirmed working",
            "Continue IBM supervised learning module",
            "Build AI Skills Tracker tab in Agent Hub",
        ]
    }
]

# ─────────────────────────────────────────────────────────────
# HOW TO USE THIS FILE
# ─────────────────────────────────────────────────────────────
INSTRUCTIONS = """
HOW TO USE THIS TRACKER:
========================
1. Upload this file at the start of each Claude session
2. Say: "Here is my AI progress tracker. I want to continue working on [topic]"
3. After each session update SESSION_NOTES

FOR INTERVIEW PREP:
===================
"Here is my tracker. Interview me for an AI QA Engineer role and critique my answers"

FILES IN C:/Users/haric/Jobsearch/:
=====================================
- job_search.py           - Hans's job search script (Performance/AI/COBOL)
- evan_job_search.py      - Evan's cybersecurity job search script
- agent_hub.py            - 5-tab AI Agent Hub
- generate_resume.js      - Resume generator (run: node generate_resume.js)
- run_job_search.bat      - Windows batch file for Task Scheduler
- job_results.json        - Latest results
- seen_jobs.json          - Hans's duplicate tracker
- evan_seen_jobs.json     - Evan's duplicate tracker (3-day expiry)
- job_search.log          - Hans's debug log
- evan_job_search.log     - Evan's debug log
- AI_Progress_Tracker.py  - This file!

MANUAL LINKEDIN SEARCHES (do weekly):
======================================
- "AI QA Engineer" remote
- "AI Test Engineer" remote
- Elios Talent company page
"""
