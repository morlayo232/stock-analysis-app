import streamlit as st import pandas as pd import os import numpy as np import sys sys.path.append(os.path.abspath("modules")) from score_utils import finalize_scores, assess_reliability from fetch_news import fetch_google_news from chart_utils import plot_price_rsi_macd from calculate_indicators import add_tech_indicators from datetime import datetime from pykrx import stock

st.set_page_config(page_title="투자 매니저", layout="wide") st.title("투자 매니저")

@st.cache_data def load_filtered_data(): try: df = pd.read_csv("filtered_stocks.csv") expected = ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률"] for col in expected: if col not in df.columns: df[col] = np.nan return df except: from update_stock_database import update_database try: update_database() df = pd.read_csv("filtered_stocks.csv") for col in expected: if col not in df.columns: df[col] = np.nan return df except: return pd.DataFrame()

style = st.sidebar.radio("투자 성향", ["aggressive", "stable", "dividend"], horizontal=True)

raw_df = load_filtered_data() if not isinstance(raw_df, pd.DataFrame): st.error("데이터가 DataFrame 형식이 아닙니다.") st.stop()

if raw_df.empty: st.error("데이터프레임이 비어 있습니다.") st.stop()

scored_df = finalize_scores(raw_df, style=style) scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)

st.subheader(f"투자 성향({style}) 통합 점수 TOP 10") top10 = scored_df.sort_values("score", ascending=False).head(10) st.dataframe(top10[[ "종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급" ]])

st.subheader("종목 검색") keyword = st.text_input("종목명을 입력하세요") filtered = scored_df[scored_df["종목명"].str.contains(keyword, case=False, na=False)]

if not filtered.empty: selected = st.selectbox("종목 선택", filtered["종목명"].tolist()) code = filtered[filtered["종목명"] == selected]["종목코드"].values[0] else: st.warning("해당 종목이 없습니다.") st.stop()

start = "20240101" end = datetime.today().strftime("%Y%m%d") df_price = stock.get_market_ohlcv_by_date(start, end, code)

if df_price is None or df_price.empty: st.warning("가격 데이터 추적 실패") else: df_price = add_tech_indicators(df_price) st.plotly_chart(plot_price_rsi_macd(df_price), use_container_width=True)

st.subheader("최신 뉴스") news = fetch_google_news(selected) if news: for n in news: st.markdown(f"- {n}") else: st.info("뉴스 정보 없음")

if st.button("데이터 수동 갱신"): from update_stock_database import update_database try: update_database() st.success("갱신 완료! 다시 골드리 해주세요") except: st.error("수동 갱신 실패")

