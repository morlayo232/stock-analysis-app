import numpy as np
import pandas as pd
from scipy.stats import zscore

def finalize_scores(df, style="안정형"):
    fin_cols = ["PER", "PBR", "ROE", "배당률"]
    for col in fin_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    valid_mask = df[fin_cols].notnull().all(axis=1)
    df_valid = df[valid_mask].copy()
    df_valid["PER_z"] = -zscore(df_valid["PER"])
    df_valid["PBR_z"] = -zscore(df_valid["PBR"])
    df_valid["ROE_z"] = zscore(df_valid["ROE"])
    df_valid["DIV_z"] = zscore(df_valid["배당률"])
    if style == "공격적":
        weights = {"PER_z": 0.32, "PBR_z": 0.17, "ROE_z": 0.31, "DIV_z": 0.2}
    elif style == "배당형":
        weights = {"PER_z": 0.08, "PBR_z": 0.07, "ROE_z": 0.18, "DIV_z": 0.67}
    else:  # 안정형
        weights = {"PER_z": 0.35, "PBR_z": 0.28, "ROE_z": 0.31, "DIV_z": 0.06}
    df_valid["score"] = (
        weights["PER_z"] * df_valid["PER_z"] +
        weights["PBR_z"] * df_valid["PBR_z"] +
        weights["ROE_z"] * df_valid["ROE_z"] +
        weights["DIV_z"] * df_valid["DIV_z"]
    ).clip(-5, 5)
    df["score"] = np.nan
    df.loc[valid_mask, "score"] = df_valid["score"]
    return df
