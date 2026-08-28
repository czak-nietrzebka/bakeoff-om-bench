# ZADANIE M2

## Cel

Program lojalnosciowy nagradza punktami rzeczywiste zakupy towarow i uslug. Dlatego
naliczanie punktow za zamowienie sprzedazy w module `loyalty`
(`apps/mercato/src/modules/loyalty/`) ma juz dzis wbudowane wykluczenia: niektore
rodzaje pozycji zamowienia celowo NIE daja punktow, bo nie reprezentuja nagradzanego
zakupu. Biznes rozszerza te polityke o jedna nowa kategorie: **linie korekt** —
pozycje zamowienia typu `adjustment`, dopisywane recznie w celu uporzadkowania
rozliczenia (przesuniecia kwot miedzy pozycjami, wyrownania groszowe, korekty
operatorskie) — od tej pory NIE naliczaja punktow. Korekta nie jest zakupem;
nagradzanie jej punktami pozwalaloby sztucznie podbijac salda kont.

Zadanie utrzymaniowe: rozszerz ISTNIEJACY mechanizm wykluczen naliczania o te
kategorie tak, zeby nowa regula wpisala sie w jego logike i intencje. Ten dokument
celowo NIE cytuje dotychczasowych wykluczen ani miejsca, w ktorym zyja — sa czescia
kodu, ktory utrzymujesz; Twoja zmiana ma pozostawic je w mocy co do joty.

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Nowe wykluczenie** — w naliczaniu punktow za zamowienie sprzedazy per linia
   (komenda **`loyalty.accruals.accrueOrder`**) linia zamowienia z
   **`kind === 'adjustment'`** NIE nalicza punktow i NIE zostawia wpisu w ledgerze.
   Wykluczenie obowiazuje NIEZALEZNIE od kwoty netto linii — takze przy DODATNIM
   `totalNetAmount` (dane historyczne bywaja niespojne) — i niezaleznie od jej rabatu.

2. **Zakres zmiany = dokladnie jedna kategoria.** Do zbioru wykluczen dolacza
   WYLACZNIE `kind === 'adjustment'`. Traktowanie wszystkich pozostalych rodzajow
   linii oraz WSZYSTKIE dotychczasowe wykluczenia pozostaja DOKLADNIE takie, jakie
   sa dzis — zmiana nie moze ani poszerzyc, ani zwezic zadnego z nich.

3. **Kontrakt komendy bez zmian.** Id komendy, wejscie, scoping tenant/org, klucze
   bledow, idempotencja per zamowienie, ksztalt wpisow ledgera (w tym powiazanie
   wpisu z linia zamowienia) oraz pole `created` w wyniku zachowuja sie jak
   dotychczas; `created` nadal rowna sie liczbie linii, ktore FAKTYCZNIE naliczyly
   punkty po wykluczeniach.

4. **Przypadek pusty** — zamowienie, ktorego wszystkie linie sa wykluczone (w tym
   zamowienie zlozone wylacznie z linii `adjustment`), konczy sie `{ created: 0 }`,
   zero zapisow, bez bledu.

5. **Sciezki bez rozroznienia linii bez zmian** — sciezki naliczen, ktore nie
   operuja na liniach zamowienia (np. import naliczen historycznych z kwot calych
   zamowien), pozostaja nietkniete.

6. **Unit testy wlasne** — w `apps/mercato/src/modules/loyalty/__tests__/`:
   nowe wykluczenie (w tym linia `adjustment` z DODATNIA kwota netto),
   wspolistnienie z dotychczasowymi wykluczeniami na zamowieniu mieszanym,
   zamowienie wylacznie z liniami wykluczonymi. Istniejacego pokrycia nie kasujesz;
   jezeli jakis istniejacy test przybija stare zachowanie linii `adjustment`,
   aktualizujesz go SWIADOMIE (nowa wyrocznia + 1-zdaniowy komentarz dlaczego),
   nie usuwasz.

## Kryteria ukonczenia

- Zamowienie z linia `adjustment` (dodatnia kwota netto) i linia produktowa:
  punkty i wpis ledgera WYLACZNIE za linie produktowa; linia `adjustment` bez
  wpisu i bez wplywu na saldo.
- Zamowienie wylacznie z liniami `adjustment` → `{ created: 0 }`, zero zapisow,
  bez bledu.
- Dotychczasowe wykluczenia i zasady naliczania pozostalych rodzajow linii
  dzialaja dokladnie jak przed zmiana: zamowienie mieszane nalicza te same linie
  co dotad, minus linie `adjustment`.
- Powtorne wywolanie dla naliczonego juz zamowienia → `{ created: 0 }`, zero
  nowych wpisow, saldo bez zmian.
- `yarn typecheck` i testy modulu zielone; caly istniejacy test-suite repo
  pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: kazdy odczyt i zapis ograniczony do tenanta/organizacji
  kontekstu.
- **Zero cross-module ORM**: dane zamowien sprzedazy wylacznie ta droga, ktora
  robi to dzisiejszy kod modulu (tokeny DI); odwolania do rekordow innych modulow
  wylacznie przez pola uuid.
- **i18n x5**: zadanie nie wymaga nowych stringow user-facing; jezeli jakis
  dodajesz, klucz musi trafic do wszystkich 5 locale (en/pl/de/es/ko) — zero
  hardcodow.
- **Walidacja przed done**: przed uznaniem zadania za skonczone `yarn jest`
  modulu + pelna suita repo + `yarn typecheck` zielone.
