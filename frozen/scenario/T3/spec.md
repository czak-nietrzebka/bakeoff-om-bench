# ZADANIE T3

## Cel

Moduł `loyalty` (`apps/mercato/src/modules/loyalty`) ma automatycznie naliczać punkty
lojalnościowe po zakończeniu zamówienia. Zbuduj trwały (persistent) subscriber eventu
`sales.order.completed`, który dopisuje do konta lojalnościowego klienta
`Math.round(total * rate)` punktów. Naliczenie musi być idempotentne: ponowne doręczenie
tego samego eventu (at-least-once delivery, replay — także po restarcie procesu) NIE
nalicza punktów drugi raz. Moduł `loyalty` istnieje po wcześniejszych zadaniach —
rozszerzasz go; jeżeli dotychczasowe artefakty modułu realizują część poniższego
kontraktu pod innymi nazwami, doprowadź stan końcowy do kontraktu z tego zadania
(kontrakt publiczny poniżej jest wiążący).

## Wymagania

1. **Subscriber (auto-discovery konwencją modułów):** dokładnie JEDEN plik bezpośrednio
   w `apps/mercato/src/modules/loyalty/subscribers/` (slug w nazwie pliku dowolny);
   wzorzec: `packages/core/src/modules/customers/subscribers/deal-closure-notification.ts`.
   Eksporty pliku:
   - `export const metadata = { event: 'sales.order.completed', persistent: true, id: 'loyalty:<slug>' }`
     (`id` z prefiksem `loyalty:`);
   - `export default async function handler(payload, ctx)` — `ctx` udostępnia
     `resolve(name)` (DI) oraz opcjonalnie `container.resolve(name)`.
   - Żaden inny plik modułu `loyalty` nie subskrybuje tego eventu (drugi subscriber
     = podwójne naliczenie).
2. **Kontrakt payloadu:** `{ orderId, tenantId, organizationId, customerId, total }`
   (`total`: number — suma zamówienia w walucie; identyfikatory: string/uuid).
   Pola nadmiarowe ignoruj.
3. **Fail-closed:** brak `orderId` / `tenantId` / `organizationId` / `customerId` albo
   `total` niebędący skończoną liczbą → handler kończy się bez wyjątku i bez ŻADNEGO
   zapisu.
4. **Formuła naliczenia:** `points = Math.round(total * LOYALTY_ORDER_RATE)`, gdzie
   `LOYALTY_ORDER_RATE = 0.1` (stała modułu `loyalty`: 1 punkt za każde pełne 10
   jednostek waluty; zaokrąglenie matematyczne JS `Math.round`). Gdy `points === 0`
   → zakończ bez zapisu.
5. **Konto lojalnościowe — kontrakt publiczny:** encja `LoyaltyAccount` eksportowana
   z `apps/mercato/src/modules/loyalty/data/entities.ts`, z polami co najmniej:
   `id`, `tenantId`, `organizationId`, `customerId`, `balance` (liczba całkowita,
   nigdy ujemna). Lookup konta:
   `em.findOne(LoyaltyAccount, { tenantId, organizationId, customerId })`.
   Brak konta → utwórz je przez `em.create(LoyaltyAccount, ...)` z polami
   `tenantId` / `organizationId` / `customerId` z payloadu i saldem `0`, po czym nalicz.
   Naliczenie: `balance += points`.
6. **Idempotencja (twarda):** klucz idempotencji = `(tenantId, orderId)`. Naliczenie
   zostawia TRWAŁY wpis w bazie z tym kluczem (encja transakcji/ledger modułu `loyalty`
   w `data/entities.ts`; jeżeli moduł ma już encję transakcji punktowych — użyj jej,
   rozszerzając o klucz; jeżeli nie — dodaj nową, np. `LoyaltyPointsTransaction`),
   z indeksem UNIQUE `(tenant_id, order_id)` w migracji. Przed naliczeniem sprawdź
   istnienie wpisu (`em.findOne` / `em.count` po kluczu) — wpis istnieje → zakończ bez
   zapisu. Dedupe MUSI przetrwać restart procesu: pamięć procesu (Set/Map/zmienna
   modułu) NIE spełnia wymagania.
7. **Dostęp do danych:** wyłącznie `em` z DI (`ctx.resolve('em')`; dozwolone `fork()`
   i `transactional()`); operacje przez `em.findOne` / `em.count` / `em.create` /
   `em.persist` / `em.flush` / `em.persistAndFlush`. Bez surowego SQL i bez
   QueryBuildera. Zero importów encji/ORM innych modułów — integracja cross-module
   wyłącznie przez eventy.
8. **Migracje:** nowe tabele/indeksy mają migrację MikroORM w
   `apps/mercato/src/modules/loyalty/migrations/`.
9. **Testy własne:** testy jednostkowe subscribera z fake-eventami i fake `em`
   (happy path, zaokrąglanie, replay, fail-closed) w
   `apps/mercato/src/modules/loyalty/__tests__/`, w stylu istniejących testów
   subscriberów (`packages/core/src/modules/customers/subscribers/__tests__/`).

## Kryteria ukończenia

- Subscriber jest wykrywalny konwencją (plik w `subscribers/`, metadata jak wyżej)
  i jest dokładnie jeden dla eventu `sales.order.completed`.
- Dla poprawnego payloadu saldo konta rośnie dokładnie o `Math.round(total * 0.1)`;
  konto powstaje automatycznie, gdy nie istnieje.
- Ponowne doręczenie eventu o tym samym `(tenantId, orderId)` — również po restarcie
  procesu — nie zmienia salda i nie dodaje żadnych wpisów.
- Różne zamówienia (różne `orderId`) naliczają się niezależnie i sumują.
- Payload niekompletny/niepoprawny oraz przypadek `points === 0` → zero zapisów,
  zero wyjątków.
- `yarn typecheck` i testy modułu przechodzą.

## Konwencje

- Tenant/org-scoping w każdym zapytaniu i zapisie (`tenantId` + `organizationId`) —
  nigdy dane cross-tenant.
- Zero cross-module ORM: nie importuj encji innych modułów; integracja przez eventy.
- i18n ×5 (de/en/es/ko/pl): każdy user-facing string przez `resolveTranslations` /
  `t(...)` z plikami w `i18n/`; subscriber nie powinien mieć user-facing stringów —
  komunikaty czysto techniczne prefiksuj `[internal]`.
- Walidacja wejścia przed zapisem; przed uznaniem zadania za skończone przejdź
  sekwencję walidacji projektu (typecheck + testy).
