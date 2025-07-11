import streamlit as st
import pandas as pd
import json

from modules import (
    load_filtered_data,
    calculate_investment_score,
    get_advice,
    get_yf_ticker  # ✅ yfinance용 종목코드 변환 함수
)
from charts import plot_price_chart, plot_indicators
from news import fetch_news_headlines

# 페이지 설정
st.set_page_config(page_title="📈 한국 주식 투자 매력도 분석", layout="wide")

# 즐겨찾기 로드/저장 함수
def load_favorites():
    try:
        with open("favorites.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_favorites(favs):
    with open("favorites.json", "w") as f:
        json.dump(favs, f, indent=2)

favorites = load_favorites()
data = load_filtered_data()

# 사이드바 - 종목 검색
st.sidebar.title("🔍 종목 검색 및 즐겨찾기")
search = st.sidebar.text_input("종목명 또는 코드 입력")
filtered = data[data["종목명"].str.contains(search, case=False) | data["종목코드"].str.contains(search)]

# 종목 선택
if not filtered.empty:
    selected = st.sidebar.selectbox("종목 선택", filtered["종목명"] + " (" + filtered["종목코드"] + ")")
    ticker = selected.split("(")[-1].strip(")")
    info = data[data["종목코드"] == ticker].iloc[0]
    market = info.get("시장구분", "코스피")  # ✅ "코스피", "코스닥"
    yf_ticker = get_yf_ticker(ticker, market)  # ✅ .KS or .KQ로 변환

    st.title(f"📊 {info['종목명']} ({ticker}) 투자 분석")

    # 기본 지표 표시
    st.markdown(f"**PER**: {info['PER']} / **PBR**: {info['PBR']} / **ROE**: {info.get('ROE', '-')}")
    st.markdown(f"**배당률**: {info['배당률']}% / **3개월 수익률**: {info['3개월수익률']:.2f}%")
    st.markdown(f"**세력지표**: {info['세력점수']} / **기술지표**: {info['기술점수']}")

    # 투자 점수 계산 및 표시
    score = calculate_investment_score(info)
    st.success(f"✅ 종합 투자 매력도 점수: **{score:.2f} / 100**")

    # 주가 차트
    st.plotly_chart(plot_price_chart(yf_ticker), use_container_width=True)
    st.plotly_chart(plot_indicators(yf_ticker), use_container_width=True)

    # 투자 조언
    st.markdown("### 💡 투자 ADVICE")
    st.info(get_advice(info, score))

    # 뉴스 섹션
    st.markdown("### 📰 관련 뉴스 헤드라인")
    news = fetch_news_headlines(info['종목명'])
    for n in news:
        st.markdown(f"- [{n['title']}]({n['link']})")

    # 보유 수익률 분석
    st.markdown("### 📈 보유 수익률 분석")
    avg_price = st.number_input("📥 매입단가 입력", value=0.0)
    if avg_price > 0:
        try:
            profit = (float(info['현재가']) - avg_price) / avg_price * 100
            st.write(f"💹 현재 수익률: **{profit:.2f}%**")
            if profit > 15:
                st.success("🎯 목표 수익 도달 → 익절 고려")
            elif profit < -10:
                st.warning("📉 손실 확대 → 손절 검토")
        except:
            st.warning("현재가 정보 없음")

    # 즐겨찾기 저장
    if st.button("⭐ 즐겨찾기에 추가"):
        favorites[ticker] = float(avg_price)
        save_favorites(favorites)
        st.sidebar.success("즐겨찾기에 추가되었습니다!")

# 수동 업데이트 표시
st.sidebar.markdown("### 🔁 수동 데이터 갱신 (자동은 매일 08:00)")
if st.sidebar.button("데이터 수동 업데이트"):
    st.sidebar.warning("GitHub Actions로 자동 수행됩니다.")
