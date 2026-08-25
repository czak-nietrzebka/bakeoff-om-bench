# ZADANIE T7

## Cel

Gdy naliczenie punktow za zamowienie przenosi konto lojalnosciowe przez prog tieru,
operator ma dostac o tym notyfikacje. Zepnij trzy istniejace elementy platformy w jeden
przeplyw: dane zamowien sprzedazy (modul `sales`, wylacznie przez DI/eventy) → domena
lojalnosciowa (modul `loyalty`: naliczenie + rozstrzygniecie tieru) → dorczenie
(modul `notifications`: typ notyfikacji z JAWNYMI defaultami kanalow, subscriber,
renderer, i18n x5). Konkretnie: komenda naliczenia emituje event **`loyalty.tier.changed`**
przy AWANSIE tieru, trwaly subscriber modulu `loyalty` konsumuje ten event i tworzy
notyfikacje typu **`loyalty.tier.changed`** dla uzytkownikow z uprawnieniem
`loyalty.accounts.view`. Modul `loyalty` istnieje po wczesniejszych zadaniach (w tym
encja `LoyaltyTier` z progami i helper `resolveTierForBalance` z `data/tiers.ts`) —
rozszerzasz go; kontrakt publiczny ponizej jest wiazacy. Wzorce: emisja
`customers.deal.won` w `packages/core/src/modules/customers/commands/deals.ts`,
para subscriber+lib `packages/core/src/modules/customers/subscribers/deal-closure-notification.ts`
+ `customers/lib/dealClosureNotification.ts`, deklaracje typow
`packages/core/src/modules/customers/notifications.ts` i
`packages/core/src/modules/sales/notifications.client.ts`.

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Deklaracja eventu** — plik `apps/mercato/src/modules/loyalty/events.ts`
   deklaruje event **`loyalty.tier.changed`** przez `createModuleEvents` z
   `@open-mercato/shared/modules/events` (`moduleId: 'loyalty'`; label/kategoria
   opisowe, np. `category: 'lifecycle'`); eksportuje `eventsConfig` (takze jako
   default). Po imporcie pliku event jest widoczny w `getDeclaredEvents()`.

2. **Detekcja progu i emisja** — w komendzie **`loyalty.accruals.accrueOrder`**
   (kontrakt serii, po zmianie wymagan T5 naliczajacej per linia), WYLACZNIE gdy
   naliczenie faktycznie zaszlo (wynik `created` >= 1):
   - `tiers = em.find(LoyaltyTier, { tenantId, organizationId, deletedAt: null })`
     — pelny tenant/org-scoping (progi cudzego tenanta NIE istnieja dla tego konta);
   - `before = resolveTierForBalance(tiers, <saldo przed uznaniem>)`,
     `after = resolveTierForBalance(tiers, <saldo po uznaniu>)` — uzyj helpera
     z `data/tiers.ts`, nie drugiej kopii tej logiki;
   - **AWANS** = `after != null && (before == null || after.minPoints > before.minPoints)`
     → DOKLADNIE JEDNA emisja:
     `eventBus.emitEvent('loyalty.tier.changed', payload, { persistent: true, tenantId, organizationId })`,
     gdzie `eventBus = ctx.container.resolve('eventBus')` (wzorzec `deals.ts`);
     przeskok o kilka progow naraz = JEDEN event z tierem KONCOWYM;
   - payload: `{ accountId, customerId, tenantId, organizationId,
     previousTierId: string|null, previousTierName: string|null,
     newTierId: string, newTierName: string, balance: <saldo po uznaniu, int> }`;
   - ZERO emisji gdy: tier bez zmian, powtorka idempotentna (`created: 0`),
     `points <= 0`, brak tierow w zasiegu tenant/org;
   - emisja jest owinieta try/catch z logiem — jej awaria NIE moze wywrocic
     naliczenia (fail-open na powiadomieniu, nie na domenie).

3. **Typ notyfikacji z JAWNYMI defaultami kanalow** — plik
   `apps/mercato/src/modules/loyalty/notifications.ts` eksportuje
   `notificationTypes: NotificationTypeDefinition[]` (typ z
   `@open-mercato/shared/modules/notifications/types`; eksport nazwany ORAZ default)
   z wpisem:
   - `type: 'loyalty.tier.changed'`, `module: 'loyalty'`;
   - **`channels: ['in_app', 'email']`** — deklaracja JAWNA; `push` swiadomie
     POZA zbiorem (awans tieru nie budzi telefonu); to pole zasila centralna
     bramke eligibility (`shouldDeliver` / `resolveEligibleChannels`);
   - `titleKey: 'loyalty.notifications.tier.changed.title'`,
     `bodyKey: 'loyalty.notifications.tier.changed.body'`;
   - `severity: 'success'`, niepusty `icon`, akcja `{ id: 'view',
     labelKey: 'common.view', ... }` (href/linkHref wedle uznania);
   - bez `nonOptOut` (uzytkownik moze wylaczyc typ per kanal).

