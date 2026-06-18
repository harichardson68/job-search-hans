"""
analyze_decisions.py — Hans Richardson Job Search
===================================================
EXPLORATORY K-Means clustering over job_decisions.json.

This is NOT a production classifier. It's a one-time (or run-occasionally)
data audit: "does my decision history have any natural groupings worth
noticing?" Think of it like a smoke test before a load test — it answers
"is there signal in this data at all?" before you'd ever invest in a real
trained model that auto-skips jobs for you.

WHAT THIS SCRIPT ACTUALLY DOES, IN PLAIN TERMS
------------------------------------------------
1. Reads every decision record across all dates in job_decisions.json.
2. Turns each record into a row of NUMBERS (the "features") — things
   like score, which track it was in, which source it came from, what
   fit_tier it got (if any). K-Means can only work with numbers, so
   text fields like "AI Engineering" get converted to numeric codes.
3. Feeds those rows to K-Means, which groups similar-looking decisions
   into K clusters WITHOUT being told what the "right" grouping is —
   it just finds rows that are numerically close to each other.
4. Prints out what's actually IN each cluster (the dominant track,
   typical score range, most common decision/reason) so you — a human
   — can look at it and ask "what do these have in common, and is that
   useful?"

K-Means doesn't know what a "good cluster" means. It just minimizes
distance. The interpretation step (step 4 here, but really your job
after reading the output) is where the actual insight comes from.

SCHEMA NOTE — built for where your data is headed, not just where it
is today. As of this writing, your 216 decisions are ALL from the old
3-track schema (AI Engineering / Performance Engineering / QA
Automation) with fit_tier essentially never populated. This script
treats every feature defensively: missing/empty values become an
explicit "Unknown" category rather than crashing or silently being
dropped. So today, fit_tier and the Gap Track ("Remote Income Floor")
will contribute close to zero signal (because you don't have that
data yet) — but as soon as decisions on Gap Track / Stretch Fit jobs
start accumulating, those same feature columns light up automatically.
No changes to this script needed when that happens.

USAGE
-----
    python analyze_decisions.py                  # auto-picks k, runs once
    python analyze_decisions.py --k 5             # force a specific k
    python analyze_decisions.py --min-k 2 --max-k 8   # search this range instead

OUTPUT
------
Prints a per-cluster summary to the console. Also writes
cluster_analysis_<date>.json with the full breakdown, in case you want
to dig into a specific cluster's actual job titles later.
"""

import os
import sys
import json
import argparse
from collections import Counter
from datetime import date

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DECISIONS_FILE = os.path.join(SCRIPT_DIR, "job_decisions.json")
TODAY = date.today().isoformat()
OUTPUT_FILE = os.path.join(SCRIPT_DIR, f"cluster_analysis_{TODAY}.json")

KMEANS_EXPLORATORY = 100   # data-audit milestone (this script's intended trigger point)
KMEANS_PRODUCTION  = 300   # full supervised-classifier milestone (future, separate effort)


# ─── LOAD & FLATTEN ──────────────────────────────────────────
def load_all_decisions():
    """Read job_decisions.json and flatten the date->list structure into
    one flat list of decision records, each tagged with its date."""
    if not os.path.exists(DECISIONS_FILE):
        print(f"[ERROR] {DECISIONS_FILE} not found.")
        sys.exit(1)

    with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for date_str, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            rec = dict(item)
            rec["_date"] = date_str
            records.append(rec)
    return records


# ─── FEATURE ENGINEERING ─────────────────────────────────────
# This is the heart of "turning a job decision into numbers." Every
# field pulled here becomes one column K-Means can use to measure
# similarity between two decisions.

def safe_str(val, default="Unknown"):
    """Treat None, missing, and empty string uniformly as 'Unknown' —
    so a missing fit_tier doesn't accidentally become its own weird
    category distinct from an explicitly empty one."""
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


