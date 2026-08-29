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
