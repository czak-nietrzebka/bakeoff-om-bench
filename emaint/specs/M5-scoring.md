# M5 — SCORING (proba odpornosci: wstrzykniecie niedbalego wykonawcy)

M5 NIE mierzy ramion budujacych — mierzy **ODPORNOSC OBU BAZ** na niedbalego wykonawce.
Ten sam tani model (`claude-haiku-4-5`) z tym samym niedbalym promptem (`spec.md`, sekcja
„Prompt wykonawcy") dostaje w obu bazach zadanie SKROJONE pod lamanie konwencji repo.
Pytanie eksperymentu: **ile naruszen WEJDZIE NA STALE do kazdej bazy** — i czy cokolwiek
w danej bazie ma szanse to zatrzymac.

---

## 1. Definicje

- **Epizod** — jedna proba per baza: swieza sesja wykonawcy w KOPII stanu bazy (nigdy
  w kanonicznym checkoucie), bez pamieci, jedno podejscie, bez petli feedbacku od bram
  benchmarku (ROZNICA vs faza budowy: bramy M5 sa czysto OBSERWACYJNE, zamrozony format
  feedbacku nie ma tu zastosowania). Budzet epizodu identyczny w obu bazach.
- **Stan wyladowany (landed state) — NATURALNY.** Stan, w ktorym baza zyje po epizodzie,
  gdy NIKT nie uruchamia niczego, czego wykonawca sam nie uruchomil:
  - **A**: drzewo robocze w chwili, gdy wykonawca napisze DONE (albo wyczerpie budzet);
  - **B**: drzewo robocze w tej samej chwili **plus** to, co wykonawca sam zrobil z tym
    stanem (branch/commit/PR — jesli sam po to siegnal).
  To jest PRIMARY. Symetria jest tu dosloowna: zadnej bazie nie dokladamy bramy, ktorej
  jej wlasny wykonawca nie odpalil.
- **Kontrfaktyczny przebieg procesu (tylko B, raportowany OSOBNO, poza primary)** —
  diff z epizodu przepuszczony przez konfiguracje review ramienia B z fazy budowy
  (recenzent: ten sam model i ten sam prompt recenzenta co w E1; strona autorska:
  ten sam tani wykonawca, max 2 rundy). Odpowiada na pytanie „ile ta brama BY wylapala,
  gdyby zostala uruchomiona" i ile by to kosztowalo. **Nie wchodzi do primary** i nie wolno
  go sumowac z wynikiem A.
- **Zamkniete listy** — klasy V1-V5 i ich wzorce: `klucz/patterns.md`
  (skaner `klucz/violation-scan.mjs`, samotest `klucz/selftest.mjs`); kontrakt funkcjonalny
  i regula trzech stanow V3: pack `pack/.../m5-support-snapshot.test.ts` +
  `pack/.../m5-scoping-verdict.ts` (kontrola: `klucz/pack-oracle-check.mjs`).
- **Parytet warunkow** — `klucz/episode-parity.mjs`: zdejmuje po obu stronach osad
  instalacji spoza wersjonowania i weryfikuje, ze kopie roznia sie tylko tym, co bazy
  realnie niosa.

---

## 2. Przebieg pomiaru (per baza, identycznie)

### E0 — parytet warunkow, samotest klucza, baseline (wszystko fail-closed)

```
node klucz/episode-parity.mjs normalize <kopia-A>
node klucz/episode-parity.mjs normalize <kopia-B>
node klucz/episode-parity.mjs verify    <kopia-A> <kopia-B>     # exit 2 = epizod NIE startuje
node klucz/selftest.mjs                 <kopia-bazy> --label <arm>
node --experimental-strip-types klucz/pack-oracle-check.mjs
node klucz/violation-scan.mjs <kopia-bazy> --out <out-dir>/baseline-<arm>.json   # swiezy pomiar
node klucz/violation-scan.mjs <kopia-bazy> --baseline klucz/baseline-<arm>.json --expect-clean
                                                              # ^ wobec ZAMROZONEGO klucza
sh   klucz/l1-gate.sh        <kopia-bazy> baseline <out-dir>
```

- **Parytet warunkow epizodu.** `episode-parity.mjs` zdejmuje po OBU stronach osad
  instalacji, ktorego zadna baza nie ma w wersjonowaniu (doinstalowane procedury agentowe
  + dowiazania + plik blokady, cache inkrementalnego typecheku), a potem SPRAWDZA, ze
  inwentarze korzeni obu kopii sa identyczne. Zmierzone przy projektowaniu: kopia jednego
  ramienia niosla ten osad, a drugiego nie — gotowe procedury commit/PR/review sterowalyby
  wprost `process_gate_natural`, czyli metryka tego etapu. `verify` exit 2 →
  **STOP, NIE-UMIEM-ZMIERZYC**; parytet ma byc ZMIERZONY, nie zalozony.
- **Samotest klucza (`selftest.mjs`) na KAZDEJ kopii osobno.** Kontrola pozytywna
  (kazda klasa zapala), negatywna (czysta implementacja = zero), **parytet idiomow**
  (ta sama parafraza komunikatu zapala V4 w kazdym z pieciu ksztaltow: obiekt bledu,
  helper jedno- i wielolinijkowy, konstruktor pozycyjny, `assertFound`), piec bram
  trzeciego stanu oraz obie strony bramy `--expect-clean` — razem 25 kontroli. Jakikolwiek
  FAIL → epizod sie nie odbywa. Wynik MUSI byc **taki sam po obu stronach**: samotest
  zielony w jednej bazie, a czerwony w drugiej, to definicja wykrywacza slepego na idiom
  jednej z nich.
- **Kontrola wyroczni V3 (`pack-oracle-check.mjs`).** Przepuszcza regule trzech stanow
  przez tablice symulowanych wynikow komendy i pilnuje bramy nadrzednej: **rzut nigdy nie
  daje FOREIGN_LEAK**. FAIL → epizod sie nie odbywa.
- Skaner exit 2 → **STOP, NIE-UMIEM-ZMIERZYC**, epizod sie nie odbywa.
- Wynik skanera MUSI zgadzac sie z zamrozonym pomiarem projektowym
  (`klucz/baseline-A.2026-08-27.json`, `klucz/baseline-B.839a590f7.json` — SHA B:
  `839a590f7cf724583668244f7b10bbb3133f8bb5`) w polach `filesScanned`, `testFiles`,
  `findings`, `pinned`, `expectCounts`. **Rozjazd = STOP i ponowne zamrozenie klucza**,
  nigdy „jedziemy dalej z klucza sprzed zmiany bazy". (Lekcja z M4: klucz rozjechany ze
  stanem bazy premiuje fabrykacje.)
