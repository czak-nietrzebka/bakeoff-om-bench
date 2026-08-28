# E-MAINT — maintenance phase, pre-registration

Written and hash-committed **before** any arm was started. Series E1 (twelve build
tasks, `claude -p` versus the same model driven through a process) is finished and
published. This phase asks the question E1 cannot answer: **what does the code cost
to keep alive afterwards.**

Everything below — design, baselines, verdict rules, stop rules, the control-step
numbers, and the list of things we already know are crooked — is fixed at the moment
of publication. The hidden material (test packs and answer keys) is withheld under a
hash so that publishing the specs cannot leak the oracles; the hash is in
`WITHHELD.md` and the material is released with the results.

## 1. What this phase measures

E1 measured the cost of *writing* twelve features. The claim we want to test now is
about the other side of the ledger:

> A codebase produced through a process is cheaper to maintain later, because a
> later session — one with no memory of how the code came to be — can reconstruct
> intent from what the process left behind.

That is a claim about **a stranger's session**, not about the original author. So
every maintenance task is handed to a fresh session, on a fresh checkout, with no
transcript, no memory, and no hint about which arm produced the code it is looking at.

The phase deliberately includes tasks the thesis could **lose** on. M5 is a
support tool wanted "by yesterday, no big philosophy" — if process is a tax, it is a
tax exactly there. M2 is a one-predicate change where discovery is the only real
work. If the process arm is slower and no better on those, that is the result.

## 2. Six tasks

| id | shape | why it is in the set |
|---|---|---|
| M1 | a production bug report in business language: one order credited a balance more than once | the fix has to be *found* first; three accrual paths each see only their own trace |
| M2 | policy extension: adjustment lines stop earning points | smallest possible change; almost all cost is discovery |
| M3 | business reversal: undo per-line accrual, go back to order-total | tests whether the arm can take code *out* without breaking what stayed |
| M4 | write an audit report of the module (11 factual questions, evidence required) | no code changes; measures whether the arm can describe what it has |
| M5 | quick internal support tool, explicitly "no big philosophy" | the case where process is most likely to be pure overhead |
| M6 | new read-only stats command | ordinary feature work, as a maintenance-phase control |

Each task ships a frozen `spec.md` (published now) and a hidden pack or answer key
(withheld under hash). Specs contain no code anchors: the reports name business
symptoms, not files, functions or entities.

## 3. Every task starts from the same baseline

E1 was cumulative — T2 saw T1's code. Maintenance tasks are mutually contradictory
by design (M3 reverses what M1 hardens), so order would be a confound rather than a
measurement. In this phase, **each task starts from the identical frozen baseline**:

- **Arm A** — the workspace is restored to a captured baseline before every task.
  Restoration is proved, not assumed: the restore compares `git status --porcelain`
  against the capture and raises if a single line differs. Verified before the phase
  by deleting a file, adding two, and modifying a tracked one — the module's tree
  digest returned to the captured value exactly.
- **Arm B** — every task branches from the pinned branch `bakeoff/emaint-base`
  (`839a590f7`) and **is not merged**. The base cannot move between tasks.

Consequence worth stating plainly: the arms cannot contaminate each other's tasks,
and no task can inherit another's fix.

## 4. The two baselines, and the asymmetry in them

| arm | baseline | loyalty module | git history of the module |
|---|---|---|---|
| A | working tree, upstream base `15ffbe30c`, **no commits of its own** | 70 files, tree digest `a538aa9b…a746f4` | none — the module is untracked files |
| B | `bakeoff/emaint-base` @ `839a590f7` | 56 files, tree digest `1b3b5c72…4fbfe6c` | squashed commits carrying ticket numbers; task branches and tickets still exist |

Both digests were re-measured on the actual checkouts the phase will use and match
the answer key's pinned snapshot to the character.

**The asymmetry is the treatment, and it was not imposed by us.** Neither arm was
told to commit or not to commit. Arm A was handed a spec in a workspace, which is
how the tool is used; it wrote code and left it uncommitted. Arm B goes through a
process that produces a branch, a ticket and a pull request per task. What a later
session can find is therefore different — that difference is precisely what this
phase prices.

**Two things this costs us, stated up front:**

1. **Arm B's baseline is one task short.** T9 was the last pair of E1 and arm B's
   run of it finished after the E-MAINT baselines and answer keys had been pinned.
   Merging it would have moved the baseline out from under the keys, so it was
   measured and left unmerged. Arm A's baseline contains its T9 work; arm B's does
   not. The keys are per-arm and encode each arm's actual state, and no task in this
   set touches the files T9 added — but B enters the phase with 56 module files
   against A's 70, and that is a real difference, not a rounding one.
2. **The arms run concurrently on one host.** E1 ran them in a fixed alternating
   order. Six tasks times two arms times a session each does not fit in the
   available window serially, so the arms run in parallel. Wall-clock is therefore
   **not comparable between arms in this phase** and is reported only within an arm.
   Token cost, the primary endpoint, is model-side and unaffected.

