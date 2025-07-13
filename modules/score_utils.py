# modules/score_utils.py
import pandas as pd
from scipy.stats import zscore

def calc_base_score(df):
    df[['PER', 'PBR', 'ROE']] = df[['PER', 'PBR', 'ROE']].astype(float)
    
    # 이상치 제거 (zscore 계산 안정화)
    df = df[(df['PER'] > 0) & (df['PBR'] > 0) & (df['ROE'] > 0)]
    df['PER_z'] = zscore(df['PER'])
    df['PBR_z'] = zscore(df['PBR'])
    df['ROE_z'] = zscore(df['ROE'])

    # 기본 점수 계산
    df['base_score'] = -df['PER_z'] - df['PBR_z'] + df['ROE_z']
    return df

def apply_style_weight(df, style):
    weight = {
        '공격적': {'기술점수': 0.4, '세력점수': 0.3, 'base_score': 0.3},
        '안정적': {'base_score': 0.6, '기술점수': 0.2, '세력점수': 0.2},
        '배당형': {'base_score': 0.4, '배당률': 0.4, '세력점수': 0.2}
    }

    df['score'] = 0.0
    for key, w in weight[style].items():
        df[key] = pd.to_numeric(df[key], errors='coerce').fillna(0)
        df['score'] += df[key] * w

    return df
