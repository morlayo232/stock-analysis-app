import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from modules.calculate_indicators import add_tech_indicators
from modules.score_utils import finalize_scores

def fetch_price(code, max_retry=10):
    today = datetime.today()
    for i in range(max_retry):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:  # 주말 제외
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
    import sys
    try:
        df_list = pd.read_csv("initial_krx_list.csv", dtype={'종목코드': str})
    except Exception as e:
        print(f"initial_krx_list.csv 파일 로드 실패: {e}", file=sys.stderr)
        return

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
            "PER": fund_info['PER'],
            "PBR": fund_info['PBR'],
            "EPS": fund_info['EPS'],
            "BPS": fund_info['BPS'],
            "배당률": fund_info['배당률']
        })

    df = pd.DataFrame(data)
    if not df.empty:
        df = finalize_scores(df, style="aggressive")
        try:
            df.to_csv("filtered_stocks.csv", index=False, encoding='utf-8-sig')
            print("filtered_stocks.csv 저장 완료!", file=sys.stderr)
        except Exception as e:
            print(f"filtered_stocks.csv 저장 실패: {e}", file=sys.stderr)
    else:
        print("수집 데이터가 비어있어 저장하지 않음", file=sys.stderr)

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
