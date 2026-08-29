#!/usr/bin/env python3
"""Package self-check: every cited path must exist, every headline number must match its report.

Two failures shipped in this package and neither was caught by anything:

  1. The README headline said the maintenance phase cost "+52%". No computation in the
     package produces that number; REPORT-EMAINT.md's paired total is +47.8%.
  2. Three documents were cited by name that were never written, one of them the hash
     record that lets a reader verify the withheld material did not move.

Both are the same class: prose asserting something the tree does not support. A reader
cannot tell the difference between a citation to a file and a citation to an intention.

    python3 check_package.py          # exit 0 = clean, 1 = findings

Stdlib only. Run it before publishing anything from this repository.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent

# Markdown links to relative paths: [text](path) — skip URLs and pure anchors.
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Backticked paths that look like files in this tree: `dir/file.ext`
INLINE_PATH = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|py|json|jsonl|sha256))`")

# Task specs describe the SUBJECT repository under test, so `en.json`, `AGENTS.md` and
# `package.json` inside them are not this package's files and must not be flagged. An
# inline path is only this package's business when it is rooted in one of our own
# directories; a markdown link is always checked, because a link promises navigation.
OUR_DIRS = ("frozen/", "e2/", "emaint/", "data/", "data-e2/", "data-emaint/")

# Bare filenames are deliberately NOT resolved: `AGENTS.md`, `package.json`, `spec.md`
# and `notes.md` in these documents mostly name files in the subject repository or in
# withheld packs, and guessing which is which produced more noise than findings.
#
# The case that matters is handled explicitly instead. These are the artifacts the
# protocols offer as the reader's means of VERIFICATION — the hash records and manifests
# that make "nothing moved between pre-registration and results" checkable. A missing one
# is not a broken link; it is a promise of auditability with nothing behind it.
INTEGRITY_ANCHORS = [
    ("frozen/MANIFEST.sha256", "Experiment 1 frozen-pack manifest"),
    ("frozen/WITHHELD.md", "Experiment 1 withheld-material accounting"),
    ("e2/MANIFEST-E2.sha256", "Experiment 2 frozen-pack manifest"),
    ("emaint/WITHHELD.md", "maintenance withheld-material accounting (promised in emaint/PROTOCOL.md)"),
]


def is_ours(target: str) -> bool:
    return target.startswith(OUR_DIRS)


def check_anchors() -> list[str]:
    """Every verification artifact the protocols promise must actually be in the tree."""
    return [
        "%s missing — %s; the package promises this as a way to check it, so its absence "
        "removes the check, not just a file" % (path, what)
        for path, what in INTEGRITY_ANCHORS
        if not (ROOT / path).exists()
    ]


# The corrections log names paths that were wrong and no longer exist — that is its job.
# Checking it would force it to describe a dead citation without writing it down.
EXEMPT = {"CORRECTIONS.md"}


def markdown_files() -> list[pathlib.Path]:
    return sorted(
        p for p in ROOT.rglob("*.md")
        if ".git" not in p.parts and p.relative_to(ROOT).as_posix() not in EXEMPT
    )


def check_paths() -> list[str]:
    """Every cited relative path resolves to something in the tree."""
    findings = []
    for md in markdown_files():
        text = md.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            cited = [(m, True) for m in LINK.findall(line)]
            cited += [(m, False) for m in INLINE_PATH.findall(line)]
            for target, is_link in cited:
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                clean = target.split("#", 1)[0].rstrip("/")
                if not clean:
                    continue
                if not is_link and not is_ours(clean):
                    continue  # a task spec talking about the repository under test
                # Resolve relative to the citing file first, then to the repo root.
                if (md.parent / clean).exists() or (ROOT / clean).exists():
                    continue
                f = "%s:%d cites `%s` — not in the tree" % (md.relative_to(ROOT), lineno, target)
                if f not in findings:  # same path in a link's text and its href
                    findings.append(f)
    return findings


def paired_total(report: pathlib.Path) -> str | None:
    """The percentage in a report's `paired total` row — the number the headline must match."""
    if not report.exists():
        return None
    for line in report.read_text(encoding="utf-8", errors="replace").splitlines():
        if "paired total" in line.lower():
            pcts = re.findall(r"([+-]?\d+\.\d+)%", line)
            if pcts:
                return pcts[-1]
    return None


