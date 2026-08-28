# Logbook — Experiment 1

How this experiment actually ran: the order of events, every defect we found in our own
measurement, how each one was found, which way it pushed the result, and which numbers
moved when we fixed it.

This file is not the result. `REPORT.md` is the result and `data/` is the evidence. This
file is the road we took to get there, including the parts of it we had to walk twice.

---

## Why a logbook at all

A benchmark result without its run is not verifiable. The reader gets a table of numbers
and has to decide whether to trust the people who produced it — and here those are the
same people who own one of the two arms. Pre-registration, hidden test packs and a runner
that neither arm controls are all real mitigations, and they are all *ex ante*: they
constrain what we could have chosen to measure, but they say nothing about what actually
happened once the machine started.

What happened is that the instrument was wrong, repeatedly, in ways large enough to change
the answer. One accounting error was charging one arm for work it never did. One arm spent
a fifth of its shell commands fighting a runtime version we had handed it by mistake. A
validation gate once counted "no tests found" as a pass, and a second gate quietly dropped
one of its own frozen test files and reported green anyway. For twenty minutes of the series
a stranger's process was running on the measurement host, because we had published a
database port to the open internet. And when the series was over, the first draft of our own
report claimed a pre-registered prediction had been met when the data says it was not.

None of that is unusual for a first run of a new measurement. Hiding it would be. So the
road is published next to the destination, at the same level of detail, and the errors we
made are written up as carefully as the results we got.

---

## Where the numbers in this file come from

Four classes, marked wherever it matters. The first three can be checked against this
package. The fourth cannot, which is the whole reason it is a separate class.

1. **From one of the two analysis scripts.** Unless the sentence says otherwise, a figure
   here is printed by `python3 analyze.py data` — the section of its output is named
   (e.g. "script §6") — or by `python3 derived.py data` for the four cuts the first script
   does not print. Re-run it and the figure is there.
2. **Quoted from a raw record, an archive README or the amendment log.** Marked
   *record note*, *archive README* or *amendment*, with the file path, so it can be read
   directly. Mostly the before/after figures attached to corrections, which the scripts do
   not recompute because the superseded value is history, not state.
3. **Our arithmetic on published material** — a ratio or a subtotal that neither script
   prints. Marked *our arithmetic*, with its inputs named, whether those are two script
   outputs or a sum over the published records, so it can be checked in one step.
4. **Counted over material this package does not publish.** Marked *not reproducible here*
   at the point of use. Three sources fall in this class: the session transcripts, the two
   arms' final work trees, and the forensic capture of the host intrusion in entry 16. A
   reader cannot check any of these against anything in this repository. Some of them are
   also quoted from a published file — entry 8's shell-command breakdown, for example, is
   quoted from an archive README — and that makes the figure *readable*, not *checkable*;
   both marks then apply.

The fourth class exists because an earlier draft of the report claimed that every number in
it came from the analysis script. That was untrue, and it was untrue in the direction of
sounding more checkable than it was. Naming the class is the fix; it does not make a
class-4 figure any stronger than our word for it. `REPORT.md` §"Reproducing this" carries
the same split as a table, row by row.

Counts of the kind "how many defects were caught by whom" are labels we attached to the
entries below by hand. They are a classification, not a measurement, and we say so where
they appear.

---

## Timeline

| When (run host local time, UTC+02:00) | What |
|---|---|
| 2026-08-25 16:02 | Pre-registration committed to this repository — design, predictions, frozen manifest of 51 files. No run had started; the commit is the timestamp. |
| 2026-08-25 18:01 → 20:1x | **Calibration pilot.** One task, both arms. Nothing in it counts. It found four defects in the instrument and produced amendments A1 and A2. Records: `data/runs/calibration-pilot/`. |
| 2026-08-26 08:47 | First launch of the headline series aborts at once: an expired credential on one arm. Zero tokens spent. Fixed, relaunched. |
| 2026-08-26 08:52 → 18:54 | **Arm A runs T1–T12**, one continuous sequence, uninterrupted. |
| 2026-08-26 09:00 → 14:5x | **Arm B's first attempt at the series.** It closes T1–T4 and is cut during T5, which therefore never produced a record. Two defects found in this window: the cost counter was crediting arm B with unrelated work (A4), and arm B had been running on the wrong runtime version the whole time (A5). |
| 2026-08-26 15:08 | A restart attempt produces twelve runs that never start — the arm had no identity of its own. `$0.00`, zero tokens, twelve times. Records: `data/runs/false-start-no-identity/`. |
| 2026-08-26 16:53 → 22:02 | **Arm B repeats the whole series T1–T12** on an equalised environment (amendment A6). Its earlier T1–T4 are archived, not deleted: `data/runs/burdened-node22/`. |
| 2026-08-26 18:53 → 19:13 (16:53–17:13 UTC) | **Someone reaches the disposable database of arm A's environment from the open internet** and starts a cryptocurrency miner inside its container. The container is dead twenty minutes later. Nothing in the harness noticed; we found it afterwards in the container's own log. Entry 16. |
| 2026-08-26 22:12 | Series closed at 11 of 12 pairs. T9 has no valid arm-B run and still does not. |
| 2026-08-27 08:49 | Amendment **A8**: an adversarial reviewer, checking something else entirely, finds that the two arms' working trees were not equivalent for the entire series. |
| 2026-08-27 08:52 | **Publication halted.** An adversarial review of the publication package finds our own report overstating the result in three places, all in the same direction. |
| 2026-08-27, rebuilding the package | A frozen check is found never to have run: the T12 acceptance pack's end-to-end oracle, which the gate's collector does not match. Both arms' T12 reads green without it. Entry 17. |

The two arms' windows **do** overlap. Arm A ran 08:52–18:54 and arm B 16:53–22:02 on one
host, so arm A's T9–T12 executed alongside arm B's T2–T5 and each arm sat inside the other's
noise floor for two hours. What does *not* overlap is a pair: the two arms never ran the
same task at the same time, and the median gap between the two starts of one task is 3.76 h
(script §4). That is amendment A6, it costs the design something real, and it has its own
entry below. An earlier draft of this file described the two windows as non-overlapping.
They were not, and the concurrency is measurable in the `wall_start` and `wall_end` fields
of the published records.

---

## Defects of measurement

Seventeen entries. Each says what was wrong, how it surfaced, which arm the error
favoured, what we did, and which published numbers moved. Ordered roughly as they were
found, which for the last four is not the order in which they happened.

### 1. The validation gate counted "no tests found" as a pass

**What was wrong.** In the pilot, an arm-A run came back green having produced nothing.
The session had died within one second on an unauthenticated account, and the gate
resolved the test-pack root incorrectly, found no tests, and reported success. The gate
was not fail-closed: absence of evidence was being scored as evidence.

**How we found it.** Reading the pilot record afterwards and noticing a pass with zero
tokens against it. Nothing in the harness objected at the time.

**Direction.** Neutral between the arms, and catastrophic for the experiment: a gate that
passes empty work makes every green in the series meaningless.

**What we did.** Fixed the pack-root resolution and made the gate fail closed. Both fixes
landed before the headline series.

**Numbers.** The run was voided at `$0.0000` and is published as such
(*record note*, `data/runs/calibration-pilot/p1-T1-A.jsonl`, line 2). No series figure
depended on it.

### 2. A headless arm deadlocked in plan mode and burned a real amount of money doing nothing

**What was wrong.** The arena repository's own agent conventions tell an agent to plan
first and wait for approval. A headless run has nobody to approve. The arm produced a
plan, waited, and was killed by the iteration cap.

**How we found it.** The transcript of the one pilot session that did real work: 1.9M
tokens, `$1.6091`, zero lines of code (*record note*,
`data/runs/calibration-pilot/p1-T1-A.jsonl`, line 4).

