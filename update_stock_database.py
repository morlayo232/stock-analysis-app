import pandas as pd
from modules.fetch_price import fetch_price
from modules.calculate_indicators import add_tech_indicators

def update_database():
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드']).zfill(6)
        try:
            price_df = fetch_price(code)
            if price_df is None or price_df.empty:
                print(f"[전체 갱신][{code}] fetch_price 결과 없음/빈 데이터. 건너뜀.")
                continue
            price_df = add_tech_indicators(price_df)
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                if col in price_df.columns:
                    df.at[i, col] = price_df[col].iloc[-1]
                else:
                    print(f"[전체 갱신][{code}] 컬럼 {col} 없음")
        except Exception as e:
            print(f"[전체 갱신][{code}] 오류: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

import streamlit as st

def update_single_stock(code):
    import streamlit as st
    st.write("===== [갱신 시작] =====")
    st.write("입력 code:", code)
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    st.write("filtered_stocks.csv 종목코드 샘플:", df['종목코드'].head())
    code = str(code).zfill(6)
    st.write("코드 변환:", code)
    row_idx = df[df['종목코드'] == code].index
    st.write("row_idx:", row_idx)
    if len(row_idx) == 0:
        st.error(f"[개별 갱신][{code}] filtered_stocks.csv에 해당 종목코드 없음")
        raise Exception(f"종목코드({code}) 없음")
    try:
        price_df = fetch_price(code)
        st.write("price_df shape:", price_df.shape if price_df is not None else None)
        st.write("price_df 컬럼:", list(price_df.columns) if price_df is not None else None)
        st.write("price_df 샘플:", price_df.head() if price_df is not None else None)
        if price_df is None or price_df.empty:
            st.error(f"[개별 갱신][{code}] fetch_price 결과 없음/빈 데이터")
            raise Exception(f"fetch_price({code}) 결과 없음/빈 데이터")
        price_df = add_tech_indicators(price_df)
        for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
            st.write(f"컬럼 {col} 값:", price_df[col].iloc[-1] if col in price_df.columns else "없음")
            if col in price_df.columns:
                df.at[row_idx[0], col] = price_df[col].iloc[-1]
        df.to_csv("filtered_stocks.csv", index=False)
        st.success(f"[개별 갱신][{code}] 성공적으로 반영됨.")
        return True
    except Exception as e:
        st.error(f"[개별 갱신][{code}] 오류: {e}")
        raise
