"""Generate final ranking tables for batters and bowlers."""
from pathlib import Path
from typing import Tuple, Dict
import pandas as pd
import numpy as np

def build_ranked_tables(
    df_shrunk: pd.DataFrame,
    mapping_df: pd.DataFrame,
    out_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Build and save batters_ranked.csv and bowlers_ranked.csv.
    
    Includes player metadata (name, main_team), sample statistics, shrunk P*,
    Delta_star, dip filter status, and rank order.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Player identity and main team mapping
    # Most frequent team for each player
    main_teams = mapping_df.groupby(["player_id", "team_name"]).size().reset_index(name="counts")
    main_teams = main_teams.sort_values(["player_id", "counts"], ascending=[True, False]).drop_duplicates(subset=["player_id"])
    player_team_map = main_teams.set_index("player_id")["team_name"].to_dict()
    
    player_names = mapping_df.drop_duplicates(subset=["player_id"]).set_index("player_id")["player_name"].to_dict()

    df = df_shrunk.copy()
    df["player_name"] = df["player_id"].map(player_names)
    df["main_team"] = df["player_id"].map(player_team_map).fillna("Unknown")

    # Batters
    batters = df[df["role"] == "bat"].copy()
    # Filter by dip and eligibility if applicable, else rank on P_star
    batters["raw_rank"] = batters["P_obs"].rank(ascending=False, method="min").astype(int)
    # Primary ranking on P_star among those passing dip filter
    batters_eligible = batters[batters["passes_dip"]].copy()
    if len(batters_eligible) < 10:
        batters_eligible = batters # fallback if few pass
    batters_eligible["rank"] = batters_eligible["P_star"].rank(ascending=False, method="min").astype(int)
    batters_ranked = batters_eligible.sort_values("rank").reset_index(drop=True)

    # Columns specified in Spec section 12
    report_cols = [
        "rank", "player_id", "player_name", "main_team", "p_balls", "p_matches_count",
        "P_obs", "U_obs", "P_star", "Delta_star", "passes_dip", "raw_rank"
    ]
    # Ensure all report columns exist
    for col in report_cols:
        if col not in batters_ranked.columns:
            batters_ranked[col] = np.nan
    batters_out = batters_ranked[report_cols]
    batters_out.to_csv(out_dir / "batters_ranked.csv", index=False)

    # Bowlers
    bowlers = df[df["role"] == "bowl"].copy()
    bowlers["raw_rank"] = bowlers["P_obs"].rank(ascending=False, method="min").astype(int)
    bowlers_eligible = bowlers[bowlers["passes_dip"]].copy()
    if len(bowlers_eligible) < 10:
        bowlers_eligible = bowlers
    bowlers_eligible["rank"] = bowlers_eligible["P_star"].rank(ascending=False, method="min").astype(int)
    bowlers_ranked = bowlers_eligible.sort_values("rank").reset_index(drop=True)

    for col in report_cols:
        if col not in bowlers_ranked.columns:
            bowlers_ranked[col] = np.nan
    bowlers_out = bowlers_ranked[report_cols]
    bowlers_out.to_csv(out_dir / "bowlers_ranked.csv", index=False)

    return batters_out, bowlers_out
