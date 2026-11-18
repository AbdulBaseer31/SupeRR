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
from pressure.winprob import fit_predict_winprob
from pressure.leverage import compute_leverage_and_flags
from pressure.aggregate import aggregate_player_match, generate_eligibility_scan
from pressure.shrink import compute_empirical_bayes_shrinkage
from pressure.report_tables import build_ranked_tables

def run_stages_1_to_6(data_dir: Path, out_dir: Path) -> None:
    """Run stages 1 to 6: end-to-end pipeline through ranking tables."""
    print(f"Loading data from: {data_dir}")
    dfs = load_all_csvs(data_dir)

    print("Stage 1: Diagnostics and ledger...")
    ledger, dup_names, diag_text = compute_diagnostics_and_ledger(dfs, out_dir)
    print(diag_text)

    print("\nStage 2: Prepping cricket delivery flags and match state...")
    df_prep = prep_deliveries(dfs)
    print(f"Prepped {len(df_prep)} deliveries across {df_prep['match_id'].nunique()} matches.")

    print("\nStage 3: Building par tables and delivery values...")
    par_table = build_par_tables(df_prep)
    wcost_table = build_wicket_costs(par_table)
    df_val = compute_values_per_ball(df_prep, par_table)
    print(f"Computed delivery values. Mean v_bat: {df_val['v_bat'].mean():.4f}")

    print("\nStage 4: Fitting win probability models and computing leverage...")
    df_wp = fit_predict_winprob(df_val)
    df_lev, df_exhibit, df_dist = compute_leverage_and_flags(df_wp, out_dir)
    print("Leverage and pressure flags calculated. Validation exhibit saved.")

    print("\nStage 5: Aggregation, eligibility scan, and Empirical-Bayes shrinkage...")
    pm, pagg = aggregate_player_match(df_lev)
    df_scan = generate_eligibility_scan(pagg, out_dir)
    shrunk, params = compute_empirical_bayes_shrinkage(
        pagg,
        min_balls=config.MIN_PRESSURE_BALLS,
        min_matches=config.MIN_PRESSURE_MATCHES,
        out_dir=out_dir
    )
    print(f"Shrinkage parameters calculated:\n{params.to_string(index=False)}")

    print("\nStage 6: Generating final ranking tables...")
    b_ranked, bowl_ranked = build_ranked_tables(shrunk, dfs["competition_team_player_mapping"], out_dir)
    print(f"\nTop 5 Batters under Pressure:\n{b_ranked.head(5)[['rank', 'player_name', 'P_star', 'Delta_star']].to_string(index=False)}")
    print(f"\nTop 5 Bowlers under Pressure:\n{bowl_ranked.head(5)[['rank', 'player_name', 'P_star', 'Delta_star']].to_string(index=False)}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pressure Pipeline")
    parser.add_argument("--fixture", action="store_true", help="Run on synthetic fixture data")
    args = parser.parse_args()

    data_dir = config.FIXTURE_DIR if args.fixture else config.DATA_DIR
    out_dir = config.OUT_DIR
    run_stages_1_to_6(data_dir, out_dir)

if __name__ == "__main__":
    main()
