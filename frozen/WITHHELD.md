# What is still withheld from `frozen/`, and why

The pre-registration hash-committed **51 files** in `MANIFEST.sha256` on 2026-08-25, before
any run, and said that some of them would be withheld until the runs were done, then
published and verified against that manifest.

Experiment 1 is done. **Most of the withheld material is still not published**, and this
file says exactly what, why, and how to check it when it is released. Deciding to keep
material back is the kind of decision that is easy to make quietly and convenient to make
in one's own favour, so it is written down with its accounting.

## Accounting against the manifest

| | files | verifiable against `MANIFEST.sha256` today |
|---|---:|---|
| published, byte-identical to the frozen original | **18** | yes — all 18 match their manifest line |
| published as a declared redaction | **1** | **no**, by construction — `symmetry-table.md`, see below |
| withheld | **32** | not yet |
| **total** | **51** | |

Anyone can reproduce the first row:

```
$ cd frozen && shasum -a 256 -c MANIFEST.sha256 2>/dev/null | grep ': OK'
```

Eighteen `OK` lines, one `FAILED` for `symmetry-table.md`, and thirty-two files reported
missing. Those three numbers are the whole of this page.

## The 32 withheld files

- **31 hidden acceptance-pack test files** — `scenario/T*/pack*/**`, the tests that decide
  whether a task counts as done.
- **1 spec** — `scenario/T5/spec-faza2.md`, the text of the mid-series requirements change.

### Why they are still withheld

The pre-registration gives two reasons for withholding: an arm with web access could
otherwise code to the test, and the agent's internals stay private. Only the **first**
applies here, and the finish of Experiment 1 does not retire it:

1. **The same packs are pre-registered for use again.** The repository announces
   Experiment 2 on "identical frozen tasks and hidden packs", and the analysis report's own
   plan lists three further uses of them: re-running arm B's voided T9, repeating the pairs
   to n=3, and a separately pre-registered maintenance phase.
2. **Both arms can read the public web.** `WebSearch` and `WebFetch` are in the permission
   surface of both arms — that is in the symmetry table, and it was true of every run in
   this series. An arm that can fetch a public repository can fetch its own acceptance
   tests.
3. Therefore publishing the packs now would not be releasing evidence about a finished
   measurement; it would be **destroying the oracle of every run that is still planned**,
   including the re-run that the report says is owed. The same argument covers the T5
   requirements-change text: an arm that has read it in advance is not being surprised by
   it, and "surprise mid-series" is the thing T5 measures.

**This defers publication; it does not cancel it.** The commitment stands: when the last
run that depends on these packs is finished, all 32 files are published and every one of
them must match the manifest line committed on 2026-08-25. Until then the honest statement
is that a reader **cannot yet** check what the gate actually asserted — only that the gate
was fixed in advance and that its hashes were public before anyone ran anything.

### What a reader loses meanwhile

Everything about *what* the tests demand. You can see that a run went green, on which
iteration, and with which failing test ids on the way — those are in the published records
— but you cannot see whether a pack was lenient, or whether it happened to favour one arm's
idiom. The mitigations against that are the ones fixed before the runs: the packs were
written and hashed before either arm existed on the machine, the same pack file decides
both arms, and the gate applies it into its own checkout rather than into either arm's
workspace.

That is weaker than being able to read them. It is stated as weaker.

## The one published redaction

`symmetry-table.md` is published **translated and redacted**, so it does not hash to its
manifest line and reports `FAILED` under `shasum -c`. That is expected, and the file itself
opens by saying so, names the frozen original's hash, and lists cell by cell what was
removed. Three cells describing how the agent arm is composed internally were reduced to
what they grant and how large they are.

The alternative was to drop the file and the report's references to it. That was rejected:
the table is the only document that states which dimensions were held equal, and a
benchmark that will not show its control conditions is asking to be taken on trust in
precisely the place where it should not be.

## The pre-registration's own wording

The repository `README.md` was committed before any run and says the withheld files will be
added "after the runs". Read against this page, that sentence is **not yet fulfilled** for
32 of the 51 files. It is left standing rather than edited, because a pre-registration that
gets rewritten when it becomes inconvenient is not a pre-registration; this page is the
amendment to it.
