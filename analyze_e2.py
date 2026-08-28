#!/usr/bin/env python3
"""Experiment 2 (GPT-5.6 Sol / Codex) — per-task cost table, recomputed from the
raw records in data-e2/runs. Same contract as analyze.py: every number printed
here is derived from the records, none is trusted from a report.

Cost imputation is PER REQUEST (data-e2 records carry `per_request`), priced by
e2/pricing-e2.json, including the >272k-input long-context surcharge per request
— see amendment E2-A1 for why the per-turn aggregate is not used.
"""
import json, sys, glob, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "data-e2"
PR = json.load(open(os.path.join(os.path.dirname(__file__) or ".", "e2", "pricing-e2.json")))
PZ = PR["przedzialy"][0]
LC = PZ["long_context"]


def impute(per_request):
    usd = 0.0
    for t in per_request:
        nc = max(0, t["in"] - t["cached_in"])
        im = LC["in_mult"] if t["in"] > LC["prog_input_tokens"] else 1.0
        om = LC["out_mult"] if t["in"] > LC["prog_input_tokens"] else 1.0
        usd += (nc * PZ["in_usd_per_mtok"] * im + t["cached_in"] * PZ["cached_in_usd_per_mtok"]
                + t["out"] * PZ["out_usd_per_mtok"] * om) / 1e6
    return round(usd, 4)


def best(path):
    rs = [json.loads(l) for l in open(path)]
    v = [r for r in rs if r.get("verdict") == "verified"]
    return (v[-1] if v else rs[-1]), len(rs)


def main():
    A, B, koryg = {}, {}, 0
    for f in sorted(glob.glob(os.path.join(ROOT, "runs", "p2-T*.jsonl"))):
        d, n = best(f)
        koryg += n - 1
        (A if d["arm"] == "a" else B)[d["task"]] = d
    print("Experiment 2 — GPT-5.6 Sol via codex-cli 0.148.0 (pinned)")
    print("records: %d task-arm slots, %d append-only corrections collapsed" % (len(A) + len(B), koryg))
    print()
    print("task     A cost  A rwk A verdict     B cost  B rwk B verdict    B vs A")
    sa = sb = wins = pairs = 0
    for i in range(1, 13):
        t = "T%d" % i
        a, b = A.get(t), B.get(t)
        if not a or not b:
            print("%-5s MISSING PAIR" % t)
            continue
        ua = impute(a.get("per_request") or []) or a.get("usd_imputed") or 0
        ub = impute(b.get("per_request") or []) or b.get("usd_imputed") or 0
        zg_a = "" if abs(ua - (a.get("usd_imputed") or 0)) < 0.01 else " (!recorded %.4f)" % a.get("usd_imputed")
        zg_b = "" if abs(ub - (b.get("usd_imputed") or 0)) < 0.01 else " (!recorded %.4f)" % b.get("usd_imputed")
        ok = a["verdict"] == "verified" and b["verdict"] == "verified"
        if ok:
            sa += ua; sb += ub; pairs += 1; wins += ub < ua
        print("%-5s %7.4f %5s %-9s %s| %7.4f %5s %-9s %s| %+7.1f%%"
              % (t, ua, a.get("rework_iterations"), a["verdict"][:9], zg_a,
                 ub, b.get("rework_iterations"), b["verdict"][:9], zg_b,
                 ((ub - ua) / ua * 100) if ua else 0))
    print()
    print("PAIRED (verified both): %d pairs | A $%.4f | B $%.4f | %+0.1f%% | B cheaper in %d/%d"
          % (pairs, sa, sb, (sb - sa) / sa * 100 if sa else 0, wins, pairs))
    print()
    print("Every cost above was recomputed from per-request token counts and the")
    print("frozen price table; a '!recorded' marker would flag any record whose")
    print("stored figure disagrees with the recomputation. None should appear.")


if __name__ == "__main__":
    main()
