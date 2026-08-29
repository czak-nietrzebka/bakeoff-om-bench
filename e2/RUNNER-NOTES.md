# E2 runner notes (outside the frozen material)

These are the runner's working notes for Experiment 2. They are not part of the frozen
pre-registration and adjudicate nothing; they are published so the operational decisions
behind the E2 series are readable. Each item states where it now stands.

- **[RESOLVED] Cost imputation must not use a single price list.** The publication
  package's `analyze.py` imputes from one price list (`claude-sonnet-5`) by Anthropic's
  usage classes. The `p2-*` records come from a different vendor and needed their own
  pricing path, or cached input would have been priced at Anthropic's cache-read rate and
  the total would have been wrong in both directions. Source: adversarial review
  2026-08-27 (measurement lens, confirmed). Resolved: `analyze_e2.py` prices **per
  request** from `e2/pricing-e2.json`, including the long-context surcharge.

- **[RESOLVED, negatively] The P4 audit-trail rubric was never written.** If it were to
  adjudicate E2 it would have to be frozen by amendment BEFORE the first counted E2 run.
  It was not. Decision at the time: E2 starts without P4, as E1 in fact did. This is not
  hidden anywhere: `README.md`, `REPORT.md` §2 and `e2/PROTOCOL-E2.md` all state that P4
  was unfalsifiable as pre-registered. Writing such a rubric is a separate piece of work.

- **[DONE] Calibration pilot records are held apart.** After the pilot, the `p2-T1-*`
  records were moved to `runs/pilot-kalibracja-e2/`. They do not count towards the series;
  they exist to calibrate budgets and to check the relation `in >= cached_in + cache_write`.

- **[MEASURED 2026-08-27] The challenger's vendor account was shared with unrelated
  production work.** The account running arm B also served an unrelated production agent of
  the operator's, whose single-request sessions went through the same account as the bench
  (54 sessions inside the B3 pilot window against 6 of ours). The series' accounting is
  robust to this — attribution is by the session's own thread id and per-thread rollout —
  but the plan's **rate-limit pool is shared**, so either workload can starve the other and
  a rate-limit event in this series may have an external cause. The first draft of the B3
  void accounting swept the unrelated sessions in by a time-glob; attribution is by the
  session's working directory and thread id ONLY. See the note on the attempt-3 record in
  `data-e2/runs/pilot-kalibracja-e2/p2-T1-B.jsonl`.
