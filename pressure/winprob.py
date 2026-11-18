"""Win probability models with odd/even match cross-fitting."""
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from pressure.config import SEED

def fit_predict_winprob(df_deliveries: pd.DataFrame) -> pd.DataFrame:
    """Fit win probability models on odd/even match splits and predict WP per delivery.
    
    Innings 1 features: balls_left, score_before, wkts_before
    Innings 2 features: balls_left, rn (required runs), wkts_before
    """
    df = df_deliveries.copy()
    
    # Target: Did the batting team win the match?
    inn2 = df[df["innings"] == 2]
    inn2_max_score = inn2.groupby("match_id").apply(lambda g: (g["score_before"] + g["total"]).iloc[-1], include_groups=False).to_dict()
    inn2_target = inn2.groupby("match_id")["target"].first().to_dict()
    
    # Batting team won:
    bat_won_map = {}
    for mid in df["match_id"].unique():
        if mid in inn2_max_score and mid in inn2_target:
            chaser_won = inn2_max_score[mid] >= inn2_target[mid]
            bat_won_map[(mid, 2)] = 1 if chaser_won else 0
            bat_won_map[(mid, 1)] = 0 if chaser_won else 1
        else:
            bat_won_map[(mid, 1)] = 1
            bat_won_map[(mid, 2)] = 0

    df["bat_won"] = [bat_won_map.get((m, inn), 0) for m, inn in zip(df["match_id"], df["innings"])]

    # Cross-fitting split: odd vs even match_id
    is_odd = (df["match_id"] % 2) != 0
    df["wp"] = np.nan

    # Fit Innings 1
    feats_inn1 = ["balls_left", "score_before", "wkts_before"]
    inn1_mask = df["innings"] == 1

    # Fit on even, predict on odd
    m1_even = LogisticRegression(random_state=SEED, max_iter=200)
    train_1_even = df[inn1_mask & (~is_odd)]
    if len(train_1_even) > 0 and train_1_even["bat_won"].nunique() > 1:
        m1_even.fit(train_1_even[feats_inn1], train_1_even["bat_won"])
        test_1_odd = df[inn1_mask & is_odd]
        if len(test_1_odd) > 0:
            df.loc[inn1_mask & is_odd, "wp"] = m1_even.predict_proba(test_1_odd[feats_inn1])[:, 1]
    
    # Fit on odd, predict on even
    m1_odd = LogisticRegression(random_state=SEED, max_iter=200)
    train_1_odd = df[inn1_mask & is_odd]
    if len(train_1_odd) > 0 and train_1_odd["bat_won"].nunique() > 1:
        m1_odd.fit(train_1_odd[feats_inn1], train_1_odd["bat_won"])
        test_1_even = df[inn1_mask & (~is_odd)]
        if len(test_1_even) > 0:
            df.loc[inn1_mask & (~is_odd), "wp"] = m1_odd.predict_proba(test_1_even[feats_inn1])[:, 1]

    # Fit Innings 2
    feats_inn2 = ["balls_left", "rn", "wkts_before"]
    inn2_mask = df["innings"] == 2

    # Fit on even, predict on odd
    m2_even = LogisticRegression(random_state=SEED, max_iter=200)
    train_2_even = df[inn2_mask & (~is_odd)]
    if len(train_2_even) > 0 and train_2_even["bat_won"].nunique() > 1:
        m2_even.fit(train_2_even[feats_inn2], train_2_even["bat_won"])
        test_2_odd = df[inn2_mask & is_odd]
        if len(test_2_odd) > 0:
            df.loc[inn2_mask & is_odd, "wp"] = m2_even.predict_proba(test_2_odd[feats_inn2])[:, 1]

    # Fit on odd, predict on even
    m2_odd = LogisticRegression(random_state=SEED, max_iter=200)
    train_2_odd = df[inn2_mask & is_odd]
    if len(train_2_odd) > 0 and train_2_odd["bat_won"].nunique() > 1:
        m2_odd.fit(train_2_odd[feats_inn2], train_2_odd["bat_won"])
        test_2_even = df[inn2_mask & (~is_odd)]
        if len(test_2_even) > 0:
            df.loc[inn2_mask & (~is_odd), "wp"] = m2_odd.predict_proba(test_2_even[feats_inn2])[:, 1]

    # Fallback for boundary / unpredicted cases
    df["wp"] = df["wp"].fillna(0.5).clip(0.001, 0.999)

    return df
