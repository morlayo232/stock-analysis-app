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
    # 결측치 및 이상치 보정
    for col in ["PER", "PBR", "ROE", "배당률"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        df[col] = df[col].fillna(df[col].median())

    # z-score 표준화
    df["PER_z"] = -zscore(df["PER"])
    df["PBR_z"] = -zscore(df["PBR"])
    df["ROE_z"] = zscore(df["ROE"])
    df["DIV_z"] = zscore(df["배당률"])

    # 안정형 가중치 (필요시 style별 커스텀 가능)
    weights = {"PER_z": 0.4, "PBR_z": 0.3, "ROE_z": 0.2, "DIV_z": 0.1}
    df["score"] = (
        weights["PER_z"] * df["PER_z"] +
        weights["PBR_z"] * df["PBR_z"] +
        weights["ROE_z"] * df["ROE_z"] +
        weights["DIV_z"] * df["DIV_z"]
    )
    # 점수 clipping (극단치 방지)
    df["score"] = df["score"].clip(-5, 5)
    return df
