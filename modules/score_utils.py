# modules/score_utils.py

import numpy as np
import pandas as pd

def finalize_scores(df, style="aggressive"):
    df = df.copy()
    # "거래량" 결측·음수·문자 예외처리
    if "거래량" in df.columns:
        거래량 = pd.to_numeric(df["거래량"], errors="coerce").fillna(0)
        거래량[거래량 < 0] = 0
        거래량_log = np.log1p(거래량)
    else:
        거래량_log = 0

    df["score"] = (
        -0.1 * pd.to_numeric(df.get("PER", 0), errors="coerce").fillna(0)
        -0.2 * pd.to_numeric(df.get("PBR", 0), errors="coerce").fillna(0)
        +0.2 * pd.to_numeric(df.get("EPS", 0), errors="coerce").fillna(0) / (pd.to_numeric(df.get("BPS", 1), errors="coerce").fillna(1) + 1)
        +0.05 * pd.to_numeric(df.get("배당률", 0), errors="coerce").fillna(0)
        +0.1 * 거래량_log
    )
    return df

def assess_reliability(row):
    # 결측/신뢰등급 평가(간단화)
    vals = [row.get(x, np.nan) for x in ["PER", "PBR", "EPS", "BPS", "배당률"]]
    missing = sum(pd.isna(vals))
    if missing == 0:
        return "A"
    elif missing <= 1:
        return "B"
    else:
        return "C"
