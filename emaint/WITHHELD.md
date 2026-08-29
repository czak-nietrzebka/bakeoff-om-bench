# Withheld material — maintenance phase

`PROTOCOL.md` promises this file twice: that the hidden material's hash "is in
`WITHHELD.md`", and that the hash is "computed over the same files that will be released,
so anyone can check afterwards that nothing moved."

**This file did not exist when the maintenance results were published.** It is written
now, after the fact, and it cannot do the job it was promised for. What follows is the
accounting as it actually stands, not a reconstruction.

## What was to be withheld

Per `PROTOCOL.md` §"Held back until results": the test packs, the M4 answer key, and the
design notes reasoning about the fix (`notes.md`). Publishing them before the runs would
have put the oracles in the open — the reason for withholding is sound and is not in
question here.

## What actually happened

| promise | state, measured against this tree |
|---|---|
| hash of the withheld material recorded in `WITHHELD.md` before the runs | **not done** — no such record exists anywhere in the repository history |
| material released together with the results | **not done** — `emaint/` contains `PROTOCOL.md` and `specs/` only; no packs, no answer key, no `notes.md` |
| reader can check afterwards that nothing moved | **impossible** — with no pre-registered hash, there is nothing to check a release against, and no release to check |

## What this costs the reader

The maintenance phase's protocol, specs, scoring rules, raw run records and analysis
script are all published, and its cost table recomputes from `data-emaint/runs/` with
`analyze_emaint.py`. That part stands on its own.

What does **not** stand is the integrity claim about the hidden half. A reader cannot
verify that the packs and the M4 answer key used in the runs were the ones fixed before
the runs, because the artifact that was supposed to make that checkable was never
produced. That is a real weakness in this phase's pre-registration, and the honest
statement of the phase's evidentiary standing has to carry it:

> The maintenance phase is pre-registered in its design and open in its data. Its hidden
> material is **unverifiable after the fact** — no hash was recorded, so the "nothing
> moved" guarantee has nothing behind it.

## What we cannot determine

Whether a hash was computed at freeze time and simply never written into a file is
**unknown**. There is no record either way. We are not claiming the material moved; we
are stating that the package gives no means to establish that it did not. Absence of a
check is not evidence of a failed check — but it is not evidence of a passed one either,
and the protocol offered it as if it were.

## What would repair it

Releasing the withheld files now would allow scoring to be re-derived, but it would
**not** restore the pre-registration guarantee: a hash computed today proves only that
today's files match today's files. The guarantee is not recoverable for this phase. It is
recoverable for future phases only by computing and publishing the hash *before* the runs,
which is what the protocol already said and what was not done.

*Recorded 2026-08-29 during a package self-audit, together with the other corrections in
[`CORRECTIONS.md`](../CORRECTIONS.md).*
