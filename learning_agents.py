"""
Hans Richardson - Learning Agents
===================================
Three learning agents in one app:
  1. Python Tutor - Learn Python for performance engineering
  2. AI Study Agent - Study AI/ML concepts from your courses
  3. LoadRunner to JMeter - Translate LR knowledge to JMeter

SETUP (run once):
    python -m pip install requests pillow

RUN:
    python learning_agents.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ─────────────────────────────────────────────
# SYSTEM PROMPTS
# ─────────────────────────────────────────────
PYTHON_TUTOR_PROMPT = """You are PyCoach, a Python tutor for Hans Richardson.

Hans is a Senior Performance Engineer with 28+ years of experience. He is currently learning Python through Coursera. He has a strong technical background in LoadRunner, VuGen, SQL, COBOL, and performance engineering.

Your job is to teach Hans Python in the context of performance engineering and automation. 

Teaching style:
- Relate Python concepts to things Hans already knows (SQL, scripting, LoadRunner)
- Give practical examples relevant to performance testing, data analysis, and automation
- Keep explanations concise and hands-on
- Provide working code examples he can run immediately
- When he shares code, review it and suggest improvements
- Build on previous lessons in the conversation
- Encourage him when he gets things right

Focus areas:
- Python basics (variables, loops, functions, classes)
- File handling and JSON (relevant to job_results.json he already uses)
- requests library (he already uses it in his job search!)
- Data analysis with pandas
- Automation scripts
- API integration
- Performance testing with Python (Locust as alternative to JMeter)

Start by asking where he is in his Python journey if you don't know yet."""

AI_STUDY_PROMPT = """You are AImentor, an AI/ML study coach for Hans Richardson.

Hans is pursuing AI Engineering through multiple Coursera and Udemy courses including:
- AI Engineer Course: Complete AI Engineer Bootcamp (Udemy)
- IBM Generative AI Engineering Professional Certificate (Coursera)
- Python for Data Science, AI & Development (Coursera)
- Generative AI: Introduction and Applications (Coursera)
- Generative AI: Prompt Engineering Basics (Coursera)
- Introduction to Artificial Intelligence (Coursera)

Hans already has hands-on experience building AI-powered tools (he built Claudio, an AI job search agent using the Claude API).

Your job is to:
- Quiz Hans on AI/ML concepts from his courses
- Explain complex AI concepts in simple terms
- Connect theory to the practical work he's already doing
- Help him prepare for AI engineering job interviews
- Suggest projects he can build to demonstrate AI skills
- Track what topics he's covered and what needs more work

Key topics to cover:
- Machine learning fundamentals (supervised, unsupervised, reinforcement)
- Neural networks and deep learning
- Large Language Models (LLMs) and how they work
- Prompt engineering (he's already doing this!)
- RAG (Retrieval Augmented Generation)
- Vector databases and embeddings
- AI APIs (Claude, OpenAI, etc.) - he's already using these
- Python for AI (he's learning this in parallel)
- Generative AI applications and use cases

Be encouraging - Hans is further along than he thinks since he's already building real AI applications!"""

LR_TO_JMETER_PROMPT = """You are JMentor, a LoadRunner to JMeter translation expert for Hans Richardson.

Hans has 14 years of expert LoadRunner/VuGen/LRE experience. He completed JMeter training on Coursera in 2025 and is building hands-on proficiency to add JMeter to his toolset alongside LoadRunner.

Your job is to help Hans translate his deep LoadRunner knowledge into JMeter expertise by:
- Mapping LoadRunner concepts directly to JMeter equivalents
- Explaining JMeter features in terms Hans already understands from LoadRunner
- Providing JMeter scripts/configurations that mirror what he'd do in VuGen
- Quizzing him on JMeter concepts
- Helping him build JMeter test plans from scratch
- Explaining differences and when to use each tool

KEY MAPPINGS to teach:
- VuGen Script = JMeter Test Plan (.jmx file)
- Virtual User (Vuser) = Thread
- Scenario = Thread Group
- Controller = Logic Controller
- LoadRunner Transactions = JMeter Transaction Controller
- Correlation in VuGen = Regular Expression Extractor / CSS Extractor in JMeter
- LR Parameters = JMeter CSV Data Set Config
- LR Think Time = JMeter Timers (Constant, Gaussian, Uniform)
- LR Rendezvous Point = JMeter Synchronizing Timer
- LR Web Recording = JMeter HTTP(S) Test Script Recorder
- LR Analysis = JMeter Listeners (View Results Tree, Summary Report, etc.)
- LR Runtime Settings = JMeter Thread Group settings
- LR Protocols (Web/HTTP) = JMeter HTTP Request Sampler
- LR REST/API = JMeter HTTP Request with JSON Extractor
- SiteScope = JMeter Backend Listener / InfluxDB + Grafana

Always frame JMeter in terms Hans already knows from LoadRunner. His LR expertise is a massive advantage!"""

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────
BG_DARK      = "#0F1117"
BG_PANEL     = "#1A1D27"
BG_INPUT     = "#22263A"
ACCENT       = "#4F8EF7"
ACCENT_DIM   = "#2A4A8A"
TEXT_PRIMARY = "#E8EAF6"
TEXT_SEC     = "#8892B0"
TEXT_USER    = "#64FFDA"
TEXT_BOT     = "#E8EAF6"
BORDER       = "#2D3154"
BTN_HOVER    = "#3D6FD4"

