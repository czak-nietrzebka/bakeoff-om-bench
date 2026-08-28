# M4 — SCORING (audyt: zamkniety klucz + skrypt porownujacy)

## Mechanizm

Zadanie audytowe — brama NIE odpala jest-packa. Werdykt orzeka skrypt
`klucz/score_audit.py` (python3, stdlib only) porownujacy `AUDIT.md` z checkoutu
z zamknietym kluczem `klucz/answer-key.json`. Klucz i skrypt zyja POZA checkoutem
(wykonawca ich nie widzi); skrypt czyta checkout wylacznie do (a) parsowania
`<checkout>/AUDIT.md`, (b) sprawdzania istnienia plikow z linii `DOWOD:`.

Wywolanie bramy:

    python3 klucz/score_audit.py --repo <checkout-root> --arm a|b

Wyjscie: JSON na stdout; przy werdykcie czerwonym linie feedbacku w formacie K5
(`M4.<atom> :: <symptom>`, zgodnie z `feedback-format.md` — symptom bez tresci
klucza, symetrycznie dla obu ramion) dodatkowo na stderr.
Exit code: `0` = verified, `1` = scored-not-verified, `2` = DNF.

## Snapshot, wzgledem ktorego klucz jest prawda (PRZYPIETY)

Klucz orzeka o faktach zmierzonych 2026-08-27T06:11:45Z; digesty przeliczone
ponownie 2026-08-27 (odczyt read-only) i zgodne co do znaku:

| ramie | ref | `module_sha256` | `module_content_sha256` | plikow |
|---|---|---|---|---|
| A | brak commitow wlasnych; upstream base `15ffbe30c` + niezacommitowane drzewo robocze | `a538aa9b…a746f4` | `abc02a78…c61f50` | 70 |
| B | `bakeoff/p1` @ `839a590f7cf724583668244f7b10bbb3133f8bb5` (T12) | `1b3b5c72…4fbfe6c` | `3c900bef…170625` | 56 |

Digesty liczy sie DOKLADNIE tak — z korzenia checkoutu, ze sciezka modulu
zapisana bez `./` (nazwy plikow wchodza do pierwszego skrotu, wiec inny zapis
TEJ SAMEJ sciezki daje inny digest, a wiec falszywy alarm):

    cd <checkout-root>
    find apps/mercato/src/modules/loyalty -type f | LC_ALL=C sort \
      | xargs sha256sum | sha256sum      # -> module_sha256
    find apps/mercato/src/modules/loyalty -type f | LC_ALL=C sort \
      | xargs cat | sha256sum            # -> module_content_sha256

Drugi skrot jest niezalezny od zapisu sciezki i sluzy jako kontrola krzyzowa:
rozjazd `module_sha256` przy ZGODNYM `module_content_sha256` i zgodnej liczbie
plikow znaczy „policzyles inaczej", nie „baza sie zmienila". Oba siedza w
`answer-key.json` w polu `snapshot` i wracaja w JSON bramy jako `key_snapshot`.

**KROK KONTROLNY ORKIESTRATORA (przed startem ramion):** przelicz oba digesty w
obu checkoutach i porownaj z tabela. **Rozjazd tresci = STOP.** Klucz opisuje
wtedy stan, ktorego w checkoucie nie ma, a bramka zaczyna nagradzac opis
nieistniejacej rzeczywistosci — dokladnie ten defekt (klucz B zadal „BRAK" dla
artefaktow, ktore w B juz byly) unieruchomil poprzednia wersje tego zadania.
Snapshot rusza → przegenerowanie klucza przez amendment PRZED runami, nie w trakcie.

## Jednostka pomiaru: atom faktu

Klucz zawiera **45 atomow** — kazdy atom to jeden weryfikowalny fakt (zestaw
regexow, ktore WSZYSTKIE musza trafic w tekst wlasciwej sekcji; tekst jest
normalizowany: lowercase + zdjete diakrytyki). Atomy przypisane sa do sekcji
A1-A11; atomy sekcji A9 celuja w pojedyncze linie `A9a:`-`A9f:`.

