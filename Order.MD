# Order.MD: Build order, sections, commits

Today is Wed 18 Nov 2026. Deadline 23:59 IST. Target submit time: 22:30 IST. The AI builds code in sections S0 to S10. You push after each section. You write the report yourself while the later sections run.

## Time budget (IST)

| Block | Sections | Clock target |
| --- | --- | --- |
| Build, part 1 | S0 to S3 | 12:30 to 15:15 |
| Build, part 2 | S4 to S7 | 15:15 to 17:45 |
| Build, part 3 | S8 to S10 | 17:45 to 19:15 |
| Squad-fit research and report writing | (you) | start 17:00 in parallel, finish by 22:00 |
| Submit | | by 22:30, buffer until 23:59 |

If you fall behind, cut in this order: S8 sensitivity (keep only Q=0.67, 0.75, 0.80), then S9 charts 3 and 4 (draw by hand from tables), then rule-based cross-check in S8. Never cut: S1 (ledger and diagnostics), S5 (shrinkage), S7 (bootstrap), S4 validation exhibit.

## Repo layout (created in S0)

```
repo/
  .gitignore            (data/, out/, *.csv, .venv/, __pycache__/)
  README.md
  CHANGELOG.md
  requirements.txt
  Spec.MD  Rules.MD  Order.MD  Agents.MD  Prompt.MD
  audit.txt             (schema only; safe to commit)
  data/                 (the six CSVs; never committed)
  out/                  (outputs; never committed)
  pressure/
    __init__.py  config.py  io_load.py  ledger.py  prep.py
    tables.py  winprob.py  leverage.py  values.py
    aggregate.py  shrink.py  bootstrap.py  sensitivity.py  report_tables.py
  tests/
    make_fixture.py  test_*.py
  run_all.py
```

The rule for committing: commit and push only after the section's acceptance tests pass. One section equals one commit. Do not push `out/` or `data/` ever.

---

## S0: Scaffold, config, synthetic fixture

- **Spec:** sections 1, 2, 13, 14.
- **Files:** everything in the layout above that is a stub, plus `config.py`, `tests/make_fixture.py`, `.gitignore`, `requirements.txt`, `README.md`, `CHANGELOG.md`.
- **Goal:** an empty-but-runnable project. `config.py` holds every parameter from Spec section 14. `make_fixture.py` writes six fake CSVs into `tests/fixture_data/` with exactly the schema in Spec section 2: about 60 matches, innings 1 and 2 plus a few super-over innings 3, some wides and no-balls, wickets of several types, a few rain-revised matches, two competition groups (one name containing "Indian Premier League"), 12 players per team, and a couple of duplicate names under different ids.
- **Done when:** `python tests/make_fixture.py` creates the six files; `.gitignore` contains `data/`, `out/`, `*.csv` (with `tests/fixture_data` allowed via a negation rule or a `.gitkeep` plus generating on demand); `python -c "import pressure.config"` works.
- **Commit:** `S0: scaffold, config, synthetic fixture generator`
- **Time box:** 20 min.

## S1: Load, diagnostics (Q1 to Q10), ledger

- **Spec:** sections 3, 4, 5.
- **Files:** `io_load.py`, `ledger.py`, `run_all.py` (stage 1 only), `tests/test_ledger.py`.
- **Goal:** load all six CSVs; print and save to `out/diagnostics.txt` the answers to Q1 to Q10 as aggregates; build and save `out/ledger.csv`; save `out/duplicate_names.csv`.
- **Done when:** ledger reconciles on the fixture; diagnostics file exists; no data rows printed.
- **Then you do:** run on the real data and send me the aggregate lines of `out/diagnostics.txt` (no rows). If any Q-answer contradicts a Spec default, tell the AI the approved change before S2.
- **Commit:** `S1: loaders, diagnostics, exclusion ledger`
- **Time box:** 40 min.

## S2: Cricket flags and match state

- **Spec:** sections 5, 6.
- **Files:** `prep.py`, `tests/test_prep.py`.
- **Goal:** add `is_wide, is_nb, legal, bat_runs, extras, total, charged, team_wicket, bowler_credit, dismissed_id`; sort; compute `legal_before, wkts_before, score_before, inn_total, remaining, balls_left, ov, wb, phase, target, rn, grp`.
- **Done when:** acceptance tests 2 and 3 pass on the fixture; on the real data, the aggregate checks (max `legal_before`, max `wkts_before`, count of clipped rows) print without raising.
- **Commit:** `S2: delivery flags and match state`
- **Time box:** 40 min.

## S3: Par tables, wicket cost, value per ball

- **Spec:** section 8.
- **Files:** `tables.py`, `values.py`, `tests/test_values.py`.
- **Goal:** build `wcost`, the four smoothed par tables from innings 1, and `v_bat`, `v_bowl` per delivery, plus the non-striker run-out events.
- **Done when:** acceptance test 6 (league mean about 0) passes on the fixture and on the real data (printed as an aggregate).
- **Commit:** `S3: par tables, wicket cost, value per ball`
- **Time box:** 45 min.

