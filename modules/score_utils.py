import numpy as np
import pandas as pd

def safe_float(x):
    try:
        return float(str(x).replace(",", "").replace("%",""))
    except:
        return np.nan

def safe_zscore(arr):
    a = np.array(arr, dtype=float)
    m,s = np.nanmean(a), np.nanstd(a)
    if s==0 or np.isnan(s):
        return np.zeros_like(a)
    return (a-m)/s

def finalize_scores(df, style="aggressive"):
    # 기본 지표
    for col in ["PER","PBR","배당수익률"]:
        df[col] = df[col].apply(safe_float)
    for col in ["PER","PBR","배당수익률"]:
        df[f"z_{col}"] = safe_zscore(df[col])

    # 스타일별 가중치
    W = {
        "aggressive": {"PER":-0.3, "PBR":-0.2, "배당수익률":0.15},
        "stable":     {"PER":-0.25,"PBR":-0.35,"배당수익률":0.10},
        "dividend":   {"PER":-0.1, "PBR":-0.1, "배당수익률":0.7 },
    }.get(style, {})
    score = np.zeros(len(df))
    for k,w in W.items():
        score += w * df[f"z_{k}"]
    df["score"] = np.where(np.isnan(score), 0, score)

    # 급등확률: 거래량 급증 + 저PER + 단기 변동성
    vol = pd.to_numeric(df.get("거래량", 0), errors="coerce").fillna(0)
    vol20 = pd.to_numeric(df.get("거래량평균20",1), errors="coerce").fillna(1)
    per = df["PER"].fillna(1e9)
    high = pd.to_numeric(df.get("고가",0), errors="coerce").fillna(0)
    low  = pd.to_numeric(df.get("저가",0), errors="coerce").fillna(0)
    last = pd.to_numeric(df.get("현재가",1), errors="coerce").fillna(1)
    volatility = (high - low) / last
    df["급등확률"] = (
        0.4 * np.clip((vol/vol20)-1, 0, 5) +
        0.3 * (per < 8).astype(float) +
        0.3 * volatility
    )
    return df

def assess_reliability(row):
    # PER, PBR, 배당수익률 중 채워진 개수로 판단
    filled = sum(pd.notna([row.PER, row.PBR, row.배당수익률]))
    if filled == 3: return "A"
    if filled == 2: return "B"
    return "C"

# 툴팁
FIELD_EXPLAIN = {
    "PER":"주가수익비율 (낮을수록 저평가)",
    "PBR":"주가순자산비율 (1 미만 저평가 가능)",
    "배당수익률":"연간 배당수익률 (%)",
    "score":"최종 투자매력 점수",
    "급등확률":"단기 급등 신호 (0~?)",
}
