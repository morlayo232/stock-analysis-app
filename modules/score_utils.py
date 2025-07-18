import numpy as np
import pandas as pd

FIELD_EXPLAIN = {
    "PER":      "주가수익비율(PER), 낮을수록 저평가",
    "PBR":      "주가순자산비율(PBR), 1 미만 저평가",
    "EPS":      "주당순이익(EPS)",
    "BPS":      "주당순자산(BPS)",
    "배당률":   "연간 배당수익률(%)",
    "score":    "최종 투자매력점수",
    "급등확률": "단기 급등 신호 확률 (0~1)",
}

def finalize_scores(df, style="aggressive"):
    def clean(col, default=0):
        s = pd.to_numeric(df.get(col, default), errors="coerce").fillna(default)
        return s.mask(s < 0, 0)

    w = {
        "aggressive": [-0.3, -0.2, 0.2, 0.1, 0.15, 0.1],
        "stable":     [-0.2, -0.3, 0.1, 0.2, 0.1, 0.1],
        "dividend":   [-0.15,-0.1, 0.05,0.05,0.4,0.1]
    }[style]

    per   = clean("PER",       20)
    pbr   = clean("PBR",       2)
    eps   = clean("EPS",       0)
    bps   = clean("BPS",       0)
    divi  = clean("배당률",     0)
    vol   = clean("거래량",     0)
    vol20 = clean("거래량평균20", max(vol.mean(),1))

    # 투자매력점수
    score = (
        w[0]*per +
        w[1]*pbr +
        w[2]*(eps/1e4) +
        w[3]*(bps/1e4) +
        w[4]*divi +
        w[5]*np.log1p(vol)
    )
    df["score"] = score

    # 급등확률
    volatility = (clean("고가",0) - clean("저가",0)) / clean("현재가",1)
    jump = (
        0.4 * np.clip((vol/vol20)-1, 0, 5) +
        0.3 * (per<8).astype(float) +
        0.2 * volatility
    )
    df["급등확률"] = jump

    return df

def assess_reliability(row):
    cnt = sum(pd.notna([row.get(k) for k in ["PER","PBR","EPS","BPS","배당률"]]))
    return "A" if cnt>=5 else "B" if cnt>=4 else "C"