**Direction.** Against arm A, which is the arm that follows those conventions.

**What we did.** Amendment **A1**: a non-interactivity preamble wrapped around the spec,
**identical text for both arms**, forbidding plan-and-wait and requiring implementation to
completion. It is a layer of the runner, not of the task: the frozen specs and their
hashes were not touched.

**Numbers.** The run was voided. `$1.6091` is published in the pilot archive and enters no
statistic.

### 3. The self-verification command was hard-coded to the wrong build tool

**What was wrong.** The harness's own verification step ran a build command that cannot
succeed on this arena repository's package layout. It therefore failed on every attempt,
including attempts where working code had in fact been delivered. Arm B's rework loop
could not close, by construction.

**How we found it.** Five consecutive red gates on delivered code, in the pilot, at a cost
of `$8.1131` for that slot (*record note*, `data/runs/calibration-pilot/p1-T1-B.jsonl`).
The loop surfaced the symptom; we diagnosed the cause.

**Direction.** Against arm B — it made a working arm look like a failing one.

**What we did.** Amendment **A2**: the verification command became configurable. This is a
bug fix in the harness, not a tuning of the method: the benchmark verdict continued to come
exclusively from the runner's hidden packs. The arm's own self-check is not the judge.

**Numbers.** Pilot only; nothing propagated to the series.

### 4. The rework loop could count iterations that never produced a session

**What was wrong.** A defect class, not a single bug: the loop that retries after a red
gate counted its iterations by ticks of a scheduler, not by sessions actually started. When
dispatch was blocked for any reason, the loop spun to its cap and recorded a
did-not-finish — a verdict about the arm, written from an event that never reached the arm.

It happened three times, with three different causes:

| When | Slot(s) | Cause | Cost recorded |
|---|---|---|---|
| 08-26 09:00 | T1, arm B | A global maintenance flag was visible to this arm's tick, and the task ticket was in a state the scheduler would not pick up | `$0.0000` |
| 08-26 15:08 | 12 slots, arm B | The arm had no identity of its own and fell back to a credential that had been revoked that day | `$0.0000` × 12 |
| 08-26 20:34 | T9, arm B | After a red gate the scheduler refused to dispatch because of a branch collision; iterations 2–5 produced no session at all, so the gate's feedback was never read | `$3.9326` |

**How we found it.** The did-not-finish check closed the runs, which made them visible; the
causes came from reading the transcripts. In the third case the cost is not zero — the
first iteration was real work — so a zero-token heuristic would not have caught it.

**Direction.** Against arm B in all three cases: a harness defect scored as an arm failure.

**What we did.** Cleared the flag and closed the dispatch path; gave the arm its own
identity derived from its parent's rather than a shared administrative credential; for T9,
a retry from a fresh ticket. All three sets of records are published, the first two in
`data/runs/`'s archive subdirectories, T9 as the last line of `data/runs/p1-T9-B.jsonl`.

**Numbers.** The twelve false starts are `$0.00` throughout — which means *no measurement*,
not *free work*, and nothing may be averaged with them. T9-B was voided as infrastructure
under a pre-registered adjudication, and **the re-run has not happened**. That is why the
head-to-head total in this repository covers 11 tasks and not 12 (script §2), and why the
series is described as unfinished rather than complete.

### 5. A fix was verified against a stand-in that did not match the live system

**What was wrong.** A repair to the dispatch path set a ticket status label that does not
exist on the live version-control server. The unit tests were green because the test double
returned whatever label it was asked for.

**How we found it.** A live check of the fix before letting it near the series — listing
the labels the server actually has, instead of the labels the test double claimed.

**Direction.** Neutral; it would have stalled arm B again had it shipped.

**What we did.** Made the code prefer the first label that actually exists among the ones
the scheduler treats as dispatchable, and added a check that keeps that preference list in
sync with the scheduler's own definition.

**Numbers.** None. This one was caught before it could cost anything, which is the only
reason it is a cheap entry in this list.

### 6. Two gate modules had been built with no caller

**What was wrong.** Two pieces of the harness existed, passed their tests, and were never
invoked by anything:

- the module delivering the **mid-series requirements change**. Without it, T5 — the one
  task in the design whose whole point is that requirements change halfway — would have run
  as an ordinary single-phase task. The arm would have received the original spec, the gate
  would have checked the first-phase pack, and the change would never have arrived.
- the **residue check**, which verifies that hidden test packs were removed from the work
  tree after validation. Its cleanup step also swallowed errors silently. A failed removal
  means the arm can see the hidden tests on its next iteration and **nobody is told** — a
  silent fail-open on the integrity of the entire experiment.

**How we found it.** A deliberate audit. Two crashes of this same class had already
happened that day, so instead of waiting for a third we swept the whole harness for modules
with no caller in production paths.

**Direction.** Both would have damaged the experiment as a whole rather than one arm.

**What we did.** Wired both in. The residue check now voids a run as infrastructure if it
trips, and for arm B it is checked before merge so a contaminated change cannot enter the
series base. Proof that these are gates and not decoration: reverting both changes makes
exactly three tests fail; restoring them returns the suite to green.

We also declared, rather than quietly fixed, one remaining module with no caller — a
cost-headroom check — because it had no effect on this series and we would rather publish
a known gap than an unstated one.

**Numbers.** None directly. Without the first fix, every T5 figure in the report would have
been measuring a different task from the one the design pre-registered.

### 7. The cost counter was charging one arm for work it never did

**What was wrong.** Cost was attributed **per account**: everything the account did inside
the run's time window. That is only true for an account used by nothing else. One arm's
account was shared with unrelated workloads, so its runs were being billed for other
processes' sessions.

**How we found it.** Inspecting the window of the first completed pair by hand. In that
15-minute window there were **41 transcripts belonging to unrelated work, carrying 15,913
working tokens, alongside one bench transcript carrying 168,491** — about 9% of the counted
working tokens were not ours (*amendment A4*, `frozen/AMENDMENTS.md`; *not reproducible
here* — the count is over session transcripts, which are not published). Pausing our own
timers did not close the hole, because some of those sessions came from elsewhere entirely,
including a pre-flight check running a different model from the one under test.

**Direction.** Asymmetric and **against arm B** — the arm whose case we are making. Arm A's
account was quiet: one foreign transcript against arm B's 28 in the same pair.

**What we did.** Amendment **A4**: attribution moved from per account to **per arm work
tree**, using the session's own working directory. The cut is hard, symmetric for both arms,
and catches the arm's workshop and its subagents alike.

**Numbers moved** (*record notes*, `data/runs/p1-T1-A.jsonl` and
`data/runs/burdened-node22/p1-T1-B.jsonl`):

| | recorded | corrected |
|---|---|---|
| T1 arm A | `$2.6912` | `$2.6599` |
| T1 arm B | `$3.2229` | `$2.7545` |
| difference B vs A on that pair | +19.8% | +3.6% |

The dollar effect on arm B (−14.5%) is larger than the 9% token share quoted above, because
working tokens deliberately exclude cached reads while the dollar figure includes them.
Both figures are real; they measure different things and we do not use them
interchangeably.

The correction is validated in the only way that means anything: the same calculator with
the filter switched **off** reproduces the original amounts to the cent, so the entire
difference comes from excluding work that was not part of the run — not from changing how
we count. Corrections are appended; the original lines are still in the files. Later records
were written with the fix already in place, and the guard correctly **refused** to "correct"
them, because the old account-wide calculator no longer reproduces their figures.

### 8. One arm ran the whole first attempt on the wrong runtime version

**What was wrong.** The arena repository declares a major runtime version. Arm A was handed
an explicit path to it — forced to be explicit, because its privilege-drop wrapper clears
the environment. Arm B inherited its parent process's environment and therefore got the
system runtime, two major versions older than the repository requires. On top of that, the
arm's work-tree parent directory was mode 750, so the account doing the work could not have
executed the correct binary even if it had been pointed at it.