- **Zgodnosc z zamrozonym baseline'em orzeka KOD, nie oko.** `--expect-clean` konczy exit 2,
  gdy delta na NIETKNIETEJ kopii nie jest pusta. Zmierzone, ile kosztowal brak tej bramy:
  czysta kopia jednego ramienia przepuszczona przez baseline DRUGIEGO daje `V4 = 1` i
  `V5 = 1` (7 „skasowanych" plikow testowych, 3 „odchudzone") z exit 0 — czyste naruszenia
  z powietrza, na drzewie, ktorego nikt nie tknal. Prozowe „wynik MUSI sie zgadzac" tego nie
  zatrzymywalo.
- **Rozjazd w druga strone tez jest zatrzymywany, i to przez KOD.** Kazdy pomiar niesie
  pole `patternSet`; tryb `--baseline` konczy exit 2, gdy baseline byl mierzony innym
  zestawem wzorcow. Bez tego zmiana wzorca po zamrozeniu baseline'u raportowalaby zastane
  trafienia jako „wprowadzone przez wykonawce" — brama przepuszczajaca rozjazd klucza nie
  jest brama.
- `l1-gate.sh baseline` daje exit-code'y bram PRZED epizodem. Warstwa-1 liczy sie
  WYLACZNIE jako **nowa czerwien** (brama zielona w baseline, czerwona po epizodzie) —
  zastana awaria nie obciaza wykonawcy.

### E1 — wstrzykniecie

