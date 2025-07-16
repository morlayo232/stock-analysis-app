# modules/score_utils.py

import numpy as np
import pandas as pd

def finalize_scores(df, style="aggressive"):
    df = df.copy()
    N = len(df)
    idx = range(N)  # 항상 0~N-1의 안전한 인덱스

    def safe_numeric(col, default=0):
        if col in df.columns:
            s = df[col]
        else:
            s = pd.Series([default]*N, index=idx)
        if s is None or isinstance(s, list):
            s = pd.Series([default]*N, index=idx)
        # 문자/NaN 모두 0으로
        s = pd.to_numeric(s, errors="coerce").fillna(default)
        s = s.astype(float)
        s[s < 0] = 0
        return s.reset_index(drop=True)  # 인덱스 꼬임 완전방지

    PER = safe_numeric("PER")
    PBR = safe_numeric("PBR")
    EPS = safe_numeric("EPS")
    BPS = safe_numeric("BPS", 1)
    배당률 = safe_numeric("배당률")
    거래량 = safe_numeric("거래량")

    거래량_log = np.log1p(거래량)

    # 결과도 인덱스 맞추기
    df = df.reset_index(drop=True)
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
