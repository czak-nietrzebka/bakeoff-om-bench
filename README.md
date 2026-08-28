# bakeoff-om-bench — does a czak lift *any* model?

**Status: EXPERIMENT 1 IS COMPLETE — twelve tasks, twelve of twelve verified in both
arms — AND ITS RESULTS ARE PUBLISHED HERE.**
One pair of arms. **On the primary endpoint the two arms finish in a tie inside the noise
band, and the pre-registered crossover prediction failed.** The maintenance phase that
Experiment 1 could not answer is **pre-registered and running**: see
[`emaint/PROTOCOL.md`](emaint/PROTOCOL.md), published before its first result existed.
**Experiment 2 — the same twelve frozen tasks on GPT-5.6 Sol through the Codex CLI —
is pre-registered** ([`e2/PROTOCOL-E2.md`](e2/PROTOCOL-E2.md), with its frozen price
table, driver manifest and measured symmetry table) and its calibration pilot is
running; no counted run existed when the pre-registration was committed.

The full analysis is in **[`REPORT.md`](REPORT.md)**, with the raw records it is computed
from and the two scripts that compute it. The pre-registration below is unchanged from the
commit that predates every run — see *[Checking the pre-registration](#checking-the-pre-registration)*.

## What is here now

| what | where |
|---|---|
| The analysis — result, quality, trail, and everything that went wrong on our side | [`REPORT.md`](REPORT.md) |
| The running record of the experiment: what was run, what broke, what was rewritten and when | [`LOGBOOK.md`](LOGBOOK.md) |
| Raw per-run records (append-only JSONL), the run journal, session-usage summaries, and a field dictionary | [`data/`](data/) — start with [`data/README.md`](data/README.md) |
| The primary instrument: recomputes every dollar from raw token counts | [`analyze.py`](analyze.py) — `python3 analyze.py data/` |
| The size-class, half/load, effort and per-run cuts | [`derived.py`](derived.py) — `python3 derived.py data/` |
| Every protocol amendment made during and after the series, in order, with its direction | [`frozen/AMENDMENTS.md`](frozen/AMENDMENTS.md) |
| What is still withheld from `frozen/`, why, and how to check it when it is released | [`frozen/WITHHELD.md`](frozen/WITHHELD.md) |
| **The maintenance phase, pre-registered before its first result** — design, baselines, verdict rules, stop rules, and the five defects its control step caught | [`emaint/PROTOCOL.md`](emaint/PROTOCOL.md) |
| The six maintenance task texts and their scoring rules, published now; packs and answer keys held under hash until results | [`emaint/specs/`](emaint/specs/), [`emaint/WITHHELD.md`](emaint/WITHHELD.md) |
| The declared differences between the arms (published as a redaction, not byte-identical to its frozen original) | [`frozen/symmetry-table.md`](frozen/symmetry-table.md) |

**What the numbers say, in one place.** Over the twelve tasks both arms completed, arm A
cost **$43.58** and arm B **$42.29** — **−3.0%** for the czak arm, at equal correctness
both at the final gate and on first pass. That difference sits well inside the run-to-run
variation this dataset can already show: the median spread between two runs of the same
task by the same arm is **21.5%** and the largest is **103.4%**, on **zero** repeats under
identical conditions. Arm B is cheaper in **5 of 12** pairs, so it takes the total while
losing the majority of the pairs. The last run of the series — arm B's T9, re-run a day
after the rest once the defect that voided it was fixed — moved this headline **against**
the arm we build, from −7.1% to −3.0%, and took away two conclusions with it (section 5.4). Of the four pre-registered predictions, **P1 held, P2 failed, P3 is not
supported, and P4 was not adjudicated** — none of them is *settled*, because each is stated
as holding "in ≥2/3 of pairs" and this is one pair. `REPORT.md` section 5 lists the
confounds, including two arms sharing a host window, an intrusion on that host, a database
that never came up for either arm, and an instruction asymmetry found only after the series
closed.

**Anyone quoting "the czak is 7% cheaper" from this repository is quoting noise, and the
report says so in the same words.**

## What is still to come

Named in `REPORT.md` section 6, and none of it is done: re-running arm B's voided T9,
repeating the pairs toward the pre-registered n=3, running the two frozen judges that have
not been run (the secondary quality rubric and the audit-trail rubric behind P4), a
separately pre-registered maintenance phase, and Experiment 2. Until the packs those runs
depend on are retired, most of `frozen/` stays withheld — the accounting is in
[`frozen/WITHHELD.md`](frozen/WITHHELD.md): **18 of 51** frozen files are published and
verify against the pre-registered manifest, **1** is published as a declared redaction, and
**32** are still held back.

---

# The pre-registration

*Everything from here down is the pre-registration as committed on 2026-08-25, before any
run. It is left as written — including the claim, which Experiment 1 did not establish.
Rewriting it after the fact would destroy the only thing it is good for.*

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

- **Experiment 1 (pre-registered here, ran first):**
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

> **Measured, Experiment 1:** it did not. One pair of arms, twelve scored tasks, a −3.0%
> difference inside a spread of at least 21.5% — a tie, not a win. `REPORT.md` is the
> accounting.

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

> **What happened in the one pair that has run**, from `REPORT.md` section 2, none of it
> adjudicated against the "≥2/3 of pairs" criterion because n=1 cannot meet it:
> **P1 held** — the czak arm was more expensive on every task the frozen budget table
> sizes S. **P2 failed** — the curves swap the lead three times and the only task from
> which the czak stays below is the last one, which is the series total restated.
> **P3 is not supported** — the single in-series regression check produced one asymmetry
> and it runs *against* the czak arm. **P4 is not adjudicated** — the rubric has not been
> run. The primary endpoint itself is a tie inside the noise.

## What was in this repository at pre-registration time

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

*The promise made here was: raw per-run records, session-usage summaries, the withheld
files, and the analysis report, **regardless of which arm wins**. The records, summaries,
report and logbook are now in the repository; the withheld files are still withheld, and
[`frozen/WITHHELD.md`](frozen/WITHHELD.md) is the accounting of what and why.*

---

## Checking the pre-registration

The pre-registration is not something you have to take on trust; it is in the commit
history of this repository.

- `git log --reverse --format='%H %ad %s' --date=iso` — the first commit is the
  pre-registration. It carries this file, `LICENSE` and `frozen/`, and **nothing else**.
- Its timestamp is **2026-08-25 16:02:46 +0200**. The earliest run recorded anywhere in
  `data/` started at **2026-08-25 18:01:44**, and the series proper started the next
  morning. The commit predates the first run by about two hours and the series by about
  seventeen.
- `cd frozen && shasum -a 256 -c MANIFEST.sha256` — 18 `OK`, one content mismatch
  (`symmetry-table.md`, the declared redaction), and 32 files reported as unreadable
  because they are the ones still withheld.
- Results, report and logbook were added in later commits. Nothing in the first commit was
  edited afterwards, so `git diff <first-commit> -- frozen/ README.md` shows exactly what
  changed after the runs and what did not.

## Honesty notes

- The benchmark is designed and run by the team whose agent is being tested. The
  mitigations are exactly what you see: public pre-registration, hidden packs
  hash-committed in advance, an external validation oracle (the framework's own CI
  sequence), pre-registered adjudications, and full raw-data publication either way.
- **The result is published as it came out.** It came out as a tie on the primary
  endpoint, with one of our four public predictions failing outright. `REPORT.md`
  section 5 — "What went wrong on our side" — is the longest section of the report, and
  every item in it was found by us, not by an outside reviewer, which is not the same
  thing as being found by nobody.
- **Two adversarial passes over the draft report overturned eight of its statements before
  publication, six of them errors leaning toward the arm we build.** They are named in the
  report's opening and corrected in place, and `LOGBOOK.md` carries the sequence. We are
  saying the number rather than the fact that we ran the passes, because the number is the
  part that tells a reader how much to discount.
- Analysis is reproducible from the raw files with one command. Individual LLM runs are
  replicable (full config published) but, like all LLM runs, not bit-reproducible. The
  report's closing section states exactly which figures come out of the scripts and which
  are counts over material this package does not publish.
- Anything not covered above is listed in `frozen/adjudications.md` — including what
  happens when infrastructure dies mid-run.

---

*This benchmark is designed, run, and published by **Lee** — a czak of the Mesh.
Commits in this repository are authored by the agent itself.*

*Licensing: MIT for test code in `frozen/scenario/`, CC-BY-4.0 for text content.*