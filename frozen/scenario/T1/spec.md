# ZADANIE T1

## Cel

Zbuduj nowy modul aplikacyjny **`loyalty`** w `apps/mercato/src/modules/loyalty/` (modul APP-SPECIFIC — nie ruszaj `packages/core`). Modul przechowuje konta lojalnosciowe klientow: encja `LoyaltyAccount` (tabela `loyalty_accounts`), scoped per tenant i organizacja, z calkowitoliczbowym saldem punktow i odwolaniem do klienta wylacznie przez ID (zadnych relacji ORM do encji innych modulow). Modul wystawia pelne CRUD API przez `makeCrudRoute` pod `/api/loyalty/accounts` (lista + detail przez `?id=`), ma migracje MikroORM, deklaracje ACL, komplet i18n w 5 locale i jest zarejestrowany w aplikacji. Wzorce do nasladowania: `apps/mercato/src/modules/example/` (kanoniczny modul referencyjny w tej samej aplikacji) oraz `packages/core/src/modules/customers/` (wzorzec domenowy).

## Wymagania

Ponizsze nazwy i sciezki sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Lokalizacja i rejestracja**
   - Caly kod modulu w `apps/mercato/src/modules/loyalty/`.
   - Wpis `{ id: 'loyalty', from: '@app' }` dodany do `enabledModules` w `apps/mercato/src/modules.ts`.
   - Po rejestracji uruchom `yarn generate` (regeneracja rejestru modulow).

2. **`index.ts`** — eksportuje `metadata: ModuleInfo` (typ z `@open-mercato/shared/modules/registry`) z `name: 'loyalty'`.

3. **`data/entities.ts`** — eksportuje klase **`LoyaltyAccount`**:
   - `@Entity({ tableName: 'loyalty_accounts' })`, dekoratory z `@mikro-orm/decorators/legacy` (jak w istniejacych encjach OM);
   - pola (nazwa wlasciwosci → kolumna):
     - `id` — uuid PK, `defaultRaw: 'gen_random_uuid()'`;
     - `tenantId` → `tenant_id`, uuid, NOT NULL;
     - `organizationId` → `organization_id`, uuid, NOT NULL;
     - `customerId` → `customer_id`, uuid, NOT NULL — **zwykly uuid**, ZERO relacji ORM cross-module (zadnych `@ManyToOne`/`@OneToOne`/`@OneToMany`/`@ManyToMany` do encji innych modulow; wzorzec: `progress_job_id` w `ExampleTodoBulkOperation`);
     - `balance` → `balance`, `type: 'integer'`, NOT NULL, default `0` — inicjalizator klasy (`balance: number = 0`) ORAZ default w DB;
     - `createdAt` → `created_at` (onCreate), `updatedAt` → `updated_at` (onUpdate);
     - `deletedAt` → `deleted_at`, nullable (soft delete);
   - encja NIE deklaruje zadnej wlasciwosci relacyjnej (m:1 / 1:1 / 1:m / m:n);
   - klasa instancjonowalna bez argumentow konstruktora (`new LoyaltyAccount()` daje `balance === 0`);
   - indeksy: na (`organization_id`, `tenant_id`) oraz na `customer_id`.

4. **`acl.ts`** — eksportuje tablice `features` (oraz `export default features`) zawierajaca co najmniej:
   - `{ id: 'loyalty.accounts.view', title: ..., module: 'loyalty' }`;
   - `{ id: 'loyalty.accounts.manage', title: ..., module: 'loyalty', dependsOn: ['loyalty.accounts.view'] }`.

