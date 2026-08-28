# Symmetry table — what is held equal, and what is the measurement

Frozen before any run, as required by the pre-registration: *"what differs, and why that
difference is the OBJECT OF MEASUREMENT rather than a confound."*

Read it with `AMENDMENTS.md` open. This table states the **design**; four of its rows did
not survive contact with the runs, and the annex at the bottom says which.

> **This file is a redaction, and it does not match its manifest hash.**
> `frozen/MANIFEST.sha256` pins the frozen original at
> `d7bb0b75c243b9ee29f9b5abb47054336086a6dc805d4febbbaf60a39dfa3f41`. That original is in
> Polish and three of its cells describe how the agent arm is built internally, which is
> not published. What you are reading is translated and redacted, so it **will not** hash
> to that value, and it is not evidence in the way the hash-committed files are. Exactly
> what was taken out is listed under the table — nothing was removed from the columns that
> say what was held equal.

| dimension | arm A — naive baseline | arm B — the agent | status |
|---|---|---|---|
| model | `claude-sonnet-5` (pinned) | `claude-sonnet-5` (pinned) | **IDENTICAL** |
| CLI build | same version, autoupdate OFF | same | **IDENTICAL** |
| account | dedicated to A (reserved) | dedicated to B (reserved) | symmetric *(see annex — this did not hold)* |
| sessions | fresh per task and per iteration; `--resume` FORBIDDEN | same | **IDENTICAL** |
| permission surface | `--permission-mode acceptEdits --allowedTools "Bash Read Glob Grep Edit Write WebSearch WebFetch"` | the same effective tool list, plus the operator's own operations tools, which do not touch the arena repository | roughly equal; the difference is enumerated rather than assumed |
| standing prompt | the arena repository's `AGENTS.md` (32 KiB, their own CI budget) + their skills at the pin | the agent's standing process prompt (~48 kB in total) | **OBJECT OF MEASUREMENT** — this *is* method against method |
| carrier of continuity between tasks | workspace + `git log` + its own notes (`.ai/`, `CLAUDE.md` — full rights) | workspace + a task ticket per task in an issue tracker | **OBJECT OF MEASUREMENT** |
| task spec | frozen verbatim, identical file | the same text verbatim, delivered in the ticket | **IDENTICAL in content**; the channel differs, and the channel is the method |
| T5 requirements change | appended to the next session's prompt | a comment on the ticket, plus the next session's prompt | symmetric moment (deterministic trigger); channel = method |
| review | none — the arm decides for itself when it is done | an in-session self-review pass by a second agent before the work is offered | **OBJECT OF MEASUREMENT** |
| done verdict | the RUNNER: the framework's own validation + the hidden packs | the same runner, the same packs | **IDENTICAL** |
| feedback after a red gate | frozen format, `test-id::assertion` | same | **IDENTICAL** |
| humans in the loop | zero (pre-registration rule R12) | zero | **IDENTICAL** |
| billing / measurement | closed-world account manifest + parser | the same, plus a cross-check that only arm B can emit | instrument identical; the cross-check is one-sided and that is enumerated |

## What was redacted from this file, and what it costs you

Three cells were reduced. In each case the **fact that matters for judging the experiment**
is kept and only the internal composition is dropped.

| cell | what the original said | what is published | what a reader loses |
|---|---|---|---|
| standing prompt, arm B | the prompt's name and its breakdown into named internal components with their sizes | the total size (~48 kB) | the internal structure of the agent. **The comparison itself is intact**: both arms' standing-prompt sizes are stated, 32 KiB against about 48 kB, which is the only part of it this benchmark can measure |
| permission surface, arm B | the name of the internal permission profile | what that profile grants, in tool terms | a label. The tool list — the thing that decides what each arm could actually do — is unchanged |
| continuity carrier and review, arm B | internal names of the issue tracker and of the reviewing role | what they are: a ticket per task, and a self-review pass inside the session | product names. What was done, and by what kind of actor, is unchanged |

Nothing was removed from the arm-A column, and nothing was removed from any cell marked
IDENTICAL. A redaction that quietly widened or narrowed a claimed symmetry would be worth
more than the internals it protects, so those cells were left alone.

## Annex — where the runs departed from this table

The table is the **pre-registered design**. The series then departed from it four times.
Each departure is in `AMENDMENTS.md` with its measurement; this annex only maps them onto
the rows, so that the table cannot be read as a description of what happened.

| row | what actually happened | amendment |
|---|---|---|
| **account** — "dedicated to B" | arm B ran on an organization **shared with unrelated workloads**; only two usable organizations existed. Those workloads were paused per window, and any leakage loads the arm under test, never the baseline | **A3** |
| **billing / measurement** — "closed-world account manifest" | attribution per account turned out to charge arm B for other people's sessions; it was changed mid-series to per-work-tree. The error was asymmetric and inflated the arm under test by 14.5% on the T1 pair | **A4** |
| *not a row at all* | the two arms were handed **different Node runtimes**. Arm B's first four runs are archived as loaded | **A5** |
| *not a row at all* | arm B's sessions inherited the parent process environment **including a credential**; arm A's did not. Behavioural, not cosmetic, and this table does not list it — which is itself the point | **A7** |
| *not a row at all* | arm A's tree carried a catalogue of **51 repository procedures** whose listing entered its context in 12 of 12 runs; arm B's tree had none. Found after the series closed, and it runs **against** this benchmark's own thesis | **A8** |
| **sessions were paired in time** (implicit in the design, not stated as a row) | after A5 the arms stopped being measured in adjacent windows, so a pair no longer shares machine load or time of day | **A6** |

Three of these six are things the frozen table **does not have a row for**. That is the
honest summary of what a pre-registered symmetry table is worth: it constrains the
dimensions you thought of, and the confounds that actually bit were mostly in dimensions
nobody had written down.
