# ZADANIE T10

## Cel

Stawka naliczania punktow za zamowienia przestaje byc stala zaszyta w kodzie i staje sie
KONFIGURACJA rozwiazywana per organizacja przez modul `configs` (serwis `moduleConfigService`
z DI). Rozwiazywanie stawki idzie od ogolu do szczegolu: wpis globalny (instance) -> wpis
per TENANT -> nadpisanie per ORGANIZACJA; wygrywa najbardziej szczegolowy istniejacy poziom.
Dodatkowo migracja MikroORM przenosi dotychczasowa GLOBALNA stawke serii (1 punkt za kazda
pelna jednostke waluty netto, dotad implicytna w kodzie komendy) do modulu configs jako wpis
instance-scope. Komenda `loyalty.accruals.accrueOrder` z wczesniejszej pracy w tej serii
stosuje odtad stawke WEWNATRZ swojej dotychczasowej matematyki (kanon serii po zmianie
wymagan T5: naliczanie per kwalifikujaca sie linia zamowienia, formula ze wspolnej
biblioteki `lib/accrual.ts`): kwota netto wchodzaca do formuly jest mnozona przez stawke.
Przy braku JAKIEJKOLWIEK konfiguracji zachowanie
musi byc IDENTYCZNE z dotychczasowym (stawka 1) — cale istniejace pokrycie testowe modulu
`loyalty` i calego repo ma pozostac zielone.

## Wymagania

Ponizsze identyfikatory sa KONTRAKTEM PUBLICZNYM — musza sie zgadzac co do znaku.

1. **Modul przechowywania: `configs` (zero wlasnych tabel).** Stawki zyja w istniejacej
   infrastrukturze modulu `configs` (`moduleId: 'loyalty'`), odczyt WYLACZNIE przez serwis
   z DI: `container.resolve('moduleConfigService')` i jego metode `getValue(...)`. ZAKAZ
   importu encji `ModuleConfig` z `@open-mercato/core` (zero cross-module ORM) i ZAKAZ
   wlasnej tabeli na stawki. Modul configs trzyma jeden wpis per `(moduleId, name, tenantId)`,
   wiec poziom organizacyjny rozroznia sie NAZWA klucza (pkt 2).

2. **Nazwany kontrakt modulu — `apps/mercato/src/modules/loyalty/lib/accrualRate.ts`.**
   Plik eksportuje:
   - `DEFAULT_ORDER_RATE = 1` — dotychczasowa globalna stawka serii (1 punkt za pelna
     jednostke waluty netto);
   - `ORDER_RATE_CONFIG_NAME = 'accruals.orderRate'` — nazwa klucza poziomu tenant
     (i wpisu globalnego instance-scope);
   - `orderRateOrgConfigName(organizationId: string): string` — zwraca DOKLADNIE
     `` `accruals.orderRate.org:${organizationId}` `` (nazwa klucza nadpisania per
     organizacja);
   - `async resolveOrderRate(container, scope: { tenantId: string; organizationId?: string | null }): Promise<number>`
     — rozwiazuje efektywna stawke wg pkt 3. `container` to kontener DI (obiekt z metoda
     `resolve(name)`).

3. **Algorytm `resolveOrderRate` (precedencja + fallback, fail-closed na wartosciach):**
   1. `moduleConfigService` z `container.resolve('moduleConfigService')`; jezeli resolve
      rzuca (serwis niezarejestrowany, np. w odchudzonym kontekscie), zwroc
      `DEFAULT_ORDER_RATE` — bez wyjatku;
   2. gdy `organizationId` podane: odczytaj
      `getValue('loyalty', orderRateOrgConfigName(organizationId), { scope: { tenantId } })`;
      wartosc POPRAWNA (pkt 4) -> zwroc ja (nadpisanie org WYGRYWA z poziomem tenant);
   3. odczytaj `getValue('loyalty', ORDER_RATE_CONFIG_NAME, { scope: { tenantId } })` —
      wbudowany fallback serwisu configs (wpis tenantowy -> wpis globalny instance) jest
      czescia kontraktu: to przez niego dziala wpis z migracji (pkt 6); wartosc POPRAWNA
      -> zwroc ja;
   4. inaczej zwroc `DEFAULT_ORDER_RATE`.
   Przekazywany `scope` MUSI zawierac `tenantId` wywolujacego; przekazanie dodatkowo
   `organizationId` w scope jest dozwolone.

4. **Poprawna wartosc stawki** = `typeof value === 'number'` i `Number.isFinite(value)`
   i `value > 0`. KAZDA inna wartosc wpisu (0, liczba ujemna, `NaN`, string — takze
   "liczbowy", obiekt, `null`) traktuj jak wpis NIEUSTAWIONY: przejdz do nastepnego
   poziomu precedencji. Zadnych wyjatkow z powodu smieciowej konfiguracji; dopuszczalny
   wylacznie log techniczny prefiksowany `[internal]`.

