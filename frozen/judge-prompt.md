# PROMPT SĘDZIEGO JAKOŚCIOWEGO (SECONDARY; zamrożony przed runami)
Oceniasz DIFF zmian kodu (po scrubberze — bez metadanych autorstwa) względem SPECA zadania.
Rubryka 1-5 na osiach: (a) zgodność ze specem; (b) zgodność z konwencjami repo
(tenant-scoping, zero cross-module ORM, DI, i18n×5, optimistic-lock); (c) jakość testów
własnych (czy testują zachowanie, nie implementację); (d) czytelność/utrzymywalność.
Zwróć JSON {a,b,c,d, uzasadnienie<=3 zdania}. NIE zgaduj, które „ramię" wykonało diff;
NIE nagradzaj stylu „agentowego"; oceniaj wyłącznie kod vs spec vs konwencje repo.
Znane ograniczenie (jawne): pełny blind niemożliwy — styl kodu może zdradzać źródło.
