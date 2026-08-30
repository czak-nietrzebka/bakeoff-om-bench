#!/usr/bin/env python3
"""Maintenance phase — per-task cost table plus the pre-registered mechanism
check, recomputed from data-emaint/runs and data/judge. Same contract as
analyze.py: numbers come from records, not from the report."""
import json, sys, glob, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "data-emaint"


def best(path):
    """Primary = the FIRST verified record. Three of arm B's tasks carry a second
    verified run (an orphaned runner instance repeated M2-M4 the same evening —
    the records were left in, append-only); those repeats are reported separately
    below as noise data, never silently averaged or cherry-picked."""
    rs = [json.loads(l) for l in open(path)]
    v = [r for r in rs if r.get("verdict") == "verified"]
    return (v[0] if v else rs[-1]), len(rs), v


def main():
    A, B, kor = {}, {}, 0
    for f in sorted(glob.glob(os.path.join(ROOT, "runs", "em-M*.jsonl"))):
        d, n, vall = best(f)
        kor += n - 1
        d["_repeats"] = vall
        (A if d["arm"] == "a" else B)[d["task"]] = d
    print("Maintenance phase (E-MAINT) — Claude Sonnet, fresh sessions on frozen bases")
    print("records: %d slots, %d append-only corrections/voids collapsed" % (len(A) + len(B), kor))
    print()
    print("task     A cost  A rwk verdict      B cost  B rwk verdict     B vs A")
    sa = sb = wins = pairs = 0
    for i in range(1, 7):
        t = "M%d" % i
        a, b = A.get(t), B.get(t)
        if not a or not b:
            print("%-5s MISSING" % t)
            continue
        ua, ub = a.get("usd_imputed") or 0, b.get("usd_imputed") or 0
        ok = a["verdict"] == "verified" and b["verdict"] == "verified"
        if ok:
            sa += ua; sb += ub; pairs += 1; wins += ub < ua
        print("%-5s %7.4f %5s %-9s | %7.4f %5s %-9s | %+7.1f%%"
              % (t, ua, a.get("rework_iterations"), a["verdict"][:9],
                 ub, b.get("rework_iterations"), b["verdict"][:9],
                 ((ub - ua) / ua * 100) if ua else 0))
    print()
    print("PAIRED (verified both): %d pairs | A $%.4f | B $%.4f | %+0.1f%% | B cheaper in %d/%d"
          % (pairs, sa, sb, (sb - sa) / sa * 100 if sa else 0, wins, pairs))
    print()
    print("REPEATS (unplanned, kept append-only): task slots with >1 verified run")
    for D, arm_label in ((A, "A"), (B, "B")):
        for t in sorted(D, key=lambda x: int(x[1:])):
            rep = D[t].get("_repeats") or []
            if len(rep) > 1:
                ceny = [r.get("usd_imputed") or 0 for r in rep]
                lo, hi = min(ceny), max(ceny)
                print("  %s-%s: %d runs, $%.4f-$%.4f, spread %.1f%%"
                      % (t, arm_label, len(rep), lo, hi, (hi - lo) / lo * 100 if lo else 0))
    print()
    print("MECHANISM CHECK (pre-registered): did the fresh session read the trail?")
    print("Counted from session transcripts during the phase (observable, not asked):")
    print("  arm A: git-history reads 1 (one task, once); ticket/PR reads 0")
    print("  arm B: git-history reads 14 (6 of 6 tasks); ticket/PR reads 25 (6 of 6)")
    print("Those four numbers are TRANSCRIBED, not computed. The two lines above are")
    print("literals in this script; no record in data-emaint carries a read count, so")
    print("nothing here recomputes them. The transcripts are not published (see")
    print("data/README.md), the finest published grain is the arm-level table in")
    print("REPORT-EMAINT.md, and the package contains no per-task rows. Everything")
    print("else this script prints IS computed from the published records.")


if __name__ == "__main__":
    main()
