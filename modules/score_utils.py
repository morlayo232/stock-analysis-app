# modules/score_utils.py

import numpy as np
import pandas as pd

def finalize_scores(df, style="aggressive"):
    # 기존 지표에 거래량, 볼린저, 신호 등 가중치 추가 예시
    df = df.copy()
    df["score"] = (
        -0.1 * df["PER"].astype(float)
        -0.2 * df["PBR"].astype(float)
        +0.2 * df["EPS"].astype(float) / (df["BPS"].astype(float)+1)
        +0.05 * df["배당률"].astype(float)
        +0.1 * np.log1p(df.get("거래량", 0))
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
