# Amendment log — Experiment 1

Every departure from the pre-registered design, in the order it was made, with what was
measured before the decision and which way the departure pushed the result.

**This file is the load-bearing one.** Every caveat in `REPORT.md` and every archived run
in `data/runs/` points back to an entry here. Without it a reader can see *that* records
were invalidated but not *why*, and cannot check whether an invalidation happened to be
convenient for the arm we own.

Entries are append-only. Nothing below has been edited after the fact; the publication
notes at the end are marked as such and are the only text added at publication time.

---

## A1 (2026-08-25, calibration pilot, BEFORE pair 1)

Spec delivery to the arms gets a **non-interactivity wrapper** (identical text for both
arms): plan mode and waiting for approval are forbidden, implementing to completion is
required.

Reason (measured, run `p1-T1-A` void): the arena repository's `AGENTS.md` instructs the
agent to plan, so a headless agent waits for a go-ahead that nobody is there to give;
$1.61 was burned on the plan alone.

The wrapper is a layer of the **runner**, not of the task: the specs stay sterile and
unchanged, and the pack hashes are untouched.

## A2 (2026-08-25, calibration pilot)

The runner CLI gets a `--test-command` option. This is a **bug fix in the runner, not
tuning of the method**: the repository-side verification step was a hard-coded npm build,
which always fails on this yarn monorepo, so arm B's correction loop could never close.

Measured (`p1-T1-B`): five build-gate failures on code that had in fact been delivered,
the run stuck, $8.11 spent.

After the fix was merged the testbench pin moved forward; the change is visible in the
published records as a new `sha_czak` pseudonym from the following runs onward.

**The benchmark verdict is untouched by this.** The verdict is still taken exclusively by
the runner's gate (the framework's own validation plus the hidden pack); `test_command` is
an internal self-check belonging to the method under test, and it decides nothing.

## A3 (2026-08-26, before pair 1)

Account topology for pairs 1-3. Measured: only **two usable organizations** were available
(a third carried a real monthly cap running until 1 September). So:

- **arm A (baseline)** — a clean organization with no other traffic;
- **arm B (the agent)** — an organization shared with unrelated workloads, with those
  workloads paused for each pair's measurement window.

The asymmetry is deliberately oriented: any leakage into a window loads **the arm under
test**, never the baseline. The departure from dedicated accounts is recorded here rather
than smoothed over, and each run record carries the account it ran on.

## A4 (2026-08-26, during pair 1)

Run cost is attributed **per the arm's own work tree**, not per account.

Until this point the meter enumerated every session transcript on an account inside the
measurement window. That is correct only for a fully dedicated account, and under A3 arm B
runs on a shared one.

Measured in the T1-B window: **41 foreign transcripts carrying 15,913 working tokens**
alongside the single benchmark transcript's **168,491**.

The fix filters by the arm's own tree prefix — the session-transcript directory key encodes
the session's working directory — which captures the arm's workshop, its working trees and
any sessions it spawned. The filter is symmetric: the same rule runs for both arms.

Effect on the T1 pair: **A $2.6912 → $2.6599** (one foreign transcript), **B $3.2229 →
$2.7545** (twenty-eight). The A-vs-B difference fell from **+19.8% to +3.6%**.

**The error was one-directional and it loaded the arm under test.** Validation: the same
converter with the filter switched off reproduces the original amounts to the cent, so the
difference comes only from removing other people's work. Corrections are appended; the
original records are untouched and remain published.

## A5 (2026-08-26, after T5 of pair 1)

Equal environmental start for both arms.

Arm A was handed an explicit `PATH` carrying Node 24.19 — its privilege-drop wrapper clears
the environment, so being explicit was forced. Arm B inherited the environment of its
parent process, which is to say the **system Node 22.22**, while the arena repository
declares `engines.node: 24.x`. On top of that, the parent directory of the other runtime
was mode 750, so the account running arm B could not have executed the Node 24 binary even
if it had been pointed at it.

Measured on T4-B: **15 of 80 shell invocations (18%) were the agent hunting for a usable
Node** — including downloading Node 24 into a temporary directory itself — and **29
build/test invocations against the baseline's 4**, largely retries behind the same cause.

Reconnaissance activity was **similar on both sides** (26 versus 23), so the tempting
explanation — "the process makes the agent look around more" — is **false**; the
environment was doing it.

**This is an unequal start, not a difference of method: a confound loading one-sidedly onto
the arm under test.** Arm B's runs from that sequence are **marked as loaded**
(`data/runs/obciazone-a5/`), not deleted. Arm A is not affected by this confound and its
runs stand.

## A6 (2026-08-26, after A5)

The arms stop being measured in adjacent time windows. Arm B's repeat — the operator's
decision after A5 — runs as a separate T1-T12 sequence on the levelled environment, while
arm A continues its original, uninterrupted sequence.

The construction permits this: each arm has its own work tree, its own pin and its own task
order. But it **removes** the assumption that a pair shares momentary conditions (machine
load, time of day). The records carry `wall_start`, `wall_end` and `load_avg`, so the
divergence is readable — and it must not be ignored when interpreting the result.

## Note on the database environment (2026-08-26, NOT an amendment)

