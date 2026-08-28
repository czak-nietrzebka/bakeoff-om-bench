# M2 — SCORING (jak orzekamy werdykt)

## Mechanizm: ukryty pack jest (fail-closed)

Pack: `pack/apps/mercato/src/modules/loyalty/__tests__/bakeoff/m2-adjustment-exclusion.test.ts`
(1 plik, 4 testy). Brama kopiuje plik packa do checkoutu (sciezka docelowa =
sciezka w packu, dokladnie jak w E1) i odpala celowany jest:

    yarn jest apps/mercato/src/modules/loyalty/__tests__/bakeoff/m2-adjustment-exclusion.test.ts

## Definicja werdyktu

- **verified** = WSZYSTKIE trzy warunki, w tej kolejnosci:
  1. pack M2 zielony (4/4),
  2. wlasna suita modulu `loyalty` zielona (zero skasowanego pokrycia — liczba
     plikow testowych modulu nie maleje wzgledem stanu przed zadaniem; spadek =
     czerwona flaga do recznego potwierdzenia, ze przypadki przeniesiono,
     zanim uznamy verified),
  3. `yarn typecheck` zielony.
- **DNF** = budzet wyczerpany zanim (1)-(3) zielone jednoczesnie.
- Primary endpoint (identycznie jak E1): koszt dojscia do zielonej bramy
  (tokeny / czas / liczba podejsc do bramy) + verified/DNF. Zero ocen na oko.

## Fail-closed — dowod konstrukcyjny + krok kontrolny

Na bazie BEZ zmiany M2 (obie ramiona, stan zmierzony 2026-08-26) kwalifikacja
linii wyklucza wylacznie `kind === 'shipping'` i `discountPercent >= 100`, wiec
linia `adjustment` z dodatnim netto NALICZA punkty i kazdy z 4 testow pada na
pierwszej asercji (`created` / saldo / liczba wpisow):

- test 1: `created` 2 zamiast 1;
- test 2: `created` 1 zamiast 0;
- test 3: `created` 4 zamiast 3;
- test 4: pierwsze wywolanie `created` 4 zamiast 3.

KROK KONTROLNY ORKIESTRATORA (przed startem ramion): odpal pack na NIETKNIETYCH
checkoutach obu ramion i potwierdz 4x RED w OBU. Zielony test na nietknietej
bazie = blad projektanta packa, STOP.

## Feedback po czerwonej bramie

Zamrozony format (feedback-format.md), bez zmian:

    <test-id> :: <pierwsza linia komunikatu asercji, max 200 znakow>

Zero tresci testow, zero sciezek packow, zero stack-trace, identycznie dla obu
ramion.

## Symetria pomiaru (dlaczego pack nie faworyzuje zadnego ramienia)

- Pack ZAWSZE seeduje konto lojalnosciowe — kolejnosc lookupu konta wzgledem
  filtracji linii NIE byla przybita w E1 i rozni sie miedzy ramionami (A liczy
  linie przed lookupem konta, B odwrotnie); z zasianym kontem oba porzadki daja
  identyczne wyniki, wiec pack nie orzeka po niepinowanym wymiarze.
- Brak konfiguracji stawki w kontenerze (Proxy zwracajacy undefined) → oba
  resolvery stawki spadaja na default 1; matematyka packa = floor(netto linii).
- Harness (fake em / DI tokeny / echo-i18n) jest bajt-w-bajt konwencja
  zamrozonych packow E1, ktore oba ramiona juz przechodzily.

## Endpointy wtorne (obserwacje, ZERO wplywu na werdykt — R8)

- Czy nowa kategoria weszla w ISTNIEJACY mechanizm kwalifikacji (ramie A:
  helper `isQualifyingLine`; ramie B: lancuch `.filter()` w accrueOrder), czy
  jako rownolegly, drugi filtr w innym miejscu — notowane jako obserwacja
  intencji, bez wagi w werdykcie.
- Koszt FAZY POSZUKIWANIA (od startu sesji do pierwszej edycji wlasciwego
  pliku) — to jest wlasciwy pomiar tezy M2 (intencja sprzed tygodni): ile
  kosztuje ODTWORZENIE intencji ze swojego swiata (slad vs goly kod).
- Checklista R8: K1 (scoping — bez zmian), K2 (zero cross-module ORM), K5
  (typecheck). K3 trywialnie zielone (zadnych nowych stringow). Naruszenia
  spoza listy: odnotowane, bez wplywu na werdykt.
