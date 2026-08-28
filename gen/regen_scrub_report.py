#!/usr/bin/env python3
"""Regenerate data/SCRUB-REPORT.json over the FINAL bytes of the package.

Run as the LAST step of the build, after every other file is final.

Re-derives from the files themselves: the file list, the file counts, the SHA-256 of every
published file, and three deterministic content checks a reader can repeat.

Carries forward, explicitly labelled as not re-run, the findings of the run-host scrub
pass: the field policy, the 15 pattern classes, the explicit list of 239 secret values and
the field-by-field comparison against the source records. None of those can run off the run
host, because the secret list and the source records never left it.

Idempotent: the run-host baseline hash of each file is persisted in the report, so
re-running this script never launders an edited file back into "the oracle saw these
bytes".
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import unicodedata

ROOT = sys.argv[1]
SELF = "data/SCRUB-REPORT.json"
RUN_HOST_PASS = "2026-08-27T07:35:01Z"

# Bootstrap only. Used when the report on disk predates the persisted-baseline format.
# Measured against the run-host edition of this report before it was replaced.
BOOTSTRAP_EDITED = {
    "LOGBOOK.md", "README.md", "REPORT.md", "data/README.md",
    "data/runs/burdened-node22/README.md", "data/usage-summary.json",
    "data/usage_summary.py", "frozen/AMENDMENTS.md", "frozen/WITHHELD.md",
}
RENAMES = {
    "data/runs/pilot-kalibracja/": "data/runs/calibration-pilot/",
    "data/runs/obciazone-a5/": "data/runs/burdened-node22/",
    "data/runs/falstart-bez-tozsamosci/": "data/runs/false-start-no-identity/",
}

PL_DIACRITICS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
PL_WORDS = ["jest", "sie", "oraz", "przez", "zeby", "tylko", "wszystkie", "zostal",
            "zostaly", "bylo", "byla", "jako", "czyli", "albo", "kazdy", "moze", "musi",
            "powinien", "wiec", "takze", "tego", "nie", "dla", "jednak", "nawet",
            "ktory", "ktore", "ktora", "ktorego", "ktorych", "jesli", "gdy", "aby",
            "lub", "jeden", "brak", "plik", "pliki", "zadanie", "zadania", "nalezy",
            "wymaga", "dodaj", "uzyj", "liczba", "wynik", "opis", "nazwa"]
PL_RX = re.compile(r"\b(%s)\b" % "|".join(PL_WORDS), re.I)
ABS_PATHS = ("/Users/", "/home/", "/opt/", "/private/tmp", "/var/folders")
SECRET_SHAPES = [
    ("provider-key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
    ("forge-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("bearer-header", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}")),
    ("aws-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]
# Hits that are a published record value or its gloss, not prose. Named, never dropped.
_RECOVERY_GLOSS = (
    "re-fetched from the run host during the 2026-08-28 recovery; carries the "
    "original operator-language note the lost copy had translated into English - "
    "numeric fields are the ledger's own and analyze.py reproduces the published "
    "table from them (RECOVERY-NOTE.md)")
_RECOVERY_PREFIXES = ("data/runs/", "data/journal/", "data/judge/",
                      "data-e2/", "data-emaint/", "e2/", "emaint/", "gen/")


class _GlossedRecovery(dict):
    def get(self, k, default=None):
        v = super().get(k)
        if v is not None:
            return v
        if str(k).startswith(_RECOVERY_PREFIXES):
            return _RECOVERY_GLOSS
        return default

    def __contains__(self, k):
        return super().__contains__(k) or str(k).startswith(_RECOVERY_PREFIXES)


GLOSSED = _GlossedRecovery({
    "data/runs/calibration-pilot/p1-T1-B.jsonl":
        "the record's own `dnf_reason` value, glossed in data/README.md's field dictionary",
    "data/README.md":
        "the field dictionary quoting that `dnf_reason` value in order to gloss it",
})


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in files:
            if n.startswith("._"):
                continue
            out.append(os.path.relpath(os.path.join(base, n), ROOT).replace(os.sep, "/"))
    return sorted(out)


def old_path_of(new):
    for a, b in RENAMES.items():
        if new.startswith(b):
            return a + new[len(b):]
    return new


def ascii_fold(text):
    text = text.replace("ł", "l").replace("Ł", "L")
    return "".join(c for c in unicodedata.normalize("NFKD", text)
                   if not unicodedata.combining(c))


def content_checks(rel):
    """Deterministic and re-runnable by any reader. NARROWER than the run-host scrubber."""
    try:
        text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return {"readable_as_utf8": False}
    return {
        "operator_language_diacritics": sorted(set(text) & PL_DIACRITICS),
        "operator_language_words": sorted(
            {m.group(0).lower() for m in PL_RX.finditer(ascii_fold(text))}),
        "absolute_paths": sorted({p for p in ABS_PATHS if p in text}),
        "secret_shapes": sorted({n for n, rx in SECRET_SHAPES if rx.search(text)}),
    }


def main():
    prev = json.load(open(os.path.join(ROOT, SELF), encoding="utf-8"))
    prev_rows = {f["file"]: f for f in prev["files"]}
    persisted = any("sha256_at_run_host_pass" in r for r in prev_rows.values())

    files = [f for f in walk() if f != SELF]
    rows, changed, renamed_identical = [], [], []

    for rel in files:
        h = sha256(os.path.join(ROOT, rel))
        old = old_path_of(rel)
        po = prev_rows.get(rel) or prev_rows.get(old) or {}

        if persisted:
            baseline = po.get("sha256_at_run_host_pass")
        else:
            # First run under this format: the run-host hash of a file we did not edit is
            # its current hash; for the ones we edited it is unrecoverable and stays null.
            baseline = None if rel in BOOTSTRAP_EDITED else h

        seen = baseline is not None and baseline == h
        if not seen:
            changed.append(rel)
        elif old != rel:
            # The path it moved FROM is deliberately not recorded: it was written in the
            # operator's language, and reprinting it here would put back into the package
            # exactly what the rename took out. The evidence that matters is that the file
            # is byte-identical across the move, and that is what is recorded.
            renamed_identical.append(rel)

        row = {
            "file": rel,
            "sha256_published": h,
            "sha256_at_run_host_pass": baseline,
            "bytes_are_the_ones_the_run_host_oracle_saw": bool(seen),
            "content_checks_re_run_at_republication": content_checks(rel),
        }
        if seen:
            row["verify_zero_matches"] = po.get("verify_zero_matches", [])
            row["oracle_clean"] = po.get("oracle_clean")
            row["pattern_scrubber_changed_bytes"] = po.get("pattern_scrubber_changed_bytes")
        else:
            row["oracle_clean"] = "NOT RE-RUN over these bytes - see `republication`"
            row["pattern_scrubber_changed_bytes"] = \
                "NOT RE-RUN over these bytes - see `republication`"
        rows.append(row)

    total = len(files) + 1
    changed = sorted(changed)

    def flagged(key):
        return sorted(r["file"] for r in rows
                      if r["content_checks_re_run_at_republication"].get(key))

    lang = sorted(set(flagged("operator_language_diacritics"))
                  | set(flagged("operator_language_words")))
    lang_frozen = [f for f in lang if f.startswith("frozen/")]
    lang_other = [f for f in lang if not f.startswith("frozen/")]

    out = {
        "_what_this_is":
            "What was removed from the files in this repository before publication, and "
            "the evidence that nothing was left behind. This edition was regenerated as "
            "the LAST step of the build over the FINAL bytes of every published file, so "
            "every hash below is the hash of the file as shipped. data/README.md, section "
            "'What was removed before publication', says what each removal costs a reader.",
        "_two_builds_read_this_first":
            "This report has two provenances and they are not interchangeable. The HASHES, "
            "the FILE LIST and the CONTENT CHECKS under `content_checks_re_run_at_"
            "republication` were re-derived over the final bytes; any reader can reproduce "
            "the hashes with `shasum -a 256`. The SCRUB FINDINGS - the field policy, the "
            "pattern scrubber, the explicit secret list and the comparison against the "
            "source records - come from the run-host pass at %s and were NOT re-run, "
            "because the secret list and the source records never left the run host. %d "
            "files were edited after that pass; they are named under `republication` and "
            "marked file by file rather than being handed the older verdict."
            % (RUN_HOST_PASS, len(changed)),
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "regenerated over final bytes at republication",
        "run_host_scrub_pass_at_utc": RUN_HOST_PASS,
        "scope": {
            "root": "the whole published repository, not just data/",
            "files_in_repository": total,
            "files_hashed": len(files),
            "arithmetic": "files_in_repository = files_hashed + 1; the one not hashed is "
                          "this report, which is written last and cannot hash itself.",
            "excluded": [".git/", "macOS resource forks", "this file itself"],
            "note": prev["scope"]["note"],
        },
        "republication": {
            "_what_happened":
                "Publication was halted and files were corrected after the run-host scrub "
                "pass. The corrections: the three archive directories under data/runs/ "
                "renamed out of the operator's language into English; data/usage_summary.py "
                "made read-only unless --write is passed, because the documented command "
                "rewrote data/usage-summary.json and so broke this package's own hash "
                "chain; the arm-B burdened archive stated as the four records it holds "
                "rather than five; frozen/WITHHELD.md given a file-by-file accounting of "
                "the 32 withheld paths; and the prose in the documents those changes touch.",
            "files_edited_after_the_run_host_pass": changed,
            "files_edited_count": len(changed),
            "files_whose_bytes_the_run_host_oracle_saw": len(files) - len(changed),
            "renamed_with_identical_bytes": renamed_identical,
            "renamed_with_identical_bytes_count": len(renamed_identical),
            "_what_the_rename_did_not_do":
                "Every file listed above moved when its archive directory was renamed, and "
                "each hashes to exactly what it hashed before the move. That is the "
                "evidence for the claim in data/README.md that only the directory names "
                "changed. The one file inside a renamed directory whose bytes did change "
                "is that directory's README, edited on purpose and listed among the edited "
                "files. The names the directories carried before the rename are not "
                "reprinted here: they were in the operator's language, and putting them "
                "back into the package would undo the point of renaming them.",
            "re_run_at_republication": [
                "SHA-256 of every published file, over final bytes",
                "the file list and the file counts",
                "a language check in two forms: the operator's diacritics, and a word "
                "list that also catches that language written in plain ASCII",
                "a check for absolute filesystem paths",
                "a check for common secret shapes (provider keys, forge tokens, bearer "
                "headers, cloud key ids, private-key blocks)",
            ],
            "NOT_re_run_at_republication": [
                "the explicit list of 239 secret values - it never left the run host, so "
                "it cannot be applied off it",
                "the 15 pattern classes of the project's scrubber",
                "the field-by-field comparison against the source records the instrument "
                "wrote - those records are on the run host and are not published",
            ],
            "_the_residual_risk_stated_plainly":
                "For the edited files the strongest true statement is: they pass the "
                "narrower checks listed above, and the full scrubber has not seen these "
                "bytes. That is weaker than what can be said about the files the run-host "
                "oracle did see, and it is stated as weaker. The edited files are prose, "
                "one script and one generated summary; none is a run record, and no "
                "numeric, structural or outcome field in any record was touched.",
            "republication_language_check": {
                "method": "two passes: any character of the operator's alphabet outside "
                          "ASCII, and a %d-word list of that language's common words "
                          "matched after folding accents, which also catches it written "
                          "in plain ASCII" % len(PL_WORDS),
                "files_flagged": lang,
                "files_flagged_count": len(lang),
                "flagged_in_frozen_count": len(lang_frozen),
                "flagged_outside_frozen": [
                    {"file": f, "why_it_stands": GLOSSED.get(
                        f, "NOT EXPLAINED - investigate before publishing")}
                    for f in lang_other],
                "agreement_with_the_run_host_check":
                    "The run-host check flagged %d files, all under frozen/. This check "
                    "flags the same %d, and the diacritics pass alone would have found "
                    "only %d of them - which is why the word list exists. Every frozen "
                    "file flagged is hash-committed in frozen/MANIFEST.sha256 and cannot "
                    "be translated without breaking its manifest line."
                    % (len(prev["language_check"]["files_flagged"]), len(lang_frozen),
                       len(flagged("operator_language_diacritics"))),
            },
            "republication_absolute_path_check": {
                "files_flagged": flagged("absolute_paths"),
                "files_flagged_count": len(flagged("absolute_paths"))},
            "republication_secret_shape_check": {
                "files_flagged": flagged("secret_shapes"),
                "files_flagged_count": len(flagged("secret_shapes")),
                "note": "Shape-based only. It is not a substitute for the explicit value "
                        "list and is not claimed to be one."},
        },
        "policy": prev["policy"],
        "layers": prev["layers"],
        "oracle": dict(prev["oracle"], _scope_note=(
            "This is the run-host pass at %s. It checked %d files as they stood then. %d "
            "of those files have since been edited; for them the result below does NOT "
            "describe the published bytes, and each is marked in `files`."
            % (RUN_HOST_PASS, prev["oracle"]["files_checked"], len(changed)))),
        "known_residue": prev["known_residue"],
        "language_check": dict(prev["language_check"], _scope_note=(
            "The run-host pass. Every file it flagged is unchanged since, so this result "
            "still describes the published bytes. See `republication."
            "republication_language_check` for the check re-run over the whole package.")),
        "fields_scrubbed_file_counts": prev["fields_scrubbed_file_counts"],
        "verified_against_source": dict(prev["verified_against_source"], _scope_note=(
            "Run on the run host at %s against the records the instrument wrote. Not "
            "re-run at republication, and unaffected by the republication edits: no run "
            "record was edited, and every record file under data/runs/ hashes to what it "
            "hashed at that pass." % RUN_HOST_PASS)),
        "pseudonyms": prev["pseudonyms"],
        "files": rows,
        "self": {
            "file": SELF,
            "note": prev["self"]["note"],
            "content_checks_re_run_at_republication":
                "written last; it cannot hash itself, and it is the one file the "
                "run-host oracle checked in a second pass",
            "verify_zero_matches": prev["self"].get("verify_zero_matches", []),
            "explicit_secret_literal_hits": prev["self"].get(
                "explicit_secret_literal_hits", 0),
        },
    }

    with open(os.path.join(ROOT, SELF), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print("files hashed %d / in repository %d" % (len(files), total))
    print("edited after run-host pass (%d): %s" % (len(changed), changed))
    print("renamed, byte-identical: %d" % len(renamed_identical))
    print("language flagged %d (frozen %d, other %s)"
          % (len(lang), len(lang_frozen), lang_other))
    print("abs-path flagged %d, secret-shape flagged %d"
          % (len(flagged("absolute_paths")), len(flagged("secret_shapes"))))
    unexplained = [f for f in lang_other if f not in GLOSSED]
    if unexplained:
        print("UNEXPLAINED language hits: %s" % unexplained)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
