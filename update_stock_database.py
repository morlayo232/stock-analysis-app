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
    df_list = pd.read_csv("initial_krx_list.csv", dtype={'종목코드': str})
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

def update_single_stock(code):
    import streamlit as st
    from datetime import datetime
    from modules.calculate_indicators import add_tech_indicators
    from pykrx import stock

    st.write("===== [개별 갱신 시작] =====")
    st.write("입력 code:", code)

    code = str(code).zfill(6)

    try:
        today = datetime.today()
        max_retry = 10
        price_info = None
        fund_info = None

        for i in range(max_retry):
            day = today - timedelta(days=i)
            if day.weekday() >= 5:
                continue
            date = day.strftime("%Y%m%d")
            try:
                df_price = stock.get_market_ohlcv_by_date(date, date, code)
                if df_price is not None and not df_price.empty:
                    price_info = {
                        "현재가": int(df_price['종가'].iloc[-1]),
                        "거래량": int(df_price['거래량'].iloc[-1]),
                        "거래대금": int(df_price['종가'].iloc[-1]) * int(df_price['거래량'].iloc[-1]),
                        "가격데이터": df_price
                    }
                    break
            except Exception:
                continue

        for i in range(max_retry):
            day = today - timedelta(days=i)
            if day.weekday() >= 5:
                continue
            date = day.strftime("%Y%m%d")
            try:
                df_fund = stock.get_market_fundamental_by_date(date, date, code)
                if df_fund is not None and not df_fund.empty:
                    fund_info = {
                        'PER': float(df_fund['PER'].iloc[-1]) if not pd.isna(df_fund['PER'].iloc[-1]) else None,
                        'PBR': float(df_fund['PBR'].iloc[-1]) if not pd.isna(df_fund['PBR'].iloc[-1]) else None,
                        'EPS': float(df_fund['EPS'].iloc[-1]) if not pd.isna(df_fund['EPS'].iloc[-1]) else None,
                        'BPS': float(df_fund['BPS'].iloc[-1]) if not pd.isna(df_fund['BPS'].iloc[-1]) else None,
                        '배당률': float(df_fund['DIV'].iloc[-1]) if not pd.isna(df_fund['DIV'].iloc[-1]) else None
                    }
                    break
            except Exception:
                continue

        if price_info is None or fund_info is None or price_info.get("가격데이터") is None:
            st.error(f"[개별 갱신][{code}] 데이터 없음")
            return None

        df_price = price_info["가격데이터"]
        df_price = add_tech_indicators(df_price)

        df_update = pd.DataFrame({
            "현재가": [price_info["현재가"]],
            "거래량": [price_info["거래량"]],
            "거래대금": [price_info["거래대금"]],
            "PER": [fund_info['PER']],
            "PBR": [fund_info['PBR']],
            "EPS": [fund_info['EPS']],
            "BPS": [fund_info['BPS']],
            "배당률": [fund_info['배당률']],
            "RSI_14": [df_price['RSI_14'].iloc[-1] if 'RSI_14' in df_price.columns else None],
            "MACD": [df_price['MACD'].iloc[-1] if 'MACD' in df_price.columns else None],
            "MACD_SIGNAL": [df_price['MACD_SIGNAL'].iloc[-1] if 'MACD_SIGNAL' in df_price.columns else None],
            "EMA_20": [df_price['EMA_20'].iloc[-1] if 'EMA_20' in df_price.columns else None],
        })

        st.success(f"[개별 갱신][{code}] 최신 데이터 반영 완료")
        return df_update

    except Exception as e:
        st.error(f"[개별 갱신][{code}] 오류 발생: {e}")
        return None
