# Raw data — Experiment 1

This directory is the raw material the pre-registration promised to publish after the
series, whichever arm won: the per-run records, the series journal, and a usage summary
computed from them. It also contains the runs we **threw out**, with the reasons, because
a benchmark that publishes only its surviving runs is not publishing its data.

Read this file before reading any number. Several of the caveats below are large enough to
change what you conclude.

```
data/
├─ README.md                  this file
├─ journal-p1.jsonl           append-only event log of the whole series
├─ usage-summary.json         per-run usage, computed from runs/ — never typed by hand
├─ usage_summary.py           the script that computes it (stdlib only, no arguments)
├─ SCRUB-REPORT.json          what was removed before publication, and the check that it was
└─ runs/
   ├─ p1-T<n>-A.jsonl         arm A — naive baseline (12 files)
   ├─ p1-T<n>-B.jsonl         arm B — agent with process (12 files)
   ├─ pilot-kalibracja/       ARCHIVE — calibration pilot        + README + its own journal
   ├─ obciazone-a5/           ARCHIVE — runs burdened by confound A5 + README
   └─ falstart-bez-tozsamosci/ ARCHIVE — false start, zero measurement + README
```

The archive directory names are the original ones from the run host and were deliberately
not renamed; each carries a README in English explaining why its records do not count.

---

## How to read an append-only record

**Every `.jsonl` file under `runs/` is one task slot, not one run.** Each line is a complete
snapshot of that slot's state at the moment it was written. Lines are only ever appended —
a correction never overwrites the line it corrects.

**The last line is the current state. Everything above it is history.**

```
$ tail -n 1 data/runs/p1-T7-A.jsonl        # the state that counts
$ cat      data/runs/p1-T7-A.jsonl         # how it got there
```

A line whose `notes` field begins with `CORRECTION` is an amendment written after the fact.
It restates the whole record with the corrected values and says, in prose, what changed and
why. So `runs/p1-T1-A.jsonl` has two lines: the original, and the line that re-attributes
its cost per work tree instead of per account (amendment A4). Both are published; the
original figure is still there to check the correction against.

Some slots took several attempts. `runs/pilot-kalibracja/p1-T1-A.jsonl` has five lines and
walks through a false green, a did-not-finish, its adjudication as infrastructure rather
than rework, and finally a verified run. That whole path is the record.

Because of this, **do not sum a file — sum the last line of each file.** `usage_summary.py`
does exactly that, and nothing else.

`journal-p1.jsonl` is a flat event stream for the whole series, ordered by time, one event
per line: session spawns, session ends, validation-gate attempts and results, gate feedback
handed back to an arm, and the four deliveries of the mid-series requirements change. Join
it to the records on `run_id`.

---

## Field dictionary

Some field names are in Polish, because that is the language the instrument was written in
and renaming keys after the fact would make the published records differ from the ones the
runs actually produced. They are glossed here.

### Identity and configuration

| field | meaning |
|---|---|
| `run_id`, `pair`, `task`, `arm` | slot identity; `arm` is `a` (naive baseline) or `b` (agent with process) |
| `sha_om` | commit of the arena repository — public, identical for every run in the series |
| `sha_czak` | revision of the private testbench tree that produced the record. **Pseudonymised** (see below); distinct revisions keep distinct labels, so you can still see *that* the instrument changed between runs |
| `sha_skills` | which framework skills the arm had. `pin-w-frozen` = pinned in the frozen bundle; `niezmierzone-repo-skills` = present but the installer left no explicit revision behind |
| `base_branch` | branch the series was built on |
| `model_id`, `cli_version` | the model and agent CLI. Identical for both arms |
| `host` | **Scrubbed.** The runner host |
| `frozen_hash` | SHA-256 of the frozen bundle handed to the run — ties each run to the pre-registered manifest |
| `session_ids` | **Pseudonymised.** The list length is preserved, which is the part that matters: an empty list means *no session ever started*, i.e. no measurement was taken |

### Usage and cost

| field | meaning |
|---|---|
| `tokens.in` / `.out` | plain input / output tokens |
| `tokens.cache_creation_5m` / `.cache_creation_1h` | cache writes at the two retention tiers |
| `tokens.cache_read` | cache reads |
| `tokens.thinking` | **a subset of `out`**, reported separately for information. It is *not* added to the cost a second time |
| `usd_imputed` | imputed cost. The runs were made on a subscription, which does not bill per token, so dollars are a *model*: token counts times the rate card frozen in `frozen/pricing.json` before any run. The rate card is dated and the imputation picks it by the run's start date |
| `token_budget` | the working-token cap for this task's size class |

Working tokens (the metric the budget uses) are `in + out + cache_creation_5m +
cache_creation_1h`, deliberately **excluding** `cache_read`: cheap re-reads would otherwise
dominate and penalise whichever method carries the larger prompt. The rule is symmetric for
both arms and was fixed before the runs.

### Time

