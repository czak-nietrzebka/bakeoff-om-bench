# M3 — SCORING (rollback biznesowy: per-linia -> od sumy zamowienia)

## Mechanizm werdyktu (primary endpoint — orzekany KODEM, fail-closed)

Identycznie jak bramy E1: brama kopiuje ukryty pack do checkoutu ramienia
(`apps/mercato/src/modules/loyalty/__tests__/bakeoff/m3-*.test.ts`) i odpala celowany
jest na tych plikach (po `yarn build:packages` + `yarn typecheck` jak w bramie E1).
Werdykt FAIL-CLOSED: test czerwony, nieuruchamialny (blad importu, brak komendy,
brak katalogu) albo typecheck czerwony = brama CZERWONA.

Pack — 4 pliki, **20 przypadkow raportowanych przez jest** (13 + 3 + 3 + 1):

| Plik | Przyp. | Co orzeka |
|---|---|---|
| `m3-accrue-order-rollback.test.ts` | 13 | rejestracja komendy; matematyka od sumy (1 wpis, floor, bez `orderLineId`); stempel `expiresAt` +12 mies. UTC; przypadki puste (suma<=0, gosc); idempotencja (replay, wpisy per-linia, wpis NULL); regresja 404/scoping/zod |
| `m3-later-features-smoke.test.ts` | 3 | event `loyalty.tier.changed` na nowej matematyce (dokladnie 1 emisja z tierem koncowym i saldem po uznaniu; cisza przy braku awansu i przy replayu); stawka org: floor(suma*stawka), mnozenie PRZED floor (499 vs 498) |
| `m3-migration-history.test.ts` | 3 | historia migracji append-only + spojnosc decyzji schematowej — wszystko orzekane **wylacznie po ciele `up()`** i po DEKLARACJI property (szczegoly nizej) |
| `m3-shared-math-source.test.ts` | 1 | jedno zrodlo matematyki: podmiana `calculateOrderNetPoints` na sentinel (7) MUSI zmienic wynik naliczenia (1 wpis, 7 pkt) |

