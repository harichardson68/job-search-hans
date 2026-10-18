"""
learn_weights.py — learns score adjustments from Hans's own decisions.
2026-10-18. Kept separate from job_search.py (per project rule: learning
logic lives in its own script). job_search.py only READS the output.

Signal:
  positive = "applied"
  negative = "too_senior", "not_interested", "salary_too_low"
  (location/link/onsite/search-page decisions are ignored here — the
   hard filters + update_scoring.py blocklists already handle those)

Features: title words and two-word phrases (e.g. "senior", "architect",
"ai qa"). For each feature: recency-weighted counts (90-day half-life,
so new preferences outweigh old ones), Laplace-smoothed log-odds vs.
the overall apply rate, scaled to points. Only features seen >= 5
weighted times get an adjustment. Output is a readable JSON table so
every learned number can be checked by hand.

Query learning (2026-10-18): every Serper job records the query that
found it. A query is PAUSED when it has surfaced >= 10 jobs, Hans applied
to none, and >= 3 were explicit rejects. Pauses expire after 30 days so
the query gets re-tested. LoadRunner/performance queries are never
paused — that market is scarce and it's the top-priority track.

Output: json_files/learned_adjustments.json
Run:    python learn_weights.py        (also called by run_update_scoring.bat)
"""
import json, math, os, re, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(HERE, "json_files")
DECISIONS = os.path.join(JSON_DIR, "job_decisions.json")
OUT = os.path.join(JSON_DIR, "learned_adjustments.json")

POS = {"applied"}
NEG = {"too_senior", "not_interested", "salary_too_low"}
HALF_LIFE_DAYS = 90
MIN_SUPPORT = 5.0
SCALE = 8.0            # points per unit of log-odds
MAX_UP, MAX_DOWN = 10, -15

STOP = {"and", "the", "for", "with", "remote", "job", "jobs", "hiring", "position",
        "role", "usa", "united", "states", "full", "time", "contract", "w2",
        "dice", "com", "lever", "greenhouse", "indeed", "id", "at", "in", "of", "to"}

def features(title):
    t = re.sub(r"[^a-z0-9+ ]", " ", title.lower())
    t = re.split(r"\s+-\s+|\s+at\s+| \| ", t)[0] if t else t
    words = [w for w in t.split() if len(w) >= 2 and w not in STOP and not w.isdigit()]
    feats = set(w for w in words if len(w) >= 3 or w in ("ai", "qa", "ml", "sr"))
    feats |= {f"{a} {b}" for a, b in zip(words, words[1:])}
    return feats

def main():
    data = json.load(open(DECISIONS, encoding="utf-8"))
    now = datetime.now()
    pos, neg = {}, {}
    tot_p = tot_n = 0.0
    for day, recs in data.items():
        try:
            age = (now - datetime.strptime(day[:10], "%Y-%m-%d")).days
        except ValueError:
            continue
        w = 0.5 ** (age / HALF_LIFE_DAYS)
        for r in recs:
            d = r.get("decision")
            if d not in POS and d not in NEG:
                continue
            bucket = pos if d in POS else neg
            if d in POS: tot_p += w
            else: tot_n += w
            for f in features(r.get("title", "")):
                bucket[f] = bucket.get(f, 0.0) + w
    prior = math.log((tot_p + 1) / (tot_n + 1))
    table = {}
    for f in set(pos) | set(neg):
        p, n = pos.get(f, 0.0), neg.get(f, 0.0)
        if p + n < MIN_SUPPORT:
            continue
        lo = math.log((p + 1) / (n + 1)) - prior
        adj = max(MAX_DOWN, min(MAX_UP, round(SCALE * lo)))
        if adj != 0:
            table[f] = {"adj": adj, "applied_w": round(p, 1), "rejected_w": round(n, 1)}
    # ── query performance ──
    qstats = {}
    for day, recs in data.items():
        for r in recs:
            q = r.get("query")
            if not q:
                continue
            st = qstats.setdefault(q, {"shown": 0, "applied": 0, "rejected": 0, "last_seen": day})
            st["shown"] += 1
            st["last_seen"] = max(st["last_seen"], day)
            if r.get("decision") in POS: st["applied"] += 1
            elif r.get("decision") in NEG: st["rejected"] += 1
    prev = {}
    try:
        prev = json.load(open(OUT, encoding="utf-8")).get("paused_queries", {})
    except Exception:
        pass
    paused = {}
    for q, st in qstats.items():
        protected = any(k in q.lower() for k in ("loadrunner", "vugen", "performance", "jmeter", "neoload", "load test"))
        if protected:
            continue
        if st["shown"] >= 10 and st["applied"] == 0 and st["rejected"] >= 3:
            since = prev.get(q, {}).get("paused_on", now.strftime("%Y-%m-%d"))
            if (now - datetime.strptime(since, "%Y-%m-%d")).days < 30:
                paused[q] = {"paused_on": since, **st,
                             "why": f"{st['shown']} shown, 0 applied, {st['rejected']} rejected"}

    out = {
        "generated_at": now.isoformat(timespec="seconds"),
        "labeled_weighted": {"applied": round(tot_p, 1), "rejected": round(tot_n, 1)},
        "settings": {"half_life_days": HALF_LIFE_DAYS, "min_support": MIN_SUPPORT,
                     "points_per_logodds": SCALE, "clamp": [MAX_DOWN, MAX_UP]},
        "adjustments": dict(sorted(table.items(), key=lambda kv: kv[1]["adj"])),
        "paused_queries": paused,
        "query_stats": dict(sorted(qstats.items(), key=lambda kv: -kv[1]["applied"])),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"[LEARN] {len(table)} title features learned from "
          f"{tot_p:.1f} applied / {tot_n:.1f} rejected (recency-weighted)")
    for f, v in out["adjustments"].items():
        print(f"   {v['adj']:+4d}  {f:<28} applied={v['applied_w']:<5} rejected={v['rejected_w']}")
    print(f"[LEARN] Query tracking: {len(qstats)} queries with history, {len(paused)} paused")
    for q, v in paused.items():
        print(f"   PAUSED  {q[:60]}  ({v['why']})")

if __name__ == "__main__":
    main()
