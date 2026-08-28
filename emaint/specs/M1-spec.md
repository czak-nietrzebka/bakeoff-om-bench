# ZADANIE M1

## Cel

Program lojalnosciowy (`apps/mercato/src/modules/loyalty/`) nalicza dzis punkty za
zamowienia sprzedazy TRZEMA drogami: automatycznie po zakonczeniu zamowienia,
recznie (operator wsparcia nalicza wskazane zamowienie) oraz importem naliczen
historycznych. Ze wsparcia przyszly trzy zgloszenia z produkcji. Wszystkie sa tej samej
klasy: **to samo zamowienie uznalo saldo klienta wiecej niz raz**.

**Zgloszenie #1 — dubel po recznym naliczeniu.** Zamowienie SO-4172 (dwie pozycje: 169.99
i 79.99 netto, razem 249.98) po zakonczeniu dostalo automatycznie 25 punktow. Klient
napisal, ze punktow nie widzi; operator wsparcia — nie wiedzac o naliczeniu automatycznym —
uruchomil naliczenie reczne dla TEGO SAMEGO zamowienia. Konto dostalo DODATKOWE 248
punktow, razem 273 za jedno zamowienie. Wsparcie oczekiwalo, ze druga proba skonczy sie
informacja "nic do naliczenia".

**Zgloszenie #2 — dubel przy imporcie historii.** Import naliczen historycznych za styczen
objal takze zamowienia, ktore przy zakonczeniu dostaly punkty automatycznie. Kazde z nich
zostalo uznane drugi raz i salda podskoczyly. Ponowne uruchomienie SAMEGO importu nie
dubluje (to sprawdzono) — dubel powstaje wylacznie krzyzowo, wobec naliczen automatycznych.

**Zgloszenie #3 — dubel po spoznionym zdarzeniu.** Zamowienie naliczone najpierw recznie
przez operatora dostalo po kilku godzinach ponowne, spoznione powiadomienie o zakonczeniu
(powiadomienia sa dostarczane co najmniej raz, wiec powtorki sa normalne) — i automat uznal
je drugi raz.

**Oczekiwanie biznesu:** jedno zamowienie uznaje saldo klienta **najwyzej RAZ** — niezaleznie
od tego, ktora droga naliczyla jako pierwsza i w jakiej kolejnosci przychodza kolejne proby.

Znajdz przyczyne, napraw i pokryj testami. **Matematyka poszczegolnych drog jest POZA
ZAKRESEM** — ile punktow nalicza dana droga, gdy jest PIERWSZA, zostaje dokladnie takie,
jakie jest dzisiaj; tego nie wolno zmieniac.

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.
Ten dokument celowo NIE wskazuje miejsca w kodzie ani tego, jak dotychczasowe drogi
zapisuja swoje naliczenia — to czesc modulu, ktory utrzymujesz.

1. **Invariant "jedno uznanie na zamowienie" (nowe zachowanie).** Zamowienie, ktore
   zostalo juz uznane KTORAKOLWIEK z trzech drog, przy kazdej kolejnej probie — dowolna
   droga, w dowolnej kolejnosci — konczy sie bez zmiany salda i bez zadnego nowego zapisu:
   - reczne naliczenie (`loyalty.accruals.accrueOrder`) zamowienia uznanego wczesniej
     automatycznie → wynik `{ created: 0 }`, zero nowych wpisow, saldo nietkniete;
   - import (`loyalty.accruals.bulkImport`): pozycja wskazujaca zamowienie uznane wczesniej
     automatycznie → liczona do `skipped`, zero zapisow dla tej pozycji;
   - droga automatyczna (obsluga zakonczenia zamowienia) dla zamowienia uznanego wczesniej
     recznie albo importem → konczy sie bez wyjatku, bez zmiany salda i bez zadnego nowego
     zapisu.
   Proba, ktora nie uznaje salda, nie zostawia ZADNEGO nowego zapisu — takze zadnego wpisu
   "na pamiatke" o pominieciu.

2. **Rozstrzyganie w RUNTIME, na danych zastanych.** "Czy to zamowienie bylo juz uznane"
   rozstrzygasz w momencie wykonania, na danych w takiej postaci, w jakiej zapisaly je
   dotychczasowe drogi naliczen. Poprawnosc NIE moze zalezec od jednorazowego przepisania
   historii: zgloszenia #2 i #3 dotycza zamowien uznanych dawno temu, a system pracuje bez
   przerwy (import i spoznione powiadomienia biegna na zywym systemie). Migracje danych sa
   DODATKOWO dozwolone, ale nie moga byc warunkiem poprawnosci.