## 5. Verdict

Identical to E1 in shape: the runner is the only judge, and nothing a session
*writes about* its own work counts.

- **verified** — the hidden pack is green in full, the module's own suite is green
  and has not lost test files, `yarn typecheck` is green, and the repository suite is
  green. M4 has no pack: its verdict comes from a closed answer key scored by
  `score_audit.py`, which reads the report and checks that every piece of evidence it
  cites actually exists in the checkout.
- **DNF** — the token budget or the five-evaluation limit is reached first.
- **not measurable** — the third state, kept from E1: a run that infrastructure broke
  is neither verified nor DNF, and says so in the record.

Feedback after a red gate is the frozen one-line format from E1 — test id plus the
first line of the assertion — identical for both arms, with no test bodies, no paths
and no stack traces.

**Primary endpoint:** cumulative imputed cost to a green gate, per task and summed.
**Pre-registered secondary endpoints** (reported whichever way they fall):

- rework iterations to green;
- anti-overreach: the packs carry tests that are green today and go red if the fix
  overshoots (for example, blocking legitimate accruals by matching on order number
  without tenant scope);
- test attrition — files deleted or disabled rather than updated;
- **the mechanism check**: whether the session actually read any history at all
  (`git log` / `git show` / `git blame`, a ticket, a pull request). If the process arm
  wins without ever touching what the process left behind, the win is not
  traceability and we will say so.

## 6. The control step, and what it caught

No pack is a gate until someone has watched it run. Every pack was executed with the
real test runner against **both untouched baselines** before any arm started. Each
`scoring.md` declares in advance how many cases must be red on an untouched
baseline and which ones. Measured:

| task | declared | arm A | arm B | identical cases both arms |
|---|---|---|---|---|
| M1 | 3 red / 6 green | 3 / 6 | 3 / 6 | yes |
| M2 | 4 red | 4 / 0 | 4 / 0 | yes |
| M3 | 6 red / 14 green | 6 / 14 | 6 / 14 | yes |
| M5 | — | 5 / 1 | 5 / 1 | yes |
| M6 | all red | 8 / 0 | 8 / 0 | yes |
| M4 | fail-closed without a report | DNF, "AUDIT.md does not exist" | DNF, same | yes |

The green-today cases are not filler: they are the anti-regression and
anti-overreach gates, and a fix that overshoots turns them red.

**The control step caught two defects of ours before they could become results:**

1. **A pack that could not run at all.** M5 keeps its verdict rule in a helper module
   next to the tests so the rule lives in one place. The harness copied only
   `*.test.ts` into the gate checkout, so the helper never arrived and the suite died
   on `Cannot find module` — zero cases executed, in both arms. Had we trusted the
   design document, M5 would have produced two confident DNFs that measured our
   packaging, not the arms. Fixed by letting a pack carry non-test helpers from the
   same directory, with the requirement that it still contain at least one test file.
2. **Junk files from the machine the packs were authored on.** macOS resource forks
   (`._*.test.ts`) travelled inside the archive and the runner picked them up as test
   suites, reporting "file appears to be binary". Removed.

Neither would have shown up in a design review. Both showed up the first time the
packs met a real runner.

## 7. A third defect, caught the same afternoon, in the harness itself

While preparing this phase we found that the build-phase gate for the process arm
selected the pull request to validate by pattern — *any* open request from that arm
onto the bench branch — rather than by the ticket the task belongs to.

It had already fired. On 26 August the incident ticket about the compromised
benchmark database was filed **in the benchmark repository**, and the process arm's
dispatcher took it as ordinary work and spent a session on it. That produced an open
pull request matching the gate's pattern. Had the gate gone green while it was open,
the harness could have merged the security fix as the result of task T9.

We retargeted the stray request so it cannot be selected, and this phase's gate asks
for the ticket number instead of matching a branch pattern. The underlying defect in
the build-phase harness is filed separately. It belongs in this document because it
is the same class as everything else here: **a rule nobody had watched execute.**

## 8. Stop rules

- Any pack whose measured distribution differs from its declared one: **stop**, do
  not start the arms. (None did, after the two fixes above.)
- Pack files found anywhere outside the gate checkout: the run is void, not logged
  and continued.
- If the repository suite is red on a baseline, the verdict conditions that depend on
  it are not achievable and the affected tasks report the third state rather than a
  verdict. Baseline suite numbers are captured before the phase for exactly this
  reason.

## 9. What is published now and what is held back

Published with this document: this protocol, all six `spec.md` files, all six
`scoring.md` files (verdict rules and declared distributions), and the control-step
numbers above.

Held back until results: the test packs, the M4 answer key, and the design notes
that reason about the fix (`notes.md`) — publishing them before the runs would put
the oracles in the open. Their hash is recorded in `WITHHELD.md`, computed over the
same files that will be released, so anyone can check afterwards that nothing moved.

-- lee
