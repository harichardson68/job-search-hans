// Hans Richardson - Updated Resume Generator
// 
// SETUP (run once):
//   npm install docx
//
// RUN:
//   node generate_resume.js
//
// OUTPUT:
//   Hans-Richardson-Performance_Engineer.docx

const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  LevelFormat, HeadingLevel, BorderStyle, UnderlineType
} = require("docx");
const fs = require("fs");

// ─── HELPERS ───────────────────────────────────────────────
const FONT = "Arial";

function heading1(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 28, bold: true, color: "1F3864" })],
    spacing: { before: 240, after: 80 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "1F3864", space: 1 } },
  });
}

function jobTitle(title, company, dates) {
  return new Paragraph({
    children: [
      new TextRun({ text: title, font: FONT, size: 24, bold: true }),
      new TextRun({ text: "  |  ", font: FONT, size: 24, color: "888888" }),
      new TextRun({ text: company, font: FONT, size: 24, bold: true, color: "1F3864" }),
      new TextRun({ text: "  |  ", font: FONT, size: 24, color: "888888" }),
      new TextRun({ text: dates, font: FONT, size: 22, italics: true, color: "555555" }),
    ],
    spacing: { before: 200, after: 60 },
  });
}

function bullet(text, numbering) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
    spacing: { before: 40, after: 40 },
  });
}

function body(text, options = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 22, ...options })],
    spacing: { before: 60, after: 60 },
  });
}

function skillRow(label, value) {
  return new Paragraph({
    children: [
      new TextRun({ text: label + ": ", font: FONT, size: 22, bold: true }),
      new TextRun({ text: value, font: FONT, size: 22 }),
    ],
    spacing: { before: 40, after: 40 },
  });
}

function spacer() {
  return new Paragraph({ children: [new TextRun("")], spacing: { before: 40, after: 40 } });
}