3. **Historia jest nienaruszalna.** Zapisy naliczen wykonane dotad przez kazda z drog to
   dane zastane: zero przepisywania, usuwania, przenoszenia ani przemianowywania istniejacych
   encji, tabel i pol modulu. Wolno DODAWAC (kolumny, indeksy, nowe zapisy przy NOWYCH
   naliczeniach). Zmiana schematu ma migracje MikroORM w
   `apps/mercato/src/modules/loyalty/migrations/`.

4. **Rozstrzygniecie PRZED zapisem.** Decyzja "juz uznane / uznaje" zapada na podstawie
   ODCZYTU wykonanego przed zapisem. Nie wolno opierac jej na tym, ze baza odrzuci zapis
   (lapanie bledu ograniczenia unikalnosci).

5. **Zasieg bez zmian.** Rozstrzyganie obowiazuje w obrebie tenanta wykonania: zapis INNEGO
   tenanta dotyczacy tego samego numeru zamowienia NIE moze zablokowac naliczenia. Zadnych
   odczytow ani zapisow poza tenantem/organizacja kontekstu wykonania.

6. **Zero regresji dotychczasowych kontraktow.** Dla zamowienia, ktore nie bylo jeszcze
   uznane zadna droga, kazda droga dziala DOKLADNIE jak dzis. W szczegolnosci bez zmian
   zostaja: matematyka i wykluczenia naliczenia recznego (naliczanie per kwalifikujaca sie
   pozycja zamowienia, wynik `{ created: <liczba wpisow> }`, powiazanie wpisu z pozycja,
   stemplowanie terminu waznosci), matematyka drogi automatycznej wraz z zakladaniem konta
   gdy go brak i odpornoscia na powtorke tego samego powiadomienia (takze po restarcie
   procesu), liczniki importu `{ imported, skipped }` (suma = liczba pozycji) wraz z
   pomijaniem pozycji bez klienta, pozycji nienaliczalnych i duplikatow w obrebie jednej
   paczki, a takze walidacja wejsc, bledy 404 z kluczami i18n i tenant/org-scoping.

7. **Testy wlasne.** Nowe zachowanie pokryte unit testami w
   `apps/mercato/src/modules/loyalty/__tests__/` (styl jak dotychczasowe testy modulu).
   Istniejace testy modulu wolno aktualizowac WYLACZNIE z zachowaniem intencji przypadku
   (nowa wyrocznia + jednozdaniowy komentarz, dlaczego sie zmienila); kasowanie pokrycia
   (usuniecie przypadku zamiast przepisania) jest zabronione.

## Kryteria ukonczenia

- Kazdy z trzech scenariuszy ze zgloszen konczy sie po naprawie pojedynczym uznaniem:
  druga proba (dowolna droga, w dowolnej kolejnosci) nie zmienia salda i nie zostawia
  zadnego nowego zapisu.
- Dotyczy to takze zamowien, ktorych pierwsze uznanie nastapilo PRZED ta naprawa —
  rozstrzygane na danych w postaci, w jakiej sa zapisane, bez zakladania migracji.
- Zamowienie nieuznane zadna droga nalicza sie kazda droga dokladnie tak jak dotad:
  matematyka, wykluczenia i liczniki bez zmian, a zapisy, ktore dana droga robi dzis,
  zachowuja swoj dotychczasowy typ i ksztalt pol. Kontrakt NIE przybija LICZBY zapisow
  powstajacych przy naliczeniu — dolozenie przy okazji nowego zapisu jest dozwolone
  (wym. 3), o ile powyzsze zostaje nietkniete.
- Zapis innego tenanta o tym samym numerze zamowienia nie blokuje naliczenia.
- Istniejace encje, tabele i pola modulu pozostaja pod swoimi dotychczasowymi nazwami.
- `yarn typecheck` i testy modulu zielone; caly istniejacy test-suite repo pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: kazdy odczyt i zapis ograniczony do tenanta/organizacji kontekstu
  wykonania.
- **Zero cross-module ORM**: dane zamowien sprzedazy wylacznie ta droga, ktora robi to
  dzisiejszy kod modulu (tokeny DI); odwolania do rekordow innych modulow wylacznie przez
  pola uuid.
- **i18n x5**: zadanie nie wymaga nowych stringow user-facing; jezeli jakis dodajesz, klucz
  musi trafic do wszystkich 5 locale (en/pl/de/es/ko) przez
  `resolveTranslations().translate(<klucz>, <fallback>)` — zero hardcodow w `throw`.
- **Walidacja przed done**: przed uznaniem zadania za skonczone `yarn typecheck` +
  `yarn jest` modulu + pelna suita repo zielone.