- **32 atomy wspolne** (`all`) — fakt identyczny w obu bazach.
- **13 atomow per ramie** (`all_a` / `all_b`) — fakt, ktory w bazach RZECZYWISCIE
  sie rozni, zweryfikowany grepem po obu drzewach (lista i dowody: `notes.md` §2):
  nazwa pliku subskrybenta · nazwa migracji `order_line_id` · nazwa zdejmowanego
  wymuszenia unikalnosci · nazwa indeksu zastepczego · nazwa migracji `expires_at` ·
  nazwa migracji backfillu · nazwa unikalnego indeksu transakcji punktowych ·
  nazwa migracji zasiewajacej stawke · trzy powierzchnie integracyjne A9 (widget
  karty klienta, serwis w kontenerze, endpoint podsumowania) · nazwa funkcji
  guarda · sposob sygnalizacji bledu przez guarda.
- **8 atomow z tagiem `dlog`** — podzbior pytan klasy „ktora zmiana wprowadzila X
  i po co"; skrypt raportuje `dlog_score`/`dlog_max` osobno.
- Skrypt raportuje takze `arm_specific_score`/`arm_specific_max` — ile z 13 faktow
  ROZNICUJACYCH ramie trafilo. To bezposredni pomiar „czy audyt zmierzyl SWOJA
  baze, czy opisal ja z pamieci" — i od tej wersji nie tylko metryka, ale i
  warunek werdyktu (nizej).

