# What is withheld from `e2/`, and why

`MANIFEST-E2.sha256` hash-commits **three** files. Two of them are published and verify
against their manifest lines. One is not published:

| file | published | verifies today |
|---|---|---|
| `PROTOCOL-E2.md` | yes | yes |
| `pricing-e2.json` | yes | yes |
| `codex_agent.py` | **no** | not yet — `shasum -c` reports it as missing |

Reproduce it:

```
$ cd e2 && shasum -a 256 -c MANIFEST-E2.sha256
```

Two `OK` lines and one `FAILED open or read`. Those two numbers are the whole of this page.

## `codex_agent.py`

It is the driver that runs the challenger arm: the script the run host executes to give
that arm its task, its budget and its transcript. It is hash-committed here for the same
reason the frozen packs are — so that a reader can tell afterwards that the thing which
drove the arm was fixed before the runs, not adjusted during them.

It is withheld under the second of the pre-registration's two reasons for withholding: the
agent side's internals stay private. The first reason (an arm with web access could code to
a published test) does not apply to a driver.

**This defers publication; it does not cancel it.** Its hash is
`7b774f288468c6136458ae1ee204425dbf801a3a076078ae728ddb55a2b5881a`, committed before the
E2 runs. If it is published, it must match that line.

What a reader loses meanwhile: the ability to check how the arm was driven — the prompt
assembly, the budget enforcement and the stop conditions — beyond what `PROTOCOL-E2.md`
states about them. That is weaker than reading the file. It is stated as weaker.

The E2 **runner** (`exec_e2.py`) is a different thing and is deliberately outside the
manifest altogether, as `exec_real` was in Experiment 1: it is the harness, and it changed
between attempts by design.

## Refreeze history

The manifest was re-frozen three times before the counted E2 runs. What changed, in order:

- **E2-A1** — cost imputation moved to per-request, taken from the rollout. The pilot had
  measured a bias of about +40% against the previous method.
- **E2-A2** — sandbox disabled for the challenger arm, and the error classifier changed to
  key on the event TYPE rather than on a substring of the whole event.
- **E2-A2b** — A2 was first deployed to the WRONG PATH, so pilot attempt 5 ran on the OLD
  engine. The money spent on that attempt bought nothing; it was caught by the sandbox
  policy visible in the session's metadata. A checksum comparison at both ends was added to
  the start-up procedure as a result.

## This page was late

This accounting did not exist until 2026-08-29. Between publication and that date,
`MANIFEST-E2.sha256` listed a file that was not in the tree and nothing in the package said
so — a reader running `shasum -c` got a `FAILED open or read` with no explanation to read.
The same gap existed for the maintenance phase and is recorded in `CORRECTIONS.md`; this is
the second instance of it. The check that now catches it is `check_package.py`.
