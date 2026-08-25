# ZADANIE T2

## Cel

Dodaj do modulu `loyalty` (`apps/mercato/src/modules/loyalty/`) komende korekty salda konta lojalnosciowego z twardym guardem „saldo nigdy ujemne". Bledy sa typowane (`CrudHttpError`) z komunikatami rozwiazywanymi przez i18n, a klucze bledow istnieja we wszystkich 5 locale (en/pl/de/es/ko). Komenda jest scoped per tenant/organizacja i pokryta unit testami happy-path i error-path. Wzorce: `apps/mercato/src/modules/example/commands/todos.ts` (rejestracja i ksztalt komendy), `packages/core/src/modules/customers/commands/deals.ts` (blad z `resolveTranslations` + `CrudHttpError`), `packages/core/src/modules/customers/commands/__tests__/updatePerson.displayName.test.ts` (styl testow komend).

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Rejestracja i discovery**
   - Kod komendy w `apps/mercato/src/modules/loyalty/commands/` (nazwa pliku dowolna).
   - Istnieje `commands/index.ts`, ktory importuje wszystkie pliki komend modulu — sam import `apps/mercato/src/modules/loyalty/commands` MUSI zarejestrowac komendy (side-effect `registerCommand` z `@open-mercato/shared/lib/commands`), tak jak w `packages/core/src/modules/customers/commands/index.ts`.
   - Id komendy: **`loyalty.accounts.adjustBalance`**.

2. **Wejscie** — walidowane zodem w `execute` PRZED jakimkolwiek odczytem/zapisem:
   - `{ id: string (uuid konta), delta: liczba calkowita (dodatnia albo ujemna) }`;
   - wejscie niepoprawne (np. `delta: 1.5`, brak `id`) → wyjatek (blad walidacji zod).

3. **Lookup konta** — przez EntityManager z DI (`ctx.container.resolve('em')`), scoped: konto musi nalezec do `tenantId` i organizacji z kontekstu (`ctx.auth.tenantId`, `ctx.auth.orgId` / `ctx.selectedOrganizationId`) oraz miec `deletedAt: null`. Scoping w klauzuli zapytania ALBO jawnym sprawdzeniem po odczycie — oba warianty poprawne.
   - Konto nieznalezione lub spoza zasiegu tenant/org → `throw new CrudHttpError(404, { error: translate('loyalty.errors.accountNotFound', <fallback po angielsku>) })`, gdzie `translate` pochodzi z `await resolveTranslations()` (`@open-mercato/shared/lib/i18n/server`), a `CrudHttpError` z `@open-mercato/shared/lib/crud/errors`.

4. **GUARD nigdy-ujemne** — sprawdzany PRZED mutacja:
   - jezeli `account.balance + delta < 0` → `throw new CrudHttpError(400, { error: translate('loyalty.errors.balanceBelowZero', <fallback po angielsku>) })`; saldo pozostaje NIEZMIENIONE, zadnego flusha;
   - wynik rowny dokladnie `0` jest DOZWOLONY (guard blokuje wylacznie zejscie PONIZEJ zera).

5. **Happy path** — mutacja na wczytanej encji: `account.balance = account.balance + delta`, nastepnie `await em.flush()`. Wynik komendy (`execute` zwraca): obiekt zawierajacy co najmniej `{ id: <id konta>, balance: <nowe saldo> }`.

6. **i18n** — klucze `loyalty.errors.balanceBelowZero` i `loyalty.errors.accountNotFound` dodane do WSZYSTKICH PIECIU plikow locale modulu (`i18n/en.json`, `pl.json`, `de.json`, `es.json`, `ko.json`) z niepustymi, przetlumaczonymi wartosciami.

7. **Unit testy** — w `apps/mercato/src/modules/loyalty/__tests__/` (jest, styl OM: mock `em` + `ctx`, komenda pobrana z `commandRegistry` po imporcie `../commands`):
   - happy path (korekta dodatnia i ujemna, w tym zejscie dokladnie do zera);
   - error path (guard ponizej zera: typ bledu, status, klucz i18n, saldo nietkniete).

## Kryteria ukonczenia

- Import `apps/mercato/src/modules/loyalty/commands` rejestruje komende; `commandRegistry.get('loyalty.accounts.adjustBalance')` zwraca handler.
- Korekta dodatnia i ujemna aktualizuje saldo i zwraca `{ id, balance }` z nowym saldem; zejscie dokladnie do zera przechodzi.
- Zejscie ponizej zera odrzucone `CrudHttpError` o statusie 400 z komunikatem z klucza `loyalty.errors.balanceBelowZero`; saldo pozostaje niezmienione.
- Konto spoza tenanta/organizacji kontekstu → `CrudHttpError` 404 z kluczem `loyalty.errors.accountNotFound`.
- Niepoprawne wejscie (nie-calkowite `delta`) odrzucone.
- Oba klucze bledow obecne we wszystkich 5 plikach locale.
- Unit testy modulu przechodza (`yarn jest`); caly istniejacy test-suite repo pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: zadnego odczytu ani zapisu konta poza tenantem/organizacja kontekstu wywolania.
- **Zero cross-module ORM**: komenda operuje wylacznie na encji `LoyaltyAccount` modulu loyalty.
- **i18n x5**: kazdy nowy klucz we wszystkich piecu locale; komunikaty bledow wylacznie przez `resolveTranslations().translate(<klucz>, <fallback>)` — zadnych hardcodowanych stringow w `throw`.
- **Walidacja przed done**: zod na wejsciu komendy; przed uznaniem zadania za skonczone uruchom `yarn jest` i upewnij sie, ze przechodzi.