4. **Subscriber** — dokladnie JEDEN plik bezposrednio w
   `apps/mercato/src/modules/loyalty/subscribers/` z
   `export const metadata = { event: 'loyalty.tier.changed', persistent: true, id: 'loyalty:<slug>' }`
   i `export default async function handler(payload, ctx)`:
   - fail-closed: brak `tenantId` / `accountId` / `newTierName` w payloadzie →
     zakoncz bez wyjatku i bez tworzenia notyfikacji;
   - serwis: `resolveNotificationService(container)` z
     `@open-mercato/core/modules/notifications/lib/notificationService`
     (`container = ctx.container ?? { resolve: ctx.resolve }`);
   - budowa: `buildFeatureNotificationFromType(typeDef, { requiredFeature:
     'loyalty.accounts.view', bodyVariables: { tierName: payload.newTierName, ... },
     sourceEntityType: 'loyalty:loyalty_account', sourceEntityId: payload.accountId })`
     z `@open-mercato/core/modules/notifications/lib/notificationBuilder`, gdzie
     `typeDef` to wpis z pkt 3 (import z `../notifications`);
   - dostarczenie: `await service.createForFeature(input, { tenantId:
     payload.tenantId, organizationId: payload.organizationId ?? null })` —
     odbiorcy = uzytkownicy z feature **`loyalty.accounts.view`** w tenant/org
     konta;
   - blad `createForFeature` → log warn, bez rethrow (wzorzec
     `dealClosureNotification`).

5. **Renderer** — komponent kliencki
   `apps/mercato/src/modules/loyalty/widgets/notifications/LoyaltyTierChangedRenderer.tsx`
   (`'use client'`, props `NotificationRendererProps`), ktory pokazuje nazwe tieru
   z `notification.bodyVariables?.tierName`; podpiety w
   `apps/mercato/src/modules/loyalty/notifications.client.ts` — plik eksportuje
   (default) tablice `NotificationTypeDefinition[]` z wpisem
   `type: 'loyalty.tier.changed'` i polem `Renderer` wskazujacym ten komponent
   (wzorzec: `sales/notifications.client.ts`). Renderer trzymaj lekki (react +
   `@open-mercato/shared`/`@open-mercato/ui` primitives) — zadnych importow
   server-only.

6. **i18n x5** — klucze `loyalty.notifications.tier.changed.title` i
   `loyalty.notifications.tier.changed.body` we WSZYSTKICH PIECIU plikach locale
   modulu (`i18n/en.json`, `pl.json`, `de.json`, `es.json`, `ko.json`), niepuste,
   przetlumaczone (nie kopie angielskiego); wartosc `...body` w KAZDYM locale
   zawiera placeholder **`{tierName}`**.

7. **Unit testy wlasne** — w `apps/mercato/src/modules/loyalty/__tests__/`
   (styl OM: mock `em` + `ctx`, subscriber przez discovery z katalogu
   `subscribers/`, serwis notyfikacji mockowany): emisja przy przekroczeniu progu
   i cisza bez przekroczenia, fail-closed subscribera, ksztalt inputu
   `createForFeature`, eligibility kanalow z deklaracji `channels`.

## Kryteria ukonczenia

- Import `events.ts` deklaruje `loyalty.tier.changed` (widoczny w `getDeclaredEvents()`).
- Naliczenie przenoszace saldo przez prog emituje DOKLADNIE jeden
  `loyalty.tier.changed` z kompletem pol payloadu i opcjami
  `{ persistent: true, tenantId, organizationId }`; naliczenie bez zmiany tieru,
  powtorka idempotentna i brak tierow w zasiegu nie emituja nic; progi cudzego
  tenanta sa ignorowane.
- Subscriber jest dokladnie jeden dla `loyalty.tier.changed`, trwaly, i dla
  poprawnego payloadu wola `createForFeature` z typem `loyalty.tier.changed`,
  feature `loyalty.accounts.view`, `bodyVariables.tierName` = nazwa nowego tieru
  i scope tenant/org z payloadu; payload niekompletny → zero wywolan, zero wyjatkow.
- `notifications.ts` deklaruje typ z JAWNYM `channels: ['in_app', 'email']`;
  centralna bramka eligibility wyklucza `push` dla tego typu, a operator-override
  kanalow ja zastepuje (zachowanie `resolveEligibleChannels`/`shouldDeliver`).
- `notifications.client.ts` podpina `LoyaltyTierChangedRenderer` pod ten typ.
- Oba klucze i18n obecne w 5 locale, body wszedzie z `{tierName}`.
- `yarn typecheck` i testy modulu przechodza; caly istniejacy test-suite repo
  pozostaje zielony.

## Konwencje

- **Tenant/org-scoping**: progi tierow, konto i odbiorcy notyfikacji zawsze w
  tenancie/organizacji kontekstu lub payloadu eventu; nigdy dane cross-tenant.
- **Zero cross-module ORM**: dane `sales` wylacznie przez tokeny DI, dorczenie
  wylacznie przez API modulu `notifications` (service/builder) i event bus —
  zadnych importow cudzych encji.
- **i18n x5**: kazdy user-facing string przez klucze i18n obecne we wszystkich
  5 locale (en/pl/de/es/ko); stringi czysto techniczne prefiksuj `[internal]`.
- **Walidacja przed done**: payload eventu walidowany przed jakimkolwiek zapisem
  (fail-closed); przed uznaniem zadania za skonczone uruchom `yarn typecheck`
  oraz `yarn jest` i upewnij sie, ze przechodza.
