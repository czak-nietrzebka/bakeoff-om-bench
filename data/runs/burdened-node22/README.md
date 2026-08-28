OBCIAZONE CONFOUNDEM A5 (2026-08-26) — runy ramienia B z serii RUN-1 (kwit #5454).

Ramie B pracowalo na systemowym node 22.22, podczas gdy repo poligonu deklaruje
`engines.node: 24.x`, a ramie A dostawalo jawny PATH z node 24.19.

Dwie przyczyny, obie po stronie testbencha:
1. `launcher_b_env` nie ustawial PATH — tick whipa dziedziczyl srodowisko procesu.
   Ramie A wymuszalo jawnosc, bo `sudo` czysci env; ramie B nie, wiec nikt nie
   sprawdzil, co dziedziczy. W pilocie wygladalo zdrowo, bo `--test-command` MA
   jawny PATH: weryfikacja miala dobry node, a sama praca nie.
2. `/home/bakeoff` mial tryb 750, wiec user `czak` nie moglby wykonac binarki
   node 24 nawet gdyby mu ja wskazano — PATH wskazywalby cel, a shell cicho
   spadalby na systemowy node 22.

Zmierzone na T4-B: 15 z 80 wywolan basha (18%) to szukanie node'a, z pobraniem
node 24 do /tmp wlacznie; 29 wywolan build/test wobec 4 u baseline'u (retry).
Rozpoznanie bylo po obu stronach PODOBNE (26 vs 23) — czyli teza „persona kaze
czakowi rekonowac wiecej" jest falszywa; rozjazd robilo srodowisko.

To nierowny START, nie roznica metody — confound jednostronnie obciazajacy czaka.

Rekordy NIE sa kasowane: sa dowodem i punktem odniesienia dla MIARY confoundu
(porownanie z powtorka na wyrownanym srodowisku). Ramienia A confound NIE dotyczy —
jego runy T1-T5 zostaja wazne i nie sa powtarzane.

Fix: PR czak-v2#5470 (`launcher_b_env(node_path=...)` + meta-test symetrii: node
z komendy ramienia A == node z env ramienia B) + ACL traverse dla usera `czak`.
Decyzja o powtorce ramienia B: operator, 2026-08-26.
