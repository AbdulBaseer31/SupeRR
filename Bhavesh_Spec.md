# Bhavesh_Spec.md: Parallel Work Package for Bhavesh

## Overview & Architecture Context
The core pipeline in `Order.MD` follows a linear dependency for data transformation:
```
S1 (Load/Ledger) -> S2 (Match State) -> S3 (Par Tables/Value) -> S4 (WinProb/Leverage) -> S5 (Shrinkage) -> S6 (Ranking)
```

However, statistical modules, chart rendering engines, and validation suites can be developed **in parallel on independent files** with zero merge conflicts, provided the input/output interfaces defined below are honored.

---

## 1. Work Packages Bhavesh Can Own (Zero-Conflict Parallel Modules)

### Package A: S7 — Match-Level Bootstrap (`pressure/bootstrap.py`)
- **Files Owned**: `pressure/bootstrap.py`, `tests/test_bootstrap.py`
- **Spec Section**: Section 10
- **Why Parallel**: The bootstrap logic does not depend on delivery-level details; it operates on a pre-aggregated DataFrame with schema:
  `[match_id, player_id, role, p_balls, p_val, u_balls, u_val]`
- **Interface Contract**:
  ```python
  def run_match_bootstrap(
      df_player_match: pd.DataFrame,
      n_rounds: int = 1000,
      seed: int = 42
  ) -> pd.DataFrame:
      """
      Resamples unique match_ids with replacement B=1000 times.
      Re-calculates shrunk P* per resample.
      Returns DataFrame per player_id with:
      ['player_id', 'top10_prob', 'rank_p10', 'rank_median', 'rank_p90']
      """
  ```
- **Acceptance Criterion**: Vectorized execution finishes $B=1000$ in $< 60$ seconds on fixture; identical output with fixed seed.

---

### Package B: S8 — Split-Half Reliability & Sensitivity Grid (`pressure/sensitivity.py`)
- **Files Owned**: `pressure/sensitivity.py`, `tests/test_sensitivity.py`
- **Spec Section**: Section 11
- **Why Parallel**: Pure standalone statistical utility. Takes aggregated player-match data and computes:
  1. **Split-Half Reliability**: Splits match IDs into alternating halves (or odd/even seasons) and computes the Spearman rank correlation of $P^*$ across eligible players. Writes `out/split_half.csv`.
  2. **Sensitivity Grid**: Evaluates robustness under varied pressure cutoffs ($Q \in \{0.67, 0.75, 0.80\}$), loosened/tightened ball floors, and IPL-only vs. All-T20. Computes `robust_count` (how many variants each player stays in top 10). Writes `out/sensitivity_*.csv`.
- **Interface Contract**:
  ```python
  def compute_split_half(df_player_match: pd.DataFrame) -> pd.DataFrame:
      ...

  def run_sensitivity_grid(
      df_deliveries_with_leverage: pd.DataFrame,
      variants_config: dict
  ) -> pd.DataFrame:
      ...
  ```

---

### Package C: S9 — Report Charts & Visualizations (`pressure/charts.py`)
- **Files Owned**: `pressure/charts.py` (isolated from `report_tables.py`), `tests/test_charts.py`
- **Spec Section**: Section 12a
- **Output Target**: 4 PNGs saved to `out/charts/`:
  1. **Chart 1**: Leverage distribution & pressure threshold cutoff ($Q$).
  2. **Chart 2**: Validation exhibit — Pressure vs. Ordinary delivery distributions (Dot %, Boundary %, Wicket % across Powerplay, Middle, Death phases).
  3. **Chart 3**: Batter Finalists — Shrunk $P^*$ point estimates and $[P_{10}, P_{90}]$ bootstrap rank intervals.
  4. **Chart 4**: Bowler Finalists — Shrunk $P^*$ point estimates and $[P_{10}, P_{90}]$ bootstrap rank intervals.
- **Why Parallel**: Bhavesh can write the visualization functions using mock/fixture dataframes. When S6/S7 complete, the orchestrator simply feeds the real tables into Bhavesh's chart functions.
- **Constraints**: Clean, readable on slides, styled with matplotlib, no magic numbers.

---

## 2. File Ownership Rules to Prevent Merge Conflicts

| Developer | Files Owned Exclusively | Responsibilities |
| :--- | :--- | :--- |
| **Main Pipeline (AI / You)** | `pressure/io_load.py`<br>`pressure/ledger.py`<br>`pressure/prep.py`<br>`pressure/tables.py`<br>`pressure/winprob.py`<br>`pressure/leverage.py`<br>`pressure/values.py`<br>`pressure/aggregate.py`<br>`pressure/shrink.py`<br>`pressure/report_tables.py`<br>`run_all.py` | Core delivery state calculation, par lookups, leverage, shrinkage, and final ranking tables. |
| **Bhavesh** | `pressure/bootstrap.py`<br>`pressure/sensitivity.py`<br>`pressure/charts.py`<br>`tests/test_bootstrap.py`<br>`tests/test_sensitivity.py`<br>`tests/test_charts.py` | Standalone analytical & presentation layers (Bootstrap intervals, sensitivity grid, and chart generation). |

---

## 3. How to Merge Bhavesh's Work
1. Bhavesh works on a feature branch (e.g., `git checkout -b bhavesh-modules`).
2. Because his files (`bootstrap.py`, `sensitivity.py`, `charts.py`) do not overlap with the main data pipeline files, his branch will merge into `main` cleanly with `git merge bhavesh-modules` with **0 merge conflicts**.
3. Once merged, `run_all.py` imports Bhavesh's functions in Stages 7, 8, and 9:
   ```python
   from pressure.bootstrap import run_match_bootstrap
   from pressure.sensitivity import compute_split_half, run_sensitivity_grid
   from pressure.charts import generate_all_charts
   ```
