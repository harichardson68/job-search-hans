"""
Automated Job Search Script for Hans Richardson - Performance Engineer
Searches: RemoteOK, Indeed RSS, LinkedIn RSS, Adzuna, USAJobs
Targets: LoadRunner, JMeter, NeoLoad, Performance Engineer roles (Remote)

SETUP:
    pip install requests feedparser python-dateutil anthropic python-dotenv

OPTIONAL API KEYS (free tiers available):
    - Adzuna: https://developer.adzuna.com/  (free, ~1000 calls/day)
    - USAJobs: https://developer.usajobs.gov/ (free, requires registration)
    - OpenAI: https://platform.openai.com/   (for cover letter generation)
      OR leave blank to use a template-based cover letter instead
"""

import requests
import feedparser
import json
import re
import os
import time
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
import logging
import sys
from dotenv import load_dotenv

# Load .env file from same directory as this script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

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

# 
# 48-HOUR FRESHNESS FILTER
# 
MAX_AGE_HOURS = 120  # 5 days
DEBUG_MODE = True   # Set to False once confirmed working
GENERATE_COVER_LETTERS = False  # Set to False to disable cover letter generation

NON_US_LOCATIONS = [
    "india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
    "chennai", "pune", "kolkata", "noida", "gurugram", "gurgaon",
    " ind ", "united kingdom", "london", "canada", "toronto",
    "australia", "sydney", "melbourne", "germany", "berlin",
    "france", "paris", "brazil", "philippines", "manila",
    "pakistan", "singapore", "china", "japan", "tokyo",
    "poland", "ukraine", "romania", "latam", "latin america", "apac", "emea",
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
]

def is_blocked_site(url):
    """Returns True if the job URL is from a blocked middleman site."""
    url_lower = str(url).lower()
    return any(site in url_lower for site in BLOCKED_JOB_SITES)

def is_us_remote(title, description, location=""):
    # Check location field first - if it contains a non-US location, reject immediately
    loc_lower = location.lower().strip()
    if loc_lower:
        for non_us in NON_US_LOCATIONS:
            if non_us.strip() in loc_lower:
                return False
    # Also check title and description for strong non-US indicators
    check = (title + " " + description).lower()
    # Strong indicators - if these appear anywhere, reject
    strong_indicators = [
        # India
        "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
        "chennai", "pune", "kolkata", "noida", "gurugram", "gurgaon",
        "india only", "india based", "based in india", "location: india",
        "karnataka", "maharashtra", "tamil nadu",
        "cochin", "coimbatore", "kochi", "kolkata", "indore",
        "jaipur", "ahmedabad", "chandigarh", "bhopal", "lucknow",
        "smartworking", "smart working", "smart-working solutions", "smart working solutions",
        "verito solutions", "verito",
        # Canada
        "remote in canada", "canada remote", "location: canada",
        "based in canada", "toronto", "vancouver", "montreal",
        "ontario", "british columbia", "alberta", "markham, on",
        "markham, ontario", " on,", ", on ", "qualcomm canada",
        # UK
        "remote in uk", "united kingdom", "london, uk", "location: uk",
        # Other
        "remote in australia", "remote in germany", "remote in europe",
        "remote in india", "europe, remote", "europe remote",
        "available from: europe", "offer is available from: europe",
        "remote jobs anywhere worldwide", "worldwide remote",
        "principal ai engineer (europe", "europe only",
        "emea remote", "apac remote", "latam remote",
        "latin america", "latam", "south america",
        "colombia", "argentina", "brazil", "mexico", "chile",
        "remote people", "globally distributed",
    ]
    for indicator in strong_indicators:
        if indicator in check:
            return False
    # Detect state-restricted remote jobs (remote but must live in specific state)
    # These phrases indicate state restrictions
    import re
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
    # These are onsite roles masquerading in search results
    onsite_city_pattern = r"[-–|,]\s*(seattle|chicago|boston|austin|dallas|denver|phoenix|atlanta|houston|new york|san francisco|los angeles|philadelphia|charlotte|orlando|miami|bellevue|portland|minneapolis|pittsburgh|raleigh|nashville|detroit|baltimore|st\. louis|cleveland|columbus|indianapolis|louisville|memphis|richmond|norfolk|sacramento|san diego|san jose|las vegas|tampa|jacksonville|hartford|providence|buffalo|rochester|albany|newark|jersey city)\s*,\s*[a-z]{2}"
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
    ]
    check = (title + " " + description + " " + company).lower()
    return any(co in check for co in blocked_companies)
