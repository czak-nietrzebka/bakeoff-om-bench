# M1 — SCORING (jak orzekamy werdykt)

## 1. Mechanizm: ukryty pack jest (fail-closed)

Pack: 3 pliki w konwencji `apps/mercato/src/modules/loyalty/__tests__/bakeoff/`
(sciezka docelowa = sciezka w packu, dokladnie jak w fazie budowy):

| plik | testy | co orzeka |
|---|---|---|
| `m1-single-credit-command.test.ts` | 4 | reczne naliczenie zamowienia uznanego juz automatycznie; zasieg tenanta; brak regresji naliczania per pozycja + idempotencja; nienaruszalnosc nazw encji |
| `m1-single-credit-event.test.ts` | 3 | droga automatyczna po naliczeniu recznym; zasieg tenanta; brak regresji matematyki i odpornosci na powtorke |
| `m1-single-credit-import.test.ts` | 2 | pozycja importu wskazujaca zamowienie uznane automatycznie; brak regresji regul pomijania i licznikow |

Brama kopiuje pliki packa do checkoutu i odpala celowany jest:

    yarn jest apps/mercato/src/modules/loyalty/__tests__/bakeoff/m1-single-credit-command.test.ts \
              apps/mercato/src/modules/loyalty/__tests__/bakeoff/m1-single-credit-event.test.ts \
              apps/mercato/src/modules/loyalty/__tests__/bakeoff/m1-single-credit-import.test.ts

## 2. Definicja werdyktu

- **verified** = WSZYSTKIE cztery warunki, w tej kolejnosci:
  1. pack M1 zielony (9/9),
  2. wlasna suita modulu `loyalty` zielona, przy czym liczba plikow testowych modulu
     NIE maleje wzgledem stanu przed zadaniem (spadek = czerwona flaga; zanim uznamy
     verified, trzeba recznie potwierdzic, ze przypadki przeniesiono, a nie skasowano),
  3. `yarn typecheck` zielony,
  4. pelna suita repo zielona (definicja bramy jak w fazie budowy).
- **DNF** = budzet wyczerpany albo limit ewaluacji bramy przekroczony, zanim (1)-(4) sa
  zielone jednoczesnie.
- Primary endpoint (identycznie jak w fazie budowy): koszt dojscia do zielonej bramy
  (tokeny robocze / czas scienny / liczba podejsc do bramy) + verified/DNF.
  **Zero ocen na oko.** Zaden element werdyktu nie opiera sie na tym, co sesja NAPISALA
  o stanie repo — liczy sie wylacznie wynik odpalenia packa i bram.

## 3. Fail-closed — rachunek na nietknietych bazach + krok kontrolny

Na obu nietknietych bazach (stan zmierzony 2026-08-27, SHA w `notes.md`) zadna z trzech
drog naliczen nie oglada sladu pozostalych drog: reczne naliczenie i import patrza
wylacznie na wpisy ledgera, droga automatyczna wylacznie na swoje zapisy transakcji
punktowych. Stad **dokladnie 3 z 9 testow sa CZERWONE, a 6 ZIELONYCH** — i to w OBU
bazach:

| test | dzis | zmierzone zachowanie nietknietej bazy |
|---|---|---|
| command: `returns { created: 0 }, leaves the balance alone and writes nothing` | **RED** | `created` = 2 (zamiast 0), saldo 548 (zamiast 300), 2 nowe wpisy ledgera |
| command: `still accrues when the only earlier credit belongs to another tenant` | GREEN | slad obcego tenanta ignorowany, `created` = 2, saldo 248 |
| command: `accrues per qualifying line ... idempotent on replay` | GREEN | 169 + 79, saldo 248, powtorka `created` = 0 |
| command: `keeps the existing accrual record types under their existing names` | GREEN | encje eksportowane pod dotychczasowymi nazwami |
| event: `completes without throwing, leaves the balance alone and writes nothing` | **RED** | saldo 325 (zamiast 300), 1 nowy zapis (zamiast zera) |
| event: `still credits when the only earlier credit belongs to another tenant` | GREEN | +25 |
| event: `credits the order exactly as before ... repeated notice` | GREEN | +25, powtorka bez zapisu |
| import: `skips the already-credited order, imports the untouched one ...` | **RED** | `imported` = 2, `skipped` = 0 (zamiast 1/1), saldo 349 (zamiast 100) |
| import: `keeps skipping guest items, non-accruable amounts and duplicates ...` | GREEN | `{ imported: 1, skipped: 3 }` |

