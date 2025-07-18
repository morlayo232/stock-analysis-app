import numpy as np
import pandas as pd

DEFAULT_FIN = ['PER', 'PBR', 'ROE', '배당수익률']

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except Exception:
        return np.nan

def clean(df: pd.DataFrame, col: str, default=0.0) -> pd.Series:
    """
    df[col] 이 존재하면 숫자로 바꿔 결측치는 default 로,
    없으면 기본값(default) 시리즈를 반환합니다.
    """
    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce").fillna(default)
    else:
        # 없는 컬럼이라면 전체 length 만큼 default 시리즈
        s = pd.Series(default, index=df.index, dtype=float)
    return s

def safe_zscore(arr):
    arr = np.array(arr, dtype=np.float64)
    mean = np.nanmean(arr)
    std = np.nanstd(arr)
    if std == 0 or np.isnan(std):
        return np.zeros_like(arr)
    return (arr - mean) / std

def finalize_scores(df: pd.DataFrame, style="aggressive") -> pd.DataFrame:
    # 1) 모든 DEFAULT_FIN 컬럼을 safe_float → numeric
    for col in DEFAULT_FIN:
        df[col] = df[col].apply(safe_float)

    # 2) z-스코어 계산
    for col in DEFAULT_FIN:
        df[f'z_{col}'] = safe_zscore(df[col])

    # 3) 스타일별 가중합
    if style == "aggressive":
        score = (-df['z_PER']*0.25
                 -df['z_PBR']*0.25
                 +df['z_ROE']*0.35
                 +df['z_배당수익률']*0.15)
    elif style == "stable":
        score = (-df['z_PER']*0.3
                 -df['z_PBR']*0.4
                 +df['z_ROE']*0.2
                 +df['z_배당수익률']*0.1)
    elif style == "dividend":
        score = ( df['z_배당수익률']*0.7
                 -df['z_PBR']*0.2
                 -df['z_PER']*0.1)
    else:
        score = np.zeros(len(df))

    df['score'] = np.where(np.isnan(score), 0, score)

    return df