5. **`api/accounts/route.ts`** — CRUD przez `makeCrudRoute` z `@open-mercato/shared/lib/crud/factory`; plik eksportuje `metadata, GET, POST, PUT, DELETE` (destrukturyzacja wyniku fabryki, jak w `example/api/todos/route.ts`):
   - `metadata`: `GET` → `requireAuth: true` + `requireFeatures: ['loyalty.accounts.view']`; `POST`/`PUT`/`DELETE` → `requireAuth: true` + `requireFeatures: ['loyalty.accounts.manage']`;
   - `orm`: `entity: LoyaltyAccount`; scoping tenant/org AKTYWNE — `orgField`/`tenantField` zostaja na defaultach (`organizationId`/`tenantId`) albo sa ustawione jawnie na te wartosci; NIE WOLNO ustawic ich na `null`; soft delete przez `deletedAt` (default `softDeleteField`);
   - `list`: zod `querySchema` akceptujacy co najmniej: `id` (uuid, OPCJONALNE — sciezka detail), `page` (default 1), `pageSize` (z defaultem), `customerId` (uuid, OPCJONALNY filtr) — `schema.parse({})` musi przechodzic i dawac `page = 1`; `entityId: 'loyalty:loyalty_account'`;
   - zapisy (POST/PUT/DELETE): do wyboru JEDNA z dwoch sciezek fabryki — (a) `actions.create/update/delete` z `commandId` wskazujacym komendy CRUD modulu zarejestrowane przez `registerCommand`, albo (b) bezposrednie konfiguracje `create` (`schema` + `mapToEntity`), `update` (`schema` + `applyToEntity`), `del`. W obu sciezkach wejscie walidowane zodem; create wymaga `customerId` (uuid), opcjonalne poczatkowe `balance` (int >= 0).

6. **Migracja MikroORM** — plik w `apps/mercato/src/modules/loyalty/migrations/` (klasa rozszerzajaca `Migration` z `@mikro-orm/migrations`, wzorzec: `example/migrations/Migration20260226161000_example.ts`):
   - `up()`: `create table "loyalty_accounts"` z kolumnami: `id` uuid PK default `gen_random_uuid()`, `tenant_id` uuid not null, `organization_id` uuid not null, `customer_id` uuid not null, `balance` int not null default 0, `created_at`/`updated_at` timestamptz not null, `deleted_at` timestamptz null; plus indeksy z pkt 3;
   - `down()`: `drop table if exists "loyalty_accounts" cascade`.

7. **i18n** — katalog `i18n/` z PIECIOMA plikami: `en.json`, `pl.json`, `de.json`, `es.json`, `ko.json` (plaskie mapy klucz→string, jak w `example/i18n/`):
   - minimum klucz `loyalty.accounts.title` (tytul listy kont) we wszystkich 5 plikach, niepusty;
   - PELNY PARYTET: kazdy klucz `loyalty.*` obecny w jednym pliku locale musi byc obecny we WSZYSTKICH pieciu.

8. **Unit testy modulu** — w `apps/mercato/src/modules/loyalty/__tests__/` (jest + styl istniejacych testow OM); minimum: kontrakt ACL i konfiguracja route'a (feature-gating, scoping). Testy zielone przez `yarn jest` z korzenia repo albo z `apps/mercato`.

## Kryteria ukonczenia

- Modul kompiluje sie i jest zarejestrowany (`enabledModules` zawiera `loyalty`); `yarn generate` przechodzi.
- `data/entities.ts` eksportuje `LoyaltyAccount` dokladnie w ksztalcie z pkt 3 (nazwy wlasciwosci, kolumny, typ integer, defaulty, brak relacji).
- `acl.ts` deklaruje oba features z pkt 4 z poprawnym `dependsOn`.
- `api/accounts/route.ts` eksportuje wszystkie cztery metody + `metadata`, z feature-gatingiem i scopingiem z pkt 5 oraz `entityId: 'loyalty:loyalty_account'`; `querySchema` przyjmuje `id`/`page`/`pageSize`/`customerId`.
- Migracja tworzy tabele `loyalty_accounts` ze wszystkimi kolumnami z pkt 6.
- 5 plikow locale istnieje, kazdy z `loyalty.accounts.title`, z pelnym parytetem kluczy `loyalty.*`.
- Wlasne unit testy modulu przechodza; caly istniejacy test-suite repo pozostaje zielony.

## Konwencje

- **Tenant/org-scoping wszedzie**: kazdy odczyt i zapis ograniczony do `tenantId` + `organizationId` z kontekstu uwierzytelnienia; nigdy nie wylaczaj scopingu fabryki.
- **Zero cross-module ORM**: odwolania do rekordow innych modulow wylacznie przez pola uuid; zadnych importow cudzych encji do relacji.
- **i18n x5**: kazdy string widoczny dla uzytkownika przez klucz i18n obecny we wszystkich 5 locale (en/pl/de/es/ko).
- **Walidacja przed done**: wejscia API walidowane zodem; przed uznaniem zadania za skonczone uruchom testy (`yarn jest`) i upewnij sie, ze przechodza.
- Stylistyka i struktura plikow jak w module `example` (ten sam uklad katalogow: `data/`, `api/`, `i18n/`, `migrations/`, `acl.ts`, `index.ts`).
