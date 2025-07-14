import numpy as np
from scipy.stats import zscore

DEFAULT_FIN = {
    "PER": 10.0,
    "PBR": 1.0,
    "ROE": 8.0,
    "배당률": 2.0
}

def safe_float(val, default):
    try:
        sval = str(val).replace(',', '').replace('%', '').replace('N/A', '').replace('-', '').replace('\n', '').replace('l', '').strip().upper()
        if sval in ['', 'NONE', 'NAN']:
            return default
        return float(sval)
    except Exception:
        return default

def finalize_scores(df, style="안정형"):
    valid_mask = (df["PER"].notnull()) & (df["PBR"].notnull()) & (df["ROE"].notnull()) & (df["배당률"].notnull())
    df_valid = df[valid_mask].copy()
    for col in ["PER", "PBR", "ROE", "배당률"]:
        df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce')
        df_valid[col] = df_valid[col].replace([np.inf, -np.inf], np.nan)
        df_valid[col] = df_valid[col].fillna(df_valid[col].median())

    df_valid["PER_z"] = -zscore(df_valid["PER"])
    df_valid["PBR_z"] = -zscore(df_valid["PBR"])
    df_valid["ROE_z"] = zscore(df_valid["ROE"])
    df_valid["DIV_z"] = zscore(df_valid["배당률"])

    if style == "공격적":
        weights = {"PER_z": 0.3, "PBR_z": 0.2, "ROE_z": 0.2, "DIV_z": 0.1}
    elif style == "배당형":
        weights = {"PER_z": 0.1, "PBR_z": 0.1, "ROE_z": 0.1, "DIV_z": 0.5}
    else:  # 안정형
        weights = {"PER_z": 0.4, "PBR_z": 0.3, "ROE_z": 0.2, "DIV_z": 0.1}
    df_valid["score"] = (
        weights["PER_z"] * df_valid["PER_z"] +
        weights["PBR_z"] * df_valid["PBR_z"] +
        weights["ROE_z"] * df_valid["ROE_z"] +
        weights["DIV_z"] * df_valid["DIV_z"]
    )
    df_valid["score"] = df_valid["score"].clip(-5, 5)
    df["score"] = np.nan
    df.loc[valid_mask, "score"] = df_valid["score"]
    return df
