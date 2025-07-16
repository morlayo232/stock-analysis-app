# update_stock_database.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.calculate_indicators import add_tech_indicators

def update_database():
    """
    전체 종목 데이터베이스 갱신(야간 또는 수동 갱신용)
    """
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드']).zfill(6)
        try:
            # 데이터 예시 : 네이버/pykrx 등 fetch 함수 사용
            price_df = pd.DataFrame()  # 실제 fetch_price(code) 등으로 대체
            price_df = add_tech_indicators(price_df) if not price_df.empty else price_df
            if not price_df.empty:
                for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량', '거래량평균20']:
                    if col in price_df.columns:
                        df.at[i, col] = price_df[col].iloc[-1]
            # 지표 등 추가 저장 가능
        except Exception as e:
            print(f"[전체 갱신][{code}] 오류: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    """
    단일 종목만 최신 데이터로 갱신 (수동 버튼)
    """
    import streamlit as st
    code = str(code).zfill(6)
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    row_idx = df[df['종목코드'] == code].index
    if len(row_idx) == 0:
        st.error(f"[개별 갱신][{code}] filtered_stocks.csv에 해당 종목코드 없음")
        return False
    idx = int(row_idx[0])
    try:
        # pykrx, 네이버 등에서 데이터 fetch
        price_df = pd.DataFrame()  # 실제 fetch_price(code) 등으로 대체
        price_df = add_tech_indicators(price_df) if not price_df.empty else price_df
        if not price_df.empty:
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량', '거래량평균20']:
                if col in price_df.columns:
                    df.at[idx, col] = price_df[col].iloc[-1]
            df.to_csv("filtered_stocks.csv", index=False)
            st.success(f"[개별 갱신][{code}] 최신 데이터 및 기술지표 반영됨")
            return True
        else:
            st.error(f"[개별 갱신][{code}] 데이터 수집 실패")
            return False
    except Exception as e:
        st.error(f"[개별 갱신][{code}] 오류: {e}")
        return False