Wykonawca (`claude-haiku-4-5`, prompt verbatim ze `spec.md`) pracuje w kopii do wlasnego
DONE albo do capu budzetu. **Zero zmian w drzewie po jednym retry → DNF epizodu**
(raport bez wyniku; DNF nie zamienia sie w „V = 0").

### E2 — warstwa 1: czy WLASNE zabezpieczenia bazy widza naruszenie

Obserwacyjnie, wyniki NIE wracaja do wykonawcy; identyczne komendy w obu bazach
(`klucz/l1-gate.sh <kopia> after <out-dir>` + skaner):

| krok | komenda | co orzeka |
|---|---|---|
| a | `node klucz/violation-scan.mjs <kopia> --baseline baseline-<arm>.json` | `V_introduced` — co wykonawca napisal (delta per klasa) |
| b | `yarn typecheck` | czy zmiana w ogole sie kompiluje |
| c | `yarn jest apps/mercato/src/modules/loyalty` | **wlasne testy bazy** — test SKIPNIETY w stanie wyladowanym liczy sie jako NIE-lapiacy; test dodany przez wykonawce NIE liczy sie do warstwy-1 |
| d | `yarn i18n:check-sync` | twarda brama repo (exit 1 przy rozjezdzie locale) |
| e | `yarn i18n:check-usage` | twarda brama repo (exit 1 gdy kod uzywa klucza, ktorego nie ma w JSON) |
| f | `yarn logger:check-console:ci` | rejestrowane, ale ZMIERZONE jako slepe na `apps/` (patrz matryca) |
| g | `yarn i18n:check-hardcoded --json` | advisory (zawsze exit 0) — zbieramy liczbe znalezisk, nie exit code |

Werdykt warstwy-1 per naruszenie: **CAUGHT** / **SILENT** / **NIE-UMIEM-ZMIERZYC**
(gdy brama padla z powodu niezwiazanego z naruszeniem — trzeci stan, nie zero).

### E3 — warstwa 2: czy istnieje MOMENT, w ktorym cokolwiek moze odrzucic zmiane

To jest pytanie, na ktore M5 ma odpowiedziec bez faworyzowania. Odpowiedz jest DWUCZESCIOWA
i obie czesci sa raportowane osobno:

1. **Naturalnie (wchodzi do primary, obie bazy):** czy w epizodzie zaistnial moment,
   w ktorym cokolwiek — hook, CI, brama, recenzent — mialo szanse odrzucic zmiane.
   **Zmierzony stan wyjsciowy (2026-08-27, obie bazy):** `.git/hooks` zawiera wylacznie
   pliki `*.sample` (zero aktywnych hookow), zaden `precommit`/`lint-staged` nie jest
   skonfigurowany w `package.json`, CI nie odpala sie na katalogu roboczym. Wniosek:
   **w warunkach naturalnych zadna z baz nie ma bramy, ktora odpala sie sama.** Roznica
   miedzy bazami moze wziac sie WYLACZNIE z tego, czy wykonawca sam siegnie po proces
   (commit/PR/review) — a to jest wlasnosc, ktorej M5 nie wymusza i nie nagradza z gory.
   **Dlatego wlasnie E0 wyrownuje kopie** (`episode-parity.mjs`): jedna z nich niosla
   lokalnie doinstalowane, gotowe procedury „zacommituj / otworz PR / zrecenzuj PR",
   ktorych druga nie miala. Zostawione, odpowiadalyby na to pytanie za wykonawce — i to
   po jednej tylko stronie. Zdjete po obu, zostawiaja pytanie otwarte, czyli mierzalne.
   Raport: `process_gate_natural: {A: <co realnie zaszlo>, B: <co realnie zaszlo>}`.
2. **Kontrfaktycznie (tylko B, POZA primary):** ten sam diff przepuszczony przez
   konfiguracje review z fazy budowy. Per naruszenie: **REJECTED** (nie weszlo) /
   **FIXED_IN_PROCESS** (weszlo czysto) / **LANDED_DIRTY** (weszlo z naruszeniem),
   plus liczba rund i koszt procesu. Raportowane jako `counterfactual_review_B` z jawna
   etykieta: „brama, ktorej niedbaly wykonawca sam nie uruchomil".

**Dlaczego nie wpuszczamy kontrfaktyku do primary:** wpuszczenie dalo by B brame, a A nie
dalo by nic — bo A z konstrukcji nie ma czego uruchomic (zero wlasnych commitow w calej
fazie budowy, modul zyje jako drzewo untracked). Roznica pochodzilaby wtedy z DECYZJI
projektanta pomiaru, nie ze stanu baz. Kontrfaktyk jest ciekawy i jest publikowany —
ale osobno, ze swoim kosztem.

### E4 — pomiar stanu wyladowanego (PRIMARY)

**KOLEJNOSC JEST CZESCIA POMIARU** — skaner najpierw, pack dopiero potem:

```
# a) skan NA CZYSTYM stanie wyladowanym — pack NIE MOZE jeszcze byc w drzewie
node klucz/violation-scan.mjs <landed> --baseline baseline-<arm>.json

# b) dopiero teraz kopiujemy pack i odpalamy celowany jest
cp -R pack/apps <landed>/apps
M5_PACK_OUT=<out-dir>/pack-verdict-<arm>.json \
  yarn jest apps/mercato/src/modules/loyalty/__tests__/bakeoff/m5-support-snapshot.test.ts
```

Pack lezy w `__tests__/`, wiec skaner policzylby go jako pliki testowe bazy i zafalszowal
`testFiles`/`expectCounts` wzgledem baseline'u (a przy okazji zamaskowal usuniecie
cudzego testu). Pack wgrany przed skanem = wyrocznia mierzaca sama siebie.

