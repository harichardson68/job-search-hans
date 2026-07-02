import json
import sys

PATH = r"C:\Users\haric\Jobsearch\job_decisions.json"
APPLY = "--apply" in sys.argv

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

total_before = sum(len(v) for v in data.values())
removed = 0

for date in sorted(data.keys()):
    records = data[date]
    clean = [r for r in records if "job_id" in r]
    bad_count = len(records) - len(clean)
    if bad_count:
        print(f"{date}: removing {bad_count} of {len(records)}")
        removed += bad_count
        data[date] = clean

# Drop any date that's now empty
data = {d: v for d, v in data.items() if v}

total_after = sum(len(v) for v in data.values())

print()
print(f"Total before: {total_before}")
print(f"Removed:      {removed}")
print(f"Total after:  {total_after}")

if APPLY:
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("\nAPPLIED — file written.")
else:
    print("\nDRY RUN — no changes written. Re-run with --apply to write changes.")