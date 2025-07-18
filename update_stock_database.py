# update_stock_database.py

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pykrx import stock
from modules.score_utils import finalize_scores

# 가격 히스토리 60일치 저장 (차트용)
def save_price_history(code, days=60):
    today = datetime.today().strftime("%Y%m%d")
    start = (datetime.today() - timedelta(days=days*1.5)).strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(start, today, code)
    if not df.empty:
        df.to_csv(f"price_{code}.csv")

# 개별 종목 데이터 수집
def fetch_krx_snapshot(code):
    today = datetime.today().strftime("%Y%m%d")
    df = stock.get_market_fundamental_by_date(today, today, code)
    ohlcv = stock.get_market_ohlcv_by_date(today, today, code)
    return {
        "현재가": int(ohlcv["종가"].iloc[-1]),
        "PER": float(df["PER"].iloc[-1]),
        "PBR": float(df["PBR"].iloc[-1]),
        "EPS": float(df["EPS"].iloc[-1]),
        "BPS": float(df["BPS"].iloc[-1]),
        "배당률": float(df["DIV"].iloc[-1]),
        "거래량": int(ohlcv["거래량"].iloc[-1]),
        # 단순히 예시, 필요시 더 추가
    }

def update_database():
    stocks = pd.read_csv("initial_krx_list_test.csv", dtype=str)
    all_data = []
    for idx, row in stocks.iterrows():
        code = row["종목코드"].zfill(6)
        snap = fetch_krx_snapshot(code)
        record = {
            "종목명": row["종목명"],
            "종목코드": code,
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **snap
        }
        all_data.append(record)
        save_price_history(code)
    if not all_data:
        print("수집된 데이터가 없습니다.")
        return
    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 및 price_*.csv 생성 완료!")

def update_single_stock(code):
    # code는 already zfill(6)
    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    idx = df.index[df["종목코드"] == code]
    if idx.empty:
        print("해당 종목이 없습니다.")
        return
    snap = fetch_krx_snapshot(code)
    for k, v in snap.items():
        df.loc[idx, k] = v
    df.loc[idx, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    save_price_history(code)
    print(f"{code} 개별 업데이트 및 price_{code}.csv 저장 완료!")

if __name__ == "__main__":
    update_database()
