"""
Hans Richardson - Agent Hub
============================
All four agents in one app:
  1. Job Search (Claudio)   - Job search assistant
  2. Python Tutor (PyCoach) - Learn Python for performance engineering
  3. AI Study (AImentor)    - Study AI/ML concepts
  4. LR to JMeter (JMentor) - Translate LoadRunner to JMeter

SETUP (run once):
    python -m pip install requests pillow

RUN:
    python agent_hub.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import json
import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
JOB_RESULTS_FILE = os.path.join(os.path.dirname(__file__), "job_results.json")
JOB_SCRIPT       = os.path.join(os.path.dirname(__file__), "job_search.py")

# ─────────────────────────────────────────────
# SYSTEM PROMPTS
# ─────────────────────────────────────────────
CLAUDIO_PROMPT = """You are Claudio, a personal job search assistant for Hans Richardson.

Hans is a Senior Performance/QA Test Engineer with 28+ years of experience, expert in LoadRunner (14 years), trained in JMeter and NeoLoad. He is looking for remote work - contract or full-time. He is also pursuing AI Engineering and QA Automation roles.

You help Hans with:
1. Reviewing today's job results
2. Rewriting or customizing cover letters for specific jobs
3. Answering questions about his job search
4. General career advice
5. Interview preparation

Be friendly, concise, and address Hans by name. You have access to his latest job results data which will be provided.
When Hans asks about jobs, reference specific job titles, companies, and scores from the data.
When rewriting cover letters, make them more targeted and powerful using his real experience."""

PYTHON_TUTOR_PROMPT = """You are PyCoach, a Python tutor for Hans Richardson.

Hans is a Senior Performance Engineer with 28+ years of experience. He is currently learning Python through Coursera. He has a strong technical background in LoadRunner, VuGen, SQL, COBOL, and performance engineering. He has already built real Python scripts (an automated job search tool using requests, feedparser, and smtplib).

Your job is to teach Hans Python in the context of performance engineering and automation.

Teaching style:
- Relate Python concepts to things Hans already knows (SQL, scripting, LoadRunner)
- Give practical examples relevant to performance testing, data analysis, and automation
- Keep explanations concise and hands-on
- Provide working code examples he can run immediately
- When he shares code, review it and suggest improvements
- Encourage him - he is further along than he thinks since he already built a real Python app!

Focus areas:
- Python basics (variables, loops, functions, classes)
- File handling and JSON
- requests library (he already uses it!)
- Data analysis with pandas
- Automation scripts
- API integration
- Performance testing with Python (Locust)"""

AI_STUDY_PROMPT = """You are AImentor, an AI/ML study coach for Hans Richardson.

Hans is pursuing AI Engineering through multiple courses including:
- AI Engineer Course: Complete AI Engineer Bootcamp (Udemy)
- IBM Generative AI Engineering Professional Certificate (Coursera)
- Python for Data Science, AI & Development (Coursera)
- Generative AI: Introduction and Applications (Coursera)
- Generative AI: Prompt Engineering Basics (Coursera)
- Introduction to Artificial Intelligence (Coursera)

Hans has already built real AI applications - he built Claudio (an AI job search agent) and a Learning Agent hub using the Claude API. He is further along than he thinks!

Your job is to:
- Quiz Hans on AI/ML concepts from his courses
- Explain complex AI concepts in simple terms
- Connect theory to the practical work he is already doing
- Help him prepare for AI engineering job interviews
- Suggest projects he can build to demonstrate AI skills

Key topics: ML fundamentals, neural networks, LLMs, prompt engineering, RAG, vector databases, embeddings, Python for AI, Generative AI applications."""

LR_TO_JMETER_PROMPT = """You are JMentor, a LoadRunner to JMeter translation expert for Hans Richardson.

Hans has 14 years of expert LoadRunner/VuGen/LRE experience. He completed JMeter training on Coursera in 2025 and is building hands-on proficiency.

Your job is to help Hans translate his deep LoadRunner knowledge into JMeter expertise.