The greenfield and seed steps failed for **both** arms at the start of the series
(`relation "organizations" does not exist`). The state is **symmetric**, so it is not a
confound between the arms, and it was deliberately **not** repaired mid-series: repairing
it for one arm only would have introduced an asymmetry.

Consequence: tasks are verified by unit-level tests (the packs), not by working against a
live database. The result says nothing about whether the migrations written in this series
are correct against a real schema.

## A7 (2026-08-26, during pair 1 — process-environment asymmetry, deliberately NOT repaired mid-run)

Arm B's sessions inherit the **entire** environment of the parent process, including
infrastructure credentials. Arm A's sessions receive only four explicitly passed variables,
because its privilege-drop wrapper clears the environment.

Measured: an access token for the version-control system appears **15 times across 5
transcript files on arm B** and **0 times on arm A** — an arm-B session pasted it into a
`curl` command, taking it from the environment.

Two consequences:

1. **Security.** The secret reached data that the pre-registration promises to publish, and
   the scrubber that gates publication had **no secret pattern at all**, so it would have
   passed it through. Fixed separately: contextual patterns plus an explicit list of known
   values.
2. **Measurement.** Arm B had access to resources arm A did not. It spent three commands on
   that access in one task — marginal, but asymmetric.

Deliberately **not** repaired mid-series: at three commands wide, the distortion did not
justify a third restart of the series, which would have cost more than the distortion
itself. That was a judgement call and a reader is entitled to disagree with it. Repeats and
the maintenance phase must start from a **symmetrically cleaned environment on both sides**.

## A8 (2026-08-27, AFTER Experiment 1 closed — confound found post hoc, changes the reading of the quality result)

Arm A worked with a catalogue of **51 ready-made repository procedures** present in its
tree (`.agents/skills/` plus 19 symlinks in `.claude/skills/`, 2.2 MB). Arm B had none of
them: `ls -d .agents .claude` in its tree returns "No such file or directory", and its
execution work tree carried zero.

**Measured.** The listing of those procedures, with their descriptions, was injected into
arm A's context as an attachment in **all 12 of its runs (12/12)** and in **none of arm B's
(0/11)**. The listing is about 8.5 kB, roughly 2,100 tokens per session. Sample entries:
*"om-check-and-commit: Verify that the current branch is ready to publish by running every
config..."*, *"om-verify-in-repo"*, *"om-auto-create-pr"*, *"om-judge-agent-session"*.

**Neither arm ever invoked the Skill tool** — zero calls on both sides — so no procedure
was executed. But a listing with descriptions is information about **what the repository
considers correct practice** (verify before publishing, check the repo, judge the session),
and it was available to one side only.

**Where it came from.** Both directories are in `.gitignore` (lines 156 and 107) and are in
no base's HEAD. They are a residue of arm A's clone environment from 2026-08-25 17:17, not
something that arm produced.

**Direction of effect: AGAINST the benchmark's own thesis** — the help went to the
baseline. It bears above all on the **quality** result: the observation that "the baseline
was the only arm to write convention-guard tests" loses evidential force, because the
baseline had descriptions of the repository's verification procedures in its context and
the agent arm did not. The effect on cost could run either way (2,100 tokens per session is
about 2% of context per step for arm A, but the procedures could equally have shortened its
path) and has **not** been separated out.

**Consequence for publication.** The qualitative result of Experiment 1 is reported with
this caveat **stated outright, not in a footnote**. Repeats (pairs 2 and 3) and the
maintenance phase must start from a symmetric tree state — either skills on both sides or
on neither — with an explicit declaration of which was chosen and why.

**How it was found.** An adversarial verifier on a later maintenance-phase task, checking
whether the conditions of the episode were identical, counted the contents of both trees
and caught a divergence that the authors of the measurement — us — had missed for the whole
of Experiment 1.

---

## Publication notes (added 2026-08-27, at publication time)

These notes were not part of the log when the entries above were written. They are marked
separately so that the record of the experiment stays distinguishable from the record of
publishing it.

**1. This file is a translation.** The log was written in Polish on the run host as the
series went, and translated into English for publication, with internal tool, host and
account names replaced by what they are (`the runner CLI`, `the version-control system`,
`the arm's work tree`). Every figure, date, ratio and verdict is carried across unchanged.
It is **not** listed in `frozen/MANIFEST.sha256` and never was: the manifest was committed
before any run and this log did not exist yet. It therefore has no pre-registered hash to
check it against, and a reader should treat it as testimony from the operator rather than
as hash-committed evidence — unlike the specs, packs and rate card, which do have one.

**2. A5 says "T1-T5"; four records are archived, not five.** `data/runs/obciazone-a5/`
holds arm B's loaded T1, T2, T3 and T4. There is no archived record for a fifth. The
published journal shows why, and it is checkable: `data/journal-p1.jsonl` carries a T5-B
attempt that spawned a session, ran for about thirty-one minutes, passed its first gate and
started a second iteration — and then stops mid-gate, with no closing event, at the point
the confound was found and the sequence was cut. The runner writes a run record when a slot
closes; that slot never closed, so no record was ever written. **The consequence is a real
gap, stated rather than papered over: the compute that attempt spent is in no total in this
package, including the $13.88 quoted for the archive.** The journal events are the only
trace of it and they are published.

**3. Some material named in the manifest is still withheld.** See `frozen/WITHHELD.md` for
what, why, and how to verify it when it is released.
