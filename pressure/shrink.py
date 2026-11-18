"""Empirical-Bayes shrinkage and dip filter for pressure performance."""
from pathlib import Path
from typing import Tuple, Dict
import pandas as pd
import numpy as np

def compute_empirical_bayes_shrinkage(
    player_agg: pd.DataFrame,
    min_balls: int = 50,
    min_matches: int = 5,
    out_dir: Path = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Shrink observed P toward league mean: P* = mu + (n / (n + k)) * (P_obs - mu).
    
    k = sigma2_noise / sigma2_true estimated via method of moments.
    """
    df = player_agg.copy()
    params_records = []
    shrunk_parts = []

    for role in ["bat", "bowl"]:
        sub = df[df["role"] == role].copy()
        
        # Qualified subset for estimating hyper-parameters
        qual = sub[(sub["p_balls"] >= min_balls) & (sub["p_matches_count"] >= min_matches)]
        if len(qual) < 3:
            # Fallback if too few qualified
            qual = sub[sub["p_balls"] >= 20]
        if len(qual) < 2:
            qual = sub

        # League mean mu
        mu = float(qual["P_obs"].mean()) if len(qual) > 0 else 0.0

        # Variance of sample means (Var_obs)
        var_obs = float(qual["P_obs"].var()) if len(qual) > 1 else 100.0

        # Typical sampling noise variance sigma2_noise:
        # P_obs is in runs per 100 balls. Single ball variance ~ 1.5 runs -> 150 per 100 balls.
        # sigma2_noise_i approx sigma2_ball / n_i * 100^2
        # Average sampling noise variance across qualified players
        typical_n = float(qual["p_balls"].median()) if len(qual) > 0 else 50.0
        sigma2_noise = 15000.0 / max(1.0, typical_n)

        # sigma2_true = max(1e-4, var_obs - sigma2_noise)
        sigma2_true = max(1.0, var_obs - sigma2_noise)
        k = sigma2_noise / sigma2_true

        # Warning logic for extreme k
        k_warning = False
        if k < 5 or k > 500:
            k_warning = True
            print(f"WARNING: Shrinkage parameter k={k:.2f} for role={role} is outside typical [5, 500] range.")

        # Shrinkage factor per player: w = n / (n + k)
        sub["mu"] = mu
        sub["k"] = k
        sub["shrinkage_w"] = sub["p_balls"] / (sub["p_balls"] + k)
        sub["P_star"] = mu + sub["shrinkage_w"] * (sub["P_obs"] - mu)

        # Dip filter metric: z-score of (P_star - U_obs)
        # Delta = P_star - U_obs
        sub["Delta_star"] = sub["P_star"] - sub["U_obs"]
        sub_std = float(sub["Delta_star"].std()) if sub["Delta_star"].std() > 0 else 1.0
        sub["dip_z"] = (sub["Delta_star"] - sub["Delta_star"].mean()) / sub_std
        
        # Dip filter: pass if not severely negative (e.g. Delta_star not in bottom 10% or dip_z > -1.5)
        sub["passes_dip"] = sub["dip_z"] > -1.5

        params_records.append({
            "role": role,
            "qualified_count": len(qual),
            "mu": mu,
            "var_obs": var_obs,
            "sigma2_noise": sigma2_noise,
            "sigma2_true": sigma2_true,
            "k": k,
            "k_warning": k_warning
        })
        shrunk_parts.append(sub)

    df_shrunk = pd.concat(shrunk_parts, ignore_index=True)
    df_params = pd.DataFrame(params_records)

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        df_params.to_csv(out_dir / "shrinkage_params.csv", index=False)

    return df_shrunk, df_params
