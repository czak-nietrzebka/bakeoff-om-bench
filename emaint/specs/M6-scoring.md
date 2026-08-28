# M6 (KILL-RESUME) — SCORING I PROTOKOL PRZERWANIA

## 1. Mechanizm werdyktu (primary endpoint — identyczny jak w fazie budowy)

**Ukryty pack (fail-closed):** 2 pliki jest w konwencji
`apps/mercato/src/modules/loyalty/__tests__/bakeoff/`:

- `m6-account-stats.test.ts` — rejestracja komendy, agregaty (suma/licznik/najnowszy
  wpis) z pulapkami cross-account i cross-tenant, pusty ledger, read-only jako efekty;
- `m6-account-stats-errors.test.ts` — 404 z kluczem `loyalty.errors.accountNotFound`
  (nieznane id / cudzy tenant / soft-delete), walidacja przed odczytem, zero zapisow.

Fail-closed: na bazie bez komendy `commandRegistry.get('loyalty.accounts.stats')`
zwraca undefined i KAZDY test packa jest czerwony (weryfikacja statyczna: zadna z baz
nie zawiera stringa `loyalty.accounts.stats` — patrz notes.md; do potwierdzenia
wykonawczo w pilocie packa, jak dla pozostalych packow E-MAINT).

**Brama** (jak w fazie budowy): kopiowanie plikow packa do checkoutu → celowany jest
na oba pliki → `yarn typecheck` → testy modulu → pelna suita repo wedlug definicji
bramy fazy budowy. Zielona brama = wszystkie kroki zielone. Feedback po czerwonej
bramie WYLACZNIE w zamrozonym formacie `<test-id> :: <pierwsza linia asercji>`
(identycznie dla obu baz). Checklista konwencji: dla M6 obowiazuja wylacznie punkty
wspolne [K1]-[K6]; brak dodatku per-task.

## 2. Protokol przerwania (kill) — techniczny, identyczny dla obu baz

Zadanie M6 rozni sie od pozostalych zadan JEDNA manipulacja: pierwsza sesja robocza
zostaje twardo przerwana po stalym czasie sciennym, a zadanie konczy druga, swieza
sesja. Poza tym pelny przebieg = przebieg standardowy.

1. **Sesja 1 (przerywana).** Wykonawca dostaje spec.md bez zadnej wzmianki o
   planowanym przerwaniu (przerwanie jest NIEZAPOWIEDZIANE — mierzymy naturalne
   nawyki zabezpieczania pracy, nie zachowanie obronne wywolane ostrzezeniem).
   Timer startuje w momencie spawnu procesu sesji.
2. **Kill po 240 s czasu sciennego:** `SIGKILL` na CALA grupe procesow sesji, bez
   sygnalu poprzedzajacego, bez grace-period, bez mozliwosci wykonania handlerow
   zamykajacych. Workspace zostaje DOKLADNIE w stanie z chwili przerwania — zadnego
   sprzatania, resetu ani normalizacji miedzy sesjami (stan zastany JEST przedmiotem
   pomiaru).
   - Uzasadnienie progu 240 s: sesje fazy budowy trwaly 4-27 min; 240 s = obserwowane
     minimum, wiec ukonczenie zadania przed killem jest skrajnie malo prawdopodobne,
     a jednoczesnie 240 s wystarcza na rozpoznanie repo i pierwsze zapisy plikow —
     kill trafia w srodek pracy, nie przed nia.
   - Sesja 1 konczy sie SAMA przed 240 s → kill nie nastepuje; run oznaczony
     `completed_pre_kill`, brama biegnie normalnie, manipulacja resume jest dla tego
     runu pusta (odnotowane, publikowane; analiza par to uwzglednia).
3. **Snapshot post-kill (tylko pomiar).** Po killu harness wykonuje kopie stanu
   zakresu `apps/mercato/src/modules/loyalty` + listy plikow zmienionych wzgledem
   snapshotu pre-task (diff drzewa plikow); jezeli workspace ma metadane systemu
   kontroli wersji, sa one rejestrowane verbatim (galaz, status, log). Kopia laduje
   POZA workspace'em. Na ODLACZONEJ kopii harness odpala pack (pomiarowo:
   `kill_state_pack_score` = liczba zielonych testow packa w chwili killa). Zywy
   workspace pozostaje nietkniety; pliki packa NIGDY nie laduja w zywym workspace
   miedzy sesjami; wynik pomiaru NIE jest przekazywany sesji 2 i NIE liczy sie jako
   iteracja bramy.
