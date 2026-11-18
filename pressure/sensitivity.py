"""S8 — Split-Half Reliability & Sensitivity Grid.

Owned by Bhavesh. Zero-conflict with the main pipeline files.

Spec reference: Section 11 of Spec.MD
  - Split-half: split match IDs into halves, compute Spearman correlation of P*.
  - Sensitivity grid: vary pressure cutoff Q, eligibility floors, and
    competition subset; compute robust_count for each player.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from pressure.config import (
    DEFAULT_PRESSURE_QUANTILE,
    LEVERAGE_QUANTILES,
    MIN_PRESSURE_BALLS,
    MIN_PRESSURE_MATCHES,
    SEED,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _shrink_p(p_obs: np.ndarray, n_balls: np.ndarray) -> np.ndarray:
    """Empirical-Bayes shrinkage (same logic as bootstrap module)."""
    if len(p_obs) == 0:
        return np.array([])
    mu = np.average(p_obs, weights=n_balls)
    var_obs = np.average((p_obs - mu) ** 2, weights=n_balls)
    noise_var = np.abs(mu) * 0.5
    mean_inv_n = np.mean(1.0 / np.maximum(n_balls, 1))
    tau2 = max(var_obs - noise_var * mean_inv_n, 1e-12)
    k = noise_var / tau2
    return mu + (n_balls / (n_balls + k)) * (p_obs - mu)


def _aggregate_and_rank(
    df: pd.DataFrame,
    min_balls: int = MIN_PRESSURE_BALLS,
    min_matches: int = MIN_PRESSURE_MATCHES,
) -> pd.DataFrame:
    """Aggregate player-match rows, apply shrinkage, return eligible players with P*.

    Parameters
    ----------
    df : DataFrame with columns [player_id, match_id, p_balls, p_val]

    Returns
    -------
    DataFrame with columns [player_id, p_star, rank]
    """
    agg = df.groupby("player_id").agg(
        total_p_balls=("p_balls", "sum"),
        total_p_val=("p_val", "sum"),
        n_matches=("match_id", "nunique"),
    )
    eligible = agg[
        (agg["total_p_balls"] >= min_balls)
        & (agg["n_matches"] >= min_matches)
    ].copy()

    if eligible.empty:
        return pd.DataFrame(columns=["player_id", "p_star", "rank"])

    p_obs = (eligible["total_p_val"] / eligible["total_p_balls"]).values
    n_b = eligible["total_p_balls"].values
    eligible["p_star"] = _shrink_p(p_obs, n_b)
    eligible["rank"] = eligible["p_star"].rank(ascending=False, method="min").astype(int)
    eligible = eligible.reset_index()
    return eligible[["player_id", "p_star", "rank"]]


# ---------------------------------------------------------------------------
# Public API — Split-Half
# ---------------------------------------------------------------------------

def compute_split_half(
    df_player_match: pd.DataFrame,
    min_balls: int = MIN_PRESSURE_BALLS,
    min_matches: int = MIN_PRESSURE_MATCHES,
) -> pd.DataFrame:
    """Split matches into alternating halves and compute Spearman correlation of P*.

    Parameters
    ----------
    df_player_match : DataFrame
        One row per (player_id, match_id) with columns:
        ``[match_id, player_id, p_balls, p_val, u_balls, u_val]``

    Returns
    -------
    DataFrame with a single row:
        ``[method, n_players, spearman_r, p_value]``
    """
    unique_matches = np.sort(df_player_match["match_id"].unique())
    half_a_matches = unique_matches[0::2]  # even-indexed
    half_b_matches = unique_matches[1::2]  # odd-indexed

    df_a = df_player_match[df_player_match["match_id"].isin(half_a_matches)]
    df_b = df_player_match[df_player_match["match_id"].isin(half_b_matches)]

    rank_a = _aggregate_and_rank(df_a, min_balls=max(min_balls // 2, 1),
                                  min_matches=max(min_matches // 2, 1))
    rank_b = _aggregate_and_rank(df_b, min_balls=max(min_balls // 2, 1),
                                  min_matches=max(min_matches // 2, 1))

    if rank_a.empty or rank_b.empty:
        return pd.DataFrame([{
            "method": "alternating_match_split",
            "n_players": 0,
            "spearman_r": np.nan,
            "p_value": np.nan,
        }])

    merged = rank_a.merge(rank_b, on="player_id", suffixes=("_a", "_b"))

    if len(merged) < 3:
        return pd.DataFrame([{
            "method": "alternating_match_split",
            "n_players": len(merged),
            "spearman_r": np.nan,
            "p_value": np.nan,
        }])

    r, p_val = scipy_stats.spearmanr(merged["p_star_a"], merged["p_star_b"])
    return pd.DataFrame([{
        "method": "alternating_match_split",
        "n_players": len(merged),
        "spearman_r": round(float(r), 4),
        "p_value": round(float(p_val), 6),
    }])


# ---------------------------------------------------------------------------
# Public API — Sensitivity Grid
# ---------------------------------------------------------------------------

# Default variant configuration
DEFAULT_VARIANTS: dict[str, dict[str, Any]] = {
    "baseline": {
        "q": DEFAULT_PRESSURE_QUANTILE,
        "min_balls": MIN_PRESSURE_BALLS,
        "min_matches": MIN_PRESSURE_MATCHES,
        "comp_filter": None,
    },
    "q_067": {
        "q": 0.67,
        "min_balls": MIN_PRESSURE_BALLS,
        "min_matches": MIN_PRESSURE_MATCHES,
        "comp_filter": None,
    },
    "q_080": {
        "q": 0.80,
        "min_balls": MIN_PRESSURE_BALLS,
        "min_matches": MIN_PRESSURE_MATCHES,
        "comp_filter": None,
    },
    "strict_floor": {
        "q": DEFAULT_PRESSURE_QUANTILE,
        "min_balls": int(MIN_PRESSURE_BALLS * 1.5),
        "min_matches": int(MIN_PRESSURE_MATCHES * 1.5),
        "comp_filter": None,
    },
    "loose_floor": {
        "q": DEFAULT_PRESSURE_QUANTILE,
        "min_balls": max(MIN_PRESSURE_BALLS // 2, 10),
        "min_matches": max(MIN_PRESSURE_MATCHES // 2, 2),
        "comp_filter": None,
    },
    "ipl_only": {
        "q": DEFAULT_PRESSURE_QUANTILE,
        "min_balls": MIN_PRESSURE_BALLS,
        "min_matches": MIN_PRESSURE_MATCHES,
        "comp_filter": "ipl",
    },
}


def run_sensitivity_grid(
    df_deliveries_with_leverage: pd.DataFrame,
    variants_config: dict[str, dict[str, Any]] | None = None,
) -> pd.DataFrame:
    """Evaluate ranking stability under varied pressure definitions and floors.

    Parameters
    ----------
    df_deliveries_with_leverage : DataFrame
        Delivery-level data with at least:
        ``[match_id, player_id, p_balls, p_val, leverage, comp_name]``
        (If ``leverage`` is not present, the function falls back to using
        pre-flagged ``p_balls`` / ``p_val`` columns directly.)
    variants_config : dict
        Mapping of variant name → config dict with keys:
        ``q`` (pressure quantile), ``min_balls``, ``min_matches``,
        ``comp_filter`` (None or "ipl").

    Returns
    -------
    DataFrame with columns:
        ``[player_id, variant, rank, in_top10, robust_count]``
        (``robust_count`` added after all variants are run)
    """
    if variants_config is None:
        variants_config = DEFAULT_VARIANTS

    all_variant_results = []

    for variant_name, cfg in variants_config.items():
        df_v = df_deliveries_with_leverage.copy()

        # Competition filter
        if cfg.get("comp_filter") == "ipl" and "comp_name" in df_v.columns:
            df_v = df_v[
                df_v["comp_name"].str.contains("Indian Premier League", case=False, na=False)
            ]

        # If leverage column exists, re-flag pressure based on quantile
        if "leverage" in df_v.columns:
            q_val = cfg.get("q", DEFAULT_PRESSURE_QUANTILE)
            threshold = df_v["leverage"].quantile(q_val)
            df_v["is_pressure"] = df_v["leverage"] >= threshold
            # Recalculate p_balls and p_val based on new threshold
            if "v_bat" in df_v.columns:
                df_v["p_balls"] = df_v["is_pressure"].astype(int)
                df_v["p_val"] = np.where(df_v["is_pressure"], df_v["v_bat"], 0.0)

        # Aggregate to player-match level
        if "player_id" not in df_v.columns:
            continue

        agg_cols = {
            "p_balls": "sum",
            "p_val": "sum",
        }
        # Include match_id for counting
        if "match_id" in df_v.columns:
            df_pm = df_v.groupby(["player_id", "match_id"]).agg(agg_cols).reset_index()
        else:
            continue

        ranked = _aggregate_and_rank(
            df_pm,
            min_balls=cfg.get("min_balls", MIN_PRESSURE_BALLS),
            min_matches=cfg.get("min_matches", MIN_PRESSURE_MATCHES),
        )
        ranked["variant"] = variant_name
        ranked["in_top10"] = (ranked["rank"] <= 10).astype(int)
        all_variant_results.append(ranked)

    if not all_variant_results:
        return pd.DataFrame(
            columns=["player_id", "variant", "rank", "in_top10", "robust_count"]
        )

    df_all = pd.concat(all_variant_results, ignore_index=True)

    # Compute robust_count: number of variants where each player is in top 10
    robust = df_all.groupby("player_id")["in_top10"].sum().reset_index()
    robust.columns = ["player_id", "robust_count"]
    df_all = df_all.merge(robust, on="player_id", how="left")

    return df_all[["player_id", "variant", "p_star", "rank", "in_top10", "robust_count"]]
