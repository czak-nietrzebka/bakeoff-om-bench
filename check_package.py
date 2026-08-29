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


def main() -> int:
    findings = check_anchors() + check_paths() + check_headlines()
    if not findings:
        print("package check: clean (%d markdown files)" % len(markdown_files()))
        return 0
    print("package check: %d finding(s)\n" % len(findings))
    for f in findings:
        print("  " + f)
    return 1


if __name__ == "__main__":
    sys.exit(main())
