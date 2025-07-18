import numpy as np
import pandas as pd

# KRX에서 제공되는 주요 재무지표
DEFAULT_FIN = ['PER', 'PBR', '배당수익률']

def safe_float(val):
    """문자열 포함 숫자 → float, 실패 시 NaN"""
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except:
        return np.nan

def safe_zscore(arr: pd.Series):
    """Z-스코어 표준화 (NaN 제외), 분산 0일 땐 0 반환"""
    a = np.array(arr, dtype=float)
    m, s = np.nanmean(a), np.nanstd(a)
    if s == 0 or np.isnan(s):
        return np.zeros_like(a)
    return (a - m) / s

def finalize_scores(df: pd.DataFrame, style: str = "aggressive") -> pd.DataFrame:
    """
    df에 'PER','PBR','배당수익률','거래량','고가','저가' 컬럼이 있어야 함.
    style: aggressive / stable / dividend
    """
    # 재무데이터 정제
    for col in DEFAULT_FIN:
        if col in df:
            df[col] = df[col].apply(safe_float)
        else:
            df[col] = np.nan

    # Z-스코어 추가
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    # 거래량, 변동성 정제
    df['거래량'] = df.get('거래량', 0).apply(lambda x: safe_float(x))
    df['거래량평균20'] = df.get('거래량평균20', df['거래량']).apply(lambda x: safe_float(x))
    # 단기변동성 = (고가-저가)/종가
    df['고가'] = df.get('고가', 0).apply(lambda x: safe_float(x))
    df['저가'] = df.get('저가', 0).apply(lambda x: safe_float(x))
    df['현재가'] = df.get('현재가', 1).apply(lambda x: safe_float(x))
    vol = (df['고가'] - df['저가']) / df['현재가']

    # 기본 가중치 (재무 + 수급 반영)
    w = {
        "aggressive": [-0.25, -0.25, +0.15, +0.30],  # (PER, PBR, 배당률, 거래량 모멘텀)
        "stable":     [-0.30, -0.40, +0.10, +0.20],
        "dividend":   [-0.10, -0.20, +0.70, +0.20],
    }.get(style, [-0.25, -0.25, +0.15, +0.30])

    mom = np.log1p(df['거래량'] / df['거래량평균20'])  # 거래량 모멘텀

    # 투자매력점수 계산
    score = (
        w[0] * df['z_PER'] +
        w[1] * df['z_PBR'] +
        w[2] * df['z_배당수익률'] +
        w[3] * mom
    )
    df['score'] = np.nan_to_num(score, nan=0.0)

    # 급등예상확률 계산 (0~1로 정규화)
    jump = 0.4 * np.clip(mom, 0, None) + 0.3 * (df['z_PER'] < -1) + 0.3 * vol
    # 0~1 범위로 스케일링
    df['급등확률'] = np.clip(jump / np.nanpercentile(jump, 98), 0, 1)

    return df

# 재무정보 신뢰등급
def assess_reliability(row: pd.Series) -> str:
    present = sum(pd.notna(row.get(col)) for col in DEFAULT_FIN)
    return 'A' if present == 3 else 'B' if present == 2 else 'C'

# 툴팁 설명
FIELD_EXPLAIN = {
    "PER": "주가수익비율(P/E), 낮을수록 저평가",
    "PBR": "주가순자산비율(P/B), 1 미만 저평가",
    "배당수익률": "연간 배당수익률(%)",
    "score": "투자매력점수 (재무+수급 가중합)",
    "급등확률": "단기 급등 예측 확률 (0~1)",
}
