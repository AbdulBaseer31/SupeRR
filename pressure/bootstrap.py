"""S7 — Match-Level Bootstrap for rank intervals and top-10 probabilities.

Owned by Bhavesh. Zero-conflict with the main pipeline files.

Spec reference: Section 10 of Spec.MD
  - Resample matches with replacement B=1000 times.
  - Recompute shrunk P* each time.
  - Report rank interval [P10, P90] and top-10 probability per player.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pressure.config import (
    BOOTSTRAP_ROUNDS,
    MIN_PRESSURE_BALLS,
    MIN_PRESSURE_MATCHES,
    SEED,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _empirical_bayes_shrink(
    p_obs: np.ndarray,
    n_balls: np.ndarray,
) -> np.ndarray:
    """Apply empirical-Bayes shrinkage: P* = mu + (n / (n + k)) * (P_obs - mu).

    Parameters
    ----------
    p_obs : array of raw pressure performance per player
    n_balls : array of pressure balls per player

    Returns
    -------
    p_star : array of shrunk P* values
    """
    mu = np.average(p_obs, weights=n_balls)

    # Method-of-moments estimate of k = sigma2_noise / sigma2_true
    # sigma2_noise ≈ pooled within-player variance proxy (use mu*(1-mu/100))
    # sigma2_true  ≈ Var(P_obs) - E[sigma2_noise / n]
    var_obs = np.average((p_obs - mu) ** 2, weights=n_balls)
    noise_var = np.abs(mu) * 0.5  # reasonable proxy for per-ball variance
    mean_inv_n = np.mean(1.0 / np.maximum(n_balls, 1))
    tau2 = max(var_obs - noise_var * mean_inv_n, 1e-12)
    k = noise_var / tau2

    p_star = mu + (n_balls / (n_balls + k)) * (p_obs - mu)
    return p_star


def _aggregate_one_resample(
    player_ids: np.ndarray,
    match_ids: np.ndarray,
    p_balls: np.ndarray,
    p_val: np.ndarray,
    u_balls: np.ndarray,
    u_val: np.ndarray,
    resampled_match_ids: np.ndarray,
    min_balls: int,
    min_matches: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate a single bootstrap resample and return (player_ids_eligible, ranks).

    Returns player_ids (sorted by P* descending) and corresponding ranks.
    """
    # Build a mask for rows whose match_id is in the resample
    # Use searchsorted for speed: resampled_match_ids is already sorted
    unique_matches = np.unique(resampled_match_ids)
    mask = np.isin(match_ids, unique_matches)

    # Count how many times each match was drawn (for weighting)
    match_counts = pd.Series(resampled_match_ids).value_counts()

    # Subset to resampled rows, with match-level weights
    s_player = player_ids[mask]
    s_match = match_ids[mask]
    s_p_balls = p_balls[mask]
    s_p_val = p_val[mask]

    # Multiply by how many times each match was drawn
    weights = match_counts.reindex(s_match).values.astype(float)
    s_p_balls_w = s_p_balls * weights
    s_p_val_w = s_p_val * weights

    # Aggregate per player
    df_tmp = pd.DataFrame({
        "player_id": s_player,
        "p_balls_w": s_p_balls_w,
        "p_val_w": s_p_val_w,
        "match_id": s_match,
    })
    agg = df_tmp.groupby("player_id").agg(
        total_p_balls=("p_balls_w", "sum"),
        total_p_val=("p_val_w", "sum"),
        n_matches=("match_id", "nunique"),
    )

    # Eligibility filter
    eligible = agg[
        (agg["total_p_balls"] >= min_balls)
        & (agg["n_matches"] >= min_matches)
    ].copy()

    if len(eligible) == 0:
        return np.array([], dtype=int), np.array([], dtype=int)

    p_obs = (eligible["total_p_val"] / eligible["total_p_balls"]).values
    n_b = eligible["total_p_balls"].values
    p_star = _empirical_bayes_shrink(p_obs, n_b)

    # Rank: 1 = best (highest P* for batters, context-dependent)
    order = np.argsort(-p_star)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(order) + 1)

    return eligible.index.values, ranks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_match_bootstrap(
    df_player_match: pd.DataFrame,
    n_rounds: int = BOOTSTRAP_ROUNDS,
    seed: int = SEED,
    min_balls: int = MIN_PRESSURE_BALLS,
    min_matches: int = MIN_PRESSURE_MATCHES,
) -> pd.DataFrame:
    """Resample unique match_ids with replacement B times and recompute P*.

    Parameters
    ----------
    df_player_match : DataFrame
        Pre-aggregated to one row per (player_id, match_id) with columns:
        ``[match_id, player_id, role, p_balls, p_val, u_balls, u_val]``
    n_rounds : int
        Number of bootstrap resamples (default 1000).
    seed : int
        Random seed for reproducibility.
    min_balls : int
        Minimum pressure balls for eligibility.
    min_matches : int
        Minimum distinct pressure matches for eligibility.

    Returns
    -------
    DataFrame with columns:
        ``[player_id, top10_prob, rank_p10, rank_median, rank_p90]``
    """
    rng = np.random.default_rng(seed)

    required_cols = {"match_id", "player_id", "p_balls", "p_val", "u_balls", "u_val"}
    missing = required_cols - set(df_player_match.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Pre-extract numpy arrays for speed
    player_ids = df_player_match["player_id"].values
    match_ids = df_player_match["match_id"].values
    p_balls = df_player_match["p_balls"].values.astype(float)
    p_val = df_player_match["p_val"].values.astype(float)
    u_balls = df_player_match["u_balls"].values.astype(float)
    u_val = df_player_match["u_val"].values.astype(float)

    unique_matches = np.unique(match_ids)
    n_matches_total = len(unique_matches)

    # Collect ranks across resamples
    all_ranks: dict[int, list[int]] = {}

    for _ in range(n_rounds):
        resampled = rng.choice(unique_matches, size=n_matches_total, replace=True)

        eligible_ids, ranks = _aggregate_one_resample(
            player_ids, match_ids, p_balls, p_val, u_balls, u_val,
            resampled, min_balls, min_matches,
        )

        for pid, rank in zip(eligible_ids, ranks):
            all_ranks.setdefault(pid, []).append(int(rank))

    # Build results
    results = []
    for pid, rank_list in all_ranks.items():
        arr = np.array(rank_list)
        top10_prob = float(np.mean(arr <= 10))
        rank_p10 = int(np.percentile(arr, 10))
        rank_median = int(np.median(arr))
        rank_p90 = int(np.percentile(arr, 90))
        results.append({
            "player_id": pid,
            "top10_prob": round(top10_prob, 4),
            "rank_p10": rank_p10,
            "rank_median": rank_median,
            "rank_p90": rank_p90,
        })

    df_result = pd.DataFrame(results)
    if df_result.empty:
        df_result = pd.DataFrame(
            columns=["player_id", "top10_prob", "rank_p10", "rank_median", "rank_p90"]
        )

    return df_result.sort_values("rank_median").reset_index(drop=True)
