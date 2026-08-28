# ZADANIE M3

## Cel

Biznes WYCOFUJE naliczanie punktow lojalnosciowych per linia zamowienia. Modul `loyalty`
(`apps/mercato/src/modules/loyalty/`) nalicza dzis punkty za zamowienie sprzedazy komenda
**`loyalty.accruals.accrueOrder`** OSOBNO dla kazdej kwalifikujacej sie linii zamowienia
(linie wysylkowe i zrabatowane w 100% wykluczone), zapisujac jeden wpis ledgera per linia
z odnosnikiem `order_line_id`. Decyzja biznesowa: wracamy do prostszego modelu — punkty
liczone od **SUMY NETTO calego zamowienia** (`grandTotalNetAmount` / kolumna
`grand_total_net_amount` z `sales_orders`), **JEDEN wpis ledgera per zamowienie**, bez
analizy linii i bez wykluczen liniowych.

WSZYSTKIE pozostale zdolnosci modulu maja dzialac dalej bez regresji: konfigurowalna
stawka naliczania, termin waznosci punktow, event awansu tieru z notyfikacja, wspolna
biblioteka matematyki, idempotencja, tenant/org-scoping, typowane bledy i18n. Historia
jest nietykalna: zamowienia juz naliczone — w dowolnym z dotychczasowych modeli — NIE sa
przeliczane ani donaliczane.

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.
Wszystkie sciezki wzgledem korzenia repo; pliki modulu wzgledem
`apps/mercato/src/modules/loyalty/`.

1. **Matematyka od sumy zamowienia.** W komendzie `loyalty.accruals.accrueOrder`:
   - `points = calculateOrderNetPoints(Number(order.grandTotalNetAmount) * rate)` —
     formula WYLACZNIE przez `calculateOrderNetPoints` z `lib/accrual.ts` (jedno zrodlo
     matematyki naliczen: podmiana implementacji tej funkcji MUSI zmieniac wynik
     naliczenia); stawka mnozy kwote PRZED formula (floor PO przemnozeniu, nie przed);
   - `rate` z `resolveOrderRate(container, { tenantId: <tenant kontekstu>,
     organizationId: <organizacja zamowienia> })` z `lib/accrualRate.ts` — precedencja
     org > tenant > default (1) BEZ ZMIAN; zadnej drugiej kopii logiki precedencji;
   - `points <= 0` → `{ created: 0 }`, zero zapisow, bez bledu;
   - zamowienie bez `customerEntityId` (gosc) → `{ created: 0 }`, zero zapisow, bez bledu.

2. **Jeden wpis ledgera per naliczone zamowienie** — encja `LoyaltyLedgerEntry` (tabela
   `loyalty_ledger_entries`), tworzona przez `em.create(...)`, pola co najmniej:
   `points` (int, dodatni, = wynik formuly z pkt 1), `orderId` = id zamowienia,
   `accountId` = id konta, `tenantId`/`organizationId` zgodne z kontekstem. Wpis NIE
   wskazuje zadnej linii zamowienia (los kolumny `order_line_id` — pkt 5).
   `expiresAt` = moment naliczenia + 12 miesiecy kalendarzowych UTC, ustawiany przez
   istniejaca funkcje modulu `computeExpiresAt` z `data/expiry.ts` — nie druga kopie
   tej arytmetyki.

3. **Uznanie salda** — `account.balance = account.balance + points` na wczytanej encji
   + `flush` (konto: `LoyaltyAccount` po `customerId == order.customerEntityId`, w tym
   samym tenant/org, `deletedAt: null`).

4. **Wykluczenia liniowe znikaja razem z modelem per linia.** Kwota bazowa to
   `grandTotalNetAmount` zamowienia takim, jakim jest — linie wysylkowe, rabaty
   czesciowe i pelne NIE sa osobno analizowane ani odejmowane.

