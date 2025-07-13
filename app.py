import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import apply_score_model
from modules.chart_utils import plot_stock_chart, plot_rsi_macd
from modules.fetch_price import fetch_stock_price
from modules.fetch_news import fetch_news_headlines
from update_stock_database import main as update_main

st.set_page_config(page_title="📈 한국 주식 분석", layout="wide")

FAV_FILE = "favorites.json"

@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv("filtered_stocks.csv", dtype=str)

def load_favorites():
    try:
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=2)

def search_stocks(keyword, df):
    return df[df["종목명"].str.contains(keyword, case=False)] if keyword else pd.DataFrame()

filtered_stocks = load_filtered_stocks()
favorites = load_favorites()

st.title("📊 한국 주식 시장 투자 매력도 분석")

style = st.sidebar.radio("투자 성향", ["공격적", "안정적", "배당형"])
keyword = st.sidebar.text_input("🔍 종목 검색")
results = search_stocks(keyword, filtered_stocks)

selected_code, selected_name = None, None
if not results.empty:
    selection = st.sidebar.selectbox("검색 결과", results["종목명"] + " (" + results["종목코드"] + ")")
    selected_name = selection.split(" (")[0]
    selected_code = selection.split("(")[1].strip(")")

# 즐겨찾기
st.sidebar.markdown("### ⭐ 즐겨찾기")
for fav in favorites:
    name = filtered_stocks[filtered_stocks["종목코드"] == fav]["종목명"].values
    if len(name):
        st.sidebar.write(f"- {name[0]} ({fav})")

if selected_code and st.sidebar.button("즐겨찾기 추가"):
    if selected_code not in favorites:
        favorites.append(selected_code)
        save_favorites(favorites)
        st.sidebar.success("추가 완료")

# 상위 10개 종목 추천 테이블 (점수 기준, 투자 성향별)
def get_top10(df, style):
    df["score"] = pd.to_numeric(df["score"], errors='coerce')
    # 투자 성향별 정렬/가중치 예시 (원하면 커스텀 가능)
    # 여기서는 점수 내림차순 top10만 간단 추출
    top10 = df.sort_values("score", ascending=False).head(10)
    return top10

st.markdown("## 🏆 투자 성향별 추천 TOP 10")
top10 = get_top10(filtered_stocks, style)
st.table(top10[["종목명", "종목코드", "시장구분", "score"]])

if selected_code:
    df = fetch_stock_price(selected_code)
    if df.empty:
        st.warning("📉 주가 데이터를 불러올 수 없습니다.")
    else:
        df = calculate_indicators(df)
        # 실제 점수 계산 함수/적용
        latest_info = {
            "PER": filtered_stocks[filtered_stocks["종목코드"] == selected_code]["PER"].values[0] if "PER" in filtered_stocks else None,
            "PBR": filtered_stocks[filtered_stocks["종목코드"] == selected_code]["PBR"].values[0] if "PBR" in filtered_stocks else None,
            "ROE": filtered_stocks[filtered_stocks["종목코드"] == selected_code]["ROE"].values[0] if "ROE" in filtered_stocks else None,
            "배당률": filtered_stocks[filtered_stocks["종목코드"] == selected_code]["배당률"].values[0] if "배당률" in filtered_stocks else None
        }
        score_info = apply_score_model(latest_info)

        st.subheader(f"📌 {selected_name} ({selected_code})")
        st.markdown(f"투자 성향: **{style}** | 종합 점수: **{score_info['score']:.2f}**")

        st.plotly_chart(plot_stock_chart(df), use_container_width=True)
        st.plotly_chart(plot_rsi_macd(df), use_container_width=True)

        # 매수/매도 시점
        crosses = {
            "골든크로스": df[(df["EMA5"] > df["EMA20"]) & (df["EMA5"].shift(1) <= df["EMA20"].shift(1))],
            "데드크로스": df[(df["EMA5"] < df["EMA20"]) & (df["EMA5"].shift(1) >= df["EMA20"].shift(1))]
        }
        st.markdown("### 💰 추천 매수/매도 가격")
        if not crosses["골든크로스"].empty:
            st.success(f"최근 골든크로스 매수: {crosses['골든크로스']['Close'].iloc[-1]:,.2f}원")
        if not crosses["데드크로스"].empty:
            st.warning(f"최근 데드크로스 매도: {crosses['데드크로스']['Close'].iloc[-1]:,.2f}원")

        # 투자 어드바이스
        st.markdown("### 🧭 투자 판단 요약")
        if df["RSI"].iloc[-1] > 70:
            st.warning("과매수 (RSI>70) → 매도 고려")
        elif df["RSI"].iloc[-1] < 30:
            st.success("과매도 (RSI<30) → 매수 기회")
        else:
            st.info("RSI 중간 → 관망")

        if df["MACD"].iloc[-1] > df["Signal"].iloc[-1]:
            st.success("MACD > Signal → 상승 흐름")
        else:
            st.warning("MACD < Signal → 하락 흐름")

        # 뉴스
        st.markdown("### 📰 관련 뉴스")
        news = fetch_news_headlines(selected_name)
        if news:
            for title, link in news:
                st.markdown(f"- [{title}]({link})")
        else:
            st.info("뉴스 없음")

# 수동 업데이트
st.sidebar.markdown("### 🔄 수동 데이터 갱신")
if st.sidebar.button("Update Now"):
    with st.spinner("업데이트 중..."):
        try:
            before = filtered_stocks.copy()
            update_main()
            st.cache_data.clear()
            after = load_filtered_stocks()
            changes = pd.concat([before, after]).drop_duplicates(keep=False)
            st.success("업데이트 완료")
            if not changes.empty:
                st.info(f"📌 변경 {len(changes)}건")
                st.dataframe(changes)
        except Exception as e:
            st.error("업데이트 실패")
            st.exception(e)

# 마지막 업데이트 시간
try:
    t = os.path.getmtime("filtered_stocks.csv")
    st.sidebar.caption(f"📅 마지막 갱신: {datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}")
except:
    st.sidebar.warning("CSV 없음")
