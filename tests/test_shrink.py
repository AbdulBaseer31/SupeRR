"""Acceptance tests for S5: Aggregation, empirical-Bayes shrinkage, and dip filter."""
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
from pressure.aggregate import aggregate_player_match, generate_eligibility_scan
from pressure.shrink import compute_empirical_bayes_shrinkage

def test_aggregation_and_shrinkage(tmp_path):
    """Verify player aggregation, shrinkage formulas, and k warning logic (Acceptance Test 7)."""
    dfs = load_all_csvs(FIXTURE_DIR)
    df_prep = prep_deliveries(dfs)
    par_table = build_par_tables(df_prep)
    df_val = compute_values_per_ball(df_prep, par_table)
    df_wp = fit_predict_winprob(df_val)
    df_lev, _, _ = compute_leverage_and_flags(df_wp, tmp_path)

    pm, pagg = aggregate_player_match(df_lev)

    # Acceptance Test 7 checks: totals reconcile
    total_val_pm = pm["total_val"].sum()
    total_val_pagg = pagg["total_val"].sum()
    assert abs(total_val_pm - total_val_pagg) < 1e-3, "Player-match totals must equal player career totals"

    # Eligibility scan
    df_scan = generate_eligibility_scan(pagg, tmp_path)
    assert (tmp_path / "eligibility_scan.csv").exists()
    assert len(df_scan) > 0

    # Shrinkage
    shrunk, params = compute_empirical_bayes_shrinkage(pagg, min_balls=30, min_matches=3, out_dir=tmp_path)
    assert (tmp_path / "shrinkage_params.csv").exists()
    assert "P_star" in shrunk.columns
    assert "passes_dip" in shrunk.columns

    # Test extreme case for k warning logic
    # In shrunk.py: warning triggers if k < 5 or k > 500
    assert params["k_warning"].any(), "Shrinkage parameters should record k_warning"
