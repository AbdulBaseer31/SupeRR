"""Per-delivery value calculations for batting and bowling."""
import pandas as pd
import numpy as np

def compute_values_per_ball(df_prep: pd.DataFrame, par_table: pd.DataFrame) -> pd.DataFrame:
    """Compute V_t = r_t + ER(s_{t+1}) - ER(s_t) per delivery for batters and bowlers."""
    df = df_prep.copy()

    # Match state after delivery t
    # Balls left decreases by 1 if legal ball
    df["balls_left_next"] = np.where(df["legal"], np.maximum(0, df["balls_left"] - 1), df["balls_left"])
    # Wickets lost increases by 1 if wicket fell
    df["wkts_next"] = np.where(df["team_wicket"], np.minimum(10, df["wkts_before"] + 1), df["wkts_before"])

    # Lookup ER(s_t)
    df = pd.merge(
        df,
        par_table.rename(columns={"er": "er_t"}),
        on=["grp", "balls_left", "wkts_before"],
        how="left"
    )

    # Lookup ER(s_{t+1})
    df = pd.merge(
        df,
        par_table.rename(columns={"balls_left": "balls_left_next", "wkts_before": "wkts_next", "er": "er_t_next"}),
        on=["grp", "balls_left_next", "wkts_next"],
        how="left"
    )
    # If all out (10 wickets) or 0 balls left, ER_{t+1} is 0
    df.loc[df["wkts_next"] >= 10, "er_t_next"] = 0.0
    df["er_t_next"] = df["er_t_next"].fillna(0.0)
    df["er_t"] = df["er_t"].fillna(0.0)

    # Value of the delivery: V_t = total_runs + ER_{t+1} - ER_t
    # Batter currency: bat_runs + (ER_{t+1} - ER_t) if legal/wicket, adjusted for wicket cost
    df["delta_er"] = df["er_t_next"] - df["er_t"]
    
    # Batting value:
    # Batter gets credit for bat_runs and is charged wicket loss if dismissed
    # Non-striker run out: charged to non-striker
    is_run_out = df["dismissal_type"].fillna("").str.lower() == "run out"
    is_non_striker_dismissed = is_run_out & (df["dismissed_id"] == df["non_striker_id"])

    # Standard striker value
    df["v_bat"] = np.where(
        is_non_striker_dismissed,
        df["bat_runs"], # striker gets bat runs, not charged for partner's run out
        df["bat_runs"] + df["delta_er"]
    )

    # Bowling value:
    # Bowler is credited with savings: - (charged_runs + delta_er) for bowler-credited events
    # For non-bowler wickets (e.g. run outs), delta_er wicket penalty is not credited to bowler
    df["v_bowl"] = np.where(
        df["bowler_credit"],
        -(df["charged"] + df["delta_er"]),
        -df["charged"] # just negative of runs conceded
    )

    return df
