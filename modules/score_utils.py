# modules/score_utils.py

import numpy as np
import pandas as pd

# 1) 기본 재무/수급 컬럼: ROE 대신 거래량평균20 이용
DEFAULT_FIN = ['PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량평균20']

# 2) 툴팁 설명
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
    """문자열 → float, 실패시 NaN"""
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except:
        return np.nan

def safe_zscore(arr):
    """NaN을 무시한 Z-Score 계산 (std=0일 땐 0 반환)"""
    a = np.array(arr, dtype=np.float64)
    m, s = np.nanmean(a), np.nanstd(a)
    if s == 0 or np.isnan(s):
        return np.zeros_like(a)
    return (a - m) / s

def assess_reliability(row):
    """간단 신뢰등급 예시: 결측치 비율로 A/B/C 판정"""
    miss = sum(pd.isna(row[col]) for col in DEFAULT_FIN)
    pct = miss / len(DEFAULT_FIN)
    if pct == 0:
        return 'A'
    if pct < 0.3:
        return 'B'
    return 'C'

def finalize_scores(df: pd.DataFrame, style: str = "aggressive") -> pd.DataFrame:
    """
    style ∈ {'aggressive','stable','dividend'}:
      - aggressive: 수익·수급↑ 가중
      - stable: 밸류·안정↑ 가중
      - dividend: 배당↑ 가중
    """
    # 1) 숫자 변환
    for col in DEFAULT_FIN:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)
        else:
            df[col] = np.nan

    # 2) Z-Score 열 추가
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    # 3) 스타일별 가중합
    if style == "aggressive":
        # PER↓·PBR↓·EPS↑·BPS↑·배당↑·수급(거래량평균20)↑
        score = (
            -0.2 * df['z_PER']
            -0.2 * df['z_PBR']
            +0.25 * df['z_EPS']
            +0.25 * df['z_BPS']
            +0.05 * df['z_배당률']
            +0.15 * df['z_거래량평균20']
        )
    elif style == "stable":
        # 밸류 안정형: PER·PBR ↓↑, 배당·수급 약간 반영
        score = (
            -0.3 * df['z_PER']
            -0.3 * df['z_PBR']
            +0.1 * df['z_EPS']
            +0.1 * df['z_BPS']
            +0.1 * df['z_배당률']
            +0.1 * df['z_거래량평균20']
        )
    elif style == "dividend":
        # 배당형: 배당↑ 중심, 수급·저PBR 보조
        score = (
            +0.6 * df['z_배당률']
            -0.1 * df['z_PER']
            -0.1 * df['z_PBR']
            +0.1 * df['z_거래량평균20']
        )
    else:
        score = np.zeros(len(df))

    # 4) NaN → 0, 결과 반영
    df['score'] = np.where(np.isnan(score), 0, score)

    # 5) 단기 급등확률(예시: 저PER·거래량 급증 반영)
    # 여기서는 단순히 z_PER·z_거래량평균20 합산 예시
    df['급등확률'] = df['z_거래량평균20'] - df['z_PER']

    return df
