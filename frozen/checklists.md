# ZAMKNIĘTA CHECKLISTA KONWENCJI PER TASK (R8 — sprawdzana KODEM: linty OM + grep bramy)
Wspólne (każdy task): [K1] encje/query z tenant+org scoping · [K2] zero importów ORM
cross-module · [K3] i18n komplet 5 locale (i18n:check-sync/usage zielone) · [K4] zero
console.* (logger-check) · [K5] typecheck zielony · [K6] zero time-bombs.
Per task dodatkowo: T1+[modules.ts wpis] · T3/T5+[idempotencja: klucz unique] ·
T4+[acl.ts feature + requireFeatures] · T6+[backfill osobną migracją] · T7+[channel-defaults
jawne] · T10+[precedencja tenant→org] · T12+[query_index rejestracja].
Naruszenie SPOZA tej listy = odnotowane, bez wpływu na werdykt (R8).
