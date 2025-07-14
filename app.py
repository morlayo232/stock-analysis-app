import streamlit as st import pandas as pd import os from modules.score_utils import finalize_scores, assess_reliability from modules.fetch_news import fetch_google_news from modules.chart_utils import plot_price_rsi_macd from modules.calculate_indicators import add_tech_indicators from datetime import datetime from pykrx import stock

st.set_page_config(page_title="투자 매니저", layout="wide") st.title("\ud22c\uc790 \ub9e4\ub2c8\uc800")

자동/수동 데이터 로딩 

@st.cache_data

def load_filtered_data(): try: return pd.read_csv("filtered_stocks.csv") except: from update_stock_database import update_database try: update_database() return pd.read_csv("filtered_stocks.csv") except: return pd.DataFrame()

style = st.sidebar.radio("\ud22c\uc790 \uc131\ud5a5", ["aggressive", "stable", "dividend"], horizontal=True)

데이터 로딩 

raw_df = load_filtered_data() if raw_df.empty: st.error("\ub370이\ud130\ub97c \ub85c\ub4dc\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.") st.stop()

점수 계산 + 실력도 포함화 

scored_df = finalize_scores(raw_df, style=style) scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)

통합 목록 

st.subheader(f"\ud22c\uc790 \uc131\ud5a5({style}) \ud1b5합 \uc810수 TOP 10") top10 = scored_df.sort_values("score", ascending=False).head(10) st.dataframe(top10[["종목명", "종목코드", "현재가", "PER", "PBR", "ROE", "배당수익률", "score", "신뢰등급"]])

조회 필드 

selected = st.selectbox("\uc870명 \uc120\ud0dd", top10["종목명"].tolist()) code = top10[top10["종목명"] == selected]["종목코드"].values[0]

가격 환기 경로 + 지표 

start = "20240101" end = datetime.today().strftime("%Y%m%d") df_price = stock.get_market_ohlcv_by_date(start, end, code) if df_price.empty: st.warning("\uac00\uaca9 \ub370\uc774\ud130 \ucd94\uc801 \uc2e4\ud328") else: df_price = add_tech_indicators(df_price) st.plotly_chart(plot_price_rsi_macd(df_price), use_container_width=True)

최신 뉴스 

st.subheader("\ucd5c신 \ub274스") news = fetch_google_news(selected) if news: for n in news: st.markdown(f"- {n}") else: st.info("\ub274\uc2a4 \uc815\ubcf4 \uc5c6\uc74c")

수동 갱신 버튼 

if st.button("\ub370\uc774\ud130 \uc218동 \uac31신"): from update_stock_database import update_database update_database() st.success("\uac31신 \uc644\ub8cc! \ub2e4시 \uace8\ub4dc\ub9ac \ud574\uc8fc세요")

