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
def update_single_stock(code):
import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from modules.calculate_indicators import add_tech_indicators
st.write("===== [갱신 시작] =====") st.write("입력 code:", code) df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str}) code = str(code).zfill(6) row_idx = df[df['종목코드'] == code].index if len(row_idx) == 0: st.error(f"[개별 갱신][{code}] filtered_stocks.csv에 해당 종목코드 없음") raise Exception(f"종목코드({code}) 없음") idx = int(row_idx[0]) try: # 1. 과거 1년치 가격 데이터 불러오기 today = datetime.today() start = (today - timedelta(days=365)).strftime("%Y%m%d") end = today.strftime("%Y%m%d") df_price = stock.get_market_ohlcv_by_date(start, end, code) if df_price is None or df_price.empty: st.error(f"[개별 갱신][{code}] 가격 데이터 없음") raise Exception("가격 데이터 없음") # 2. 기술적 지표 계산 df_price = add_tech_indicators(df_price) # 3. 최신 재무 데이터 (pykrx fundamental) fund = stock.get_market_fundamental_by_date(end, end, code) # 4. filtered_stocks.csv에 최신값 반영 df.at[idx, '현재가'] = int(df_price['종가'].iloc[-1]) if not fund.empty: for col in ['PER', 'PBR', 'EPS', 'BPS', 'DIV']: if col in fund.columns: val = fund[col].iloc[-1] if col == "DIV": df.at[idx, '배당률'] = val else: df.at[idx, col] = val # 5. 기술적지표 값도 csv에 반영 for col in ['RSI', 'MACD', 'Signal', 'EMA20']: if col in df_price.columns: df.at[idx, col] = df_price[col].iloc[-1] df.to_csv("filtered_stocks.csv", index=False) st.success(f"[개별 갱신][{code}] 최신 데이터 및 기술지표 반영됨") return True except Exception as e: st.error(f"[개별 갱신][{code}] 오류: {e}") raise 