def parse_relative_date(date_str):
    """Handle relative dates like '1 day ago', '3 days ago', '2 hours ago'"""
    import re
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
# CONFIGURATION   Edit these
# 
ADZUNA_APP_ID   = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY  = os.environ.get("ADZUNA_APP_KEY", "")
USAJOBS_API_KEY = os.environ.get("USAJOBS_API_KEY", "")
USAJOBS_EMAIL   = os.environ.get("USAJOBS_EMAIL", "")
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")   # optional, for AI cover letters
CLAUDE_API_KEY  = os.environ.get("CLAUDE_API_KEY", "")

#  Email notifications
GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS", "")
EMAIL_TO       = os.environ.get("EMAIL_TO", GMAIL_ADDRESS)

SEARCH_KEYWORDS = [
    # Track 1: Performance Engineering (core)
    "LoadRunner", "performance engineer", "performance tester",
    "JMeter", "NeoLoad", "load testing", "performance testing",
    # Track 3: AI Engineering (entry level)
    "entry level AI engineer", "junior AI engineer", "associate AI engineer",
    "AI engineer entry", "machine learning engineer entry",
]

CANDIDATE = {
    "name": "Hans Richardson",
    "location": "Lee's Summit, MO (Remote)",
    "linkedin": "linkedin.com/in/hans-richardson",
    "years_exp": 28,
    "top_skills": ["LoadRunner", "VuGen", "LRE", "JMeter", "NeoLoad",
                   "AppDynamics", "Splunk", "Prometheus", "Grafana",
                   "AWS", "Kubernetes", "REST API", "SQL", "Python",
                   "Selenium", "Test Automation", "AI Engineering",
                   "Performance Engineering", "Workload Modeling",
                   "Scalability Testing", "SLA Compliance"],
}

OUTPUT_FILE    = "job_results.json"
SEEN_JOBS_FILE = "seen_jobs.json"

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
# RELEVANCE SCORING - Three tracks
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

# 
# STRICT TITLE FILTER
# 
# Job title MUST contain at least one of these to be included
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
]

def is_relevant_title(title):
    """Returns True only if the job title contains a required technical keyword
    AND does not contain an excluded management term."""
    import re as _retitle
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
        r"best.*jobs in \d{4}",
        r"top \d+.*jobs",
        # Job application form pages
        r"^job application for ",
        r"^apply (now|for|to) ",
        r"hiring\] ",
    ]
    for pattern in search_page_patterns:
        if _retitle.search(pattern, t):
            return False
    # First check it has a required keyword
    if not any(kw in t for kw in REQUIRED_TITLE_KEYWORDS):
        return False
    # Then make sure it is not a management role
    if any(excl in t for excl in EXCLUDED_TITLE_TERMS):
        return False
    return True


