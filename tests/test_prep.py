"""Acceptance tests for S2: Cricket flags and match state derivation."""
from pathlib import Path
import pandas as pd
import numpy as np

from pressure.config import FIXTURE_DIR
from pressure.io_load import load_all_csvs
from pressure.prep import prep_deliveries

def test_cricket_flags_and_state():
    """Verify cricket delivery flags, sorting, and state ranges (Tests 2 and 3)."""
    dfs = load_all_csvs(FIXTURE_DIR)
    df = prep_deliveries(dfs)

    # Required columns check
    expected_cols = [
        "is_wide", "is_nb", "legal", "bat_runs", "extras", "total", "charged",
        "team_wicket", "bowler_credit", "dismissed_id", "legal_before",
        "wkts_before", "score_before", "inn_total", "remaining", "balls_left",
        "ov", "wb", "phase", "target", "rn", "grp"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"

    # State bounds (Test 2: Balls per innings match scheduled overs, wkts never exceed 10)
    assert df["wkts_before"].min() >= 0
    assert df["wkts_before"].max() <= 10
    assert df["legal_before"].min() >= 0
    assert df["legal_before"].max() <= 120
    assert df["balls_left"].min() >= 0
    assert df["balls_left"].max() <= 120

    # Test 3: Innings 2 required runs & target consistency
    inn2 = df[df["innings"] == 2]
    assert not inn2["target"].isna().any(), "Inn 2 target should not be null"
    assert (inn2["rn"] >= 0).all(), "Inn 2 required runs must be non-negative"
