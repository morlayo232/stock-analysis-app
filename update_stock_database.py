# update_stock_database.py

import os
import pandas as pd
import numpy as np
import time
from datetime import datetime
from modules.score_utils import finalize_scores

# 실제 KRX/API 로직으로 대체할 함수 자리
def fetch_krx_data(code):
    try:
        # TODO: 실제 수집 로직
        return {
            "현재가": np.random.randint(1000, 50000),
            "PER":     np.random.uniform(5, 20),
            "PBR":     np.random.uniform(0.5, 3),
            "EPS":     np.random.randint(100, 50000),
            "BPS":     np.random.randint(1000, 50000),
            "배당률":  np.random.uniform(0, 5),
            "거래량":  np.random.randint(1000, 100000),
            "거래량평균20": np.random.randint(1000, 100000),
            "고가":     np.random.randint(2000, 60000),
            "저가":     np.random.randint(500, 30000),
        }
    except:
        return None

def update_database():
    CSV = "initial_krx_list_test.csv"
    df0 = pd.read_csv(CSV, dtype=str)
    all_data = []
    for i, r in df0.iterrows():
        data = fetch_krx_data(r["종목코드"])
        if data is None:
            continue
        record = {
            "종목명":   r["종목명"],
            "종목코드": r["종목코드"].zfill(6),
            "갱신일":   datetime.now().strftime("%Y-%m-%d %H:%M"),
            **data
        }
        all_data.append(record)
        print(f"\r{i+1}/{len(df0)} 업데이트", end="")
    if not all_data:
        print("데이터 수집 실패. 파일 미생성")
        return
    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("\nfiltered_stocks.csv 생성 완료")

def update_single_stock(code):
    # CSV 위치 고정
    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    idx = df.index[df["종목코드"]==code]
    if len(idx)==0:
        print("해당 종목 없음")
        return
    data = fetch_krx_data(code)
    if data is None:
        print("수집 실패")
        return
    for k,v in data.items():
        df.at[idx[0], k] = v
    df.at[idx[0], "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("개별 갱신 완료")
