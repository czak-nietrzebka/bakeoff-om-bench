#!/usr/bin/env python3
"""Regenerates `data/usage-summary.json` from the raw records in `data/runs/`.

Nothing in the summary is typed by hand: every token count is read from the last
line of a run's append-only record, and every dollar figure is recomputed from
those counts times the frozen rate card in `frozen/pricing.json` (SHA-256 of that
file is pinned in `frozen/MANIFEST.sha256`, committed before any run).

    python3 data/usage_summary.py            # rewrite data/usage-summary.json
    python3 data/usage_summary.py --print    # also print the at-a-glance table
    python3 data/usage_summary.py --check    # exit 1 if the file on disk differs

Standard library only. No arguments, no network, no configuration.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNS = os.path.join(HERE, "runs")
PRICING = os.path.join(REPO, "frozen", "pricing.json")
OUT = os.path.join(HERE, "usage-summary.json")

ARM_LABEL = {"a": "A - naive baseline", "b": "B - agent with process"}

# Working tokens per frozen/budgets.json: in + out + both cache-creation classes,
# deliberately WITHOUT cache_read (cheap re-reads would otherwise dominate and
# penalise whichever method carries the larger prompt). Symmetric for both arms.
WORKING = ("in", "out", "cache_creation_1h", "cache_creation_5m")
BILLED = ("in", "out", "cache_creation_1h", "cache_creation_5m", "cache_read")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pricing() -> dict:
    with open(PRICING, encoding="utf-8") as fh:
        return json.load(fh)


def rate_card(pricing: dict, run_date: str) -> dict:
    """Pick the rate card by the run's wall_start date (adjudication #10)."""
    for card in pricing["stawki_per_mtok"]:
        if "obowiazuje_do" in card and run_date <= card["obowiazuje_do"]:
            return card
    return pricing["stawki_per_mtok"][-1]


def impute(tokens: dict, card: dict) -> float:
    """Cost in USD. `thinking` is a SUBSET of `out` and is NOT added again."""
    per_mtok = {
        "in": card["input"],
        "out": card["output"],
        "cache_read": card["cache_read"],
        "cache_creation_5m": card["cache_creation_5m"],
        "cache_creation_1h": card["cache_creation_1h"],
    }
    return sum(tokens.get(k, 0) * v for k, v in per_mtok.items()) / 1_000_000


def wall_seconds(rec: dict) -> float | None:
    try:
        a = _dt.datetime.fromisoformat(rec["wall_start"])
        b = _dt.datetime.fromisoformat(rec["wall_end"])
    except (KeyError, TypeError, ValueError):
        return None
    return round((b - a).total_seconds(), 1)


def last_state(path: str) -> tuple[dict, int]:
    """Append-only: the LAST line is the current state; earlier lines are history."""
    recs = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    return recs[-1], len(recs)


def exclusion_for(rec: dict, archive: str | None) -> dict | None:
    if archive:
        return {"code": "archived", "archive": archive,
                "note": "see runs/%s/README.md - excluded from every statistic" % archive}
    if rec.get("disposition") != "complete":
        return {"code": rec.get("disposition"),
                "note": "record's own disposition is not `complete`; the last line of the "
                        "record carries the adjudication that voided it"}
    if rec.get("verdict") != "verified":
        return {"code": "not-verified", "note": "verdict is not `verified`"}
    return None


