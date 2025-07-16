# modules/score_utils.py

import numpy as np
import pandas as pd

def finalize_scores(df, style="aggressive"):
    df = df.copy()
    N = len(df)

    def safe_numeric(col, default=0):
        # 없는 컬럼 → 0, None, '' 모두 0으로
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            # None → 0
            s = s.fillna(default)
            # 무한대/음수도 0으로
            s = s.replace([np.inf, -np.inf], 0)
            s = s.mask(s < 0, 0)
            return s
        else:
            return pd.Series([default]*N, index=df.index)

    PER = safe_numeric("PER")
    PBR = safe_numeric("PBR")
    EPS = safe_numeric("EPS")
    BPS = safe_numeric("BPS", 1)
    배당률 = safe_numeric("배당률")

    거래량 = safe_numeric("거래량")
    거래량_log = np.log1p(거래량)

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