def get_job_track(title, description):
    """Identify which track a job belongs to and check level requirements."""
    text = (title + " " + description).lower()
    t = title.lower()

    is_ai   = any(kw in text for kw in AI_HIGH_KEYWORDS)
    is_sdet = any(kw in ["sdet", "junior sdet", "entry level sdet", "associate sdet",
                          "junior test engineer", "junior software engineer in test"] for kw in [text] if kw in text) or "sdet" in t
    is_qa   = any(kw in text for kw in QA_HIGH_KEYWORDS)
    if is_ai:
        is_senior = any(s in t for s in ["senior", "sr.", "sr ", "lead ", "principal", "staff ", "director", "head of", "vp "])
        if is_senior:
            return "AI Engineering", False

        # Check description for experience requirements
        import re as _re
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
            matches = _re.findall(pattern, full_text)
            for match in matches:
                try:
                    first_num = next((x for x in match if x and x.isdigit()), None)
                    if first_num and int(first_num) >= exp_threshold:
                        return "AI Engineering", False
                except:
                    pass

        # Allow if explicitly entry/mid OR if no strong seniority signal in description
        entry_mid_signals = [
            "entry level", "entry-level", "junior", "associate", "new grad",
            "recent graduate", "0-2 years", "0-3 years", "1-3 years",
            "mid level", "mid-level", "intermediate", "2-4 years", "3-5 years",
            "no experience required", "training provided",
        ]
        senior_desc_signals = [
            "extensive experience", "proven track record", "expert level",
            "deep expertise", "seasoned", "7+ years", "8+ years", "10+ years",
            "subject matter expert", "sme ", "advanced degree required",
            "5+ years", "6+ years", "significant experience",
        ]
        has_entry_mid = any(sig in full_text for sig in entry_mid_signals)
        has_senior_desc = any(sig in full_text for sig in senior_desc_signals)

        if has_senior_desc and not has_entry_mid:
            return "AI Engineering", False

        return "AI Engineering", True
    if is_sdet:
        level_ok = any(lvl in t for lvl in ["junior", "entry", "associate", "entry-level"])
    if is_qa:
        level_ok = any(lvl in t for lvl in QA_AUTOMATION_LEVEL_FILTER) or not any(
            senior in t for senior in ["senior", "lead", "principal", "staff", "director"]
        )
        return "QA Automation", level_ok
    # Performance Engineering - Senior OK only if LoadRunner/VuGen/LRE mentioned
    is_senior = any(s in t for s in ["senior", "sr.", "sr ", "lead", "principal", "staff", "director", "head of", "vp"])
    has_loadrunner = any(kw in text for kw in ["loadrunner", "vugen", "lre", "load runner", "vuser"])
    if is_senior and not has_loadrunner:
        return "Performance Engineering", False  # Senior but no LoadRunner = skip
    return "Performance Engineering", True

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

    # COBOL in title gets small bonus (last resort - lowest priority)
    if any(kw in t for kw in ["cobol", "cics", "mainframe"]):
        score += 2
        matched.append("COBOL-in-title")

    # LoadRunner anywhere in description = high priority
    for kw in LOADRUNNER_PRIORITY:
        if kw in text and kw + "-in-title" not in matched:
            score += 50
            matched.append(kw)

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
    # AI keywords = 20 pts (title already scored above)
    for kw in AI_HIGH_KEYWORDS:
        if kw in text and kw not in matched:
            score += 20
            matched.append(kw)
    # Bonus keywords = 3 pts
    for kw in PERF_BONUS_KEYWORDS + QA_BONUS_KEYWORDS + AI_BONUS_KEYWORDS:
        if kw in text and kw not in matched:
            score += 3
            matched.append(kw)
    # COBOL = 2 pts - absolute last resort
    for kw in COBOL_HIGH_KEYWORDS + COBOL_BONUS_KEYWORDS:
        if kw in text and kw not in matched:
            score += 2
            matched.append(kw)
    # Bonus keywords handled above per track
    return score, list(set(matched))

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
            title = item.get("position", "")
            desc  = item.get("description", "")
            score, matched = score_job(title, desc)
            track, level_ok = get_job_track(title, desc)
            if DEBUG_MODE and title:
                if score == 0:
                    print(f"   [DEBUG] RemoteOK FILTERED-score: {title[:60]}")
                elif not level_ok:
                    print(f"   [DEBUG] RemoteOK FILTERED-level: {title[:60]}")
                elif not is_recent(item.get("date", "")):
                    print(f"   [DEBUG] RemoteOK FILTERED-date: {title[:60]}")
                elif not is_relevant_title(title):
                    print(f"   [DEBUG] RemoteOK FILTERED-title: {title[:60]}")
            if score > 0 and level_ok and is_recent(item.get("date", "")) and is_relevant_title(title) and is_us_remote(title, desc) and not is_blocked_site(url_job) and not is_blocked_company(title, desc):
                jobs.append({
                    "source": "RemoteOK",
                    "title": title,
                    "company": item.get("company", "N/A"),
                    "url": item.get("url", ""),
                    "posted": item.get("date", ""),
                    "description": desc[:500],
                    "score": score,
                    "matched_keywords": matched,
                    "track": track,
                })
        print(f"   [OK] RemoteOK: {len(jobs)} relevant jobs found")
    except Exception as e:
        print(f"   [ERROR] RemoteOK error: {e}")
    return jobs

# 
# SOURCE 2: Serper.dev Google Jobs API (2,500 free searches/month - direct apply links!)
# Sign up free at: https://serper.dev
# 
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