def build() -> dict:
    pricing = load_pricing()
    runs, archived = [], []

    paths = sorted(glob.glob(os.path.join(RUNS, "**", "*.jsonl"), recursive=True))
    for path in paths:
        rel = os.path.relpath(path, HERE).replace(os.sep, "/")
        if os.path.basename(path).startswith("journal"):
            continue
        parent = os.path.relpath(os.path.dirname(path), RUNS).replace(os.sep, "/")
        archive = None if parent == "." else parent

        rec, n_lines = last_state(path)
        tok = rec.get("tokens", {})
        card = rate_card(pricing, rec["wall_start"][:10])
        recomputed = impute(tok, card)
        recorded = rec.get("usd_imputed")
        excl = exclusion_for(rec, archive)

        row = {
            "run_id": rec.get("run_id"),
            "task": rec.get("task"),
            "arm": rec.get("arm"),
            "arm_label": ARM_LABEL.get(rec.get("arm"), rec.get("arm")),
            "source": rel,
            "record_lines": n_lines,
            "amended_after_the_fact": n_lines > 1,
            "model_id": rec.get("model_id"),
            "cli_version": rec.get("cli_version"),
            "counts_towards_series": excl is None,
            "excluded_because": excl,
            "verdict": rec.get("verdict"),
            "disposition": rec.get("disposition"),
            "rework_iterations": rec.get("rework_iterations"),
            "compact_boundary_count": rec.get("compact_boundary_count"),
            "sessions_recorded": len(rec.get("session_ids") or []),
            "tokens": {k: tok.get(k, 0) for k in
                       ("in", "out", "thinking", "cache_creation_5m",
                        "cache_creation_1h", "cache_read")},
            "tokens_working": sum(tok.get(k, 0) for k in WORKING),
            "tokens_billed_total": sum(tok.get(k, 0) for k in BILLED),
            "token_budget_working": rec.get("token_budget"),
            "usd_imputed": round(recomputed, 4),
            "usd_in_record": recorded,
            "usd_recompute_delta": round(recomputed - recorded, 6)
            if isinstance(recorded, (int, float)) else None,
            "rate_card": {"per_mtok": card,
                          "selected_by_wall_start_date": rec["wall_start"][:10]},
            "wall_start": rec.get("wall_start"),
            "wall_end": rec.get("wall_end"),
            "wall_clock_s": wall_seconds(rec),
            "compute_active_s": rec.get("compute_active_s"),
            "gate_time_s": rec.get("gate_time_s"),
            "build_time_s": rec.get("build_time_s"),
            "unmeasurable": rec.get("nie_umiem_zmierzyc"),
        }
        (archived if archive else runs).append(row)

    runs.sort(key=lambda r: (int(r["task"][1:]), r["arm"]))
    archived.sort(key=lambda r: (r["source"], int(r["task"][1:]), r["arm"]))

    def total(rows, arm=None, skip_tasks=()):
        sel = [r for r in rows if r["counts_towards_series"]
               and (arm is None or r["arm"] == arm) and r["task"] not in skip_tasks]
        return {
            "tasks": sorted({r["task"] for r in sel}, key=lambda t: int(t[1:])),
            "n": len(sel),
            "usd_imputed": round(sum(r["usd_imputed"] for r in sel), 4),
            "tokens_working": sum(r["tokens_working"] for r in sel),
            "tokens_billed_total": sum(r["tokens_billed_total"] for r in sel),
            "wall_clock_s": round(sum(r["wall_clock_s"] or 0 for r in sel), 1),
            "compute_active_s": round(sum(r["compute_active_s"] or 0 for r in sel), 1),
            "rework_iterations": sum(r["rework_iterations"] or 0 for r in sel),
        }

    counted_b = {r["task"] for r in runs if r["arm"] == "b" and r["counts_towards_series"]}
    counted_a = {r["task"] for r in runs if r["arm"] == "a" and r["counts_towards_series"]}
    both = sorted(counted_a & counted_b, key=lambda t: int(t[1:]))
    a_only = sorted(counted_a - counted_b, key=lambda t: int(t[1:]))

    totals = {
        "arm_a_all_counted": total(runs, "a"),
        "arm_b_all_counted": total(runs, "b"),
        "arm_a_on_tasks_both_arms_completed": total(runs, "a", skip_tasks=a_only),
        "arm_b_on_tasks_both_arms_completed": total(runs, "b", skip_tasks=a_only),
        "tasks_completed_by_both_arms": both,
        "tasks_completed_by_arm_a_only": a_only,
        "archive_usd_spent_but_not_counted": round(
            sum(r["usd_in_record"] or 0 for r in archived), 4),
        "voided_usd_spent_but_not_counted": round(
            sum(r["usd_in_record"] or 0 for r in runs
                if not r["counts_towards_series"]), 4),
    }

    a = totals["arm_a_on_tasks_both_arms_completed"]["usd_imputed"]
    b = totals["arm_b_on_tasks_both_arms_completed"]["usd_imputed"]
    totals["like_for_like_ratio_b_over_a"] = round(b / a, 4) if a else None

    gaps = []
    for task in sorted({r["task"] for r in runs}, key=lambda t: int(t[1:])):
        for arm in ("a", "b"):
            rows = [r for r in runs if r["task"] == task and r["arm"] == arm]
            if not rows:
                gaps.append({"slot": "%s-%s" % (task, arm.upper()),
                             "state": "no record at all"})
            elif not rows[0]["counts_towards_series"]:
                gaps.append({
                    "slot": "%s-%s" % (task, arm.upper()),
                    "state": "record exists but does not count",
                    "usd_spent_anyway": rows[0]["usd_in_record"],
                    "why": rows[0]["excluded_because"],
                    "pending": "awaiting a re-run; until it lands this slot is EMPTY, "
                               "and no per-arm total covering this task is like-for-like",
                })

    return {
        "_what_this_is":
            "Per-run usage summary for Experiment 1, computed from the raw records in "
            "data/runs/ - not transcribed from any report. Regenerate with "
            "`python3 data/usage_summary.py`.",
        "_how_cost_is_imputed":
            "The runs were made on a subscription, which does not bill per token. Dollar "
            "figures are IMPUTED: token counts read from the records, multiplied by the "
            "rate card frozen in frozen/pricing.json before the runs. `thinking` tokens "
            "are a subset of `out` and are reported separately for information only - they "
            "are NOT added to the cost a second time.",
        "_read_the_caveats": "data/README.md, frozen/AMENDMENTS.md",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "data/usage_summary.py",
        "inputs": {
            "records_glob": "data/runs/**/*.jsonl",
            "pricing_file": "frozen/pricing.json",
            "pricing_sha256": sha256(PRICING),
            "record_files_read": len(runs) + len(archived),
        },
        "series_runs": runs,
        "archive_runs": archived,
        "totals": totals,
        "empty_slots": gaps,
    }