5. **Integracja z komenda `loyalty.accruals.accrueOrder`** (kontrakt komendy z
   wczesniejszego zadania pozostaje w mocy — zmienia sie WYLACZNIE zrodlo stawki):
   - stawke rozwiazuj przez `resolveOrderRate` (REUSE — zadnej drugiej kopii logiki
     precedencji), z `tenantId` kontekstu wywolania i `organizationId` ZAMOWIENIA
     (`order.organizationId`; przy poprawnym scopingu tozsame z org kontekstu);
   - matematyka: dotychczasowa formula serii ze wspolnej biblioteki `lib/accrual.ts`
     (kontrakt serii — `calculateOrderNetPoints`, stosowana per kwalifikujaca sie linia
     zamowienia) dostaje kwote netto PRZEMNOZONA przez stawke:
     `linePoints = calculateOrderNetPoints(Number(line.totalNetAmount) * rate)`;
     stawka NIE zmienia zasad kwalifikacji linii, wykluczen ani zadnej innej czesci
     formuly — i nie wolno powielic formuly poza biblioteka;
   - linia, ktorej `linePoints <= 0` po zastosowaniu stawki (np. ulamkowa stawka przy
     malej kwocie netto), nie zostawia wpisu; gdy ZADNA linia nie naliczy punktow ->
     `{ created: 0 }`, zero zapisow, bez bledu — tak jak dotychczasowa galaz pustych
     przypadkow;
   - CALA reszta kontraktu komendy BEZ ZMIAN: walidacja zod wejscia, scoping tenant/org,
     bledy 404 z kluczami i18n, idempotencja per zamowienie (dziala tak samo przy stawce
     z konfiguracji), ksztalt wpisow ledgera (jeden per naliczona linia, z `orderLineId`),
     uznanie salda o SUME naliczonych `linePoints`,
     wynik `{ created: number }`;
   - stawka jest rozwiazywana PRZED jakimkolwiek zapisem; nieudany odczyt konfiguracji
     nie moze zostawic polowicznego stanu.

6. **Migracja przenoszaca stawke globalna** — nowy plik w
   `apps/mercato/src/modules/loyalty/migrations/` (klasa `Migration` z
   `@mikro-orm/migrations`, wylacznie `this.addSql(...)` — bez ORM, bez knex):
   - `up()`: INSERT wpisu instance-scope do `module_configs`:
     `module_id = 'loyalty'`, `name = 'accruals.orderRate'`, `value_json = '1'`
     (literal JSON liczby 1), `tenant_id = NULL`, `organization_id = NULL`;
     INSERT IDEMPOTENTNY — `on conflict do nothing` (tabela ma czesciowy unikalny indeks
     `module_configs_global_unique` na `(module_id, name) where tenant_id is null`) albo
     rownowazny guard `where not exists`; migracja nie dotyka ZADNYCH innych wierszy;
   - `down()`: `delete from module_configs` wylacznie dla wpisu
     `module_id = 'loyalty' and name = 'accruals.orderRate' and tenant_id is null`.
   Insert surowym SQL w migracji jest tu wlasciwa sciezka (migracje operuja na schemacie
   fizycznym); zakaz z pkt 1 dotyczy kodu runtime.

7. **Ustawianie wartosci** odbywa sie istniejacymi powierzchniami modulu configs
   (`moduleConfigService.setValue('loyalty', <name>, <number>, { tenantId, organizationId })`
   — scope jest CZWARTYM argumentem `setValue` wprost, w odroznieniu od `getValue`,
   ktore bierze `{ scope }` w obiekcie opcji / API configs) — to zadanie NIE dodaje
   wlasnego UI ani API do ustawiania stawek. Dla klucza org-nadpisania
   `organizationId` w scope setValue jest metadanym wpisu; rozrozninie poziomow
   robi NAZWA klucza.

8. **Poza zakresem — NIE RUSZAC:** subscriber eventu `sales.order.completed` z
   wczesniejszej pracy serii i jego stala stawka pozostaja NIETKNIETE (to odrebna
   powierzchnia naliczania z wlasnym kontraktem i wlasnym pokryciem testowym).

9. **Testy wlasne** — unit testy w `apps/mercato/src/modules/loyalty/__tests__/`
   (styl istniejacych testow komend OM: fake `em` + fake `moduleConfigService` przez
   kontener ctx): precedencja org>tenant, fallback tenant, fallback default, odrzucenie
   smieciowych wartosci, `linePoints <= 0` po stawce, parytet zachowania przy braku
   konfiguracji.

## Kryteria ukonczenia

- `lib/accrualRate.ts` eksportuje komplet z pkt 2 i realizuje algorytm z pkt 3-4.
- Nadpisanie org ustawione -> kazda kwalifikujaca sie linia nalicza
  `floor(netto_linii * stawka_org)` niezaleznie od wartosci tenantowej; tylko poziom
  tenant ustawiony -> `floor(netto_linii * stawka_tenant)`; nic nie ustawione ->
  `floor(netto_linii * 1)`, bajt w bajt zachowanie sprzed zadania.
- Smieciowa wartosc na wyzszym poziomie precedencji nie wysadza naliczenia — schodzi
  na nizszy poziom.
- Idempotencja, scoping, bledy 404 i ksztalt wyniku komendy — bez regresji; istniejace
  testy modulu `loyalty` i cala suita repo zielone.
- Migracja z pkt 6 istnieje, jest idempotentna i przenosi stawke globalna do configs.
- `yarn typecheck` i testy modulu przechodza.

## Konwencje

- **Tenant/org-scoping**: kazdy odczyt konfiguracji niesie `tenantId` w scope; stawka
  organizacyjna rozwiazywana dla organizacji ZAMOWIENIA; zadnych danych cross-tenant.
- **Zero cross-module ORM**: modul configs wylacznie przez serwis DI
  (`moduleConfigService`), nigdy przez import jego encji; encje `sales` jak dotad —
  wylacznie przez tokeny DI.
- **i18n x5**: kazdy NOWY user-facing string przez `resolveTranslations` / `translate`
  z kluczem `loyalty.*` obecnym we wszystkich 5 locale (en/pl/de/es/ko); to zadanie nie
  wymaga nowych kluczy — komunikaty czysto techniczne prefiksuj `[internal]`.
- **Walidacja przed done**: walidacja wejscia przed zapisem (bez zmian); przed uznaniem
  zadania za skonczone `yarn typecheck` + testy modulu + pelna suita repo zielona.
