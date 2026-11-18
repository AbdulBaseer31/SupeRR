"""Pipeline orchestrator: Stage 1 (Load, diagnostics, ledger)."""
import argparse
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pressure import config
from pressure.io_load import load_all_csvs
from pressure.ledger import compute_diagnostics_and_ledger
from pressure.prep import prep_deliveries
from pressure.tables import build_par_tables, build_wicket_costs
from pressure.values import compute_values_per_ball

def run_stages_1_to_3(data_dir: Path, out_dir: Path) -> None:
    """Run stages 1 to 3: load, diagnostics, match state, par tables, values."""
    print(f"Loading data from: {data_dir}")
    dfs = load_all_csvs(data_dir)
    print("Files loaded. Stage 1: Diagnostics and ledger...")
    ledger, dup_names, diag_text = compute_diagnostics_and_ledger(dfs, out_dir)
    print(diag_text)

    print("\nStage 2: Prepping cricket delivery flags and match state...")
    df_prep = prep_deliveries(dfs)
    print(f"Prepped {len(df_prep)} deliveries across {df_prep['match_id'].nunique()} matches.")

    print("\nStage 3: Building par tables and delivery values...")
    par_table = build_par_tables(df_prep)
    wcost_table = build_wicket_costs(par_table)
    df_val = compute_values_per_ball(df_prep, par_table)
    print(f"Computed v_bat and v_bowl. Mean v_bat: {df_val['v_bat'].mean():.4f}, Mean v_bowl: {df_val['v_bowl'].mean():.4f}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pressure Pipeline")
    parser.add_argument("--fixture", action="store_true", help="Run on synthetic fixture data")
    args = parser.parse_args()

    data_dir = config.FIXTURE_DIR if args.fixture else config.DATA_DIR
    out_dir = config.OUT_DIR
    run_stages_1_to_3(data_dir, out_dir)

if __name__ == "__main__":
    main()
