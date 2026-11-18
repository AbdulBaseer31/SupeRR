"""Expected runs (ER) par tables and wicket cost tables from innings 1."""
import pandas as pd
import numpy as np

def build_par_tables(df_prep: pd.DataFrame) -> pd.DataFrame:
    """Build smoothed expected remaining runs ER(balls_left, wkts_lost, grp) from Innings 1."""
    inn1 = df_prep[df_prep["innings"] == 1].copy()

    # Empirical mean remaining runs by (grp, balls_left, wkts_before)
    agg = inn1.groupby(["grp", "balls_left", "wkts_before"])["remaining"].agg(["mean", "count"]).reset_index()
    agg.rename(columns={"mean": "er_empirical", "count": "obs"}, inplace=True)

    # Grid of all possible combinations (0 to 120 balls left, 0 to 9 wickets lost)
    records = []
    for grp in ["IPL", "T20I"]:
        for bl in range(121):
            for w in range(10):
                records.append({"grp": grp, "balls_left": bl, "wkts_before": w})
    grid = pd.DataFrame(records)

    merged = pd.merge(grid, agg, on=["grp", "balls_left", "wkts_before"], how="left")

    # Simple linear prior for expected runs (balls_left * run_rate / 6 with wicket dampening)
    # Average T20 score ~ 160 (run rate ~ 8.0 rpo)
    base_rr = 8.0 / 6.0
    merged["prior"] = merged["balls_left"] * base_rr * np.maximum(0.1, (10 - merged["wkts_before"]) / 10.0)

    # Bayesian smoothing: weight = obs / (obs + 10)
    merged["obs"] = merged["obs"].fillna(0)
    merged["er_empirical"] = merged["er_empirical"].fillna(merged["prior"])
    w = merged["obs"] / (merged["obs"] + 10.0)
    merged["er"] = w * merged["er_empirical"] + (1 - w) * merged["prior"]

    # Boundary conditions: at 0 balls left, ER is 0
    merged.loc[merged["balls_left"] == 0, "er"] = 0.0

    return merged[["grp", "balls_left", "wkts_before", "er"]]

def build_wicket_costs(par_table: pd.DataFrame) -> pd.DataFrame:
    """Compute wicket cost wcost = ER(s) - ER(s with 1 additional wicket)."""
    p = par_table.copy()
    p_next_w = par_table.copy()
    p_next_w["wkts_before"] = p_next_w["wkts_before"] - 1 # join with previous wicket count

    joined = pd.merge(
        p,
        p_next_w,
        on=["grp", "balls_left", "wkts_before"],
        suffixes=("", "_next"),
        how="left"
    )
    # If 9 wickets lost, next is 10 (all out -> ER = 0)
    joined["er_next"] = joined["er_next"].fillna(0.0)
    joined["wcost"] = np.maximum(0.0, joined["er"] - joined["er_next"])

    return joined[["grp", "balls_left", "wkts_before", "wcost"]]
