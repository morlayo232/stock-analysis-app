import numpy as np
import pandas as pd

# 기본 재무/수급 컬럼: ROE 빼고 거래량평균20 추가
DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량평균20']

# 툴팁 설명
FIELD_EXPLAIN = {
    'PER': "주가수익비율: 낮을수록 실적 대비 저평가",
    'PBR': "주가순자산비율: 1 미만이면 자산 대비 저평가",
    'EPS': "주당순이익: 기업의 이익성장성 지표",
    'BPS': "주당순자산: 회계장부상의 순자산 가치",
    '배당률': "배당수익률: 배당투자 매력도",
    '거래량평균20': "20일 평균 거래량: 수급 흐름 지표",
    'score': "종합 투자매력 점수",
    '급등확률': "단기 급등 가능성(수급·변동성 반영)"
}

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except:
        return np.nan

def safe_zscore(arr):
    a = np.array(arr, dtype=np.float64)
    m, s = np.nanmean(a), np.nanstd(a)
    if s == 0 or np.isnan(s):
        return np.zeros_like(a)
    return (a - m) / s

def assess_reliability(row):
    miss = sum(pd.isna(row[col]) for col in DEFAULT_FIN)
    pct = miss / len(DEFAULT_FIN)
    return 'A' if pct == 0 else 'B' if pct < 0.3 else 'C'

def finalize_scores(df: pd.DataFrame, style: str = "aggressive") -> pd.DataFrame:
    # 1) 필수 컬럼 숫자로 변환
    for col in DEFAULT_FIN:
        df[col] = df.get(col, np.nan)
        df[col] = df[col].apply(safe_float)

    # 2) Z-Score 열 추가
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    # 3) 스타일별 가중합
    if style == "aggressive":
        score = (
            -0.2 * df['z_PER']
            -0.2 * df['z_PBR']
            +0.25 * df['z_EPS']
            +0.25 * df['z_BPS']
            +0.05 * df['z_배당률']
            +0.15 * df['z_거래량평균20']
        )
    elif style == "stable":
        score = (
            -0.3 * df['z_PER']
            -0.3 * df['z_PBR']
            +0.1 * df['z_EPS']
            +0.1 * df['z_BPS']
            +0.1 * df['z_배당률']
            +0.1 * df['z_거래량평균20']
        )
    elif style == "dividend":
        score = (
            +0.6 * df['z_배당률']
            -0.1 * df['z_PER']
            -0.1 * df['z_PBR']
            +0.1 * df['z_거래량평균20']
        )
    else:
        score = np.zeros(len(df))

    df['score'] = np.where(np.isnan(score), 0, score)

    # 4) 단기 급등확률: 단순 예시 (거래량↑, 저PER↑)
    df['급등확률'] = df['z_거래량평균20'] - df['z_PER']

    return df