def search_serper_jobs():
    print("[SEARCH] Searching Google Jobs via Serper...")
    jobs = []
    if SERPER_API_KEY == "YOUR_SERPER_API_KEY":
        print("   [WARN] Serper skipped - add your free API key from serper.dev")
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
                company  = item.get("company", item.get("source", "N/A"))
                desc     = item.get("description", item.get("snippet", ""))
                url_job  = item.get("applyLink", "") or item.get("link", "") or item.get("url", "")
                posted   = item.get("date", item.get("publishedDate", ""))
                # Skip search results pages - we want direct job postings only
                search_page_indicators = [
                    "jobs?q=", "job-search?", "jobs-search?", "/jobs/search",
                    "/jobs?", "q=ai+ml", "search?q=", "find-jobs",
                    "indeed.com/jobs", "indeed.com/q-", "linkedin.com/jobs/search",
                    "glassdoor.com/Job/jobs", "glassdoor.com/Job/remote",
                    "monster.com/jobs/search",
                    "ziprecruiter.com/Jobs/", "ziprecruiter.com/jobs-search",
                    "naukri.com/loadrunner", "naukri.com/cobol", "naukri.com/",
                    "dice.com/jobs/q-", "dice.com/jobs?",
                    "jobs-in-remote", "jobs-in-usa", "job-vacancies",
                    "vacancies-in", "/remote-jobs?", "remote-jobs-in",
                ]
                if any(indicator in url_job.lower() for indicator in search_page_indicators):
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Serper FILTERED-searchpage: {title[:50]}")
                    continue
                location = item.get("location", "").lower()
                if url_job in seen:
                    continue
                seen.add(url_job)
                if "remote" not in location and "remote" not in (title + desc).lower():
                    continue
                score, matched = score_job(title, desc)
                track, level_ok = get_job_track(title, desc)
                if score > 0 and level_ok and is_recent(posted) and is_relevant_title(title) and is_us_remote(title, desc, location) and not is_blocked_site(url_job) and not is_blocked_company(title, desc, company):
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
                        "salary": item.get("salary", ""),
                    })
        except Exception as e:
            print(f"   [ERROR] Serper error ({query}): {e}")
        time.sleep(1.2)  # Rate limit: stay under Serper's burst threshold
    print(f"   [OK] Google Jobs: {len(jobs)} relevant jobs found")
    return jobs


# 
# SOURCE 4: Adzuna API
# 
def search_adzuna():
    print("[SEARCH] Searching Adzuna...")
    jobs = []
    if ADZUNA_APP_ID == "YOUR_ADZUNA_APP_ID":
        print("   [WARN]  Adzuna skipped  add your API key to the config")
        return jobs

    # Broader performance testing titles — filter for LR/LRE in description
    queries = [
        "performance test engineer",
        "performance engineer",
        "load test engineer",
        "performance testing engineer",
        "sr performance engineer",
        "senior performance engineer",
        "performance qa engineer",
        "software performance engineer",
        "application performance engineer",
        "enterprise performance engineer",
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

                if "remote" not in combined:
                    continue
                if is_blocked_site(url_job) or is_blocked_company(title, desc, company):
                    continue
                if not is_recent(posted):
                    if DEBUG_MODE:
                        print(f"   [DEBUG] Adzuna FILTERED-stale: {title[:50]} [{posted[:10]}]")
                    continue

                score, matched = score_job(title, desc)
                track, level_ok = get_job_track(title, desc)
                # For Performance track, require LR signal for quality control
                if track == "Performance Engineering":
                    if not any(sig in combined for sig in LR_SIGNALS):
                        if DEBUG_MODE:
                            print(f"   [DEBUG] Adzuna FILTERED-no-LR: {title[:50]}")
                        continue
                if score > 0 and level_ok and is_relevant_title(title) and is_us_remote(title, desc):
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
                        "salary": "",
                    })
        except Exception as e:
            print(f"   [ERROR] Adzuna error ({query}): {e}")
        time.sleep(1)
    print(f"   [OK] Adzuna: {len(jobs)} relevant jobs found")
    return jobs

# 
# SOURCE 5: USAJobs API
# 
def search_usajobs():
    print("[SEARCH] Searching USAJobs...")
    jobs = []
    if USAJOBS_API_KEY == "YOUR_USAJOBS_API_KEY":
        print("   [WARN]  USAJobs skipped  add your API key to the config")
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
                score, matched = score_job(title, desc)
                track, level_ok = get_job_track(title, desc)
                if score > 0 and level_ok and is_recent(mv.get("PublicationStartDate", "")) and is_relevant_title(title):
                    jobs.append({
                        "source": "USAJobs",
                        "title": title,
                        "company": mv.get("OrganizationName", "Federal Agency"),
                        "url": mv.get("PositionURI", ""),
                        "posted": mv.get("PublicationStartDate", ""),
                        "description": desc[:500],
                        "score": score,
                        "matched_keywords": matched,
                        "track": track,
                        "salary": mv.get("PositionRemuneration", [{}])[0].get("MinimumRange", "")
                              + " - " + mv.get("PositionRemuneration", [{}])[0].get("MaximumRange", ""),
                    })
        except Exception as e:
            print(f"   [ERROR] USAJobs error ({query}): {e}")
    seen = set()
    unique = []
    for j in jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
    print(f"   [OK] USAJobs: {len(unique)} relevant jobs found")
    return unique

