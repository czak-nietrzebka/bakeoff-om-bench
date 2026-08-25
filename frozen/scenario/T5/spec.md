# ZADANIE T5

## Cel

Skonsoliduj naliczanie punktow lojalnosciowych za zamowienia sprzedazy jako publiczna,
idempotentna komende modulu `loyalty` (`apps/mercato/src/modules/loyalty/`). Punkty liczone
sa od SUMY NETTO calego zamowienia (`grand_total_net_amount` z `sales_orders`) — 1 punkt za
kazda pelna jednostke waluty, zaokraglenie w dol. Naliczenie zapisuje JEDEN wpis ledgera
(`LoyaltyLedgerEntry`) i uznaje saldo konta (`LoyaltyAccount.balance`) o te sama liczbe
punktow. Ponowne wywolanie dla tego samego zamowienia NIE tworzy duplikatow i NIE uznaje
salda drugi raz. Jezeli czesc tej logiki juz istnieje z wczesniejszej pracy w tej serii,
doprowadz ja DOKLADNIE do ponizszego kontraktu (bez kasowania istniejacego pokrycia testowego).

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Rejestracja i discovery**
   - Kod komendy w `apps/mercato/src/modules/loyalty/commands/` (nazwa pliku dowolna);
     import `apps/mercato/src/modules/loyalty/commands` (przez `commands/index.ts`)
     rejestruje komende side-effectem (`registerCommand` z `@open-mercato/shared/lib/commands`).
   - Id komendy: **`loyalty.accruals.accrueOrder`**.

2. **Wejscie** — walidowane zodem PRZED jakimkolwiek odczytem/zapisem:
   - `{ orderId: string (uuid) }`; brak/nieprawidlowe `orderId` → wyjatek walidacji, zero zapisow.

3. **Zrodlo danych zamowienia — zero cross-module ORM importow.** Encje modulu `sales`
   rezolwujesz z DI po tokenach klas: `ctx.container.resolve('SalesOrder')`
   (oraz `ctx.container.resolve('SalesOrderLine')`, gdyby byl potrzebny) — moduł `sales`
   rejestruje swoje klasy encji w kontenerze pod nazwami klas. ZAKAZ importu tych encji
   z `@open-mercato/core`. EntityManager z DI (`ctx.container.resolve('em')`).
   Ograniczaj sie do standardowego API em: `fork/findOne/findOneOrFail/find/count/create/
   assign/persist/persistAndFlush/flush/nativeInsert/nativeUpdate/transactional/getReference`
   (bez QueryBuildera) — tak jak istniejace komendy w tym repo.

4. **Scoping i bledy** (styl jak w istniejacych komendach modulu):
   - zamowienie musi nalezec do `tenantId`/`organizationId` kontekstu (`ctx.auth.tenantId`,
     `ctx.auth.orgId` / `ctx.selectedOrganizationId`) i miec `deletedAt: null`; nieznalezione
     lub spoza zasiegu → `throw new CrudHttpError(404, { error: translate('loyalty.errors.orderNotFound', <fallback en>) })`
     (`resolveTranslations` z `@open-mercato/shared/lib/i18n/server`, `CrudHttpError`
     z `@open-mercato/shared/lib/crud/errors`); ZERO zapisow;
   - klucz `loyalty.errors.orderNotFound` dodany do WSZYSTKICH 5 locale modulu
     (`en/pl/de/es/ko`), niepusty, przetlumaczony;
   - konto lojalnosciowe klienta zamowienia (`LoyaltyAccount` po `customerId ==
     order.customerEntityId`, w tym samym tenant/org, `deletedAt: null`) nieznalezione →
     `CrudHttpError(404)` z istniejacym kluczem `loyalty.errors.accountNotFound`; ZERO zapisow.

5. **Matematyka (identyczna z dotychczasowa logika serii):**
   - `points = floor(Number(order.grandTotalNetAmount))` — 1 punkt za kazda pelna jednostke
     waluty netto sumy zamowienia;
   - `points <= 0` → wynik `{ created: 0 }`, zero zapisow, bez bledu;
   - zamowienie bez `customerEntityId` (gosc) → `{ created: 0 }`, zero zapisow, bez bledu.

6. **Wpis ledgera** — encja `LoyaltyLedgerEntry` (tabela `loyalty_ledger_entries`,
   kontrakt serii) tworzona przez `em.create(...)`; pola wpisu naliczenia co najmniej:
   - `points` (int, dodatni), `orderId` = id zamowienia (kolumna `order_id`),
     `accountId` = id konta (kolumna `account_id`), `tenantId`/`organizationId` = z zamowienia
     (zgodne z kontekstem).

7. **Uznanie salda** — `account.balance = account.balance + points` na wczytanej encji
   + `flush` (wzorzec jak `loyalty.accounts.adjustBalance`).

8. **Idempotencja per zamowienie** — PRZED zapisem sprawdz przez em (`findOne`/`count`),
   czy w tenant/org istnieje juz wpis ledgera z `orderId` tego zamowienia; jezeli tak →
   `{ created: 0 }`, zero nowych wpisow, saldo NIETKNIETE. Idempotencji nie wolno opierac
   na lapaniu bledu unique constraint.

9. **Wynik** — `execute` zwraca obiekt zawierajacy co najmniej `{ created: number }`:
   liczba NOWO utworzonych wpisow ledgera (`1` przy naliczeniu, `0` przy powtorce/pominieciu).

10. **Unit testy wlasne** — w `apps/mercato/src/modules/loyalty/__tests__/` (styl OM:
    mock `em` + `ctx`, komenda z `commandRegistry` po imporcie `../commands`): happy path
    (floor, wpis, saldo), idempotencja, `points <= 0`, brak klienta, 404-y.

## Kryteria ukonczenia

- Import `.../loyalty/commands` rejestruje komende; `commandRegistry.get('loyalty.accruals.accrueOrder')` zwraca handler.
- Naliczenie: jeden wpis ledgera z kompletem pol z pkt 6, saldo konta uznane o `floor(suma netto)`.
- Powtorne wywolanie dla tego samego zamowienia: `created: 0`, zero nowych wpisow, saldo bez zmian.
- Suma `<= 0` oraz zamowienie bez klienta → `created: 0`, zero zapisow.
- Zamowienie spoza tenant/org lub nieistniejace → `CrudHttpError(404)` z kluczem
  `loyalty.errors.orderNotFound`; zadnych zapisow.
- Klucz `loyalty.errors.orderNotFound` we wszystkich 5 plikach locale.
- `yarn typecheck` i testy modulu zielone; caly istniejacy test-suite repo pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: kazdy odczyt i zapis ograniczony do tenanta/organizacji kontekstu.
- **Zero cross-module ORM**: encje `sales` wylacznie przez tokeny DI (`SalesOrder`,
  `SalesOrderLine`); odwolania do rekordow innych modulow wylacznie przez pola uuid.
- **i18n x5**: kazdy nowy klucz we wszystkich 5 locale (en/pl/de/es/ko); komunikaty bledow
  przez `resolveTranslations().translate(<klucz>, <fallback>)` — zero hardcodow w `throw`.
- **Walidacja przed done**: zod na wejsciu; przed uznaniem zadania za skonczone `yarn jest`
  modulu + pelna suita repo zielona.