5. **Kolumna `order_line_id` — decyzja schematowa nalezy do Ciebie**, obie opcje legalne:
   - (a) kolumna ZOSTAJE (nullable): historyczne wpisy per linia zachowuja swoje
     odnosniki, nowe wpisy maja NULL; zadna migracja nie jest wtedy potrzebna; ALBO
   - (b) kolumna zostaje USUNIETA: NOWA migracja MikroORM w `migrations/`, ktorej `up()`
     zawiera `drop column "order_line_id"` na tabeli `loyalty_ledger_entries`
     (`down()` odtwarza kolumne jako nullable uuid).
   **Encja i migracje musza sie ZGADZAC** — dokladnie jedna z tych dwoch opcji, bez
   stanow posrednich: albo encja `LoyaltyLedgerEntry` nadal DEKLARUJE kolumne i ZADNA
   migracja nie usuwa jej w `up()`, albo encja przestaje ja deklarowac i NOWA migracja
   usuwa ja w `up()`. Usuniecie property bez migracji zostawia osierocona kolumne na
   kazdym wdrozonym srodowisku; usuniecie kolumny migracja przy encji, ktora dalej ja
   mapuje, wywraca kazdy insert.
   **Historia migracji jest APPEND-ONLY**: nie wolno edytowac ani kasowac ZADNEJ
   istniejacej migracji modulu — sa juz wydane na srodowiska; cofniecie schematu to
   zawsze NOWA migracja, nigdy przepisanie historii — w szczegolnosci wydanej migracji,
   ktora DODALA kolumne, nie wolno przerobic ani dopisac jej `drop` w jej wlasnym `up()`.

6. **Idempotencja per zamowienie — bez wyjatkow dla starych wpisow.** JAKIKOLWIEK
   istniejacy wpis ledgera z `orderId` tego zamowienia w tenant/org — takze wpis modelu
   per linia (z ustawionym `order_line_id`) i wpis najstarszego modelu (NULL) — blokuje
   naliczenie: `{ created: 0 }`, zero nowych wpisow, saldo NIETKNIETE. Zamowienia
   naliczone per linia NIE sa przeliczane na model od sumy ani "dorownywane".
   Sprawdzenie PRZED zapisem przez em (`findOne`/`count`); idempotencji nie wolno
   opierac na lapaniu bledu unique constraint.

7. **Walidacja, scoping i bledy — bez zmian:**
   - wejscie `{ orderId: string (uuid) }` walidowane zodem PRZED jakimkolwiek
     odczytem/zapisem; niepoprawne → wyjatek walidacji, zero odczytow i zapisow;
   - zamowienie musi nalezec do tenant/org kontekstu (`ctx.auth.tenantId`,
     `ctx.auth.orgId` / `ctx.selectedOrganizationId`) i miec `deletedAt: null`;
     nieznalezione lub spoza zasiegu → `CrudHttpError(404)` z kluczem
     `loyalty.errors.orderNotFound`; brak konta lojalnosciowego klienta →
     `CrudHttpError(404)` z kluczem `loyalty.errors.accountNotFound`; oba komunikaty
     przez `resolveTranslations`/`translate`, zero zapisow przy bledzie;
   - encje modulu `sales` nadal WYLACZNIE przez tokeny DI
     (`ctx.container.resolve('SalesOrder')`, w razie potrzeby
     `ctx.container.resolve('SalesOrderLine')`); ZAKAZ importu tych encji z
     `@open-mercato/core`; EntityManager z DI, standardowe API em (bez QueryBuildera);
   - wynik `execute` zawiera co najmniej `{ created: number }` — `1` przy naliczeniu,
     `0` przy powtorce/pominieciu.

8. **Event awansu tieru dziala dalej na nowej matematyce.** Gdy naliczenie faktycznie
   zaszlo (`created` >= 1) i saldo przekroczylo prog tieru — DOKLADNIE JEDNA emisja
   `loyalty.tier.changed` przez `eventBus` z DI, z opcjami `{ persistent: true,
   tenantId, organizationId }` i payloadem z tierem KONCOWYM (`newTierName`, ...) oraz
   saldem PO uznaniu; zero emisji przy braku awansu, przy `{ created: 0 }` i przy
   powtorce idempotentnej; awaria emisji nie wywraca naliczenia. Dalszy lancuch
   (subscriber, typ notyfikacji, renderer, i18n) — bez zmian.

