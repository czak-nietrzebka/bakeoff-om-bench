# ADJUDYKACJE PRE-REJESTROWANE (K8; rozszerzenia R11/R12)
1. Pad runnera/boxa w trakcie SESJI → run `infra-void` + task-level reset (journal attempt bez done).
2. Pad w trakcie walidacji/księgowania → powtórka kroku (idempotentne), run żyje.
3. api_error/529/rate-limit w sesji bez outputu → retry sesji; iteracja NIE liczona jako rework; `rate_limit_events`+1.
4. Konto auth_broken → bench STOI (nigdy zmiana konta); relogin=operator; runy nieruszone.
5. Golden patch konflikt → przebieg ramienia przerwany; taski od T<i> = `infra-void`; publikowane (zakaz przycinania ogona).
6. Dotyk człowieka wykryty (touch-log/auto) → run DNF; drugi raz w parze → para unieważniona; publikowane.
7. Boot-fail środowiska (compose/ephemeral timeout) → infra-void z retry ×2; trzeci fail = przebieg wstrzymany do decyzji operatora (jawnie w kwicie).
8. Pack okazuje się błędny (fail z winy TESTU, nie implementacji — orzeka amendment-log z dowodem) → run powtórzony po poprawce packa; poprawka = amendment z diffem; oba runy publikowane.
9. Trigger T5 fallback (+20 min) zamiast typecheck → odnotowane w rekordzie; run ważny.
10. Zmiana cennika w trakcie (intro→standard 2026-09-01) → imputacja po dacie wall_start; obie stawki w pricing.json; NIE jest amendmentem.