In the pilot this looked healthy, because the *verification* command did carry an explicit
path. The checking had the right runtime; the actual work did not.

**How we found it.** While investigating a different question — why was arm B taking so
many more steps? The answer was not the one we expected, and it was our fault, not the
arm's. Breaking arm B's shell commands down by purpose on T4: **15 of 80 invocations (18%)
were the arm hunting for a usable runtime**, up to and including downloading it into a
temporary directory and exporting a path by hand before each command. It ran 29 build/test
invocations against arm A's 4, largely retries caused by this (*archive README*,
`data/runs/burdened-node22/README.md`; *not reproducible here* — the breakdown is counted
over session transcripts).

The same breakdown killed the explanation we had been reaching for: **reconnaissance was
near-identical on both sides** (26 vs 23 invocations). "The agent's process makes it explore
more" is false, and we had been about to write it down.

**Direction.** Against arm B, one-sidedly. This is an unequal start, not a difference in
method.

**What we did.** An explicit runtime path for both arms, a symmetry meta-test asserting that
the runtime in arm A's command equals the runtime in arm B's environment, and traverse
permission on the work-tree path. Arm B's completed runs from that sequence — **T1, T2, T3
and T4, four of them** — were **marked as burdened and archived, not deleted**
(`data/runs/burdened-node22/`); arm A was unaffected and was not re-run. Repeating arm B was
the operator's decision, taken because without a repeat the size of the confound would have
stayed a guess, and we did not want a guess in the report.

**There is no fifth archived record, and the reason is a gap, not a tidy-up.** The sequence
was cut while its T5 attempt was still running. A run record is written when a slot closes;
that slot never closed. What survives is in the published journal
(`data/journal-p1.jsonl`): a session spawned at 14:10, ran about thirty-one minutes, passed
its first gate, took the T5 requirements change, entered a second iteration — and the events
end mid-gate with nothing closing them. **That attempt's compute is in no total in this
package**, the $13.88 archive figure included. We are stating the hole rather than writing
"T1–T5" over it, which is what an earlier draft of this logbook and of the report both did.

**Numbers moved.** Arm B's first four tasks, before → after (script §6, which prints both
figures for each repeat group):

| task | burdened | equalised | change |
|---|---|---|---|
| T1 | `$2.7545` | `$3.6096` | **+31.0%** |
| T2 | `$2.9418` | `$2.8825` | −2.0% |
| T3 | `$2.8689` | `$2.3620` | −17.7% |
| T4 | `$5.3159` | `$3.2496` | **−38.9%** |

(*our arithmetic*: each change is (equalised − burdened) ÷ burdened on the two figures the
script prints. Both columns are post-A4, so the comparison is like for like and does not
smuggle in entry 7.) The confound hit unevenly — hardest on T4, where we had measured the
most environment-fighting, and not at all on T2.

**And it produced the most uncomfortable number in the experiment.** T1 got *more*
expensive after the repair, by 31%. That is the same task, the same arm, run twice — our
first look at run-to-run spread, and it moves in both directions. See entry 13.

### 9. Credential resolution preferred a revoked secret over a live one

**What was wrong.** The gate for one run went to the version-control server and got a 401.
The credential resolver was falling back to a shared secret from a central store that had
been invalidated, and the store outranked the local environment where a working credential
sat.

**How we found it.** The gate failed. This one the harness caught by itself, immediately,
because a gate that cannot reach the server is a gate that fails closed.

**Direction.** Against arm B: the run stalled and produced no record.

**What we did.** Made the runner's identity explicit rather than resolved by fallback.

**Numbers.** That attempt produced no record at all, so nothing entered any statistic.

### 10. A secret from the environment ended up inside one arm's transcripts, and the scrubber had no pattern for secrets

**What was wrong.** Two problems stacked.

First, an asymmetry: arm B's session inherits the whole parent environment, including
infrastructure credentials, while arm A's session gets four explicitly-passed variables
because its wrapper clears everything else. Measured: an access token appears **15 times
across 5 transcript files on arm B and 0 times on arm A** (*not reproducible here* —
transcripts are not published). The session had taken it from
the environment and pasted it into a shell command.

Second, and worse: the tool that scrubs material before publication had **not a single
pattern for secrets**. The pre-registration promises to publish raw data. That token would
have gone out with it.

**How we found it.** Reading transcripts for an unrelated breakdown of what each arm spends
its steps on. Nothing flagged it; we happened to look.

**Direction.** The asymmetry itself slightly favours arm B — it had reachable resources arm
A did not, and used them in three commands in one task. The publication risk favoured
nobody.

**What we did.** The scrubber gained contextual secret patterns — authorisation headers,
assignments, known key prefixes — plus a second layer that erases an explicit list of known
secret values supplied by the caller. Two layers, because a pattern is always a bet about
the *shape* of a secret, and one of these has the same shape as a commit hash: matching it
without context would delete real evidence. At publication the raw files were passed
through both layers plus an oracle that reports any remaining match; the result and the
per-file hashes are in `data/SCRUB-REPORT.json`.

The environment asymmetry itself was recorded as amendment **A7** and **deliberately not
fixed mid-series**: three commands' worth of effect did not justify a third restart, which
would have cost more than the damage. Repeats and the maintenance phase must start from a
symmetrically cleaned environment on both sides.

**Numbers.** None moved. What changed is that raw data ships with the credentials removed
and the removal independently checked, rather than shipping with them in it.

### 11. Our own step classifier keyed on the first word of a command

**What was wrong.** The breakdown of what each arm spends its steps on — reconnaissance vs
build vs version control — classified a shell command by its first word. Commands that
begin by changing directory and then do the real work were therefore filed under "other",
which understated build activity and made the picture look tidier than it was.

**How we found it.** Ourselves, checking the classifier against a sample of the commands it
was sorting.

**Direction.** Symmetric in the rule, one-sided in effect — and we can name the side
without being able to size it. The rule filed anything that began with a directory change or
an environment assignment under "other". Those prefixes were mostly arm B's: while it was
fighting the runtime it exported a path by hand ahead of its commands (entry 8). So the
undercount of build activity landed mainly in arm B's column, and the effect on the
published picture ran toward **flattering arm B** — a tidier step profile than it actually
had, and a runtime confound that stayed harder to see for as long as the bad table stood. We
did not re-run the old classifier per arm to measure that, so the direction is reasoned from
entry 8 rather than counted, and the magnitude is unknown. What is certain is the scope: it
distorted a supporting analysis, not the primary endpoint.

**What we did.** Fixed the classifier and republished the table, saying in the same message
that the earlier version had been wrong.

**Numbers.** The step-breakdown table changed. No cost figure depended on it. Every figure
in that table is *not reproducible here*, before and after the fix alike: it is counted over
session transcripts.

### 12. Our own convention check counted the guards as the violation

**What was wrong.** One of the frozen convention checks looks for cross-module database
relations, which the arena's conventions forbid. A first pass reported eight of them in arm
A's output. All eight were **assertions in arm A's tests proving the relations are absent**.
The check was counting the guard as the crime.

**How we found it.** Ourselves, because eight violations in an otherwise clean run did not
look like the arm's other behaviour, and we went to read them.

**Direction.** Against arm A. Had it stood, the report would have carried a false quality
finding in favour of arm B — which is exactly the direction that later got the publication
halted.

**What we did.** Excluded test files from the check. Result: zero on both sides.

**Numbers.** That row of the convention table went from "8 vs 0" to "0 vs 0"
(*not reproducible here* — the check runs over each arm's final module tree, which is not
published).

### 13. We never measured run-to-run noise cleanly, and for a while we quoted it as if we had

