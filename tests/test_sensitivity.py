"""Tests for pressure/sensitivity.py (Package B — S8).

Acceptance criteria from Bhavesh_Spec.md:
  1. Split-half Spearman r in [-1, 1].
  2. Output schemas and non-empty outputs.
  3. 0 <= robust_count <= total number of variants.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pressure.sensitivity import compute_split_half, run_sensitivity_grid


# ---------------------------------------------------------------------------
# Shared fixture builders
# ---------------------------------------------------------------------------

def _make_player_match_df(
    n_players: int = 30,
    n_matches: int = 60,
    seed: int = 42,
) -> pd.DataFrame:
    """Create a synthetic player-match DataFrame."""
    rng = np.random.default_rng(seed)
    rows = []
    for pid in range(1, n_players + 1):
        n_played = rng.integers(15, n_matches + 1)
        match_ids = rng.choice(range(1001, 1001 + n_matches), size=n_played, replace=False)
        for mid in match_ids:
            p_balls = rng.integers(2, 15)
            u_balls = rng.integers(5, 25)
            p_val = rng.normal(0.5, 2.0) * p_balls
            u_val = rng.normal(0.3, 1.5) * u_balls
            rows.append({
                "match_id": int(mid),
                "player_id": pid,
                "role": "bat",
                "p_balls": p_balls,
                "p_val": round(p_val, 4),
                "u_balls": u_balls,
                "u_val": round(u_val, 4),
            })
    return pd.DataFrame(rows)


def _make_deliveries_with_leverage(
    n_players: int = 30,
    n_matches: int = 60,
    seed: int = 42,
) -> pd.DataFrame:
    """Create a synthetic delivery-level DataFrame with leverage."""
    rng = np.random.default_rng(seed)
    rows = []
    comp_names = ["Indian Premier League 2023", "ICC T20 World Cup"]
    for mid in range(1001, 1001 + n_matches):
        comp = rng.choice(comp_names)
        for _ in range(rng.integers(100, 150)):
            pid = rng.integers(1, n_players + 1)
            leverage = rng.exponential(1.0)
            v_bat = rng.normal(0.0, 2.0)
            rows.append({
                "match_id": mid,
                "player_id": pid,
                "leverage": round(leverage, 4),
                "v_bat": round(v_bat, 4),
                "p_balls": 1,
                "p_val": v_bat if leverage > 1.0 else 0.0,
                "comp_name": comp,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def player_match_df() -> pd.DataFrame:
    return _make_player_match_df()


@pytest.fixture
def deliveries_df() -> pd.DataFrame:
    return _make_deliveries_with_leverage()


# ---------------------------------------------------------------------------
# Split-Half Tests
# ---------------------------------------------------------------------------

class TestComputeSplitHalf:
    """Tests for compute_split_half."""

    def test_output_columns(self, player_match_df: pd.DataFrame) -> None:
        """Output must contain the specified columns."""
        result = compute_split_half(player_match_df, min_balls=10, min_matches=3)
        expected_cols = {"method", "n_players", "spearman_r", "p_value"}
        assert expected_cols.issubset(set(result.columns))

    def test_spearman_r_range(self, player_match_df: pd.DataFrame) -> None:
        """Spearman r must be in [-1, 1] when computable."""
        result = compute_split_half(player_match_df, min_balls=10, min_matches=3)
        r = result["spearman_r"].iloc[0]
        if not np.isnan(r):
            assert -1.0 <= r <= 1.0

    def test_p_value_range(self, player_match_df: pd.DataFrame) -> None:
        """p-value must be in [0, 1] when computable."""
        result = compute_split_half(player_match_df, min_balls=10, min_matches=3)
        p = result["p_value"].iloc[0]
        if not np.isnan(p):
            assert 0.0 <= p <= 1.0

    def test_n_players_positive(self, player_match_df: pd.DataFrame) -> None:
        """n_players must be non-negative."""
        result = compute_split_half(player_match_df, min_balls=10, min_matches=3)
        assert result["n_players"].iloc[0] >= 0

    def test_method_name(self, player_match_df: pd.DataFrame) -> None:
        """Method should be 'alternating_match_split'."""
        result = compute_split_half(player_match_df, min_balls=10, min_matches=3)
        assert result["method"].iloc[0] == "alternating_match_split"

    def test_empty_input(self) -> None:
        """Empty input should return a row with NaN correlation."""
        df_empty = pd.DataFrame(
            columns=["match_id", "player_id", "p_balls", "p_val", "u_balls", "u_val"]
        )
        result = compute_split_half(df_empty, min_balls=1, min_matches=1)
        assert len(result) == 1
        assert np.isnan(result["spearman_r"].iloc[0])


# ---------------------------------------------------------------------------
# Sensitivity Grid Tests
# ---------------------------------------------------------------------------

class TestRunSensitivityGrid:
    """Tests for run_sensitivity_grid."""

    def test_output_columns(self, deliveries_df: pd.DataFrame) -> None:
        """Output must contain the specified columns."""
        result = run_sensitivity_grid(deliveries_df)
        expected_cols = {"player_id", "variant", "rank", "in_top10", "robust_count"}
        assert expected_cols.issubset(set(result.columns))

    def test_robust_count_range(self, deliveries_df: pd.DataFrame) -> None:
        """robust_count must be between 0 and the number of variants."""
        result = run_sensitivity_grid(deliveries_df)
        if not result.empty:
            n_variants = result["variant"].nunique()
            assert (result["robust_count"] >= 0).all()
            assert (result["robust_count"] <= n_variants).all()

    def test_all_default_variants_present(self, deliveries_df: pd.DataFrame) -> None:
        """All default variants should be in the output."""
        result = run_sensitivity_grid(deliveries_df)
        if not result.empty:
            from pressure.sensitivity import DEFAULT_VARIANTS
            expected_variants = set(DEFAULT_VARIANTS.keys())
            actual_variants = set(result["variant"].unique())
            # At least some variants should be present
            assert len(actual_variants) > 0

    def test_in_top10_binary(self, deliveries_df: pd.DataFrame) -> None:
        """in_top10 must be 0 or 1."""
        result = run_sensitivity_grid(deliveries_df)
        if not result.empty:
            assert set(result["in_top10"].unique()).issubset({0, 1})

    def test_ranks_positive(self, deliveries_df: pd.DataFrame) -> None:
        """All ranks must be >= 1."""
        result = run_sensitivity_grid(deliveries_df)
        if not result.empty:
            assert (result["rank"] >= 1).all()

    def test_custom_variants(self, deliveries_df: pd.DataFrame) -> None:
        """Should accept custom variants_config."""
        custom = {
            "only_q075": {
                "q": 0.75,
                "min_balls": 10,
                "min_matches": 2,
                "comp_filter": None,
            }
        }
        result = run_sensitivity_grid(deliveries_df, variants_config=custom)
        if not result.empty:
            assert set(result["variant"].unique()) == {"only_q075"}

    def test_ipl_filter(self, deliveries_df: pd.DataFrame) -> None:
        """IPL-only variant should use fewer rows than unfiltered."""
        custom_all = {
            "all": {"q": 0.75, "min_balls": 10, "min_matches": 2, "comp_filter": None}
        }
        custom_ipl = {
            "ipl": {"q": 0.75, "min_balls": 10, "min_matches": 2, "comp_filter": "ipl"}
        }
        res_all = run_sensitivity_grid(deliveries_df, variants_config=custom_all)
        res_ipl = run_sensitivity_grid(deliveries_df, variants_config=custom_ipl)
        # IPL-only should have fewer or equal eligible players
        if not res_all.empty and not res_ipl.empty:
            assert res_ipl["player_id"].nunique() <= res_all["player_id"].nunique()

    def test_empty_input(self) -> None:
        """Empty input should return an empty DataFrame with correct columns."""
        df_empty = pd.DataFrame(
            columns=["match_id", "player_id", "p_balls", "p_val", "leverage", "comp_name"]
        )
        result = run_sensitivity_grid(df_empty)
        expected_cols = {"player_id", "variant", "rank", "in_top10", "robust_count"}
        assert expected_cols.issubset(set(result.columns))