KEY MAPPINGS:
- VuGen Script = JMeter Test Plan (.jmx)
- Virtual User (Vuser) = Thread
- Scenario = Thread Group
- Transactions = Transaction Controller
- Correlation in VuGen = Regular Expression Extractor / CSS Extractor
- LR Parameters = CSV Data Set Config
- Think Time = Timers (Constant, Gaussian, Uniform)
- Rendezvous Point = Synchronizing Timer
- Web Recording = HTTP(S) Test Script Recorder
- LR Analysis = Listeners (View Results Tree, Summary Report)
- Runtime Settings = Thread Group settings
- Web/HTTP Protocol = HTTP Request Sampler
- SiteScope = Backend Listener / InfluxDB + Grafana

Always frame JMeter in terms Hans already knows from LoadRunner. His LR expertise is a massive advantage!"""

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────
BG_DARK      = "#0F1117"
BG_PANEL     = "#1A1D27"
BG_INPUT     = "#22263A"
TEXT_PRIMARY = "#E8EAF6"
TEXT_SEC     = "#8892B0"
TEXT_USER    = "#64FFDA"
TEXT_BOT     = "#E8EAF6"
BORDER       = "#2D3154"
ACCENT_DIM   = "#2A4A8A"
BTN_HOVER    = "#3D6FD4"

TAB_ACCENTS = {
    "Job Search":   "#4F8EF7",
    "Python Tutor": "#4CAF50",
    "AI Study":     "#FF9800",
    "LR to JMeter": "#E91E63",
}

QUICK_BUTTONS = {
    "Job Search": [
        ("Today's Jobs",  "Show me today's job matches"),
        ("Top Match",     "Tell me about the #1 job match"),
        ("Run Search",    "RUN_SEARCH"),
    ],
    "Python Tutor": [
        ("Start Lesson",  "I'm ready to learn. Where should we start based on my background?"),
        ("Code Review",   "Can you review my understanding of the requests library I already use?"),
        ("Quiz Me",       "Quiz me on Python basics"),
    ],
    "AI Study": [
        ("Quiz Me",       "Quiz me on AI/ML concepts for an AI engineer role"),
        ("Explain LLMs",  "Explain how large language models work in simple terms"),
        ("Project Ideas", "Suggest an AI project I can build for my portfolio"),
    ],
    "LR to JMeter": [
        ("Key Differences", "What are the biggest differences between LoadRunner and JMeter?"),
        ("Correlation",     "How do I do correlation in JMeter like I do in VuGen?"),
        ("Test Plan",       "Walk me through creating a basic JMeter test plan"),
    ],
}

AGENT_NAMES = {
    "Job Search":   "Claudio",
    "Python Tutor": "PyCoach",
    "AI Study":     "AImentor",
    "LR to JMeter": "JMentor",
}

WELCOME_MSGS = {
    "Job Search":
        "Hey Hans! I'm Claudio, your job search agent.\n\n"
        "Ask me about today's job matches, cover letters, or click 'Run Search' to search now!\n\n"
        "What can I help you with?",
    "Python Tutor":
        "Hey Hans! I'm PyCoach, your Python tutor.\n\n"
        "I'll teach Python using examples from performance engineering - stuff you already know!\n\n"
        "You've already built a real Python app (your job search tool), so you're further along than you think.\n\n"
        "Where would you like to start?",
    "AI Study":
        "Hey Hans! I'm AImentor, your AI/ML study coach.\n\n"
        "I'll help you master concepts from your Coursera and Udemy courses and prep you for AI engineering roles.\n\n"
        "You already built Claudio using the Claude API - that's real AI engineering!\n\n"
        "What topic would you like to tackle today?",
    "LR to JMeter":
        "Hey Hans! I'm JMentor, your LoadRunner to JMeter guide.\n\n"
        "Your 14 years of LoadRunner expertise is a HUGE advantage - you already know all the concepts, "
        "you just need to learn the JMeter way of doing them.\n\n"
        "Where would you like to start?",
}

# ─────────────────────────────────────────────
# JOB DATA HELPERS
# ─────────────────────────────────────────────
def load_job_results():
    try:
        if os.path.exists(JOB_RESULTS_FILE):
            with open(JOB_RESULTS_FILE, "r") as f:
                data = json.load(f)
            return data.get("top_jobs", []), data.get("generated_at", "")
    except Exception:
        pass
    return [], None

def format_jobs_for_context(jobs, generated_at):
    if not jobs:
        return "No job results found yet. Click 'Run Search' to search now."
    lines = [f"Search ran: {generated_at}", f"Top matches: {len(jobs)}", ""]
    for i, job in enumerate(jobs, 1):
        lines.append(f"Job #{i}: {job.get('title','N/A')} at {job.get('company','N/A')}")
        lines.append(f"  Source: {job.get('source','N/A')} | Score: {job.get('score',0)} pts | Track: {job.get('track','N/A')}")
        lines.append(f"  URL: {job.get('url','N/A')}")
        lines.append(f"  Keywords: {', '.join(job.get('matched_keywords',[]))}")
        lines.append(f"  Description: {job.get('description','')[:200]}")
        cover = job.get('cover_letter','')
        if cover:
            lines.append(f"  Cover Letter: {cover[:300]}...")
        lines.append("")
    return "\n".join(lines)

# ─────────────────────────────────────────────
# CLAUDE API
# ─────────────────────────────────────────────
def ask_claude(system_prompt, history, user_message, tab_name):
    # Inject job data for Claudio tab
    system = system_prompt
    if tab_name == "Job Search":
        jobs, gen = load_job_results()
        system += f"\n\nCURRENT JOB RESULTS:\n{format_jobs_for_context(jobs, gen)}"

    history.append({"role": "user", "content": user_message})
    try:
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1024,
            "system": system,
            "messages": history[-20:]
        }
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers, json=payload, timeout=30
        )
        if resp.status_code == 200:
            reply = resp.json()["content"][0]["text"].strip()
            history.append({"role": "assistant", "content": reply})
            return reply
        else:
            return f"API Error {resp.status_code}: {resp.json().get('error',{}).get('message','Unknown error')}"
    except Exception as e:
        return f"Connection error: {e}"

# ─────────────────────────────────────────────
# CHAT TAB
# ─────────────────────────────────────────────
class ChatTab:
    def __init__(self, parent, name, system_prompt):
        self.name          = name
        self.system_prompt = system_prompt
        self.accent        = TAB_ACCENTS[name]
        self.history       = []

        self.frame = tk.Frame(parent, bg=BG_DARK)

        # Chat area
        self.chat = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=BG_DARK, fg=TEXT_BOT, font=("Courier New", 11),
            relief=tk.FLAT, padx=16, pady=12,
            insertbackground=self.accent,
            selectbackground=ACCENT_DIM, spacing3=4
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        self.chat.tag_configure("user",       foreground=TEXT_USER,   font=("Courier New", 11, "bold"))
        self.chat.tag_configure("bot",        foreground=TEXT_BOT,    font=("Courier New", 11))
        self.chat.tag_configure("system",     foreground=TEXT_SEC,    font=("Courier New", 10, "italic"))
        self.chat.tag_configure("label_user", foreground=self.accent, font=("Courier New", 9, "bold"))
        self.chat.tag_configure("label_bot",  foreground=TEXT_SEC,    font=("Courier New", 9))

        # Quick buttons
        btn_frame = tk.Frame(self.frame, bg=BG_PANEL, pady=6)
        btn_frame.pack(fill=tk.X)
        for label, cmd in QUICK_BUTTONS.get(name, []):
            b = tk.Button(
                btn_frame, text=label, font=("Courier New", 8),
                fg=self.accent, bg=BG_INPUT, relief=tk.FLAT,
                padx=8, pady=4, cursor="hand2",
                command=lambda c=cmd: self._quick_send(c),
                activebackground=ACCENT_DIM, activeforeground=TEXT_PRIMARY,
                bd=1, highlightthickness=1, highlightbackground=BORDER
            )
            b.pack(side=tk.LEFT, padx=(8, 0))

        tk.Frame(self.frame, bg=BORDER, height=1).pack(fill=tk.X)

        # Input
        input_frame = tk.Frame(self.frame, bg=BG_PANEL, pady=10)
        input_frame.pack(fill=tk.X, padx=12, pady=(8, 4))

        self.input = tk.Text(
            input_frame, height=3, font=("Courier New", 11),
            bg=BG_INPUT, fg=TEXT_PRIMARY, relief=tk.FLAT,
            padx=12, pady=8, wrap=tk.WORD,
            insertbackground=self.accent, selectbackground=ACCENT_DIM
        )
        self.input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input.bind("<Return>", self._on_enter)

        tk.Button(
            input_frame, text="Send", font=("Courier New", 10, "bold"),
            fg=TEXT_PRIMARY, bg=self.accent, relief=tk.FLAT,
            padx=14, pady=8, cursor="hand2", command=self._send,
            activebackground=BTN_HOVER, activeforeground=TEXT_PRIMARY
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Label(self.frame, text="Enter to send  |  Shift+Enter for new line",
                 font=("Courier New", 8), fg=TEXT_SEC, bg=BG_PANEL).pack(pady=(0, 6))

        # Welcome
        self._add_message(AGENT_NAMES[name], WELCOME_MSGS[name], "bot")

    def _add_message(self, sender, text, tag):
        self.chat.configure(state=tk.NORMAL)
        ts = datetime.now().strftime("%I:%M %p")
        if sender == "Hans":
            self.chat.insert(tk.END, f"\n  Hans  {ts}\n", "label_user")
        else:
            self.chat.insert(tk.END, f"\n  {sender}  {ts}\n", "label_bot")
        self.chat.insert(tk.END, f"{text}\n", tag)
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _send(self):
        msg = self.input.get("1.0", tk.END).strip()
        if not msg:
            return
        self.input.delete("1.0", tk.END)

        # Special: Run Search button
        if msg == "RUN_SEARCH":
            self._add_message(AGENT_NAMES[self.name],
                "Running job search now... check your email in a few minutes!", "bot")
            threading.Thread(
                target=lambda: subprocess.run([sys.executable, JOB_SCRIPT], capture_output=True),
                daemon=True
            ).start()
            return

        self._add_message("Hans", msg, "user")
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n  thinking...\n", "system")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

        def worker():
            reply = ask_claude(self.system_prompt, self.history, msg, self.name)
            self.chat.configure(state=tk.NORMAL)
            content = self.chat.get("1.0", tk.END)
            idx = content.rfind("\n  thinking...\n")
            if idx >= 0:
                self.chat.delete(
                    f"1.0 + {idx} chars",
                    f"1.0 + {idx + len(chr(10) + '  thinking...' + chr(10))} chars"
                )
            self.chat.configure(state=tk.DISABLED)
            self.frame.after(0, lambda: self._add_message(AGENT_NAMES[self.name], reply, "bot"))

        threading.Thread(target=worker, daemon=True).start()

    def _quick_send(self, cmd):
        self.input.delete("1.0", tk.END)
        self.input.insert("1.0", cmd)
        self._send()

    def _on_enter(self, event):
        if not event.state & 0x1:
            self._send()
            return "break"

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
class AgentHub:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent Hub - Hans Richardson")
        self.root.geometry("580x720")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        # Center on screen
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"580x720+{sw//2 - 290}+{sh//2 - 360}")

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG_PANEL, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="Agent Hub", font=("Courier New", 15, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_PANEL).pack(side=tk.LEFT, padx=16, pady=16)
        tk.Label(header, text="Hans Richardson", font=("Courier New", 9),
                 fg=TEXT_SEC, bg=BG_PANEL).pack(side=tk.LEFT, padx=(4, 0), pady=20)

        # Job count
        jobs, _ = load_job_results()
        badge = f"{len(jobs)} jobs today" if jobs else "no jobs yet"
        tk.Label(header, text=badge, font=("Courier New", 8),
                 fg=TAB_ACCENTS["Job Search"], bg=BG_PANEL).pack(side=tk.RIGHT, padx=16, pady=20)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)

        # Style tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",       background=BG_PANEL, borderwidth=0)
        style.configure("TNotebook.Tab",   background=BG_INPUT, foreground=TEXT_SEC,
                        font=("Courier New", 9, "bold"), padding=[12, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", BG_DARK)],
                  foreground=[("selected", TEXT_PRIMARY)])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # All 4 tabs
        tabs = [
            ("Job Search",   CLAUDIO_PROMPT),
            ("Python Tutor", PYTHON_TUTOR_PROMPT),
            ("AI Study",     AI_STUDY_PROMPT),
            ("LR to JMeter", LR_TO_JMETER_PROMPT),
        ]

        for name, prompt in tabs:
            tab = ChatTab(notebook, name, prompt)
            notebook.add(tab.frame, text=f"  {name}  ")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AgentHub()
    app.run()
