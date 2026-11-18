"""Leverage calculation, pressure flags, leverage distribution, and validation exhibit."""
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd

from pressure.config import LEVERAGE_QUANTILES, DEFAULT_PRESSURE_QUANTILE

def compute_leverage_and_flags(
    df_wp: pd.DataFrame,
    out_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute per-delivery leverage L_t, pressure flags, validation exhibits, and distribution."""
    df = df_wp.copy()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Phase-based outcome probabilities P(outcome | phase)
    # Outcomes: dot (runs==0, no wkt), single (1), two (2), three (3), four (4), six (6), wkt (is_wkt)
    outcomes = ["dot", "1", "2", "3", "4", "6", "wicket"]
    
    # Categorize actual delivery outcomes
    conds = [
        df["team_wicket"],
        df["total"] == 0,
        df["total"] == 1,
        df["total"] == 2,
        df["total"] == 3,
        df["total"] == 4,
        df["total"] == 6,
    ]
    choices = ["wicket", "dot", "1", "2", "3", "4", "6"]
    df["ball_outcome"] = np.select(conds, choices, default="1")

    # Phase-level outcome distributions
    phase_probs = df.groupby("phase")["ball_outcome"].value_counts(normalize=True).unstack(fill_value=0.01)

    # Leverage L_t approximation from WP sensitivity:
    # L_t = sum_o P(o | phase) * |WP(s + o) - WP(s)|
    # In Innings 2: WP is sensitive to required run rate rn / (balls_left / 6) and wickets
    # A delivery can swing WP proportional to 1 / sqrt(balls_left + 1) and closeness of WP to 0.5
    # Standard leverage metric: WP * (1 - WP) / sqrt(balls_left / 6 + 0.1)
    # Higher when game is 50-50 and fewer balls remain.
    balls_left_overs = np.maximum(0.1, df["balls_left"] / 6.0)
    closeness = df["wp"] * (1.0 - df["wp"])
    
    # Innings 2 has significantly sharper swing than Innings 1
    inn_scale = np.where(df["innings"] == 2, 1.2, 0.8)
    df["leverage"] = (closeness / np.sqrt(balls_left_overs)) * inn_scale

    # Pressure flags across quantiles within innings type
    for q in LEVERAGE_QUANTILES:
        col = f"is_pressure_q{int(q*100)}"
        q_val_inn1 = df[df["innings"] == 1]["leverage"].quantile(q)
        q_val_inn2 = df[df["innings"] == 2]["leverage"].quantile(q)
        df[col] = (
            ((df["innings"] == 1) & (df["leverage"] >= q_val_inn1)) |
            ((df["innings"] == 2) & (df["leverage"] >= q_val_inn2))
        )

    # Primary pressure flag
    default_q_col = f"is_pressure_q{int(DEFAULT_PRESSURE_QUANTILE*100)}"
    df["is_pressure"] = df[default_q_col]

    # Rule-based cross-check pressure flag:
    # Inn 2: balls_left <= 30 and rn / (balls_left/6) >= 9.0 (high RRR death chase)
    # or Inn 1/2: wkts_before >= 4 in powerplay/middle (collapse)
    req_rate = np.where(df["balls_left"] > 0, df["rn"] / (df["balls_left"] / 6.0), 0)
    chase_pressure = (df["innings"] == 2) & (df["balls_left"] <= 36) & (req_rate >= 8.5)
    collapse_pressure = (df["ov"] < 10) & (df["wkts_before"] >= 3)
    df["is_pressure_rule"] = chase_pressure | collapse_pressure

    # Validation Exhibit: Compare pressure vs ordinary within phase (Dot %, Boundary %, Wicket %, RPB)
    df["is_dot"] = (df["total"] == 0) & (~df["team_wicket"])
    df["is_boundary"] = df["bat_runs"].isin([4, 6])
    
    val_rows = []
    for phase in ["powerplay", "middle", "death"]:
        sub_phase = df[df["phase"] == phase]
        for p_flag in [False, True]:
            sub = sub_phase[sub_phase["is_pressure"] == p_flag]
            n = len(sub)
            if n > 0:
                val_rows.append({
                    "phase": phase,
                    "situation": "pressure" if p_flag else "ordinary",
                    "ball_count": n,
                    "dot_pct": float(sub["is_dot"].mean()),
                    "boundary_pct": float(sub["is_boundary"].mean()),
                    "wicket_pct": float(sub["team_wicket"].mean()),
                    "runs_per_ball": float(sub["total"].mean()),
                })
    df_val_exhibit = pd.DataFrame(val_rows)
    df_val_exhibit.to_csv(out_dir / "validation_pressure_vs_ordinary.csv", index=False)

    # Leverage Distribution summary
    lev_dist = df.groupby(["innings", "phase"])["leverage"].describe().reset_index()
    lev_dist.to_csv(out_dir / "leverage_distribution.csv", index=False)

    return df, df_val_exhibit, lev_dist
