import os
import pandas as pd
import numpy as np
import time
from datetime import datetime
from modules.score_utils import finalize_scores

def fetch_krx_data(code):
    # TODO: 진짜 KRX/API 수집 로직으로 교체
    try:
        return {
            "현재가": np.random.randint(1000, 50000),
            "PER": np.random.uniform(5, 20),
            "PBR": np.random.uniform(0.5, 3),
            "EPS": np.random.randint(100, 50000),
            "BPS": np.random.randint(1000, 50000),
            "배당률": np.random.uniform(0, 5),
            "거래량": np.random.randint(1000, 100000),
            "거래량평균20": np.random.randint(1000, 100000),
            "고가": np.random.randint(2000, 60000),
            "저가": np.random.randint(500, 30000),
        }
    except Exception as e:
        print("수집오류:", e)
        return None

def update_database():
    stocks = pd.read_csv("initial_krx_list_test.csv", dtype=str)
    all_data = []
    for i, row in stocks.iterrows():
        d = fetch_krx_data(row["종목코드"])
        if d is None:
            continue
        record = {
            "종목명": row["종목명"],
            "종목코드": row["종목코드"].zfill(6),
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **d
        }
        all_data.append(record)
    if not all_data:
        print("수집된 데이터가 없습니다.")
        return
    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 생성 완료!")

if __name__ == "__main__":
    update_database()

def update_single_stock(code):
    os.chdir(ROOT)

    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    idx = df[df["종목코드"] == str(code).zfill(6)].index
    if not len(idx):
        print("해당 종목이 없습니다.")
        return

    stock_data = fetch_krx_data(code)
    if stock_data is None:
        print(f"{code}: 개별 수집 실패")
        return

    for k, v in stock_data.items():
        df.loc[idx, k] = v
    df.loc[idx, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("개별 종목 업데이트 및 저장 완료!")
