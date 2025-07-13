import pandas as pd
from scipy.stats import zscore

# 절대 기준 기반 스코어 계산
def calc_score(fin_df):
    fin_df[['PER', 'PBR', 'ROE']] = fin_df[['PER', 'PBR', 'ROE']].astype(float)

    # z-score 계산
    try:
        fin_df['PER_z'] = zscore(fin_df['PER'])
        fin_df['PBR_z'] = zscore(fin_df['PBR'])
        fin_df['ROE_z'] = zscore(fin_df['ROE'])
    except:
        fin_df['PER_z'] = 0
        fin_df['PBR_z'] = 0
        fin_df['ROE_z'] = 0

    # 종합 투자 점수 계산 (z-score 기반)
    fin_df['score_z'] = -fin_df['PER_z'] - fin_df['PBR_z'] + fin_df['ROE_z']

    # 절대 기준 기반 정량 스코어 (가중치 조정 가능)
    def compute_absolute_score(row):
        per_score = 10 if row['PER'] < 10 else 5 if row['PER'] < 15 else 0
        pbr_score = 10 if row['PBR'] < 1 else 5 if row['PBR'] < 1.5 else 0
        roe_score = 10 if row['ROE'] > 10 else 5 if row['ROE'] > 5 else 0
        return per_score + pbr_score + roe_score

    fin_df['score_abs'] = fin_df.apply(compute_absolute_score, axis=1)

    # 최종 score: 절대 점수와 z-score 기반 점수의 평균
    fin_df['score'] = (fin_df['score_abs'] + fin_df['score_z']) / 2
    return fin_df
