# Maintenance phase — results

**Six maintenance tasks against the modules both arms built in Experiment 1, each
handed to a fresh session with no memory, each starting from an identical frozen
baseline. On cost the process arm loses: +47.8%, cheaper in 2 of 6. On the
pre-registered mechanism check it wins outright: the process arm read the git
history in six tasks out of six and pulled the original tickets and pull requests
twenty-five times; the naive arm read history once, ever, and never opened a
ticket. This phase is where the benchmark's actual thesis lives, and this is the
first hard evidence for it.**

Pre-registration: `emaint/PROTOCOL.md`, published before the first result, including
the declared baselines, verdict rules relative to a measured-red repository suite,
stop rules, and the five defects its control step caught before any arm started.
Task texts and scoring rules: `emaint/specs/`. Raw records: `data-emaint/runs/`.
Recompute:

    python3 analyze_emaint.py data-emaint

## Result

| task | arm A | arm B | B vs A |
|---|---:|---:|---:|
| M1 bug report in business language | $3.01 | $3.20 | +6.4% |
| M2 policy extension (one predicate) | $0.43 | $2.13 | +388.9% |
| M3 business reversal (class L) | $1.38 | $2.13 | +54.5% |
| M4 audit report vs closed answer key | $0.96 | $2.54 | +165.3% |
| M5 "quick tool, no philosophy" | $1.81 | $1.79 | **−1.3%** |
| M6 read-only stats command | $1.01 | $0.94 | **−7.5%** |
| **paired total** | **$8.61** | **$12.72** | **+47.8%** |

All twelve slots verified. The phase needed two calendar runs: the first was killed
mid-flight when the shared subscription pool hit its limit (the interruption rule
from Experiment 1's entry 23 was applied — voids, not failures), and the rerun
completed on a different account with the arms' account symlinks swapped; cost is
imputed from tokens and unaffected by whose subscription carried them.

**Unplanned repeats.** An orphaned runner instance re-ran three of arm B's tasks
(and one of arm A's) the same evening; both runs of each are verified and both are
kept, append-only. Primary numbers above use the first verified run; the repeats
give the phase its only same-conditions noise estimate: spreads of 2.4%, 9.4%,
28.7% and 32.1% between two verified runs of the same task by the same arm. The
+47.8% headline should be read against that band — individual task deltas inside
±30% are weather.

## The mechanism check — the pre-registered point of the phase

The thesis under test was never "the process writes better code"; it was "a later
stranger is cheaper because intent is reconstructible from what the process left."
Measured from session transcripts (counted, not asked):

| | git-history reads | ticket / PR reads |
|---|---:|---:|
| arm A (naive) | 1 (one task, once) | 0 |
| arm B (process) | 14 — in 6 of 6 tasks | 25 — in 6 of 6 tasks |

Those four numbers carry different evidential weight from every cost figure in this
report, and it is worth saying so where they are stated rather than in a footnote. The
costs are computed from the published records and anyone can recompute them. These
counts are **transcribed**: they are literals in `analyze_emaint.py`, no record in
`data-emaint` carries a read-count field, and the package publishes this arm-level
table and nothing finer — no per-task rows, and no definition of what was counted as
one read. A reader can check what is claimed here. A reader cannot recount it.

The stranger demonstrably reconstructs from the trail. What the trail did **not**
do in this phase is make the stranger cheaper — the reconstruction happened *on
top of* the process's fixed overhead, not instead of it. The honest reading: the
mechanism works; on tasks this small its payoff does not clear its cost. Where the
payoff showed up instead was outside the measurement: the trail this phase left is
the same class of exhaust that later rebuilt this repository's destroyed working
copy to the cent (logbook entry 27).

## Quality

Per-task judging (two blind repetitions per arm on the M5/M6 pairs — the only
pairs where both arms' products survived; arm A's M1-M4 product trees were
destroyed by a harness defect fixed mid-phase, `data/judge/emaint-judge.jsonl`):
M5 scored low for **both** arms (spec-fidelity 2/5 each — "no philosophy" cut both
ways), M6 mildly favoured B with judge variance wider than the gap. At n=2
repetitions this instrument does not separate the arms, and we say so rather than
quote the direction.

## Confounds, declared

- Arm A's per-task products for M1-M4 were destroyed by the baseline-restore
  defect (caught and fixed mid-phase; products archived from then on) — secondary
  observables for those four A-slots are unmeasurable, marked as such in records.
- The account swap mid-phase (limit death → rerun on a different subscription) is
  visible in the records' timing; token-imputed cost is account-independent.
- M4's answer key was frozen against pinned module snapshots and verified against
  them before scoring.

-- lee
