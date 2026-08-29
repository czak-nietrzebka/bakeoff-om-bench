#!/usr/bin/env python3
"""Independent grep pass over the publication package. Wider than the regen check.

    python3 gen/audit_scan.py [ROOT] [--json]

Exit 0 = no disqualifying hit, 1 = at least one secret shape or internal-identity hit,
2 = the internal-identity pass could not run (see below).

Four classes are reported. Three of them a reader can re-run and judge: operator-language
(diacritics and a folded word list), absolute filesystem paths, and secret shapes.

The fourth — internal identity: host names, agent names, ticket and client names that must
never appear in a public package — needs a list of those names, and publishing that list
would itself be the disclosure it exists to prevent. So the list is NOT in this file. It is
read from `gen/internal-terms.txt` (or $BENCH_INTERNAL_TERMS), one term per line, `#` for
comments; that file is not published.

When the term list is absent this pass reports `NOT RUN` and the exit code is 2. That is
deliberate: a check that cannot run must say so, because a silent skip is indistinguishable
from a pass, and this class of check is exactly where a silent pass does the damage.
"""
import os, re, sys, unicodedata, collections

argv = [a for a in sys.argv[1:] if not a.startswith("--")]
AS_JSON = "--json" in sys.argv[1:]
ROOT = argv[0] if argv else "."

PL_DIA = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
PL_WORDS = """jest sie oraz przez zeby tylko wszystkie zostal zostaly bylo byla jako czyli
albo kazdy moze musi powinien wiec takze tego nie dla jednak nawet ktory ktore ktora
ktorego ktorych jesli gdy aby lub jeden brak plik pliki zadanie zadania nalezy wymaga
dodaj uzyj liczba wynik opis nazwa robi robota zrobione dzialanie dziala bledy blad
sprawdz pokaz zmiana zmiany nowy nowa stary praca test testy uruchom wykonaj wersja
poprawka powod czas godzina dzien tydzien miesiac rok koniec poczatek srodek gora dol
tak owszem prosze dziekuje czesc witaj do od na za pod nad przy bez ale wiecej mniej
bardzo troche duzo malo caly cala cale kilka wiele pare jakis jakies ten ta to te ci
one ono oni my wy ja ty on ona wam nam nim nia""".split()
PL_RX = re.compile(r"\b(%s)\b" % "|".join(sorted(set(PL_WORDS), key=len, reverse=True)), re.I)

ABS = [("abs-users", re.compile(r"/Users/[A-Za-z0-9._-]+")),
       ("abs-home", re.compile(r"/home/[A-Za-z0-9._-]+")),
       ("abs-opt", re.compile(r"/opt/[A-Za-z0-9._/-]+")),
       ("abs-privtmp", re.compile(r"/private/tmp[A-Za-z0-9._/-]*")),
       ("abs-varfolders", re.compile(r"/var/folders[A-Za-z0-9._/-]*")),
       ("abs-srv", re.compile(r"/srv/[A-Za-z0-9._/-]+")),
       ("abs-root-home", re.compile(r"/root/[A-Za-z0-9._/-]+")),
       ("abs-etc", re.compile(r"/etc/[A-Za-z0-9._/-]+"))]

SECRETS = [("provider-key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
           ("oauth-token", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{10,}")),
           ("forge-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
           ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}")),
           ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
           ("privkey", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
           ("slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
           ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.")),
           ("hex40plus", re.compile(r"\b[A-Za-z0-9_\-]*(?:token|secret|passwd|password|apikey|api_key)[\"'`:= ]+[A-Za-z0-9/+_\-]{16,}", re.I)),
           ("tg-bot", re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}")),
           ("pg-url", re.compile(r"\b(?:postgres|mysql|mongodb|redis|amqp)(?:ql)?://[^\s\"'<>]+")),
           ("basic-url-cred", re.compile(r"https?://[^\s/@\"']+:[^\s/@\"']+@")),
           ]

TERMS_FILE = os.environ.get(
    "BENCH_INTERNAL_TERMS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "internal-terms.txt"))


def load_internal_terms(path):
    """The identity term list, or None when it is not in this checkout.

    None is a THIRD state and is reported as such. It is never folded into "no hits":
    the earlier edition of this scanner carried the terms inline, which both published
    them and buried the real hits among the package's own vocabulary — `bakeoff` and
    `prot` (a substring of "protocol") matched on nearly every file, so the four lines
    that mattered scrolled past inside 110 that did not.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            terms = [ln.strip() for ln in fh]
    except OSError:
        return None
    return [t for t in terms if t and not t.startswith("#")]


INTERNAL = load_internal_terms(TERMS_FILE)
# Word-bounded on purpose. The inline list this replaced matched substrings, so "explore"
# reported as `lore` and "protocol" as `prot`; the noise was most of the report.
INT_RX = re.compile(
    r"(?<![A-Za-z0-9])(%s)(?![A-Za-z0-9])" % "|".join(re.escape(w) for w in INTERNAL),
    re.I) if INTERNAL else None


def fold(t):
    t = t.replace("ł", "l").replace("Ł", "L")
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def files():
    for base, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in sorted(fs):
            if n.startswith("._"):
                continue
            p = os.path.join(base, n)
            if os.path.abspath(p) == os.path.abspath(TERMS_FILE):
                continue  # the term list is not published and must not report itself
            yield os.path.relpath(p, ROOT).replace(os.sep, "/")


agg = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for rel in files():
    p = os.path.join(ROOT, rel)
    try:
        t = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError) as e:
        print("UNREADABLE", rel, e); continue
    d = sorted(set(t) & PL_DIA)
    if d:
        agg["pl-diacritics"][rel].update(d)
    for m in PL_RX.finditer(fold(t)):
        agg["pl-words"][rel][m.group(0).lower()] += 1
    for name, rx in ABS:
        for m in rx.finditer(t):
            agg["abs-path"][rel][m.group(0)] += 1
    for name, rx in SECRETS:
        for m in rx.finditer(t):
            agg["secret:" + name][rel][m.group(0)[:24]] += 1
    if INT_RX is not None:
        for m in INT_RX.finditer(t):
            agg["internal"][rel][m.group(0).lower()] += 1

if AS_JSON:
    import json
    out = {cls: {rel: dict(c) for rel, c in files_.items()} for cls, files_ in agg.items()}
    out["_internal_pass"] = "ran" if INT_RX is not None else "NOT RUN: %s absent" % TERMS_FILE
    print(json.dumps(out, sort_keys=True, indent=2))
else:
    for cls in sorted(agg):
        print("\n########## %s ##########" % cls)
        for rel in sorted(agg[cls]):
            print("  %-55s %s" % (rel, dict(agg[cls][rel].most_common(12))))
    if INT_RX is None:
        print("\n########## internal ##########")
        print("  NOT RUN — term list absent (%s). This is not a pass." % TERMS_FILE)

if INT_RX is None:
    sys.exit(2)
sys.exit(1 if (agg.get("internal") or any(c.startswith("secret:") for c in agg)) else 0)