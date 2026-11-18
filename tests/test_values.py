"""Acceptance tests for S3: Par tables and value per ball."""
from pathlib import Path
import pandas as pd
import numpy as np

from pressure.config import FIXTURE_DIR
from pressure.io_load import load_all_csvs
from pressure.prep import prep_deliveries
from pressure.tables import build_par_tables, build_wicket_costs
from pressure.values import compute_values_per_ball

def test_par_tables_and_values():
    """Verify par tables generation and value-per-ball properties (Acceptance Test 6)."""
    dfs = load_all_csvs(FIXTURE_DIR)
    df_prep = prep_deliveries(dfs)

    par_table = build_par_tables(df_prep)
    wcost_table = build_wicket_costs(par_table)
    df_val = compute_values_per_ball(df_prep, par_table)

    # Par tables checks
    assert len(par_table) == 2 * 121 * 10 # 2 groups, 121 balls_left, 10 wickets
    assert (par_table.loc[par_table["balls_left"] == 0, "er"] == 0).all()
    assert (wcost_table["wcost"] >= 0).all(), "Wicket cost must be non-negative"

    # Values check (Test 6: League mean value per ball is approximately centered around 0)
    # Mean batter value per ball in expectation is close to 0 against par
    mean_v_bat = df_val["v_bat"].mean()
    print(f"Mean v_bat across league: {mean_v_bat:.4f}")
    assert abs(mean_v_bat) < 1.5, f"League mean v_bat {mean_v_bat} diverged significantly from 0"

    assert "v_bat" in df_val.columns
    assert "v_bowl" in df_val.columns
    assert not df_val["v_bat"].isna().any()
    assert not df_val["v_bowl"].isna().any()
