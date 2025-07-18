# update_stock_database.py

import os
import pandas as pd
import numpy as np
import time
from datetime import datetime
from modules.score_utils import finalize_scores

def fetch_krx_data(code: str):
    """
    TODO: 실제 KRX/API 수집 로직으로 교체하세요.
    테스트용 더미 데이터 반환.
    """
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
    """
    initial_krx_list_test.csv 에 있는 모든 종목을 새로 수집해서
    filtered_stocks.csv 로 저장합니다.
    """
    csv_in = "initial_krx_list_test.csv"
    if not os.path.exists(csv_in):
        print(f"{csv_in} 파일이 없습니다.")
        return

    stocks = pd.read_csv(csv_in, dtype=str)
    all_data = []

    for idx, row in stocks.iterrows():
        code = row["종목코드"].zfill(6)
        raw = fetch_krx_data(code)
        if raw is None:
            print(f"{code} 데이터 수집 실패, 건너뜀")
            continue

        record = {
            "종목명": row["종목명"],
            "종목코드": code,
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **raw
        }
        all_data.append(record)
        print(f"{idx+1}/{len(stocks)} 갱신 중...", end="\r")

    if not all_data:
        print("수집된 데이터가 없습니다. filtered_stocks.csv 저장 건너뜀.")
        return

    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)

    # 안정화를 위해 잠시 대기
    time.sleep(0.5)
    if os.path.exists("filtered_stocks.csv"):
        print("filtered_stocks.csv 생성 완료!")
    else:
        print("filtered_stocks.csv 생성 실패!")

def update_single_stock(code: str):
    """
    이미 있는 filtered_stocks.csv 에서 해당 코드의 행만 새로 수집해서
    덮어쓴 뒤 다시 저장합니다.
    """
    csv_out = "filtered_stocks.csv"
    if not os.path.exists(csv_out):
        print(f"{csv_out} 파일이 없습니다. 전체 갱신을 먼저 실행하세요.")
        return

    df = pd.read_csv(csv_out, dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    idxs = df.index[df["종목코드"] == code]
    if len(idxs) == 0:
        print(f"{code} 종목을 찾을 수 없습니다.")
        return

    raw = fetch_krx_data(code)
    if raw is None:
        print(f"{code} 데이터 수집 실패")
        return

    i = idxs[0]
    for k, v in raw.items():
        df.at[i, k] = v
    df.at[i, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    df = finalize_scores(df)
    df.to_csv(csv_out, index=False)

    # 안정화
    time.sleep(0.2)
    print(f"{code} 개별 갱신 완료! filtered_stocks.csv 저장됨.")
