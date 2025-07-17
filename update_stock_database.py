# update_stock_database.py

import pandas as pd
import numpy as np
import os
from datetime import datetime
from pykrx import stock

COLUMNS = [
    "종목코드", "종목명", "시장구분",
    "현재가", "거래량", "거래량평균20",
    "PER", "PBR", "EPS", "BPS", "배당률",
    "score", "급등확률", "갱신일"
]

def initialize_filtered_stocks(initial_csv="initial_krx_list_test.csv", filtered_csv="filtered_stocks.csv"):
    """
    최초 1회: initial_krx_list.csv(종목코드, 종목명, 시장구분 등) → filtered_stocks.csv 구조로 변환/생성
    """
    df_init = pd.read_csv(initial_csv, dtype=str)
    for c in COLUMNS:
        if c not in df_init.columns:
            df_init[c] = ""
    df_init = df_init[COLUMNS]
    df_init.to_csv(filtered_csv, index=False)
    print(f"[초기생성] {filtered_csv} 생성 완료 ({len(df_init)}종목)")

def update_single_stock(code, filtered_csv="filtered_stocks.csv"):
    """
    단일 종목의 최신 데이터 갱신
    """
    df = pd.read_csv(filtered_csv, dtype=str)
    code = str(code).zfill(6)
    idx = df.index[df["종목코드"] == code]
    if len(idx) == 0:
        print(f"[개별갱신] {code} 없음")
        return
    i = idx[0]
    today = datetime.today().strftime("%Y%m%d")
    # KRX 데이터 수집(가격/재무/거래량)
    try:
        price = stock.get_market_ohlcv_by_date(today, today, code)
        fund = stock.get_market_fundamental_by_date(today, today, code)
        if not price.empty:
            df.at[i, "현재가"] = int(price["종가"][-1])
            df.at[i, "거래량"] = int(price["거래량"][-1])
            # 20일 평균 거래량
            hist = stock.get_market_ohlcv_by_date(
                (datetime.today() - pd.Timedelta(days=30)).strftime("%Y%m%d"),
                today, code)
            if not hist.empty:
                df.at[i, "거래량평균20"] = int(hist["거래량"].tail(20).mean())
        if not fund.empty:
            for c in ["PER", "PBR", "EPS", "BPS"]:
                if c in fund.columns:
                    df.at[i, c] = fund[c][-1]
            if "DIV" in fund.columns:
                df.at[i, "배당률"] = fund["DIV"][-1]
        df.at[i, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"[개별갱신] {code} 완료")
    except Exception as e:
        print(f"[개별갱신] {code} 오류: {e}")
    df.to_csv(filtered_csv, index=False)

def update_database(filtered_csv="filtered_stocks.csv"):
    """
    전체 종목 최신 데이터 일괄 갱신
    """
    if not os.path.exists(filtered_csv):
        print(f"[전체갱신] {filtered_csv} 없음. 초기화 후 실행 바랍니다.")
        return
    df = pd.read_csv(filtered_csv, dtype=str)
    total = len(df)
    for i, code in enumerate(df["종목코드"]):
        update_single_stock(code, filtered_csv)
        print(f"[전체갱신] {i+1}/{total} 완료")
    df = pd.read_csv(filtered_csv, dtype=str)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    df["갱신일"] = now
    df.to_csv(filtered_csv, index=False)
    print(f"[전체갱신] {total}종목 완료, {filtered_csv} 저장됨.")

if __name__ == "__main__":
    # 최초 실행(1회): filtered_stocks.csv 생성
    if not os.path.exists("filtered_stocks.csv"):
        initialize_filtered_stocks()
    # 전체 종목 자동 갱신 실행
    update_database()