Tekst sekcji brany do dopasowania **obejmuje takze linie `DOWOD:`** — nazwa pliku
podana jako dowod jest pelnoprawnym stwierdzeniem tego samego faktu. Wlasnosc
zadeklarowana swiadomie (nie gotcha „dobra nazwa, zla linia"); atomy nie-plikowe
(nazwy ograniczen, indeksow, funkcji, klas bledu) i tak wymagaja tresci sekcji,
bo nie wystepuja w zadnej sciezce.

## Bramki waznosci sekcji (fail-closed)

Sekcja jest scoringowana TYLKO gdy jednoczesnie:

1. istnieje (`## A<n>`),
2. ma <= 1800 znakow (spec mowi ~1200; 1800 to twardy limit — chroni przed
   wklejeniem calego kodu, zeby regexy trafily „za darmo"; oba raporty wzorcowe
   miesca sie w 1196 znakach na najdluzszej sekcji),
3. jest **UGRUNTOWANA**: wskazuje **co najmniej JEDNA istniejaca** sciezke i
   **zadna** z podanych sciezek nie jest zmyslona.

Stany sekcji w JSON: `ok` · `too-long` · `fabricated` (jakas sciezka nie istnieje
w tym checkoucie albo prowadzi poza niego) · `no-path` (linia `DOWOD:` bez
sciezki) · `brak-only` (`DOWOD:` deklaruje BRAK zamiast wskazac plik) ·
`missing` (brak linii `DOWOD:`) · `absent` (brak sekcji). Wszystko poza `ok`
uniewaznia sekcje: zero punktow za jej fakty.

**`BRAK` nie jest wylacznikiem bramy.** Poprzednia wersja zwracala `ok`, gdy
linia `DOWOD:` zawierala slowo „brak" i zadnej sciezki — czyli hedge wylaczal
CALE gruntowanie. Zmierzone na tamtej wersji: raport wzorcowy B z kazda linia
`DOWOD:` podmieniona na `DOWOD: BRAK` dostawal **45/45 i werdykt zielony**, a
raport ramienia A wklejony do repo B z tym samym zabiegiem skakal z 11/45 na
32/45. Dzis oba warianty daja **0/45** (wszystkie 11 sekcji `brak-only`).
Jedyny wyjatek jest waski i jawny w specu: sekcja A9, gdy WSZYSTKIE szesc
pod-odpowiedzi brzmi czyste `BRAK` — czyli gdy naprawde nie ma na co wskazac.
Wyjatek nie odpala sie w zadnej z dzisiejszych baz (obie maja `search.ts`,
`ce.ts`, `data/extensions.ts`), jest tam dla poprawnosci reguly, nie dla wygody.

**Sciezka musi lezec w AUDYTOWANYM checkoucie.** `..` jest odrzucane, a sciezka
po normalizacji musi rozwiazywac sie wewnatrz korzenia (`resolve()` +
`is_relative_to`). Bez tego `../<sciezka>` przechodzilo jako dowod — a w ukladzie
benchu oba checkouty sa katalogami-siostrami, wiec ramie mogloby „udowodnic"
wlasny fakt plikiem z CUDZEJ bazy. Zlapane wlasnym testem brzegowym, nie w
teorii: czyszczenie interpunkcji zjadalo kropki i `../apps/...` stawalo sie
`apps/...`. Tokeny prozy (`(linie`, `patrz`) sa nadal ignorowane — bramkujemy
prawdziwosc dowodu, nie interpunkcje; wiodace `./` i `/` normalizowane do
sciezki wzglednej (wiec `/etc/passwd` przepada jako dowod, zamiast wyjsc poza
checkout).

## A9: zdanie samo-sprzeczne nie punktuje po ZADNEJ stronie

Pod-odpowiedzi A9 to jedyne miejsce, gdzie `BRAK` jest pelnoprawna odpowiedzia —
i wlasnie dlatego bylo tam najlatwiej o hedge. Linia typu
`A9a: TAK search.ts, ce.ts, extensions.ts; poza tym BRAK` trafiala JEDNOCZESNIE
atom twierdzacy i przeczacy, bo przeczenie kotwiczylo sie na golym `\bbrak\b`
gdziekolwiek w linii. Zmierzone na tamtej wersji: raport wygenerowany WYLACZNIE
z listingu plikow (zero czytania tresci) zbieral dla ramienia B **komplet 6
atomow A9**, w tym trzy roznicujace; opis CUDZEJ bazy z takim hedgem dochodzil
do **35/45** przy progu 36 — deklarowany margines 4 atomow byl realnie jednym.

Dwie kotwice zamykaja to w obie strony:

- atom przeczacy wymaga, zeby odpowiedz **zaczynala sie** od przeczenia:
  `^\s*a9<x>\s*:\s*brak\b` — linia prowadzaca sciezkami przepada;
- atom twierdzacy wymaga, zeby w linii **nie bylo** slowa `brak`:
  `^(?!.*\bbrak\b)` — linia asekuracyjna przepada tak samo.

Efekt zmierzony: hedge we wszystkich szesciu liniach daje **0 z 6** atomow A9
(zamiast 6 z 6), a JSON bramy raportuje `a9_hedge_lines` — ile pod-odpowiedzi
mowilo naraz „jest" i „nie ma". Licznik jest telemetria, nie kara: hedge kosztuje
utracone atomy, nie dodatkowy mnoznik. Kontrakt jest jawny w specu („nigdy jedno
i drugie w tej samej linii"), wiec to regula gry, nie pulapka.

## Werdykt

- **DNF**: brak `AUDIT.md` w korzeniu checkoutu, plik > 32 KB, albo mniej niz
  8 z 11 sekcji `## A1..## A11` (struktura nieczytelna) — exit 2.
- **verified**: status `scored` i **trzy warunki NARAZ** (`verdict_gates` w JSON) — exit 0:
  1. `score >= 36/45` (80%),
  2. `arm_specific_score >= 4` — co najmniej cztery fakty, ktorych nie da sie
     podac bez otwarcia WLASNEJ bazy,
  3. `sections_present == 11` — komplet odpowiedzi.
- **scored-not-verified**: policzone, ponizej ktoregokolwiek warunku — ramie
  dostaje feedback K5 i moze poprawic raport (standardowa petla E-MAINT: koszt
  do zielonej bramy) — exit 1.

**Dlaczego trzy warunki, a nie sam prog.** Kazdy z pozostalych dwoch zamyka droge
na skroty, ktora sam prog punktowy zostawial otwarta — obie zmierzone, nie
przewidziane:

- *bez warunku 2*: opis cudzej bazy z hedgem A9 dochodzil do 35/45, o jeden atom
  od progu; kazda przyszla inflacja atomow wspolnych zjadalaby ten margines dalej.
  Warunek 2 zapisuje WPROST intencje, ktora wczesniej byla tylko arytmetyczna;
- *bez warunku 3*: raport odpowiadajacy idealnie na 8 z 11 pytan (pominiete A6,
  A7, A10) dawal **dokladnie 36/45** — czyli prog dalo sie osiagnac, nie
  odpowiadajac na trzy pytania. Dzis taki raport konczy czerwono na bramie
  `sections`, ze wskazaniem brakujacych sekcji w feedbacku.

**Skad prog 36.** Sufit dla raportu opisujacego CUDZA baze przy neutralizowanym
groundingu wynosi 32/45 — zmierzone w OBU kierunkach (§cross-check). Prog 36 lezy
4 atomy nad tym sufitem i zostawia 9 atomow luzu na slepe plamy prawdziwego audytu.

## Cross-check dyskryminacji i odpornosci — zmierzone, oba kierunki

Wzorcowe raporty prawdy dla obu baz + fake-repo odwzorowujace PELNE drzewa plikow
obu modulow (70 i 56 pustych plikow pod prawdziwymi sciezkami), zeby
grounding-gate dzialal realistycznie. Warsztat i konstrukcja: `notes.md` §4.

| przebieg | score | arm-spec | dlog | sekcje | werdykt |
|---|---|---|---|---|---|
| raport-prawda A / klucz A / repo A | **45/45** | 13/13 | 8/8 | 11/11 | ZIELONY |
| raport-prawda B / klucz B / repo B | **45/45** | 13/13 | 8/8 | 11/11 | ZIELONY |
| raport A / klucz B / repo B (naiwny) | 11/45 | 0/13 | 0/8 | 11/11 | czerwony |
| raport B / klucz A / repo A (naiwny) | 17/45 | 0/13 | 0/8 | 11/11 | czerwony |
| fakty A / klucz B, DOWODy poprawne w B (twardy) | **32/45** | 0/13 | 3/8 | 11/11 | czerwony |
| fakty B / klucz A, DOWODy poprawne w A (twardy) | **32/45** | 0/13 | 3/8 | 11/11 | czerwony |
| fakty A + hedge A9 / klucz B (atak 1) | 29/45 | 0/13 | 3/8 | 11/11 | czerwony |
| fakty B + hedge A9 / klucz A (atak 1) | 29/45 | 0/13 | 3/8 | 11/11 | czerwony |
| raport z samego listingu plikow + hedge A9 / klucz B | 11/45 | 5/13 | 4/8 | 11/11 | czerwony |
| sufit „zero czytania tresci" (sam listing, poprawne A9) | **17/45** | 8/13 | 4/8 | 11/11 | czerwony |
| wzorzec B z `DOWOD: BRAK` wszedzie (atak 2) | **0/45** | 0/13 | 0/8 | 11/11 | czerwony |
| fakty A w repo B z `DOWOD: BRAK` (atak 2) | **0/45** | 0/13 | 0/8 | 11/11 | czerwony |
| prawda B, ale 8 z 11 pytan (atak 3) | 36/45 | 13/13 | 8/8 | 8/11 | czerwony (`sections`) |
| fakty wspolne + wlasny listing B (najmocniejszy atak) | 40/45 | 8/13 | 7/8 | 11/11 | **ZIELONY** |

Wariant „naiwny" = raport przeniesiony verbatim: sciezki cudzej bazy nie istnieja,
wiec grounding-gate uniewaznia po 5-7 sekcji. Wariant „twardy" neutralizuje
grounding (linie `DOWOD:` podmienione na sciezki istniejace w bazie docelowej),
zeby zmierzyc SAMA dyskryminacje faktow — i jest **symetryczny co do atomu**:
32/45 w obie strony, pudlo dokladnie na 13 atomach roznicujacych.

**Ostatni wiersz deklarujemy WPROST, bo przechodzi.** Raport zlozony z 32 faktow
wspolnych plus poprawek wyczytanych z wlasnego listingu (nazwy migracji, nazwa
subskrybenta, obecnosc trzech powierzchni A9) osiaga 40/45 i jest zielony. To NIE
jest luka, tylko granica tego, co ta brama mierzy: 32 fakty wspolne sa do zdobycia
**wylacznie przez przeczytanie TRESCI modulu** (stale, formuly, identyfikatory
feature'ow ACL, kanaly notyfikacji — nic z tego nie widac w `ls`), a jedyna tresc,
do ktorej ramie ma dostep, to jego wlasna baza. Brama nie odroznia agenta, ktory
przeczytal modul, ale nie otworzyl cial migracji (traci 5 atomow nazw ograniczen
i indeksow), od agenta idealnego — i nie ma takiej ambicji. Sufit dla agenta,
ktory nie przeczytal ANI JEDNEGO pliku, wynosi **17/45**: prog jest nieosiagalny
bez czytania tresci wlasnej bazy.

## Pomiar decision-logu (WPROST, z uczciwym dnem)

Podzbior `dlog` (8 atomow: `a3.migration`, `a3.dropped-name`, `a3.unique-drop`,
`a3.nullable-why`, `a4.migration`, `a4.backfill-migration`, `a5.durable`,
`a8.seed-migration`) to pytania klasy „ktora zmiana wprowadzila X i po co" —
odpowiedz jest do odczytania albo ze sladu decyzyjnego, albo z inzynierii
wstecznej plikow migracji. Skrypt raportuje `dlog_score`/`dlog_max` osobno.

**Dno tej skali jest wysokie i trzeba je odjac przy interpretacji:** cztery z
osmiu atomow `dlog` to NAZWY PLIKOW migracji, ktore widac w samym listingu —
zmierzone: raport bez czytania czegokolwiek dostaje **dlog 4/8**. Informacyjna
jest dopiero czesc powyzej 4 (`a3.dropped-name`, `a3.unique-drop`,
`a3.nullable-why`, `a5.durable`), bo tylko ona wymaga otwarcia plikow.
UWAGA: oba ramiona MOGA zdobyc komplet dlog-atomow (wszystkie fakty leza w
plikach; sprawdzone — komentarz „czemu nullable" jest w `data/entities.ts` w OBU
bazach). Mierzymy koszt i trafnosc, nie mozliwosc.

## Budzet

Klasa **M** (`token_budget_robocze` 800 000, `task_budget_usd` 3.0,
`dnf_max_iterations` 5 wg `frozen/budgets.json`).

Uzasadnienie: M4 nie pisze kodu, ale wymaga PRZECZYTANIA calego modulu —
70 plikow w A, 56 w B, w tym 7 migracji, encje, 4 komendy, subskrybenci, ACL,
routy i biblioteki — oraz wyprodukowania 45 dokladnych identyfikatorow (nazwy
ograniczen i indeksow bazodanowych da sie podac tylko po otwarciu migracji).
To zakres czytania porownywalny z taskiem klasy M fazy budowy (T5/T6/T8), przy
zerowym koszcie pisania. Klasa S (300 000) jest za ciasna: przy dopuszczonych
5 iteracjach i swiezej sesji per iteracje sam recon zjadlby budzet po dwoch
podejsciach i produkowalby DNF-tokenowe z powodu petli bramy, nie z powodu
trudnosci zadania. Klasa L jest nieuzasadniona — nie ma tu buildu, migracji ani
suity do zazielenienia. Wartosc jest draftem kalibrowanym pilotazem, jak kazdy
budzet fazy (korekta przez amendment PRZED runami wlasciwymi).

## Definicje i metryki

- **verified** = exit 0 (trzy warunki werdyktu spelnione naraz).
- **DNF** = exit 2 albo wyczerpanie budzetu klasy M / 5 ewaluacji bramy bez
  werdyktu verified.
- **Primary endpoint** (identycznie jak E1): koszt dojscia do verified — tokeny
  robocze, czas scienny, imputacja USD, liczba podejsc do bramy.
- **Secondary** (z JSON-a bramy, zero uznaniowosci): `score` 0-45,
  `arm_specific_score` 0-13, `dlog_score` 0-8 (interpretowac ponad dnem 4 —
  patrz wyzej), `sections_ok`, `sections_invalid`, `dowod_brak_sections`,
  `a9_hedge_lines`.
- **Czym jest licznik sekcji uniewaznionych (`fabricated` / `no-path` /
  `brak-only` / `missing`) — i czym NIE jest.** To **dolne oszacowanie**
  halucynacji o stanie repo, nie ich dokladna liczba: brama sprawdza, czy
  wskazany plik ISTNIEJE, nie czy jest wlasciwy. Raport podpierajacy kazda sekcje
  prawdziwym, ale nie na temat plikiem bedzie mial ten licznik na zerze — nie
  zyska na tym ani jednego atomu, ale metryki nie wolno czytac jako „tyle razy
  zmyslil". `dowod_brak_sections` (ile sekcji uchylilo sie slowem BRAK) i
  `a9_hedge_lines` (ile pod-odpowiedzi mowilo naraz „jest" i „nie ma") sa
  raportowane osobno wlasnie dlatego, ze to inna klasa zachowania niz zmyslona
  sciezka i nie wolno ich mieszac w jedna liczbe.
- **Warunek dodatkowy do verified, egzekwowany na poziomie bramy fazy** (nie tego
  skryptu): diff checkoutu wzgledem stanu pre-task zawiera WYLACZNIE `AUDIT.md`.
  Audyt czyta, nie pisze; zmiana kodu pod raport = werdykt niewazny.
- Checklista konwencji R8: dla M4 nie stosuje sie (zero zmian w kodzie, zero
  nowych stringow); [K5] typecheck pozostaje trywialnie zielony, bo drzewo kodu
  jest nietkniete.
