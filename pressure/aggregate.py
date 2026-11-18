"""Player and player-match level aggregation for batting and bowling."""
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np

def aggregate_player_match(df_deliveries: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate per-delivery values to player-match and player career summary tables.
    
    Produces player_match table and player career aggregates for both batters and bowlers.
    """
    df = df_deliveries.copy()

    # Batting aggregations per player per match
    df_bat = df[~df["is_wide"]].copy()
    df_bat["p_val_bat"] = np.where(df_bat["is_pressure"], df_bat["v_bat"], 0.0)
    df_bat["u_val_bat"] = np.where(~df_bat["is_pressure"], df_bat["v_bat"], 0.0)
    df_bat["p_ball_cnt"] = df_bat["is_pressure"].astype(int)
    df_bat["u_ball_cnt"] = (~df_bat["is_pressure"]).astype(int)

    bat_pm = df_bat.groupby(["match_id", "striker_id", "grp"]).agg(
        p_balls=("p_ball_cnt", "sum"),
        p_val=("p_val_bat", "sum"),
        u_balls=("u_ball_cnt", "sum"),
        u_val=("u_val_bat", "sum"),
        total_balls=("legal", "count"),
        total_val=("v_bat", "sum")
    ).reset_index().rename(columns={"striker_id": "player_id"})
    bat_pm["role"] = "bat"

    # Bowling aggregations per player per match
    df_bowl = df.copy()
    df_bowl["p_val_bowl"] = np.where(df_bowl["is_pressure"], df_bowl["v_bowl"], 0.0)
    df_bowl["u_val_bowl"] = np.where(~df_bowl["is_pressure"], df_bowl["v_bowl"], 0.0)
    df_bowl["p_ball_legal"] = (df_bowl["is_pressure"] & df_bowl["legal"]).astype(int)
    df_bowl["u_ball_legal"] = ((~df_bowl["is_pressure"]) & df_bowl["legal"]).astype(int)

    bowl_pm = df_bowl.groupby(["match_id", "bowler_id", "grp"]).agg(
        p_balls=("p_ball_legal", "sum"),
        p_val=("p_val_bowl", "sum"),
        u_balls=("u_ball_legal", "sum"),
        u_val=("u_val_bowl", "sum"),
        total_balls=("legal", "sum"),
        total_val=("v_bowl", "sum")
    ).reset_index().rename(columns={"bowler_id": "player_id"})
    bowl_pm["role"] = "bowl"

    player_match = pd.concat([bat_pm, bowl_pm], ignore_index=True)

    # Player career aggregation
    player_agg = player_match.groupby(["player_id", "role"]).agg(
        matches_count=("match_id", "nunique"),
        p_matches_count=("p_balls", lambda x: int((x > 0).sum())),
        p_balls=("p_balls", "sum"),
        p_val=("p_val", "sum"),
        u_balls=("u_balls", "sum"),
        u_val=("u_val", "sum"),
        total_balls=("total_balls", "sum"),
        total_val=("total_val", "sum")
    ).reset_index()

    # Rates per 100 balls
    player_agg["P_obs"] = np.where(player_agg["p_balls"] > 0, (player_agg["p_val"] / player_agg["p_balls"]) * 100.0, 0.0)
    player_agg["U_obs"] = np.where(player_agg["u_balls"] > 0, (player_agg["u_val"] / player_agg["u_balls"]) * 100.0, 0.0)
    player_agg["Delta_obs"] = player_agg["P_obs"] - player_agg["U_obs"]

    return player_match, player_agg

def generate_eligibility_scan(player_agg: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Scan eligibility numbers across varied ball and match floors and save to CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)
    scan_rows = []
    
    ball_floors = [30, 50, 60, 80, 100]
    match_floors = [3, 5, 8, 10]

    for role in ["bat", "bowl"]:
        sub = player_agg[player_agg["role"] == role]
        for b_floor in ball_floors:
            for m_floor in match_floors:
                eligible = sub[(sub["p_balls"] >= b_floor) & (sub["p_matches_count"] >= m_floor)]
                scan_rows.append({
                    "role": role,
                    "min_pressure_balls": b_floor,
                    "min_pressure_matches": m_floor,
                    "eligible_players_count": len(eligible)
                })

    df_scan = pd.DataFrame(scan_rows)
    df_scan.to_csv(out_dir / "eligibility_scan.csv", index=False)
    return df_scan