def build_feature_frame(records):
    """
    Convert the raw list of decision dicts into a pandas DataFrame of
    NUMERIC features suitable for K-Means, plus a parallel DataFrame of
    the original human-readable fields (kept alongside for the
    post-clustering interpretation step — K-Means never sees these).

    Features used (current schema + forward-compatible):
      - score              : numeric, as-is (already on a comparable
                              scale across all tracks/sources)
      - track_code         : "AI Engineering" / "Performance Engineering" /
                              "QA Automation" / "Remote Income Floor" (Gap
                              Track) / "Unknown" -> integer code
      - fit_tier_code       : "Excellent Fit" / "Strong Fit" / "Decent Fit" /
                              "Stretch Fit" / "Weak Fit" / "Unknown" ->
                              integer code. Will be "Unknown" for nearly
                              all of today's 216 records (not yet
                              backfilled) — that's expected, not a bug.
      - source_code         : which job board/API this came from
      - is_amazon           : 0/1, already a clean boolean-ish field
      - decision_code       : the human decision/reason category. This
                              is included as a feature deliberately, even
                              though it's also sort of the "answer" you'd
                              eventually want a classifier to predict —
                              for THIS exploratory pass, including it
                              helps reveal whether score/track/source
                              naturally separate by decision, which is
                              exactly the audit question we're asking.
    """
    track_vocab = {}
    fit_tier_vocab = {}
    source_vocab = {}
    decision_vocab = {}

    def code_for(vocab, value):
        if value not in vocab:
            vocab[value] = len(vocab)
        return vocab[value]

    rows = []
    meta_rows = []
    for rec in records:
        score = rec.get("score")
        score = float(score) if isinstance(score, (int, float)) else 0.0

        track = safe_str(rec.get("track"))
        fit_tier = safe_str(rec.get("fit_tier"))
        source = safe_str(rec.get("source"))
        decision = safe_str(rec.get("decision"))
        is_amazon = 1 if rec.get("is_amazon") else 0

        rows.append({
            "score": score,
            "track_code": code_for(track_vocab, track),
            "fit_tier_code": code_for(fit_tier_vocab, fit_tier),
            "source_code": code_for(source_vocab, source),
            "is_amazon": is_amazon,
            "decision_code": code_for(decision_vocab, decision),
        })
        meta_rows.append({
            "title": rec.get("title", ""),
            "level_signal": safe_str(rec.get("level_signal"), default=""),
            "track": track,
            "fit_tier": fit_tier,
            "source": source,
            "decision": decision,
            "score": score,
            "is_amazon": is_amazon,
            "date": rec.get("_date", ""),
            "url": rec.get("url", ""),
        })

    feature_df = pd.DataFrame(rows)
    meta_df = pd.DataFrame(meta_rows)
    vocabs = {
        "track": track_vocab,
        "fit_tier": fit_tier_vocab,
        "source": source_vocab,
        "decision": decision_vocab,
    }
    return feature_df, meta_df, vocabs


# ─── K SELECTION ─────────────────────────────────────────────
def pick_best_k(X_scaled, min_k=2, max_k=8):
    """
    Try a range of k values, score each with silhouette score (a metric
    from -1 to 1: how well-separated the clusters are — higher is
    better, roughly "points are close to their own cluster and far from
    others"), and return the k with the best score.

    This matters because K-Means doesn't pick k for you — you have to
    tell it how many clusters to look for, and the "right" number isn't
    obvious in advance. Silhouette score is one reasonable way to let
    the data suggest a good k rather than guessing.
    """
    best_k, best_score = min_k, -1
    scores = {}
    n_samples = X_scaled.shape[0]
    max_k = min(max_k, n_samples - 1)  # can't have more clusters than (samples-1)

    for k in range(min_k, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X_scaled, labels)
        scores[k] = score
        if score > best_score:
            best_k, best_score = k, score

    return best_k, scores


# ─── CLUSTER INTERPRETATION ──────────────────────────────────
def summarize_cluster(meta_df, cluster_labels, cluster_id):
    """
    For one cluster, pull together the human-readable summary: how many
    decisions are in it, what tracks/sources/decisions dominate, score
    range, and a few example job titles. This is the part meant for
    YOU to read and pattern-match on — K-Means itself doesn't produce
    any of this interpretation, it only produces the grouping.
    """
    mask = cluster_labels == cluster_id
    subset = meta_df[mask]

    def top_n(series, n=3):
        counts = Counter(series)
        return counts.most_common(n)

    summary = {
        "cluster_id": int(cluster_id),
        "size": int(mask.sum()),
        "score_min": float(subset["score"].min()) if len(subset) else None,
        "score_max": float(subset["score"].max()) if len(subset) else None,
        "score_mean": round(float(subset["score"].mean()), 1) if len(subset) else None,
        "top_tracks": top_n(subset["track"]),
        "top_fit_tiers": top_n(subset["fit_tier"]),
        "top_sources": top_n(subset["source"]),
        "top_decisions": top_n(subset["decision"]),
        "amazon_pct": round(100 * subset["is_amazon"].mean(), 1) if len(subset) else 0.0,
        "example_titles": subset["title"].head(5).tolist(),
    }
    return summary


