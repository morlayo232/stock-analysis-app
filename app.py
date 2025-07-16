# app.py

import streamlit as st
import pandas as pd
import numpy as np
from update_stock_database import update_single_stock, update_database
from modules.chart_utils import plot_price_rsi_macd, plot_bollinger_band
from modules.fetch_news import fetch_google_news
from modules.score_utils import finalize_scores
from modules.fetch_price import fetch_price

# 헤더 및 타이틀 설정
st.title("주식 투자 분석 도구")

# 전략 선택 옵션
strategy = st.sidebar.selectbox("투자 성향 선택", ("공격형", "안정형", "배당형"))
st.sidebar.markdown("### 투자 성향에 맞는 전략을 선택하세요.")
st.sidebar.info("투자 성향에 대한 간단한 설명 ❓")

# 종목 검색 및 갱신 버튼
stock_code = st.sidebar.text_input("종목 코드 입력 (예: 005930)", "")

# 데이터 갱신 버튼
if st.sidebar.button('개별 종목 갱신'):
    if stock_code:
        try:
            st.write(f"갱신 중: {stock_code}")
            update_single_stock(stock_code)
            st.success(f"갱신 완료: {stock_code}")
        except Exception as e:
            st.error(f"갱신 오류: {e}")
    else:
        st.error("종목 코드를 입력하세요.")

# 종목 선택
selected_stock = st.selectbox("종목을 선택하세요", ["삼성전자", "LG전자", "SK하이닉스"])

# 재무 정보 출력
st.subheader(f"{selected_stock}의 재무 정보")
df_price = fetch_price(selected_stock)  # 예시로 단순하게 선택

if not df_price.empty:
    st.write(df_price)

# 차트 및 기술적 분석 출력
st.subheader("주식 차트 & 기술적 지표")
plot_price_rsi_macd(df_price)
plot_bollinger_band(df_price)

# 뉴스 출력
st.subheader("최근 뉴스")
news = fetch_google_news(selected_stock, max_items=5)
st.write("\n".join(news))

# 추천 매수/매도 가격
st.subheader("추천 매수/매도 가격")
score_df = finalize_scores(df_price, style=strategy)
st.write(score_df[["종목명", "추천매수", "추천매도", "score"]])

# 알림/경고
if df_price["PER"].isna().any() or df_price["PBR"].isna().any():
    st.warning("재무 데이터에 결측값이 있습니다. 일부 정보가 표시되지 않을 수 있습니다.")
