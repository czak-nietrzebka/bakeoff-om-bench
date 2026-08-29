# E2 symmetry table — pre-flight measurements (supplements PROTOCOL-E2 §2)

| measurement | arm A | arm B | date |
|---|---|---|---|
| AGENTS.md loaded by the engine | YES — "YES (Agents Guidelines)", 11149 input tokens | YES — from the git worktree, "YES (Agents Guidelines)", 11134 tokens | 2026-08-27 15:34 |
| base | bakeoff/p2 @ 15ffbe30c (fresh clone) | bakeoff/p2 @ 15ffbe30c (fresh clone) | 2026-08-27 |
| deps | pristine (8x node_modules, one shared set) | identical pristine | 2026-08-27 |
| engine PATH | node24-first, sanitised | identical | frozen |
| session timeout | 3600 s | 3600 s (override; the 1800 default was rejected) | frozen |
| network in the sandbox | network_access=true | network_access=true | frozen |
| forge token in the environment | NO (not needed) | YES (parity with E1-B, measured in the E1 transcript) | frozen |
| spec channel | prompt (preamble + spec) | the dispatcher's prompt with the work ticket's body appended (D9) | frozen |
| self-review | n/a (method A has no such step) | challenger engine, E1 guidance, cost charged to B (D11) | frozen |

Conclusion A8: the "instruction asymmetry" class from E1 does NOT occur in E2 — both arms
receive an identical AGENTS.md through the same engine mechanism (measured, not assumed).