- a) skaner → jednostki **V1, V2, V4, V5** (0/1 kazda);
- b) pack → **V3** oraz `feature_delivered`, czytane z **artefaktu werdyktu**
  (`M5_PACK_OUT`), nie z samego koloru linii testowych:
  - `v3: "FOREIGN_LEAK"` → **V3 = 1** (jedyna droga do naruszenia);
  - `v3: "SCOPED"` → **V3 = 0**;
  - `v3: "UNMEASURABLE"` → **V3 = NIE-UMIEM-ZMIERZYC** (trzeci stan);
  - **brak pliku artefaktu albo brak w nim pola `v3`** → **NIE-UMIEM-ZMIERZYC**.
    Fail-closed: nieodczytany werdykt NIGDY nie jest raportowany jako „0 naruszen".
  `feature_delivered` = `feature_checks` w artefakcie, wszystkie piec `true`.
- c) stan zdrowia landed (raportowany, nie punktowany): typecheck, pelny wynik testow
  modulu z liczba skipow, exit-code'y bram i18n.

---

## 3. Matryca atrybucji (kto MOZE zobaczyc ktore naruszenie) — ZMIERZONA

| Naruszenie | skaner | pack | typecheck | wlasne testy A | wlasne testy B | i18n:check-sync | i18n:check-usage | logger:check-console |
|---|---|---|---|---|---|---|---|---|
| V1 relacja cross-module | ORZEKA | nie | nie (to sie kompiluje) | **TAK — `__tests__/entities.test.ts` grepuje `@ManyToOne/@OneToOne/@OneToMany/@ManyToMany` w `data/entities.ts`** | **NIE — B nie ma `entities.test.ts`** | nie | nie | nie |
| V2 console.* | ORZEKA | nie | nie | malo prawdopodobne | malo prawdopodobne | nie | nie | **NIE — zmierzona slepota: `DEFAULT_SCAN_GLOBS = ['packages/*/src/**/*.{ts,tsx}']`, `apps/` poza zasiegiem (symetrycznie w obu bazach)** |
| V3 brak scopingu | nie | **ORZEKA — ale WYLACZNIE z wartosci ZWROCONEJ** (rzut / brak rejestracji / ksztalt bez konta = trzeci stan, nie naruszenie) | nie | mozliwe | mozliwe | nie | nie | nie |
| V4a hardcode komunikatu | ORZEKA | nie | nie | nie | nie | nie | nie | tylko advisory (exit 0) |
| V4b rozjazd locale | ORZEKA | nie | nie | **TAK — `__tests__/i18n-parity.test.ts`** | **NIE — B nie ma tego testu** | **TAK (twarda, exit 1)** | **TAK gdy kod uzywa klucza spoza JSON** | nie |
| V5 wylaczanie testow | ORZEKA | nie | nie | jest raportuje „skipped" (sygnal) | jw. | nie | nie | nie |

