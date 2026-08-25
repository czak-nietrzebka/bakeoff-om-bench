# ZADANIE T8

## Cel

Moduł `loyalty` (`apps/mercato/src/modules/loyalty`) ma dziś dwie ścieżki naliczania
punktów za zamówienia: subscriber eventu `sales.order.completed` oraz komendę
`loyalty.accruals.accrueOrder`. Zadanie ma dwie części, które muszą wejść RAZEM:

1. **Ekstrakcja matematyki** naliczeń do współdzielonej biblioteki modułu
   (`lib/accrual.ts`), z której korzystają OBIE istniejące ścieżki.
2. **Bulk-import naliczeń historycznych** — nowa komenda, która nalicza punkty za
   listę historycznych zamówień (dane przychodzą w wejściu komendy) TĄ SAMĄ
   biblioteką.

Obserwowane zachowanie obu istniejących ścieżek NIE MOŻE się zmienić: zaokrąglenia,
wykluczenia (zamówienie bez klienta, punkty <= 0), idempotencja per zamówienie oraz
błędy 404 zostają dokładnie takie, jakie są. Całe dotychczasowe pokrycie testowe
modułu pozostaje zielone. Jeżeli część artefaktów istnieje pod innymi nazwami z
wcześniejszej pracy, doprowadź stan końcowy DOKŁADNIE do kontraktu poniżej.

## Wymagania

Poniższe identyfikatory są KONTRAKTEM PUBLICZNYM — muszą się zgadzać co do znaku.

1. **Biblioteka współdzielona** — `apps/mercato/src/modules/loyalty/lib/accrual.ts`,
   moduł CZYSTY (zero efektów ubocznych przy imporcie, zero importów ORM/encji/DI/
   i18n; funkcje deterministyczne). Eksporty:
   - `export const LOYALTY_ORDER_RATE = 0.1` — stawka ścieżki eventowej;
   - `export function calculateOrderNetPoints(netTotal: unknown): number` —
     kanoniczna matematyka floor od kwoty NETTO (1 punkt za każdą pełną jednostkę
     waluty; w `accrueOrder` stosowana do kwoty netto każdej kwalifikującej się
     linii — kontrakt T5 po zmianie wymagań — a w bulk-imporcie do `netTotal`
     itemu): `n = Number(netTotal)` (wejście może być number albo
     string — ORM oddaje decimal jako string); `n` niebędące skończoną liczbą → `0`;
     wynik `Math.floor(n)`; wynik ujemny → `0`;
   - `export function calculateOrderCompletedPoints(total: unknown): number` —
     matematyka ścieżki eventowej: `n = Number(total)`; `n` niebędące skończoną
     liczbą → `0`; wynik `Math.round(n * LOYALTY_ORDER_RATE)`; wynik ujemny → `0`.

2. **Jedno źródło formuł (refaktor obu ścieżek):**
   - komenda `loyalty.accruals.accrueOrder` liczy punkty WYŁĄCZNIE przez
     `calculateOrderNetPoints` (wywoływaną per kwalifikująca się linia zamówienia,
     zgodnie z kontraktem T5 po zmianie wymagań);
   - subscriber `sales.order.completed` liczy punkty WYŁĄCZNIE przez
     `calculateOrderCompletedPoints`;
   - komenda bulk-importu (pkt 3) liczy punkty WYŁĄCZNIE przez
     `calculateOrderNetPoints`;
   - żadna z formuł nie jest powielona nigdzie indziej w module — podmiana
     implementacji funkcji w `lib/accrual.ts` (np. w teście) MUSI zmieniać wynik
     każdej z trzech ścieżek;
   - zachowanie obu istniejących ścieżek pozostaje IDENTYCZNE: w komendzie floor
     netto per kwalifikująca się linia (wykluczenia shipping / 100% rabatu bez
     zmian; brak naliczonych punktów → `{ created: 0 }`, zamówienie bez
     klienta → `{ created: 0 }`, idempotencja per zamówienie, 404-y z i18n);
     w subscriberze `Math.round(total * 0.1)`, brak zapisu przy `points === 0`,
     fail-closed na złym payloadzie i trwała idempotencja replay.

3. **Komenda bulk-importu** — id **`loyalty.accruals.bulkImport`**, kod w
   `apps/mercato/src/modules/loyalty/commands/` (nazwa pliku dowolna), rejestracja
   side-effectem importu `commands/index.ts` (`registerCommand` z
   `@open-mercato/shared/lib/commands`), jak pozostałe komendy modułu.

4. **Wejście** — walidowane zodem W CAŁOŚCI, PRZED jakimkolwiek odczytem/zapisem:
   `{ items: Array<{ orderId: string (uuid), customerId: string (uuid) | null,
   netTotal: number (skończony) }> }`, od 1 do 500 pozycji. `customerId: null`
   reprezentuje historyczne zamówienie gościa. Jakikolwiek błąd walidacji →
   wyjątek, ZERO zapisów (batch nie jest przetwarzany częściowo przy złym wejściu).

5. **Scope** — `tenantId`/`organizationId` WYŁĄCZNIE z kontekstu wywołania
   (`ctx.auth.tenantId`, `ctx.auth.orgId` / `ctx.selectedOrganizationId`), nigdy
   z items.

