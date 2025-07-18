import os
import pandas as pd
import numpy as np
from datetime import datetime
from modules.score_utils import finalize_scores

# 실제 KRX/API 수집 로직으로 교체하세요
def fetch_krx_data(code: str) -> dict | None:
    try:
        # ↓ 여기를 실제 크롤러/API로 대체
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
    except:
        return None

def update_database():
    csv_in = "initial_krx_list_test.csv"
    if not os.path.exists(csv_in):
        print(f"{csv_in} not found.")
        return

    stocks = pd.read_csv(csv_in, dtype=str)
    records = []
    for _, row in stocks.iterrows():
        data = fetch_krx_data(row["종목코드"])
        if not data:
            continue
        rec = {
            "종목명": row["종목명"],
            "종목코드": row["종목코드"].zfill(6),
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **data
        }
        records.append(rec)

    if not records:
        print("데이터 수집 실패: 저장 건너뜀")
        return

    df = pd.DataFrame(records)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 생성 완료.")

def update_single_stock(code: str):
    path = "filtered_stocks.csv"
    if not os.path.exists(path):
        print("filtered_stocks.csv가 없습니다. 전체갱신 먼저 실행하세요.")
        return

    df = pd.read_csv(path, dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    idx = df.index[df["종목코드"] == code]
    if len(idx) == 0:
        print(f"{code} 종목을 찾을 수 없습니다.")
        return

    data = fetch_krx_data(code)
    if not data:
        print(f"{code} 개별 수집 실패")
        return

    i = idx[0]
    for k, v in data.items():
        df.at[i, k] = v
    df.at[i, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 재계산 후 저장
    df = finalize_scores(df)
    df.to_csv(path, index=False)
    print(f"{code} 개별 업데이트 완료.")
