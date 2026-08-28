# ZADANIE M6

## Cel

Modul `loyalty` (`apps/mercato/src/modules/loyalty/`) ma udostepnic odczyt statystyk
punktowych pojedynczego konta lojalnosciowego jako publiczna komende TYLKO-DO-ODCZYTU
**`loyalty.accounts.stats`**. Komenda przyjmuje id konta i zwraca aktualne saldo oraz
agregaty policzone z wpisow ledgera punktow modulu (encja `LoyaltyLedgerEntry`, tabela
`loyalty_ledger_entries` — wpisy naliczen punktow za zamowienia): sume punktow ze
wszystkich wpisow konta, liczbe tych wpisow oraz moment ostatniego naliczenia.
Komenda NICZEGO nie zapisuje — zaden rekord nie powstaje, nie zmienia sie i nie znika.

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Rejestracja i discovery**
   - Kod komendy w `apps/mercato/src/modules/loyalty/commands/` (nazwa pliku dowolna);
     import `apps/mercato/src/modules/loyalty/commands` (przez `commands/index.ts`)
     rejestruje komende side-effectem (`registerCommand` z `@open-mercato/shared/lib/commands`),
     tak jak pozostale komendy modulu.
   - Id komendy: **`loyalty.accounts.stats`**.

2. **Wejscie** — walidowane zodem PRZED jakimkolwiek odczytem:
   - `{ accountId: string (uuid) }`; brak/nieprawidlowe `accountId` → wyjatek walidacji,
     zero odczytow i zero zapisow.

3. **Konto i scoping** (styl jak w istniejacych komendach modulu):
   - konto rezolwowane po `id == accountId` W GRANICACH kontekstu wywolania:
     `tenantId` z `ctx.auth.tenantId`, `organizationId` z `ctx.selectedOrganizationId` /
     `ctx.auth.orgId`, oraz `deletedAt: null`;
   - konto nieznalezione, nalezace do innego tenanta/organizacji albo skasowane miekko →
     `CrudHttpError` ze statusem 404 i trescia rozwiazana przez i18n z ISTNIEJACEGO
     klucza **`loyalty.errors.accountNotFound`** (`resolveTranslations` z
     `@open-mercato/shared/lib/i18n/server`; `CrudHttpError` / helpery z
     `@open-mercato/shared/lib/crud/errors`); ZERO zapisow. To zadanie NIE dodaje
     zadnych nowych kluczy i18n.

4. **Agregaty z ledgera** — liczone WYLACZNIE z wpisow `LoyaltyLedgerEntry`, ktore
   naleza do tego konta (`accountId` wpisu == id konta) ORAZ do tenanta/organizacji
   kontekstu; wpisy innych kont oraz wpisy spoza tenanta/organizacji NIE wchodza do
   zadnego agregatu:
   - **`lifetimePoints`** = suma pol `points` wszystkich pasujacych wpisow; `0` gdy brak wpisow;
   - **`entryCount`** = liczba pasujacych wpisow; `0` gdy brak;
   - **`lastAccrualAt`** = wartosc `createdAt` NAJNOWSZEGO pasujacego wpisu
     (najpozniejsze `createdAt`; dopuszczalny typ: `Date` albo string ISO wskazujacy
     te sama chwile); **`null`** gdy konto nie ma zadnego pasujacego wpisu.

5. **Wynik** — `execute` zwraca obiekt zawierajacy co najmniej:
   `{ accountId, balance, lifetimePoints, entryCount, lastAccrualAt }`,
   gdzie `accountId` = id konta z wejscia, `balance` = aktualne saldo wczytanego konta
   (liczba), a pozostale pola jak w pkt 4.

6. **Read-only, twardo** — w KAZDYM przebiegu (sukces, 404, blad walidacji) komenda nie
   tworzy, nie modyfikuje i nie usuwa zadnych rekordow; saldo konta pozostaje nietkniete.

7. **Dostep do danych** — EntityManager z DI (`ctx.container.resolve('em')`). Ograniczaj
   sie do standardowego API em: `fork/findOne/findOneOrFail/find/count/create/assign/
   persist/persistAndFlush/flush/nativeInsert/nativeUpdate/transactional/getReference`
   (bez QueryBuildera) — tak jak istniejace komendy w tym repo. Zadnych odwolan do encji
   innych modulow.

8. **Unit testy wlasne** — w `apps/mercato/src/modules/loyalty/__tests__/` (styl repo:
   mock `em` + `ctx`, komenda z `commandRegistry` po imporcie `../commands`): happy path
   (suma, licznik, wybor najnowszego wpisu, echo salda), konto bez wpisow (zera + `null`),
   404-y (nieznane id / cudzy tenant / skasowane konto), walidacja przed odczytem,
   brak zapisow.

## Kryteria ukonczenia

- Import `.../loyalty/commands` rejestruje komende; `commandRegistry.get('loyalty.accounts.stats')` zwraca handler.
- Happy path: poprawne `lifetimePoints`/`entryCount`/`lastAccrualAt`/`balance`; wpisy
  innych kont i innych tenantow/organizacji NIE wliczone do zadnego agregatu.
- Konto bez wpisow: `lifetimePoints: 0`, `entryCount: 0`, `lastAccrualAt: null`.
- Nieznane id, konto innego tenanta/organizacji, konto z `deletedAt` → `CrudHttpError(404)`
  z kluczem `loyalty.errors.accountNotFound`; zero zapisow.
- Nieprawidlowe wejscie → wyjatek walidacji przed jakimkolwiek odczytem; zero zapisow.
- Zaden przebieg komendy nie zapisuje, nie modyfikuje ani nie usuwa rekordow.
- `yarn typecheck` i testy modulu zielone; caly istniejacy test-suite repo pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: kazdy odczyt ograniczony do tenanta/organizacji kontekstu.
- **Zero cross-module ORM**: komenda operuje wylacznie na encjach wlasnych modulu
  `loyalty`; zakaz importu encji innych modulow.
- **i18n**: zadnych nowych kluczy w tym zadaniu; komunikat bledu przez
  `resolveTranslations().translate(<istniejacy klucz>, <fallback>)` — zero hardcodow w `throw`.
- **Walidacja przed done**: zod na wejsciu; przed uznaniem zadania za skonczone
  `yarn jest` modulu + pelna suita repo zielona.