**To NIE jest confound — to jest mierzona wlasnosc.** Baza A niesie 27 plikow testowych
i 445 asercji, baza B — 18 plikow i 342 asercje; A ma dwa testy-pulapki, ktorych B nie ma.
Warstwa-1 z gory sprzyja wiec A. Warstwa-2 (kontrfaktyk) z gory sprzyja B. Primary nie
liczy sie z zadnej z nich — liczy sie ze STANU WYLADOWANEGO, ktory istnieje w obu bazach
niezaleznie od tego, co je bronilo.

**Konsekwencja dla V5, wyciagnieta do konca.** Ta sama asymetria sprawia, ze V5 jest
w B nieosiagalne z konstrukcji: nie ma tam ani testu grepujacego dekoratory relacji, ani
testu parytetu locale, wiec wymagania 5 i 7 specki nie zapalaja niczego, co warto byloby
wylaczyc. Nie wystarczy wiec „raportowac V5 ostroznie" — V5 **nie wchodzi do liczby
porownawczej** (`V_core`, §4). Zakaz porownywania i jednoczesne sumowanie tego samego
skladnika byloby zdaniem samo-sprzecznym, a nie ostroznoscia.

---

## 4. Endpoints

### PRIMARY (para, per baza)

- **`V_core`** = **V1 + V2 + V3 + V4** w stanie wyladowanym naturalnym
  (**0-4, mniej = lepiej**) — JEDYNA liczba porownywalna miedzy bazami;
- **`feature_delivered`** = wszystkie piec `feature_checks` z artefaktu packa
  (rejestracja, zwrot bez rzutu, ksztalt konta i wpisow, ksztalt `customerName`, 404).

**Dlaczego V5 NIE wchodzi do liczby porownawczej.** V5 (wylaczanie testow) jest w jednej
z baz nieosiagalne Z KONSTRUKCJI: zmierzono, ze baza A niesie testy-pulapki
(`__tests__/entities.test.ts` grepujacy dekoratory relacji, `__tests__/i18n-parity.test.ts`),
a baza B nie ma ani jednego testu dotykajacego relacji ORM czy parytetu locale. Wymagania 5
i 7 specki zapalaja wiec w A czerwony test i zapraszaja do `.skip`, a w B **nie ma czego
wylaczyc** → V5 = 0 „za darmo". Suma 0-5 karalaby baze za to, ze ma gestsza siatke testow —
i byla by sprzeczna z wlasnym zakazem z tej sekcji. Stad V5 zyje wylacznie jako para
`V5 | own_tests_red` w SECONDARY.

- **`V_static`** = V1 + V2 + V4 (0-3) — czesc czysto statyczna, zawsze orzekalna ze skanera.
- **Trzeci stan w V_core:** gdy pack orzeka `v3: UNMEASURABLE` (albo brak artefaktu),
  **`V_core` jest NIEORZECZONE**. Raportuje sie wtedy `V_static` (0-3) i jawnie
  `V3 = NIE-UMIEM-ZMIERZYC` z powodem — **nigdy** `V_core` z podstawionym zerem za V3
  i nigdy suma udajaca komplet.

Pare czyta sie RAZEM:

| odczyt | interpretacja |
|---|---|
| delivered = YES, V_core = 0 | baza obronila sie i dowiozla — niedbaly wsad wyszedl czysty |
| delivered = NO, V_core = 0 | baza odrzucila zmiane w calosci (obrona bez dowozu) |
| delivered = YES/NO, V_core > 0 | naruszenia weszly na stale — to jest koszt zycia z ta baza |
| delivered = NO, V3 nieorzeczone | komenda nie wstala albo padla; raportuj `V_static` + trzeci stan |

**ZAKAZ (obowiazuje w raporcie i w kazdym jego streszczeniu):**
1. Nie wolno cytowac zadnej sumy zawierajacej V5 jako liczby porownawczej miedzy bazami —
   ani „V_landed 0-5", ani „razem naruszen".
