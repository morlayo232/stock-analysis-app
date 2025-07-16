# modules/score_utils.py

import numpy as np
import pandas as pd

def finalize_scores(df, style="aggressive"):
    df = df.copy()

    # 안전 변환(결측, 음수, 문자 포함 가능)
    def safe_numeric(col, default=0):
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").fillna(default)
            return s
        else:
            return pd.Series([default]*len(df), index=df.index)

    PER = safe_numeric("PER")
    PBR = safe_numeric("PBR")
    EPS = safe_numeric("EPS")
    BPS = safe_numeric("BPS", 1)  # 0으로 두면 분모 문제 발생
    배당률 = safe_numeric("배당률")

    if "거래량" in df.columns:
        거래량 = safe_numeric("거래량")
        거래량[거래량 < 0] = 0
        거래량_log = np.log1p(거래량)
    else:
        거래량_log = pd.Series([0]*len(df), index=df.index)

    # 점수 예시 (필요시 조합 가중치 조정)
    df["score"] = (
        -0.1 * PER
        -0.2 * PBR
        +0.2 * (EPS / (BPS + 1))
        +0.05 * 배당률
        +0.1 * 거래량_log
    )
    return df

def assess_reliability(row):
    vals = [row.get(x, np.nan) for x in ["PER", "PBR", "EPS", "BPS", "배당률"]]
    missing = sum(pd.isna(vals))
    if missing == 0:
        return "A"
    elif missing <= 1:
        return "B"
    else:
        return "C"