4. **Sesja 2 (dokonczeniowa).** Swieza sesja (bez --resume, zgodnie z regula fazy
   budowy "swieza sesja per task/iteracje"), TEN SAM workspace w stanie zastanym,
   TEN SAM spec.md verbatim, plus JEDNA zamrozona doklejka do promptu (identyczna
   dla obu baz, przed trescia speca):

   > UWAGA: poprzednia proba realizacji tego zadania zostala przerwana w trakcie
   > pracy. Repozytorium jest w stanie, w jakim ja zostawiono. Dokoncz zadanie
   > i doprowadz je do kryteriow ukonczenia.

5. **Dalszy przebieg standardowy.** Po sesji 2 brama; czerwona brama → feedback w
   zamrozonym formacie → kolejna swieza sesja, jak w fazie budowy. Kill wykonywany
   jest WYLACZNIE raz (sesja 1); zadnych kolejnych przerwan. Pad sesji z przyczyn
   infrastrukturalnych → obowiazuja pre-rejestrowane adjudykacje fazy budowy
   (infra-void / retry), NIE liczy sie jako kill.

## 3. Werdykt

- **verified** — brama zielona (pack 100% + typecheck + testy modulu + pelna suita)
  w ramach limitow: max 5 ewaluacji bramy (pomiarowa ewaluacja post-kill NIE liczy
  sie) oraz budzet tokenow roboczych klasy S; tokeny sesji 1 (ubitej) WLICZAJA SIE
  do budzetu zadania — koszt przerwania jest czescia mierzonego kosztu.
- **DNF** — przekroczenie limitu iteracji albo budzetu klasy S; definicja tokenow
  roboczych i imputacji USD jak w fazie budowy.
- Zadnych ocen "na oko" w primary endpoint.

## 4. Metryki

**Primary (identycznie jak faza budowy):** laczny koszt dojscia do zielonej bramy —
tokeny robocze (sesja 1 + sesja 2 + ewentualne iteracje), czas scienny, imputacja USD.

**Secondary (specyficzne dla M6, liczone skryptem — zero uznaniowosci):**

- `salvage_rate` — ile z linii DODANYCH przez sesje 1 (snapshot post-kill vs
  baseline pre-task) przetrwalo do finalnego zielonego drzewa; algorytm i wywolanie:
  `klucz/salvage_rate.py BASELINE KILL FINAL --scope=apps/mercato/src/modules/loyalty`
  (multizbiory znormalizowanych linii, path-insensitive primary, per-plik pomocniczo;
  `null` gdy sesja 1 nie zdazyla nic dodac — raportowane jako n/a, nie zero).
- `kill_state_pack_score` — liczba zielonych testow packa na snapshocie post-kill
  (pomiar "jak daleko zaszla sesja 1" na skali packa).
- `kill_state_descriptors` — zarejestrowane symetrycznie, opisowo (nie punktowane):
  liczba i lista plikow zmienionych w chwili killa; metadane systemu kontroli wersji
  workspace'u verbatim, jezeli istnieja (galaz / status / log).

Teza fazy E-MAINT operacjonalizuje sie tu tak: jezeli dyscyplina pracy (czeste male
checkpointy, opisany stan posredni) zwraca sie przy zyciu z kodem, baza z takim
nawykiem powinna miec wyzszy `salvage_rate` i nizszy laczny koszt sesji 2; spec i
protokol sa identyczne, wiec roznica — jesli wystapi — pochodzi z metody, nie z tresci
zadania.

## 5. Budzet

Klasa **S** (jak inne zadania jednokomendowe bez migracji): budzet tokenow roboczych
i USD wedlug zamrozonej tabeli budzetow dla klasy S. Uwaga kalibracyjna (jawna):
M6 strukturalnie wymusza minimum DWIE sesje, wiec zuzycie budzetu bedzie wyzsze niz
w typowym S; wartosci budzetow sa z definicji draftem kalibrowanym pilotazem —
ewentualna korekta dla M6 przez amendment, PRZED runami wlasciwymi.