def render(summary: dict) -> str:
    out = []
    hdr = ("task arm  status      usd   tokens_work   wall_s  active_s rw  model")
    out.append(hdr)
    out.append("-" * len(hdr))
    for r in summary["series_runs"]:
        out.append("%-5s%-4s %-9s %7.4f %12d %8.0f %9.0f %2d  %s" % (
            r["task"], r["arm"].upper(),
            "counted" if r["counts_towards_series"] else "EXCLUDED",
            r["usd_imputed"], r["tokens_working"], r["wall_clock_s"] or 0,
            r["compute_active_s"] or 0, r["rework_iterations"] or 0, r["model_id"]))
    t = summary["totals"]
    out.append("")
    out.append("arm A, all counted runs (%d): $%.4f" % (
        t["arm_a_all_counted"]["n"], t["arm_a_all_counted"]["usd_imputed"]))
    out.append("arm B, all counted runs (%d): $%.4f" % (
        t["arm_b_all_counted"]["n"], t["arm_b_all_counted"]["usd_imputed"]))
    out.append("like-for-like, only tasks BOTH arms completed (%s):" % ", ".join(
        t["tasks_completed_by_both_arms"]))
    out.append("  arm A $%.4f vs arm B $%.4f -> B/A = %.4f" % (
        t["arm_a_on_tasks_both_arms_completed"]["usd_imputed"],
        t["arm_b_on_tasks_both_arms_completed"]["usd_imputed"],
        t["like_for_like_ratio_b_over_a"]))
    out.append("tasks completed by arm A only (NOT like-for-like): %s" % (
        ", ".join(t["tasks_completed_by_arm_a_only"]) or "none"))
    out.append("spent but not counted: $%.4f voided in series + $%.4f in archives" % (
        t["voided_usd_spent_but_not_counted"], t["archive_usd_spent_but_not_counted"]))
    bad = [r["run_id"] for r in summary["series_runs"] + summary["archive_runs"]
           if r["usd_recompute_delta"] is None or abs(r["usd_recompute_delta"]) > 0.005]
    out.append("records whose stored cost does NOT match the recomputation: %s" % (
        ", ".join(bad) if bad else "none (all %d agree to the cent)" % (
            len(summary["series_runs"]) + len(summary["archive_runs"]))))
    for g in summary["empty_slots"]:
        out.append("EMPTY SLOT %s: %s" % (g["slot"], g["state"]))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print", dest="do_print", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    summary = build()
    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        drop = lambda s: "\n".join(
            l for l in s.splitlines() if '"generated_utc"' not in l)
        if drop(current) != drop(text):
            print("DIFFERS: usage-summary.json is not what the records produce",
                  file=sys.stderr)
            return 1
        print("OK: usage-summary.json matches the records")
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    if args.do_print:
        print(render(summary))
    else:
        print("wrote %s (%d series runs, %d archived)" % (
            os.path.relpath(OUT, REPO), len(summary["series_runs"]),
            len(summary["archive_runs"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
