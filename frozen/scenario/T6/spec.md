# ZADANIE T6

## Cel

Punkty lojalnosciowe dostaja termin waznosci, a modul `loyalty`
(`apps/mercato/src/modules/loyalty/`) — konfigurowalne progi tierow. Trzy rzeczy do
zbudowania: (1) kolumna `expires_at` na wpisach ledgera (`LoyaltyLedgerEntry` /
`loyalty_ledger_entries`) plus stemplowanie jej na kazdym NOWYM naliczeniu, (2) nowa
encja **`LoyaltyTier`** (tabela `loyalty_tiers`) z progami punktowymi per
tenant/organizacja wraz z czystym helperem rozstrzygajacym tier dla salda, (3) para
migracji: WYGENEROWANA migracja schematu ORAZ OSOBNA, RECZNIE napisana migracja
backfillu, ktora uzupelnia `expires_at` na wpisach ledgera zapisanych przez
dotychczasowe sciezki modulu (naliczenia z zamowien). Modul istnieje po
wczesniejszych zadaniach — rozszerzasz go; jezeli dotychczasowe artefakty realizuja
czesc ponizszego kontraktu pod innymi nazwami, doprowadz stan koncowy do kontraktu
z tego zadania. Wzorce: `apps/mercato/src/modules/example/migrations/` (styl migracji
schematu), `packages/core/src/modules/attachments/migrations/Migration20251117181353.ts`
(precedens backfillu danych w migracji).

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **`expires_at` na ledgerze** — encja `LoyaltyLedgerEntry`
   (`data/entities.ts`, tabela `loyalty_ledger_entries`, kontrakt serii) dostaje
   wlasciwosc **`expiresAt`** → kolumna **`expires_at`**, `timestamptz` NULLABLE,
   bez defaultu w DB (typ TS: `Date | null`, inicjalizator `null`). Zero relacji ORM,
   jak dotad.

2. **Encja `LoyaltyTier`** — eksportowana z `data/entities.ts`:
   - `@Entity({ tableName: 'loyalty_tiers' })`, dekoratory z
     `@mikro-orm/decorators/legacy` (jak pozostale encje modulu);
   - pola (wlasciwosc → kolumna): `id` uuid PK `defaultRaw: 'gen_random_uuid()'`;
     `tenantId` → `tenant_id` uuid NOT NULL; `organizationId` → `organization_id`
     uuid NOT NULL; `name` → `name` text NOT NULL (nazwa tieru, np. "Silver");
     `minPoints` → `min_points` integer NOT NULL (prog wejscia w tier, `>= 0`);
     `createdAt` → `created_at` (onCreate); `updatedAt` → `updated_at` (onUpdate);
     `deletedAt` → `deleted_at` nullable (soft delete);
   - ZERO wlasciwosci relacyjnych (zadnych `@ManyToOne`/`@OneToOne`/`@OneToMany`/
     `@ManyToMany`); klasa instancjonowalna bez argumentow (`new LoyaltyTier()`);
   - unikalnosc progu w zasiegu: UNIQUE na (`tenant_id`, `organization_id`,
     `min_points`); dodatkowo indeks na (`organization_id`, `tenant_id`).

3. **Named contract: `data/tiers.ts`** — eksportuje czysta funkcje
   **`resolveTierForBalance(tiers, balance)`**:
   - wejscie: tablica encji/obiektow tierow (dowolna kolejnosc!) + calkowite saldo;
   - zwraca tier o NAJWYZSZYM `minPoints` sposrod tych z `minPoints <= balance`,
     z pominieciem rekordow z `deletedAt != null`; saldo rowne dokladnie progowi
     WCHODZI w tier (`>=`); brak pasujacego tieru / pusta tablica → `null`;
   - wynik NIE moze zalezec od kolejnosci elementow wejscia; funkcja niczego nie
     mutuje i nie dotyka bazy (filtrowanie po tenant/org robi wolajacy, ktory
     przekazuje juz zescopowana liste).

4. **Named contract: `data/expiry.ts`** — eksportuje:
   - **`LOYALTY_POINTS_VALIDITY_MONTHS = 12`** (stala modulu, liczba);
   - **`computeExpiresAt(createdAt: Date): Date`** — zwraca NOWA date przesunieta
     o dokladnie `LOYALTY_POINTS_VALIDITY_MONTHS` miesiecy KALENDARZOWYCH w UTC
     (semantyka `setUTCMonth(getUTCMonth() + 12)`); obowiazuje naturalna
     normalizacja JS `Date` (np. `2028-02-29` + 12 mies. → `2029-03-01`); wejscie
     nie jest mutowane;
   - **`backfillLedgerExpiry(em): Promise<{ updated: number }>`** — jednorazowe
     uzupelnienie historii: przez standardowe API EntityManagera
     (`em.find(LoyaltyLedgerEntry, ...)` + mutacja wczytanych encji + `flush`;
     bez surowego SQL i bez QueryBuildera) laduje wpisy ledgera z `expiresAt`
     rownym NULL i:
     - wpis z `points > 0` (naliczenie) → `expiresAt = computeExpiresAt(entry.createdAt)`;
     - wpis z `points <= 0` → zostaje NULL (nie wygasa);
     - wpis z juz ustawionym `expiresAt` → NIETKNIETY;
     - zwraca `{ updated: <liczba faktycznie ostemplowanych wpisow> }`; wywolanie
       powtorne jest idempotentne (`{ updated: 0 }`, zero zmian);
     - UWAGA zasiegowa: to funkcja MIGRACYJNA — dziala na CALEJ tabeli, przez
       wszystkie tenanty/organizacje (migracja schematu z natury obejmuje cala
       baze); to jedyny swiadomy wyjatek od tenant-scopingu w tym module i nie
       wolno go reuzywac w sciezkach runtime.