6. **Przetwarzanie per item** (w kolejności wejścia). Item jest POMIJANY
   (liczony w `skipped`, bez wyjątku, bez żadnego zapisu dla tego itemu), gdy:
   - `calculateOrderNetPoints(netTotal) <= 0`;
   - `customerId === null` (gość — wykluczenie jak w ścieżce komendy);
   - wpis ledgera z tym `orderId` już istnieje w tenant/org — w bazie ALBO
     utworzony wcześniej w TYM SAMYM wywołaniu (duplikat `orderId` wewnątrz
     batcha: pierwszy nalicza, kolejne pomijane);
   - konto `LoyaltyAccount` klienta nie istnieje w tenant/org kontekstu
     (lookup: `em.findOne(LoyaltyAccount, { tenantId, organizationId, customerId,
     deletedAt: null })`); bulk-import NIE tworzy kont.

7. **Naliczenie itemu:** `points = calculateOrderNetPoints(netTotal)`; JEDEN wpis
   `LoyaltyLedgerEntry` (kontrakt serii; pola co najmniej: `points` — int dodatni,
   `orderId`, `accountId` — id konta, `tenantId`/`organizationId` — z kontekstu)
   oraz `account.balance = account.balance + points` na wczytanej encji + flush
   (flush per item albo raz na koniec — oba poprawne). Wiele itemów tego samego
   klienta w jednym batchu nalicza się niezależnie i sumuje na saldzie.

8. **Idempotencja** — sprawdzana PRZED zapisem przez `em.findOne`/`em.count` po
   `orderId` w tenant/org; NIE przez łapanie błędu unique constraint. Ponowne
   wywołanie z tym samym batchem → wszystkie itemy `skipped`, zero nowych wpisów,
   salda bez zmian. Zamówienie naliczone wcześniej ścieżką eventową albo komendą
   `accrueOrder` NIE naliczy się drugi raz przez bulk (wspólny klucz: `orderId`
   per tenant/org w ledgerze).

9. **Wynik** — `execute` zwraca obiekt zawierający co najmniej
   `{ imported: number, skipped: number }`; zawsze
   `imported + skipped === items.length`.

10. **Dostęp do danych** — wyłącznie `em` z DI (`ctx.container.resolve('em')`),
    standardowe API (`fork/findOne/find/count/create/assign/persist/
    persistAndFlush/flush/transactional/getReference`), bez QueryBuildera i bez
    surowego SQL. Bulk-import NIE czyta modułu `sales` (dane historyczne
    przychodzą w items) i nie importuje żadnych encji innych modułów.

11. **Schemat** — zadanie nie wymaga zmian schematu (reuse `loyalty_ledger_entries`
    i `loyalty_accounts`); jeżeli jednak schemat się zmienia, migracja MikroORM w
    `apps/mercato/src/modules/loyalty/migrations/`.

12. **Testy własne** — w `apps/mercato/src/modules/loyalty/__tests__/` (styl OM:
    mock `em` + `ctx`, komenda z `commandRegistry` po imporcie `../commands`):
    happy path bulk (floor, wpisy, salda, licznik), wykluczenia, idempotencja
    (w tym duplikat w batchu i re-run), walidacja-zero-zapisów oraz regresja obu
    istniejących ścieżek po refaktorze.

## Kryteria ukończenia

- `lib/accrual.ts` istnieje, eksportuje `LOYALTY_ORDER_RATE`,
  `calculateOrderNetPoints`, `calculateOrderCompletedPoints` z matematyką z pkt 1;
  import biblioteki działa samodzielnie (bez DI/ORM).
- `accrueOrder` i subscriber liczą punkty przez bibliotekę; ich obserwowane
  zachowanie jest bez zmian; CAŁE dotychczasowe pokrycie testowe modułu zielone.
- `commandRegistry.get('loyalty.accruals.bulkImport')` zwraca handler po imporcie
  `.../loyalty/commands`.
- Poprawny batch: po jednym wpisie ledgera per naliczony item (komplet pól z pkt
  7), salda uznane o `Math.floor(netTotal)`, wynik `{ imported, skipped }` zgodny.
- Wykluczenia i idempotencja dokładnie jak w pkt 6/8; re-run tego samego batcha
  oraz batch z zamówieniem już naliczonym inną ścieżką → zero nowych zapisów.
- Walidacja odrzuca: puste `items`, ponad 500 pozycji, `orderId` nie-uuid,
  `netTotal` niebędący skończoną liczbą — za każdym razem zero zapisów.
- `yarn typecheck` i testy modułu przechodzą; cała istniejąca suita repo zielona.

## Konwencje

- **Tenant/org-scoping**: każdy odczyt i zapis ograniczony do tenanta/organizacji
  kontekstu wywołania; identyfikatory scope zawsze z auth/kontekstu, nie z wejścia.
- **Zero cross-module ORM**: nie importuj encji innych modułów; odwołania do
  rekordów innych modułów wyłącznie przez pola uuid.
- **i18n ×5 (de/en/es/ko/pl)**: bulk-import nie wymaga nowych user-facing
  stringów; jeżeli jakiś dodajesz, klucz musi trafić do wszystkich 5 locale przez
  `resolveTranslations`/`translate` — zero hardcodów.
- **Walidacja przed done**: zod na wejściu przed jakimkolwiek zapisem; przed
  uznaniem zadania za skończone `yarn typecheck` + testy modułu + pełna suita
  repo zielona.
