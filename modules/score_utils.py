import numpy as np
import pandas as pd

FIELD_EXPLAIN = {
    "PER":"주가수익비율, 낮을수록 저평가",
    "PBR":"주가순자산비율, 1 미만이 저평가 가능",
    "EPS":"주당순이익",
    "BPS":"주당순자산",
    "배당률":"연간 배당수익률(%)",
    "score":"최종 투자매력점수",
    "급등확률":"단기 급등 신호(0~1)",
}

def finalize_scores(df, style="aggressive"):
    def safe_col(col, default=0):
        # 항상 Series로 반환 (결측/없으면 0으로 채움)
        return df[col] if col in df.columns else pd.Series([default]*len(df), index=df.index)
    def clean(s, default=0):
        s = pd.to_numeric(s, errors="coerce").fillna(default)
        s = s.mask(s < 0, 0)
        return s
    # style별 가중치
    w = {
        "aggressive": [-0.3,-0.2,0.2,0.1,0.15,0.1],
        "stable":     [-0.2,-0.3,0.1,0.2,0.1,0.1],
        "dividend":   [-0.15,-0.1,0.05,0.05,0.4,0.1]
    }.get(style, [-0.3,-0.2,0.2,0.1,0.15,0.1])

    df["score"] = (
        w[0]*clean(safe_col("PER", 20), 20)
        + w[1]*clean(safe_col("PBR", 2), 2)
        + w[2]*clean(safe_col("EPS", 0), 0)/1e4
        + w[3]*clean(safe_col("BPS", 0), 0)/1e4
        + w[4]*clean(safe_col("배당률", 0), 0)
        + w[5]*np.log1p(clean(safe_col("거래량", 0), 0))
    )

    거래량 = clean(safe_col("거래량", 0), 0)
    거래량평균 = clean(safe_col("거래량평균20", 0), max(거래량.mean(),1))
    per = clean(safe_col("PER", 20), 20)
    변동성 = (clean(safe_col("고가", 0), 0) - clean(safe_col("저가", 0), 0)) / clean(safe_col("현재가", 1), 1)
    df["급등확률"] = (
        0.4*np.clip((거래량/거래량평균)-1,0,5)
        + 0.3*(per<8)
        + 0.2*변동성
    )
    return df

def assess_reliability(row):
    filled = sum(pd.notna([row.get(k,None) for k in ["PER","PBR","EPS","BPS","배당률"]]))
    if filled >= 5: return "A"
    elif filled >= 4: return "B"
    else: return "C"
