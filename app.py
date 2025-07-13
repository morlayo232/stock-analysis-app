# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import calc_investment_score
from modules.chart_utils import plot_stock_chart, plot_rsi_macd
from modules.fetch_price import load_stock_price
from modules.fetch_news import fetch_news_headlines
from update_stock_database import main as update_main

st.set_page_config(page_title="📊 한국 주식 분석", layout="wide")

FAV_FILE = "favorites.json"

def load_favorites():
    try:
        with open(FAV_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_favorites(favs):
    with open(FAV_FILE, 'w') as f:
        json.dump(favs, f, indent=2)

@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv("filtered_stocks.csv", dtype=str)

favorites = load_favorites()
filtered_stocks = load_filtered_stocks()

st.title("📈 한국 주식 시장 종목 분석 및 추천")

# --- 사이드바 ---
investment_style = st.sidebar.radio("투자 성향 선택", ['공격적', '안정적', '배당형'])
keyword = st.sidebar.text_input("🔍 종목명 검색")

search_df = filtered_stocks[filtered_stocks['종목명'].str.contains(keyword, case=False)] if keyword else pd.DataFrame()
selected_ticker, selected_name = None, None

if not search_df.empty:
    options = search_df['종목명'] + " (" + search_df['종목코드'] + ")"
    selected = st.sidebar.selectbox("종목 선택", options)
    selected_name = selected.split(" (")[0]
    selected_ticker = selected.split("(")[1].strip(")")

if selected_ticker:
    if st.sidebar.button("⭐ 즐겨찾기 추가"):
        if selected_ticker not in favorites:
            favorites.append(selected_ticker)
            save_favorites(favorites)
            st.sidebar.success("즐겨찾기에 추가됨")

st.sidebar.markdown("---")
st.sidebar.markdown("📌 즐겨찾기 종목")
for code in favorites:
    name = filtered_stocks[filtered_stocks['종목코드'] == code]['종목명'].values
    if len(name) > 0:
        st.sidebar.write(f"- {name[0]} ({code})")

# --- 종목 분석 ---
if selected_ticker:
    df = load_stock_price(selected_ticker)
    if df.empty:
        st.error("❌ 주가 데이터를 불러올 수 없습니다.")
    else:
        df = calculate_indicators(df)
        score = calc_investment_score(df, selected_ticker, investment_style)

        st.subheader(f"🔍 {selected_name} ({selected_ticker})")
        st.markdown(f"**투자 성향:** {investment_style} / **점수:** {score:.2f}")

        st.plotly_chart(plot_stock_chart(df), use_container_width=True)
        st.plotly_chart(plot_rsi_macd(df), use_container_width=True)

        # 매수/매도 판단
        golden = df[(df['EMA5'] > df['EMA20']) & (df['EMA5'].shift(1) <= df['EMA20'].shift(1))]
        dead = df[(df['EMA5'] < df['EMA20']) & (df['EMA5'].shift(1) >= df['EMA20'].shift(1))]
        st.markdown("### 💸 매수/매도 시점")
        if not golden.empty:
            st.success(f"최근 골든크로스 → 매수 추천가: {golden['Close'].iloc[-1]:,.0f}")
        if not dead.empty:
            st.warning(f"최근 데드크로스 → 매도 추천가: {dead['Close'].iloc[-1]:,.0f}")

        # 어드바이스
        st.markdown("### 🧠 투자 어드바이스")
        rsi, macd, signal = df['RSI'].iloc[-1], df['MACD'].iloc[-1], df['Signal'].iloc[-1]
        if rsi > 70:
            st.warning("과매수 상태입니다 (RSI > 70) → 매도 유의")
        elif rsi < 30:
            st.success("과매도 상태입니다 (RSI < 30) → 매수 기회")
        else:
            st.info("RSI 중립 → 관망 추천")

        if macd > signal:
            st.success("MACD 상승 신호")
        else:
            st.warning("MACD 하락 신호")

        # 뉴스
        st.markdown("### 📰 관련 뉴스")
        news = fetch_news_headlines(selected_name)
        if news:
            for title, link in news:
                st.markdown(f"- [{title}]({link})")
        else:
            st.info("관련 뉴스 없음")

# --- 투자 성향 상위 10 종목 ---
st.markdown("---")
st.markdown(f"## 💡 {investment_style} 투자 성향별 상위 10개 종목")
scored = pd.read_csv("filtered_stocks.csv")
scored["score"] = scored["score"].astype(float)
top10 = scored.sort_values("score", ascending=False).head(10)
st.dataframe(top10[['종목명', '종목코드', 'score', '현재가', 'PER', 'PBR', 'ROE', '배당률']])

# --- 수동 업데이트 ---
st.sidebar.markdown("---")
st.sidebar.markdown("🛠️ 수동 데이터 업데이트")
if st.sidebar.button("🔄 Update Now"):
    with st.spinner("업데이트 중..."):
        try:
            update_main()
            st.cache_data.clear()
            st.success("업데이트 완료!")
        except Exception as e:
            st.error("업데이트 실패")
            st.exception(e)

# --- 마지막 업데이트 표시 ---
try:
    last_time = os.path.getmtime("filtered_stocks.csv")
    st.sidebar.caption(f"📅 마지막 업데이트: {datetime.fromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')}")
except:
    st.sidebar.warning("CSV 없음")