Testy zielone-dzis nie sa wypelniaczem: to bramy anty-regresyjne i anty-nadgorliwosc
(fix, ktory zaczyna blokowac naliczenia po samym numerze zamowienia, bez tenanta, albo
psuje matematyke ktorejkolwiek drogi, zapala je na czerwono).

**Rozklad zweryfikowany SUCHYM PRZEBIEGIEM, nie oszacowany.** `klucz/dryrun_simulate.js`
(node, zero zaleznosci) odtwarza harness packa 1:1 i przeportowany przeplyw sterowania OBU
ramion (reczne naliczenie / droga automatyczna / import), po czym odpala scenariusze packa.
Wynik: **A i B nietkniete → RED dokladnie w tych trzech scenariuszach**; **A i B z minimalna
naturalna naprawa** (dolozenie krzyzowego odczytu w trzech miejscach) **→ 8/8 zielonych**
(suchy przebieg pokrywa 8 scenariuszy behawioralnych; dziewiaty test packa — nazwy encji —
jest statyczny i nie ma w nim odpowiednika);
**naprawa BEZ zasiegu tenanta** (dopasowanie po samym numerze zamowienia) **→ czerwone
dokladnie dwie bramy "foreign-tenant"** w obu ramionach. To domyka trzy pytania naraz:
zadanie jest wykonalne, luka jest symetryczna, a testy zielone-dzis realnie gryza.

Suchy przebieg mierzy takze **DRUGI, rownie legalny ksztalt naprawy**: droga automatyczna
dokladajaca przy naliczeniu wpis ledgera, zeby trzy drogi zbiegly sie na jednym, czytelnym
sladzie (wym. 3 pozwala DODAWAC zapisy przy nowych naliczeniach). Wynik: **8/8 zielonych
w obu ramionach** — pack orzeka zachowanie, nie wybiera projektu. Kontrola przeciwna,
zeby poluzowana asercja nie stala sie stemplem: dwie atrapy naprawy bez TRWALEGO sladu
(deduplikacja w pamieci procesu; zapis nieopatrzony numerem zamowienia) **zapalaja
dokladnie brame regresji drogi automatycznej** w obu ramionach.

Suchy przebieg NIE zastepuje pilota packa jako pliku jest w prawdziwym repo (rozwiazywanie
modulow, transform, nazwy klas encji po kompilacji) — patrz `notes.md` §7.1.

**KROK KONTROLNY ORKIESTRATORA (przed startem ramion):** odpal pack na NIETKNIETYCH
checkoutach obu ramion i potwierdz DOKLADNIE ten rozklad (3 RED / 6 GREEN, te same trzy
testy) w OBU. Kazde odstepstwo = blad projektanta packa, **STOP** — w szczegolnosci
zielony test "already credited" na nietknietej bazie oznaczalby, ze luka NIE jest
symetryczna i wynik bylby nieinterpretowalny.

## 4. Feedback po czerwonej bramie

Zamrozony format (`feedback-format.md`), bez zmian:

    <test-id> :: <pierwsza linia komunikatu asercji, max 200 znakow>

Zero tresci testow, zero sciezek packow, zero stack-trace, identycznie dla obu ramion.

## 5. Symetria pomiaru (dlaczego pack nie faworyzuje zadnego ramienia)

- **Zero nazw prywatnych w packu.** Komendy adresowane po id z rejestru
  (`loyalty.accruals.accrueOrder`, `loyalty.accruals.bulkImport`), a droga automatyczna
  wylacznie przez DISCOVERY katalogu `subscribers/` po `metadata.event` — bazy nazywaja
  ten plik roznie (`order-completed-points.ts` vs `order-completed-points-accrual.ts`),
  wiec import po nazwie pliku zlamalby symetrie. Mechanizm discovery przeniesiony 1:1
  z zamrozonego packa T3, ktory oba ramiona juz przechodzily.
- **Pack ZAWSZE seeduje konto lojalnosciowe.** Kolejnosc lookupu konta wzgledem filtracji
  pozycji i sprawdzenia idempotencji NIE byla przybita w fazie budowy i rozni sie miedzy
  ramionami (A: pozycje → suma → sprawdzenie → konto; B: konto → sprawdzenie → stawka →
  pozycje). Z zasianym kontem oba porzadki daja identyczne obserwacje, wiec pack nie
  orzeka po niepinowanym wymiarze.
