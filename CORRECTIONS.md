# Corrections to the published package

Corrections made after publication, in order, with what was wrong and how it was found.
Published text is not edited silently: if a number or a citation changes, it is recorded
here.

State before these corrections: commit `45de467`.

---

## 2026-08-29 — package self-audit

Found by running a citation-and-headline check over the package (`check_package.py`,
added in this pass), not by a reader and not by an outside reviewer. The check was
written because the first defect below had been sitting in the opening paragraph of the
README since publication and nothing in the package was in a position to notice it.

### C1 — the maintenance headline stated a number nothing computes

`README.md`, opening paragraph: the process arm was said to lose maintenance by
**+52%**. `REPORT-EMAINT.md` computes **+47.8%** from the paired totals ($8.61 against
$12.72), and the string "52" appears in neither the report nor `analyze_emaint.py`. The
figure had no source in the package.

**Corrected to +47.8%.** Direction of the error is worth stating plainly: it *overstated*
the penalty against the arm this package was built to test, so it did not flatter the
result. It was wrong all the same, and a headline that no computation reproduces is the
same defect whichever way it leans.

### C2 — two documents were cited by name and had never been written

- `REPORT-E2.md` (twice) cited `e2/AMENDMENTS-E2.md` for the calibration amendments.
  No such file was ever written; the amendments are in `LOGBOOK.md`. **Citations now
  point to `LOGBOOK.md`.**
- `README.md` cited `emaint/WITHHELD.md`, and `emaint/PROTOCOL.md` cited it twice more
  as the record of the withheld material's hash. It did not exist. See C3.

### C3 — a missing verification artifact, not a missing file

`emaint/WITHHELD.md` was not a broken link. It was the artifact the maintenance
protocol offered as the reader's means of checking that the withheld packs and answer
key had not moved between pre-registration and results — and it was never produced. The
withheld material was also never released, though the protocol said it would be released
with the results.

**`emaint/WITHHELD.md` now exists and states this**, including what cannot be determined
after the fact and why releasing the files today would not restore the guarantee. The
maintenance phase's hidden half is unverifiable, and the package now says so where a
reader will look for it rather than leaving a dead link.

This is the correction that matters most in this pass. The other three are accuracy; this
one is an evidentiary claim the package could not support.

### C4 — a run journal cited under a name it never had

`data/journal-p1.jsonl` was cited in `LOGBOOK.md`, `REPORT.md` and
`frozen/AMENDMENTS.md`, and once as `journal-p1.jsonl` in `data/README.md`. The file is
`data/journal/p1.jsonl` and has been there all along. **Paths corrected.** Nothing was
missing; three documents simply pointed at a name that was never used.

`frozen/AMENDMENTS.md` is edited here despite living under `frozen/`. It is not covered
by `frozen/MANIFEST.sha256` (51 entries, none of them this file), so the edit does not
disturb hash verification of the frozen packs. No file that the manifest covers was
touched.

### What is now checked automatically

`check_package.py` fails the package when a markdown link or a package-rooted path does
not resolve, when a named verification artifact (manifest or withheld-accounting) is
absent, or when a cost figure in the README disagrees with the paired total its report
computes. It deliberately does not resolve bare filenames inside task specs: those name
files in the repository under test, and flagging them buried the real findings under
eighty false ones on the first run.

Three of the four corrections above would have been caught by it. C3 is caught by the
artifact check specifically, which exists because a missing hash record reads exactly
like a typo and is not one.

---

## 2026-08-29 (second pass) — what the package said it had removed, and had not

State before this pass: commit `3434bb0`.

Found while verifying the push above, by running the package's own leak scrubber
(`gen/audit_scan.py`) — which had been in the tree, and firing, since publication. The
check added in the first pass reported `clean` over the same tree, because it ran neither
the scrubber nor the manifests. A gate that does not run the checks the package already
owns is not a gate.

### C5 — the host name was declared scrubbed and was not

`SCRUB-REPORT.json` → `layers[0]` says "the host name replaced with a marker", and
`data/README.md` said the `host` field was "replaced with `[scrubbed:host]`". Neither was
true of the published bytes: **130 records in 80 files** carried the run host's real short
name, and no marker was ever written. The field-count table alongside those claims says 42
files, which is not the number of files that carry the field.

