# modules/score_utils.py

import numpy as np
import pandas as pd

DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률']

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except Exception:
        return np.nan

def assess_reliability(row):
    count = sum(~np.isnan([row.get(c, np.nan) for c in DEFAULT_FIN]))
    if count >= 5: return 'A'
    elif count >= 4: return 'B'
    else: return 'C'

def finalize_scores(df, style="aggressive"):
    df = df.copy()
    # 결측값 보정
    for c in DEFAULT_FIN:
        if c not in df.columns:
            df[c] = np.nan
    df["PER"] = df["PER"].apply(safe_float)
    df["PBR"] = df["PBR"].apply(safe_float)
    df["EPS"] = df["EPS"].apply(safe_float)
    df["BPS"] = df["BPS"].apply(safe_float)
    df["배당률"] = df["배당률"].apply(safe_float)

    # 급등 신호 계산(예시: 등락률+거래량+최고가갱신)
    df["거래량급증"] = (df["거래량"] / df["거래량평균20"]).replace([np.inf, -np.inf], np.nan)
    df["거래량급증"] = df["거래량급증"].fillna(0)
    df["최고가갱신"] = ((df["현재가"] >= df["현재가"].rolling(60, min_periods=1).max())).astype(int)
    df["등락률"] = ((df["현재가"] - df["현재가"].shift(1)) / df["현재가"].shift(1) * 100).fillna(0)

    # 급등점수: 거래량급증, 등락률, 최고가갱신의 가중평균
    df["급등점수"] = 0.5 * df["거래량급증"].rank(pct=True) + \
                    0.3 * df["등락률"].rank(pct=True) + \
                    0.2 * df["최고가갱신"]

    # 투자성향별 score (예시: 각 항목에 맞게 조합)
    if style == "aggressive":
        df["score"] = (
            0.4 * df["급등점수"].rank(pct=True) +
            0.2 * (1 - df["PER"].rank(pct=True)) +
            0.2 * (1 - df["PBR"].rank(pct=True)) +
            0.2 * df["EPS"].rank(pct=True)
        )
    elif style == "stable":
        df["score"] = (
            0.2 * df["급등점수"].rank(pct=True) +
            0.3 * (1 - df["PER"].rank(pct=True)) +
            0.3 * (1 - df["PBR"].rank(pct=True)) +
            0.2 * df["BPS"].rank(pct=True)
        )
    elif style == "dividend":
        df["score"] = (
            0.1 * df["급등점수"].rank(pct=True) +
            0.3 * df["배당률"].rank(pct=True) +
            0.2 * (1 - df["PER"].rank(pct=True)) +
            0.4 * df["EPS"].rank(pct=True)
        )
    else:
        df["score"] = 0
    return df
