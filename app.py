import streamlit as st
import yfinance as yf
import pandas as pd
import json
import subprocess
import os
from datetime import datetime
from modules import calculate_indicators, calc_investment_score, TOOLTIP_EXPLANATIONS, load_stock_price
from charts import plot_stock_chart, plot_rsi_macd
from news import fetch_news_keywords

st.set_page_config(page_title="한국 주식 분석", layout="wide")

# 즐겨찾기 로드/저장
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

favorites = load_favorites()

# 필터링된 종목 데이터 로드
@st.cache_data(ttl=86400)
def load_filtered_stocks():
    df = pd.read_csv('filtered_stocks.csv', dtype=str)
    return df

filtered_stocks = load_filtered_stocks()

# 종목 검색 함수
def search_stocks(keyword, stocks_df):
    if keyword.strip() == '':
        return pd.DataFrame()
    return stocks_df[stocks_df['종목명'].str.contains(keyword, case=False)]

st.title("📈 한국 주식 시장 투자 매력도 분석")

# 사이드바 UI
investment_style = st.sidebar.radio("투자 성향 선택", ['공격적', '안정적', '배당형'])
search_keyword = st.sidebar.text_input("종목명 검색")
search_results = search_stocks(search_keyword, filtered_stocks)
selected_ticker = None
selected_name = None
selected_market = None

if not search_results.empty:
    selection = st.sidebar.selectbox("검색된 종목 선택", options=search_results['종목명'] + ' (' + search_results['종목코드'] + ')')
    selected_name = selection.split(' (')[0]
    selected_ticker = selection.split('(')[1].strip(')')
    selected_market = filtered_stocks[filtered_stocks['종목코드'] == selected_ticker]['시장구분'].values[0]

# 즐겨찾기 표시 및 추가 기능
st.sidebar.markdown("### ⭐ 즐겨찾기")
for fav_code in favorites:
    fav_row = filtered_stocks[filtered_stocks['종목코드'] == fav_code]
    if not fav_row.empty:
        name = fav_row['종목명'].values[0]
        st.sidebar.write(f"- {name} ({fav_code})")

if selected_ticker:
    if st.sidebar.button("⭐ 즐겨찾기 추가"):
        if selected_ticker not in favorites:
            favorites.append(selected_ticker)
            save_favorites(favorites)
            st.sidebar.success("추가 완료!")

# 선택한 종목 주가 데이터 로드 및 분석
if selected_ticker:
    ticker_yf = selected_ticker + (".KS" if selected_market == "코스피" else ".KQ")
    df = load_stock_price(ticker_yf)
    if df.empty:
        st.warning("❌ 주가 데이터를 불러올 수 없습니다.")
    else:
        df = calculate_indicators(df)
        score = calc_investment_score(df, investment_style)

        st.subheader(f"선택 종목: {selected_name} ({selected_ticker})")
        st.markdown(f"🧭 투자 성향: **{investment_style}** / 🧮 투자 점수: **{score:.2f}**")

        # 차트 출력
        st.plotly_chart(plot_stock_chart(df), use_container_width=True)
        st.plotly_chart(plot_rsi_macd(df), use_container_width=True)

        # 추천 매수/매도 가격
        golden_cross = df[(df['EMA5'] > df['EMA20']) & (df['EMA5'].shift(1) <= df['EMA20'].shift(1))]
        dead_cross = df[(df['EMA5'] < df['EMA20']) & (df['EMA5'].shift(1) >= df['EMA20'].shift(1))]
        st.markdown("### 💰 추천 매수/매도 가격")
        if not golden_cross.empty:
            buy_price = golden_cross['Close'].iloc[-1]
            st.success(f"🟢 최근 골든크로스 매수 가격: {buy_price:.2f}")
        if not dead_cross.empty:
            sell_price = dead_cross['Close'].iloc[-1]
            st.warning(f"🔴 최근 데드크로스 매도 가격: {sell_price:.2f}")

        # 투자 판단 요약
        st.markdown("### 📌 투자 판단 요약")
        if df['RSI'].iloc[-1] > 70:
            st.warning("⚠️ RSI 70 이상 → 과매수 구간입니다.")
        elif df['RSI'].iloc[-1] < 30:
            st.success("✅ RSI 30 이하 → 매수 유망 구간입니다.")
        else:
            st.info("ℹ️ RSI 중립 → 관망 권장")

        if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]:
            st.success("📈 MACD > Signal → 상승 전환 시그널")
        else:
            st.warning("📉 MACD < Signal → 하락 주의")

        # 뉴스 키워드 요약
        st.markdown("### 📰 뉴스 키워드 요약")
        keywords = fetch_news_keywords(selected_name)
        if keywords:
            st.info(" | ".join(keywords))
        else:
            st.warning("최근 뉴스 키워드를 찾을 수 없습니다.")

# 기술 지표 설명
with st.sidebar.expander("📘 기술 지표 설명"):
    for key, desc in TOOLTIP_EXPLANATIONS.items():
        st.markdown(f"**{key}**: {desc}")

# 수동 데이터 업데이트
st.sidebar.markdown("### ⟳ 수동 데이터 갱신")
if st.sidebar.button("Update Now"):
    with st.spinner("업데이트 중입니다..."):
        result = subprocess.run(["python", "update_stock_database.py"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("업데이트 성공 ✅")
        else:
            st.error("업데이트 실패 ❌")
            st.code(result.stderr)

# 마지막 업데이트 시간 표시
try:
    last_updated = datetime.fromtimestamp(os.path.getmtime("filtered_stocks.csv"))
    st.sidebar.markdown(f"**📅 마지막 갱신:** {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
except:
    st.sidebar.warning("CSV 파일을 찾을 수 없습니다.")
# app.py 마지막 부분에 추가

from update_stock_database import main as update_main

if st.sidebar.button("Update Now"):
    with st.spinner("업데이트 중입니다... 잠시만 기다려 주세요."):
        try:
            update_main()
            st.success("업데이트가 성공적으로 완료되었습니다.")
        except Exception as e:
            st.error("업데이트 실패:")
            st.exception(e)
