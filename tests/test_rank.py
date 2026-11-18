"""Acceptance tests for S6: Final ranking tables."""
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
from pressure.aggregate import aggregate_player_match
from pressure.shrink import compute_empirical_bayes_shrinkage
from pressure.report_tables import build_ranked_tables

def test_ranked_tables(tmp_path):
    """Verify final ranking tables and ensure all ranked IDs exist in mapping (Acceptance Test 9)."""
    dfs = load_all_csvs(FIXTURE_DIR)
    df_prep = prep_deliveries(dfs)
    par_table = build_par_tables(df_prep)
    df_val = compute_values_per_ball(df_prep, par_table)
    df_wp = fit_predict_winprob(df_val)
    df_lev, _, _ = compute_leverage_and_flags(df_wp, tmp_path)

    _, pagg = aggregate_player_match(df_lev)
    shrunk, _ = compute_empirical_bayes_shrinkage(pagg, min_balls=20, min_matches=2, out_dir=tmp_path)

    mapping = dfs["competition_team_player_mapping"]
    b_ranked, bowl_ranked = build_ranked_tables(shrunk, mapping, tmp_path)

    # Acceptance Test 9: Output files exist and all ranked player IDs exist in the mapping file
    assert (tmp_path / "batters_ranked.csv").exists()
    assert (tmp_path / "bowlers_ranked.csv").exists()

    known_ids = set(mapping["player_id"].unique())
    assert set(b_ranked["player_id"]).issubset(known_ids), "All ranked batter IDs must exist in mapping"
    assert set(bowl_ranked["player_id"]).issubset(known_ids), "All ranked bowler IDs must exist in mapping"

    # Verify required report columns are populated
    for table in [b_ranked, bowl_ranked]:
        assert len(table) >= 10, "Should have at least top 10 ranked players"
        assert "rank" in table.columns
        assert "player_name" in table.columns
        assert "P_star" in table.columns
        assert "Delta_star" in table.columns
        assert not table["player_name"].isna().any()
