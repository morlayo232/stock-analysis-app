# update_stock_database.py

import pandas as pd
import os
from pykrx import stock
from datetime import datetime, timedelta
from modules.calculate_indicators import add_tech_indicators
import sys

def fetch_price(code, max_retry=10):
    today = datetime.today()
    for i in range(max_retry):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:
            continue
        date = day.strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_date(date, date, code)
            if df is not None and not df.empty:
                price = int(df['종가'].iloc[-1])
                volume = int(df['거래량'].iloc[-1])
                transaction_value = price * volume
                return {
                    "현재가": price,
                    "거래량": volume,
                    "거래대금": transaction_value,
                    "가격데이터": df
                }
        except Exception:
            continue
    return {"현재가": None, "거래량": None, "거래대금": None, "가격데이터": None}

def fetch_fundamental(code, max_retry=10):
    today = datetime.today()
    for i in range(max_retry):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:
            continue
        date = day.strftime("%Y%m%d")
        try:
            df = stock.get_market_fundamental_by_date(date, date, code)
            if df is not None and not df.empty:
                return {
                    'PER': float(df['PER'].iloc[-1]) if not pd.isna(df['PER'].iloc[-1]) else None,
                    'PBR': float(df['PBR'].iloc[-1]) if not pd.isna(df['PBR'].iloc[-1]) else None,
                    'EPS': float(df['EPS'].iloc[-1]) if not pd.isna(df['EPS'].iloc[-1]) else None,
                    'BPS': float(df['BPS'].iloc[-1]) if not pd.isna(df['BPS'].iloc[-1]) else None,
                    '배당률': float(df['DIV'].iloc[-1]) if not pd.isna(df['DIV'].iloc[-1]) else None
                }
        except Exception:
            continue
    return {'PER': None, 'PBR': None, 'EPS': None, 'BPS': None, '배당률': None}

def update_database():
    df_list = pd.read_csv("initial_krx_list_test.csv", dtype={'종목코드': str})
    codes = dict(zip(df_list['종목명'], df_list['종목코드']))
    data = []
    for name, code in codes.items():
        price_info = fetch_price(code)
        fund_info = fetch_fundamental(code)
        data.append({
            "종목명": name,
            "종목코드": code,
            "현재가": price_info["현재가"],
            "거래량": price_info["거래량"],
            "거래대금": price_info["거래대금"],
            "PER": fund_info["PER"],
            "PBR": fund_info["PBR"],
            "EPS": fund_info.get("EPS"),
            "BPS": fund_info.get("BPS"),
            "배당률": fund_info["배당률"]
        })
    df = pd.DataFrame(data)
    print(f"[update_database] 수집 데이터 건수: {len(df)}", file=sys.stderr)
    print(df.head(), file=sys.stderr)
    print(df.info(), file=sys.stderr)

    csv_path = "filtered_stocks.csv"
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"{csv_path} 파일 생성/갱신 완료!", file=sys.stderr)
    except Exception as e:
        print(f"{csv_path} 저장 실패: {e}", file=sys.stderr)

if __name__ == "__main__":
    update_database()