def check_headlines() -> list[str]:
    """A cost figure in the README must be the one its report computes.

    Matched by phase keyword on the same line, so a reworded headline still gets checked.
    """
    findings = []
    readme = ROOT / "README.md"
    if not readme.exists():
        return ["README.md missing"]
    phases = [("maintenance", ROOT / "REPORT-EMAINT.md")]
    for keyword, report in phases:
        truth = paired_total(report)
        if truth is None:
            findings.append("no `paired total` row in %s — cannot check the headline" % report.name)
            continue
        for lineno, line in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1):
            if keyword not in line.lower():
                continue
            for claimed in re.findall(r"\(([+-]?\d+(?:\.\d+)?)%\)", line):
                if abs(float(claimed) - float(truth)) > 0.5:
                    findings.append(
                        "README.md:%d says %s%% for %s; %s computes %s%%"
                        % (lineno, claimed, keyword, report.name, truth)
                    )
    return findings


# Manifests, and the accounting file that has to explain anything they do not match.
# `shasum -c` reports three outcomes and the accounting must survive all three: OK,
# FAILED (the bytes differ) and "FAILED open or read" (the file is not here). The third
# is the one prose forgets, because a missing file produces no diff to look at.
MANIFESTS = [
    ("frozen/MANIFEST.sha256", "frozen/WITHHELD.md"),
    ("e2/MANIFEST-E2.sha256", "e2/WITHHELD.md"),
]

HASH_LINE = re.compile(r"^([0-9a-f]{64})\s+\*?(.+)$")
# Backticked tokens in an accounting file. A group of files may be accounted for by a
# pattern (`scenario/T*/pack*/**`) rather than by 31 literal lines, and that is the better
# document; the check honours the pattern instead of forcing the prose into a file list.
BACKTICKED = re.compile(r"`([^`\n]+)`")


def accounted_for(name: str, acct_text: str) -> bool:
    if name in acct_text:
        return True
    import fnmatch
    for token in BACKTICKED.findall(acct_text):
        if "*" in token and fnmatch.fnmatch(name, token.replace("**", "*")):
            return True
    return False


# A file whose bytes DIFFER from its manifest line is corruption unless someone decided
# otherwise, so the accounting page does not get to excuse it: a page that names a file at
# all would then absorb a real hash failure in silence (this was caught by mutation, after
# the first version of this check did exactly that). Missing files are the withheld page's
# business; changed bytes are a decision, and a decision belongs where it can be read.
DECLARED_MISMATCH = {
    ("frozen/MANIFEST.sha256", "symmetry-table.md"):
        "published translated and redacted; the file opens by saying so, names the frozen "
        "original's hash and lists cell by cell what was removed (frozen/WITHHELD.md)",
}


def check_manifests() -> list[str]:
    """Every manifest line that does not verify must be named in its accounting file.

    Counts are not enough and are not checked here: a count can stay right while the paths
    behind it change. What is checked is the property the reader actually needs — that no
    file silently fails and none silently vanishes.

    Also reported: manifest lines that are neither a hash line nor a comment. `shasum -c`
    skips anything it cannot parse WITHOUT a word of complaint, so prose written into a
    manifest is invisible to the very command the documents tell the reader to run.

    Where this check is weak, stated rather than left to be found: the excuse for a MISSING
    file is a substring or glob match against the accounting page, so a page that mentions
    a *published* file would also excuse that file's disappearance. What covers that case
    is `check_paths`, which fails on any document citing a path that is not in the tree.
    """
    import hashlib

    findings = []
    for manifest_rel, accounting_rel in MANIFESTS:
        manifest = ROOT / manifest_rel
        if not manifest.exists():
            findings.append("%s missing — nothing to verify against" % manifest_rel)
            continue
        accounting = ROOT / accounting_rel
        acct_text = (accounting.read_text(encoding="utf-8", errors="replace")
                     if accounting.exists() else "")
        unexplained = []
        for lineno, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
            line = line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            m = HASH_LINE.match(line)
            if not m:
                findings.append(
                    "%s:%d is neither a hash line nor a comment — `shasum -c` skips it "
                    "silently, so it is invisible to the check this file exists for"
                    % (manifest_rel, lineno))
                continue
            want, name = m.group(1), m.group(2).strip()
            # `shasum` writes the path as it was given to it, so most lines here carry a
            # leading "./". The accounting files name the paths without it.
            name = name[2:] if name.startswith("./") else name
            target = manifest.parent / name
            if not target.exists():
                # Missing: the accounting page may explain it, by name or by pattern.
                if not accounted_for(name, acct_text):
                    unexplained.append(
                        "%s is not in the tree and is not named in %s"
                        % (name, accounting_rel))
            elif hashlib.sha256(target.read_bytes()).hexdigest() != want:
                # Present but different: only a written decision excuses this.
                if (manifest_rel, name) not in DECLARED_MISMATCH:
                    unexplained.append(
                        "%s does not match its manifest line in %s and is not a declared "
                        "redaction" % (name, manifest_rel))
        if unexplained and not accounting.exists():
            findings.append(
                "%s missing — %d file(s) in %s do not verify and nothing accounts for "
                "them: %s" % (accounting_rel, len(unexplained), manifest_rel,
                              "; ".join(sorted(unexplained))))
        else:
            findings += sorted(unexplained)
    return findings


