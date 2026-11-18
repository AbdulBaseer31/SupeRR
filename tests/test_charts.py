"""Tests for pressure/charts.py (Package C — S9).

Acceptance criteria from Bhavesh_Spec.md:
  1. All 4 PNGs exist and have non-zero size.
  2. No data rows or player IDs on chart titles (except finalist names on charts 3/4).
  3. Functions run without error on mock DataFrames.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pressure.charts import (
    chart_batter_finalists,
    chart_bowler_finalists,
    chart_leverage_distribution,
    chart_validation_exhibit,
    generate_all_charts,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_charts_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for chart output."""
    d = tmp_path / "charts"
    d.mkdir()
    return d


@pytest.fixture
def leverage_df() -> pd.DataFrame:
    """Mock leverage DataFrame."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({"leverage": rng.exponential(1.0, size=1000)})


@pytest.fixture
def validation_df() -> pd.DataFrame:
    """Mock validation exhibit DataFrame."""
    rows = []
    for phase in ["Powerplay", "Middle", "Death"]:
        for group in ["pressure", "ordinary"]:
            rows.append({
                "phase": phase,
                "group": group,
                "dot_pct": np.random.uniform(30, 50),
                "boundary_pct": np.random.uniform(10, 25),
                "wicket_pct": np.random.uniform(2, 8),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def batters_df() -> pd.DataFrame:
    """Mock ranked batters DataFrame."""
    names = [f"Batter_{i}" for i in range(1, 11)]
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "player_name": names,
        "p_star": np.sort(rng.uniform(0.5, 3.0, 10))[::-1],
        "rank_p10": list(range(1, 11)),
        "rank_median": [i + 1 for i in range(10)],
        "rank_p90": [i + 5 for i in range(10)],
    })


@pytest.fixture
def bowlers_df() -> pd.DataFrame:
    """Mock ranked bowlers DataFrame."""
    names = [f"Bowler_{i}" for i in range(1, 11)]
    rng = np.random.default_rng(99)
    return pd.DataFrame({
        "player_name": names,
        "p_star": np.sort(rng.uniform(0.3, 2.5, 10))[::-1],
        "rank_p10": list(range(1, 11)),
        "rank_median": [i + 1 for i in range(10)],
        "rank_p90": [i + 4 for i in range(10)],
    })


# ---------------------------------------------------------------------------
# Tests — Individual Chart Functions
# ---------------------------------------------------------------------------

class TestChartLeverageDistribution:
    def test_creates_png(self, leverage_df: pd.DataFrame, tmp_charts_dir: Path) -> None:
        out = tmp_charts_dir / "leverage_distribution.png"
        result = chart_leverage_distribution(leverage_df, out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_custom_quantile(self, leverage_df: pd.DataFrame, tmp_charts_dir: Path) -> None:
        out = tmp_charts_dir / "leverage_q067.png"
        result = chart_leverage_distribution(leverage_df, out, q=0.67)
        assert result.exists()


class TestChartValidationExhibit:
    def test_creates_png(self, validation_df: pd.DataFrame, tmp_charts_dir: Path) -> None:
        out = tmp_charts_dir / "validation_exhibit.png"
        result = chart_validation_exhibit(validation_df, out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0


class TestChartBatterFinalists:
    def test_creates_png(self, batters_df: pd.DataFrame, tmp_charts_dir: Path) -> None:
        out = tmp_charts_dir / "batter_finalists.png"
        result = chart_batter_finalists(batters_df, out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_empty_input(self, tmp_charts_dir: Path) -> None:
        df_empty = pd.DataFrame(
            columns=["player_name", "p_star", "rank_p10", "rank_median", "rank_p90"]
        )
        out = tmp_charts_dir / "batter_empty.png"
        result = chart_batter_finalists(df_empty, out)
        assert out.exists()
        assert out.stat().st_size > 0


class TestChartBowlerFinalists:
    def test_creates_png(self, bowlers_df: pd.DataFrame, tmp_charts_dir: Path) -> None:
        out = tmp_charts_dir / "bowler_finalists.png"
        result = chart_bowler_finalists(bowlers_df, out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0


# ---------------------------------------------------------------------------
# Tests — generate_all_charts convenience function
# ---------------------------------------------------------------------------

class TestGenerateAllCharts:
    def test_all_four_pngs_exist(
        self,
        leverage_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        batters_df: pd.DataFrame,
        bowlers_df: pd.DataFrame,
        tmp_charts_dir: Path,
    ) -> None:
        """All 4 PNGs must be created with non-zero size."""
        paths = generate_all_charts(
            leverage_df, validation_df, batters_df, bowlers_df, tmp_charts_dir
        )

        assert len(paths) == 4
        expected_names = {
            "leverage_distribution",
            "validation_exhibit",
            "batter_finalists",
            "bowler_finalists",
        }
        assert set(paths.keys()) == expected_names

        for name, path in paths.items():
            assert path.exists(), f"{name} chart not created"
            assert path.stat().st_size > 0, f"{name} chart is empty"
            assert path.suffix == ".png", f"{name} chart is not a PNG"

    def test_creates_output_directory(
        self,
        leverage_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        batters_df: pd.DataFrame,
        bowlers_df: pd.DataFrame,
        tmp_path: Path,
    ) -> None:
        """Should create the output directory if it doesn't exist."""
        new_dir = tmp_path / "new_charts_dir"
        assert not new_dir.exists()

        paths = generate_all_charts(
            leverage_df, validation_df, batters_df, bowlers_df, new_dir
        )
        assert new_dir.exists()
        assert len(paths) == 4
