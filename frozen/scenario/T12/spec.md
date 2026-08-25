# ZADANIE T12

## Cel

Konto lojalnosciowe staje sie pelnoprawnym obywatelem platformy: (1) encja
`loyalty:loyalty_account` wchodzi do globalnego wyszukiwania (Cmd+K) i do query-indexu —
po reindeksie KAZDE konto ma w wynikach wyszukiwania DOKLADNIE JEDEN hit; (2) modul
deklaruje pole niestandardowe **`vip_note`** na koncie lojalnosciowym przez `ce.ts`
(zapisywalne przez istniejace CRUD API jako `cf_vip_note`, indeksowane i przeszukiwalne);
(3) modul deklaruje jawne powiazanie konta z klientem przez **`defineLink`**
(`data/extensions.ts`) — bez zadnej relacji ORM. Wzorzec do nasladowania w calosci:
`apps/mercato/src/modules/example/` (`search.ts`, `ce.ts`, `data/extensions.ts`).

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **`apps/mercato/src/modules/loyalty/search.ts`** — konfiguracja wyszukiwania modulu
   (wzorzec: `apps/mercato/src/modules/example/search.ts`):
   - `export const searchConfig: SearchModuleConfig` (typ z
     `@open-mercato/shared/modules/search`) jako LITERAL obiektowy z literalna tablica
     `entities` (generator rejestru parsuje ten plik statycznie — struktura jak w
     example); dodatkowo `export default searchConfig` i `export const config = searchConfig`;
   - dokladnie JEDEN wpis `entities` dla `entityId: 'loyalty:loyalty_account'`:
     - `enabled: true`;
     - `aclFeatures: ['loyalty.accounts.view']` (feature modulu z wczesniejszej pracy);
     - `buildSource(ctx)`: buduje `SearchIndexSource` z rekordu indeksu (klucze rekordu
       snake_case, jak w example: `ctx.record.id`, `ctx.record.customer_id`) oraz pol
       niestandardowych (`ctx.customFields.vip_note`); polaczony tekst zrodla MUSI
       zawierac wartosc `customer_id` konta oraz — gdy niepusta — wartosc `vip_note`;
       zwraca niepusty obiekt dla kazdego zywego rekordu (samo `customer_id` wystarcza);
       ustawia `presenter` i `checksumSource`;
     - `formatResult(ctx)`: `SearchResultPresenter` z niepustym `title` oraz
       `badge` rozwiazywanym przez i18n z klucza **`loyalty.search.badge`**
       (`resolveTranslations` z `@open-mercato/shared/lib/i18n/server`, jak w example);
     - `resolveUrl(ctx)`: sciezka zaczynajaca sie od `/backend/loyalty/` i zawierajaca
       id rekordu.
2. **`apps/mercato/src/modules/loyalty/ce.ts`** — deklaracja pol niestandardowych
   (wzorzec: `packages/core/src/modules/customers/ce.ts` — wpis dla istniejacej encji
   ORM): `export const entities` (i `export default entities`) z wpisem
   `{ id: 'loyalty:loyalty_account', label: <opisowy>, showInSidebar: false, fields: [...] }`,
   gdzie `fields` zawiera pole:
   - `key: 'vip_note'`, `kind: 'multiline'`, niepusty `label`;
   - `formEditable: true` (zapisywalne przez CRUD API fabryki jako `cf_vip_note` —
     route kont ma ustawione `entityId: 'loyalty:loyalty_account'` z wczesniejszej
     pracy, wiec sciezka custom fields dziala bez zmian w route);
   - `filterable: true`, `indexed: true` (wartosc trafia do dokumentu query-indexu,
     skad czyta ja `buildSource`).
3. **`apps/mercato/src/modules/loyalty/data/extensions.ts`** — deklaracja powiazania
   (wzorzec: `apps/mercato/src/modules/example/data/extensions.ts`): tablica
   eksportowana jako `extensions` ORAZ `export default`, zawierajaca dokladnie jeden
   wpis zbudowany przez **`defineLink`** z `@open-mercato/shared/modules/dsl`:
   - base `'customers:customer_entity'`, extension `'loyalty:loyalty_account'`;
   - `join: { baseKey: 'id', extensionKey: 'customer_id' }`;
   - `cardinality: 'one-to-many'` (jeden klient — konta w wielu organizacjach);
   - niepusty `description`;
   - BEZ wlasnej tabeli posredniej i BEZ relacji ORM — link to deklaracja nad zwykla
     kolumna uuid `customer_id`; pola `table` nie deklaruj (regularna liczba mnoga
     `loyalty_account -> loyalty_accounts` jest derywowana poprawnie) albo zadeklaruj
     dokladnie `'loyalty_accounts'`.
