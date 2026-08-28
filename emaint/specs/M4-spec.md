# ZADANIE M4

## Cel

Przygotuj raport audytowy modulu `loyalty` (`apps/mercato/src/modules/loyalty/`)
w pliku **`AUDIT.md` w korzeniu repo**. Raport odpowiada na 11 pytan o FAKTY dotyczace
modulu w jego OBECNYM stanie — kazda odpowiedz musi byc weryfikowalna w plikach repo
i podparta dowodem (sciezka pliku). Zadanie NIE zmienia zadnego kodu: jedynym
artefaktem jest `AUDIT.md`. Werdykt orzeka automat porownujacy tresc raportu ze
stanem repo — licza sie trafione fakty i prawdziwe dowody, nie forma literacka.

## Wymagania

Ponizsza struktura pliku jest KONTRAKTEM PUBLICZNYM — musi sie zgadzac co do znaku.

1. **Struktura `AUDIT.md`:**
   - naglowek `# AUDYT MODULU LOYALTY`;
   - 11 sekcji o naglowkach DOKLADNIE `## A1` ... `## A11` (po numerze wolno dodac
     tytul, np. `## A3 Pochodzenie order_line_id`);
   - kazda sekcja: ZWIEZLA odpowiedz — **max ~1200 znakow na sekcje**; sekcja
     rozstrzelona ponad limit zostaje zdyskwalifikowana w scoringu;
   - kazda sekcja konczy sie co najmniej jedna linia
     `DOWOD: <sciezka-wzgledna-pliku-w-repo>` (wolno podac kilka sciezek po
     przecinku). Obowiazuja DWA warunki naraz: **sekcja musi wskazac co
     najmniej JEDNA ISTNIEJACA sciezke** oraz **KAZDA podana sciezka musi
     istniec w repo** — jedna zmyslona sciezka uniewaznia CALA sekcje (zero
     punktow za jej fakty), takze wtedy, gdy obok stoi sciezka prawdziwa.
     Sciezki wylacznie wzgledne od korzenia repo, bez `..`; sciezka
     wyprowadzajaca poza korzen repo liczy sie tak samo jak zmyslona;
   - `DOWOD: BRAK` jest dopuszczalny **wylacznie w sekcji A9 i tylko wtedy, gdy
     wszystkie szesc pod-odpowiedzi brzmi `BRAK`** — czyli gdy naprawde nie ma
     na co wskazac. W kazdym innym miejscu `DOWOD: BRAK` uniewaznia sekcje:
     odpowiedz bez dowodu nie jest odpowiedzia. We wszystkich pozostalych
     sekcjach odpowiedz ma swoje pliki — trzeba je znalezc, nie uchylic sie;
   - w sekcji A9 szesc pod-odpowiedzi w OSOBNYCH liniach zaczynajacych sie
     DOKLADNIE od `A9a:`, `A9b:`, `A9c:`, `A9d:`, `A9e:`, `A9f:`; kazda
     pod-odpowiedz to **albo** `TAK` + sciezka pliku, **albo** samo slowo
     `BRAK` — nigdy jedno i drugie w tej samej linii. Linia mowiaca
     naraz `TAK <sciezki>` i `BRAK` jest sprzeczna i nie zalicza NICZEGO:
     ani odpowiedzi twierdzacej, ani przeczacej. Odpowiadasz na szesc
     osobnych pytan, nie wypisujesz wszystkiego przy kazdym z nich.

