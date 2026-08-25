# ZADANIE T9

## Cel

Na karcie klienta (person detail w module `customers`) ma się pojawić podsumowanie
lojalnościowe: **saldo punktów + aktualny tier**. Wstrzyknięcie odbywa się
WYŁĄCZNIE przez istniejący mechanizm widget-injection modułu `customers`
(spot `detail:customers.person:header`) — moduł `customers` pozostaje NIETKNIĘTY
i nie wie o istnieniu `loyalty`. Dane płyną przez własny serwis DI modułu
`loyalty` i jego własny endpoint API. Twarda granica: ZERO importów ORM/encji
między modułami — relacja wyłącznie po uuid klienta. Jeżeli część artefaktów
istnieje z wcześniejszej pracy pod innymi nazwami, doprowadź stan końcowy
DOKŁADNIE do kontraktu poniżej.

## Wymagania

Poniższe identyfikatory są KONTRAKTEM PUBLICZNYM — muszą się zgadzać co do znaku.

1. **Serwis DI (read-model):** `apps/mercato/src/modules/loyalty/di.ts` eksportuje
   `register(container)` (konwencja modułów, wzorzec:
   `apps/mercato/src/modules/example/di.ts`) oraz
   `export const LOYALTY_SUMMARY_SERVICE = 'loyaltySummaryService'`.
   - Rejestracja: `container.register({ [LOYALTY_SUMMARY_SERVICE]:
     asFunction(...).scoped() })` — kontener działa w trybie awilix CLASSIC
     (zależności rozwiązywane po NAZWACH parametrów fabryki); serwis zależy
     WYŁĄCZNIE od `em` (EntityManager z DI). Lifetime `scoped` jest wymagany —
     singleton przypiąłby `em` jednego requestu na życie procesu.
   - API serwisu: `getCustomerSummary({ tenantId, organizationId, customerId })`
     → `Promise<{ balance: number, tier: string | null }>`:
     - konto: `em.findOne(LoyaltyAccount, { tenantId, organizationId, customerId,
       deletedAt: null })` — pełny tenant/org-scoping (w klauzuli zapytania ALBO
       jawnym sprawdzeniem po odczycie; konto innego tenanta/organizacji = nie
       istnieje);
     - brak konta / konto spoza zasięgu → `{ balance: 0, tier: null }` (bez
       wyjątku);
     - `balance` = saldo konta (`LoyaltyAccount.balance`); `tier` = aktualny tier
       lojalnościowy konta wyznaczany logiką tierów modułu `loyalty` (jeżeli moduł
       ją posiada z wcześniejszej pracy — użyj jej, nie pisz drugiej kopii); typ
       ZAWSZE `string | null`; moduł bez tierów / konto bez tieru → `null`;
     - serwis jest READ-ONLY: zero `flush`/`persist`/mutacji.

2. **Endpoint API:** `apps/mercato/src/modules/loyalty/api/customers/summary/route.ts`
   (URL: `GET /api/loyalty/customers/summary?customerId=<uuid>`):
   - `export const metadata = { GET: { requireAuth: true, requireFeatures:
     ['loyalty.accounts.view'] } }` — brama uprawnień (egzekwowana centralnie po
     tej deklaracji);
   - `export async function GET(req)`: kontener requestowy
     (`createRequestContainer`), auth z requestu (`getAuthFromRequest`); brak
     auth / brak `tenantId` → response 401; `customerId` z query stringa,
     walidowany zodem (uuid) PRZED odczytem — brak/niepoprawny → response 400,
     serwis NIE jest wołany;
   - `tenantId`/`organizationId` WYŁĄCZNIE z auth/scope requestu — parametry
     query poza `customerId` są ignorowane (query nie może przestawić scope);
   - dane WYŁĄCZNIE przez serwis `LOYALTY_SUMMARY_SERVICE` z kontenera; response
     200 JSON `{ balance, tier }` (wynik serwisu bez przeróbek).

