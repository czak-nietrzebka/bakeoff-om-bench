#!/usr/bin/env python3
"""Second analysis pass: the tables `analyze.py` does not print.

    python3 derived.py data/           # human-readable tables
    python3 derived.py data/ --json    # the same numbers, machine-readable

`analyze.py` is the primary instrument: it recomputes every dollar from the raw
token counts and the frozen rate card, and it prints the per-task, paired-total,
cumulative, half-split, token-class, repeat-spread and exclusion tables.

This script exists because the analysis report also quotes four cuts of the same
records that `analyze.py` does not print: the size-class split, the machine-load
medians, active compute minutes and context-compaction counts. Those were
previously computed by hand, which meant a reader had to take them on trust. They
are computed here instead, from the published records only, so that every number
in the report is either produced by one of these two scripts or is explicitly
declared as coming from material that is not published.

Standard library only, no network, no configuration.

READING RULES (the same ones `analyze.py` applies, restated so this file stands
on its own):

  * a run record is append-only; group its lines by `wall_start` (one attempt per
    group), take the last line of each group, and treat the newest group as the
    slot's current state;
  * sub-directories of `runs/` are archives and never enter a statistic;
  * only `disposition == "complete"` is a measurement;
  * a task enters a head-to-head only if BOTH arms completed it.

Dollar figures are read from the records. They are not re-derived here on purpose:
`analyze.py` already recomputes each one from that run's own token counts and the
frozen dated price table and reports the disagreement (0 at publication). Two
scripts computing the same dollars two ways would be duplication, not a check.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys

ARM_LABEL = {"a": "A - naive baseline", "b": "B - agent with process"}


def _task_key(task: str) -> tuple:
    return (0, int(task[1:])) if task[1:].isdigit() else (1, task)


def load_records(root: str) -> dict:
    """Return {(task, arm): record} for the headline series only."""
    runs_dir = os.path.join(root, "runs")
    if not os.path.isdir(runs_dir):
        runs_dir = root
    out = {}
    for path in sorted(glob.glob(os.path.join(runs_dir, "*.jsonl"))):
        lines = []
        for raw in open(path, encoding="utf-8"):
            raw = raw.strip()
            if raw:
                lines.append(json.loads(raw))
        if not lines:
            continue
        newest = max(l.get("wall_start") or "" for l in lines)
        current = [l for l in lines if (l.get("wall_start") or "") == newest][-1]
        out[(current["task"], current["arm"].lower())] = current
    return out


def load_budgets(root: str) -> dict:
    for cand in (
        os.path.join(root, "..", "frozen", "budgets.json"),
        os.path.join(root, "frozen", "budgets.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen", "budgets.json"),
    ):
        if os.path.isfile(cand):
            with open(cand, encoding="utf-8") as fh:
                return json.load(fh)
    raise SystemExit("frozen/budgets.json not found - it carries the pre-registered size classes")


def paired_tasks(recs: dict) -> list:
    tasks = sorted({t for (t, _a) in recs}, key=_task_key)
    return [
        t for t in tasks
        if all(recs.get((t, a), {}).get("disposition") == "complete" for a in ("a", "b"))
    ]


def load1(rec: dict):
    la = rec.get("load_avg") or []
    return la[0] if la else None


def build(root: str) -> dict:
    recs = load_records(root)
    budgets = load_budgets(root)
    sizes = budgets["przypisanie"]          # pre-registered task -> size class
    paired = paired_tasks(recs)

    cost = {(t, a): recs[(t, a)]["usd_imputed"] for t in paired for a in ("a", "b")}

    # --- cumulative, with the ratio the crossover prediction is read from -----
    cum, ca, cb = [], 0.0, 0.0
    for t in paired:
        ca += cost[(t, "a")]
        cb += cost[(t, "b")]
        cum.append({"task": t, "cum_a": round(ca, 4), "cum_b": round(cb, 4),
                    "ratio_b_over_a": round(cb / ca, 4), "b_below_a": cb < ca})

    # --- size classes, as frozen before any run ------------------------------
    by_size = {}
    for cls in ("S", "M", "L"):
        ts = [t for t in paired if sizes.get(t) == cls]
        if not ts:
            continue
        a = sum(cost[(t, "a")] for t in ts)
        b = sum(cost[(t, "b")] for t in ts)
        by_size[cls] = {
            "tasks": ts,
            "a": round(a, 4), "b": round(b, 4),
            "b_vs_a_pct": round((b - a) / a * 100, 1) if a else None,
            "tasks_b_cheaper": sum(1 for t in ts if cost[(t, "b")] < cost[(t, "a")]),
            "unpaired_tasks_in_class": [t for t, c in sizes.items()
                                        if c == cls and t not in paired],
        }

    # --- halves: the same median split analyze.py uses -----------------------
    half = len(paired) // 2
    halves = {}
    for name, ts in (("early", paired[:half]), ("late", paired[half:])):
        entry = {"tasks": ts}
        for a in ("a", "b"):
            loads = [load1(recs[(t, a)]) for t in ts]
            loads = [x for x in loads if x is not None]
            entry[a] = {
                "cost": round(sum(cost[(t, a)] for t in ts), 4),
                "load1_mean": round(statistics.mean(loads), 2) if loads else None,
                "load1_median": round(statistics.median(loads), 2) if loads else None,
            }
        entry["b_vs_a_pct"] = round((entry["b"]["cost"] - entry["a"]["cost"])
                                    / entry["a"]["cost"] * 100, 1)
        halves[name] = entry

    # --- effort that is not dollars -----------------------------------------
    effort = {}
    for a in ("a", "b"):
        scored = [recs[(t, a)] for t in paired]
        all_headline = [r for (t, arm), r in recs.items() if arm == a]
        effort[a] = {
            "scored_runs": len(scored),
            "active_minutes_scored": round(sum(r.get("compute_active_s") or 0
                                               for r in scored) / 60, 1),
            "compactions_scored": sum(r.get("compact_boundary_count") or 0 for r in scored),
            "compactions_all_headline_runs": sum(r.get("compact_boundary_count") or 0
                                                 for r in all_headline),
            "runs_with_human_touch": sum(1 for r in all_headline if r.get("human_touch")),
            "runs_with_rate_limit": sum(1 for r in all_headline if r.get("rate_limit_events")),
        }

    per_run = [
        {"task": t, "arm": a.upper(), "usd": cost[(t, a)],
         "load1": load1(recs[(t, a)]),
         "active_min": round((recs[(t, a)].get("compute_active_s") or 0) / 60, 1)}
        for t in paired for a in ("a", "b")
    ]

    return {"paired_tasks": paired, "cumulative": cum, "size_classes": by_size,
            "halves": halves, "effort": effort, "per_run": per_run}


def report(d: dict) -> None:
    line = "=" * 78
    print(line)
    print("derived.py - the cuts analyze.py does not print")
    print("every number below comes from the published run records")
    print(line)
    print(f"paired tasks ({len(d['paired_tasks'])}): {', '.join(d['paired_tasks'])}")

    print("\n" + line)
    print("1. CUMULATIVE COST AND THE RATIO THE CROSSOVER IS READ FROM")
    print("-" * 78)
    print("task        cum A      cum B     B/A   B below A?")
    for r in d["cumulative"]:
        print(f"{r['task']:<6}{r['cum_a']:10.4f}{r['cum_b']:11.4f}{r['ratio_b_over_a']:8.3f}"
              f"   {'yes' if r['b_below_a'] else 'no'}")
    below = [r["task"] for r in d["cumulative"] if r["b_below_a"]]
    tail = []
    for i, r in enumerate(d["cumulative"]):
        if all(x["b_below_a"] for x in d["cumulative"][i:]):
            tail.append(r["task"])
    first_sustained = tail[0] if tail else None
    print(f"\n  arm B's cumulative cost is below arm A's after: {', '.join(below) or 'never'}")
    if first_sustained is None:
        print("  no task from which arm B stays below arm A through the end of the series")
    elif first_sustained == d["cumulative"][-1]["task"]:
        print(f"  first task from which B stays below A to the end: {first_sustained}"
              " - the LAST task, i.e. the series total restated, not a crossover")
    else:
        print(f"  first task from which B stays below A to the end: {first_sustained}")

    print("\n" + line)
    print("2. BY PRE-REGISTERED SIZE CLASS (frozen/budgets.json, fixed before any run)")
    print("-" * 78)
    print("size  tasks                          arm A      arm B    B vs A   B cheaper in")
    for cls, r in d["size_classes"].items():
        print(f"{cls:<6}{', '.join(r['tasks']):<28}{r['a']:9.4f}{r['b']:11.4f}"
              f"{r['b_vs_a_pct']:9.1f}%   {r['tasks_b_cheaper']} of {len(r['tasks'])}")
        if r["unpaired_tasks_in_class"]:
            print(f"        (not in the comparison: {', '.join(r['unpaired_tasks_in_class'])}"
                  " - no paired measurement)")
    print("\n  The size class is the one frozen in the budget table before any run, so"
          "\n  it is not a post-hoc cut. It is NOT independent of series position:"
          "\n  see the task numbers in each row.")

    print("\n" + line)
    print("3. HALVES, WITH MACHINE LOAD (median split, same as analyze.py)")
    print("-" * 78)
    print("half   tasks                     arm    cost   load1 mean  load1 median")
    for name, h in d["halves"].items():
        for a in ("a", "b"):
            print(f"{name:<7}{', '.join(h['tasks']):<26}{a.upper():<6}"
                  f"{h[a]['cost']:8.4f}{h[a]['load1_mean']:12.2f}{h[a]['load1_median']:14.2f}")
        print(f"{'':<39}B vs A {h['b_vs_a_pct']:+.1f}%")
    print("\n  Load is the runner's 1-minute load average as recorded with each run."
          "\n  It does not consume tokens by itself; it is here because the two arms"
          "\n  did not run in the same windows, so it moves with the halves.")

    print("\n" + line)
    print("4. EFFORT THAT IS NOT DOLLARS")
    print("-" * 78)
    for a in ("a", "b"):
        e = d["effort"][a]
        print(f"  {ARM_LABEL[a]}")
        print(f"    scored runs                    {e['scored_runs']}")
        print(f"    active compute, scored runs    {e['active_minutes_scored']} min")
        print(f"    context compactions, scored    {e['compactions_scored']}")
        print(f"    context compactions, all runs  {e['compactions_all_headline_runs']}"
              "  (includes runs excluded from the totals)")
        print(f"    runs with human intervention   {e['runs_with_human_touch']}")
        print(f"    runs with a rate-limit event   {e['runs_with_rate_limit']}")

    print("\n" + line)
    print("5. PER-RUN COST, LOAD AND ACTIVE TIME (so any claim above is checkable)")
    print("-" * 78)
    print("task  arm      usd   load1   active min")
    for r in d["per_run"]:
        l1 = f"{r['load1']:.2f}" if r["load1"] is not None else "n/a"
        print(f"{r['task']:<6}{r['arm']:<5}{r['usd']:8.4f}{l1:>8}{r['active_min']:12.1f}")
    print(line)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default="data",
                    help="directory holding runs/ (default: data)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()
    d = build(args.root)
    if args.json:
        json.dump(d, sys.stdout, indent=2, sort_keys=False)
        print()
    else:
        report(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())