**What was wrong.** Not a bug — a gap we did not notice we had. The design budgeted no
repeats under identical conditions. Every repeat this dataset contains exists because a run
was disqualified for a stated reason and redone **after something was changed**. So each
repeat pair mixes randomness with the effect of that change.

**How we found it.** The T1 repeat in entry 8 came out 31% more expensive after a repair
that should, if anything, have made it cheaper. That is when we understood that differences
smaller than the spread we can already see are not distinguishable from noise at this
sample size — and that we had been quoting mid-series differences without saying so.

**Direction.** It inflated the confidence of every in-flight comparison we published,
including ones that favoured our own arm.

**What we did.** The analysis script now enumerates every repeat group, prints how many of
them ran under identical conditions (**zero**), and states in its own output that the figure
is an **upper bound on noise, not an estimate of it**.

**Numbers** (script §6): 5 repeat groups, 7 pairwise comparisons, spread **min 2.1%,
median 21.5%, max 103.4%**. The head-to-head difference over the series is −3.0%. The
effect is comfortably inside the variation already visible in the data. Any sentence of the
form "the agent is X% cheaper" needs repeats before it means anything, and this experiment
does not have them.

### 14. The two arms' working trees were not equivalent, for the entire series

**What was wrong.** Arm A's tree contained a catalogue of **51 ready-made repository
procedures** (2.2 MB, plus a directory of links to them). Arm B's tree contained none of
them — the directories did not exist at all. Measured: the listing of those procedures,
with their descriptions, entered the session context as an attachment in **12 of 12 arm-A
runs and 0 of 11 arm-B runs**, about 8.5 kB (~2,100 tokens) per session (*not reproducible
here* — counted over session transcripts and the two checkouts).

