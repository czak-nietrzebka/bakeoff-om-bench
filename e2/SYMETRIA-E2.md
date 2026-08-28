# Tabela symetrii E2 — pomiary pre-flight (uzupelnia PROTOCOL-E2 §2)

| pomiar | ramie A | ramie B | data |
|---|---|---|---|
| AGENTS.md ladowany przez silnik | TAK — "YES (Agents Guidelines)", 11149 tok. wejscia | TAK — z git-worktree, "YES (Agents Guidelines)", 11134 tok. | 2026-08-27 15:34 |
| baza | bakeoff/p2 @ 15ffbe30c (swiezy klon) | bakeoff/p2 @ 15ffbe30c (swiezy klon) | 2026-08-27 |
| deps | pristine (8x node_modules, wspolny komplet) | identyczny pristine | 2026-08-27 |
| PATH silnika | node24-first, sanityzowany (env_silnika) | identyczny | frozen |
| timeout sesji | 3600 s | 3600 s (override; default 1800 odrzucony) | frozen |
| siec w sandboxie | network_access=true | network_access=true | frozen |
| token forge w env | NIE (nie potrzebuje) | TAK (parytet z E1-B, zmierzone w transkrypcie E1) | frozen |
| kanal specu | prompt (PREAMBULA+spec) | prompt whipa + doklejone body kwitu (D9) | frozen |
| self-review | n/d (metoda A nie ma tego kroku) | codex, guidance E1, koszt liczony do B (D11) | frozen |

Wniosek A8: klasa "asymetria instrukcji" z E1 NIE wystepuje w E2 — oba ramiona
dostaja identyczne AGENTS.md tym samym mechanizmem silnika (zmierzone, nie zalozone).
