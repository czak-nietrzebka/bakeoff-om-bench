#!/usr/bin/env python3
"""Reproduce the whole Experiment-1 analysis from the raw published files.

    python3 analyze.py data/            # human-readable report
    python3 analyze.py data/ --json     # same numbers, machine-readable

Standard library only, no network, no configuration. Every number printed by the
analysis report in this repository is produced here; nothing is typed in by hand.

--------------------------------------------------------------------------------
EXPECTED INPUT LAYOUT
--------------------------------------------------------------------------------

    data/
      runs/                     per-run records, one JSONL file per (task, arm)
        p1-T1-A.jsonl           <- headline series: these are the runs that count
        p1-T1-B.jsonl
        ...
        <archive-dir>/          <- ARCHIVES: excluded from every statistic
          README.md             <- says, in prose, why the directory is excluded
          p1-T1-B.jsonl
      journal/                  optional; step-level event log, not used for money
      frozen/pricing.json       the dated price table committed before any run
      frozen/AMENDMENTS.md      optional; the protocol amendment log

`runs/` may be omitted, in which case the record files are looked for directly in
the root you pass. `pricing.json` is searched for in a few conventional places and
can always be overridden with --pricing.

--------------------------------------------------------------------------------
THE FIVE READING RULES, AND WHY THEY ARE WHAT THEY ARE
--------------------------------------------------------------------------------

1.  THE RECORD FILES ARE APPEND-ONLY, SO THE LAST LINE WINS.
    A run's bookkeeping can be corrected after the fact (a mis-attributed cost, a
    verdict overturned by a pre-registered adjudication). Corrections are appended
    as a new full line; the earlier line is never edited or deleted, so the file
    keeps its own audit trail. Reading a record therefore means: take the LAST
    line for that run, not the first, and not a merge of the two.

2.  ONE FILE CAN HOLD SEVERAL ATTEMPTS, AND `wall_start` TELLS THEM APART.
    When a run died on infrastructure and was retried, the retry was appended to
    the same file. Retries are genuinely different runs; corrections are the same
    run re-stated. The discriminator is `wall_start`: a correction repeats the
    timestamp of the line it corrects, a retry carries a new one. So we group
    lines by `wall_start` (= one attempt), take the last line of each group (rule
    1), and treat the attempt with the newest `wall_start` as the run's current
    state. Everything older in the file is a superseded attempt and is reported
    in the invalidated list rather than silently dropped.

3.  ARCHIVE DIRECTORIES NEVER ENTER A STATISTIC.
    A subdirectory under `runs/` is an archive: runs that were disqualified as a
    block, each directory carrying a README that states the reason. They are kept
    because deleting inconvenient measurements is how benchmarks lie, and they are
    read here for exactly two purposes: to be listed as excluded, and to supply
    the repeated (task, arm) runs used for the run-to-run spread section, which is
    labelled as an upper bound precisely because those repeats are not clean.

4.  ONLY `disposition == "complete"` IS A MEASUREMENT.
    `disposition` is the field that says whether a run measured the thing we set
    out to measure. Anything else -- `infra-void` (the harness, not the arm,
    failed) or `DNF` (the arm ran out of its iteration budget) -- is not a cheaper
    or dearer result, it is an absent result. We read the field; we never infer
    validity from cost being zero or from a verdict looking bad.

5.  A TASK ENTERS THE HEAD-TO-HEAD ONLY IF BOTH ARMS COMPLETED IT.
    A per-arm total over different task sets is not a comparison. So the primary
    number is the PAIRED total over tasks where both arms have a complete run, and
    every task dropped from it is printed with its reason. The unpaired per-arm
    totals are printed too, clearly labelled, because they are what a reader would
    otherwise compute themselves and wonder why it differs.

--------------------------------------------------------------------------------
HOW MONEY IS COMPUTED
--------------------------------------------------------------------------------

The runs were executed on a subscription, which does not bill per token, so a
dollar figure has to be IMPUTED: token counts from the session transcripts,
multiplied by a public price list frozen before the series started. The price list
is dated -- the model's introductory rates expired mid-window -- so the rate band
is selected by each run's own `wall_start` date, not by today's date.

`thinking` tokens are reported as their own class for information but are NOT
priced separately: they are a subset of the output tokens and are already inside
`out`. Adding them would double-count.

This script does not trust the `usd_imputed` field. It recomputes every run's cost
from that run's token counts and the frozen table, and reports any disagreement in
the integrity section. If the two ever diverge, the reader sees it here first.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

# The two arms, named as the public README names them. "A" and "B" are the letters
# in the record filenames; the descriptions are what the reader needs.
ARMS = ("a", "b")
ARM_LABEL = {
    "a": "A - naive baseline",
    "b": "B - agent with process",
}

# A record filename looks like: p<pair>-T<task>-<arm>.jsonl
RUN_FILE_RE = re.compile(r"^p(?P<pair>\d+)-T(?P<task>\d+)-(?P<arm>[AB])\.jsonl$", re.I)

# Token classes as they appear in the record, in the order we want them printed.
# `thinking` is deliberately last and deliberately unpriced (see module docstring).
TOKEN_CLASSES = ("in", "out", "cache_creation_1h", "cache_creation_5m", "cache_read")
TOKEN_CLASS_INFO = "thinking"

# Cost agreement tolerance, in dollars. Recorded costs are stored to 4 decimal
# places, so anything at or below half of the last place is rounding, not a
# discrepancy.
COST_TOLERANCE_USD = 0.00005

SEP = "=" * 78
SUB = "-" * 78


# ------------------------------------------------------------------------------
# input discovery
# ------------------------------------------------------------------------------

def _is_noise(name: str) -> bool:
    """macOS writes AppleDouble sidecars (`._foo.jsonl`) next to real files when
    an archive is unpacked on a non-native filesystem. They are not records."""
    return name.startswith("._") or name.startswith(".")


def find_runs_root(root: str) -> str:
    """Records live in `<root>/runs/` by convention; fall back to `<root>` itself
    so the script still works if someone hands it the records directory."""
    candidate = os.path.join(root, "runs")
    if os.path.isdir(candidate):
        return candidate
    return root


def find_pricing(root: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (
        os.path.join(root, "frozen", "pricing.json"),
        os.path.join(root, "pricing.json"),
        os.path.join(os.path.dirname(os.path.abspath(root)), "frozen", "pricing.json"),
        os.path.join(here, "frozen", "pricing.json"),
    ):
        if os.path.isfile(path):
            return path
    return None


def find_amendments(root: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (
        os.path.join(root, "frozen", "AMENDMENTS.md"),
        os.path.join(root, "AMENDMENTS.md"),
        os.path.join(here, "frozen", "AMENDMENTS.md"),
    ):
        if os.path.isfile(path):
            return path
    return None


def collect_record_files(runs_root: str) -> list[dict]:
    """Return every record file with its archive membership.

    Depth is the whole rule: a file sitting directly in `runs/` is headline, a file
    in any subdirectory is archived under that subdirectory's name (rule 3).
    """
    found: list[dict] = []
    if not os.path.isdir(runs_root):
        return found

    for name in sorted(os.listdir(runs_root)):
        if _is_noise(name):
            continue
        path = os.path.join(runs_root, name)
        if os.path.isfile(path) and RUN_FILE_RE.match(name):
            found.append({"path": path, "archive": None, "archive_reason": ""})
        elif os.path.isdir(path):
            reason = read_archive_reason(path)
            for inner in sorted(os.listdir(path)):
                if _is_noise(inner) or not RUN_FILE_RE.match(inner):
                    continue
                found.append({
                    "path": os.path.join(path, inner),
                    "archive": name,
                    "archive_reason": reason,
                })
    return found


def read_archive_reason(dir_path: str) -> str:
    """First non-empty line of the archive's README -- the directory's own account
    of why its runs do not count. Absent README is reported as such, not guessed."""
    readme = os.path.join(dir_path, "README.md")
    if not os.path.isfile(readme):
        return "(no README.md in the archive directory - reason NOT RECORDED)"
    with open(readme, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                return line
    return "(README.md present but empty - reason NOT RECORDED)"


# ------------------------------------------------------------------------------
# pricing
# ------------------------------------------------------------------------------

class Pricing:
    """The frozen, dated price table.

    Field names in pricing.json are in the operators' language; mapped here once:
      stawki_per_mtok  -> rate bands, dollars per million tokens
      obowiazuje_do    -> band applies through this date (inclusive)
      obowiazuje_od    -> band applies from this date (inclusive)
    """

    def __init__(self, path: str | None, raw: dict | None):
        self.path = path
        self.raw = raw or {}
        self.bands = self.raw.get("stawki_per_mtok") or []
        self.model_id = self.raw.get("model_id")

    @property
    def available(self) -> bool:
        return bool(self.bands)

    def band_for(self, when: date) -> tuple[int, dict] | tuple[None, None]:
        for idx, band in enumerate(self.bands):
            through = band.get("obowiazuje_do")
            since = band.get("obowiazuje_od")
            if through and when > date.fromisoformat(through):
                continue
            if since and when < date.fromisoformat(since):
                continue
            return idx, band
        return None, None

    def band_label(self, idx: int) -> str:
        band = self.bands[idx]
        through = band.get("obowiazuje_do")
        since = band.get("obowiazuje_od")
        if through and since:
            return f"{since}..{through}"
        if through:
            return f"through {through}"
        if since:
            return f"from {since}"
        return "unbounded"

    def cost_by_class(self, tokens: dict, when: date) -> tuple[dict | None, int | None]:
        """Dollars per token class. Returns (None, None) when the band cannot be
        resolved -- an unpriceable run is reported as unpriceable, not as free."""
        idx, band = self.band_for(when)
        if band is None:
            return None, None
        out = {}
        for cls in TOKEN_CLASSES:
            rate = band.get(cls if cls != "in" and cls != "out" else {"in": "input", "out": "output"}[cls])
            if rate is None:
                return None, None
            out[cls] = (tokens.get(cls, 0) or 0) / 1_000_000.0 * float(rate)
        return out, idx


def load_pricing(path: str | None) -> Pricing:
    if not path or not os.path.isfile(path):
        return Pricing(path, None)
    with open(path, encoding="utf-8") as fh:
        return Pricing(path, json.load(fh))


# ------------------------------------------------------------------------------
# record parsing
# ------------------------------------------------------------------------------

def parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def read_attempts(entry: dict) -> list[dict]:
    """Turn one record file into a list of attempts, newest last.

    Applies reading rules 1 and 2: group the appended lines by `wall_start`, keep
    the last line of each group as that attempt's current state, and remember how
    many lines were superseded so the correction count can be reported.
    """
    meta = RUN_FILE_RE.match(os.path.basename(entry["path"])).groupdict()
    order: list[str] = []
    grouped: dict[str, list[dict]] = {}
    malformed = 0

    with open(entry["path"], encoding="utf-8") as fh:
        for raw_line in fh:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                rec = json.loads(raw_line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            key = str(rec.get("wall_start"))
            if key not in grouped:
                grouped[key] = []
                order.append(key)
            grouped[key].append(rec)

    attempts = []
    for key in order:
        lines = grouped[key]
        current = lines[-1]                      # rule 1: last line wins
        tokens = current.get("tokens") or {}
        attempts.append({
            "file": entry["path"],
            "file_name": os.path.basename(entry["path"]),
            "archive": entry["archive"],
            "archive_reason": entry["archive_reason"],
            "run_id": current.get("run_id"),
            "pair": current.get("pair"),
            "task": f"T{int(meta['task'])}",
            "task_no": int(meta["task"]),
            "arm": meta["arm"].lower(),
            "wall_start": current.get("wall_start"),
            "wall_end": current.get("wall_end"),
            "tokens": {k: int(tokens.get(k, 0) or 0)
                       for k in TOKEN_CLASSES + (TOKEN_CLASS_INFO,)},
            "usd_recorded": current.get("usd_imputed"),
            "verdict": current.get("verdict"),
            "disposition": current.get("disposition"),
            "dnf_reason": current.get("dnf_reason"),
            "rework_iterations": current.get("rework_iterations"),
            "gate_runs": len(current.get("gate_runs") or []),
            "notes": (current.get("notes") or "").strip(),
            "load_avg_1m": (current.get("load_avg") or [None])[0],
            "measurement_gaps": current.get("nie_umiem_zmierzyc") or [],
            "revisions": len(lines),            # 1 = never corrected
            "malformed_lines": malformed,
        })

    # Newest attempt last, so [-1] is the run's current state (rule 2).
    attempts.sort(key=lambda a: (parse_ts(a["wall_start"]) or datetime.min))
    for i, att in enumerate(attempts):
        att["is_current"] = (i == len(attempts) - 1)
        att["superseded_by_retry"] = not att["is_current"]
    return attempts


def price_attempt(att: dict, pricing: Pricing) -> None:
    """Attach recomputed cost + the per-class breakdown. Mutates `att`."""
    started = parse_ts(att["wall_start"])
    att["usd_computed"] = None
    att["cost_by_class"] = None
    att["price_band"] = None
    att["cost_agrees"] = None

    if not pricing.available or started is None:
        return
    by_class, band_idx = pricing.cost_by_class(att["tokens"], started.date())
    if by_class is None:
        return

    att["cost_by_class"] = by_class
    att["usd_computed"] = round(sum(by_class.values()), 4)
    att["price_band"] = pricing.band_label(band_idx)
    if att["usd_recorded"] is not None:
        att["cost_agrees"] = abs(att["usd_computed"] - float(att["usd_recorded"])) <= COST_TOLERANCE_USD


def usd(att: dict) -> float:
    """The dollar figure we use. Prefer our own recomputation from the frozen
    table; fall back to the recorded field only when we could not price the run
    ourselves (and the integrity section says so out loud)."""
    if att.get("usd_computed") is not None:
        return float(att["usd_computed"])
    if att.get("usd_recorded") is not None:
        return float(att["usd_recorded"])
    return 0.0


# ------------------------------------------------------------------------------
# analysis
# ------------------------------------------------------------------------------

def pct(new: float, base: float) -> float | None:
    if not base:
        return None
    return (new - base) / base * 100.0


def fmt_pct(value: float | None, sign: bool = True) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1f}%" if sign else f"{value:.1f}%"


def fmt_usd(value: float | None) -> str:
    return "     -" if value is None else f"{value:8.4f}"


def analyse(root: str, pricing_path: str | None, amendments_path: str | None,
            split_at: int | None) -> dict:
    runs_root = find_runs_root(root)
    files = collect_record_files(runs_root)
    pricing = load_pricing(pricing_path)

    all_attempts: list[dict] = []
    for entry in files:
        for att in read_attempts(entry):
            price_attempt(att, pricing)
            all_attempts.append(att)

    headline = [a for a in all_attempts if a["archive"] is None]
    archived = [a for a in all_attempts if a["archive"] is not None]

    # ---- the runs that count: headline, current attempt, disposition complete --
    counted = [a for a in headline if a["is_current"] and a["disposition"] == "complete"]
    by_task_arm = {(a["task_no"], a["arm"]): a for a in counted}

    tasks = sorted({a["task_no"] for a in headline})
    paired_tasks = [t for t in tasks
                    if (t, "a") in by_task_arm and (t, "b") in by_task_arm]
    unpaired_tasks = [t for t in tasks if t not in paired_tasks]

    # ---- per-task rows ------------------------------------------------------
    rows = []
    for t in tasks:
        row = {"task": f"T{t}", "task_no": t, "paired": t in paired_tasks}
        for arm in ARMS:
            att = by_task_arm.get((t, arm))
            if att:
                row[arm] = {
                    "usd": usd(att),
                    "gate_runs": att["gate_runs"],
                    "rework_iterations": att["rework_iterations"],
                    "verdict": att["verdict"],
                    "disposition": att["disposition"],
                    "wall_start": att["wall_start"],
                    "load_avg_1m": att["load_avg_1m"],
                }
            else:
                # No complete run for this arm. Say which attempt exists instead;
                # an empty slot must read as empty, never as zero cost.
                other = [a for a in headline
                         if a["task_no"] == t and a["arm"] == arm and a["is_current"]]
                row[arm] = {
                    "usd": None,
                    "gate_runs": other[0]["gate_runs"] if other else None,
                    "rework_iterations": other[0]["rework_iterations"] if other else None,
                    "verdict": other[0]["verdict"] if other else None,
                    "disposition": other[0]["disposition"] if other else "NO RECORD",
                    "wall_start": other[0]["wall_start"] if other else None,
                    "load_avg_1m": other[0]["load_avg_1m"] if other else None,
                }
        a_usd, b_usd = row["a"]["usd"], row["b"]["usd"]
        row["delta_pct"] = pct(b_usd, a_usd) if (a_usd and b_usd) else None
        rows.append(row)

    # ---- totals -------------------------------------------------------------
    def total(arm: str, task_list: list[int]) -> float:
        return round(sum(usd(by_task_arm[(t, arm)]) for t in task_list
                         if (t, arm) in by_task_arm), 4)

    arm_all_tasks = {arm: sorted(t for t in tasks if (t, arm) in by_task_arm) for arm in ARMS}
    totals = {
        "unpaired": {arm: {"usd": total(arm, arm_all_tasks[arm]),
                           "n_tasks": len(arm_all_tasks[arm]),
                           "tasks": [f"T{t}" for t in arm_all_tasks[arm]]}
                     for arm in ARMS},
        "paired": {arm: {"usd": total(arm, paired_tasks),
                         "n_tasks": len(paired_tasks),
                         "tasks": [f"T{t}" for t in paired_tasks]}
                   for arm in ARMS},
    }
    totals["paired"]["delta_pct"] = pct(totals["paired"]["b"]["usd"],
                                        totals["paired"]["a"]["usd"])
    totals["paired"]["delta_usd"] = round(totals["paired"]["b"]["usd"]
                                          - totals["paired"]["a"]["usd"], 4)
    b_cheaper = sum(1 for r in rows if r["paired"] and r["delta_pct"] is not None
                    and r["delta_pct"] < 0)
    totals["paired"]["b_cheaper_in"] = b_cheaper
    totals["paired"]["of_pairs"] = len(paired_tasks)

    # Exclusions from the paired total, each with the reason taken from the record.
    exclusions = []
    for t in unpaired_tasks:
        for arm in ARMS:
            att = next((a for a in headline
                        if a["task_no"] == t and a["arm"] == arm and a["is_current"]), None)
            exclusions.append({
                "task": f"T{t}",
                "arm": arm,
                "disposition": att["disposition"] if att else "NO RECORD",
                "usd_would_have_been": (usd(att) if att and att["disposition"] == "complete"
                                        else None),
                "reason": (att["notes"] or att["dnf_reason"] or "") if att else
                          "no record file for this slot",
            })

    # ---- cumulative curve (the pre-registered crossing endpoint) -------------
    cumulative = []
    run_a = run_b = 0.0
    for t in paired_tasks:
        run_a += usd(by_task_arm[(t, "a")])
        run_b += usd(by_task_arm[(t, "b")])
        cumulative.append({"task": f"T{t}", "cum_a": round(run_a, 4),
                           "cum_b": round(run_b, 4),
                           "b_below_a": run_b < run_a})
    crossing = None
    for i, point in enumerate(cumulative):
        if all(p["b_below_a"] for p in cumulative[i:]):
            crossing = point["task"]
            break

    # ---- halves -------------------------------------------------------------
    # Median split of the paired tasks in series order. Stated as a rule so the
    # reader can check we did not hunt for a flattering cut; --split-at overrides
    # it and the report says which cut produced the numbers.
    n = len(paired_tasks)
    cut = split_at if split_at is not None else n // 2
    cut = max(0, min(cut, n))
    first_half, second_half = paired_tasks[:cut], paired_tasks[cut:]

    def half_stats(task_list: list[int]) -> dict:
        a_sum, b_sum = total("a", task_list), total("b", task_list)
        loads = {arm: [by_task_arm[(t, arm)]["load_avg_1m"] for t in task_list
                       if by_task_arm[(t, arm)]["load_avg_1m"] is not None]
                 for arm in ARMS}
        return {
            "tasks": [f"T{t}" for t in task_list],
            "n_tasks": len(task_list),
            "a_usd": a_sum, "b_usd": b_sum,
            "delta_pct": pct(b_sum, a_sum),
            "mean_load_1m": {arm: (round(sum(v) / len(v), 2) if v else None)
                             for arm, v in loads.items()},
        }

    halves = {
        "split_rule": ("median split of the paired tasks in series order"
                       if split_at is None else f"explicit --split-at {split_at}"),
        "early": half_stats(first_half),
        "late": half_stats(second_half),
    }

    # Measured signals that make the halves split hard to read. All three are
    # computed, not asserted: if a future series does not have them, they vanish.
    gaps_h = []
    for t in paired_tasks:
        sa = parse_ts(by_task_arm[(t, "a")]["wall_start"])
        sb = parse_ts(by_task_arm[(t, "b")]["wall_start"])
        if sa and sb:
            gaps_h.append(abs((sb - sa).total_seconds()) / 3600.0)
    halves["pairing_gap_hours"] = {
        "min": round(min(gaps_h), 2) if gaps_h else None,
        "max": round(max(gaps_h), 2) if gaps_h else None,
        "median": round(sorted(gaps_h)[len(gaps_h) // 2], 2) if gaps_h else None,
        "n": len(gaps_h),
    }
    # Did each arm actually execute the tasks in numeric order? If it did, "early
    # task" and "early wall-clock" are the same axis and cannot be separated.
    halves["executed_in_task_order"] = {}
    for arm in ARMS:
        seq = [(t, parse_ts(by_task_arm[(t, arm)]["wall_start"]))
               for t in sorted(arm_all_tasks[arm])]
        starts = [s for _, s in seq if s]
        halves["executed_in_task_order"][arm] = (starts == sorted(starts))

    # ---- token classes ------------------------------------------------------
    token_stats = {}
    for arm in ARMS:
        arm_runs = [by_task_arm[(t, arm)] for t in tasks if (t, arm) in by_task_arm]
        tok = {c: sum(a["tokens"].get(c, 0) for a in arm_runs)
               for c in TOKEN_CLASSES + (TOKEN_CLASS_INFO,)}
        cost = {c: round(sum((a["cost_by_class"] or {}).get(c, 0.0) for a in arm_runs), 4)
                for c in TOKEN_CLASSES}
        tok_total = sum(tok[c] for c in TOKEN_CLASSES)
        cost_total = round(sum(cost.values()), 4)
        token_stats[arm] = {
            "n_runs": len(arm_runs),
            "tokens": tok,
            "tokens_total_priced": tok_total,
            "cost": cost,
            "cost_total": cost_total,
            "token_share_pct": {c: (tok[c] / tok_total * 100.0 if tok_total else None)
                                for c in TOKEN_CLASSES},
            "cost_share_pct": {c: (cost[c] / cost_total * 100.0 if cost_total else None)
                               for c in TOKEN_CLASSES},
            "cache_read_cost_share_pct": (cost["cache_read"] / cost_total * 100.0
                                          if cost_total else None),
            "cache_read_token_share_pct": (tok["cache_read"] / tok_total * 100.0
                                           if tok_total else None),
        }

    # ---- run-to-run spread --------------------------------------------------
    # Every (task, arm) that was executed more than once ANYWHERE in the data, so
    # long as the run actually produced a measurement. Runs with zero worked
    # tokens never got off the ground and would fake a 100% spread.
    repeat_pool: dict[tuple[int, str], list[dict]] = {}
    for att in all_attempts:
        worked = sum(att["tokens"].get(c, 0) for c in
                     ("in", "out", "cache_creation_1h", "cache_creation_5m"))
        if att["disposition"] != "complete" or worked <= 0:
            continue
        repeat_pool.setdefault((att["task_no"], att["arm"]), []).append(att)

    spread_groups, n_pairs = [], 0
    for (task_no, arm), runs in sorted(repeat_pool.items()):
        if len(runs) < 2:
            continue
        costs = [usd(r) for r in runs]
        lo, hi = min(costs), max(costs)
        n_pairs += len(runs) * (len(runs) - 1) // 2
        spread_groups.append({
            "task": f"T{task_no}",
            "arm": arm,
            "n_runs": len(runs),
            "min_usd": round(lo, 4),
            "max_usd": round(hi, 4),
            "spread_pct": round((hi - lo) / lo * 100.0, 1) if lo else None,
            # Naming the source of each repeat is the whole point: if two runs sit
            # in different archives, they differed by a KNOWN condition, and the
            # spread between them is not pure noise.
            "runs": [{"usd": round(usd(r), 4),
                      "source": r["archive"] or "headline",
                      "wall_start": r["wall_start"]} for r in runs],
            "same_conditions": len({r["archive"] for r in runs}) == 1,
        })
    spreads = [g["spread_pct"] for g in spread_groups if g["spread_pct"] is not None]
    spread = {
        "n_repeat_groups": len(spread_groups),
        "n_pairwise_comparisons": n_pairs,
        "n_groups_under_identical_conditions": sum(1 for g in spread_groups
                                                   if g["same_conditions"]),
        "groups": spread_groups,
        "min_spread_pct": min(spreads) if spreads else None,
        "max_spread_pct": max(spreads) if spreads else None,
        "median_spread_pct": (sorted(spreads)[len(spreads) // 2] if spreads else None),
    }

    # ---- invalidated / excluded runs ---------------------------------------
    invalid = []
    for att in all_attempts:
        why = []
        if att["archive"]:
            why.append(f"archived in '{att['archive']}'")
        if att["superseded_by_retry"]:
            why.append("superseded by a later attempt in the same file")
        if att["disposition"] != "complete":
            why.append(f"disposition '{att['disposition']}'")
        if not why:
            continue
        invalid.append({
            "run_id": att["run_id"],
            "task": att["task"],
            "arm": att["arm"],
            "source": att["archive"] or "headline",
            "wall_start": att["wall_start"],
            "usd": round(usd(att), 4),
            "verdict": att["verdict"],
            "disposition": att["disposition"],
            "dnf_reason": att["dnf_reason"],
            "why_excluded": "; ".join(why),
            # Verbatim from the record. Not paraphrased, not shortened: the note
            # is the adjudication, and a summary of an adjudication is an opinion.
            "notes": att["notes"],
            "archive_reason": att["archive_reason"],
        })
    invalid.sort(key=lambda r: (r["source"] != "headline", r["task"], r["arm"],
                                r["wall_start"] or ""))

    # ---- integrity ----------------------------------------------------------
    mismatches = [{
        "run_id": a["run_id"], "source": a["archive"] or "headline",
        "recorded": a["usd_recorded"], "recomputed": a["usd_computed"],
    } for a in all_attempts if a["cost_agrees"] is False]
    unpriceable = [{"run_id": a["run_id"], "source": a["archive"] or "headline",
                    "wall_start": a["wall_start"]}
                   for a in all_attempts if a["usd_computed"] is None]
    bands_used = sorted({a["price_band"] for a in all_attempts if a["price_band"]})
    gaps_declared: dict[str, int] = {}
    for att in counted:
        for gap in att["measurement_gaps"]:
            key = f"{gap.get('pole')}: {gap.get('powod')}"
            gaps_declared[key] = gaps_declared.get(key, 0) + 1

    amendments = read_amendment_headings(amendments_path)

    return {
        "meta": {
            "data_root": os.path.abspath(root),
            "runs_root": os.path.abspath(runs_root),
            "pricing_file": pricing.path,
            "pricing_model_id": pricing.model_id,
            "amendments_file": amendments_path,
            "record_files": len(files),
            "attempts_parsed": len(all_attempts),
            "arms": ARM_LABEL,
        },
        "per_task": rows,
        "totals": totals,
        "exclusions_from_paired_total": exclusions,
        "cumulative": {"points": cumulative, "b_stays_below_a_from": crossing},
        "halves": halves,
        "tokens": token_stats,
        "run_to_run_spread": spread,
        "invalidated_runs": invalid,
        "integrity": {
            "cost_recomputed_from_frozen_table": pricing.available,
            "price_bands_used": bands_used,
            "cost_mismatches": mismatches,
            "runs_we_could_not_price": unpriceable,
            "corrections_appended": sum(1 for a in all_attempts if a["revisions"] > 1),
            "malformed_lines": sum(a["malformed_lines"] for a in all_attempts),
            "declared_measurement_gaps": gaps_declared,
        },
        "amendment_log": amendments,
    }


def read_amendment_headings(path: str | None) -> dict:
    """List the amendment headings so the report cannot quietly omit one.

    We print headings only and point at the file for the text: the analysis owns
    numbers, the amendment log owns protocol history, and paraphrasing the second
    inside the first is how caveats get softened.
    """
    if not path or not os.path.isfile(path):
        return {"file": path, "found": False,
                "note": "amendment log NOT FOUND - protocol changes could not be listed here",
                "headings": []}
    headings = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                headings.append(line.strip("# \n"))
    return {"file": path, "found": True, "note": "", "headings": headings}


# ------------------------------------------------------------------------------
# rendering
# ------------------------------------------------------------------------------

def render(res: dict) -> str:
    out: list[str] = []
    w = out.append
    m = res["meta"]

    w(SEP)
    w("bakeoff-om-bench - Experiment 1 - cost analysis")
    w("produced by analyze.py; every number below is computed from the raw records")
    w(SEP)
    w(f"data root      : {m['data_root']}")
    w(f"record files   : {m['record_files']}  ({m['attempts_parsed']} attempts after "
      f"collapsing append-only corrections)")
    w(f"price table    : {m['pricing_file'] or 'NOT FOUND'}"
      + (f"   model {m['pricing_model_id']}" if m["pricing_model_id"] else ""))
    for arm in ARMS:
        w(f"arm {arm.upper()}          : {ARM_LABEL[arm]}")
    w("")

    # -- 1. per task ----------------------------------------------------------
    w(SEP)
    w("1. PER-TASK RESULTS")
    w(SUB)
    w(f"{'task':<5} {'A cost':>9} {'A gate':>7} {'A rwk':>6} {'A verdict':<10} "
      f"{'B cost':>9} {'B gate':>7} {'B rwk':>6} {'B verdict':<10} {'B vs A':>8}  status")
    for row in res["per_task"]:
        a, b = row["a"], row["b"]
        status = "paired" if row["paired"] else "NOT PAIRED - excluded from totals"
        w(f"{row['task']:<5} {fmt_usd(a['usd']):>9} {str(a['gate_runs'] or '-'):>7} "
          f"{str(a['rework_iterations'] if a['rework_iterations'] is not None else '-'):>6} "
          f"{str(a['verdict'] or '-'):<10} "
          f"{fmt_usd(b['usd']):>9} {str(b['gate_runs'] or '-'):>7} "
          f"{str(b['rework_iterations'] if b['rework_iterations'] is not None else '-'):>6} "
          f"{str(b['verdict'] or '-'):<10} {fmt_pct(row['delta_pct']):>8}  {status}")
    w("")
    w("  'gate' = how many times the runner validated the work (the judge is the")
    w("  runner, not either arm). 'rwk' = rework iterations after a red gate.")
    w("  A dash in a cost column is an ABSENT measurement, not a zero.")
    w("")

    # -- 2. totals ------------------------------------------------------------
    t = res["totals"]
    w(SEP)
    w("2. TOTALS")
    w(SUB)
    w("Per-arm totals over each arm's own completed tasks (DIFFERENT task sets -")
    w("printed for transparency, NOT a head-to-head number):")
    for arm in ARMS:
        u = t["unpaired"][arm]
        w(f"  arm {arm.upper()}: ${u['usd']:.4f} over {u['n_tasks']} tasks "
          f"({', '.join(u['tasks'])})")
    w("")
    w("PAIRED TOTAL - the head-to-head number. Only tasks completed by BOTH arms:")
    pa, pb = t["paired"]["a"], t["paired"]["b"]
    w(f"  tasks in comparison ({pa['n_tasks']}): {', '.join(pa['tasks'])}")
    w(f"  arm A : ${pa['usd']:.4f}")
    w(f"  arm B : ${pb['usd']:.4f}")
    w(f"  difference: {t['paired']['delta_usd']:+.4f} USD  "
      f"({fmt_pct(t['paired']['delta_pct'])} for arm B)")
    w(f"  arm B cheaper in {t['paired']['b_cheaper_in']} of {t['paired']['of_pairs']} pairs")
    w("")
    w("Excluded from the paired total (reason read from the record, never guessed):")
    if not res["exclusions_from_paired_total"]:
        w("  (none)")
    for ex in res["exclusions_from_paired_total"]:
        head = (f"  {ex['task']} arm {ex['arm'].upper()}: disposition "
                f"'{ex['disposition']}'")
        if ex["usd_would_have_been"] is not None:
            head += (f" - this run IS complete (${ex['usd_would_have_been']:.4f}) but its "
                     f"counterpart is not, so the task cannot be paired")
        w(head)
        if ex["reason"]:
            w(f"      reason (verbatim): {ex['reason']}")
    w("")

    # -- 3. cumulative --------------------------------------------------------
    c = res["cumulative"]
    w(SEP)
    w("3. CUMULATIVE COST ACROSS THE SERIES (paired tasks only)")
    w(SUB)
    w(f"{'task':<6} {'cum A':>10} {'cum B':>10}  B below A?")
    for p in c["points"]:
        w(f"{p['task']:<6} {p['cum_a']:10.4f} {p['cum_b']:10.4f}  "
          f"{'yes' if p['b_below_a'] else 'no'}")
    w("")
    if c["b_stays_below_a_from"]:
        w(f"  arm B's cumulative cost stays below arm A's from {c['b_stays_below_a_from']} "
          f"through the end of the series.")
    else:
        w("  arm B's cumulative cost NEVER stays below arm A's through the end of the "
          "series.")
    w("")

    # -- 4. halves ------------------------------------------------------------
    h = res["halves"]
    w(SEP)
    w("4. EARLY vs LATE HALF OF THE SERIES")
    w(SUB)
    w(f"split rule: {h['split_rule']}")
    for name in ("early", "late"):
        s = h[name]
        w(f"  {name:<5} ({s['n_tasks']} tasks: {', '.join(s['tasks'])})")
        w(f"        arm A ${s['a_usd']:.4f}   arm B ${s['b_usd']:.4f}   "
          f"B vs A {fmt_pct(s['delta_pct'])}")
        w(f"        mean 1-min machine load during those runs: "
          f"A {s['mean_load_1m']['a']}, B {s['mean_load_1m']['b']}")
    w("")
    w("  *** CONFOUNDED - READ BEFORE QUOTING THESE TWO NUMBERS ***")
    w("  The early/late split is NOT a clean measurement of 'does the method pay off")
    w("  later in a series'. At least three things move together with task position,")
    w("  and this data cannot separate them:")
    g = h["pairing_gap_hours"]
    if g["n"]:
        w(f"   (a) The two arms did not run side by side. Wall-clock gap between the two")
        w(f"       arms' start of the SAME task: median {g['median']} h, range "
          f"{g['min']}-{g['max']} h over {g['n']} pairs. Machine load, time of day and")
        w("       any drift in the environment therefore differ per arm, not just per task.")
    order = h["executed_in_task_order"]
    if all(order.values()):
        w("   (b) Both arms executed the tasks in numeric order, so 'early task' and")
        w("       'early wall-clock' are the same axis here. A position effect and a")
        w("       time-of-day effect are indistinguishable by construction.")
    w("   (c) Protocol amendments landed DURING the series (see the amendment log at")
    w("       the end of this report). Anything fixed mid-series separates the early")
    w("       tasks from the late ones for a reason that has nothing to do with method.")
    w("")

    # -- 5. tokens ------------------------------------------------------------
    w(SEP)
    w("5. TOKEN CLASSES AND WHERE THE MONEY ACTUALLY GOES")
    w(SUB)
    for arm in ARMS:
        s = res["tokens"][arm]
        w(f"arm {arm.upper()} ({ARM_LABEL[arm]}) - {s['n_runs']} counted runs")
        w(f"  {'class':<20} {'tokens':>14} {'% tokens':>9} {'cost USD':>10} {'% cost':>8}")
        for cls in TOKEN_CLASSES:
            w(f"  {cls:<20} {s['tokens'][cls]:>14,} "
              f"{fmt_pct(s['token_share_pct'][cls], sign=False):>9} "
              f"{s['cost'][cls]:>10.4f} "
              f"{fmt_pct(s['cost_share_pct'][cls], sign=False):>8}")
        w(f"  {'TOTAL':<20} {s['tokens_total_priced']:>14,} {'100.0%':>9} "
          f"{s['cost_total']:>10.4f} {'100.0%':>8}")
        w(f"  {TOKEN_CLASS_INFO:<20} {s['tokens'][TOKEN_CLASS_INFO]:>14,}   "
          f"(informational: a subset of 'out', already priced inside it - NOT added)")
        w(f"  cache_read is {fmt_pct(s['cache_read_token_share_pct'], sign=False)} of "
          f"tokens but {fmt_pct(s['cache_read_cost_share_pct'], sign=False)} of cost.")
        w("")
    w("  Cached reads are billed at a tenth of input, which is why they dominate the")
    w("  token counts without dominating the bill. Any comparison that counts raw")
    w("  tokens instead of dollars will therefore say something different from this")
    w("  report - the primary endpoint is imputed dollars.")
    w("")

    # -- 6. run-to-run spread -------------------------------------------------
    sp = res["run_to_run_spread"]
    w(SEP)
    w("6. RUN-TO-RUN SPREAD (how much does the same task, same arm, move?)")
    w(SUB)
    w(f"repeat groups (same task, same arm, run more than once): "
      f"N = {sp['n_repeat_groups']}")
    w(f"pairwise comparisons available:                          N = "
      f"{sp['n_pairwise_comparisons']}")
    w(f"of those groups, repeats under IDENTICAL conditions:     N = "
      f"{sp['n_groups_under_identical_conditions']}")
    w("")
    if sp["groups"]:
        w(f"  {'task':<6} {'arm':<4} {'runs':>5} {'min USD':>9} {'max USD':>9} "
          f"{'spread':>8}  sources")
        for grp in sp["groups"]:
            sources = ", ".join(f"{r['source']} ${r['usd']:.4f}" for r in grp["runs"])
            w(f"  {grp['task']:<6} {grp['arm'].upper():<4} {grp['n_runs']:>5} "
              f"{grp['min_usd']:>9.4f} {grp['max_usd']:>9.4f} "
              f"{fmt_pct(grp['spread_pct'], sign=False):>8}  {sources}")
        w("")
        w(f"  spread across groups: min {fmt_pct(sp['min_spread_pct'], sign=False)}, "
          f"median {fmt_pct(sp['median_spread_pct'], sign=False)}, "
          f"max {fmt_pct(sp['max_spread_pct'], sign=False)}")
    else:
        w("  No task was run twice by the same arm anywhere in this data set, so")
        w("  run-to-run variation is NOT MEASURED here. It is not thereby small.")
    w("")
    w("  *** WHAT THIS NUMBER IS AND IS NOT ***")
    if sp["n_groups_under_identical_conditions"] == 0 and sp["groups"]:
        w("  Every repeat we have comes from runs that differ by a KNOWN condition -")
        w("  they sit in different archives, which is to say they were disqualified for")
        w("  a stated reason and then redone after something was changed. So the spread")
        w("  above mixes run-to-run randomness with the effect of that change and is an")
        w("  UPPER BOUND on noise, not an estimate of it. We have ZERO repeats under")
        w("  identical conditions; the honest statement is that run-to-run noise in this")
        w("  series was NOT CLEANLY MEASURED.")
    total_delta = res["totals"]["paired"]["delta_pct"]
    if sp["median_spread_pct"] is not None and total_delta is not None:
        w("")
        w(f"  For scale: the headline series difference is {fmt_pct(total_delta)}, while the")
        w(f"  median observed spread between two runs of the SAME task by the SAME arm is")
        w(f"  {fmt_pct(sp['median_spread_pct'], sign=False)} (max "
          f"{fmt_pct(sp['max_spread_pct'], sign=False)}). The effect is well inside the")
        w("  noise we can see. This is an exploratory series with n=1 pair, not a")
        w("  significance test, and it must not be read as one.")
    w("")

    # -- 7. invalidated runs --------------------------------------------------
    w(SEP)
    w("7. EVERY INVALIDATED OR EXCLUDED RUN, WITH ITS REASON")
    w(SUB)
    w(f"{len(res['invalidated_runs'])} runs are recorded but do not enter any statistic.")
    w("Nothing here was deleted; notes are reproduced verbatim from the record.")
    w("")
    for r in res["invalidated_runs"]:
        w(f"  {r['run_id']}  [{r['source']}]  started {r['wall_start']}")
        w(f"      verdict={r['verdict']}  disposition={r['disposition']}"
          + (f"  dnf_reason={r['dnf_reason']}" if r["dnf_reason"] else "")
          + f"  imputed=${r['usd']:.4f}")
        w(f"      excluded because: {r['why_excluded']}")
        if r["notes"]:
            w(f"      note (verbatim): {r['notes']}")
        elif r["archive_reason"]:
            w(f"      archive says: {r['archive_reason']}")
        else:
            w("      note: EMPTY - this run carries no written reason of its own")
        w("")

    # -- 8. integrity ---------------------------------------------------------
    it = res["integrity"]
    w(SEP)
    w("8. INTEGRITY CHECKS")
    w(SUB)
    if it["cost_recomputed_from_frozen_table"]:
        w("  Every cost above was recomputed here from the run's own token counts and")
        w("  the frozen dated price table; the recorded figure was not trusted.")
        w(f"  price bands actually used: {', '.join(it['price_bands_used']) or 'none'}")
        if len(it["price_bands_used"]) > 1:
            w("  NOTE: runs fall in more than one price band - the table changed mid-series.")
        w(f"  cost disagreements (recorded vs recomputed): {len(it['cost_mismatches'])}")
        for mm in it["cost_mismatches"]:
            w(f"      {mm['run_id']} [{mm['source']}]: recorded {mm['recorded']}, "
              f"recomputed {mm['recomputed']}")
    else:
        w("  PRICE TABLE NOT FOUND - costs could NOT be recomputed and are reproduced")
        w("  from the records as-is. This is a measurement gap, not a clean bill.")
    if it["runs_we_could_not_price"]:
        w(f"  runs we could not price ourselves: {len(it['runs_we_could_not_price'])}")
        for u in it["runs_we_could_not_price"]:
            w(f"      {u['run_id']} [{u['source']}] wall_start={u['wall_start']}")
    w(f"  append-only corrections found in the records: {it['corrections_appended']}")
    w(f"  unparseable lines skipped: {it['malformed_lines']}")
    w("")
    w("  Fields the instrument itself declared it could not measure:")
    if it["declared_measurement_gaps"]:
        for key, count in sorted(it["declared_measurement_gaps"].items()):
            w(f"      {key}  (on {count} counted runs)")
    else:
        w("      (none declared)")
    w("")

    # -- 9. amendment log -----------------------------------------------------
    am = res["amendment_log"]
    w(SEP)
    w("9. PROTOCOL AMENDMENTS DURING THE SERIES")
    w(SUB)
    if am["found"]:
        w(f"  Full text: {am['file']}. Headings only, so nothing gets softened in")
        w("  paraphrase. Each of these changed the protocol WHILE the series ran and")
        w("  belongs in any reading of the numbers above:")
        for heading in am["headings"]:
            w(f"      {heading}")
    else:
        w(f"  {am['note']}")
    w("")
    w(SEP)
    return "\n".join(out)


# ------------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Reproduce the Experiment-1 cost analysis from the raw records.",
        epilog="Standard library only; reads local files only; makes no network calls.")
    ap.add_argument("data", help="path to the published data directory (e.g. data/)")
    ap.add_argument("--json", action="store_true",
                    help="emit the same numbers as JSON instead of a report")
    ap.add_argument("--pricing", default=None,
                    help="override the path to the frozen pricing.json")
    ap.add_argument("--amendments", default=None,
                    help="override the path to the frozen AMENDMENTS.md")
    ap.add_argument("--split-at", type=int, default=None, metavar="N",
                    help="cut the series into halves after the Nth PAIRED task "
                         "instead of at the median; the report states which cut was used")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.data):
        print(f"analyze.py: not a directory: {args.data}", file=sys.stderr)
        return 2

    res = analyse(args.data,
                  find_pricing(args.data, args.pricing),
                  find_amendments(args.data, args.amendments),
                  args.split_at)

    if not res["per_task"]:
        print(f"analyze.py: no run records found under {res['meta']['runs_root']}",
              file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=False))
    else:
        print(render(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
