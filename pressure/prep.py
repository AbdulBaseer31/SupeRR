"""Cricket delivery flags, match state calculation, and ordering."""
from typing import Dict
import pandas as pd
import numpy as np

def prep_deliveries(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compute cricket flags, order deliveries, and derive match state per delivery."""
    bbb = dfs["ball_by_ball"].copy()
    matches = dfs["matches"]
    comps = dfs["competitions"]

    # Filter out super overs (innings > 2) and rain-revised/abandoned matches
    revised_mids = set(matches[~matches["first_inn_revised_overs"].isna()]["match_id"].unique())
    no_result_mids = set(matches[matches["win_team_id"].isna()]["match_id"].unique())
    exclude_mids = revised_mids.union(no_result_mids)

    df = bbb[(bbb["innings"] <= 2) & (~bbb["match_id"].isin(exclude_mids))].copy()

    # Cricket flags
    df["is_wide"] = df["extras_type"].str.lower() == "wides"
    df["is_nb"] = df["extras_type"].str.lower() == "noballs"
    df["legal"] = (~df["is_wide"]) & (~df["is_nb"])

    # Runs accounting
    # Byes & leg-byes are not batter runs
    df["bat_runs"] = df["runs"].fillna(0).astype(int)
    extras_total = df["extras1_runs"].fillna(0).astype(int) + df["extras_2_runs"].fillna(0).astype(int)
    df["extras"] = extras_total
    df["total"] = df["bat_runs"] + df["extras"]

    # Charged to bowler: total runs except byes and leg-byes
    is_bye_legbye = df["extras_type"].str.lower().isin(["byes", "legbyes"])
    df["charged"] = np.where(is_bye_legbye, 0, df["total"])

    # Wickets
    # Dismissal types that are bowler credit (caught, bowled, lbw, stumped, hit wicket)
    non_bowler_dismissals = ["run out", "retired hurt", "obstructing the field", "timed out"]
    is_wkt = df["is_wicket"].fillna(False).astype(bool)
    d_type_clean = df["dismissal_type"].fillna("").str.lower()

    df["team_wicket"] = is_wkt
    df["bowler_credit"] = is_wkt & (~d_type_clean.isin(non_bowler_dismissals))
    df["dismissed_id"] = df["dismissed_player_id"]

    # Strict sorting
    df = df.sort_values(["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]).reset_index(drop=True)

    # Cumulative match state per innings
    grouped = df.groupby(["match_id", "innings"], group_keys=False)

    df["score_before"] = grouped["total"].cumsum() - df["total"]
    df["legal_before"] = grouped["legal"].cumsum() - df["legal"].astype(int)
    df["wkts_before"] = grouped["team_wicket"].cumsum() - df["team_wicket"].astype(int)

    # Balls left out of 120 (standard T20)
    df["balls_left"] = np.maximum(0, 120 - df["legal_before"])
    df["ov"] = df["legal_before"] // 6
    df["wb"] = df["legal_before"] % 6

    # Phase: Powerplay (0-5 overs), Middle (6-14 overs), Death (15-19 overs)
    conditions = [
        df["ov"] < 6,
        (df["ov"] >= 6) & (df["ov"] < 15),
        df["ov"] >= 15
    ]
    df["phase"] = np.select(conditions, ["powerplay", "middle", "death"], default="death")

    # Join competition group (IPL vs T20I/other)
    match_comp = matches.set_index("match_id")["comp_id"].to_dict()
    df["comp_id"] = df["match_id"].map(match_comp)

    comp_name_map = comps.set_index("comp_id")["comp_name"].to_dict()
    df["comp_name"] = df["comp_id"].map(comp_name_map)
    df["grp"] = np.where(
        df["comp_name"].fillna("").str.contains("Indian Premier League", case=False),
        "IPL",
        "T20I"
    )

    # Target & required runs for innings 2
    # First innings total per match
    inn1_totals = df[df["innings"] == 1].groupby("match_id")["total"].sum().to_dict()
    df["inn_total"] = df.groupby(["match_id", "innings"])["total"].transform("sum")

    df["target"] = np.where(df["innings"] == 2, df["match_id"].map(inn1_totals) + 1, np.nan)
    df["rn"] = np.where(df["innings"] == 2, np.maximum(0, df["target"] - df["score_before"]), np.nan)
    df["remaining"] = df["inn_total"] - df["score_before"]

    return df