def audit_seniority_filter(meta_df):
    """
    THE specific question that motivated adding level_signal in the first
    place: when Hans marks a job 'too_senior', did the seniority filter
    in get_job_track() already catch it (level_signal shows a seniority
    rule fired, meaning the job should never have been sent at all — a
    real filter bug), or did the filter correctly find no seniority
    signal (level_signal is "none:no-seniority-signal-found" or missing
    entirely), meaning Hans caught something from reading the actual
    posting that no keyword-based filter could have caught?

    This is NOT a clustering question — it's a direct crosstab, and a
    crosstab is the right tool here: K-Means measuring "distance" between
    a free-text level_signal string and a decision category would be
    arbitrary and wouldn't actually answer the question cleanly. A
    crosstab does.

    NOTE: level_signal will be empty for any historical record that
    predates this field being added — those rows are reported separately
    so they don't get misread as "filter found nothing."
    """
    too_senior = meta_df[meta_df["decision"] == "too_senior"]
    if len(too_senior) == 0:
        print("\n[INFO] No 'too_senior' decisions in this dataset — nothing to audit.")
        return

    has_signal = too_senior[too_senior["level_signal"] != ""]
    no_signal_data = too_senior[too_senior["level_signal"] == ""]

    print(f"\n{'='*60}")
    print(f"  Seniority Filter Audit: 'too_senior' decisions")
    print(f"{'='*60}")
    print(f"  Total 'too_senior' decisions: {len(too_senior)}")
    print(f"  ...with level_signal data:    {len(has_signal)}")
    print(f"  ...predating level_signal:    {len(no_signal_data)} "
          f"(can't audit these — field didn't exist yet when they were scored)")

    if len(has_signal) == 0:
        print(f"\n  [INFO] None of your 'too_senior' decisions have level_signal data yet.")
        print(f"  This will fill in as NEW decisions come in from runs using the")
        print(f"  updated job_search.py — re-run this audit again after that.")
        return

    filter_caught_it = has_signal[~has_signal["level_signal"].str.startswith("none:")]
    filter_missed_it = has_signal[has_signal["level_signal"].str.startswith("none:")]

    print(f"\n  Of the {len(has_signal)} with usable level_signal data:")
    print(f"    Filter ALREADY flagged seniority ({len(filter_caught_it)}):")
    print(f"      -> These should have been REJECTED before you ever saw them.")
    print(f"      -> If you're seeing these, something downstream isn't honoring level_ok.")
    for sig, count in Counter(filter_caught_it["level_signal"]).most_common(5):
        print(f"         {count}x  {sig}")

    print(f"\n    Filter found NO seniority signal ({len(filter_missed_it)}):")
    print(f"      -> These are honest filter misses — Hans caught something from")
    print(f"         reading the actual posting that no keyword list could see.")
    print(f"      -> This is the more EXPECTED outcome — keyword filters can't")
    print(f"         catch everything, and that's fine. Worth a skim for any")
    print(f"         recurring phrase that COULD be added as a new signal.")
    for title in filter_missed_it["title"].head(8):
        print(f"         - {title[:70]}")


def print_cluster_summary(summary):
    print(f"\n{'='*60}")
    print(f"  Cluster {summary['cluster_id']}  —  {summary['size']} decisions")
    print(f"{'='*60}")
    print(f"  Score range: {summary['score_min']:.0f}–{summary['score_max']:.0f} "
          f"(avg {summary['score_mean']:.1f})")
    print(f"  Top tracks:    {summary['top_tracks']}")
    print(f"  Top fit tiers: {summary['top_fit_tiers']}")
    print(f"  Top sources:   {summary['top_sources']}")
    print(f"  Top decisions: {summary['top_decisions']}")
    print(f"  Amazon %:      {summary['amazon_pct']}%")
    print(f"  Example titles:")
    for t in summary["example_titles"]:
        print(f"    - {t[:70]}")


