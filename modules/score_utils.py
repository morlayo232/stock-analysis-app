import numpy as np
import pandas as pd

# KRX에서 가져올 수 있는 지표만 사용하며, ROE는 취득 불가로 제외했습니다.
DEFAULT_FIELDS = ['PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량', '거래량평균20', '고가', '저가']

def clean_series(s, default=0.0):
    """숫자로 변환, 음수 및 NaN을 default로 대체"""
    return pd.to_numeric(s, errors='coerce').fillna(default).clip(lower=0)

def finalize_scores(df: pd.DataFrame, style: str = 'aggressive') -> pd.DataFrame:
    """
    - df에 반드시: PER, PBR, EPS, BPS, 배당률, 거래량, 거래량평균20, 고가, 저가 컬럼 있어야 합니다.
    - style: 'aggressive', 'stable', 'dividend' 중 선택
    """
    # 1) 기본 클린업
    for f in DEFAULT_FIELDS:
        df[f] = clean_series(df.get(f, default=0.0))

    # 2) 투자매력 점수 계산 (금융권 실제 가중치 참고 예시)
    weights = {
        'aggressive': {'PER': -0.3, 'PBR': -0.2, 'EPS': 0.25, 'BPS': 0.15, '배당률': 0.05, '거래량': 0.05},
        'stable':     {'PER': -0.25,'PBR': -0.25,'EPS': 0.15, 'BPS': 0.15, '배당률': 0.15, '거래량': 0.05},
        'dividend':   {'PER': -0.1, 'PBR': -0.1, 'EPS': 0.1,  'BPS': 0.1,  '배당률': 0.5,  '거래량': 0.1},
    }[style]

    df['score'] = (
        weights['PER'] * df['PER'] +
        weights['PBR'] * df['PBR'] +
        weights['EPS'] * (df['EPS'] / 1e4) +
        weights['BPS'] * (df['BPS'] / 1e4) +
        weights['배당률'] * df['배당률'] +
        weights['거래량'] * np.log1p(df['거래량'])
    )

    # 3) 급등 확률 계산 (거래량 급증, 저 PER, 단기 변동성 반영)
    vol_ratio = df['거래량'] / df['거래량평균20'].replace(0, np.nan)
    volatility = (df['고가'] - df['저가']) / df['현재가'].replace(0, np.nan)
    df['급등확률'] = (
        0.5 * np.clip(vol_ratio - 1, 0, 5) +
        0.3 * (df['PER'] < 8).astype(float) +
        0.2 * volatility.fillna(0)
    )

    # 4) NaN은 0으로
    df['score']     = df['score'].fillna(0)
    df['급등확률'] = df['급등확률'].fillna(0)

    return df

def assess_reliability(row: pd.Series) -> str:
    """필수 지표 결측 개수에 따른 신뢰등급(A,B,C)"""
    filled = sum(pd.notna([row[f] for f in ['PER','PBR','EPS','BPS','배당률']]))
    if filled >= 5:
        return 'A'
    elif filled >= 4:
        return 'B'
    else:
        return 'C'

FIELD_EXPLAIN = {
    "PER": "주가수익비율: 낮을수록 저평가",
    "PBR": "주가순자산비율: 1 이하 저평가",
    "EPS": "주당순이익",
    "BPS": "주당순자산",
    "배당률": "연간 배당수익률(%)",
    "score": "투자매력점수",
    "급등확률": "단기 급등 예상 확률(0~?)",
}
