"""Acceptance tests for S4: Win probability, leverage, and validation exhibits."""
from pathlib import Path
import pandas as pd
import numpy as np

from pressure.config import FIXTURE_DIR
from pressure.io_load import load_all_csvs
from pressure.prep import prep_deliveries
from pressure.tables import build_par_tables
from pressure.values import compute_values_per_ball
from pressure.winprob import fit_predict_winprob
from pressure.leverage import compute_leverage_and_flags

def test_winprob_and_leverage(tmp_path):
    """Verify WP cross-fitting, leverage, pressure flags, and exhibit generation (Tests 4 & 5)."""
    dfs = load_all_csvs(FIXTURE_DIR)
    df_prep = prep_deliveries(dfs)
    par_table = build_par_tables(df_prep)
    df_val = compute_values_per_ball(df_prep, par_table)

    df_wp = fit_predict_winprob(df_val)

    # Acceptance Test 4: WP within [0, 1] bounds without NaNs
    assert "wp" in df_wp.columns
    assert (df_wp["wp"] >= 0.0).all() and (df_wp["wp"] <= 1.0).all()
    assert not df_wp["wp"].isna().any()

    df_lev, df_exhibit, df_dist = compute_leverage_and_flags(df_wp, tmp_path)

    # Acceptance Test 5: Leverage exhibit and distributions exist and separate situations
    assert "leverage" in df_lev.columns
    assert "is_pressure" in df_lev.columns
    assert "is_pressure_rule" in df_lev.columns
    assert (tmp_path / "validation_pressure_vs_ordinary.csv").exists()
    assert (tmp_path / "leverage_distribution.csv").exists()

    assert len(df_exhibit) > 0
    # Confirm dot_pct, boundary_pct, wicket_pct exist
    for metric in ["dot_pct", "boundary_pct", "wicket_pct", "runs_per_ball"]:
        assert metric in df_exhibit.columns
