# ZADANIE T11

## Cel

Modul lojalnosciowy (`apps/mercato/src/modules/loyalty`) urosl w poprzednich zadaniach o API,
strony backendu i komunikaty uzytkownika. Wykonaj pelny audyt i18n modulu w jego obecnym stanie
i napraw znalezione braki: (1) zadna odpowiedz API modulu loyalty nie moze zwracac surowego
klucza i18n zamiast przetlumaczonej tresci, (2) wszystkie piec locale modulu (en, pl, es, de, ko)
ma byc kompletne i zawierac prawdziwe tlumaczenia — nie kopie angielskiego tekstu. Zadanie jest
audytowo-naprawcze i obejmuje caly dotychczasowy dorobek i18n modulu, nie tylko nowe klucze.

## Wymagania

- Katalog `apps/mercato/src/modules/loyalty/i18n/` zawiera dokladnie piec plikow: `en.json`,
  `pl.json`, `es.json`, `de.json`, `ko.json`. Format plaski (dot-notation, bez zagniezdzonych
  obiektow), klucze posortowane alfabetycznie, wartosci wylacznie niepuste stringi — tak jak
  w pozostalych modulach repo.
- Parytet kluczy: kazdy locale ma identyczny zbior kluczy co `en.json` (zero brakujacych,
  zero nadmiarowych). `yarn i18n:check-sync` przechodzi.
- Kazdy klucz i18n, do ktorego odwoluje sie kod modulu loyalty — wywolania `t('loyalty.*')`
  i `translate('loyalty.*')`, wywolania na template literalu ze statycznym prefiksem
  (`` t(`loyalty.x.${...}`) ``), propy typu `labelKey`/`titleKey` — istnieje w `en.json`
  ORAZ we wszystkich czterech pozostalych locale. `yarn i18n:check-usage` przechodzi.
- Odpowiedzi API: kazdy user-facing string w odpowiedziach API modulu loyalty (pola takie jak
  `error`, `message`, `title`, `detail`) przechodzi przez `resolveTranslations()` /
  `translate(klucz, fallbackEn)` z kluczem o prefiksie `loyalty.`. Zakaz umieszczania golego
  klucza jako tresci odpowiedzi (np. `error: 'loyalty.errors.notFound'` bez `translate`) oraz
  zakaz hardcode'owanych user-facing stringow. Komunikaty czysto wewnetrzne (nie-user-facing)
  oznaczaj prefiksem `[internal]` zgodnie z konwencja repo.
- Tresc zlokalizowana naprawde: zadna wartosc w zadnym locale nie moze byc rowna wlasnemu
  kluczowi ani miec formy surowego klucza `loyalty.*`. W locale pl/es/de/ko wielowyrazowe
  wartosci nie moga byc bajt-w-bajt kopiami wartosci angielskiej. Wartosci zasadnie identyczne
  miedzy jezykami (pojedyncze slowa/akronimy/nazwy wlasne, wartosci numeryczne, wartosci
  zlozone wylacznie z placeholderow, URL-e) sa dozwolone; jesli konkretny klucz wymaga
  identycznej wartosci wielowyrazowej (np. nazwa wlasna produktu), dopisz go do repo-wide
  allowlisty `scripts/i18n-values-allowlist.json` w formacie `{"keys": ["..."]}`.
- Brakujace tlumaczenia uzupelnij recznie i sensownie jezykowo. `yarn i18n:fix`
  (`i18n-check-sync --fix`) dodaje angielskie kopie — to NIE spelnia wymagania.

## Kryteria ukonczenia

- Piec kompletnych plikow locale z pelnym parytetem kluczy i prawdziwymi tlumaczeniami
  dla calego modulu loyalty.
- Zero sciezek, ktorymi odpowiedz API loyalty moze zwrocic surowy klucz i18n; kazda
  referencja klucza w kodzie modulu rozwiazuje sie do tresci w kazdym z pieciu locale.
- Kanoniczna walidacja repo zielona:
  `yarn build:packages && yarn generate && yarn build:packages && yarn i18n:check-sync && yarn i18n:check-usage && yarn typecheck && yarn test && yarn build:app`.

## Konwencje

- Tenant/organization scoping istniejacych endpointow pozostaje nietkniety — to zadanie nie
  zmienia semantyki dostepu do danych; nie wolno przy okazji poluzowac zadnego filtra
  `tenant_id`/`organization_id`.
- Zero cross-module ORM — audyt nie wprowadza zadnych relacji miedzy modulami.
- i18n x5 (en, pl, es, de, ko) dla kazdego user-facing stringa.
- Przed zgloszeniem done przejdz pelna sekwencje walidacyjna repo (jak wyzej) i upewnij sie,
  ze `yarn test` konczy sie bez faili.
