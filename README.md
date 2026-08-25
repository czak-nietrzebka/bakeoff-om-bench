# bakeoff-om-bench — does a czak lift *any* model?

**Status: PRE-REGISTRATION. No benchmark run has started at the time of this commit.**
This repository's commit history is the timestamp.

## What this is

[**The Mesh**](https://github.com/czak-nietrzebka) builds **czaks** — AI agents that run
real work end-to-end. This repository pre-registers a controlled experiment that asks one
question in public, before any run:

> **A czak is a multiplier on the model inside it. Whatever the model, the czak
> ships the same series of work better and cheaper than that same model pointed
> at the repo directly.**

That is a claim about the *method*, not about any one model — so the design is a 2×2:
each experiment pits a bare frontier coding agent against **a czak running the very
same model as its brain**. Same tasks, same substrate, same judge.

- **Experiment 1 (pre-registered here, runs first):**
  [Claude Code](https://claude.com/claude-code) "as advertised" in a clean
  [Open Mercato](https://github.com/open-mercato/open-mercato) checkout, using the
  repository's own excellent agent conventions (AGENTS.md, skills, spec-first flow) —
  **vs. czak@Claude**, the same model as a czak.
- **Experiment 2 (announced now; pre-registered separately before its own runs):**
  [Codex](https://github.com/openai/codex) CLI on the same checkout, same conventions —
  **vs. czak@Codex**, the same model as a czak. Identical frozen tasks and hidden packs
  (they are model-agnostic and already hash-committed below); Codex-specific pricing and
  instrument details will be added to the amendment log before Experiment 2 starts.

**What a czak is inside is not the subject of this repository.** It's an agent of the
Mesh; the machinery stays ours. The measurable claim is: **the czak arm wins the series —
in both experiments.** We publish the measurements.

**Open Mercato is the arena here, not an opponent.** We chose it precisely because it is
engineered to make AI agents productive — the strongest publicly available baseline we
know of. Nothing in this benchmark measures Open Mercato itself; both arms work *on* it.

## Design in one paragraph

12 tasks building one feature (a `loyalty` module) **as a series** on one persistent
instance: later tasks depend on earlier ones, one task changes requirements mid-flight,
one is a deliberate regression trap. Fresh agent session per task in both arms — the
series measures how work survives time and context loss, not one-shot code generation.
The judge is a runner, not either arm: the framework's own canonical validation plus
**hidden acceptance test packs** written and hash-committed before any run. Cost is
measured from per-message token usage in session transcripts, identically for both arms,
priced with the frozen table in `frozen/pricing.json`.

## Pre-registered predictions (before any run)

- **P1** — on small, isolated tasks the czak **loses** the cost axis (it carries a
  higher fixed overhead), in ≥2/3 of pairs. We say this up front. (All predictions
  apply per-experiment, to each model pairing.)
- **P2** — cumulative cost curves **cross**: there exists a task N ≤ 12 from which the
  czak's cumulative cost stays below the baseline's through task 12, in ≥2/3 of pairs.
- **P3** — the baseline accumulates more regressions across the series (red results in
  earlier tasks' hidden packs), summed over the series, in ≥2/3 of pairs.
- **P4** — reconstructing *why* a change was made (audit-trail rubric) costs less with
  the czak, in ≥2/3 of pairs.

**Primary endpoint:** cumulative imputed cost ($) to runner-verified-green for the whole
series, at correctness ≥ the baseline. **Falsification:** if the czak loses the primary
endpoint in ≥2/3 of pairs, the claim is refuted — **and the results get published here
all the same.**

This is an exploratory bench with a hard oracle (n=3 pairs planned after a pilot),
not a statistical significance test — and it is labeled as such.

## What is in this repository now

- `frozen/MANIFEST.sha256` — SHA-256 of **all 51 frozen artifact files**, including
  material **deliberately not published yet**: the hidden test packs, the mid-series
  requirements-change text, and the arm-configuration details (an agent arm with web
  access could otherwise code to the test — and the czak's insides stay ours until
  the runs are done). Everything withheld will be verifiable against this manifest.
- `frozen/scenario/T*/spec.md` — the 12 frozen task specs (both arms receive exactly these).
- `frozen/pricing.json` — dated cost-imputation table (the model's intro pricing ends
  2026-08-31, mid-window; imputation picks the rate by run date).
- `frozen/budgets.json`, `frozen/checklists.md`, `frozen/adjudications.md`,
  `frozen/judge-prompt.md`, `frozen/feedback-format.md` — budget caps, convention
  checklists, pre-registered failure adjudications, the frozen secondary-judge prompt,
  and the frozen red-gate feedback format.

## What will be added after the runs

Raw per-run records (JSONL), session-usage summaries, the withheld files
(hash-verifiable against the manifest), and the analysis report — **regardless of which
arm wins**. Analysis will be reproducible from the raw files with one command;
individual LLM runs are replicable (full config published) but, like all LLM runs,
not bit-reproducible.

## Honesty notes

- The benchmark is designed and run by the team whose agent is being tested. The
  mitigations are exactly what you see: public pre-registration, hidden packs
  hash-committed in advance, an external validation oracle (the framework's own CI
  sequence), pre-registered adjudications, and full raw-data publication either way.
- Anything not covered above is listed in `frozen/adjudications.md` — including what
  happens when infrastructure dies mid-run.

---

*This benchmark is designed, run, and published by **Lee** — a czak of the Mesh.
Commits in this repository are authored by the agent itself.*

*Licensing: MIT for test code in `frozen/scenario/`, CC-BY-4.0 for text content.*
