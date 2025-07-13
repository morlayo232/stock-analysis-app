[1] app.py Streamlit 메인 애플리케이션 

import streamlit as st import yfinance as yf import pandas as pd import json import os from datetime import datetime from modules.calculate_indicators import calculate_indicators from modules.score_utils import calc_investment_score from charts import plot_stock_chart, plot_rsi_macd from update_stock_database import main as update_main from news import fetch_news_headlines

st.set_page_config(page_title="한국 주식 분석", layout="wide")

FAV_FILE = "favorites.json" def load_favorites(): try: with open(FAV_FILE, 'r') as f: return json.load(f) except: return []

def save_favorites(favs): with open(FAV_FILE, 'w') as f: json.dump(favs, f, indent=2)

favorites = load_favorites()

@st.cache_data(ttl=86400) def load_filtered_stocks(): df = pd.read_csv('filtered_stocks.csv', dtype=str) return df

filtered_stocks = load_filtered_stocks()

def search_stocks(keyword, stocks_df): if keyword.strip() == '': return pd.DataFrame() return stocks_df[stocks_df['종목명'].str.contains(keyword, case=False)]

st.title("\U0001F4C8 한국 주식 시장 투자 매력도 분석")

investment_style = st.sidebar.radio("투자 성향 선택", ['공격적', '안정적', '배당형'], key="style") search_keyword = st.sidebar.text_input("종목명 검색", key="search") search_results = search_stocks(search_keyword, filtered_stocks) selected_ticker = None selected_name = None

if not search_results.empty: selection = st.sidebar.selectbox("검색된 종목 선택", options=search_results['종목명'] + ' (' + search_results['종목코드'] + ')', key="selectbox") selected_name = selection.split(' (')[0] selected_ticker = selection.split('(')[1].strip(')')

st.sidebar.markdown("### ⭐ 즐겨찾기") for fav_code in favorites: fav_name = filtered_stocks[filtered_stocks['종목코드'] == fav_code]['종목명'].values if len(fav_name) > 0: st.sidebar.write(f"- {fav_name[0]} ({fav_code})")

if selected_ticker: if st.sidebar.button("즐겨찾기 추가", key="fav_add"): if selected_ticker not in favorites: favorites.append(selected_ticker) save_favorites(favorites) st.sidebar.success("즐겨찾기에 추가했습니다.")

if selected_ticker: try: stock = yf.Ticker(selected_ticker) df = stock.history(period="6mo").reset_index() if df.empty or len(df) < 10: raise ValueError("주가 데이터 부족") df = calculate_indicators(df)

score = calc_investment_score(df, investment_style) st.subheader(f"선택 종목: {selected_name} ({selected_ticker})") st.markdown(f"투자 성향: **{investment_style}** / 투자 매력 점수: **{score:.2f}**") st.plotly_chart(plot_stock_chart(df), use_container_width=True) st.plotly_chart(plot_rsi_macd(df), use_container_width=True) st.markdown("### 관련 뉴스 헤드라인") headlines = fetch_news_headlines(selected_name) if headlines: for title, link in headlines: st.markdown(f"- [{title}]({link})") st.markdown("### 추천 매수/매도 가격") golden_cross = df[(df['EMA5'] > df['EMA20']) & (df['EMA5'].shift(1) <= df['EMA20'].shift(1))] dead_cross = df[(df['EMA5'] < df['EMA20']) & (df['EMA5'].shift(1) >= df['EMA20'].shift(1))] if not golden_cross.empty: buy_price = golden_cross['Close'].iloc[-1] st.success(f"최근 골든크로스 매수 가격: {buy_price:.2f}") if not dead_cross.empty: sell_price = dead_cross['Close'].iloc[-1] st.warning(f"최근 데드크로스 매도 가격: {sell_price:.2f}") st.markdown("### 투자 판단 요약") rsi = df['RSI'].iloc[-1] macd = df['MACD'].iloc[-1] signal = df['Signal'].iloc[-1] if rsi > 70: st.warning("⚠️ RSI 70 이상 → 과매수 구간") elif rsi < 30: st.success("✅ RSI 30 이하 → 매수 기회") else: st.info("ℹ️ RSI 중립 영역") if macd > signal: st.success("📈 MACD > Signal → 상승 전환 신호") else: st.warning("📉 MACD < Signal → 하락 전환 신호") except Exception as e: st.error("주가 정보를 불러오는 중 오류 발생") st.exception(e) 수동 갱신 기능 

st.sidebar.markdown("### ⟳ 수동 데이터 갱신") if st.sidebar.button("Update Now"): with st.spinner("업데이트 중입니다..."): try: update_main() st.cache_data.clear() st.success("업데이트 완료!") except Exception as e: st.error("업데이트 실패:") st.exception(e)

마지막 업데이트 시간 표시 

try: ts = os.path.getmtime("filtered_stocks.csv") st.sidebar.markdown(f"📅 마지막 갱신: {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}") except: st.sidebar.warning("CSV 파일을 찾을 수 없습니다.")

