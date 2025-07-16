# modules/score_utils.py

import numpy as np
import pandas as pd

DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률']

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
    if count >= 5:
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

    # 급등점수 z점수
    if "급등점수" in df.columns:
        df['z_급등점수'] = safe_zscore(df["급등점수"])
    else:
        df['z_급등점수'] = 0

    if style == "aggressive":
        score = (
            -df['z_PER'] * 0.15 +
            -df['z_PBR'] * 0.15 +
            df['z_EPS'] * 0.15 +
            df['z_BPS'] * 0.10 +
            df['z_배당률'] * 0.10 +
            df['z_급등점수'] * 0.20 +
            df['z_EPS'] * 0.15  # 성장성 추가 비중
        )
    elif style == "stable":
        score = (
            -df['z_PER'] * 0.15 +
            -df['z_PBR'] * 0.25 +
            df['z_BPS'] * 0.20 +
            df['z_배당률'] * 0.20 +
            df['z_급등점수'] * 0.10 +
            df['z_EPS'] * 0.10
        )
    elif style == "dividend":
        score = (
            df['z_배당률'] * 0.40 +
            -df['z_PBR'] * 0.15 +
            -df['z_PER'] * 0.10 +
            df['z_BPS'] * 0.10 +
            df['z_급등점수'] * 0.10 +
            df['z_EPS'] * 0.15
        )
    else:
        score = np.zeros(len(df))

    score = np.where(np.isnan(score), 0, score)
    df['score'] = score
    return df
