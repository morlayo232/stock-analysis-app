import streamlit as st
import pandas as pd
import os
from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd
from modules.calculate_indicators import add_tech_indicators
from datetime import datetime
from pykrx import stock

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

@st.cache_data
def load_filtered_data():
    try:
        return pd.read_csv("filtered_stocks.csv")
    except:
        from update_stock_database import update_database
        try:
            update_database()
            return pd.read_csv("filtered_stocks.csv")
        except:
            return pd.DataFrame()

style = st.sidebar.radio("투자 성향", ["aggressive", "stable", "dividend"], horizontal=True)

raw_df = load_filtered_data()
if raw_df.empty:
    st.error("데이터를 로드할 수 없습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)

st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
top10 = scored_df.sort_values("score", ascending=False).head(10)
st.dataframe(top10[["종목명", "종목코드", "현재가", "PER", "PBR", "ROE", "배당수익률", "score", "신뢰등급"]])

selected = st.selectbox("종목 선택", top10["종목명"].tolist())
code = top10[top10["종목명"] == selected]["종목코드"].values[0]

start = "20240101"
end = datetime.today().strftime("%Y%m%d")
df_price = stock.get_market_ohlcv_by_date(start, end, code)
if df_price.empty:
    st.warning("가격 데이터 추적 실패")
else:
    df_price = add_tech_indicators(df_price)
    st.plotly_chart(plot_price_rsi_macd(df_price), use_container_width=True)

st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")

if st.button("데이터 수동 갱신"):
    from update_stock_database import update_database
    update_database()
    st.success("갱신 완료! 다시 골드리 해주세요")
