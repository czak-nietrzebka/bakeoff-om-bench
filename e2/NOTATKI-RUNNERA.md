# Notatki runnera E2 (poza zamrozonym materialem)

- [OTWARTE] analyze.py pakietu publikacyjnego imputuje z JEDNEGO cennika (claude-sonnet-5)
  po klasach Anthropic. Rekordy p2-* (gpt-5.6-sol) MUSZA dostac przy publikacji wlasna
  sciezke wyceny (tabela per model_id, formula per-turn z pricing-e2.json) — inaczej
  przeliczylby cached_in stawka cache_read Anthropic i sklamal w obu kierunkach.
  Zrodlo: recenzja adwersaryjna 2026-08-27 (soczewka pomiar, potwierdzone).
- [OTWARTE] Rubryka P4 (audit-trail): nigdy nie napisana; jesli ma adjudykowac E2,
  musi byc zamrozona amendmentem PRZED pierwszym liczonym runem E2. Dzis NIE jest.
  Decyzja: E2 rusza bez P4 (jak E1 de facto); rubryka-kandydat do napisania osobno.
- [ZROBIONE] Pilot kalibracyjny: rekordy p2-T1-* po zakonczeniu przenosimy do
  runs/pilot-kalibracja-e2/ (nie licza sie do serii; sluza kalibracji budzetow
  i weryfikacji relacji in >= cached_in + cache_write).
- [ZMIERZONE 2026-08-27 16:4x] Konto codex (chatgpt-pro) hostuje ROWNOLEGLE zywego
  czaka mesha (dorfl, CITB#0) — jego jednorequestowe sesje ida tym samym kontem co
  bench (54 sesje w oknie pilota B3 vs 6 naszych). Ksiegowosc serii jest odporna
  (thread_id z wlasnego stdout + rollout per thread), ale PULA LIMITOW planu jest
  wspolna — dorfl moze zaglodzic serie i odwrotnie (D4/wpis-23; krok-0 przed kazdym
  taskiem lapie skutek). Pierwsza wersja rachunku voidu B3 zgarnela sesje dorfla
  globem po czasie — atrybucja WYLACZNIE po cwd sesji / thread_id.