3. **Widget injection:**
   `apps/mercato/src/modules/loyalty/widgets/injection/customer-loyalty-summary/`
   z plikami `widget.ts` (definicja) i `widget.client.tsx` (komponent kliencki):
   - `widget.ts` default-eksportuje `InjectionWidgetModule`
     (`@open-mercato/shared/modules/widgets/injection`) z `metadata`:
     `id: 'loyalty.injection.customer-loyalty-summary'`, `features` zawiera
     `'loyalty.accounts.view'`, `requiredModules` zawiera `'customers'`,
     `enabled: true`, oraz z `Widget` = komponent z `widget.client.tsx`
     (wzorzec: `packages/core/src/modules/customers/widgets/injection/
     ai-deal-detail-trigger/`);
   - komponent bierze id osoby z props: `context.personId`, z fallbackiem
     `context.data?.person?.id` / `data?.person?.id` (kontrakt kontekstu strony
     person detail); brak id → renderuje `null` i NIE woła API; bez hooków
     routera;
   - dane przez `apiFetch` z `@open-mercato/ui/backend/utils/api` na endpoint
     z pkt 2 (`/api/loyalty/customers/summary?customerId=<id>`); response `!ok`
     albo błąd sieci → bez crasha (brak renderu albo stan błędu);
   - render: kontener `data-testid="loyalty-customer-summary"`; saldo w elemencie
     `data-testid="loyalty-customer-summary-balance"` (tekst zawiera liczbę
     salda); tier w elemencie `data-testid="loyalty-customer-summary-tier"`
     renderowanym TYLKO gdy `tier !== null`;
   - etykiety przez `useT` (`@open-mercato/shared/lib/i18n/context`); klucze
     `loyalty.widgets.customerSummary.title`,
     `loyalty.widgets.customerSummary.balance`,
     `loyalty.widgets.customerSummary.tier` dodane do WSZYSTKICH 5 locale modułu
     (`i18n/{de,en,es,ko,pl}.json`) z niepustymi, przetłumaczonymi wartościami.

4. **Injection table:** `apps/mercato/src/modules/loyalty/widgets/injection-table.ts`
   (default-eksport `ModuleInjectionTable`) mapuje spot
   **`detail:customers.person:header`** na widget
   `loyalty.injection.customer-loyalty-summary` (wzorzec:
   `packages/core/src/modules/customers/widgets/injection-table.ts`).

5. **Izolacja modułów (twarda):**
   - moduł `customers` pozostaje NIETKNIĘTY: żadnych importów z modułu `loyalty`
     nigdzie w `packages/core/src/modules/customers/**`; istniejący host
     injection person detail zostaje jak jest (spot `detail:customers.person:header`
     w `extension-points.ts`, `<InjectionSpot>` na stronie `people-v2/[id]`);
   - moduł `loyalty` NIE importuje NICZEGO z
     `@open-mercato/core/modules/customers/data/**` ani encji ORM żadnego innego
     modułu; klient jest identyfikowany wyłącznie przez uuid.

6. **Testy własne** — w `apps/mercato/src/modules/loyalty/__tests__/` (styl OM):
   serwis (saldo, brak konta, scoping), route (200/400/401, scope z auth),
   render widgetu (mock `apiFetch`).

## Kryteria ukończenia

- `di.ts`: `register` + `LOYALTY_SUMMARY_SERVICE === 'loyaltySummaryService'`;
  rejestracja awilix `scoped`; serwis rozwiązywalny z kontenera CLASSIC z samym
  `em`; `getCustomerSummary` zwraca saldo konta z tenant/org kontekstu oraz
  `{ balance: 0, tier: null }` dla konta nieistniejącego lub spoza zasięgu;
  zero zapisów.
- Route pod pinowaną ścieżką z bramą `GET: requireAuth + ['loyalty.accounts.view']`;
  200 z `{ balance, tier }` z serwisu; 400 dla braku/złego `customerId` (serwis
  niewołany); 401 bez auth; scope wyłącznie z auth (query go nie nadpisze).
- Widget wykrywalny konwencją `widgets/injection/**/widget.ts` z pinowaną
  `metadata`; `injection-table.ts` mapuje `detail:customers.person:header` na
  pinowany widget id; na karcie klienta widget renderuje saldo i tier z API
  (testowalne przez pinowane `data-testid`).
- Izolacja: zero importów loyalty w `customers`, zero importów ORM `customers`
  w `loyalty`.
- Klucze i18n w 5 locale; `yarn typecheck` i testy modułu przechodzą; cała
  istniejąca suita repo (w tym testy modułu `customers`) pozostaje zielona.

## Konwencje

- **Tenant/org-scoping**: każdy odczyt ograniczony do tenanta/organizacji
  kontekstu requestu; identyfikatory scope zawsze z auth, nigdy z query/body.
- **Zero cross-module ORM**: integracja między `loyalty` a `customers` wyłącznie
  przez uuid + injection spot + własne API/serwis DI modułu `loyalty`.
- **i18n ×5 (de/en/es/ko/pl)**: każdy user-facing string przez `useT`/
  `resolveTranslations` z kluczami we wszystkich 5 locale — zero hardcodów.
- **Walidacja przed done**: zod na wejściu endpointu przed odczytem; przed
  uznaniem zadania za skończone `yarn typecheck` + testy modułu + pełna suita
  repo zielona.