- **Brak konfiguracji stawki w kontenerze** (Proxy zwracajacy `undefined`) → oba ramiona
  spadaja na wspolny default 1 punktu za pelna jednostke netto; matematyka packa to
  `floor` kwoty netto pozycji.
- **Zero asercji na ksztalt bledu.** Ramiona roznia sie stylem (`new CrudHttpError(404, …)`
  vs helper `notFound(…)`); M1 nie dotyka sciezek bledow, wiec ta roznica nie ma wplywu.
- **Zasiane slady historyczne niosa OBA odniesienia** (konto i klient), bo ramiona
  zapisuja je roznie; rozstrzygajacym kluczem pozostaje para (tenant, zamowienie), ktora
  obie bazy juz dzis stosuja w swoich wlasnych sciezkach.
- **Zero pinowania LICZBY zapisow, ktore zostawia legalne naliczenie.** Bramy regresji
  pilnuja tego, co kontrakt nazywa (matematyka, liczniki, wpisy ledgera per pozycja,
  brak nowych zapisow przy probie, ktora nie uznaje salda) oraz tego, ze uznanie zostawia
  TRWALY slad opatrzony para (tenant, zamowienie) — ale nie tego, ile wierszy i w ktorej
  tabeli powstaje. Inaczej ramie, ktore skonwerguje slad trzech drog, dostaloby czerwien
  za projekt dozwolony wym. 3, a drugie ramie nie — przy nieinformatywnym feedbacku
  bramy byloby to nie do odroznienia od realnego bledu.
- **Fake store nie ma ograniczen unikalnosci** — implementacja opierajaca sie na
  odrzuceniu zapisu przez baze (zamiast na odczycie przed zapisem, spec req. 4) duplikuje
  wiersze i pada. Tak samo bylo w packach fazy budowy.

## 6. Uwaga o regresji przez packi fazy budowy

Do M1 **nie dokladamy** zamrozonego packa T8 jako dodatkowej bramy regresji: przybija on
matematyke sprzed zmiany wymagan T5 (naliczenie od sumy calego zamowienia) i jest juz
dzis czerwony na obu bazach po fazie budowy. Regresje kontraktow, ktorych M1 dotyka,
niosa testy zielone-dzis w samym packu M1 (tabela w §3) plus wlasna suita modulu, ktora
brama i tak odpala.

## 7. Endpointy wtorne (obserwacje, ZERO wplywu na werdykt — R8)

- **Koszt FAZY POSZUKIWANIA** (od startu sesji do pierwszej edycji pliku, ktory faktycznie
  niesie naprawe) — to jest wlasciwy pomiar tezy M1: zgloszenie jest w jezyku biznesu i
  NIE wskazuje miejsca w kodzie ani tego, ze drogi zapisuja slad w dwoch roznych miejscach.
- **Ksztalt naprawy**: jedno wspoldzielone rozstrzygniecie reuzyte przez trzy drogi vs trzy
  kopie tej samej logiki; notowane jako obserwacja intencji, bez wagi.
- **Czy sesja dolozyla migracje danych** (dozwolona, ale nie moze byc nosnikiem poprawnosci
  — spec req. 2) i czy poprawnosc bez niej sie utrzymuje: pack odpowiada na to sam, bo
  biegnie bez migracji.
- **Czy istniejace pokrycie bylo aktualizowane czy kasowane** (spec req. 7): liczba plikow
  testowych modulu i diff w `__tests__` — raportowane opisowo.
- **Checklista konwencji (R8):** obowiazuja punkty wspolne [K1] scoping, [K2] zero
  cross-module ORM, [K4] zero `console.*`, [K5] typecheck, [K6] zero time-bombs. [K3]
  spelnia sie trywialnie (zadanie nie wymaga nowych stringow). Naruszenia spoza listy:
  odnotowane, bez wplywu na werdykt.

## 8. Budzet

Klasa **M**. Uzasadnienie: naprawa dotyka TRZECH sciezek naliczen (reczna, automatyczna,
import) plus wspolnego rozstrzygniecia i wymaga wlasnych testow w trzech obszarach; do
tego dochodzi faza poszukiwania, ktora jest istota pomiaru. Dla porownania M2 (jedna
kategoria wykluczenia w jednym miejscu) to klasa S. Wartosci budzetow pozostaja draftem
kalibrowanym pilotazem — ewentualna korekta przez amendment PRZED runami wlasciwymi.