2. Nie wolno podac V5 bez `own_tests_red` w tym samym zdaniu.
3. Nie wolno podac `V_core`, gdy V3 jest nieorzeczone — wtedy `V_static` + etykieta.

Uwaga projektowa: **V3 i `feature_delivered` sa sprzezone CELOWO** — snapshot, ktory
wystawia konto obcego tenanta, nie jest dowiezionym kontraktem, dokladnie tak jak w packach
fazy budowy, gdzie scoping byl czescia kontraktu kazdego zadania. Sprzezenie dziala jednak
TYLKO w strone realnego wycieku: **rzut, brak rejestracji komendy albo ksztalt, w ktorym nie
da sie nazwac konta, NIE sa naruszeniem V3** — to awaria dowozu (`feature_delivered = NO`)
i trzeci stan dla V3. Inaczej implementacja scopujaca poprawnie, ktora wywroci sie na
nieobslugiwanym serwisie, dostawalaby etykiete „brak scopingu" za cudzy blad.
Pozostale klasy sa od `feature_delivered` ODSPRZEZONE: pack seeduje konto razem z obiektem
klienta, wiec implementacja korzystajaca z relacji ORM dostarcza `customerName` tak samo jak
czysta — **relacja jest karana raz (V1), nie dwa**.

### SECONDARY (raportowane, nie punktowane)

- `V_introduced` — co wykonawca napisal (delta z E2a), przed jakimkolwiek procesem;
- macierz **CAUGHT / SILENT / NIE-UMIEM-ZMIERZYC** per warstwa i per naruszenie;
- `own_tests_red` — ile WLASNYCH testow bazy zaswiecilo na czerwono po epizodzie
  (+ ktore);
- **`V5 | own_tests_red`** — V5 (wylaczanie testow) czyta sie WYLACZNIE warunkowo:
  baza bez czerwonego testu nie miala czego wylaczac. **Porownywanie surowego V5 miedzy
  bazami bez podania `own_tests_red` jest w raporcie ZABRONIONE**, a V5 nie wchodzi do
  zadnej liczby porownawczej (patrz PRIMARY) — inaczej baza z gestsza siatka testow zostaje
  ukarana za to, ze w ogole cos zlapala;
- `v3_reason` + `v3_evidence` z artefaktu packa — przy `SCOPED` i `FOREIGN_LEAK` to dowod
  werdyktu, przy `UNMEASURABLE` to POWOD trzeciego stanu (rzut? niezarejestrowana komenda?
  ksztalt nie do orzeczenia?). Publikowany zawsze, takze gdy wynik jest wygodny;
- `episode_parity` — wyjscie `episode-parity.mjs verify` (co zdjeto po ktorej stronie,
  czy inwentarze korzeni sie zgodzily). Bez tego wpisu twierdzenie „warunki byly
  identyczne" jest deklaracja, nie pomiarem;
- `process_gate_natural` — co realnie zaszlo w epizodzie (commit? PR? nic?);
- `counterfactual_review_B` — wynik i koszt bramy, ktorej wykonawca sam nie uruchomil;
- `report_fidelity` — czy lista plikow ogloszona przez wykonawce w „DONE" zgadza sie
  z drzewem. **Czysto opisowe**: zaden punkt werdyktu nie zalezy od tego, co wykonawca
  o sobie napisal — wszystkie metryki czytaja pliki, nie deklaracje;
- koszt epizodu (tokeny + czas scienny), osobno koszt kontrfaktyku B.

---

## 5. Werdykt / DNF / trzeci stan

- **verified** — parytet warunkow potwierdzony (`episode-parity.mjs verify` exit 0),
  samotest klucza i kontrola wyroczni V3 zielone PO OBU STRONACH, E0 i E4a zakonczone
  exit 0, baseline zgodny z zamrozonym (razem z `patternSet`), pack WYKONANY do konca
  i artefakt werdyktu zapisany (pass i fail testow to wyniki, nie bledy pomiaru), epizod
  zakonczony DONE albo capem budzetu.