Liczba 13 w pierwszym wierszu to liczba przypadkow W RAPORCIE JEST, nie liczba blokow
w pliku: plik ma 11 blokow `it(...)` **plus jeden `it.each([...])` o DWOCH wierszach**
(`m3-accrue-order-rollback.test.ts:565`, wiersze „a non-uuid orderId" i „a missing
orderId"), ktory jest raportuje jako dwa osobne przypadki. Suma packa = 20, nie 18 —
poprzednia wersja tego dokumentu liczyla bloki, nie przypadki. Brama porownuje z liczba
raportowana przez jest, wiec liczba w tym dokumencie musi byc ta sama.

## Definicja werdyktu

**verified** = WSZYSTKIE PIEC warunkow spelnione JEDNOCZESNIE, na JEDNYM checkoucie
bramy (kolejnosc = kolejnosc uruchamiania):

1. **`yarn build:packages` + `yarn typecheck` zielone.**
2. **Pack M3 zielony w calosci: 4/4 pliki, 20/20 przypadkow.** Zero czerwonych, zero
   pominietych (`skipped`/`todo`), zero plikow nieuruchamialnych.
3. **Wlasna suita modulu `loyalty` zielona** — celowany przebieg suity modulu
   (`apps/mercato/src/modules/loyalty/`), zero czerwonych.
4. **Pelna suita repo zielona** — spec pkt 9 („caly istniejacy test-suite repo ma byc
   zielony po Twoich zmianach") i Konwencje („pelna suita repo zielona").
5. **Pokrycie nie zostalo skasowane** — Warunek 5 nizej (spec pkt 10 + Kryterium
   ukonczenia „Zaden istniejacy przypadek testowy nie zostal usuniety").

Zaden warunek nie zastepuje pozostalych i zaden nie jest domyslnie zielony: ramie
z zielonym packiem, ale czerwona wlasna suita modulu albo czerwona suita repo, NIE jest
verified. Warunki 3-4 sa w specu jako kryterium ukonczenia, wiec ramie zna je z gory
i sa identyczne dla obu ramion.

**DNF** = wyczerpanie budzetu L (token_budget_robocze 1 500 000 / $6 imputowane /
max 5 iteracji bramy per `budgets.json`) bez spelnienia (1)-(5) jednoczesnie.

**NIE-UMIEM-ZMIERZYC (trzeci stan)** = ktoregokolwiek z warunkow (1)-(5) NIE DA SIE
orzec: przebieg przerwany infrastrukturalnie, suita nieuruchamialna z powodow spoza
zmiany ramienia, brak pinu bazowego do Warunku 5. Wtedy run NIE jest ani verified, ani
DNF, ani „naruszeniem" — jest wstrzymany, zapisany jako `NIE-UMIEM-ZMIERZYC <warunek>
<powod>` i powtarzany po usunieciu przyczyny. Braku pomiaru nie wolno zaliczyc na
zielono ani policzyc jako naruszenia; iteracja nieuruchamialna nie liczy sie do limitu 5.

### Warunek 5 — pokrycie nie zostalo skasowane (kryterium WEWNATRZ-ramienne)

**Po co.** Primary endpoint to KOSZT dojscia do zielonej bramy. Skasowanie testow
przybijajacych model per-linia jest TANSZA sciezka do zielonego niz ich przepisanie,
wiec bez tego warunku brama premiuje skrot, ktory spec pkt 10 wprost zakazuje. Premia
jest przy tym ASYMETRYCZNA — wyprowadzone z pinow przedzadaniowych (dowody w `notes.md`
§Ciezar aktualizacji testow):

| Ramie | Pliki testowe modulu dotykajace modelu per-linia | Wystapienia | Linie |
|---|---|---|---|
| A | `__tests__/accrueOrder.test.ts`, `__tests__/accrueOrder-rate.test.ts`, `__tests__/expiry.test.ts` | 13 (`orderLineId`) / 15 (`orderLineId\|order_line_id`) | 1105 |
| B | `__tests__/accrueOrder.test.ts` | 5 (`orderLineId`) / 6 (`orderLineId\|order_line_id`) | 847 |

Kasowanie oplaca sie ~3x bardziej ramieniu A, czyli przesuwa dokladnie te metryke,
ktora bench mierzy. Dlatego warunek wchodzi do werdyktu, a nie zostaje obserwacja.

**Dlaczego to nie lamie symetrii.** Kryterium porownuje KAZDE ramie z JEGO WLASNYM
pinem przedzadaniowym (B: SHA `839a590f7`; A: odcisk `e3393d14...` — `notes.md`
§Snapshoty), nigdy ramie z ramieniem. Wzorzec z M2: „liczba plikow testowych modulu nie
maleje wzgledem stanu przed zadaniem; spadek = czerwona flaga do recznego potwierdzenia".
Absolutne liczby roznia sie miedzy ramionami i to jest w porzadku — progiem jest
„nie maleje wzgledem SIEBIE", nie wspolna liczba.

**Co dokladnie mierzymy.** Cztery liczby zdejmowane tym samym poleceniem w pilocie
(baseline) i po bramie (stan koncowy), plus piata liczona z diffa:

- **(a) liczba plikow testowych modulu** (`*.test.ts` / `*.test.tsx` w
  `apps/mercato/src/modules/loyalty/`) — nie maleje;
- **(b) liczba przypadkow ZALICZONYCH w raporcie jest z celowanego przebiegu wlasnej
  suity modulu** (`Tests: N passed`) — nie maleje;
- **(c) dla KAZDEGO pliku z listy „dotyka modelu per-linia" tego ramienia** (lista
  zdejmowana z pinu ramienia grepem `orderLineId\|order_line_id`, nie ustalana recznie
  — A: 3 pliki, B: 1 plik): plik istnieje, a liczba jego przypadkow zaliczonych nie
  maleje;
- **(d) liczba przypadkow ZALICZONYCH w CALYM repo** — z tego samego przebiegu pelnej
  suity, ktory i tak zapada dla warunku 4 (`Tests: N passed`, sciezka packa wylaczona)
  — nie maleje; jako cross-check liczba plikow testowych repo (`*.test.ts`/`*.test.tsx`
  z pominieciem `node_modules`, `dist`, `.next`, `build`, ta sama metoda przed i po).
  Bez (d) najtansza droga do zielonej PELNEJ suity repo jest skasowanie albo wyciszenie
  testu, ktory ramie zepsulo POZA modulem `loyalty` — (a)-(c) tego nie widza, bo sa
  zawezone do modulu. Baseline cross-checku zmierzony: A 2791 plikow, B 2782 — roznica
  9 zgadza sie co do sztuki z roznica inwentarza suity modulu (27 vs 18), co potwierdza,
  ze obie metody licza te sama populacje. Baseline przypadkow zdejmuje pilot (nie da sie
  go policzyc statycznie — zastrzezenie 2);
- **(e) liczba USUNIETYCH blokow `it(` / `test(` w diffie plikow z listy (c)** wzgledem
  kopii przedzadaniowej tego ramienia (linie `-` otwierajace blok przypadku). Bez (e)
  brama ma dziure, ktora sama otwiera: spec pkt 10 KAZE dopisac nowe testy wlasne,
  najczesciej do TYCH SAMYCH plikow, wiec skasowanie dziewieciu przypadkow per-linia
  i dopisanie dwunastu nowych PODNOSI (a)-(d) i zaden licznik nie drgnie. (e) mierzy
  usuniecia niezaleznie od dopisan. `(e) > 0` nie jest samo w sobie naruszeniem — to
  liczba kierujaca przegladem diffu, ktory i tak jest obowiazkowy (werdykt nizej).

**Piec zastrzezen pomiarowych, bez ktorych ta brama przepuszcza skrot albo karze
poprawne rozwiazanie:**

1. **Pack jest WYLACZONY z liczenia.** Wszystkie liczby (a)-(d) zdejmowane sa
   z pominieciem sciezki `apps/mercato/src/modules/loyalty/__tests__/bakeoff/`.
   Bez tego pomiar po bramie zawiera 20 przypadkow packa i ramie moze skasowac
   kilkanascie wlasnych przypadkow, a licznik i tak UROSNIE. (Katalog `bakeoff/`
   nie istnieje dzis w zadnym ramieniu — zmierzone; pojawia sie dopiero przy kopiowaniu
   packa przez brame.)
2. **Licznik statyczny NIE wystarcza.** Grep po `^\s*(it|test)(` jest slepy na
   `it.each([...])`, a tego idiomu uzywaja OBA ramiona we wlasnych suitach (A: 4
   wystapienia w 3 plikach; B: 5 wystapien w 3 plikach — zmierzone). Detektor liczacy
   bloki myli sie asymetrycznie i wlasnie tak powstala bledna liczba 18 dla packa.
   Autorytatywna jest liczba z RAPORTU JEST; grep sluzy najwyzej jako cross-check.
3. **`skip` / `todo` / `only` = pokrycie USUNIETE.** Przypadek oznaczony `.skip`/`.todo`
   nie jest zaliczony, wiec (b) i (c) spadaja — i tak ma byc: wyciszenie testu to
   kasowanie pokrycia w przebraniu. `.only` w pliku wycina reszte pliku z przebiegu,
   co rowniez zbija licznik. Baseline obu ramion: zero `skip`/`only`/`todo` we wlasnych
   suitach modulu (zmierzone statycznie, do potwierdzenia liczba z jest w pilocie).
4. **Trzeci stan.** Gdy ktorejkolwiek liczby NIE DA SIE zdjac (suita nieuruchamialna,
   przebieg przerwany, brak zapisanego pinu) — raportujemy `NIE-UMIEM-ZMIERZYC` i brama
   zostaje wstrzymana. To nie jest ani zgodnosc, ani naruszenie pkt 10.
5. **Spadek licznika to FLAGA, nie automatyczne naruszenie.** Przeniesienie albo zmiana
   nazwy pliku z listy (c) zbija licznik, a naruszeniem nie jest — rozstrzyga przeglad
   diffa (czy kazdy przypadek ma nastepce). Zamiana flagi na werdykt bez przeczytania
   diffa liczylaby poprawne rozwiazanie jako naruszenie i lamalaby symetrie tak samo,
   jak przepuszczanie skrotu.

**Werdykt Warunku 5 — dwie warstwy, bo sam licznik nie wystarcza.**

*Warstwa 1 — liczniki (a)-(d), automatyczne.* Nie maleja → w porzadku (wzrost jest
legalny zawsze, spec pkt 10 wymaga NOWYCH testow wlasnych). Spadek ktorejkolwiek →
verified WSTRZYMANE; organizator czyta diff plikow, ktore zniknely albo stracily
przypadki, i szuka nastepcow. Ta warstwa pilnuje CALEGO repo — takze testow poza
modulem, ktore ramie moglo skasowac, zeby domknac warunek 4.

*Warstwa 2 — przeglad diffu plikow z listy (c), wykonywany ZAWSZE.* Nie tylko przy
spadku licznika, bo licznik tej klasy skrotu nie widzi: spec pkt 10 kaze dopisac nowe
testy do tych samych plikow, wiec skasowanie dziewieciu przypadkow per-linia i dopisanie
dwunastu nowych PODNOSI (a)-(d). Zakres przegladu jest z gory ograniczony i znany —
**A: 3 pliki, B: 1 plik** — wiec to nie jest ocena „na oko" calego drzewa, tylko lektura
czterech konkretnych diffow. Liczba (e) kieruje wzrok: kazde usuniete `it(` musi miec
nastepce o tej samej intencji, z nowa wyrocznia i 1-zdaniowym komentarzem. Przeglad
lapie takze wypatroszenie przypadku w miejscu (blok zostaje, asercje znikaja), ktorego
zaden licznik przypadkow nie zobaczy.

*Rozstrzygniecie.* Kazdy usuniety albo wypatroszony przypadek ma nastepce → warunek
spelniony. Ktorykolwiek nie ma → pkt 10 zlamany → run nie-verified. Podstawa jest
WYLACZNIE diff i raport jest — nigdy to, co ramie napisze o sobie.

**Granica tego warunku (jawna, nie zamiatana).** Warunek 5 orzeka o KASOWANIU
i WYPATROSZENIU pokrycia, nie o jakosci przepisania: czy nowa wyrocznia jest trafna
i czy komentarz jest sensowny, zostaje obserwacja wtorna. Odrzucone swiadomie:
porownanie TYTULOW przypadkow jako kryterium automatyczne — karaloby legalna zmiane
nazwy, ktora rollback wymusza (wyrocznia sie zmienila), czyli liczyloby poprawne
rozwiazanie jako naruszenie. Poza lista (c) zostaje ryzyko wypatroszenia testu, ktory
modelu per-linia nie dotyka; tam nie ma czego kasowac w zwiazku z tym zadaniem, a ubytek
calych przypadkow lapia (b) i (d).

## Guard historii migracji — wyrocznia (po naprawie MUST-FIX)

Wersja pierwotna orzekala regexem po CALYM pliku migracji i **przepuszczala na zielono
trzy zle rozwiazania** (dowody i pomiar: `notes.md` §Defekt). Wyrocznia obowiazujaca:

| Przypadek | Obserwabla | Czerwony gdy |
|---|---|---|
| `keeps the shipped migration whose up() ADDS order_line_id...` | jakas migracja w `migrations/` DODAJE kolumne w ciele `up()` | wydana migracja wprowadzajaca kolumne skasowana albo przerobiona (nowy dropper jej NIE zastapi — jego `up()` usuwa, nie dodaje) |
| `leaves that add-column migration additive...` | zadna migracja nie ma w JEDNYM `up()` naraz `add` i `drop` tej kolumny | wydany plik przerobiony w miejscu na add+drop |
| `drops the column in a migration up() if and only if the entity stopped declaring it` | deklaracja `orderLineId` / `@Property({ name: 'order_line_id'` w klasie `LoyaltyLedgerEntry` (po odcieciu komentarzy) vs `drop` w `up()` | entity-only drop (property znika, zadna migracja nie usuwa kolumny) ALBO migration-only drop (encja dalej mapuje kolumne, ktora migracja usuwa) |

Trzy decyzje projektowe, ktore trzymaja te wyrocznie przy zyciu:
- **tylko `up()`** — kazda migracja MikroORM, ktora kolumne DODAJE, usuwa ja w `down()`;
  skan po calym pliku znajduje `drop column "order_line_id"` w nietknietej, poprawnej
  historii i dlatego przepuszcza dokladnie te bledy, ktore ma lapac. Stan wdrozonego
  schematu mieszka w `up()`;
- **deklaracja, nie goly identyfikator** — encja jest opisana proza, a proza wymienia
  property po nazwie (ramie B ma `orderLineId` w komentarzu). Komentarze sa wycinane
  przed pomiarem, liczy sie dekorator kolumny albo deklaracja property;
- **klasa encji szukana w calym module** (`data/entities.ts` w pierwszej kolejnosci) —
  przeniesienie klasy nie jest karane, ale jej BRAK jest raportowany jako czerwony
  („nie umiem zmierzyc"), nie przemilczany.

Kontrakt, ktory te przypadki orzekaja, jest w specu jawnie (pkt 5: obie opcje legalne,
encja i migracje musza sie zgadzac, append-only takze wobec `up()` wydanego pliku) —
pack nie mierzy niczego, czego spec nie przybija.

## Feedback po czerwonej bramie

Wylacznie linie `<test-id> :: <pierwsza linia komunikatu asercji, max 200 znakow>`
per `feedback-format.md` — zero tresci testow, zero sciezek packa, identycznie dla
obu ramion. Przypadki guardu historii rzucaja komunikat diagnostyczny w pierwszej
linii (co jest niespojne i z czym), a nie golego `expect(received).toEqual(...)`.

## Stan startowy — status kazdego twierdzenia

Rozroznienie jest twarde, bo poprzednia wersja tej sekcji nazywala „zmierzonym"
takze to, czego nie uruchomiono. Z PRZEBIEGOW wykonany zostal WYLACZNIE przebieg
wyroczni guardu historii migracji (`notes.md` §Pomiar wyroczni). Cala reszta zachowania
komendy jest **WYPROWADZONA z lektury kodu obu baz** — i pozostaje przewidywaniem do
konca pilotu. (Pomiary STATYCZNE na bazach — grepy, inwentarz plikow testowych, liczby
do Warunku 5 — sa zrobione i udokumentowane w `notes.md`; nie sa przebiegiem packa
i nie zastepuja pilotu.)

### WYPROWADZONE z kodu obu baz (przewidywanie, potwierdzane w pilocie)

Zrodlo: `commands/accrueOrder.ts` obu ramion na pinach z `notes.md` §Snapshoty
(A: `:107-108` `.filter(isQualifyingLine).map(... calculateOrderNetPoints(Number(line.totalNetAmount) * rate))`,
`:144 orderLineId: line.id`; B: `:117-119` ten sam uklad, `:136 orderLineId: line.id`)
oraz brak `grandTotalNetAmount` w calym module w OBU ramionach (0 trafien).

DYSKRYMINATORY — 6 przypadkow, przewidywane CZERWONE na starcie w OBU ramionach
(mierza wykonanie rollbacku):
- `order-sum accrual on a mixed order` — per-linia daje created=2/149 pkt vs 1/364;
- `stamps expiresAt` — per-linia daje created=0 (zamowienie bez linii);
- `replaying the command...` — per-linia: pierwsze wywolanie created=2/149 pkt
  zamiast 1/364, wiec test pada juz na pierwszej asercji;
- `tier promotion event` — per-linia: floor(10.00) = 10 pkt z jedynej linii,
  brak awansu, zle saldo (zamowienie ma sume netto 149.99);
- `org-level rate override` — per-linia: floor(100.00 * 2) = 200 pkt zamiast
  floor(249.99 * 2) = 499;
- `shared math source sentinel` — per-linia: 2 wpisy vs 1.

GUARDY BEHAWIORALNE — 11 przypadkow, przewidywane ZIELONE na starcie w OBU ramionach
(mierza brak regresji podczas rollbacku; zadeklarowane swiadomie per regula „nie jest
juz spelnione za darmo... chyba ze to celowy punkt pomiaru"):
- rejestracja komendy; skip suma<=0, gosc; idempotencja z wpisami per-linia
  (ZASEEDOWANYMI) i z wpisem NULL — to jest wlasnie ochrona historii, ktora
  rollback najlatwiej psuje (donaliczanie juz naliczonych zamowien = podwojny
  kredyt klienta); oba ramiona kluczuja idempotencje po `orderId`
  (A `:116-119`, B `:95-98`), wiec guard jest symetryczny mimo roznej kolejnosci
  lookupu konta;
- 404 orderNotFound / cudzy tenant / accountNotFound (seed z kwalifikujaca sie
  linia, zeby lookup konta byl osiagalny pod OBOMA modelami — kolejnosc pustego
  skipu vs lookupu konta nie jest czescia kontraktu); walidacja zod przed odczytem
  (`it.each` — DWA przypadki w raporcie jest);
- cisza tier-eventu bez przekroczenia progu.

### ZMIERZONE (przebieg wykonany, tabela w `notes.md` §Pomiar wyroczni)

- **trzy przypadki guardu historii migracji** — wyrocznia wyciagnieta verbatim z pliku
  packa i przebiegnieta na obu REALNYCH drzewach modulu oraz na 16 mutantach: zielone
  na obu bazach i na obu wariantach poprawnego rozwiazania (kolumna zostaje / kolumna
  usunieta nowa migracja), czerwone na czterech wariantach zlego. MISMATCHES: 0.
- Czego ten pomiar NIE obejmuje: uruchomienia pod prawdziwym jestem w checkoucie
  ramienia (transform, resolver, konfiguracja projektu). To domyka pilot.

6 + 11 + 3 = 20 przypadkow — zgadza sie z licznikiem packa.

## KROK KONTROLNY ORKIESTRATORA — pilot packa (przed startem ramion)

Obowiazkowy, jak dla kazdego packa E-MAINT. Wykonywany na NIETKNIETYCH checkoutach
OBU ramion (piny z `notes.md` §Snapshoty), tym samym poleceniem co brama:
`yarn build:packages` + `yarn typecheck` + celowany jest na 4 plikach packa.

Pilot zdejmuje jednoczesnie **liczby bazowe Warunku 5** — (a), (b), liste (c) i (d) — na
checkoucie BEZ skopiowanego packa, i zapisuje je przy pinie ramienia. Archiwizuje takze
**KOPIE przedzadaniowa drzewa modulu OBU ramion** (poza workspace'em): bez niej (e) jest
nieliczalne dla ramienia bez systemu kontroli wersji, a metoda przestaje byc identyczna
dla obu — kopie robimy dla obu, mimo ze dla jednego wystarczylby SHA. (b) i (d) wymagaja
jednego przebiegu wlasnej suity modulu i jednego przebiegu pelnej suity repo na stanie
nietknietym; oba i tak zapadaja przy kazdej ewaluacji bramy, wiec pilot dodaje je raz,
nie wprowadza nowego rodzaju pomiaru. Bez zapisanych liczb bazowych Warunek 5 jest
nierozstrzygalny (trzeci stan), wiec ten krok nie jest opcjonalny.

Warunek przejscia pilotu — WSZYSTKO ponizsze, w OBU ramionach:

1. **pack sie URUCHAMIA** — kazdy z 20 przypadkow konczy sie wynikiem pass albo
   assertion-fail; zaden plik nie pada na ladowaniu/imporcie/braku komendy;
2. **6 dyskryminatorow CZERWONYCH** — i to na asercji przewidzianej w tabeli wyzej
   (created / punkty / saldo / liczba wpisow), nie na blednym seedzie ani na wyjatku
   z harnessu;
3. **14 pozostalych przypadkow ZIELONYCH** (11 guardow behawioralnych + 3 guardy
   historii migracji);
4. **wynik identyczny w obu ramionach** dla kazdego z 20 przypadkow;
5. **liczby bazowe Warunku 5 zdjete i zapisane** dla obu ramion, wraz z kopiami
   przedzadaniowymi drzewa modulu (podstawa (e)).

**STOP — nie startujemy ramion**, gdy zajdzie ktorekolwiek:

- ktorykolwiek DYSKRYMINATOR jest ZIELONY na nietknietej bazie → zadanie jest tam
  spelnione za darmo, blad projektanta packa;
- ktorykolwiek GUARD jest CZERWONY na nietknietej bazie → pack karze stan zastany,
  czyli mierzy nie to, co ma mierzyc;
- pack jest NIEURUCHAMIALNY w ktorymkolwiek ramieniu → to `NIE-UMIEM-ZMIERZYC`, a nie
  „czerwony zgodnie z planem"; czerwien z bledu ladowania nie jest dowodem niczego;
- wynik ROZNI SIE miedzy ramionami na ktorymkolwiek z 20 przypadkow → zlamana symetria
  pomiaru, pack wraca do poprawki;
- liczby bazowe Warunku 5 nie daja sie zdjac w ktorymkolwiek ramieniu albo nie udalo
  sie zarchiwizowac kopii przedzadaniowej drzewa modulu.

Kazdy STOP wraca do projektanta packa; runow wlasciwych nie startujemy „na probe".

**Dowod pilotu zapisujemy, nie streszczamy.** Do rejestru zadania ida cztery rzeczy dla
KAZDEGO ramienia: podsumowanie jest per plik (nazwy przypadkow + pass/fail), wyjscie
`typecheck`, liczby bazowe (a)-(d) wraz z komendami, ktore je zdjely, przy pinie
ramienia, oraz sciezka do zarchiwizowanej kopii przedzadaniowej drzewa modulu. Zdanie
„pilot przeszedl" bez tych artefaktow NIE domyka kroku kontrolnego — brama, ktora
przyjmuje twierdzenie zamiast wyniku, nie jest brama. To samo dotyczy przebiegow po
bramie: `verified` zapada na zapisanych wynikach, nie na relacji z przebiegu.

## Wtorne obserwacje (bez wplywu na werdykt, per R8)

Checklista wspolna (K1-K6). Sposob wykonania pkt 10 speca NIE jest juz obserwacja
wtorna — kasowanie pokrycia wchodzi do werdyktu jako Warunek 5. Wtorne pozostaje:
- JAKOSC uzasadnienia w komentarzach o zmianie wyroczni (czy komentarz naprawde
  tlumaczy zmiane) — sama obecnosc komentarza przy przypadku usunietym albo
  wypatroszonym jest juz czescia przegladu z Warunku 5, wiec tu zostaje ocena
  trafnosci, nie faktu;
- ktora opcje schematowa z pkt 5 ramie wybralo (kolumna zostaje / drop nowa migracja)
  — obie legalne, notowane opisowo;
- koszt fazy poszukiwania (od startu sesji do pierwszej edycji wlasciwego pliku).

## Dlaczego pack, nie klucz odpowiedzi

Zadanie jest klasy fix/feature (zmiana zachowania kodu), nie audytem — wlasciwym
mechanizmem jest ukryty pack jest (fail-closed), jak w E1. Zaden element werdyktu
nie wymaga oceny „na oko" ani nie opiera sie na tym, co ramie o sobie NAPISZE:
kazda obserwabla jest czytana z checkoutu (zachowanie komendy pod jestem, tresc
migracji, deklaracja encji, liczby z raportu jest, diff plikow testowych).

## Budzet

**L** — uzasadnienie w `notes.md` §Budzet.