## S4: Win probability, leverage, pressure flag, validation exhibit

- **Spec:** section 7.
- **Files:** `winprob.py`, `leverage.py`, `tests/test_leverage.py`.
- **Goal:** the two logistic models with odd/even cross-fitting; outcome probabilities; leverage per delivery; flags for `Q` in `{0.67, 0.75, 0.80}` and the rule-based flag; `out/validation_pressure_vs_ordinary.csv`; `out/leverage_distribution.csv`.
- **Done when:** acceptance tests 4 and 5 pass on the fixture.
- **CHECKPOINT (you, with the real data):** open `validation_pressure_vs_ordinary.csv` and `leverage_distribution.csv`. Confirm pressure and ordinary balls differ within each phase (dot %, boundary %, wicket %). Lock the pressure cut Q (default 0.75) and tell the AI. This is the "review the leverage distribution and lock the cut" step. Do not continue past S4 until you have done it.
- **Commit:** `S4: win probability, leverage, pressure flag, validation exhibit`
- **Time box:** 60 min.

## S5: Aggregation, shrinkage, dip filter, eligibility scan

- **Spec:** section 9 (9.1 to 9.4).
- **Files:** `aggregate.py`, `shrink.py`, `tests/test_shrink.py`.
- **Goal:** player and player-match tables; pooled variance; `mu, tau2, k`; shrunk `P*`; `z` and `dip`; `out/eligibility_scan.csv`; `out/shrinkage_params.csv`.
- **Done when:** acceptance test 7 passes; the `k` warning logic is tested with a synthetic extreme case.
- **Then you do:** read `eligibility_scan.csv` and set `MIN_BALLS` and `MIN_MATCHES` in `config.py` yourself.
- **Commit:** `S5: aggregation, empirical-Bayes shrinkage, dip filter`
- **Time box:** 40 min.

## S6: Final ranking tables

- **Spec:** section 9.5, section 12 (ranked files).
- **Files:** `aggregate.py` (extend), `report_tables.py` (ranked tables only), `tests/test_rank.py`.
- **Goal:** `out/batters_ranked.csv` and `out/bowlers_ranked.csv` with every column in Spec section 12 that does not depend on the bootstrap yet; names and `main_team` from the mapping file; overall raw rank.
- **Done when:** acceptance test 9 passes (all ranked ids exist in the mapping file).
- **Commit:** `S6: ranked batter and bowler tables`
- **Time box:** 30 min.

## S7: Match-level bootstrap

- **Spec:** section 10.
- **Files:** `bootstrap.py`, `tests/test_bootstrap.py`.
- **Goal:** the vectorised bootstrap; add `top10_prob, rank_p10, rank_median, rank_p90` to the ranked tables.
- **Done when:** acceptance test 8 (identical output on two runs with the same seed) passes; B = 1000 finishes in under 60 seconds on the fixture.
- **Commit:** `S7: match-level bootstrap and rank intervals`
- **Time box:** 30 min.

## S8: Sensitivity grid and split-half

- **Spec:** section 11.
- **Files:** `sensitivity.py`, `tests/test_sensitivity.py`.
- **Goal:** the variants in section 11.1, `robust_count` added to the ranked tables, `out/sensitivity_*.csv`; split-half Spearman in `out/split_half.csv`.
- **Done when:** the fixture run produces all files; `robust_count` is between 0 and the number of variants.
- **Commit:** `S8: sensitivity variants and split-half reliability`
- **Time box:** 40 min.

## S9: Charts

- **Spec:** section 12a.
- **Files:** `report_tables.py` (extend, charts only), `tests/test_charts.py`.
- **Goal:** the four charts as PNGs in `out/charts/`. Plain, labelled, readable on a slide.
- **Done when:** four PNGs exist and open; no data rows or player ids on chart titles other than finalist names on charts 3 and 4.
- **Commit:** `S9: report charts`
- **Time box:** 30 min.

## S10: Freeze

- **Spec:** sections 1, 13, 14.
- **Files:** `run_all.py`, `README.md`, `CHANGELOG.md`, `requirements.txt` (pinned versions).
- **Goal:** one command runs every stage; prints input-file SHA-256 hashes at the top of `run_log.txt`; README states the run order, seed, and that `data/` is not included. Run time under 5 minutes on the real data.
- **Done when:** a clean run from a fresh virtual environment reproduces identical `batters_ranked.csv` and `bowlers_ranked.csv` twice.
- **Commit:** `S10: single-command run, hashes, README`
- **Time box:** 20 min.

---

## What you do outside the AI sections

1. After S1: send me the Q-answers (aggregates only) so we can confirm or change the Spec defaults.
2. At the S4 checkpoint: lock the pressure cut.
3. After S5: set the eligibility floors.
4. After S8: check each finalist's name against the Unstop dropdown and resolve any shared-name ids from `duplicate_names.csv`.
5. Squad-fit research (public data) for each of the 20 finalists, and the report, written yourself.
