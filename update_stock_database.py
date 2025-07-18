import pandas as pd
import numpy as np
from datetime import datetime
from modules.score_utils import finalize_scores

def fetch_krx_data(code):
    # TODO: 실제 KRX/API 로직으로 교체
    return {
        "현재가":       np.random.randint(1000, 50000),
        "PER":         np.random.uniform(5, 20),
        "PBR":         np.random.uniform(0.5, 3),
        "EPS":         np.random.randint(100, 50000),
        "BPS":         np.random.randint(1000, 50000),
        "배당률":      np.random.uniform(0, 5),
        "거래량":      np.random.randint(1000, 100000),
        "거래량평균20": np.random.randint(1000, 100000),
        "고가":         np.random.randint(2000, 60000),
        "저가":         np.random.randint(500, 30000),
    }

def update_database():
    df0 = pd.read_csv("initial_krx_list_test.csv", dtype=str)
    records = []
    for _, r in df0.iterrows():
        d = fetch_krx_data(r["종목코드"])
        rec = {
            "종목명":   r["종목명"],
            "종목코드": r["종목코드"].zfill(6),
            "갱신일":   datetime.now().strftime("%Y-%m-%d %H:%M"),
            **d
        }
        records.append(rec)
    if not records:
        print("데이터 수집 실패")
        return
    df = pd.DataFrame(records)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 생성 완료")

def update_single_stock(code):
    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    idx = df.index[df["종목코드"]==code]
    if idx.empty:
        print("해당 종목 없음"); return
    d = fetch_krx_data(code)
    for k,v in d.items(): df.at[idx[0], k] = v
    df.at[idx[0], "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("개별 갱신 완료")