| field | meaning |
|---|---|
| `wall_start`, `wall_end` | ISO-8601 **without an offset**, in the runner's local time, which was UTC+02:00 throughout the series |
| `ts` (inside `gate_runs` and in the journal) | Unix epoch seconds, **UTC** |
| `compute_active_s` | seconds the arm's session was actually working |
| `gate_time_s`, `build_time_s` | seconds spent in validation and in build |

The two time bases differ by the two-hour offset — do not mix them. Worked example: T1-A's
gate `ts` 1787727622.83 is 07:00:22 UTC, which is the same instant as that record's
`wall_end` of `09:00:22`.

### Outcome

| field | meaning |
|---|---|
| `verdict` | `verified` (the validation gate went green) or `failed` |
| `disposition` | `complete`, `DNF` (did not finish), or `infra-void` (the run was voided as an infrastructure failure under a pre-registered adjudication, not counted as a failure of the arm) |
| `rework_iterations` | rework loops after a red gate |
| `gate_runs[]` | one entry per validation attempt: `iteration`, `ts`, `pack_id`, `pack_task`, `passed`, `failed_test_ids` |
| `dnf_reason` | `iteracje` = the iteration cap was reached; `pilot-jeden-tick` = the pilot ran a single tick with no rework loop |
| `t5_trigger_at`, `t5_delivered_at` | when the mid-series requirements change was triggered and delivered |
| `rate_limit_events[]` | rate-limit hits; empty everywhere in this series |
| `human_touch[]` | human intervention during a run. Empty everywhere — a non-empty list voids the run under adjudication 6 |
| `compact_boundary_count` | how many times the session's context was compacted |
| `load_avg` | the runner's 1/5/15-minute load average, kept because arm B's runs ran on a visibly busier machine (see A6 below) |
| `notes` | free text; `CORRECTION` marks an after-the-fact amendment |

### `nie_umiem_zmierzyc` — the third state

Literally *"I cannot measure this"*. A list of `{"pole": <field>, "powod": <reason>}`,
where `pole` is the field and `powod` the reason.

This exists because a measuring instrument has **three** outcomes, not two: measured-well,
measured-badly, and *could not measure*. The third one has to reach the reader, or a gap in
the instrument silently reads as a finding. `context_rebuild` is `null` in every record in
this series for exactly this reason: the decomposition was never implemented, so it was
done post-hoc from transcripts and the field was left empty rather than filled with a guess.

Journal payloads use `mechanizm` for *mechanism* in the same spirit.

---

## Why the archives are in separate directories

Three sets of records were produced during this series that must not enter any statistic.
They are published, in their own directories, each with a README:

- **`runs/pilot-kalibracja/`** — the calibration pilot, run the day before the series under
  conditions that amendments A1 and A2 then changed. It measures the testbench, not the arms.
- **`runs/obciazone-a5/`** — arm B's T1-T4 from the series, invalidated when confound A5 was
  found: arm B had been running on the wrong Node version while arm A had the right one.
  An unequal start, loading onto arm B one-sidedly. Kept as the evidence for the confound.
- **`runs/falstart-bez-tozsamosci/`** — twelve runs that never started, because the arm had
  no identity to work with. `$0.00`, zero tokens, zero work. A `$0.00` line means *no
  measurement*, not *free work*.

They are separate directories rather than a flag inside the main files for one reason: a
flag gets dropped by whoever writes the next `jq` one-liner. A directory does not. Nothing
in `usage_summary.py` counts anything under a subdirectory of `runs/` towards the series,
and the summary reports what those runs cost anyway, so the money is not hidden.

The same principle applies inside the series: `runs/p1-T9-B.jsonl` sits at the top level but
its last line is `infra-void`, so it does not count either, and it is listed in the
summary's `empty_slots`.

---

## What was removed before publication

Nothing was deleted. Where a value would have exposed the operator's infrastructure, the
**value** was replaced with a marker and the **key was kept**, because dropping keys breaks
reproducibility for everyone downstream.

| field | what happened | what you lose |
|---|---|---|
| `host` | replaced with `[scrubbed:host]` | the machine's name. All runs were on one host, so no comparison depends on it |
| `session_ids` | each identifier replaced with a stable pseudonym; **list length preserved** | you cannot join to the session transcripts, which are not published. You can still see how many sessions a run took, and that some took none |
| `sha_czak` | each distinct revision replaced with a stable pseudonym | the revision hash of a private tree. You can still see when the instrument changed mid-series |
| `tool_use_id`, `spawn.uuid` (journal) | replaced / pseudonymised | as above |
| `notes`, `nie_umiem_zmierzyc[].powod`, one `sha_skills` value | rewritten in English, with internal tool and ticket names replaced by what they are (`the scheduler`, `the task ticket`, `unrelated workloads on the same account`) | the original Polish wording. The substance — what happened, what was measured, what was fixed — is unchanged, and every number quoted inside a note is untouched |

