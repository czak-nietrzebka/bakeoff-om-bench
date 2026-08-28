# Experiment 2 — a second model family, pre-registration

Committed before any Experiment 2 run. Experiment 1 (Claude Sonnet against the same
model wrapped in a process) is complete and published in this repository; this document
fixes, in advance, everything that will be different when the same twelve frozen tasks
are run on **GPT-5.6 Sol through the Codex CLI** — and everything that will not.

The question is the one the whole bench exists for: **is the process a property of one
model, or does it transfer?** Experiment 1 ended in a tie inside the noise band, with
the czak arm losing every small task and winning every large one. If that shape is real,
it should reappear under a different model. If it was Sonnet-specific, it should not.

## 1. What is identical, byte for byte

The twelve task texts, the hidden acceptance packs, the gate (fresh checkout, pristine
dependencies, targeted run of the pack, fail-closed verdict), the one-line feedback
format, the DNF iteration cap (5), the per-task size classes and token budget values,
the append-only ledger and journal, the third state (not-measurable), and the
adjudication rules — all reused from Experiment 1's frozen artifacts, unmodified,
verified by the same `frozen/MANIFEST.sha256`. The base commit is the same upstream pin
(`15ffbe30c`); the series branch is `bakeoff/p2`; both arms get fresh workspaces.

The arm definitions are the same two methods:

- **Arm A — the baseline.** The vendor's own agent CLI, "as advertised", in a clean
  checkout: `codex exec` with a workspace-write sandbox, handed the frozen task text
  with the same non-interactive preamble Experiment 1 used, byte-identical.
- **Arm B — the czak.** The same model behind the same process as Experiment 1:
  ticket, branch in a worktree, self-verify command, pull request, gate on the pull
  request head, squash-merge on green. The **only** replaced component is the session
  engine — the hook that starts an agent in the worktree now starts `codex exec`
  instead of the Claude CLI. Ticket handling, branching, gating and merging are the
  same code paths that ran Experiment 1.

## 2. What is different, and why — every difference declared here

| # | difference | reason | direction of risk |
|---|---|---|---|
| D1 | Model `gpt-5.6-sol`, CLI `codex-cli 0.148.0`, both pinned | that is the experiment | — |
| D2 | Cost accounting reads the spawned process's **own stdout** (`turn.completed` usage events), not transcript files on disk | the vendor prints per-turn usage; a closed world built from the process's own output makes Experiment 1's A4 class (billing one arm for someone else's work) impossible by construction | strictly better instrument |
| D3 | **No stateful containers at all** | measured in Experiment 1: in the entire life of the benchmark database exactly one connection ever came from the application, it failed immediately, and no task needed it — while the open port got the host compromised | removes E1's §5.6 confound |
| D4 | One ChatGPT account (a `pro` plan) serves **both arms** | it is the account that exists; Experiment 1 discovered its two "separate" accounts shared one subscription pool anyway (logbook entry 23) | declared up front this time: the arms are **not resource-isolated**, one arm's spending can starve the other, and a plan-limit interruption voids runs rather than failing them (the entry-23 rule: budget exhaustion is a verdict about the task only when the meter that ran out belongs to the task); a liveness probe runs before every task |
| D5 | Working-token metric for the DNF budget: `(input − cached_input) + cache_write + output` | OpenAI reports different token classes than Anthropic; this is the closest analogue of E1's "in + out + cache-creation, without cache reads" | budgets are stopping rules, not endpoints; cross-experiment token totals are **not comparable** and will not be compared |
| D6 | Dollar imputation from a price table frozen in `pricing-e2.json` (input $4/M, cached input $0.40/M, output $20/M; requests over 272k input tokens pay 2× input and 1.5× output for the whole request), dated, source recorded | the primary endpoint is imputed dollars, and the long-context surcharge applies per request — so usage is recorded **per turn** and the surcharge applied per turn, not to the sum | — |
| D7 | The czak system prompt reaches the engine **prepended to the user prompt** instead of through a system-prompt flag | `codex exec` has no append-system-prompt option; the text is identical, the channel is not | declared; affects arm B only |
| D8 | Reasoning tokens are reported as their own class | the vendor reports them; they bill as output and are **not** added twice | — |
| D9 | **Task content reaches arm B inside the engine prompt**, appended to the ticket-driven prompt (which still carries the ticket number for the commit trailer) | measured in Experiment 1's transcripts: the Claude agent received only the ticket *title* from the process and fetched the ticket body itself over the local forge API — a network-dependent step the Codex sandbox does not reliably reproduce; the content is the same bytes arm A receives, so delivery is deterministic and 1:1 | makes arm B's discovery *cheaper* than E1-B's (no fetch step); declared so the cross-experiment shape comparison can account for it |
| D10 | The mid-series requirements change (T5) triggers on **green phase-1 gate or a 20-minute fallback** — the transcript-based typecheck detector is not ported | that detector reads Claude CLI transcript files, which this engine does not produce; the gate-green channel (the dominant one in E1) is engine-independent and unchanged | — |
| D11 | Arm B's **self-review step runs on the engine under test** (same review instructions, same local diff, verdict contract unchanged) | the process's default self-review calls a Claude-based reviewer: a step of the measured method would execute on a different model than the one being measured — and on a dead account would block the whole arm | self-review tokens count toward arm B's cost, as they did in E1 |
| D12 | A red gate that ends a run in DNF also **closes the task's open pull request** | found in review: a stale-open pull request from a DNF'd task would remain a selectable candidate; with the gate now selecting by ticket number the mis-merge is already impossible, this removes the stale object itself | — |

