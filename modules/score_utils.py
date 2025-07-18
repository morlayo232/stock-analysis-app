# modules/score_utils.py

import numpy as np
import pandas as pd

# — 재무 필드 및 설명(툴팁) —
DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률']
FIELD_EXPLAIN = {
    'PER': '주가수익비율: 주가÷주당순이익, 이익 대비 주가 수준',
    'PBR': '주가순자산비율: 주가÷주당순자산, 자산 대비 평가',
    'EPS': '주당순이익: 순이익÷발행주식수, 수익성 지표',
    'BPS': '주당순자산: 자산총액÷발행주식수, 안전마진 지표',
    '배당률': '배당수익률: 주당배당금÷주가, 현금수익 비중',
    'score': '투자매력 점수: 재무·가치·배당 반영 가중합',
    '급등확률': '단기 급등 예측 확률: 거래량·저PER·변동성 등 반영'
}

def safe_float(val):
    try:
        return float(str(val).replace(',', '').replace('%',''))
    except:
        return np.nan

def safe_zscore(arr):
    a = np.array(arr, dtype=np.float64)
    m = np.nanmean(a)
    s = np.nanstd(a)
    if s == 0 or np.isnan(s):
        return np.zeros_like(a)
    return (a - m) / s

def finalize_scores(df: pd.DataFrame, style: str = "aggressive") -> pd.DataFrame:
    # 1) 숫자 변환
    for col in DEFAULT_FIN:
        df[col] = df.get(col, np.nan).apply(safe_float)

    # 2) z-score 생성
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    # 3) 스타일별 가중합
    if style == "aggressive":
        score = (
              df['z_EPS'] * 0.4
            - df['z_PER'] * 0.2
            - df['z_PBR'] * 0.2
            + df['z_배당률'] * 0.2
        )
    elif style == "stable":
        score = (
              df['z_EPS'] * 0.2
            - df['z_PER'] * 0.3
            - df['z_PBR'] * 0.3
            + df['z_배당률'] * 0.2
        )
    elif style == "dividend":
        score = (
              df['z_배당률'] * 0.6
            - df['z_PBR'] * 0.2
            - df['z_PER'] * 0.2
        )
    else:
        score = np.zeros(len(df))

    df['score'] = np.where(np.isnan(score), 0, score)
    return df

def assess_reliability(row: pd.Series) -> str:
    na_count = sum(pd.isna(row.get(c)) for c in DEFAULT_FIN)
    if na_count <= 1:
        return 'A'
    elif na_count <= 3:
        return 'B'
    else:
        return 'C'