TAB_COLORS = {
    "Python Tutor":       "#4CAF50",
    "AI Study":           "#FF9800",
    "LR to JMeter":       "#E91E63",
}

# ─────────────────────────────────────────────
# CLAUDE API
# ─────────────────────────────────────────────
def ask_claude(system_prompt, history, user_message):
    history.append({"role": "user", "content": user_message})
    try:
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": history[-20:]
        }
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )
        if resp.status_code == 200:
            reply = resp.json()["content"][0]["text"].strip()
            history.append({"role": "assistant", "content": reply})
            return reply
        else:
            return f"API Error {resp.status_code}"
    except Exception as e:
        return f"Connection error: {e}"

# ─────────────────────────────────────────────
# CHAT TAB
# ─────────────────────────────────────────────
class ChatTab:
    def __init__(self, parent, name, system_prompt, accent_color, welcome_msg):
        self.name          = name
        self.system_prompt = system_prompt
        self.accent_color  = accent_color
        self.history       = []

        self.frame = tk.Frame(parent, bg=BG_DARK)

        # Chat area
        self.chat = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=BG_DARK, fg=TEXT_BOT, font=("Courier New", 11),
            relief=tk.FLAT, padx=16, pady=12,
            insertbackground=accent_color,
            selectbackground=ACCENT_DIM,
            spacing3=4
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        self.chat.tag_configure("user",       foreground=TEXT_USER,     font=("Courier New", 11, "bold"))
        self.chat.tag_configure("bot",        foreground=TEXT_BOT,      font=("Courier New", 11))
        self.chat.tag_configure("system",     foreground=TEXT_SEC,      font=("Courier New", 10, "italic"))
        self.chat.tag_configure("label_user", foreground=accent_color,  font=("Courier New", 9, "bold"))
        self.chat.tag_configure("label_bot",  foreground=TEXT_SEC,      font=("Courier New", 9))

        # Quick buttons (unique per tab)
        self._build_quick_buttons()

        # Divider
        tk.Frame(self.frame, bg=BORDER, height=1).pack(fill=tk.X)

        # Input area
        input_frame = tk.Frame(self.frame, bg=BG_PANEL, pady=10)
        input_frame.pack(fill=tk.X, padx=12, pady=(8, 4))

        self.input = tk.Text(
            input_frame, height=3, font=("Courier New", 11),
            bg=BG_INPUT, fg=TEXT_PRIMARY, relief=tk.FLAT,
            padx=12, pady=8, wrap=tk.WORD,
            insertbackground=accent_color,
            selectbackground=ACCENT_DIM
        )
        self.input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input.bind("<Return>", self._on_enter)

        send_btn = tk.Button(
            input_frame, text="Send", font=("Courier New", 10, "bold"),
            fg=TEXT_PRIMARY, bg=accent_color, relief=tk.FLAT,
            padx=14, pady=8, cursor="hand2",
            command=self._send,
            activebackground=BTN_HOVER, activeforeground=TEXT_PRIMARY
        )
        send_btn.pack(side=tk.RIGHT, padx=(8, 0))

        tk.Label(self.frame, text="Enter to send  |  Shift+Enter for new line",
                 font=("Courier New", 8), fg=TEXT_SEC, bg=BG_PANEL).pack(pady=(0, 6))

        # Welcome message
        self._add_message(name, welcome_msg, "bot")

    def _build_quick_buttons(self):
        btn_frame = tk.Frame(self.frame, bg=BG_PANEL, pady=6)
        btn_frame.pack(fill=tk.X)

        quick = {
            "Python Tutor": [
                ("Start Lesson", "I'm ready to learn Python. Where should we start based on my background?"),
                ("Code Review", "Can you review my understanding of the requests library I'm already using?"),
                ("Quiz Me", "Quiz me on Python basics"),
            ],
            "AI Study": [
                ("Quiz Me", "Quiz me on AI/ML concepts I should know for an AI engineer role"),
                ("Explain LLMs", "Explain how large language models work in simple terms"),
                ("Project Ideas", "Suggest an AI project I can build to add to my portfolio"),
            ],
            "LR to JMeter": [
                ("Key Differences", "What are the biggest differences between LoadRunner and JMeter?"),
                ("Correlation", "How do I do correlation in JMeter like I do in VuGen?"),
                ("Test Plan", "Walk me through creating a basic JMeter test plan"),
            ],
        }

        for label, cmd in quick.get(self.name, []):
            b = tk.Button(
                btn_frame, text=label, font=("Courier New", 8),
                fg=self.accent_color, bg=BG_INPUT, relief=tk.FLAT,
                padx=8, pady=4, cursor="hand2",
                command=lambda c=cmd: self._quick_send(c),
                activebackground=ACCENT_DIM, activeforeground=TEXT_PRIMARY,
                bd=1, highlightthickness=1, highlightbackground=BORDER
            )
            b.pack(side=tk.LEFT, padx=(8, 0))

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
        self._add_message("Hans", msg, "user")

        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n  thinking...\n", "system")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

        def worker():
            reply = ask_claude(self.system_prompt, self.history, msg)
            self.chat.configure(state=tk.NORMAL)
            content = self.chat.get("1.0", tk.END)
            idx = content.rfind("\n  thinking...\n")
            if idx >= 0:
                self.chat.delete(f"1.0 + {idx} chars",
                                 f"1.0 + {idx + len(chr(10) + '  thinking...' + chr(10))} chars")
            self.chat.configure(state=tk.DISABLED)
            agent_name = {
                "Python Tutor": "PyCoach",
                "AI Study":     "AImentor",
                "LR to JMeter": "JMentor",
            }.get(self.name, self.name)
            self.frame.after(0, lambda: self._add_message(agent_name, reply, "bot"))

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
class LearningAgents:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hans Richardson - Learning Agents")
        self.root.geometry("560x700")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        # Position bottom left (so it doesn't overlap Claudio)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"560x700+20+{sh-740}")

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG_PANEL, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="Learning Agents", font=("Courier New", 14, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_PANEL).pack(side=tk.LEFT, padx=16, pady=16)
        tk.Label(header, text="Hans Richardson", font=("Courier New", 9),
                 fg=TEXT_SEC, bg=BG_PANEL).pack(side=tk.RIGHT, padx=16, pady=20)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)

        # Style tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",           background=BG_PANEL, borderwidth=0)
        style.configure("TNotebook.Tab",       background=BG_INPUT, foreground=TEXT_SEC,
                        font=("Courier New", 10), padding=[16, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", BG_DARK)],
                  foreground=[("selected", TEXT_PRIMARY)])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Python Tutor
        py_tab = ChatTab(
            notebook, "Python Tutor", PYTHON_TUTOR_PROMPT,
            TAB_COLORS["Python Tutor"],
            "Hey Hans! I'm PyCoach, your Python tutor.\n\nI'll teach you Python in the context of performance engineering — using examples you already understand from LoadRunner, SQL, and scripting.\n\nWhere are you in your Python journey so far? Have you written any Python code yet?"
        )
        notebook.add(py_tab.frame, text="  Python Tutor  ")

        # Tab 2: AI Study
        ai_tab = ChatTab(
            notebook, "AI Study", AI_STUDY_PROMPT,
            TAB_COLORS["AI Study"],
            "Hey Hans! I'm AImentor, your AI/ML study coach.\n\nI'll help you master the concepts from your Coursera and Udemy courses and prepare you for AI engineering roles.\n\nHere's something encouraging - you've already built Claudio, a real AI agent using the Claude API. You're further along than you think!\n\nWhat topic from your courses would you like to start with today?"
        )
        notebook.add(ai_tab.frame, text="  AI Study  ")

        # Tab 3: LR to JMeter
        lr_tab = ChatTab(
            notebook, "LR to JMeter", LR_TO_JMETER_PROMPT,
            TAB_COLORS["LR to JMeter"],
            "Hey Hans! I'm JMentor, your LoadRunner to JMeter guide.\n\nYour 14 years of LoadRunner expertise is actually a HUGE advantage when learning JMeter - you already understand all the performance testing concepts, you just need to learn the JMeter way of doing them.\n\nWhere would you like to start? I can walk you through how JMeter maps to LoadRunner, or we can dive straight into building a test plan!"
        )
        notebook.add(lr_tab.frame, text="  LR to JMeter  ")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LearningAgents()
    app.run()