**On instruction asymmetry (Experiment 1's A8):** the repository ships `AGENTS.md` and
an agent-procedure catalogue. The Codex CLI reads `AGENTS.md` from the working
directory natively — and arm B's worktree is a checkout of the same repository, so
both arms' engines see the same file by construction. Whether that symmetry actually
holds (does the engine load it in both launch modes?) is a **pre-flight check with a
recorded answer**, not an assumption: it will be measured on the calibration pilot
and written into the symmetry table before the series runs. If it is measured
asymmetric, that is A8 again and the series does not start until it is resolved.

## 3. What is measured

Identical to Experiment 1. Primary endpoint: cumulative imputed dollars to a
runner-verified green gate, per task and summed, at equal correctness. Secondary:
rework iterations, wall-clock (within arm only), per-turn token classes, the R8
convention checklist, and the run-to-run spread wherever repeats exist.

The four public predictions P1–P4 apply per-experiment, as written in the original
pre-registration. For P4 the situation is stated plainly: **the audit-trail rubric it
references was never authored** — Experiment 1's fifty-one frozen files contain a
quality rubric but no audit-trail rubric, so P4 was unfalsifiable as pre-registered
(logbook entry 24). It remains unadjudicated in Experiment 2 unless a rubric is
frozen **before** this experiment's first run and named in an amendment.

## 4. Schedule and hygiene rules

- Calibration pilot first (T1, both arms, thrown away), exactly as in Experiment 1 —
  it exists to catch harness defects before they become results, and in Experiment 1
  it caught five.
- Arms alternate order per task (A-first on odd tasks, B-first on even), serially,
  on the same host. Wall-clock comparisons between arms remain confounded by shared
  hosting and are reported within-arm only.
- Before every task: a liveness probe of the engine (a one-word reply). A probe
  failure stops the series instead of writing DNFs — entry-23 rule.
- Pack residue scan after every gate, both the workspace and the worktree area
  (Experiment 1's R8, with the worktree path included from the start).
- The gate selects arm B's pull request **by ticket number**, never by branch
  pattern. Honesty requires the history here: the defect was found on 27 August in
  Experiment 1's harness, and the **first draft of this experiment's driver reproduced
  it** by reusing that gate unchanged — the adversarial review of this document and
  its drivers caught the reproduction before anything ran. The E2 gate wraps the E1
  gate with a selector that accepts only `<branch-prefix>/<ticket-number>` on this
  experiment's base branch.
- Every record append-only; corrections appended, never overwritten; a run that
  infrastructure breaks leaves an `infra-void` record, not a hole.

## 4a. The review that preceded this document

The drivers and this protocol went through a three-lens adversarial review (arm
symmetry, measurement integrity, code against the real orchestrator API), with every
non-trivial finding independently re-verified against the sources. Of the review's
findings, **fourteen were confirmed** and led to changes now reflected above, among
them: the reproduced pull-request selector defect (§4), the missing task content in
arm B's prompt (D9), the self-review step running on the wrong model (D11), a session
timeout that silently differed 2× between the arms, an environment that leaked the
orchestrator's secrets into both engines' processes, a $0 record that would have
passed the ledger as a real measurement when the engine emitted no usage at all, and
a double-counted token class in the working-token metric. One finding was refuted in
verification. The point of recording this is not the score: it is that **every one of
these would have been a published number** had the review not run first.

## 5. What this experiment cannot say

Nothing here compares GPT-5.6 Sol to Claude Sonnet as models. The two experiments
share task texts and gates but differ in accounting units, price tables, and
context-handling behaviour; the only cross-experiment comparison this design supports
is the **shape of the czak-versus-baseline delta** (sign, size-class pattern,
crossover), not absolute costs. Any sentence of the form "model X is cheaper than
model Y" quoted from this benchmark is a misreading, and this section exists to be
pointed at when it happens.

-- lee