# 
# COVER LETTER GENERATOR
# 
RESUME_FULL = """
Name: Hans Richardson
Title: Senior Performance / QA Test Engineer
Location: Lee's Summit, MO (Remote)
LinkedIn: linkedin.com/in/hans-richardson
Email: harichardson68@gmail.com

EXPERIENCE:
- Sr. Performance/QA Test Engineer (Contract), USDA, Jan 2021 - Sep 2025
  * 14 years LoadRunner/VuGen/LRE expert
  * Led AWS/Kubernetes migration performance testing
  * Integrated AppDynamics, Splunk, Prometheus, Grafana for observability
  * Increased throughput 40%, reduced defect resolution time 35%
  * Developed test plans in Jira/Confluence using Agile/Scrum
  * SLA compliance: <5s transactions, <2s services

- Programmer/Software Engineer, Sprint/Embarq/CenturyLink, 1999-2017
  * LoadRunner specialist for 9 years
  * Scaled systems to 12,000+ transactions per minute
  * SAP CRM, ERP, BRIM performance testing
  * Agile/Scrum ceremonies and sprint planning

SKILLS:
- Performance Tools: LoadRunner/VuGen/LRE (14 yrs expert), JMeter (trained), NeoLoad (trained)
- Monitoring: AppDynamics, Splunk, Grafana, Prometheus, AWS X-Ray
- Cloud/DevOps: AWS, Kubernetes, CI/CD, GitHub
- QA: Selenium, test automation, regression testing
- Programming: Python (in training), SQL, JavaScript, COBOL
- Methodologies: Agile/Scrum, Waterfall

EDUCATION:
- BS Computer Information Science, Park University, 1996
- BA Marketing, Park University, 1992

CERTIFICATIONS:
- HP LoadRunner Training (HP, 2010)
- JMeter Performance Testing (Coursera, 2025)
- AWS Cloud Practitioner (Udemy, 2025)
- AI Engineer Bootcamp (Udemy, 2025)
- IBM Generative AI Engineering (Coursera, 2025-2026)
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
    24 years of IT experience makes him immediately productive with minimal ramp-up time.

Write only the cover letter text, no subject line or extra commentary."""

    return prompt

def generate_cover_letter_claude(job):
    """Generate tailored cover letter using Claude API with optimized prompt."""
    try:
        prompt = build_optimized_prompt(job)
        
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
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
            print(f"   [WARN] Claude API error {resp.status_code}, using template")
            return generate_cover_letter_template(job)
    except Exception as e:
        print(f"   [WARN] Claude API failed: {e}, using template")
        return generate_cover_letter_template(job)

def generate_cover_letter_template(job):
    """Fallback template-based cover letter."""
    skills_str = ", ".join(job["matched_keywords"][:5]) if job["matched_keywords"] else "LoadRunner, JMeter, NeoLoad"
    return f"""Dear Hiring Manager,

With 28+ years of performance engineering experience and deep expertise in {skills_str}, I am confident I would be a strong fit for the {job["title"]} role at {job["company"]}.

In my recent role as Sr. Performance Test Engineer at the USDA, I led performance testing for AWS/Kubernetes migrations, integrating AppDynamics, Splunk, and Prometheus to ensure SLA compliance. I increased throughput by 40% and reduced defect resolution time by 35%. Prior to that, I spent 18 years at Sprint/CenturyLink as a LoadRunner specialist, scaling systems to 12,000+ transactions per minute.

I am available immediately for remote work and would welcome the opportunity to discuss how my background aligns with your team's needs.

Best regards,
Hans Richardson
Lee's Summit, MO | linkedin.com/in/hans-richardson
"""

def generate_cover_letter(job):
    if CLAUDE_API_KEY:
        return generate_cover_letter_claude(job)
    if OPENAI_API_KEY:
        return generate_cover_letter_claude(job)
    return generate_cover_letter_template(job)

# 
# MAIN
# 

# 
# SOURCE 8: Greenhouse.io (public ATS boards)
# 

# 
# SOURCE 10: Google Custom Search (searches ALL ATS platforms)
# 
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CX      = os.environ.get("GOOGLE_CX", "")

