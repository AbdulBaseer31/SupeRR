"""Acceptance tests for S1: Load, diagnostics, and exclusion ledger."""
import pytest
from pathlib import Path
import pandas as pd

from pressure.config import FIXTURE_DIR, OUT_DIR
from pressure.io_load import load_all_csvs
from pressure.ledger import compute_diagnostics_and_ledger

def test_load_all_csvs():
    """Verify all 6 CSVs load from fixture directory."""
    dfs = load_all_csvs(FIXTURE_DIR)
    expected_keys = {
        "competitions",
        "teams",
        "competition_team_player_mapping",
        "matches",
        "playing_eleven",
        "ball_by_ball",
    }
    assert set(dfs.keys()) == expected_keys
    for name, df in dfs.items():
        assert len(df) > 0, f"Table {name} is empty"

def test_ledger_reconciliation(tmp_path):
    """Verify that every single ball_by_ball row is accounted for in the ledger."""
    dfs = load_all_csvs(FIXTURE_DIR)
    bbb_count = len(dfs["ball_by_ball"])
    
    ledger_df, dup_names_df, diag_text = compute_diagnostics_and_ledger(dfs, tmp_path)
    
    total_ledger_rows = ledger_df["count"].sum()
    assert total_ledger_rows == bbb_count, f"Ledger sum {total_ledger_rows} != raw count {bbb_count}"
    assert (tmp_path / "diagnostics.txt").exists()
    assert (tmp_path / "ledger.csv").exists()
    assert (tmp_path / "duplicate_names.csv").exists()

def test_diagnostics_content(tmp_path):
    """Verify diagnostics text contains answers for Q1 through Q10."""
    dfs = load_all_csvs(FIXTURE_DIR)
    _, _, diag_text = compute_diagnostics_and_ledger(dfs, tmp_path)
    
    for q_num in range(1, 11):
        assert f"Q{q_num}_" in diag_text, f"Missing Q{q_num} in diagnostics"
