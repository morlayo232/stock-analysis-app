import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from modules.calculate_indicators import add_tech_indicators

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

def update_single_stock(code):
    import streamlit as st

    st.write("===== [개별 갱신 시작] =====")
    st.write("입력 code:", code)

    code = str(code).zfill(6)

    try:
        price_info = fetch_price(code)
        fund_info = fetch_fundamental(code)

        if price_info["가격데이터"] is None:
            st.error(f"[개별 갱신][{code}] 가격 데이터 없음")
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
            "RSI_14": [df_price['RSI'].iloc[-1] if 'RSI' in df_price.columns else None],
            "MACD": [df_price['MACD'].iloc[-1] if 'MACD' in df_price.columns else None],
            "Signal": [df_price['Signal'].iloc[-1] if 'Signal' in df_price.columns else None],
            "EMA20": [df_price['EMA20'].iloc[-1] if 'EMA20' in df_price.columns else None],
        })

        st.success(f"[개별 갱신][{code}] 최신 데이터 반영 완료")
        return df_update

    except Exception as e:
        st.error(f"[개별 갱신][{code}] 오류 발생: {e}")
        return None