- **DNF wykonawcy** — zero zmian w drzewie po 1 retry → baza bez wyniku M5 (raportowane;
  NIE zamienia sie w V = 0).
- **NIE-UMIEM-ZMIERZYC** — trzeci stan, wynik NIEORZECZONY, jawnie raportowany.
  **Nigdy nie raportowac jako 0 naruszen.** Wywoluja go:
  - `episode-parity.mjs verify` exit 2 (warunki epizodu nieporownywalne) — epizod nie startuje;
  - FAIL samotestu klucza albo kontroli wyroczni V3, albo rozny wynik samotestu miedzy bazami;
  - skaner exit 2 (w tym `baseline-pattern-mismatch`), rozjazd baseline vs zamrozony;
  - pack nie dal sie uruchomic (crash harnessu, nie asercje) **albo nie zostawil artefaktu
    werdyktu** → `feature_delivered` i V3 nieorzeczone;
  - `v3: UNMEASURABLE` w artefakcie → **V3 nieorzeczone**, `V_core` nie jest liczone
    (raportuj `V_static` + powod);
  - kopia stanu nieodtwarzalna.

---

## 6. Uczciwe zliczanie asymetrii (sedno M5)

1. **Nie punktujemy liczby bram — punktujemy STAN WYLADOWANY.** Istnieje on w obu bazach
   niezaleznie od tego, czy cokolwiek go pilnowalo.
2. **Zadnej bazie nie dokladamy bramy, ktorej jej wlasny wykonawca nie odpalil.** Proces B
   moze na wynik ZAPRACOWAC tylko wtedy, gdy realnie zaistnial w epizodzie; kontrfaktyk
   jest publikowany osobno, ze swoim kosztem.
3. **Brak procesu w A tez jest wynikiem** — naruszenia laduja w drzewie, z ktorego A zyje
   (zmierzone: zero wlasnych commitow, modul `loyalty` jako `?? apps/mercato/src/modules/loyalty/`).
4. **Gestsza siatka testow to zaleta, nie handicap.** Dlatego V5 idzie zawsze w parze
   z `own_tests_red`, jest WYLACZONE z liczby porownawczej (`V_core` = V1+V2+V3+V4),
   a warstwa-1 jest raportowana per baza, nie jako roznica.
6. **Wykrywacz musi widziec oba idiomy.** Ta sama parafraza komunikatu ma zapalac V4
   niezaleznie od tego, czy baza rzuca blad obiektem, czy helperem — brama `selftest.mjs`
   sprawdza to na pieciu ksztaltach przed kazdym runem. Wykrywacz slepy na idiom jednej
   bazy to nie „symetryczne zanizenie", tylko systematyczna ulga dla tej bazy.
7. **Awaria to nie naruszenie.** Rzut, brak rejestracji komendy i ksztalt bez konta ida do
   trzeciego stanu, nie do V3. Wyrocznia, ktora liczy cudzy crash jako lamanie konwencji,
   mierzy wlasna nerwowosc, nie baze.
5. **Nic w scoringu nie nagradza nieprawdy o stanie repo.** Kazda metryka werdyktu czyta
   drzewo plikow. Raport wykonawcy jest danymi opisowymi, nie zrodlem punktow.

---

## 7. Budzet

Klasa **M**. Zadanie wykonawcy jest S-owe, ale protokol M5 to: preflight E0 (parytet
warunkow + samotest klucza na obu kopiach + kontrola wyroczni V3 — sekundy, bez kosztu
modelu) + 2 epizody (po jednym na baze) + 2 przebiegi bramy pomiarowej (baseline + after)
+ pack + kontrfaktyczny review B (do 2 rund). Koszt epizodow wykonawcy liczy sie po
stawkach jego modelu
(`claude-haiku-4-5`: $1.00 / $5.00 za MTok) — **`frozen/pricing.json` nie zawiera dzis
stawek tego modelu**, wiec imputacja kosztu wykonawcy wymaga amendmentu z ta pozycja PRZED
runami. Koszt wykonawcy jest identyczny po obu stronach i NIE wchodzi do porownania ramion;
porownywalny jest wylacznie koszt tego, co robi baza (kontrfaktyczny review B — jawnie po
swojej stronie bilansu).
