# update_stock_database.py

import pandas as pd
import numpy as np
from datetime import datetime
from modules.calculate_indicators import add_tech_indicators

def update_database():
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드']).zfill(6)
        try:
            price_df = pd.DataFrame()  # fetch_price(code) 등으로 실제 치환
            price_df = add_tech_indicators(price_df) if not price_df.empty else price_df
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량', '거래량평균20']:
                if col in price_df.columns:
                    df.at[i, col] = price_df[col].iloc[-1]
        except Exception as e:
            print(f"[전체 갱신][{code}] 오류: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    import streamlit as st
    code = str(code).zfill(6)
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    idx = df[df['종목코드'] == code].index
    if len(idx) == 0:
        st.error(f"[개별 갱신][{code}] 없음")
        return False
    idx = idx[0]
    try:
        price_df = pd.DataFrame()  # fetch_price(code) 등으로 실제 치환
        price_df = add_tech_indicators(price_df) if not price_df.empty else price_df
        for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률', '거래량', '거래량평균20']:
            if col in price_df.columns:
                df.at[idx, col] = price_df[col].iloc[-1]
        df.to_csv("filtered_stocks.csv", index=False)
        st.success("개별 종목 갱신 완료")
        return True
    except Exception as e:
        st.error(str(e))
        return False