**Every numeric, structural and outcome field is byte-for-byte what the instrument wrote.**
No token count, cost, timestamp, verdict, disposition or gate result was touched.

Every published file was then passed through the project's scrubber with an explicit list of
240 secret values read from the operator's private environment file on the run host — the
values never left that host — and through its oracle, which reports any remaining match of
any pattern class. **All 49 files returned zero matches, and the scrubber changed zero
bytes**, meaning the files were already clean rather than quietly rewritten at the last step.
`SCRUB-REPORT.json` carries the per-file result and the input/output hashes.

---

## Caveats you must carry into any reading

These are not footnotes. Each one is capable of changing the conclusion.

1. **Run-to-run spread is larger than the difference between the arms.** Five task slots
   were taken to a verified-green result more than once. The cost of the same task, by the
   same arm, varied by 2.1%, 6.6%, 21.5%, 63.6% and 103.4% between attempts. The headline
   difference between the two arms over the series is smaller than three of those five
   figures. See `repeat_runs` in the summary. The repeats are themselves confounded — the
   attempts straddle amendments A1, A2, A4 and A5 — so they are an *upper* bound, not a
   clean estimate of noise. There is no clean estimate of noise in this dataset. That is a
   limitation of the experiment, not a detail.

2. **One slot is empty.** Arm B has no valid T9. The run it made was voided as an
   infrastructure failure (its rework loop could not dispatch, so four of its five
   iterations produced no session at all), and the re-run has not happened. Any total that
   compares 12 arm-A tasks against 11 arm-B tasks is not a comparison. The summary
   therefore reports both the raw per-arm totals *and* a like-for-like total restricted to
   the tasks both arms completed, and lists T9-B under `empty_slots`. The voided run still
   cost money, and the summary reports that too.

3. **The arms were not run in adjacent time windows** (amendment A6). After A5 was found,
   arm B was re-run as its own sequence while arm A kept its original one. The design
   allows this — each arm has its own work tree, its own pin and its own task order — but it
   **removes** the assumption that a pair shares momentary conditions: machine load, time of
   day, service-side variation. `wall_start`, `wall_end` and `load_avg` are in every record
   so that this is readable rather than hidden; arm B's runs ran on a visibly busier machine.

4. **Cost accounting changed mid-series** (amendment A4). Cost was originally attributed per
   account; arm B's account was shared with unrelated workloads, so its runs were being
   charged for work that was not theirs. Attribution moved to per work tree. The error was
   **asymmetric and loaded onto arm B**. Every affected record carries both figures, and
   with the filter switched off the same calculator reproduces the original to the cent.

5. **Arm B's first four runs happened on the wrong runtime** (amendment A5) and were
   invalidated, not silently repaired. Arm A was unaffected and was not re-run — so the two
   arms' T1-T4 do not have equal provenance.

6. **The database never came up, for either arm.** The greenfield and seed steps failed on
   both sides at the start. The state is symmetric, so it is not a confound between the
   arms, and it was deliberately *not* fixed mid-series because fixing it for one arm only
   would have created one. The consequence is real and limits what the series can claim:
   tasks were verified by unit-level test packs, not by working against a live database.
   **Nothing here says anything about whether the migrations these tasks wrote are correct
   against a real schema.**

7. **This is an exploratory bench with a hard oracle, not a significance test.** One pair,
   twelve tasks. It is labelled as such in the pre-registration and nothing in this data
   changes that.

8. **The benchmark is designed and run by the team whose agent is under test.** The
   mitigations are the ones you can inspect: public pre-registration, hidden packs
   hash-committed in advance, an external validation oracle, pre-registered adjudications,
   and this directory.

The authoritative list of amendments is `frozen/AMENDMENTS.md`. Where this README and the
amendment log disagree, the amendment log is older and wins.

---

## Reproducing the summary

`usage-summary.json` contains no hand-entered number. Regenerate it from the raw records:

```
$ python3 data/usage_summary.py --print
```

Standard library only, no arguments, no network. It reads the last line of every file under
`data/runs/`, recomputes each cost from the token counts and the frozen rate card in
`frozen/pricing.json`, and writes `data/usage-summary.json`.

To check that the published file is the one the records produce:

```
$ python3 data/usage_summary.py --check
```

The recomputation is also a check on the instrument: the summary reports, for every record
including the archived ones, whether the cost stored in the record matches the cost
recomputed from its own token counts. At publication, all 42 agreed to the cent.

The SHA-256 of `frozen/pricing.json` is recorded in the summary and is listed in
`frozen/MANIFEST.sha256`, which was committed before any run — so the rate card used for
these dollars is verifiably the pre-registered one.

## What is not here

Session transcripts. They are the source the token counts were read from, but they contain
operational material from the run host, including credentials pasted into shell commands
during the runs. Publishing them safely would mean rewriting them, and a rewritten
transcript is not evidence. The pre-registration promised raw per-run records, usage
summaries, the withheld frozen files and the analysis — not transcripts — and that is what
is published.