def search_google_jobs():
    print("[SEARCH] Searching Google Custom Search...")
    jobs = []
    if GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY":
        print("   [WARN]  Google Custom Search skipped  add your API key to the config")
        return jobs

    queries = [
        # LoadRunner/Performance — highest value targets
        'site:boards.greenhouse.io "loadrunner" "remote"',
        'site:jobs.lever.co "loadrunner" "remote"',
        'site:myworkdayjobs.com "loadrunner" "performance engineer"',
        'site:dice.com "loadrunner" "performance engineer" "remote"',
        # Prompt Engineering
        'site:boards.greenhouse.io "prompt engineer" "remote"',
        'site:jobs.lever.co "prompt engineer" "remote"',
        # AI Agent / LLM
        'site:jobs.ashbyhq.com "ai agent engineer" "remote"',
        'site:jobs.lever.co "generative ai engineer" "remote"',
        # MLOps
        'site:boards.greenhouse.io "mlops engineer" "remote"',
        # COBOL
        '"COBOL developer" remote',
    ]
    seen = set()
    for query in queries:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CX,
                "q": query,
                "num": 10,
                "dateRestrict": "d5",  # last 5 days
            }
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            if DEBUG_MODE:
                items_count = len(data.get("items", []))
                print(f"   [DEBUG] Google Search '{query[:50]}': {items_count} results, status {resp.status_code}")
                if "error" in data:
                    print(f"   [DEBUG] Google Search error: {data['error'].get('message', '')}")
            for item in data.get("items", []):
                title   = item.get("title", "")
                desc    = item.get("snippet", "")
                url_job = item.get("link", "")
                if url_job in seen:
                    continue
                seen.add(url_job)
                score, matched = score_job(title, desc)
                track, level_ok = get_job_track(title, desc)
                if score > 0 and level_ok and is_relevant_title(title):
                    jobs.append({
                        "source": "Google Search",
                        "title": title,
                        "company": item.get("displayLink", "N/A"),
                        "url": url_job,
                        "posted": "",
                        "description": desc[:500],
                        "score": score,
                        "matched_keywords": matched,
                        "track": track,
                    })
        except Exception as e:
            print(f"   [ERROR] Google Search error: {e}")
    print(f"   [OK] Google Search: {len(jobs)} relevant jobs found")
    return jobs


# ---------------------------------------------
# SOURCE 11: Dice (tech-focused job board RSS)
# ---------------------------------------------

# ---------------------------------------------
# SOURCE 14c: Wellfound (startup jobs, direct links)
# ---------------------------------------------
def search_wellfound():
    print("[SEARCH] Searching Wellfound...")
    jobs = []
    if SERPER_API_KEY == "YOUR_SERPER_API_KEY":
        print("   [WARN] Wellfound skipped - Serper key needed")
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
                score, matched = score_job(title, desc)
                track, level_ok = get_job_track(title, desc)
                if score > 0 and level_ok and is_relevant_title(title) and is_us_remote(title, desc) and not is_blocked_site(url_job):
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
                    })
        except Exception as e:
            print(f"   [ERROR] Wellfound error ({query}): {e}")
    print(f"   [OK] Wellfound: {len(jobs)} relevant jobs found")
    return jobs
