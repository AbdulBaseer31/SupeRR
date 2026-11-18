"""Exclusion ledger and data diagnostics (Q1 to Q10) reporting only aggregates."""
from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import numpy as np

def compute_diagnostics_and_ledger(
    dfs: Dict[str, pd.DataFrame],
    out_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """Compute diagnostics Q1-Q10, generate exclusion ledger, and find duplicate names.
    
    All prints and saved diagnostic reports contain strictly aggregate summaries.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    bbb = dfs["ball_by_ball"]
    matches = dfs["matches"]
    comps = dfs["competitions"]
    teams = dfs["teams"]
    mapping = dfs["competition_team_player_mapping"]
    eleven = dfs["playing_eleven"]

    diag_lines = ["=== DIAGNOSTICS REPORT (AGGREGATES ONLY) ==="]

    # Q1: Exact duplicate rows in ball_by_ball
    dup_bbb = int(bbb.duplicated().sum())
    diag_lines.append(f"Q1_duplicate_rows_bbb: {dup_bbb}")

    # Q2: Delivery key uniqueness (match_id, innings, overid, over_ball_num)
    deliv_keys = ["match_id", "innings", "overid", "over_ball_num"]
    dup_deliv_keys = int(bbb.duplicated(subset=deliv_keys).sum())
    diag_lines.append(f"Q2_duplicate_delivery_keys: {dup_deliv_keys}")

    # Q3: Innings distribution in ball_by_ball
    inn_counts = bbb["innings"].value_counts().to_dict()
    diag_lines.append(f"Q3_innings_distribution: {inn_counts}")

    # Q4: Match result status & revisions in matches
    total_matches = len(matches)
    revised_matches = int((~matches["first_inn_revised_overs"].isna()).sum())
    no_result_matches = int(matches["win_team_id"].isna().sum())
    diag_lines.append(
        f"Q4_matches_total: {total_matches}, revised_overs_count: {revised_matches}, no_result_count: {no_result_matches}"
    )

    # Q5: Extras types distribution
    extras_counts = bbb["extras_type"].value_counts(dropna=False).to_dict()
    diag_lines.append(f"Q5_extras_type_distribution: {extras_counts}")

    # Q6: Dismissal types distribution
    dismissal_counts = bbb["dismissal_type"].value_counts(dropna=False).to_dict()
    diag_lines.append(f"Q6_dismissal_type_distribution: {dismissal_counts}")

    # Q7: Competitions breakdown (IPL vs T20I / other)
    ipl_comps = comps[comps["comp_name"].str.contains("Indian Premier League", case=False, na=False)]
    diag_lines.append(f"Q7_ipl_competitions_count: {len(ipl_comps)}, total_competitions: {len(comps)}")

    # Q8: Playing XI representation
    matches_in_eleven = eleven["match_id"].nunique()
    matches_in_bbb = bbb["match_id"].nunique()
    diag_lines.append(f"Q8_matches_in_playing_eleven: {matches_in_eleven}, matches_in_bbb: {matches_in_bbb}")

    # Q9: Player ID overlap across competitions (IPL vs Non-IPL)
    ipl_comp_ids = set(ipl_comps["comp_id"].unique())
    ipl_players = set(mapping[mapping["comp_id"].isin(ipl_comp_ids)]["player_id"].unique())
    non_ipl_players = set(mapping[~mapping["comp_id"].isin(ipl_comp_ids)]["player_id"].unique())
    overlap_count = len(ipl_players.intersection(non_ipl_players))
    diag_lines.append(
        f"Q9_ipl_unique_players: {len(ipl_players)}, non_ipl_unique_players: {len(non_ipl_players)}, overlap: {overlap_count}"
    )

    # Q10: Duplicate player names mapping to multiple IDs
    name_id_counts = mapping.groupby("player_name")["player_id"].nunique()
    dup_names_list = name_id_counts[name_id_counts > 1].index.tolist()
    diag_lines.append(f"Q10_duplicate_player_names_count: {len(dup_names_list)}")

    # Save duplicate names mapping (only name and player_id, team_id, comp_id)
    dup_names_df = mapping[mapping["player_name"].isin(dup_names_list)][
        ["player_name", "player_id", "team_id", "comp_id"]
    ].drop_duplicates().sort_values(["player_name", "player_id"])
    dup_names_df.to_csv(out_dir / "duplicate_names.csv", index=False)

    # Build Exclusion Ledger for ball_by_ball
    # Category 1: Innings > 2 (Super overs)
    cond_super_over = bbb["innings"] > 2
    
    # Category 2: Rain-revised or abandoned matches
    revised_mids = set(matches[~matches["first_inn_revised_overs"].isna()]["match_id"].unique())
    no_result_mids = set(matches[matches["win_team_id"].isna()]["match_id"].unique())
    rain_or_no_result = revised_mids.union(no_result_mids)
    cond_rain_or_no_result = bbb["match_id"].isin(rain_or_no_result) & (~cond_super_over)

    # Category 3: Used in primary index
    cond_used = (~cond_super_over) & (~cond_rain_or_no_result)

    ledger_rows = [
        {"bucket": "used_innings_1_and_2_standard", "count": int(cond_used.sum())},
        {"bucket": "excluded_super_over", "count": int(cond_super_over.sum())},
        {"bucket": "excluded_rain_revised_or_abandoned", "count": int(cond_rain_or_no_result.sum())},
    ]
    df_ledger = pd.DataFrame(ledger_rows)
    df_ledger["total_raw_rows"] = len(bbb)
    df_ledger.to_csv(out_dir / "ledger.csv", index=False)

    diag_text = "\n".join(diag_lines)
    (out_dir / "diagnostics.txt").write_text(diag_text, encoding="utf-8")

    return df_ledger, dup_names_df, diag_text
