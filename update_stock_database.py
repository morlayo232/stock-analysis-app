# update_stock_database.py
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from modules.score_utils import finalize_scores

# (1) 재무/밸류 수집 - 실제 KRX/API 로직으로 교체하세요
def fetch_krx_data(code):
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
        }
    except Exception as e:
        print("수집오류:", e)
        return None

# (2) 시계열 가격 히스토리 수집 (pykrx 사용 예시)
def fetch_price_history(code, days=90):
    from pykrx import stock
    end = datetime.today().strftime("%Y%m%d")
    start = (datetime.today() - timedelta(days=days)).strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(start, end, code)
    if not df.empty:
        df.to_csv(f"price_{code}.csv")
    return df

def update_database():
    # 초기 리스트 로드
    stocks = pd.read_csv("initial_krx_list_test.csv", dtype=str)
    stocks["종목코드"] = stocks["종목코드"].str.zfill(6)

    all_data = []
    for idx, row in stocks.iterrows():
        code = row["종목코드"]
        fin = fetch_krx_data(code)
        if fin is None:
            print(f"{code}: 재무 수집 실패, 스킵")
            continue

        record = {
            "종목명": row["종목명"],
            "종목코드": code,
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **fin
        }
        all_data.append(record)

        # 가격 히스토리도 동시에 저장
        fetch_price_history(code)

        print(f"[{idx+1}/{len(stocks)}] {code} 갱신 완료", end="\r")

    if not all_data:
        print("▶ 수집된 데이터 없음, CSV 생성 건너뜀.")
        return

    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("▶ filtered_stocks.csv 생성 완료!")

if __name__ == "__main__":
    update_database()