**The value is now the marker `run-host` in every record that has the field.** The key is
kept, line counts and key sets are unchanged, and no numeric, timestamp, verdict or gate
field was touched.

### C6 — internal names in free text the recovery had re-fetched untranslated

The 2026-08-28 recovery re-fetched records and archive READMEs with their original
operator-language wording, which the lost copy had carried in English. That wording named
internal systems, an unrelated production agent of the operator's, and internal ticket
numbers. Rewritten in English, with internal names replaced by what they are: five `notes`
values, all **219** `nie_umiem_zmierzyc[].powod` values, one journal repository path, four
archive READMEs, and the two E2 documents — now `e2/RUNNER-NOTES.md` and
`e2/SYMMETRY-E2.md`.

`data/README.md` had already claimed the `powod` values were rewritten in English. They
were not, until this pass. That field is the package's third state — the place a record
says *why* a number could not be measured — so leaving it unreadable to an English reader
defeated the point of having it.

### C7 — the scan fired, and nothing could read it

`gen/audit_scan.py` had the host name and the rest on its internal-term list and reported
them on every run. Its `internal` section held **110 entries**, almost all of them the package's own
vocabulary matched as substrings — `prot` inside "protocol", `lore` inside "explore",
`bakeoff` in the project's own name. The four lines that mattered scrolled past inside a
hundred that did not.

Worse, that list was itself published: about fifty internal names, including client names,
sitting in a public file as the price of running the check. **The list is no longer in the
scanner.** It is read from an unpublished file; matching is word-bounded; and when the list
is absent the scan reports `NOT RUN` and exits 2 rather than reporting nothing found. The
reader-runnable passes — operator-language, absolute paths, secret shapes — are unchanged
and still in the published file.

### C8 — the accounting fields were present by name and empty in substance

- `known_residue` held `{"note": "(recovered) see RECOVERY-NOTE.md"}`, and
  `RECOVERY-NOTE.md` says nothing about residue. **It is now computed** from the published
  bytes and states what remains, including what this correction did not fix.
- `agreement_with_the_run_host_check` read "The run-host check flagged **0** files, all
  under frozen/. This check flags the same **18**." One number was computed from a list the
  recovery had returned empty; the other was typed. **The generator no longer claims an
  agreement it cannot compute**, and says the run-host list did not survive.
- `verified_against_source` asserted that no run record had been edited. That was true when
  written and is not true now. **Restated**, with what changed and what still holds.

### C9 — a second manifest with no accounting page

`e2/MANIFEST-E2.sha256` hash-commits three files; one of them, `codex_agent.py`, is not
published. A reader running `shasum -c` got `FAILED open or read` and had nothing to read
about it. This is the same defect as C3, one experiment over. **`e2/WITHHELD.md` now
exists**, names the file, states why it is withheld and carries the hash it must match.

The manifest also carried five lines of prose in the operator's language. `shasum -c` skips
anything it cannot parse **without a word of complaint**, so that text was invisible to the
very command the documents tell the reader to run. The comments are now in English and
point at `e2/WITHHELD.md`; the three hash lines are byte-identical and still verify.

### What is now checked automatically

`check_package.py` additionally: verifies every line of both manifests and requires that
anything which does not verify be named — literally or by a pattern — in that manifest's
accounting page; reports any manifest line that `shasum` would silently skip; parses every
line of every published record file; and runs `gen/audit_scan.py`, failing on a secret shape
or an internal name that is not in a written, reasoned allowlist, and reporting the
`NOT RUN` state as a third outcome rather than as a pass — under its own exit code (2), so
that a reader's clone, which cannot run that one pass, does not read as a defective package.

Every defect in this pass would have been caught by it. Ten mutations were tested; each is
caught and the clean tree exits 0. One of them found a hole in the first version of the
manifest rule: an accounting page that merely *named* a file also excused a real hash
failure on it, so a changed file now needs a written decision rather than a mention.

### What this pass did not do

Git history is not rewritten. Commits before this one still carry the host name and the
untranslated notes, and the term list is still in the history of `gen/audit_scan.py`. That
was a deliberate choice: the run records are the evidence this package exists to publish,
and rewriting their history to chase bytes that have already been public costs more than it
buys. It is written here rather than left to be discovered.