def main():
    print("\n" + "="*55)
    print("  Hans Richardson  Automated Job Search")
    print("  Target: LoadRunner / Performance Engineer (Remote)")
    print("="*55 + "\n")

    all_jobs = []
    all_jobs += search_remoteok()
    all_jobs += search_serper_jobs()
    all_jobs += search_adzuna()
    all_jobs += search_usajobs()
    all_jobs += search_google_jobs()
    all_jobs += search_wellfound()

    # Sort by score descending
    all_jobs.sort(key=lambda x: x["score"], reverse=True)

    # Apply minimum score thresholds per track
    MIN_SCORES = {
        "Performance Engineering": 30,  # Lower threshold - core specialty
        "AI Engineering": 40,           # Lowered from 51 - catching real jobs
        "COBOL/Mainframe": 10,          # Last resort - low threshold
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

    # Remove jobs already seen in previous runs
    seen_urls = load_seen_jobs()
    new_jobs = [j for j in all_jobs if j.get("url", "") not in seen_urls]
    duplicate_count = len(all_jobs) - len(new_jobs)
    if duplicate_count > 0:
        print(f"[OK] Removed {duplicate_count} duplicate jobs already sent previously")
    all_jobs = new_jobs

    print(f"\n{'='*55}")
    print(f"[STATS] Total relevant jobs found: {len(all_jobs)}")

    top_jobs = all_jobs[:10]  # Send top 10 jobs per day

    if len(all_jobs) == 0:
        print(f"[STATS] No matching jobs found today.")
    elif len(all_jobs) <= 50:
        print(f"[STATS] Sending all {len(top_jobs)} job{'s' if len(top_jobs) != 1 else ''} to {EMAIL_TO}")
    else:
        print(f"[STATS] Found {len(all_jobs)} jobs — sending top {len(top_jobs)} highest scoring to {EMAIL_TO}")

    print(f"{'='*55}\n")
    print(f"[STATS] Generating cover letters for {len(top_jobs)} job{'s' if len(top_jobs) != 1 else ''}...\n")
    for i, job in enumerate(top_jobs, 1):
        if GENERATE_COVER_LETTERS:
            job["cover_letter"] = generate_cover_letter(job)
        else:
            job["cover_letter"] = ""
        print(f"  [{i:02d}] Score:{job['score']:3d} | {job['source']:<10} | {job['title'][:50]}")
        print(f"        {job['company']} | {job['url'][:60]}")
        print()

    # Save newly seen job URLs
    if top_jobs:
        # Only mark SENT jobs as seen - unsent jobs will appear tomorrow
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
    print(f"   Open it to see all jobs + cover letters.\n")

    # Send email notification always  even if no jobs found
    send_email(top_jobs)

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
        print(f"\n--- COVER LETTER ---")
        print(job["cover_letter"])
        print("-"*40)

def generate_job_id(job):
    """Generate a short stable ID for a job based on title + company + url."""
    import hashlib
    raw = f"{job.get('title','')}{job.get('company','')}{job.get('url','')}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]

def load_overnight_summary():
    """Load the overnight update summary if it exists."""
    summary_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overnight_summary.json")
    try:
        if os.path.exists(summary_file):
            with open(summary_file, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def send_email(top_jobs):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    print("\n[EMAIL] Sending email notification...")
    today      = datetime.now().strftime("%B %d, %Y")
    today_key  = datetime.now().strftime("%Y-%m-%d")
    count      = len(top_jobs)
    subject    = f"Job Search Results - {count} Top Matches - {today}" if count > 0 else f"Job Search Ran - No Matches Found - {today}"

    # ── Decision code reference ──────────────────────────────────
    decision_guide = """
<div style="background:#f0f4ff;border:1px solid #c5d0e8;border-radius:8px;padding:14px 18px;margin:16px 0 20px;">
  <p style="margin:0 0 6px;font-weight:bold;color:#1F3864;font-size:13px;">HOW TO RESPOND — Reply to this email with job numbers and codes:</p>
  <table style="font-size:12px;color:#333;border-collapse:collapse;">
    <tr><td style="padding:2px 12px 2px 0;"><strong>1</strong></td><td>Applied</td>
        <td style="padding:2px 12px 2px 16px;"><strong>5</strong></td><td>Not interested</td></tr>
    <tr><td style="padding:2px 12px 2px 0;"><strong>2</strong></td><td>Bad link</td>
        <td style="padding:2px 12px 2px 16px;"><strong>6</strong></td><td>Already seen</td></tr>
    <tr><td style="padding:2px 12px 2px 0;"><strong>3</strong></td><td>Too senior</td>
        <td style="padding:2px 12px 2px 16px;"><strong>7</strong></td><td>Search page / not a real job</td></tr>
    <tr><td style="padding:2px 12px 2px 0;"><strong>4</strong></td><td>Salary too low</td>
        <td style="padding:2px 12px 2px 16px;"><strong>8</strong></td><td>Other (add reason after colon)</td></tr>
  </table>
  <p style="margin:8px 0 0;font-size:12px;color:#555;">
    <strong>Example reply:</strong><br>
    Job 1: 1<br>
    Job 2: 3<br>
    Job 5: 8 bad location - brussels<br>
    <em>(You can reply to some, all, or none — unanswered jobs are treated as neutral)</em>
  </p>
</div>"""

    # ── Overnight summary block ──────────────────────────────────
    summary = load_overnight_summary()
    summary_html = ""
    if summary:
        auto_items = "".join(f"<li>{item}</li>" for item in summary.get("auto_handled", []))
        manual_items = "".join(f"<li>{item}</li>" for item in summary.get("needs_review", []))
        auto_block = f"<p style='margin:6px 0 2px;color:#0F6E56;font-weight:bold;font-size:12px;'>Auto-handled ✓</p><ul style='margin:0;padding-left:18px;font-size:12px;color:#333;'>{auto_items}</ul>" if auto_items else ""
        manual_block = f"<p style='margin:10px 0 2px;color:#c0392b;font-weight:bold;font-size:12px;'>Needs manual review ⚠</p><ul style='margin:0;padding-left:18px;font-size:12px;color:#333;'>{manual_items}</ul>" if manual_items else ""
        summary_html = f"""
<div style="background:#f9f9f9;border:1px solid #ddd;border-radius:8px;padding:14px 18px;margin:0 0 20px;">
  <p style="margin:0 0 8px;font-weight:bold;color:#1F3864;font-size:13px;">Overnight Update Report — {summary.get('date','')}</p>
  <p style="font-size:12px;color:#555;margin:0 0 6px;">
    Decisions received: <strong>{summary.get('decisions_received',0)}</strong> of <strong>{summary.get('jobs_sent',0)}</strong> jobs &nbsp;|&nbsp;
    No response: <strong>{summary.get('no_response',0)}</strong> &nbsp;|&nbsp;
    Git commit: <strong>{summary.get('git_committed','—')}</strong>
  </p>
  {auto_block}{manual_block}
</div>"""

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;color:#333;">
    <h2 style="color:#1F3864;">Daily Job Search Results</h2>
    <p>Hi Hans, here are your top matches for <strong>{today}</strong>.</p>
    {summary_html}
    {decision_guide}"""

    if count == 0:
        html += """<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:16px;margin:16px 0;">
        <p style="margin:0;color:#f57f17;font-weight:bold;">No matching jobs found today.</p>
        <p style="margin:8px 0 0;color:#555;">The script ran successfully but found no new jobs matching your criteria posted in the last 5 days that you haven't already seen. Check back tomorrow!</p>
        </div>"""
    html += "<hr/>"

    for i, job in enumerate(top_jobs, 1):
        job_id   = generate_job_id(job)
        keywords = ", ".join(job["matched_keywords"][:6])
        cover    = job.get("cover_letter", "").replace("\n", "<br>")
        salary   = f"<p><strong>Salary:</strong> {job['salary']}</p>" if job.get("salary","").strip(" -") else ""
        track    = job.get("track", "")
        posted   = job.get("posted","")
        posted_display = posted[:10] if posted else "Date unknown — verify before applying!"

        html += f"""
<div style="border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:24px;">
  <h3 style="color:#1F3864;margin:0 0 4px;">
    #{i} - {job["title"]}
    <span style="font-size:11px;background:#e8f0fe;color:#1F3864;padding:2px 8px;border-radius:10px;margin-left:6px;">{track}</span>
  </h3>
  <p style="margin:4px 0;"><strong>Company:</strong> {job["company"]} | <strong>Source:</strong> {job["source"]} | <strong>Score:</strong> {job["score"]} pts</p>
  <p style="margin:4px 0;"><strong>Posted:</strong> <span style="color:#e65100;font-weight:500;">{posted_display}</span> | <strong>Track:</strong> {track}</p>
  {salary}
  <p style="margin:4px 0;"><strong>Matched Skills:</strong> {keywords}</p>
  <p style="margin:12px 0 6px;">
    <a href="{job.get('url','')}" style="background:#1F3864;color:#fff;padding:8px 16px;border-radius:4px;text-decoration:none;font-size:13px;">View and Apply</a>
  </p>

  <div style="background:#f7f9fc;border:1px solid #dde3ef;border-radius:6px;padding:12px;margin-top:10px;">
    <p style="margin:0 0 8px;font-size:12px;color:#555;"><strong>Job #{i} decision</strong> &nbsp;·&nbsp; <span style="font-family:monospace;font-size:11px;color:#888;">ID: {job_id}</span></p>
    <p style="margin:0;font-size:12px;color:#444;">Reply to this email and include: &nbsp;<strong>Job {i}: [code]</strong></p>
    <p style="margin:4px 0 0;font-size:11px;color:#888;">1=Applied &nbsp; 2=Bad link &nbsp; 3=Too senior &nbsp; 4=Salary too low &nbsp; 5=Not interested &nbsp; 6=Already seen &nbsp; 7=Search page &nbsp; 8=Other (add reason)</p>
  </div>

  <hr style="border:none;border-top:1px solid #eee;margin:12px 0"/>
  <p><strong>Cover Letter:</strong></p>
  <div style="background:#f9f9f9;padding:12px;border-radius:4px;font-size:14px;">{cover}</div>
</div>"""

    html += """<hr/><p style="font-size:12px;color:#888;">Sent automatically by Hans's Job Search Script &nbsp;·&nbsp; Reply with decisions anytime before midnight.</p></body></html>"""

    # Save today's job batch for the overnight script to reference
    batch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "today_jobs.json")
    try:
        batch = {
            "date": today_key,
            "jobs": [
                {
                    "job_id": generate_job_id(j),
                    "number": idx,
                    "title": j.get("title",""),
                    "company": j.get("company",""),
                    "track": j.get("track",""),
                    "score": j.get("score",0),
                    "url": j.get("url",""),
                    "matched_keywords": j.get("matched_keywords",[]),
                    "source": j.get("source",""),
                }
                for idx, j in enumerate(top_jobs, 1)
            ]
        }
        with open(batch_file, "w") as f:
            json.dump(batch, f, indent=2)
        print(f"   [OK] Saved today's job batch to today_jobs.json")
    except Exception as e:
        print(f"   [WARN] Could not save today_jobs.json: {e}")

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


if __name__ == "__main__":
    main()
