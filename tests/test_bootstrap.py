"""Tests for pressure/bootstrap.py (Package A — S7).

Acceptance criteria from Bhavesh_Spec.md:
  1. Identical output on two runs with the same seed.
  2. B=1000 finishes in <60 seconds on the fixture.
  3. Output columns and value-range checks.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Allow running from repo root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pressure.bootstrap import run_match_bootstrap


# ---------------------------------------------------------------------------
# Shared fixture builder
# ---------------------------------------------------------------------------

def _make_player_match_df(
    n_players: int = 30,
    n_matches: int = 60,
    seed: int = 42,
) -> pd.DataFrame:
    """Create a synthetic player-match DataFrame matching the interface contract."""
    rng = np.random.default_rng(seed)

    rows = []
    for pid in range(1, n_players + 1):
        # Each player appears in a random subset of matches
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


@pytest.fixture
def player_match_df() -> pd.DataFrame:
    return _make_player_match_df()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunMatchBootstrap:
    """Tests for the main bootstrap entry point."""

    def test_deterministic_with_fixed_seed(self, player_match_df: pd.DataFrame) -> None:
        """Two runs with the same seed must produce identical output."""
        result1 = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        result2 = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        pd.testing.assert_frame_equal(result1, result2)

    def test_different_seed_different_output(self, player_match_df: pd.DataFrame) -> None:
        """Different seeds should (almost certainly) produce different results."""
        result1 = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        result2 = run_match_bootstrap(player_match_df, n_rounds=50, seed=99)
        # At least one value should differ
        assert not result1.equals(result2)

    def test_output_columns(self, player_match_df: pd.DataFrame) -> None:
        """Output must contain the specified columns."""
        result = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        expected_cols = {"player_id", "top10_prob", "rank_p10", "rank_median", "rank_p90"}
        assert expected_cols.issubset(set(result.columns))

    def test_top10_prob_range(self, player_match_df: pd.DataFrame) -> None:
        """top10_prob must be in [0.0, 1.0]."""
        result = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        if not result.empty:
            assert result["top10_prob"].min() >= 0.0
            assert result["top10_prob"].max() <= 1.0

    def test_rank_ordering(self, player_match_df: pd.DataFrame) -> None:
        """rank_p10 <= rank_median <= rank_p90 for every player."""
        result = run_match_bootstrap(player_match_df, n_rounds=100, seed=42)
        if not result.empty:
            assert (result["rank_p10"] <= result["rank_median"]).all(), \
                "rank_p10 must be <= rank_median"
            assert (result["rank_median"] <= result["rank_p90"]).all(), \
                "rank_median must be <= rank_p90"

    def test_ranks_are_positive(self, player_match_df: pd.DataFrame) -> None:
        """All rank values must be >= 1."""
        result = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        if not result.empty:
            assert (result["rank_p10"] >= 1).all()
            assert (result["rank_median"] >= 1).all()
            assert (result["rank_p90"] >= 1).all()

    def test_missing_columns_raises(self) -> None:
        """Should raise ValueError if required columns are missing."""
        df_bad = pd.DataFrame({"match_id": [1], "player_id": [1]})
        with pytest.raises(ValueError, match="Missing required columns"):
            run_match_bootstrap(df_bad)

    def test_empty_input(self) -> None:
        """Empty input should return an empty DataFrame with correct columns."""
        df_empty = pd.DataFrame(
            columns=["match_id", "player_id", "role", "p_balls", "p_val", "u_balls", "u_val"]
        )
        result = run_match_bootstrap(df_empty, n_rounds=10, seed=42)
        expected_cols = {"player_id", "top10_prob", "rank_p10", "rank_median", "rank_p90"}
        assert expected_cols.issubset(set(result.columns))
        assert len(result) == 0

    def test_performance_under_60s(self) -> None:
        """B=1000 on a fixture-sized dataset must finish in <60 seconds."""
        df = _make_player_match_df(n_players=30, n_matches=60, seed=42)
        start = time.perf_counter()
        run_match_bootstrap(df, n_rounds=1000, seed=42)
        elapsed = time.perf_counter() - start
        assert elapsed < 60, f"Bootstrap took {elapsed:.1f}s, must be <60s"

    def test_sorted_by_rank_median(self, player_match_df: pd.DataFrame) -> None:
        """Output should be sorted by rank_median ascending."""
        result = run_match_bootstrap(player_match_df, n_rounds=50, seed=42)
        if len(result) > 1:
            assert (result["rank_median"].diff().dropna() >= 0).all()