// ─── DOCUMENT ──────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1260, bottom: 1080, left: 1260 },
      },
    },
    children: [

      // ── NAME & CONTACT ──
      new Paragraph({
        children: [new TextRun({ text: "Hans Richardson", font: FONT, size: 52, bold: true, color: "1F3864" })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
      }),
      new Paragraph({
        children: [new TextRun({ text: "Senior Performance / QA Test Engineer", font: FONT, size: 28, color: "555555", italics: true })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
      }),
      new Paragraph({
        children: [new TextRun({
          text: "Lee's Summit, MO  |  Open to Remote Contract & Full-Time  |  linkedin.com/in/hans-richardson  |  harichardson68@gmail.com",
          font: FONT, size: 20, color: "555555",
        })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
      }),

      // ── PROFESSIONAL SUMMARY ──
      heading1("Professional Summary"),
      body(
        "Performance Engineer with 28+ years of experience across government, telecom, banking, and logistics. Expert in LoadRunner (VuGen/LRE) with 14 years of production experience designing and executing load, stress, scalability, and endurance tests across complex, heavily integrated enterprise environments — validating end-to-end transaction flows across REST/SOAP APIs, back-end services, and third-party system dependencies under simulated production load. Trained in JMeter and NeoLoad. Proficient in Agile/Scrum, AWS, Kubernetes, and observability tools (Splunk, AppDynamics, Prometheus, Grafana). Built a real-world AI-powered automation system using Python and the Claude API. Actively pursuing AI engineering. Early career COBOL/CICS programmer with 7 years of mainframe development experience (Yellow Freight, Sprint). Open to remote contract and full-time roles."
      ),

      spacer(),

      // ── CORE COMPETENCIES ──
      heading1("Core Competencies"),
      body(
        "LoadRunner / VuGen / LRE (14 yrs)  •  JMeter (trained)  •  NeoLoad (trained)  •  Performance & Load Testing  •  Integration & API Performance Testing  •  End-to-End Transaction Validation  •  Workload Modeling  •  SLA Compliance  •  Agile/Scrum  •  AWS  •  Kubernetes  •  CI/CD  •  Splunk  •  AppDynamics  •  Prometheus  •  Grafana  •  REST APIs  •  SQL  •  Python  •  AI Agent Development  •  Prompt Engineering  •  Root Cause Analysis  •  Selenium"
      ),

      spacer(),

      // ── RELEVANT EXPERIENCE ──
      heading1("Relevant Experience"),

      jobTitle("Sr. Performance / QA Test Engineer (Contract)", "United States Department of Agriculture (USDA)", "Jan 2021 – Sep 2025"),
      body("Contract ended Sep 2025 due to federal funding cuts. Public Trust clearance held.", { italics: true, color: "555555" }),
      bullet("Designed and executed LRE/VuGen scripts (C-based) across Web HTTP/HTML, TruClient, REST, and Web Services protocols, including script enhancements, correlation, and authentication troubleshooting (LDAP, SAML, SSO) in an Agile/Scrum framework."),
      bullet("Led performance testing for AWS/Kubernetes migration — validated scalability, ensured SLA compliance (<5s transactions, <2s services), increased throughput 40% and thread count 30-40%."),
      bullet("Integrated AppDynamics, Prometheus/Grafana, AWS X-Ray, Splunk, and SiteScope for observability and root-cause analysis; reduced defect resolution time 35%."),
      bullet("Performed performance testing across heavily integrated, multi-system environments — validating end-to-end transaction flows across REST/SOAP APIs, back-end services, and third-party system dependencies to ensure stability and SLA compliance under load."),
      bullet("Increased defect detection coverage 25% and mentored junior engineers in performance engineering best practices."),

      spacer(),

      jobTitle("Programmer / Software Engineer", "Sprint / Embarq / CenturyLink", "Jan 1999 – Dec 2017"),
      bullet("LoadRunner specialist for 9 years (2008-2017); developed and enhanced C-based VuGen scripts, scaled systems to 12,000+ TPS, increased throughput 35%, and maintained SLA compliance across Web, SAP, Citrix, and TruClient protocols in Agile/Waterfall environments."),
      bullet("Supported SAP CRM, ERP, BRIM, and FI modules with load, stress, volume, and scalability testing."),
      bullet("Conducted performance testing across complex, tightly integrated enterprise systems — including SAP, billing platforms, and internal APIs — identifying cross-system bottlenecks and validating data flow integrity under simulated production load."),
      bullet("Built LoadRunner automation frameworks reducing data preparation time 50% and improving defect detection 30%."),
      bullet("Additional roles: Test Environment Operations (3 yrs), PeopleSoft Administration (2 yrs), COBOL/CICS Programmer (5 yrs)."),

      spacer(),

      jobTitle("Programmer Analyst", "Yellow Freight", "Jan 1997 – Sep 1999"),
      bullet("Developed and maintained COBOL, DB2, JCL, and CICS mainframe applications; converted from intern to full-time based on strong performance."),

      spacer(),

      // ── ADDITIONAL EXPERIENCE ──
      heading1("Additional Experience"),

      jobTitle("Warehouse Associate", "Amazon Warehouse", "Dec 2025 – Present"),
      bullet("Consistently meet or exceed productivity targets across stowing, picking, packing, and inventory workflows."),

      spacer(),

      jobTitle("Construction & Commercial Cleaning", "Classic Cleaning", "Dec 2017 – Dec 2020"),
      body("Following layoff from CenturyLink, transitioned to self-employment while pursuing re-entry into IT.", { italics: true, color: "555555" }),

      spacer(),

      // ── PROJECTS ──
      heading1("Projects"),

      jobTitle("AI-Powered Job Search Automation System", "Personal Project", "2026"),
      bullet("Built a Python automation system searching 15 job boards, scoring results by relevance, and generating tailored cover letters via the Claude API (Anthropic)."),
      bullet("Deployed a 4-agent desktop hub (Agent Hub) with Claude-powered assistants for job search, Python tutoring, AI/ML study, and LoadRunner-to-JMeter translation."),
      bullet("Automated daily execution via Windows Task Scheduler with Gmail SMTP email delivery of ranked matches and AI-generated cover letters."),
      bullet("Engineered custom filtering pipeline including non-US location detection, URL blacklisting, relative date parsing, cross-source deduplication, and a multi-track weighted scoring algorithm to ensure only relevant, high-quality US remote positions are surfaced."),

      spacer(),

      // ── EDUCATION ──
      heading1("Education"),
      body("Park University – Parkville, MO  |  BS Computer Information Science, 1996  |  BA Marketing, 1992"),

      spacer(),

      // ── CERTIFICATIONS ──
      heading1("Certifications & Training"),
      bullet("LoadRunner – HP, 2010  |  JMeter – Coursera, 2025  |  Selenium – Coursera, 2025  |  API Performance Testing – Udemy, 2023"),
      bullet("AWS Cloud Practitioner – Udemy, 2025  |  Grafana & Prometheus (applied, USDA)"),
      bullet("AI Engineer Bootcamp – Udemy, 2025  |  IBM Generative AI Engineering – Coursera, 2025-2026  |  Python for AI – Coursera, 2025  |  Prompt Engineering – Coursera, 2025"),

      spacer(),

      // ── SKILLS ──
      heading1("Technical Skills"),
      skillRow("Performance Tools", "LoadRunner / VuGen / LRE (14 yrs, expert)  |  JMeter (trained)  |  NeoLoad (trained)  |  Blazemeter  |  Selenium"),
      skillRow("Monitoring", "AppDynamics (equiv. Dynatrace)  |  Grafana  |  Prometheus  |  Splunk  |  SiteScope  |  AWS X-Ray"),
      skillRow("Cloud & DevOps", "AWS  |  Kubernetes  |  GitHub  |  Jira  |  Confluence  |  Agile/Scrum  |  CI/CD"),
      skillRow("Clearance", "Public Trust (held during USDA federal contract, 2021-2025)"),
      skillRow("AI & Automation", "Claude API  |  Prompt Engineering  |  AI Agent Development  |  REST API Integration  |  Python"),
      skillRow("Programming", "C (VuGen/LoadRunner scripting)  |  Python  |  SQL  |  JavaScript  |  COBOL  |  Oracle  |  DB2  |  CICS  |  JCL"),



    ],
  }],
});

// ─── OUTPUT ────────────────────────────────────────────────
Packer.toBuffer(doc).then((buffer) => {
  const filename = "Hans-Richardson-Performance_Engineer.docx";
  fs.writeFileSync(filename, buffer);
  console.log("✅ Resume saved: " + filename);
}).catch(err => {
  console.error("❌ Error generating resume:", err);
});