# ─── MAIN ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Exploratory K-Means audit of job_decisions.json")
    parser.add_argument("--k", type=int, default=None,
                         help="Force a specific number of clusters (skips auto-selection)")
    parser.add_argument("--min-k", type=int, default=2, help="Minimum k to try during auto-selection")
    parser.add_argument("--max-k", type=int, default=8, help="Maximum k to try during auto-selection")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Decision Data Audit (Exploratory K-Means): {TODAY}")
    print(f"{'='*60}\n")

    records = load_all_decisions()
    n = len(records)
    print(f"[OK] Loaded {n} total decision record(s) from {DECISIONS_FILE}")

    if n < KMEANS_EXPLORATORY:
        print(f"[WARN] You have {n} decisions — below the exploratory milestone of "
              f"{KMEANS_EXPLORATORY}. Results below are still computed, but treat them "
              f"as very preliminary; small-sample clusters are easy to over-interpret.")
    elif n < KMEANS_PRODUCTION:
        pct = round(100 * n / KMEANS_PRODUCTION, 1)
        print(f"[OK] Past the exploratory milestone ({KMEANS_EXPLORATORY}). "
              f"{n}/{KMEANS_PRODUCTION} ({pct}%) toward the production classifier milestone.")
    else:
        print(f"[OK] Past BOTH milestones — {n} decisions. You have enough data to "
              f"consider building a real supervised classifier, not just this audit.")

    feature_df, meta_df, vocabs = build_feature_frame(records)

    print(f"\n[INFO] Feature vocabulary sizes (distinct values seen):")
    for name, vocab in vocabs.items():
        print(f"   {name}: {len(vocab)} distinct values -> {list(vocab.keys())}")

    # Direct crosstab audit — answers a specific question (is the
    # seniority filter under/over-catching?) more honestly than trying
    # to force it into the clustering features below.
    audit_seniority_filter(meta_df)

    # Standardize features — K-Means uses raw distance, so a feature
    # like "score" (range ~20-190) would totally dominate a feature
    # like "is_amazon" (range 0-1) unless we rescale everything to a
    # comparable scale first. StandardScaler converts every column to
    # "how many standard deviations from the mean," so no single
    # feature silently outweighs the others just because its raw
    # numbers happen to be bigger.
    X = feature_df.values
    X_scaled = StandardScaler().fit_transform(X)

    if args.k is not None:
        k = args.k
        print(f"\n[INFO] Using forced k={k} (--k flag)")
    else:
        k, scores = pick_best_k(X_scaled, args.min_k, args.max_k)
        print(f"\n[INFO] Auto-selected k={k} via silhouette score search "
              f"(tried k={args.min_k}..{args.max_k})")
        print(f"   Silhouette scores by k: {{k: round(v,3) for k,v in scores.items()}}"
              if False else f"   Silhouette scores by k: " +
              ", ".join(f"k={kk}: {round(vv,3)}" for kk, vv in scores.items()))

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    print(f"\n[OK] Ran K-Means with k={k} clusters over {n} decisions.")
    print(f"\nReading the clusters below: each one is a group of decisions K-Means")
    print(f"found to be numerically similar. Look for a pattern that's CONSISTENT")
    print(f"within a cluster but DIFFERENT from other clusters — that's the signal.")
    print(f"A cluster with no clear common thread just means K-Means grouped them")
    print(f"by leftover noise, not anything meaningful — that's a valid outcome too.")

    cluster_summaries = []
    for cluster_id in sorted(set(labels)):
        summary = summarize_cluster(meta_df, labels, cluster_id)
        print_cluster_summary(summary)
        cluster_summaries.append(summary)

    # Save full output for later digging
    output = {
        "generated_at": TODAY,
        "total_decisions": n,
        "k_used": int(k),
        "feature_vocabularies": {name: list(v.keys()) for name, v in vocabs.items()},
        "clusters": cluster_summaries,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n[OK] Full cluster breakdown saved to {OUTPUT_FILE}")
    print(f"\n{'='*60}")
    print(f"  Done.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
