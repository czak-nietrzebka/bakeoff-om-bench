#!/usr/bin/env python3
"""Independent grep pass over the publication package. Wider than the regen check."""
import os, re, sys, unicodedata, collections

ROOT = sys.argv[1]

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

INTERNAL = ["czak-lee", "czaklee", "kwit", "kwity", "krowa", "krowy", "azymut", "bolec",
            "whip", "meeseeks", "korvo", "mulder", "forgejo", "hetzner", "itm8",
            "czak-mesh", "czak-v2", "wafel", "wafle", "cukierek", "landrynka", "kutas",
            "lore", "prot", "czlek", "czleki", "mdc", "renfield", "nietrzebka",
            "wellysa", "credipass", "optimo", "entaro", "medak", "dorfl", "borewicz",
            "czakins", "sdlc", "openbao", "sierota", "obstawka", "zagroda",
            "piotr", "czesiek", "cze@", "telegram", "orchestrator", "channel_gateway",
            "task-queue", "meta_handler", "bakeoff", "ext-workspaces", "gex44",
            "claude-pool", "protocol_runtime", "_TOOL_IMPLS", "czak_"]
INT_RX = re.compile(r"(%s)" % "|".join(re.escape(w) for w in INTERNAL), re.I)


def fold(t):
    t = t.replace("ł", "l").replace("Ł", "L")
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def files():
    for base, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in sorted(fs):
            if n.startswith("._"):
                continue
            yield os.path.relpath(os.path.join(base, n), ROOT).replace(os.sep, "/")


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
    for m in INT_RX.finditer(t):
        agg["internal"][rel][m.group(0).lower()] += 1

for cls in sorted(agg):
    print("\n########## %s ##########" % cls)
    for rel in sorted(agg[cls]):
        print("  %-55s %s" % (rel, dict(agg[cls][rel].most_common(12))))