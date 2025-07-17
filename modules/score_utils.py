import numpy as np
import pandas as pd

# 용어설명
FIELD_EXPLAIN = {
    "PER":"주가수익비율, 낮을수록 저평가",
    "PBR":"주가순자산비율, 1 미만이 저평가 가능",
    "EPS":"주당순이익",
    "BPS":"주당순자산",
    "배당률":"연간 배당수익률(%)",
    "점수":"최종 투자매력점수",
}

def finalize_scores(df):
    # 결측치/이상치 보정 및 score, 급등확률 산출
    def clean(s, default=0):
        s = pd.to_numeric(s, errors="coerce").fillna(default)
        s = s.mask(s < 0, 0)
        return s
    # 점수 공식(예시: 실전 최적화 필요)
    df["score"] = (
        -0.3*clean(df.get("PER",0),20)
        -0.2*clean(df.get("PBR",0),2)
        +0.2*clean(df.get("EPS",0),0)/1e4
        +0.1*clean(df.get("BPS",0),0)/1e4
        +0.15*clean(df.get("배당률",0),0)
        +0.1*np.log1p(clean(df.get("거래량",0),0))
    )
    # 급등확률(간이: 거래량 증가, 저PER, 단기 변동성 등)
    거래량 = clean(df.get("거래량",0),0)
    거래량평균 = clean(df.get("거래량평균20",0),거래량.mean())
    per = clean(df.get("PER",0),20)
    변동성 = (clean(df.get("고가",0),0) - clean(df.get("저가",0),0)) / clean(df.get("현재가",1),1)
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
