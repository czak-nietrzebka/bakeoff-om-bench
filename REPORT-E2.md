# Experiment 2 — results (GPT-5.6 Sol via Codex)

**The same twelve frozen tasks, the same hidden packs, the same gate — a different
engine. On cost the process arm loses decisively: +135.6% over eleven verified pairs,
cheaper in none of them. On quality every instrument comes back level or against the
process arm. This is the experiment the 2×2 design existed to run, and its answer is
that the process's price is not a property of one model — it is roughly constant in
tokens, so the cheaper the engine, the worse it prices.**

Pre-registration: `e2/PROTOCOL-E2.md`, committed before any run, with every declared
difference from Experiment 1 (engine pin, per-request accounting, no stateful
containers, one shared account, working-token metric, price table). Amendments made
during calibration: `LOGBOOK.md`. Raw records: `data-e2/runs/`, one JSONL per
task-arm, append-only, with per-request token usage embedded. Recompute the table:

    python3 analyze_e2.py data-e2

## Result

| | arm A (codex, naive) | arm B (codex under the process) |
|---|---|---|
| paired total, 11 verified pairs | **$18.03** | **$42.47 (+135.6%)** |
| pairs won on cost | 11 | 0 |
| verified | 12 of 12 | 11 of 12 (T9: DNF on the token budget, red gate on the widget pack) |
| requests / task (mean) | 30.6 | 59.2 |
| engine sessions / task | 1.1 | 2.2 |

Per-task deltas range from +40.8% (T12) to +433.6% (T4). T9 is the only task either
arm failed outright in any phase of this benchmark: arm B burned its class budget
without turning the widget pack green. That is a real defeat of the method on this
engine, and it also costs arm B its spec-fidelity score with the judge below.

## Quality — every instrument, both directions

- **Frozen four-axis judge** (three blind repetitions per arm, cumulative diffs,
  `data/judge/e2-judge.jsonl`): **A 52/60, B 47/60.** B's deficit is concentrated in
  axis (a), spec fidelity — partly the honest price of the missing T9. Axis (b),
  repo conventions: one +1 for B in one repetition, otherwise level.
- **Deterministic convention checklist** (frozen R8: tenant scoping, cross-module
  imports, i18n across five locales, console noise, time-bombs): **identical for
  both arms**, to the row. The naive arm additionally opted its module into the
  repository's design-system lint on its own initiative — an unprompted
  quality-positive act by the unprocessed engine, reported as found.
- **Self-review share of arm B's cost: ~2%.** The overhead lives in the agent
  sessions under the dispatcher, not in the quality gates.

## What this experiment adds to the 2×2

Experiment 1 (Claude Sonnet) ended in a cost tie inside the noise band. This
experiment breaks the symmetry: the same process, on an engine that finishes the
same tasks for a quarter of the tokens, costs +135.6% instead of −3%. Combined
with the maintenance phase (+48% on the same engine as Experiment 1), the pattern
is consistent: **the process overhead is approximately fixed per task in tokens;
its relative price is a function of engine efficiency, not of the process.** Any
pitch for this method that leads with per-task cost is now measurably wrong on two
of three phases; what it can lead with is in the maintenance report's mechanism
check and in the main README's "what the overhead buys" section.

## Confounds and caveats, declared

- One ChatGPT account served both arms (declared in the protocol before the runs) —
  and it turned out to also serve a live production agent of ours; series accounting
  is immune (closed world = each spawned process's own stdout plus its session
  rollout, reconciled to the token), but plan limits were shared.
- The calibration pilot burned six attempts on harness defects before the first
  clean pair (ticket hijacking across experiments, a sandbox that mounted `.git`
  read-only making commits impossible, an error classifier that matched the
  substring "limit" inside a repository module name, a deployment path typo, a +40%
  cost-imputation bias). All are in `LOGBOOK.md`; none of
  the burned attempts entered the series, and their costs are booked as voids in
  the pilot records.
- Arms ran serially overnight on an otherwise idle host; wall-clock comparisons
  remain within-arm only.
- The working-token DNF budgets were calibrated for Claude token classes; the
  mapping for this engine is declared in the protocol (D5) and T9's DNF fired
  under it. A budget tuned to this engine's token economics might have let T9
  finish; that is a protocol property, stated, not adjudicated away.

-- lee
