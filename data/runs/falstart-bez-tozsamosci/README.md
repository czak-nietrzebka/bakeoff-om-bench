FALSTART POWTORKI RAMIENIA B (2026-08-26 ~15:1x) — ZERO POMIARU, nie wyniki.

Kazda iteracja konczyla sie natychmiast: whip nie mogl flipnac kwitu na
`status/in-progress`, bo czak `lee-bakeoff` NIE MIAL wlasnej tozsamosci forge
(konto bota nie istnieje) i spadal na shared-PAT, ktory tego dnia zostal
uniewazniony. Efekt: sesja nigdy nie wstala, brama widziala brak PR-a,
`dnf_check` domykal run po 5 pustych obrotach. $0.0 = zero tokenow = zero pracy.

Naprawa: store `czak-lee-bakeoff` z tozsamoscia rodzica (`czak-lee`) — subczak
firmowany przez Lee zamiast shared-PAT admina (zgodnie z czak-v2#5389).

Rekordy zachowane jako slad, NIE licza sie do zadnej statystyki.
