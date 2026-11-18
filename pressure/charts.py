"""S9 — Report Charts & Visualizations.

Owned by Bhavesh. Zero-conflict with the main pipeline files.

Spec reference: Section 12a of Spec.MD
  - Chart 1: Leverage distribution with pressure threshold cutoff Q.
  - Chart 2: Validation exhibit — Pressure vs Ordinary delivery distributions.
  - Chart 3: Batter Finalists — Shrunk P* with [P10, P90] bootstrap rank intervals.
  - Chart 4: Bowler Finalists — Shrunk P* with [P10, P90] bootstrap rank intervals.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pressure.config import DEFAULT_PRESSURE_QUANTILE


# ---------------------------------------------------------------------------
# Chart style constants (no magic numbers)
# ---------------------------------------------------------------------------
FIGURE_SIZE = (10, 6)
BAR_WIDTH = 0.35
TOP_N_FINALISTS = 10
TITLE_FONTSIZE = 14
LABEL_FONTSIZE = 12
TICK_FONTSIZE = 10
COLORS = {
    "pressure": "#d62728",
    "ordinary": "#1f77b4",
    "batter": "#2ca02c",
    "bowler": "#ff7f0e",
    "threshold": "#7f7f7f",
}


# ---------------------------------------------------------------------------
# Chart 1 — Leverage Distribution
# ---------------------------------------------------------------------------

def chart_leverage_distribution(
    df_leverage: pd.DataFrame,
    out_path: Path,
    q: float = DEFAULT_PRESSURE_QUANTILE,
) -> Path:
    """Plot leverage distribution with pressure threshold cutoffs.

    Parameters
    ----------
    df_leverage : DataFrame with column ``leverage``
    out_path : file path for the output PNG
    q : quantile used for the pressure cutoff line

    Returns
    -------
    Path to the saved PNG
    """
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    leverage_values = df_leverage["leverage"].dropna()
    threshold = leverage_values.quantile(q)

    ax.hist(leverage_values, bins=80, color=COLORS["ordinary"],
            edgecolor="white", alpha=0.75, label="Leverage values")
    ax.axvline(threshold, color=COLORS["threshold"], linewidth=2,
               linestyle="--", label=f"Pressure cutoff (Q={q:.0%}): {threshold:.3f}")

    ax.set_xlabel("Leverage", fontsize=LABEL_FONTSIZE)
    ax.set_ylabel("Frequency", fontsize=LABEL_FONTSIZE)
    ax.set_title("Leverage Distribution & Pressure Threshold", fontsize=TITLE_FONTSIZE)
    ax.legend(fontsize=TICK_FONTSIZE)
    ax.tick_params(labelsize=TICK_FONTSIZE)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Chart 2 — Validation Exhibit (Pressure vs Ordinary)
# ---------------------------------------------------------------------------

def chart_validation_exhibit(
    df_validation: pd.DataFrame,
    out_path: Path,
) -> Path:
    """Plot pressure vs ordinary delivery distributions by phase.

    Parameters
    ----------
    df_validation : DataFrame with columns:
        ``[phase, group, dot_pct, boundary_pct, wicket_pct]``
        where ``group`` is 'pressure' or 'ordinary'.
    out_path : file path for the output PNG

    Returns
    -------
    Path to the saved PNG
    """
    metrics = ["dot_pct", "boundary_pct", "wicket_pct"]
    metric_labels = ["Dot %", "Boundary %", "Wicket %"]
    phases = df_validation["phase"].unique()

    fig, axes = plt.subplots(1, len(metrics), figsize=(14, 5), sharey=False)
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric, label in zip(axes, metrics, metric_labels):
        pressure_vals = []
        ordinary_vals = []
        phase_labels = []

        for phase in phases:
            phase_data = df_validation[df_validation["phase"] == phase]
            p_row = phase_data[phase_data["group"] == "pressure"]
            o_row = phase_data[phase_data["group"] == "ordinary"]

            pressure_vals.append(p_row[metric].values[0] if len(p_row) > 0 else 0)
            ordinary_vals.append(o_row[metric].values[0] if len(o_row) > 0 else 0)
            phase_labels.append(phase)

        x = np.arange(len(phase_labels))
        ax.bar(x - BAR_WIDTH / 2, pressure_vals, BAR_WIDTH,
               label="Pressure", color=COLORS["pressure"], alpha=0.85)
        ax.bar(x + BAR_WIDTH / 2, ordinary_vals, BAR_WIDTH,
               label="Ordinary", color=COLORS["ordinary"], alpha=0.85)

        ax.set_xlabel("Phase", fontsize=LABEL_FONTSIZE)
        ax.set_ylabel(label, fontsize=LABEL_FONTSIZE)
        ax.set_title(label, fontsize=TITLE_FONTSIZE)
        ax.set_xticks(x)
        ax.set_xticklabels(phase_labels, fontsize=TICK_FONTSIZE)
        ax.legend(fontsize=TICK_FONTSIZE - 1)
        ax.tick_params(labelsize=TICK_FONTSIZE)

    fig.suptitle("Validation: Pressure vs Ordinary Deliveries by Phase",
                 fontsize=TITLE_FONTSIZE, y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Charts 3 & 4 — Finalist rank intervals
# ---------------------------------------------------------------------------

def _chart_finalist_intervals(
    df_ranked: pd.DataFrame,
    out_path: Path,
    role_label: str,
    color: str,
    top_n: int = TOP_N_FINALISTS,
) -> Path:
    """Plot shrunk P* point estimates with [P10, P90] rank intervals.

    Parameters
    ----------
    df_ranked : DataFrame with columns:
        ``[player_name, p_star, rank_p10, rank_median, rank_p90]``
    out_path : file path for the output PNG
    role_label : "Batter" or "Bowler"
    color : bar/marker color
    top_n : how many finalists to show

    Returns
    -------
    Path to the saved PNG
    """
    df = df_ranked.head(top_n).copy()
    if df.empty:
        # Create a blank chart if no data
        fig, ax = plt.subplots(figsize=FIGURE_SIZE)
        ax.text(0.5, 0.5, f"No {role_label} finalists available",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=LABEL_FONTSIZE)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Left panel: P* point estimates ---
    names = df["player_name"].values
    p_star = df["p_star"].values
    y_pos = np.arange(len(names))

    ax1.barh(y_pos, p_star, color=color, alpha=0.8, edgecolor="white")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=TICK_FONTSIZE)
    ax1.invert_yaxis()
    ax1.set_xlabel("Shrunk P*", fontsize=LABEL_FONTSIZE)
    ax1.set_title(f"Top {top_n} {role_label}s — P*", fontsize=TITLE_FONTSIZE)
    ax1.tick_params(labelsize=TICK_FONTSIZE)

    # --- Right panel: Rank intervals ---
    if "rank_p10" in df.columns and "rank_p90" in df.columns:
        rank_lo = df["rank_p10"].values
        rank_hi = df["rank_p90"].values
        rank_med = df["rank_median"].values if "rank_median" in df.columns else (
            (rank_lo + rank_hi) / 2
        )

        ax2.hlines(y_pos, rank_lo, rank_hi, color=color, linewidth=3, alpha=0.6)
        ax2.scatter(rank_med, y_pos, color=color, s=60, zorder=5, label="Median rank")
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(names, fontsize=TICK_FONTSIZE)
        ax2.invert_yaxis()
        ax2.set_xlabel("Bootstrap Rank Interval [P10, P90]", fontsize=LABEL_FONTSIZE)
        ax2.set_title(f"Top {top_n} {role_label}s — Rank Intervals",
                      fontsize=TITLE_FONTSIZE)
        ax2.legend(fontsize=TICK_FONTSIZE)
        ax2.tick_params(labelsize=TICK_FONTSIZE)
    else:
        ax2.text(0.5, 0.5, "No bootstrap intervals available",
                 transform=ax2.transAxes, ha="center", va="center",
                 fontsize=LABEL_FONTSIZE)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def chart_batter_finalists(
    df_batters: pd.DataFrame,
    out_path: Path,
    top_n: int = TOP_N_FINALISTS,
) -> Path:
    """Chart 3: Batter finalists with P* and rank intervals."""
    return _chart_finalist_intervals(df_batters, out_path, "Batter",
                                      COLORS["batter"], top_n)


def chart_bowler_finalists(
    df_bowlers: pd.DataFrame,
    out_path: Path,
    top_n: int = TOP_N_FINALISTS,
) -> Path:
    """Chart 4: Bowler finalists with P* and rank intervals."""
    return _chart_finalist_intervals(df_bowlers, out_path, "Bowler",
                                      COLORS["bowler"], top_n)


# ---------------------------------------------------------------------------
# Convenience: generate all 4 charts at once
# ---------------------------------------------------------------------------

def generate_all_charts(
    df_leverage: pd.DataFrame,
    df_validation: pd.DataFrame,
    df_batters: pd.DataFrame,
    df_bowlers: pd.DataFrame,
    out_dir: Path,
    q: float = DEFAULT_PRESSURE_QUANTILE,
) -> dict[str, Path]:
    """Generate all four report charts and return a dict of name → file path.

    Parameters
    ----------
    df_leverage : DataFrame with ``leverage`` column
    df_validation : DataFrame with ``[phase, group, dot_pct, boundary_pct, wicket_pct]``
    df_batters : ranked batters DataFrame
    df_bowlers : ranked bowlers DataFrame
    out_dir : directory to save PNGs
    q : pressure quantile for Chart 1

    Returns
    -------
    dict mapping chart name to saved file path
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    paths["leverage_distribution"] = chart_leverage_distribution(
        df_leverage, out_dir / "leverage_distribution.png", q=q
    )
    paths["validation_exhibit"] = chart_validation_exhibit(
        df_validation, out_dir / "validation_exhibit.png"
    )
    paths["batter_finalists"] = chart_batter_finalists(
        df_batters, out_dir / "batter_finalists.png"
    )
    paths["bowler_finalists"] = chart_bowler_finalists(
        df_bowlers, out_dir / "bowler_finalists.png"
    )

    return paths
