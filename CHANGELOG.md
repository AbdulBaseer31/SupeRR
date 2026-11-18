# Changelog

## [S4-S6] - 2026-11-18
- Added logistic win probability models with odd/even cross-fitting and leverage calculation (S4).
- Added pressure flags (quantiles and rule-based cross-check), validation exhibits, and leverage distribution (S4).
- Added player-match and career aggregations, eligibility scanning, and empirical-Bayes shrinkage with dip filtering (S5).
- Added final ranking tables for batters and bowlers with full mapping metadata (S6).
- Extended run_all.py to orchestrate stages 1 through 6.

## [S2-S3] - 2026-11-18
- Added delivery flags, ordering, and match state derivation (S2).
- Added expected runs par tables, wicket costs, and per-delivery values for batting and bowling (S3).
- Updated orchestrator run_all.py for stages 1 through 3.

## [S1] - 2026-11-18
- Implemented data loaders, exclusion ledger, duplicate player mapping, and Q1-Q10 diagnostics.

## [S0] - 2026-11-18
- Initial project scaffolding, configuration parameters, and synthetic fixture generator.