9. **Nietykalne pozostale powierzchnie.** Subscriber eventu `sales.order.completed`
   (matematyka `calculateOrderCompletedPoints`), komenda `loyalty.accruals.bulkImport`,
   komendy korekty salda i redeem, API modulu oraz ewentualne powierzchnie odczytowe —
   bez zmian obserwowanego zachowania. Caly istniejacy test-suite repo ma byc zielony
   po Twoich zmianach.

10. **Swiadoma aktualizacja istniejacych testow.** Testy modulu przybijajace matematyke
    per linia aktualizujesz do nowego kontraktu: kazdy zmieniony przypadek ZACHOWUJE
    swoja intencje (co bylo testowane), dostaje nowa wyrocznie i 1-zdaniowy komentarz,
    dlaczego wyrocznia sie zmienila. KASOWANIE pokrycia (usuniecie przypadku zamiast
    przepisania) jest zabronione. Nowe testy wlasne pokrywaja: matematyke od sumy
    (floor, stawka), pojedynczy wpis z `expiresAt`, idempotencje z wpisami per linia
    i z wpisem NULL, przypadki puste (suma <= 0, gosc).

## Kryteria ukonczenia

- Naliczenie zamowienia (z dowolnym ukladem linii) tworzy DOKLADNIE JEDEN wpis ledgera:
  `points = floor(suma netto zamowienia * stawka)`, bez wskazania linii, z `expiresAt`
  ~ teraz + 12 miesiecy (UTC, miesiace kalendarzowe); saldo konta uznane o te sama
  liczbe; wynik `{ created: 1 }`.
- Stawka konfigurowana dalej dziala: nadpisanie org → `floor(suma * stawka_org)`;
  mnozenie wchodzi PRZED floor; brak konfiguracji → zachowanie ze stawka 1.
- Zamowienie z JAKIMKOLWIEK istniejacym wpisem ledgera (takze per linia, takze NULL)
  → `{ created: 0 }`, zero nowych wpisow, saldo bez zmian.
- Suma <= 0 oraz gosc → `{ created: 0 }`, zero zapisow, bez bledu; nieznane / cudze
  zamowienie → 404 `loyalty.errors.orderNotFound`; brak konta → 404
  `loyalty.errors.accountNotFound`; walidacja zod przed jakimkolwiek odczytem.
- Awans tieru emituje dokladnie jeden `loyalty.tier.changed` z tierem koncowym i saldem
  po uznaniu; brak awansu / powtorka → zero emisji.
- Zadna istniejaca migracja modulu nie zostala zmieniona ani usunieta (migracja, ktora
  dodala `order_line_id`, nadal dodaje ta kolumne w swoim `up()` i nic w tym `up()` jej
  nie usuwa); deklaracja encji i migracje sa spojne w rozumieniu pkt 5 — ewentualne
  usuniecie kolumny ma wlasna NOWA migracje z pkt 5(b).
- Zaden istniejacy przypadek testowy nie zostal usuniety; przypadki przybijajace model
  per linia maja nowe wyrocznie z komentarzem.
- `yarn typecheck` i testy modulu zielone; caly istniejacy test-suite repo pozostaje
  zielony.

## Konwencje

- **Tenant/org-scoping**: kazdy odczyt i zapis (zamowienie, konto, ledger, tiery)
  ograniczony do tenanta/organizacji kontekstu.
- **Zero cross-module ORM**: encje `sales` wylacznie przez tokeny DI; odwolania do
  rekordow innych modulow wylacznie przez pola uuid.
- **i18n x5**: klucze bledow bez zmian (`loyalty.errors.orderNotFound`,
  `loyalty.errors.accountNotFound`) — nadal we wszystkich 5 locale (en/pl/de/es/ko);
  to zadanie nie wymaga nowych kluczy; jezeli jakis dodasz, komplet 5 locale i zero
  hardcodow w `throw`.
- **Walidacja przed done**: zod na wejsciu bez zmian; przed uznaniem zadania za
  skonczone `yarn typecheck` + `yarn jest` modulu + pelna suita repo zielona.
