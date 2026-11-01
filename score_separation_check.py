"""Score-separation check (2026-10-31): does the keyword score separate jobs
Hans applied to from jobs he rejected? Run: python score_separation_check.py
AUC 0.5 = coin flip, 1.0 = perfect. Build a classifier only if this is weak
AND better features exist — a classifier trained on this score alone cannot
beat the score itself."""
import json, collections, statistics as st
rows=[r|{"_day":k} for k,v in json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'json_files','job_decisions.json'),encoding='utf-8')).items() for r in v]
def sc(r):
    try: return float(r.get("score"))
    except: return None
POS={"applied"}
FIT={"too_senior","not_interested","salary_too_low","onsite"}   # real jobs, judged on fit
JUNK={"not_in_us","search_page","bad_link"}                      # filter failures, not fit
def auc(pos,neg):
    if not pos or not neg: return None
    w=sum((p>n)+0.5*(p==n) for p in pos for n in neg); return w/(len(pos)*len(neg))
def q(xs): xs=sorted(xs); return (xs[len(xs)//4], st.median(xs), xs[3*len(xs)//4]) if xs else None
for label,sub in [("ALL",rows)]+[(t,[r for r in rows if r.get("track")==t]) for t,_ in collections.Counter(r.get("track") for r in rows).most_common(4)]:
    P=[sc(r) for r in sub if r.get("decision") in POS and sc(r) is not None]
    F=[sc(r) for r in sub if r.get("decision") in FIT and sc(r) is not None]
    J=[sc(r) for r in sub if r.get("decision") in JUNK and sc(r) is not None]
    a1=auc(P,F); a2=auc(P,J)
    print(f"{label[:28]:28} applied n={len(P):3} q={q(P)}  fit-reject n={len(F):3} q={q(F)}  AUC(applied>fit-reject)={a1 and round(a1,2)}  AUC(applied>junk)={a2 and round(a2,2)}")
# threshold view for ALL
P=sorted(sc(r) for r in rows if r.get("decision") in POS and sc(r) is not None)
N=[sc(r) for r in rows if r.get("decision") in FIT|JUNK and sc(r) is not None]
print("\nthreshold  keeps-applied  removes-rejects")
for t in (30,40,50,60,80,100,120):
    print(f"  >={t:3}     {sum(p>=t for p in P):2}/{len(P)}         {sum(n<t for n in N):3}/{len(N)}")
# fit_tier
print("\nfit_tier vs decision (reviewed only):")
ct=collections.defaultdict(collections.Counter)
for r in rows:
    if r.get("decision") in POS|FIT|JUNK: ct[r.get("fit_tier")][ "applied" if r["decision"] in POS else "rejected"]+=1
for k,v in ct.items(): print(f"  {str(k):14} applied={v['applied']:3} rejected={v['rejected']:3}")
print("\nreviewed date range:", min(r["_day"] for r in rows if r.get("decision") in POS), "->", max(r["_day"] for r in rows if r.get("decision") in POS))