5. **Migracje — DWA OSOBNE pliki** w `apps/mercato/src/modules/loyalty/migrations/`:
   - **(a) wygenerowana migracja schematu** (klasa `Migration` z
     `@mikro-orm/migrations`, styl jak dotychczasowe migracje modulu):
     `alter table "loyalty_ledger_entries" add column "expires_at" timestamptz null;`
     oraz `create table "loyalty_tiers" (...)` z kolumnami i indeksami z pkt 2
     (w tym UNIQUE na `tenant_id`/`organization_id`/`min_points`); `down()` zdejmuje
     kolumne i tabele;
   - **(b) RECZNA migracja backfillu** — OSOBNY plik OBOK (a), ze znacznikiem
     czasu POZNIEJSZYM niz (a), ktory importuje `backfillLedgerExpiry` z
     `../data/expiry` i wywoluje ja w `up()` na EntityManagerze migracji
     (`this.getEntityManager()`); plik NIE zawiera zadnego DDL (`create table` /
     `alter table` / `create index`) — cala logike danych niesie
     `backfillLedgerExpiry`, zeby migracja i testy jednostkowe wykonywaly TEN SAM
     kod; `down()` moze byc no-op (backfillu nie cofamy).
   - Rozdzial (a)/(b) jest wymaganiem: schema-diff pozostaje regenerowalny
     narzedziem, a backfill danych ma wlasna, recznie reasonowana migracje.

6. **Stemplowanie NOWYCH naliczen** — komenda **`loyalty.accruals.accrueOrder`**
   (kontrakt serii) przy tworzeniu wpisu ledgera ustawia
   `expiresAt = computeExpiresAt(<moment naliczenia>)` (uzywajac funkcji z pkt 4 —
   nie drugiej kopii tej arytmetyki). Pozostale zachowania komendy (idempotencja,
   floor, scoping, bledy) pozostaja bez zmian.

7. **Unit testy wlasne** — w `apps/mercato/src/modules/loyalty/__tests__/`
   (jest, styl OM: mock `em` + `ctx`, komenda z `commandRegistry` po imporcie
   `../commands`): arytmetyka `computeExpiresAt` (w tym normalizacja 29 lutego),
   `resolveTierForBalance` (prog dokladny, kolejnosc, `deletedAt`, pusta lista),
   backfill na zaseedowanych wpisach (naliczenia, wpis ujemny, wpis juz
   ostemplowany, idempotencja), stemplowanie nowego naliczenia.

## Kryteria ukonczenia

- `data/entities.ts` eksportuje `LoyaltyTier` dokladnie w ksztalcie z pkt 2, a
  `LoyaltyLedgerEntry` ma `expiresAt`/`expires_at` (nullable) z pkt 1.
- `resolveTierForBalance` rozstrzyga tier po najwyzszym osiagnietym progu,
  z granica `>=`, niezaleznie od kolejnosci wejscia i z pominieciem skasowanych.
- `computeExpiresAt` przesuwa o 12 miesiecy kalendarzowych w UTC z normalizacja JS.
- `backfillLedgerExpiry` stempluje wylacznie wpisy `expiresAt IS NULL` o `points > 0`
  wartoscia `computeExpiresAt(createdAt)`, zwraca rzetelny licznik i jest
  idempotentna; wpisy ujemne i juz ostemplowane pozostaja nietkniete.
- W `migrations/` istnieja DWA osobne pliki: schema-DDL (kolumna + tabela + unique)
  i pozniejsza reczna migracja wywolujaca `backfillLedgerExpiry`, bez DDL w srodku.
- Nowe naliczenie przez `loyalty.accruals.accrueOrder` tworzy wpis ledgera z
  ustawionym `expiresAt` ≈ teraz + 12 miesiecy.
- `yarn typecheck` i testy modulu przechodza; caly istniejacy test-suite repo
  pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: kazda sciezka RUNTIME (komendy, API) czyta i pisze
  wylacznie w tenancie/organizacji kontekstu; jedyny wyjatek to migracyjny
  backfill z pkt 4, jawnie ograniczony do migracji.
- **Zero cross-module ORM**: `LoyaltyTier` i ledger nie deklaruja zadnych relacji;
  odwolania do rekordow innych modulow wylacznie przez pola uuid.
- **i18n x5**: to zadanie nie dodaje nowych stringow user-facing; jezeli jakis
  dodasz, klucz musi trafic do wszystkich 5 locale (en/pl/de/es/ko) przez
  `resolveTranslations().translate(<klucz>, <fallback>)`.
- **Walidacja przed done**: przed uznaniem zadania za skonczone uruchom
  `yarn typecheck` oraz `yarn jest` i upewnij sie, ze przechodza.