# Occurrences of an internal-identity term that are legitimate, each with its reason.
# An allowlist entry is a claim, so it is written where a reader can weigh it.
SCRUB_ALLOW = {
    ("README.md", "czak-nietrzebka"): "the GitHub account that owns this repository",
    ("check_package.py", "czak-nietrzebka"): "this allowlist naming the line above",
    ("gen/regen_scrub_report.py", "czak-nietrzebka"):
        "the same allowance, restated in data/SCRUB-REPORT.json's known_residue",
    ("data/SCRUB-REPORT.json", "czak-nietrzebka"):
        "that generator's output, where the allowance is declared to the reader",
}


def check_scrub() -> list[str]:
    """Run the package's own scrubber and read its verdict, including 'could not run'.

    The scrubber was in the tree before this check existed, and it was already firing on
    the right lines. Nothing consumed it, so nothing acted on it. A check nobody runs is
    prose with an exit code.
    """
    import json
    import subprocess

    scanner = ROOT / "gen" / "audit_scan.py"
    if not scanner.exists():
        return ["gen/audit_scan.py missing — the leak scan cannot run"]
    proc = subprocess.run([sys.executable, str(scanner), str(ROOT), "--json"],
                          capture_output=True, text=True)
    if proc.returncode not in (0, 1, 2):
        return ["gen/audit_scan.py failed (exit %d): %s"
                % (proc.returncode, proc.stderr.strip()[:200])]
    try:
        report = json.loads(proc.stdout)
    except ValueError:
        return ["gen/audit_scan.py produced output this check could not read"]

    findings = []
    if proc.returncode == 2:
        findings.append(
            "internal-identity scan NOT RUN — %s. This is a third state, not a pass."
            % report.get("_internal_pass", "reason not reported"))
    for rel, terms in sorted(report.get("internal", {}).items()):
        for term, count in sorted(terms.items()):
            if (rel, term) in SCRUB_ALLOW:
                continue
            findings.append("%s carries the internal name `%s` (%dx)" % (rel, term, count))
    for cls in sorted(c for c in report if c.startswith("secret:")):
        for rel in sorted(report[cls]):
            findings.append("%s matches %s" % (rel, cls))
    return findings


def check_records() -> list[str]:
    """Every line of every published record file still parses as JSON.

    This is the failure mode of editing records in bulk — a value rewritten by hand or by
    regex leaves a file that looks fine in a diff and is no longer readable by anything.
    The records are the evidence; a record nothing can parse is not evidence.
    """
    import json

    findings = []
    for path in sorted(ROOT.rglob("*.jsonl")):
        if ".git" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except ValueError as exc:
                findings.append("%s:%d does not parse as JSON — %s"
                                % (path.relative_to(ROOT), lineno, exc))
    return findings


def main() -> int:
    findings = (check_anchors() + check_paths() + check_headlines()
                + check_manifests() + check_records() + check_scrub())
    if not findings:
        print("package check: clean (%d markdown files)" % len(markdown_files()))
        return 0
    print("package check: %d finding(s)\n" % len(findings))
    for f in findings:
        print("  " + f)
    return 1


if __name__ == "__main__":
    sys.exit(main())