2. **Pytania** (odpowiadasz o STANIE TEGO repo, nie o tym, jak byc powinno):

   - **A1 — powierzchnia salda.** Wymien wszystkie pliki modulu loyalty, ktore
     MUTUJA saldo (`balance`) konta lojalnosciowego (zapisuja zmiane, nie tylko
     czytaja), kazdy z nazwa komendy/handlera, ktory to robi.
   - **A2 — wykluczenia naliczania.** W komendzie naliczania punktow za
     zamowienie: ktore linie zamowienia sa wykluczone z naliczania (rodzaj linii
     + warunek liczbowy) i co sie dzieje z zamowieniem zlozonym przez goscia
     (bez klienta)?
   - **A3 — pochodzenie `order_line_id`.** Ktory plik migracji wprowadza kolumne
     `order_line_id` w `loyalty_ledger_entries`; co ta sama migracja robi z
     wczesniejszym wymuszeniem unikalnosci na (`tenant_id`, `order_id`) —
     podaj JEGO NAZWE oraz NAZWE indeksu, ktory wchodzi na jego miejsce;
     dlaczego kolumna jest nullable?
   - **A4 — pochodzenie `expires_at`.** Ktory plik migracji dodaje kolumne
     `expires_at` do ledgera, a ktory plik migracji WYKONUJE backfill tej
     kolumny (dwie rozne nazwy); ile wynosi okres waznosci punktow i od czego
     jest liczony; jak backfill traktuje wpisy o `points <= 0`?
   - **A5 — punkty idempotencji.** Wymien wszystkie NIEZALEZNE mechanizmy
     idempotencji zapisow w module; dla kazdego: sciezka wykonania → klucz →
     mechanizm (sprawdzenie-przed-zapisem / ograniczenie bazodanowe / inne).
     Dla sciezki zdarzeniowej (obsluga zdarzenia o zakonczonym zamowieniu) podaj
     NAZWE ograniczenia albo indeksu unikalnosci, na ktorym stoi jej klucz.
     Uwzglednij takze idempotencje na poziomie migracji.
   - **A6 — ACL.** Dla kazdego feature ACL modulu: ktore endpointy/metody HTTP
     go wymagaja i jakie zaleznosci (`dependsOn`) deklaruje.
   - **A7 — dwie matematyki naliczen.** Modul ma wiecej niz jedna sciezke
     naliczania punktow za zamowienia. Wskaz plik ze wspolna matematyka oraz
     formule kazdej sciezki (rodzaj zaokraglenia + stawka).
   - **A8 — konfigurowalna stawka.** Skad komenda naliczania bierze stawke:
     nazwy kluczy konfiguracji (poziom organizacji i poziom tenanta), wartosc
     domyslna i kolejnosc rozstrzygania; ktora migracja zasiewa wartosc
     domyslna w konfiguracji (nazwa pliku); co sie dzieje ze smieciowa
     wartoscia wpisu konfiguracji?
   - **A9 — powierzchnie integracyjne.** Czy modul loyalty MA w repo:
     (a) widget wstrzykiwany na karte klienta, (b) konfiguracje globalnego
     wyszukiwania, (c) deklaracje pola niestandardowego na koncie,
     (d) jawna deklaracje powiazania klient-konto, (e) wlasny serwis
     rejestrowany w kontenerze zaleznosci modulu, (f) endpoint API zwracajacy
     podsumowanie lojalnosciowe klienta? Odpowiedz w formacie `A9a:`-`A9f:`
     opisanym w pkt 1.
   - **A10 — awans tieru.** Czym modul rozstrzyga, ze konto awansowalo do
     wyzszego tieru; jaki event wtedy emituje; ktore kanaly dorczenia deklaruje
     typ notyfikacji, a ktory kanal swiadomie pominieto?
   - **A11 — guard salda.** Gdzie zyje wspolna implementacja reguly "saldo nigdy
     ujemne", jak nazywa sie jej funkcja, czym sygnalizuje naruszenie (nazwa
     klasy albo funkcji bledu) i ktore operacje z niej korzystaja?

3. **Identyfikatory podawaj DOKLADNIE tak, jak w repo** — nazwy plikow, kolumn,
   ograniczen i indeksow bazodanowych, kluczy konfiguracji, funkcji, feature ACL
   i eventow musza sie zgadzac co do znaku (to po nich orzeka automat).

## Kryteria ukonczenia

- `AUDIT.md` istnieje w korzeniu repo i jest zgodny ze struktura z pkt 1
  (naglowek, KOMPLET sekcji A1-A11, linie `DOWOD:`, format `A9a:`-`A9f:`).
  Werdykt zielony wymaga wszystkich JEDENASTU sekcji — pominiete pytanie jest
  pytaniem bez odpowiedzi, nie oszczednoscia.
- Odpowiedzi zgodne z realnym stanem repo; kazda sekcja wskazuje co najmniej
  jeden istniejacy plik, a kazda sciezka podana jako dowod istnieje.
- Werdykt sprawdza takze, czy raport zawiera fakty, ktorych nie da sie podac
  bez otwarcia plikow TEGO repo — audyt ma opisywac ten modul, nie modul
  "taki mniej wiecej".
- Zadnych zmian w kodzie, testach, migracjach ani konfiguracji — audyt czyta,
  nie pisze; `AUDIT.md` to jedyny nowy plik.

## Konwencje

- **Fakty, nie zyczenia:** odpowiadaj o stanie TEGO repo — takze wtedy, gdy fakt
  jest niewygodny. Brak artefaktu to tez fakt: w pod-odpowiedziach A9 pisz
  `BRAK`, nie zmyslaj sciezek.
- **Nie umiem tego ustalic to trzecia odpowiedz** — i wolno ja napisac wprost.
  Kosztuje tyle, ile warta jest ta sekcja, i ani grosza wiecej. Zdanie
  asekuracyjne, ktore mowi jednoczesnie "jest" i "nie ma", nie jest trzecia
  odpowiedzia, tylko dwiema sprzecznymi — i nie liczy sie za zadna z nich.
- **Sciezki wylacznie wzgledne** od korzenia repo.
- **Zwiezlosc jest wymaganiem:** limit dlugosci sekcji jest egzekwowany
  automatycznie; wklejanie duzych fragmentow kodu dyskwalifikuje sekcje.
- **Zero zmian w kodzie:** ten audyt niczego nie naprawia; znalezione
  watpliwosci opisujesz w odpowiedziach, nie commitujesz poprawek.