4. **Rejestracja i indeks dzialaja end-to-end:**
   - po dodaniu plikow uruchom `yarn generate` (rejestr modulow podnosi search/ce/extensions);
   - reindeks encji: `yarn mercato query_index reindex --entity loyalty:loyalty_account --tenant <tenantId> --force`
     przebudowuje dokumenty i tokeny wyszukiwania kont;
   - po reindeksie zapytanie `GET /api/search/search?q=<fraza>&strategies=tokens&entityTypes=loyalty:loyalty_account`
     zwraca dla frazy unikalnej dla danego konta DOKLADNIE JEDEN wynik
     (`entityId: 'loyalty:loyalty_account'`, `recordId` = id konta) — zero duplikatow
     takze po PONOWNYM reindeksie;
   - aktualizacja `cf_vip_note` przez PUT na CRUD API kont + reindeks → stara fraza
     przestaje znajdowac konto, nowa znajduje je dokladnie raz;
   - wyniki respektuja scoping tenant/org (konto nigdy nie jest widoczne w cudzym
     tenancie/organizacji).
5. **i18n** — klucz `loyalty.search.badge` (oraz kazdy inny nowy klucz `loyalty.search.*`
   uzyty w prezenterze) dodany do WSZYSTKICH PIECIU locale modulu
   (`i18n/en.json`, `pl.json`, `de.json`, `es.json`, `ko.json`) z niepustymi,
   naprawde przetlumaczonymi wartosciami (pelny parytet kluczy `loyalty.*` obowiazuje).
6. **Testy wlasne** — unit testy w `apps/mercato/src/modules/loyalty/__tests__/`
   (kontrakt searchConfig: buildSource/formatResult/resolveUrl na fake ctx; kontrakt
   ce/extensions) w stylu istniejacych testow OM.

## Kryteria ukonczenia

- `search.ts`, `ce.ts` i `data/extensions.ts` istnieja i spelniaja kontrakty z pkt 1-3;
  `yarn generate` przechodzi i podnosi wszystkie trzy deklaracje.
- `buildSource` indeksuje `customer_id` i `vip_note`; `formatResult` daje niepusty
  `title` i badge z klucza `loyalty.search.badge`; `resolveUrl` prowadzi pod
  `/backend/loyalty/...` z id rekordu.
- Po utworzeniu kont przez CRUD API (w tym `cf_vip_note`) i reindeksie kazde konto ma
  dokladnie jeden hit w `/api/search/search` dla swojej unikalnej frazy; ponowny
  reindeks nie tworzy duplikatow; po zmianie `vip_note` stara fraza znika, nowa
  znajduje konto dokladnie raz.
- Klucze `loyalty.search.*` obecne we wszystkich 5 locale z pelnym parytetem.
- Kanoniczna walidacja repo zielona:
  `yarn build:packages && yarn generate && yarn build:packages && yarn i18n:check-sync && yarn i18n:check-usage && yarn typecheck && yarn test && yarn build:app`.

## Konwencje

- **Tenant/org-scoping**: dokumenty indeksu i wyniki wyszukiwania zawsze w obrebie
  tenanta/organizacji wywolujacego; zadnych danych cross-tenant.
- **Zero cross-module ORM**: powiazanie z klientem WYLACZNIE przez deklaracje
  `defineLink` nad kolumna uuid — zero importow encji `customers`, zero relacji ORM.
- **i18n x5** (de/en/es/ko/pl): kazdy user-facing string prezentera przez
  `resolveTranslations` / `t(...)` z kluczem `loyalty.*` obecnym we wszystkich 5 locale;
  komunikaty czysto techniczne prefiksuj `[internal]`.
- **Walidacja przed done**: przed uznaniem zadania za skonczone przejdz pelna
  kanoniczna sekwencje walidacji projektu (build + generate + i18n + typecheck +
  testy + build aplikacji).
