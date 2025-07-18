# modules/score_utils.py
import numpy as np
import pandas as pd

# 이제 PER, PBR, EPS, BPS, 배당률 만 사용
DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률']

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except:
        return np.nan

def safe_zscore(arr):
    a = np.array(arr, dtype=np.float64)
    m = np.nanmean(a)
    s = np.nanstd(a)
    if s == 0 or np.isnan(s):
        return np.zeros_like(a)
    return (a - m) / s

def finalize_scores(df: pd.DataFrame, style="aggressive") -> pd.DataFrame:
    # 1) 숫자 변환
    for col in DEFAULT_FIN:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)
        else:
            df[col] = np.nan

    # 2) z-score 생성
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    # 3) 스타일별 가중합 (예시 가중치 — 필요시 조정)
    if style == "aggressive":
        # 공격형: 수익(EPS), 가치(PER,PBR), 배당은 소폭
        score = (
              df['z_EPS'] * 0.4
            - df['z_PER'] * 0.2
            - df['z_PBR'] * 0.2
            + df['z_배당률'] * 0.2
        )
    elif style == "stable":
        # 안정형: 가치 지표 비중 ↑
        score = (
              df['z_EPS'] * 0.2
            - df['z_PER'] * 0.3
            - df['z_PBR'] * 0.3
            + df['z_배당률'] * 0.2
        )
    elif style == "dividend":
        # 배당형: 배당률 최우선
        score = (
              df['z_배당률'] * 0.6
            - df['z_PBR'] * 0.2
            - df['z_PER'] * 0.2
        )
    else:
        score = np.zeros(len(df))

    # 4) NaN → 0
    df['score'] = np.where(np.isnan(score), 0, score)
    return df
