# modules/score_utils.py
import numpy as np
import pandas as pd

FIELD_EXPLAIN = {
    "PER": "주가수익비율, 낮을수록 저평가",
    "PBR": "주가순자산비율, 1 미만이 저평가 가능",
    "EPS": "주당순이익",
    "BPS": "주당순자산",
    "배당률": "연간 배당수익률(%)",
    "score": "최종 투자매력점수",
    "급등확률": "단기 급등 신호(0~1)",
}

def _safe_series(s, df, default=0):
    # s가 Series가 아니면 (ex. int) df와 같은 index로 Series 생성
    if isinstance(s, pd.Series):
        return s
    return pd.Series([default]*len(df), index=df.index)

def finalize_scores(df, style="aggressive"):
    def clean(s, default=0):
        s = _safe_series(s, df, default)
        s = pd.to_numeric(s, errors="coerce").fillna(default)
        s = s.mask(s < 0, 0)
        return s

    w = {
        "aggressive": [-0.3, -0.2, 0.2, 0.1, 0.15, 0.1],
        "stable":     [-0.2, -0.3, 0.1, 0.2, 0.1, 0.1],
        "dividend":   [-0.15, -0.1, 0.05, 0.05, 0.4, 0.1]
    }.get(style, [-0.3, -0.2, 0.2, 0.1, 0.15, 0.1])

    df["score"] = (
        w[0]*clean(df.get("PER", 20), 20)
        + w[1]*clean(df.get("PBR", 2), 2)
        + w[2]*clean(df.get("EPS", 0), 0)/1e4
        + w[3]*clean(df.get("BPS", 0), 0)/1e4
        + w[4]*clean(df.get("배당률", 0), 0)
        + w[5]*np.log1p(clean(df.get("거래량", 0), 0))
    )

    거래량 = clean(df.get("거래량", 0), 0)
    거래량평균 = clean(df.get("거래량평균20", 0), max(거래량.mean(), 1))
    per = clean(df.get("PER", 20), 20)
    변동성 = (
        clean(df.get("고가", 0), 0) - clean(df.get("저가", 0), 0)
    ) / clean(df.get("현재가", 1), 1)
    df["급등확률"] = (
        0.4 * np.clip((거래량/거래량평균)-1, 0, 5)
        + 0.3 * (per < 8)
        + 0.2 * 변동성
    )
    return df

def assess_reliability(row):
    filled = sum(pd.notna([row.get(k, None) for k in ["PER", "PBR", "EPS", "BPS", "배당률"]]))
    if filled >= 5: return "A"
    elif filled >= 4: return "B"
    else: return "C"
