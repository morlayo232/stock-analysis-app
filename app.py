# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime
from modules import calculate_indicators, calc_investment_score, TOOLTIP_EXPLANATIONS, load_stock_price
from charts import plot_stock_chart, plot_rsi_macd
from update_stock_database import main as update_main
from news import fetch_news_headlines

st.set_page_config(page_title="한국 주식 분석", layout="wide")

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

@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv('filtered_stocks.csv', dtype=str)

filtered_stocks = load_filtered_stocks()

def search_stocks(keyword, stocks_df):
    if keyword.strip() == '':
        return pd.DataFrame()
    return stocks_df[stocks_df['종목명'].str.contains(keyword, case=False)]

st.title("📊 한국 주식 시장 투자 매력도 분석")

investment_style = st.sidebar.radio("투자 성향 선택", ['공격적', '안정적', '배당형'], key="style")
search_keyword = st.sidebar.text_input("종목명 검색", key="search")
search_results = search_stocks(search_keyword, filtered_stocks)
selected_ticker = None
selected_name = None

if not search_results.empty:
    selection = st.sidebar.selectbox("검색된 종목 선택",
                                     options=search_results['종목명'] + ' (' + search_results['종목코드'] + ')',
                                     key="selectbox")
    selected_name = selection.split(' (')[0]
    selected_ticker = selection.split('(')[1].strip(')')

st.sidebar.markdown("### ⭐ 즐겨찾기")
for fav_code in favorites:
    fav_name = filtered_stocks[filtered_stocks['종목코드'] == fav_code]['종목명'].values
    if len(fav_name) > 0:
        st.sidebar.write(f"- {fav_name[0]} ({fav_code})")

if selected_ticker:
    if st.sidebar.button("즐겨찾기 추가", key="fav_add"):
        if selected_ticker not in favorites:
            favorites.append(selected_ticker)
            save_favorites(favorites)
            st.sidebar.success("즐겨찾기에 추가했습니다.")

# 🔍 종목 상세 분석
if selected_ticker:
    df = load_stock_price(selected_ticker)
    if df.empty:
        st.warning("📉 주가 데이터를 불러올 수 없습니다.")
    else:
        df = calculate_indicators(df)
        score = calc_investment_score(df, investment_style)

        st.subheader(f"📌 선택 종목: {selected_name} ({selected_ticker})")
        st.markdown(f"투자 성향: **{investment_style}** / 투자 매력 점수: **{score:.2f}**")

        st.plotly_chart(plot_stock_chart(df), use_container_width=True)
        st.plotly_chart(plot_rsi_macd(df), use_container_width=True)

        golden_cross = df[(df['EMA5'] > df['EMA20']) & (df['EMA5'].shift(1) <= df['EMA20'].shift(1))]
        dead_cross = df[(df['EMA5'] < df['EMA20']) & (df['EMA5'].shift(1) >= df['EMA20'].shift(1))]

        st.markdown("### 💰 추천 매수/매도 가격")
        if not golden_cross.empty:
            st.success(f"✅ 최근 골든크로스 매수 가격: {golden_cross['Close'].iloc[-1]:,.2f}")
        if not dead_cross.empty:
            st.warning(f"⚠️ 최근 데드크로스 매도 가격: {dead_cross['Close'].iloc[-1]:,.2f}")

        st.markdown("### 🧭 투자 판단 요약")
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        signal = df['Signal'].iloc[-1]

        if rsi > 70:
            st.warning("RSI 70 이상 → 과매수 구간")
        elif rsi < 30:
            st.success("RSI 30 이하 → 과매도 구간")
        else:
            st.info("RSI 중립 구간")

        if macd > signal:
            st.success("MACD > Signal → 상승 전환")
        else:
            st.warning("MACD < Signal → 하락 전환")

        st.markdown("### 📰 관련 뉴스")
        news = fetch_news_headlines(selected_name)
        if news:
            for title, link in news:
                st.markdown(f"- [{title}]({link})")
        else:
            st.info("뉴스 데이터를 불러올 수 없습니다.")

# 📈 투자 성향별 상위 10개 종목 추천
st.markdown("## 🔝 투자 성향별 추천 TOP 10")
try:
    numeric_df = filtered_stocks.copy()
    numeric_df[['score']] = numeric_df[['score']].astype(float)
    top10 = numeric_df.sort_values(by='score', ascending=False).head(10)
    st.dataframe(top10[['종목명', '종목코드', '시장구분', 'score']])
except Exception as e:
    st.warning("추천 종목을 표시할 수 없습니다.")
    st.exception(e)

# ⟳ 수동 업데이트
st.sidebar.markdown("### 🔁 수동 데이터 갱신")
if st.sidebar.button("Update Now", key="update_button"):
    with st.spinner("업데이트 중입니다..."):
        try:
            before_df = filtered_stocks.copy()
            update_main()
            st.cache_data.clear()
            filtered_stocks = load_filtered_stocks()

            diff = pd.concat([before_df, filtered_stocks]).drop_duplicates(keep=False)
            st.success("업데이트 완료.")
            if not diff.empty:
                st.info(f"🔄 변경된 종목: {len(diff)}개")
                st.dataframe(diff)
        except Exception as e:
            st.error("업데이트 실패:")
            st.exception(e)

# ⏰ 마지막 업데이트 시간
try:
    last_modified = datetime.fromtimestamp(os.path.getmtime("filtered_stocks.csv"))
    st.sidebar.markdown(f"**🕒 마지막 업데이트:** {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
except:
    st.sidebar.warning("CSV 파일 정보를 불러올 수 없습니다.")

# ℹ️ 기술 지표 설명
with st.sidebar.expander("🧠 기술 지표 설명"):
    for key, desc in TOOLTIP_EXPLANATIONS.items():
        st.markdown(f"**{key}**: {desc}")