**Neither arm ever invoked one** — zero invocations on both sides — so no procedure was
executed by anybody. But the listing is a statement of *what the repository considers the
right way to work* ("verify before publishing", "check the repository", "judge the
session"), and only one side had it.

The directories are in the repository's ignore file and are in no branch's HEAD; they were
residue from how one arm's checkout was created the day before, not something either arm
earned.

**How we found it.** We did not. An adversarial reviewer of a later, unrelated piece of
work was routinely checking whether two episodes ran under identical conditions, counted
the contents of both trees, and found the divergence. We had run the entire twelve-task
series without noticing.

**Direction.** **Against the thesis this benchmark exists to test** — the help went to the
baseline arm.

**What we did.** Recorded it as amendment **A8** and changed what we are willing to claim.
The qualitative finding we had considered our strongest evidence *for* the baseline —
"the baseline was the only arm to write tests that guard the repository's conventions" —
loses its force. We are not claiming the asymmetry explains that difference. We are saying
that with this asymmetry present, the difference cannot be attributed to the arms' methods.
The cost effect could run either way (~2% of context per step for arm A, but procedures
could equally have shortened its path) and we did **not** separate it.

Repeats and the maintenance phase must start from a symmetric tree state — the procedures
on both sides or on neither, with the choice declared.

**Numbers.** None moved. A conclusion did.

### 15. One field of the instrument only ever worked on one side

**What was wrong.** The field recording which sessions a run consisted of is populated for
arm A in all 13 of its records and for **none** of arm B's 29 — including runs that spent
hundreds of thousands of tokens and reached green. It is a gap in the instrument, not a
property of the runs.

**How we found it.** Preparing the raw data for publication and checking each field against
what it claims to mean.

**Direction.** Neutral, and dangerous in a specific way: an empty list looks exactly like
"no session started", which is the evidence we used to void two runs. Those adjudications
in fact rested on the transcripts, which is what their notes say — but a reader who took
the field at face value would reach the right answer for the wrong reason, and on arm A the
same field means something different from what it means on arm B.

**What we did.** Published it as a caveat rather than a footnote (`data/README.md`,
caveat 2), and made the summary report it as an instrument gap instead of asserting
anything from it.

### 16. Someone else's process ran on the measurement host, because we published a database port to the internet

**What was wrong.** The generator that builds each arm's throwaway database published the
database's port on **every** interface instead of on the loopback address. A port published
through the container layer is inserted ahead of the host firewall's rules, so the firewall
never saw the traffic: the database stood open to the internet with the credentials the
generator itself had put in it. Two defects, ours both — one line of configuration, and no
check anywhere that asked what the run environment was listening on.

On **2026-08-26 at 16:53 UTC** (18:53 run-host local time) somebody connected to arm A's
database and used the database's own ability to run a program from inside a session to write
two executables, about 5 MB together, into the container's temporary directory. The capture
identifies them as a cryptocurrency miner. The database log carries a `Text file busy`
error against a later write — the file was already being executed, so the process had
started. The container was dead at **17:13 UTC**, twenty minutes after the first write.
Arm B's database container shows **nothing**: no files, no matching log lines.
(*Not reproducible here* — the file sizes, the log line and the two container states come
from a forensic capture that is not published.)

**How we found it.** Afterwards, reading the container's own log. Nothing in the harness was
watching: there was no check on what the generator exposed and none on what ran inside the
containers. The container had already died on its own before anyone looked. We hold the
capture and assert nothing beyond it — not what else was attempted, not how it got in beyond
the open port, and not that it was contained.

**Direction.** It does not touch the primary endpoint. Cost here is imputed from token
counts reported by the model provider, and host CPU cannot inflate those. What it touches is
**wall-clock time and machine load**, and only for the three runs that were live inside the
twenty-minute window:

| run | window (local) | overlap | 1-min load | active min | `usd_imputed` |
|---|---|---:|---:|---:|---:|
| T12-A | 18:32:04–18:54:27 | 1.4 min | 31.64 | 22.1 | `$5.7278` |
| T5-B | 18:28:08–19:09:03 | 16.1 min | 40.04 | 39.6 | `$4.7466` |
| T6-B | 19:09:04–19:28:04 | 3.9 min | 26.10 | 18.4 | `$2.8470` |

(Load and active minutes from `derived.py` §5; the windows are the `wall_start` and
`wall_end` fields of the three records; the overlaps are *our arithmetic* on those windows
against 16:53–17:13 UTC. Two of the three runs are arm B's and one is arm A's.)

**We are not claiming the miner explains those load figures.** That same window is the one
in which both arms were running concurrently on one host, and the 1-minute load was already
between **28.56 and 35.18** across the six runs of the preceding hour and a half
(`derived.py` §5). This data cannot separate host contention caused by
an intruder from host contention the two arms caused each other. The verdict on those three
runs' wall-clock figures is the one the overlap had already earned them — uninterpretable —
now for a second reason.

**What we did.** Nothing to the numbers; there is nothing in them to correct. On the
instrument, what it needs is that the throwaway database binds to the loopback address only,
and that the run environment is inspected for anything listening on a public interface before
an arm is allowed to start. **We are not claiming either has shipped** — nothing in this
package would demonstrate it, and the honest status of the instrument going into the repeats
is the one described above.

**Numbers.** None moved. The three `usd_imputed` figures are token-derived and unchanged
(script §1).

**And one error in this entry was ours, not the intruder's.** The first draft of the report
put the intrusion at 16:53 **local** — "the same minute arm B started T1" — which turned a
unit error into a coincidence, and from there into a two-hour-forty-two-minute window
overlapping seven runs. The records carry two time bases: `wall_start`/`wall_end` in
run-host local time (UTC+02:00) and `ts` in UTC, and `data/README.md` §Time says in as many
words not to mix them. We mixed them. 16:53 UTC is 18:53 local, the window is twenty
minutes, and it overlaps the three runs in the table above.

### 17. The validation gate collected only unit tests, so a frozen check never ran

**What was wrong.** The gate builds its run list by collecting unit test files from the
pack directory. The T12 acceptance pack ships three files: two unit test files and one
**integration** spec, in a directory of its own. The collector's pattern does not match the
integration file, so the gate never executed it — and said nothing about not having done so.
T12 reads **verified** for both arms on the strength of the two files the gate did run.

**What the check that never ran asserts.** It is the only end-to-end oracle in the whole
frozen set: an account must resolve to exactly one search hit after a re-index, re-indexing
must be idempotent, and a custom field must be searchable through the entire chain. It is
hash-committed like everything else —
`./scenario/T12/pack/apps/mercato/src/modules/loyalty/__integration__/TC-LOYALTY-001-search-reindex.spec.ts`
is a line of `frozen/MANIFEST.sha256`, committed before any run — so a reader can verify
that it existed and was frozen, though not what it says: its contents are withheld with the
rest of the packs (`frozen/WITHHELD.md`). Of the 31 pack files in the manifest, 30 are unit
test files and this is the one that is not. It is also the one that never ran.

**How we found it.** Ourselves, while writing the report, reading the manifest against what
the gate collects. Nothing failed and nothing looked wrong: both T12 records carry a single
gate run with `passed: true` and an empty `failed_test_ids` (`data/runs/p1-T12-A.jsonl`,
`data/runs/p1-T12-B.jsonl`; script §1).

**Direction.** **Symmetric.** The same collector, the same pack and the same omission
applied to both arms, and both were let through by it. It is not a thumb on either scale; it
is a hole in the scale. What it costs is the strength of one green on each side — and T12 is
not an arbitrary task. It is one of the three large tasks — the size class where the gap
between the arms is widest, and widest in arm B's favour at −45.9% (`derived.py` §2). The
weakened green sits on the row that flatters the arm we own. For both arms, "verified" on
T12 now means "passed the unit packs", not "the feature works end to end".

**It compounds with the database.** That oracle needs a live database, and the database
never came up for either arm (see the entry below). Had the gate collected the file it would
most likely have gone red on both sides for a reason belonging to neither arm. That does not
make the omission harmless — it makes the two into one: the instrument owned an end-to-end
check, could not have run it, and reported green without ever saying either thing. This is
the same class of defect as entry 1, where the gate scored "no tests found" as a pass. We
made that one fail closed before the series and left this one standing through all of it.

**What we did.** Diagnosed it, and wrote it down here and in `REPORT.md` §5.7. **We are not
claiming a fix.** Nothing in this package would demonstrate one, so the status of the
instrument going into the repeats and the maintenance phase is that its collector is still
the one that silently dropped this file. What it needs is a collector that takes every test
file a pack ships, whatever the directory or suffix, and a gate that fails closed when the
number of files it collected does not equal the number the pack's manifest lists.

**Numbers.** None moved — and that is the complaint, not the reassurance. The figure that
should have moved is a verdict, and we cannot say in which direction, for either arm.

### Not a defect, but it limits the result: the database never came up

The greenfield and seed steps failed **for both arms** at the start of the series. The state
is symmetric, so it is not a confound between them, and we deliberately did **not** repair
it mid-series, because repairing it for one arm would have created one.

The consequence is real and constrains what this experiment can claim: the tasks were
verified by unit-level hidden packs, not by working against a live database. **Nothing here
says anything about whether the migrations these tasks wrote are correct against a real
schema.**

---

## Day two — closing the series, and opening the next one

*Everything above was written when the series still had a hole in it. This section covers
27 August: the missing run, the phase that follows, and five more defects of ours. The
numbering continues the list above; the "Who caught what" tally below it was computed over
entries 1–17 and has not been recomputed.*

### 18. The database at the centre of the intrusion was never used by either arm

Preparing the maintenance phase, we asked a question we should have asked in week one:
does anything in this benchmark actually need the throwaway Postgres container? The
hidden packs are unit tests with in-memory fakes. The task specs never mention it. So we
read the compromised container's own log end to end. In the whole life of that container
there is **one** connection from the application, at 06:32:10 on 26 August, and it failed
immediately — `relation "custom_field_defs" does not exist`, `relation "organizations"
does not exist`. The database was never migrated. Everything else in the log is the
intruder: 830 lines of `role ... is not permitted to log in`, then a sweep of
`ALTER USER <common-service-name> WITH PASSWORD ...` against roles that do not exist.

So the attack surface that got us compromised existed for **no benefit at all**. The
logbook entry above records that the database never came up and treats it as a limit on
what the experiment can claim. That is still true. What is new is that the container did
not need to be running for a single measurement in the series — and the maintenance phase
runs with no containers at all.

### 19. The re-run we owed, and what it cost us

The correction loop that voided arm B's T9 was fixed by giving each rework iteration its
own ticket. T9 was re-run on 27 August and came back **verified at $4.48 on the first gate
evaluation** — which means the repaired loop was never exercised, because there was nothing
to repair.

It moved the headline **against** the arm we build: the series went from −7.1% over eleven
tasks to −3.0% over twelve. It also took away two things the previous draft had argued at
length. The dip in the cumulative curve at T10, and the rebound at T11 that we had made a
point of publishing — both were artefacts of the missing task; with T9 in place arm B is
simply above arm A for eleven tasks and below on the last. And first-pass correctness,
which we had reported as *not* a tie because arm A's only red gate sat outside the scored
set, **is** a tie: one red gate each.

We are recording this in the same weight as the rest because the temptation ran the other
way. The eleven-task number was better for us and was already published.

### 20. The validation gate chose which pull request to judge by pattern, not by ticket

Arm B's gate looked for *any* open pull request from that arm onto the bench branch. On
26 August the incident ticket about the compromised database was filed **in the benchmark
repository**, and arm B's dispatcher picked it up as ordinary work and spent a session on
it — producing an open pull request that matched the gate's pattern exactly. Had a gate
gone green while it was open, the harness could have merged the security fix as the result
of task T9.

Nothing was mis-merged: we found it while preparing the next phase and retargeted the
stray request first. But the defect is not "a stray ticket got in" — it is that the gate
never asked *which* pull request belongs to the task it is judging. The maintenance
phase's gate asks for the ticket number.

### 21. The maintenance phase's control step caught five defects before the first result

The rule for the new phase is that no hidden pack is a gate until it has been watched
running against both untouched baselines, with the distribution its design document
declares. Running that step found five things, three of which would have produced a
*number* rather than an error:

1. **A pack that could not run at all.** M5 keeps its verdict rule in a helper module next
   to its tests; the harness copied only `*.test.ts` into the gate checkout, so the helper
   never arrived and the suite died on `Cannot find module` — zero cases executed, both
   arms. Trusting the design document would have produced two confident DNFs measuring our
   packaging.
2. **Resource-fork files from the authoring machine** (`._*.test.ts`) travelled inside the
   archive and the runner picked them up as test suites.
3. **The gate checkout was missing most of its dependencies.** Eight `node_modules`
   directories in this monorepo; the harness copied one. Twenty typecheck errors, all
   environment, on a module that is declared in the manifest and present in both arms'
   own workspaces.
4. **A cache made one arm's typecheck look green without running it.** Arm B reported
   `FULL TURBO`, twenty-seven of twenty-seven tasks replayed from cache — a clean bill of
   health for a check that never executed, on a checkout whose dependencies were broken.
   The same run reported arm A red. Taken at face value: *B typechecks, A does not*. It
   was a cache artefact end to end.
5. **One arm's checkout was missing generated code.** Arm A's baseline is a copy of a
   working tree and carries generated registries; arm B's is a fresh worktree and does
   not. Before the fix: 21 suites failing to load in arm B against 4 in arm A — a
   difference that reads as a quality gap and was entirely our checkout preparation. With
   the repository's own generator run first, both sit at 4, with identical failing sets.

After the fixes the two baselines are symmetric to the character: identical six failing
tests in identical four suites, zero typecheck errors, module suites green in both.

### 22. A measurement we performed and threw away, and a test that wrote into the evidence

Two in one afternoon, both ours, both about the difference between doing the work and
recording it.

**A run happened in full and vanished.** The first maintenance task ran in arm A: session,
gate, green verdict. Then the ledger refused the record because two fields it requires
(`build_time_s`, `context_rebuild`) were absent, the exception escaped, and the result was
gone from process memory. The measurement had been *made* and was lost on the way to
paper. Recovered from the run journal — which records every step as it happens, including
the gate's verdict — and from the account transcripts, which hold the tokens; the record
is in `data/` marked as reconstructed, with each field the reconstruction cannot supply
listed as unmeasurable rather than zero. The write path now has a smoke test with a stub
session and a stub gate, so it is exercised before a real session pays for it.

**And that smoke test wrote into the run journal.** Its stub reported a spawned session
and a green gate for a task that had not run. The journal is append-only, so the entries
stand and a correction entry naming them by timestamp stands beneath them; the stub is now
forbidden to write there at all. It is a small thing and it is exactly the class this
whole logbook is about: a test that leaves marks in the evidence it was supposed to
protect.

### 23. Both arms' accounts ran out of subscription budget mid-phase, together

At 14:06 on 27 August, five tasks into the maintenance phase, both arms' runs
started failing in seconds. Both accounts answered the same sentence: *"You've hit
your limit — resets Aug 29, 1pm."* The same sentence is the finding: two accounts
that were supposed to be the two arms' separate vehicles **share one subscription
pool with one reset clock**. The arms were never resource-isolated, in this phase
or in the series before it — one arm's spending could always exhaust the other's
account, and on 27 August our own activity (the T9 re-run, the control steps, the
first five maintenance tasks) did exactly that to both.

What it did to the records: seven runs closed as DNF with five "iterations" each.
None of them was a DNF. The runner counted loop turns in which no session ever did
work — the same class as entry 4, from the other side: there the loop was dead and
the arm was charged for it; here the account was dead and the arm was charged for
it. All seven are corrected to infrastructure-void in the ledger, append-only, each
with what its journal and transcripts actually show: M5-A's first iteration is a
real red gate (a 4-minute session that failed the pack honestly) and the account
died before it could try again; M2-B's first tick did sixteen minutes of real work
that the limit killed before a commit existed, so the gate correctly said "no pull
request"; the other five never got a session at all.

Five measurements stand: M1 in both arms, M2/M3/M4 in arm A. Seven slots wait for
the reset. The DNF rule now has a sibling it always needed: **budget exhaustion is
a verdict about the task only when the meter that ran out belongs to the task.**

### 24. The rubric behind one of our four public predictions never existed

Preparing to run the two "frozen but never executed" judges, we went to the frozen
manifest for the audit-trail rubric that prediction P4 depends on. It is not among the
fifty-one hash-committed files. There is a quality rubric; there is no audit-trail
rubric. Nobody deleted it — **it was never written**. P4 ("reconstructing why a change
was made costs less with the czak") was therefore unfalsifiable from the day it was
pre-registered: a public prediction with no instrument behind it. Every prior statement
that the rubric "has not been run" — including three in the published report — implied
an artefact that did not exist, and we did not notice while writing any of them, because
"not yet run" and "not real" look identical until you reach for the thing.

The same preparation found a second absence, same class, other arm: the quality judge
was designed to score **per-task** diffs, and arm A has none — the harness never
captured its tree between tasks, so the per-task quality resolution of half the
experiment was never collectable. The maintenance phase had the same defect until this
afternoon (its arm-A products were being destroyed by the next task's baseline restore;
four tasks' secondary observables are gone); the driver now archives the product after
every gate, smoke-tested before use.

### 25. The quality judge finally ran: a dead tie, and one axis pointing somewhere

Three blind repetitions per arm, pinned model, an account outside the benchmark pool,
each verdict recorded with the SHA-256 of the exact bytes the judge saw — plus the two
runner failures that preceded the working run (a 330 KB prompt does not fit in a
process argument list; measured twice before the stdin pipe worked). Input: each arm's
cumulative series diff — 239 KB and 236 KB, sizes we did not plan and cannot stop
noticing — against all twelve specs, symmetrically, because of the arm-A gap in entry 24.

Totals: **50/60 against 50/60.** The only directionally consistent difference is the
repo-convention axis, where the process arm scored one point higher in two of three
repetitions and equal in the third. A one-point gap on a five-point scale, three
repetitions, judge variance visibly ±1: a weak signal, printed because it is the only
quality measurement in the whole experiment that separates the arms at all — and
because the instruction asymmetry of entry 14/§5.8 runs **against** it, which makes it
harder, not easier, to dismiss: the arm that held the repository's own procedure
catalogue in context is the one the judge docked on convention fidelity.

### 26. Experiment 2's calibration pilot: one bias caught by arithmetic, one hijack caught in the act

Experiment 2's pilot ran the same afternoon, and it earned its existence twice inside
an hour.

**First, the cost instrument was wrong by +40%.** The new engine reports a session's
usage as a single aggregated stdout event; the frozen price table's long-context
surcharge applies per request. The pilot's first run priced at $1.2483; the session's
own on-disk rollout carries the per-request breakdown — twenty-one requests, the
largest 67k input tokens, none over the 272k threshold — so no surcharge was due and
the true figure is $0.8911. The adversarial review had flagged the aggregation as a
risk; the pilot turned it into a number. Imputation now reads per-request usage with
an exact-sum reconciliation oracle (it reconciled to the token), and the fallback to
the aggregate declares itself biased upward. Amendment E2-A1, re-frozen before any
counted run.

**Second, the dispatcher hijacked a ticket from the other experiment — again.** The
maintenance phase and Experiment 2 share one ticket pool in the benchmark repository.
The maintenance tickets, left dispatchable when the account limit killed that phase
mid-run, were sitting there marked ready — and the process arm's first pilot tick
took one of them (the M6 stats-command task) instead of its own T1, and started
implementing the wrong experiment's task on the wrong base branch. This is the
**third** instance of the class "the dispatcher takes whatever is dispatchable":
the incident ticket in Experiment 1 (entry 20 territory), and now a cross-experiment
capture. The session was killed mid-flight, its worktree and branch deleted, nothing
pushed, and its tokens deliberately counted toward **no** arm — the void record says
so. The kill exposed a second layer: the worker's persisted state still said the
hijacked task was in progress, so the next tick **resumed the hijack** past a
freshly-written guard that only checked labels. State cleared, guard now refuses to
start when any ticket other than the current task's is dispatchable — in both
experiments' drivers — and the maintenance tickets sit non-dispatchable until their
own rerun flips them one at a time.

The third attempt took the right ticket. Nothing from either failure entered any
series measurement; both live in the pilot's records as infrastructure-void with the
full story in their notes.

### 27. We lost the entire results package, and rebuilt it from the transcripts that survived

On the morning of 28 August the working copy of this repository — report, logbook,
analysis scripts, data mirrors, four unpushed result commits — ceased to exist. It had
lived, all of it, in a session-scoped scratch directory on the operator's machine; the
session's worktree was recycled, the scratch directory went with it, and the remote
still held only the pre-registration commit. Nothing on the benchmark host was touched:
the ledgers, journals and judge records this package mirrors are append-only and were
never at risk. What died was every word written *about* them.

The recovery is documented in `RECOVERY-NOTE.md` and took one working day: file births
were pulled from the transcripts of the review agents that built and audited the drafts,
every subsequent edit was replayed in order from the session transcript (each anchored
on exact surrounding text, so a wrong base fails loudly instead of silently), the final
consistency check's full-file reads supplied the paragraphs whose edit anchors were
missing, and the data directories were re-fetched from the host. The oracle for the
whole exercise: `analyze.py` over the re-fetched records reproduces the published
per-task table to the cent. It does.

Two things deserve to be written down plainly. First, the failure is precisely the
class this benchmark keeps cataloguing in its subjects — a single unreplicated copy of
finished work, held in a location whose lifecycle nobody had read, with publication
deferred to a later step that never came. We spent a week measuring whether a process
protects work from its author, then kept the measurements in /tmp. Second, the thing
that made recovery possible was not a backup — there was none — but the same property
the czak arm is being measured for: **the work left a trail as a side effect of how it
was done.** Review rounds ran as agents whose transcripts persist; edits were made as
anchored replacements that carry their own context; data was append-only on a durable
host. The trail was never designed as a backup. It was simply complete enough to be one.

---

## Who caught what

A classification of the seventeen entries above, by how each one surfaced. It is a label we
applied by hand, not a measurement, and the categories are ours.

| How it surfaced | Entries | Count |
|---|---|---|
| We found it ourselves, reading our own records, transcripts or logs | 1, 2, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17 | 12 |
| An automated check in the harness refused and made it visible | 3, 4, 9 | 3 |
| A live check of a fix, before it reached the series | 5 | 1 |
| An adversarial reviewer, not the author of the thing reviewed | 14 | 1 |

Plus the halt described in the next section, which was also the adversarial reviewer.

Four observations, offered dry:

**Most of the defects were found by us, and that is not a compliment to us.** They were
findable because the instrument records enough to find them: append-only records that keep
the superseded value, per-run token accounting, transcripts, an amendment log. A measurement
that overwrites its own history would have hidden every one of these, and we would have
published a cleaner-looking result.

**The ones we missed longest are the ones nobody's failure pointed at.** Most entries
announced themselves: a red gate, a stalled loop, a number that looked wrong. Three did not.
Entry 14 had no symptom at all — both arms ran, both went green — and it survived the whole
series; it took someone whose job was to ask "are the conditions identical?" rather than
"did the run succeed?" Entry 17 is the same shape one layer down: a frozen test that was
never collected, on a task both arms passed, with nothing in any record to show for it.
Entry 16 is the same shape again, outside the measurement: a stranger's process on the
measurement host, and not one check in the harness pointed at it. Symptomless defects are
not rarer than loud ones. They are just the ones your own reading will not find, because
your own reading follows the failures.

**Direction of error is not evidence of good faith.** It is tempting to point out that most
of the errors here ran *against* the arm we own: the accounting error, the runtime version,
the dead loops, and the tree asymmetry we did not find ourselves. That defence collapses on
one fact — the single artefact where the errors all ran the *other* way was the report we
wrote about the results, and we did not catch that either. An adversarial review did.

**Five of the seventeen entries surfaced because something other than our own reading
refused** — three automated checks in the harness, one live check of a fix, one adversarial
reviewer — and so did the halt. In every one of those cases the check was one we had built
ourselves, and what it caught was an error we had also made. That is a point in favour of
building checks that can contradict you, and it is worth exactly as much as the sample it
comes from: one experiment, run once.

---

## The halt

On 2026-08-27, an adversarial review of the publication package stopped it. Five findings.
Three of them were the same failure: our own report was overstating the result in our own
favour.

**1. A pre-registered prediction reported as met, when the data says it was not.** The
report claimed the cumulative cost curves cross at T10 and that prediction P2 held. P2
requires the agent arm's cumulative cost to go below the baseline's at some task and
**stay** below through the end of the series. The cumulative ratio (*our arithmetic* on the
two cumulative columns in script §3):

| after task | T8 | T10 | T11 | T12 |
|---|---|---|---|---|
| arm B ÷ arm A, cumulative | 1.024 | 0.987 | **1.008** | 0.929 |

After T11 the agent arm is back **above** the baseline, so there is no crossing at T10. The
only "from here to the end" that survives is at T12 — the last task — which is the series
total wearing a trend's clothes. **The report's cumulative table omitted the T11 row: the
one row that refutes the claim.** Our own analysis script had printed the correct verdict
in plain text ("DEGENERATE… no sustained crossover"); the report said something else.

**2. Noise understated, in the same direction.** The report quoted four repeat comparisons
(+31%, −2%, −17.7%, −38.9%). The script on the same data reports 5 groups, 7 comparisons,
**median 21.5%, maximum 103.4%** (script §6). The omitted material included the fact that
one slot had been run **three** times, not twice — and that the third run was the most
expensive of the three.

**3. A false claim of reproducibility.** The report stated that every number in it came
from the analysis script. It did not: the quality, traceability and code-size tables were
computed by hand and the script does not know about them. The reviewer checked those
numbers and found them **correct** — what was false was the claim about where they came
from, which is the claim a reader would rely on to check them.

**4. Implementation detail in the publication package.** Two files staged for publication
described how one arm is assembled internally, along with internal system and account
names, and were in the wrong language for this repository. The scrubber passed them green,
because its patterns match structured identifiers and these were ordinary words.

**5. An incomplete package.** Of the raw material the pre-registration promised, most was
not in the repository — including the amendment log on which every caveat in the report
depends. A reader could not have verified a single one of them.

Findings 1–3 all point the same way. A pipeline built to measure honesty had produced a
report tilted toward the people who built it, in three places at once, and none of the three
was caught by the people who wrote it.

The package was rebuilt before publication: the prediction restated as the script computes
it, the noise reported as median and maximum with the full list of repeats, the
reproducibility claim narrowed to what the script actually produces, the leaking files
removed from the publication path, and the raw records, journal, usage summaries and
amendment log added.

---

## How our conclusions changed

In order, with what killed each one.

1. **"The agent arm is ~54% more expensive."** Held for a few hours mid-series. Killed by
   entry 8: it was measuring a runtime handicap we had created.
2. **"The agent pays for its process — self-review and pull requests."** Killed by looking
   at where the tokens actually went: subagent work appears sporadically on **both** sides
   and is not a process surcharge.
3. **"The agent's process makes it explore more."** Killed twice, by two independent step
   breakdowns: reconnaissance commands are near-identical on both sides (26 vs 23 on one
   task; entry 8).
4. **"The agent carries a larger context per step, so it costs more per step."** Formed on
   the first four tasks, under the runtime confound, and **not supported by the completed
   series**. On the eleven tasks both arms finished, cached-read tokens come to 111,029,679
   for arm A against 107,988,315 for arm B — **10.09M against 9.82M per run, 2.7% apart,
   arm B the lower of the two** (*our arithmetic*: sum `tokens.cache_read` over the last
   line of the eleven paired records on each side and divide by eleven; neither script
   prints this subtotal, and the paired task list is in script §2).
   An earlier version of this line put it at 9.98M against 9.82M and called it "within 2%".
   That figure took **12** arm-A runs against **11** arm-B ones, because arm A has a T9 and
   arm B does not — two different task sets, which is not a comparison. T9-A reads fewer
   cached tokens than arm A's average, so including it pulled arm A's per-run figure down
   and made the two arms look closer than the paired data does. The direction of the
   correction, stated because every entry here states one: the paired gap is **wider**, and
   it runs toward the arm we own carrying *less* cached context per run, not more. The
   hypothesis is dead on either set. And "per run" is not "per step" — the arms
   did not take the same number of steps, and no per-step figure is published — so this
   retires the claim rather than establishing its opposite. We are leaving it here because
   we published it in-flight and it did not survive.
5. **"The baseline is better on quality: more test cases, and the only convention
   guards."** Weakened by entry 14. The baseline had repository-authored procedure
   descriptions in its context in every single run and the agent arm had none in any. We
   still report the observation; we no longer attribute it to the arms' methods.
6. **"The agent gets cheaper as the codebase grows."** The late-half figure looks like it
   (script §4: early +41.8%, late −27.3%) and the script prints a three-paragraph warning
   next to it saying the split is confounded by task content, by wall-clock position, and by
   amendments that landed mid-series. The two arms were also not run side by side: the
   median gap between the arms' starts of the same task is 3.76 h (range 3.04–8.02 h), and
   the mean machine load differs sharply between the halves. We report the shape and
   explicitly do not claim it.
7. **"The cumulative curves cross and P2 holds."** Killed by the adversarial review. See
   the halt.

What we are left with, on cost, is a draw inside the noise. That is a duller answer than
either of the ones we held during the run, and it is the one the data supports.

---

## Where the numbers stand

From `python3 analyze.py data`, §2:

- Head-to-head over the 12 tasks **both** arms completed: arm A `$43.5772`, arm B
  `$42.2890` — **−3.0%** for the agent arm. *(Before arm B's T9 was re-run, the same
  comparison over eleven tasks read `$40.7176` against `$37.8134`, −7.1%. The twelfth
  task moved it against the arm we build — entry 19.)*
- Correctness at which those costs were reached: **verified ×12 on both sides**, and on
  first pass as well — one red gate each. Equal correctness is a condition of the primary
  endpoint, not a footnote. One green on each side is weaker than it reads: T12's
  acceptance pack ships an end-to-end check the gate never collected, for either arm
  (entry 17).
- The agent arm is cheaper in **5 of 12 individual pairs**. It wins the total while losing
  the majority of pairs: the total is carried by a few large tasks, not by a broad
  advantage, and the script says so in its own output.
- The median observed spread between two runs of the same task by the same arm is **21.5%**,
  the largest **103.4%**, with **zero** repeats under identical conditions (§6). The −3.0%
  sits well inside that.
- **The series is complete.** Twelve of twelve in both arms; no slot is open. What is
  *not* complete is the pre-registered plan of three pairs — this is one.

---

## What we would do differently

For anyone attempting a measurement of this shape, in rough order of how much pain each one
would have saved us.

**Equalise the environment by construction, and assert it.** Both arms should be launched
through the *same* code path with the *same* explicit environment — runtime version,
permissions, the contents of the working tree — with a meta-test that fails the run when
they diverge. We built that test, but only after the confound had already cost us a full
arm's worth of runs. Two of our worst defects (entries 8 and 14) are the same defect at
different layers: nobody diffed the two arms' starting conditions before starting.

**Inventory both working trees before every episode, and put the inventory in the record.**
File counts and directory listings for both sides, compared automatically. Entry 14 would
have been caught on day one by three lines of shell.

**Dedicated accounts per arm, and cost attributed per work tree from the first line of
code.** Per-account accounting is only correct on an account nothing else touches, and you
will not notice the difference until you go looking.

**Budget repeats under identical conditions from the start.** We finished with zero of
them, so we cannot state a noise floor — only an upper bound that mixes randomness with the
effect of whatever change prompted the repeat. Two or three repeated slots per arm, run
deliberately and changing nothing, would have made every comparison in the report
interpretable. This is the single change we would most want back.

**Interleave the arms, or randomise the task order — and separate the arms' windows.**
Both arms took the tasks in numeric order, so within an arm, task position and wall-clock
position are one axis: any "it gets better later in the series" claim is uninterpretable by
construction, and we had to say so rather than make it. The two arms' windows were not
separated either. Arm A ran 08:52–18:54 and arm B 16:53–22:02 on one host, so arm A's
T9–T12 executed alongside arm B's T2–T5 and each arm spent two hours inside the other's
noise floor — which is where the load figures in the early/late split come from, and part of
why that split cannot be read as a result. Randomised task order fixes the first problem;
only disjoint windows, or a host per arm, fix the second.

**Make every gate fail closed, and test it by removing its caller.** "No tests found" must
never be a pass. A module that is a gate must have a caller, and there must be a test that
goes red when the call is deleted — for us, reverting both wirings turned exactly three
tests red, which is how we know they are gates rather than decoration.

**Collect the acceptance pack from its manifest, not from a filename pattern.** A pattern
is a guess about what a pack contains; the manifest is the pack's own statement of it. Ours
matched unit test files and silently walked past the one end-to-end check in the whole
frozen set, so a task read green on both arms with its only integration oracle unexecuted
(entry 17). The gate should compare what it collected against what the pack declares and
fail closed on any difference — a check that ran fewer files than it was given is a check
that did not run.

**Do not let the measurement environment listen on a public interface.** Ours published a
throwaway database's port on every interface, and a port published through the container
layer sits ahead of the host firewall, so the firewall never saw it. Somebody found it in a
day and ran their own workload on the measurement host (entry 16). Bind to loopback, and
verify what the environment is listening on before an arm starts rather than reading it out
of a log afterwards.

**Keep one clock, or label every timestamp with its zone.** Our records carry local time in
one field and UTC in another. We read a UTC stamp against the local fields and turned a
twenty-minute incident into a two-hour-forty-two-minute one overlapping seven runs instead
of three (entry 16). Two time bases in one record is a defect waiting for a reader.

**Count rework iterations by sessions started, not by scheduler ticks.** An iteration that
dispatched nothing is not the arm's failure and must not be scored as one. Distinguish
"the arm failed", "the harness failed", and "no measurement was taken" — three states, not
two — and make the third one visible in the record instead of letting it read as a zero.

**Assume the environment carries secrets, and scrub before the first byte of raw data
reaches a publication path.** Have secret patterns from the beginning, and pair them with a
list of the actual values you know about, because pattern-matching alone cannot tell a
credential from a commit hash without context.

**Have an adversarial reviewer who did not write the thing being reviewed, and run it
before publication, not after.** Ours found the two defects we would never have found
ourselves — a confound with no symptom, and our own report's slant. Give it standing to
stop publication, or it is decoration.

**Keep one script as the single source of every number, or label the exceptions in the
text.** The moment a report mixes script output with hand-computed tables and claims
otherwise, the reader has no way to tell which is which — and neither, it turns out, do the
authors.

**Decide before the run what happens when the substrate is broken.** Our database never
came up for either arm. Symmetric, so not a confound — but it silently narrowed what the
whole experiment can claim, and we would rather have made that trade knowingly than
discovered it in the caveats.

---

*Every run record referenced here is in `data/`, including the ones that were thrown out
and the reasons they were thrown out, and the amendments are in `frozen/AMENDMENTS.md`.
That is the whole of what this package contains, and it is less than what this logbook
cites. What is **not** here:*

- ***Session transcripts.** They carry credentials from the run host, and a rewritten
  transcript is not evidence (`data/README.md`, "What is not here"). Every figure marked
  *not reproducible here* in entries 7, 8, 10, 11 and 14 was counted over them.*
- ***The two arms' work trees**, both the starting checkouts and the final module trees.
  The convention and volume counts in entry 12 and in `REPORT.md` §3–§4 were taken over the
  arms' output, and the tree inventory in entry 14 over their checkouts. Publishing either
  is a separate decision that has not been taken.*
- ***The forensic capture behind entry 16.** The file sizes, the log line and the state of
  each arm's container come from it, and it is not published.*
- ***Thirty-two of the 51 hash-committed frozen files**, among them every hidden acceptance
  pack — including the one in entry 17 that never ran. They stay withheld because the same
  packs are pre-registered for runs that have not happened yet. `frozen/WITHHELD.md` is the
  accounting; it leaves the pre-registration's promise to publish them standing unfulfilled
  rather than quietly rewritten.*
- ***One attempt with no record at all.** The T5 run cut mid-flight in entry 8 never closed,
  so nothing was written for it and its compute is in no total anywhere in this package. Its
  only trace is in the published journal.*

*Where this logbook and the amendment log disagree, the amendment log was written first and
wins.*
