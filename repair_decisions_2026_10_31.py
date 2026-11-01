"""One-off repair (2026-10-31) of job_decisions.json from the Google Sheet.
Fixes records hit by three update_scoring.py bugs:
  1. form labels that didn't match DECISION_MAP were saved as "other"
  2. late form submissions matched by submission date + job number -> wrong job
  3. G/S-prefixed job numbers were dropped
Token rows are matched by job_id. Never touches decisions made in the chat
backlog review (raw_decision starts with 'backlog-review').
Usage: python repair_decisions_2026_10_31.py          (dry run)
       python repair_decisions_2026_10_31.py --apply
"""
import json, sys, ast, re, os, warnings, collections
from datetime import datetime
warnings.filterwarnings("ignore")
from googleapiclient.discovery import build
from google.oauth2 import service_account
HERE=os.path.dirname(os.path.abspath(__file__)); J=os.path.join(HERE,"json_files")
src=open(os.path.join(HERE,"update_scoring.py"),encoding="utf-8").read(); ns={"re":re,"os":os,"json":json,"JSON_DIR":J}
tree=ast.parse(src)
keep=[n for n in tree.body if (isinstance(n,ast.Assign) and any(getattr(t,'id','') in ('DECISION_MAP','_DECISION_PREFIXES') for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name in ('normalize_decision','parse_job_number','load_token_index'))]
exec(compile(ast.Module(keep,[]),'u','exec'),ns)
norm, pnum, tok_index = ns['normalize_decision'], ns['parse_job_number'], ns['load_token_index']()
c=service_account.Credentials.from_service_account_file(os.path.join(J,'google_credentials.json'),scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
rows=build("sheets","v4",credentials=c).spreadsheets().values().get(spreadsheetId="1nv9XmVWJUvJ08t6ldjJFYhZ25MfTLhUAAph3CrSzlmE",range="Form Responses 1!A:H").execute().get("values",[])[1:]
P=os.path.join(J,"job_decisions.json"); d=json.load(open(P,encoding="utf-8"))
by_id=collections.defaultdict(list)
for day,v in d.items():
    for r in v: by_id[r.get("job_id")].append((day,r))
protected=lambda r: str(r.get("raw_decision","")).startswith("backlog-review")
truth={}   # job_id -> (decision, raw)
wrong=[]   # records a late token row was misrouted onto
for row in rows:
    row=list(row)+[""]*(8-len(row)); raw=row[2] or row[7]; tok=row[4].strip()
    if not tok or not raw.strip() or tok not in tok_index: continue
    jid=tok_index[tok].get("job_id"); truth[jid]=(norm(raw),raw)
    day=datetime.strptime(row[0].split()[0],"%m/%d/%Y").strftime("%Y-%m-%d"); num=pnum(row[1])
    for e in d.get(day,[]):
        if (str(e.get("number"))==str(num) and e.get("job_id")!=jid and e.get("raw_decision")==raw
                and e.get("title","").strip().lower()!=tok_index[tok].get("title","").strip().lower()):  # same job, two ids
            wrong.append(e.get("job_id"))
changes=collections.Counter(); log=[]
for jid,(dec,raw) in truth.items():
    for day,r in by_id.get(jid,[]):
        if protected(r) or r.get("decision")==dec: continue
        if r.get("decision") in ("no_response",None,"","other"):
            log.append(f"  set   {day} {r.get('title','')[:50]!r}: {r.get('decision')} -> {dec}")
            changes[f"{r.get('decision')}->{dec}"]+=1
            r["decision"]=dec; r["raw_decision"]=raw; r["repaired"]="2026-10-31 token"
for jid in set(wrong)-set(truth):
    for day,r in by_id.get(jid,[]):
        if protected(r) or r.get("decision") in ("no_response",None,""): continue
        log.append(f"  reset {day} {r.get('title','')[:50]!r}: {r.get('decision')} -> no_response (decision belonged to another job)")
        changes[f"{r.get('decision')}->no_response(misrouted)"]+=1
        r["decision"]="no_response"; r["raw_decision"]=""; r["repaired"]="2026-10-31 misrouted"
print("\n".join(log)); print("\nSUMMARY:",dict(changes),"total",sum(changes.values()))
if "--apply" in sys.argv:
    json.dump(d,open(P,"w",encoding="utf-8"),indent=2); print("APPLIED")
else: print("dry run — nothing written")
