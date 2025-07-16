# app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd
from update_stock_database import update_single_stock, update_database

st.set_page_config(page_title="투자 매니저", layout="wide")

@st.cache_data
def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv")
        expected = [
            "종목명", "종목코드", "현재가", "거래량", "거래량평균20", "PER", "PBR", "EPS", "BPS", "배당률",
            "등락률", "거래량급증", "최고가갱신", "score", "급등점수", "신뢰등급"
        ]
        for col in expected:
            if col not in df.columns:
                df[col] = np.nan
        return df
    except Exception as e:
        st.error(f"filtered_stocks.csv 로딩 실패: {e}")
        return pd.DataFrame(columns=[
            "종목명", "종목코드", "현재가", "거래량", "거래량평균20", "PER", "PBR", "EPS", "BPS", "배당률",
            "등락률", "거래량급증", "최고가갱신", "score", "급등점수", "신뢰등급"
        ])

raw_df = load_filtered_data()
if raw_df.empty:
    st.error("데이터프레임이 비어 있습니다.")
    st.stop()

style = st.sidebar.radio("투자 성향", ["aggressive", "stable", "dividend"], horizontal=True)
scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)

top10 = scored_df.sort_values("score", ascending=False).head(10)
spike10 = scored_df.sort_values("급등점수", ascending=False).head(10)

st.title("투자 매니저")

# TOP10 선택 박스
selected = st.selectbox("TOP10 종목명", top10["종목명"].tolist())
# 급등 종목 빠른 선택
if not spike10.empty:
    st.selectbox("🔥 급등 예상종목 TOP10", spike10["종목명"].tolist(), key="spike10")

# 최신 재무 정보 2열 표시
st.subheader("📊 최신 재무 정보")
try:
    info_row = scored_df[scored_df["종목명"] == selected].iloc[0]
    col1, col2 = st.columns(2)
    with col1:
        st.metric("PER", f"{info_row['PER']:.2f}" if pd.notna(info_row['PER']) else "-")
        st.metric("EPS", f"{int(info_row['EPS']):,}" if pd.notna(info_row['EPS']) else "-")
        st.metric("점수", f"{info_row['score']:.3f}" if pd.notna(info_row['score']) else "-")
    with col2:
        st.metric("PBR", f"{info_row['PBR']:.2f}" if pd.notna(info_row['PBR']) else "-")
        st.metric("BPS", f"{int(info_row['BPS']):,}" if pd.notna(info_row['BPS']) else "-")
        st.metric("배당률(%)", f"{info_row['배당률']:.2f}" if pd.notna(info_row['배당률']) else "-")
except Exception:
    st.info("재무 데이터가 부족합니다.")

# TOP10 표
st.markdown(f"#### 투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[[
    "종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률",
    "등락률", "거래량", "거래량평균20", "거래량급증", "최고가갱신", "score", "급등점수", "신뢰등급"
]])

# 급등 TOP10
st.markdown("#### 🔥 급등 예상 종목 TOP10")
st.dataframe(spike10[[
    "종목명", "종목코드", "현재가", "등락률", "거래량", "거래량급증", "최고가갱신", "급등점수"
]])

# 가격 차트
from modules.fetch_price import fetch_price

df_price = fetch_price(info_row["종목코드"])
if df_price is not None and not df_price.empty:
    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.plotly_chart(fig_rsi, use_container_width=True, config={"displayModeBar": False})
    st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})
else:
    st.warning("주가 데이터가 없습니다.")

# 뉴스
st.markdown("#### 📰 관련 뉴스")
for n in fetch_google_news(info_row["종목명"]):
    st.markdown(f"- {n}")

# 투자전략/종목평가
st.markdown("#### 📋 종목 평가 및 투자 전략(전문가 의견)")
score = info_row['score']
spike_score = info_row.get('급등점수', np.nan)
strategy = []
if pd.notna(info_row['PBR']) and info_row['PBR'] > 2:
    strategy.append("⚠️ [PBR] PBR이 2를 초과합니다.")
if pd.notna(info_row['배당률']) and info_row['배당률'] < 1:
    strategy.append("💡 [배당] 배당수익률이 1% 미만으로 낮습니다.")
if pd.notna(spike_score) and spike_score > 2:
    strategy.append("🔥 [거래] 단기 급등 패턴 및 거래량 급증 신호. 변동성 유의!")
if score < 0:
    strategy.append("❌ [종합진단] 투자 매력도가 낮은 구간입니다. 모니터링 권장.")
elif score > 1.5:
    strategy.append("✅ [종합진단] 투자매력도 상위 구간입니다. 추가 모니터링 후 진입 고려.")
else:
    strategy.append("ℹ️ [종합진단] 무난한 구간입니다. 시장 상황과 함께 참고.")
for s in strategy:
    st.write(f"- {s}")

# 로고 중앙 하단 배치
st.markdown("---")
st.image("logo_tynex.png", width=160, use_column_width=False, caption="TYNEX", output_format="auto")
