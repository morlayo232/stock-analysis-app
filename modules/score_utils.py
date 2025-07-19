# modules/score_utils.py

import numpy as np
import pandas as pd

DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률', '거래대금']

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except Exception:
        return np.nan

def safe_zscore(arr):
    arr = np.array(arr, dtype=np.float64)
    mean = np.nanmean(arr)
    std = np.nanstd(arr)
    if std == 0 or np.isnan(std):
        return np.zeros_like(arr)
    return (arr - mean) / std

def assess_reliability(row):
    count = sum(~np.isnan([row.get(c, np.nan) for c in DEFAULT_FIN]))
    if count >= 6:
        return 'A'
    elif count >= 4:
        return 'B'
    else:
        return 'C'

def finalize_scores(df, style="aggressive"):
    for col in DEFAULT_FIN:
        df[col] = df[col].apply(safe_float)
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    if style == "aggressive":
        score = (
            -df['z_PER'] * 0.25
            -df['z_PBR'] * 0.2
            +df['z_EPS'] * 0.2
            +df['z_BPS'] * 0.1
            +df['z_배당률'] * 0.1
            +df['z_거래대금'] * 0.15
        )
        score += np.where(df['EPS'] > 0, 0.1, -0.1)
    elif style == "stable":
        score = (
            -df['z_PER'] * 0.3
            -df['z_PBR'] * 0.35
            +df['z_BPS'] * 0.2
            +df['z_배당률'] * 0.1
            +df['z_거래대금'] * 0.05
        )
        score += np.where(df['BPS'] > df['BPS'].median(), 0.1, 0)
    elif style == "dividend":
        score = (
            df['z_배당률'] * 0.7
            -df['z_PBR'] * 0.15
            -df['z_PER'] * 0.1
            +df['z_거래대금'] * 0.05
        )
        score += np.where(df['배당률'] >= 3, 0.15, 0)
    else:
        score = np.zeros(len(df))

    score = np.where(np.isnan(score), 0, score)
    df['score'] = score
    return df
