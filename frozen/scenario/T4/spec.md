# ZADANIE T4

## Cel

Dodaj do modułu `loyalty` (`apps/mercato/src/modules/loyalty`) operację **redeem**
(wydanie punktów z konta lojalnościowego): komendę `loyalty.points.redeem` oraz
endpoint HTTP chroniony NOWYM ACL-feature `loyalty.points.redeem`. Saldo konta nigdy
nie schodzi poniżej zera — wykorzystaj (nie duplikuj) guard nieujemnego salda
wprowadzony w module we wcześniejszym zadaniu. Moduł istnieje — rozszerzasz go;
kontrakt publiczny poniżej jest wiążący.

## Wymagania

1. **ACL (`acl.ts`):** do tablicy `features` w `apps/mercato/src/modules/loyalty/acl.ts`
   dopisz feature `{ id: 'loyalty.points.redeem', title: <opisowy>, module: 'loyalty' }`
   (ewentualne `dependsOn` wyłącznie na feature zadeklarowane; wzorzec:
   `packages/core/src/modules/customers/acl.ts`).
2. **Komenda:** `CommandHandler` (typ z `@open-mercato/shared/lib/commands`) o id
   **`loyalty.points.redeem`**, rejestrowany przez `registerCommand(...)` jako
   side-effect importu `apps/mercato/src/modules/loyalty/commands/index.ts`
   (konwencja: `packages/core/src/modules/customers/commands/`).
3. **Input komendy:** `{ tenantId, organizationId, customerId, points }`.
   Walidacja zod (`data/validators.ts`): `points` — liczba całkowita > 0;
   identyfikatory wymagane. Niepoprawny input → wyjątek, zero zapisu
   (w szczególności `points` ujemny NIE może „naliczyć” punktów).
4. **Logika `execute(input, ctx)`** (em przez `ctx.container.resolve('em')`):
   - konto: `em.findOne(LoyaltyAccount, { tenantId, organizationId, customerId })` —
     pełny tenant/org-scoping (konto innego tenanta/organizacji = nie istnieje);
     brak konta → `CrudHttpError` ze statusem 404
     (`@open-mercato/shared/lib/crud/errors`);
   - **guard nigdy-ujemne (reuse):** `points > balance` → `CrudHttpError` ze
     statusem 400, saldo bez zmian, zero zapisu; wykorzystaj istniejący w module
     guard/helper nieujemnego salda — nie pisz drugiej kopii tej reguły;
   - `points <= balance` → `balance -= points` + flush; redeem całego
     salda (do 0) jest legalny;
   - wynik: obiekt zawierający co najmniej pole `balance` (saldo po operacji).
5. **Endpoint:** `apps/mercato/src/modules/loyalty/api/points/redeem/route.ts`:
   - `export const metadata = { POST: { requireAuth: true, requireFeatures: ['loyalty.points.redeem'] } }`
     — to jest brama uprawnień (egzekwowana centralnie po tej deklaracji);
   - `export async function POST(req)`: auth z requestu; `tenantId` / `organizationId`
     **z auth/scope requestu, nigdy z body**; body: `{ customerId, points }`;
     wywołanie komendy; `CrudHttpError` mapowany na response o tym samym statusie
     (wzorzec: `packages/core/src/modules/customers/api/interactions/cancel/route.ts`).
6. **Komunikaty błędów** user-facing przez i18n (`loyalty.errors.*`), pliki lokalizacji
   ×5 (de/en/es/ko/pl).
7. **Testy własne:** allowed (poprawny redeem), denied (brak feature → brama
   deklaracyjna route), insufficient-balance; w
   `apps/mercato/src/modules/loyalty/__tests__/`, w stylu
   `packages/core/src/modules/customers/commands/__tests__/deletePerson.test.ts`.

## Kryteria ukończenia

- Feature `loyalty.points.redeem` zadeklarowany w `acl.ts` modułu `loyalty`.
- Po imporcie `commands` modułu komenda `loyalty.points.redeem` jest dostępna
  w `commandRegistry`.
- Poprawny redeem zmniejsza saldo dokładnie o `points` i zwraca nowe saldo;
  redeem równy saldu zostawia saldo 0.
- Redeem większy niż saldo → odrzucenie ze statusem 400 bez jakiejkolwiek zmiany
  stanu; saldo nigdy nie jest ujemne.
- Input niepoprawny (`points` ≤ 0, niecałkowite, braki pól) → odrzucenie bez zmiany
  stanu.
- Konto spoza tenanta/organizacji requestu jest niewidoczne (404), jego saldo
  nietknięte.
- Route deklaruje bramę: `requireAuth: true` + `requireFeatures:
  ['loyalty.points.redeem']`, a handler `POST` istnieje.
- `yarn typecheck` i testy modułu przechodzą.

## Konwencje

- Tenant/org-scoping w każdym zapytaniu i zapisie — nigdy dane cross-tenant;
  identyfikatory scope zawsze z auth, nie z body.
- Zero cross-module ORM: nie importuj encji innych modułów.
- i18n ×5 (de/en/es/ko/pl) dla wszystkich user-facing stringów; komunikaty czysto
  wewnętrzne prefiksuj `[internal]`.
- Walidacja wejścia przed zapisem; przed uznaniem zadania za skończone przejdź
  sekwencję walidacji projektu (typecheck + testy).
