FALSE START OF THE ARM-B RERUN (2026-08-26, ~15:1x) - ZERO MEASUREMENT, not results.

Every iteration ended immediately: the dispatcher could not flip the work ticket to
`status/in-progress`, because the arm-B agent HAD NO FORGE IDENTITY OF ITS OWN (its bot
account did not exist) and fell back to a shared access token that had been revoked that
day. The effect: the session never started, the gate saw no PR, and `dnf_check` closed the
run after 5 empty cycles. $0.0 = zero tokens = zero work.

Fix: a credential store for the arm-B agent carrying its parent agent's identity - a
sub-agent vouched for by its parent instead of an administrator's shared token.

The records are kept as a trace. They count towards no statistic.
