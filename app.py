import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from modules.score_utils import FIELD_EXPLAIN, assess_reliability
from modules.chart_utils import plot_price_rsi_macd_bb
from modules.fetch_news import fetch_google_news

st.set_page_config(page_title="투자 매니저", layout="wide")

@st.cache_data
def load_filtered_data():
    return pd.read_csv("filtered_stocks.csv")

df = load_filtered_data()

st.title("투자 매니저")

# --- 종목 검색 + 선택 ---
query = st.text_input("🔍 종목명 또는 코드 입력", "")
filtered = df[df["종목명"].str.contains(query, na=False) | df["종목코드"].astype(str).str.contains(query)]
if not filtered.empty:
    row = filtered.iloc[0]
else:
    row = df.iloc[0]

# --- 조회 종목명 + 개별/전체 갱신 버튼 ---
c1, c2, c3 = st.columns([2,1,1])
with c1:
    st.markdown(f"### {row['종목명']} ({row['종목코드']})")
with c2:
    if st.button("↻ 개별갱신"):
        st.info("개별갱신 실행(여기서 update_single_stock 연결)")
with c3:
    if st.button("🌐 전체갱신"):
        st.info("전체갱신 실행(여기서 update_database 연결)")

# --- 2열 재무정보(호버 설명) ---
colA, colB = st.columns(2)
f1 = ["PER", "EPS", "score"]
f2 = ["PBR", "BPS", "배당률"]
for i in range(3):
    with colA:
        f = f1[i]
        st.metric(f"{f} ❓", f"{row[f]}", help=FIELD_EXPLAIN.get(f, ""))
    with colB:
        f = f2[i]
        st.metric(f"{f} ❓", f"{row[f]}", help=FIELD_EXPLAIN.get(f, ""))

st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {assess_reliability(row)}")

# --- 차트 (종가/EMA/볼린저/RSI/MACD) ---
st.subheader("📈 주가 및 기술지표 차트")
try:
    from modules.load_price import load_price_history
    price_df = load_price_history(row["종목코드"])
    if price_df is not None and not price_df.empty:
        price_df = price_df.copy()
        # 볼린저밴드 계산(20, 2)
        price_df["MA20"] = price_df["종가"].rolling(20).mean()
        price_df["STD20"] = price_df["종가"].rolling(20).std()
        price_df["BB_high"] = price_df["MA20"] + 2*price_df["STD20"]
        price_df["BB_low"] = price_df["MA20"] - 2*price_df["STD20"]
        fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(price_df)
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_rsi, use_container_width=True)
        st.plotly_chart(fig_macd, use_container_width=True)
        with st.expander("💡 차트와 지표 해설(초보용)"):
            st.markdown("""
- **종가/EMA**: 단기·중기 추세 전환, 타이밍 참고 (EMA20 돌파 주목)
- **볼린저밴드**: BB_low 하단 터치 후 반등(저점), BB_high 상단 돌파 후 조정(고점) 주의
- **RSI**: 30↓ 과매도, 70↑ 과매수(단기 반등/과열 신호)
- **MACD**: MACD > Signal(매수), < Signal(매도), 0선 전환 체크
            """)
    else:
        st.info("차트 데이터가 부족합니다.")
except Exception as e:
    st.warning(f"차트 로딩 에러: {e}")

# --- 추천 매수/매도가 ---
st.subheader("📌 추천 매수/매도가")
try:
    price_df_recent = price_df.tail(5)
    # 예시: EMA20 아래 + RSI < 35 + MACD 골든 → 매수
    buy_cond = (
        (price_df_recent["종가"] < price_df_recent["EMA20"]) &
        (price_df_recent["RSI"] < 35) &
        (price_df_recent["MACD"] > price_df_recent["Signal"])
    )
    sell_cond = (
        (price_df_recent["종가"] > price_df_recent["EMA20"]) &
        (price_df_recent["RSI"] > 65) &
        (price_df_recent["MACD"] < price_df_recent["Signal"])
    )
    buy_price = price_df_recent.loc[buy_cond, "종가"].min() if buy_cond.any() else None
    sell_price = price_df_recent.loc[sell_cond, "종가"].max() if sell_cond.any() else None
    col1, col2 = st.columns(2)
    with col1:
        st.metric("추천 매수가", f"{buy_price:,.0f}원" if buy_price else "조건 미충족")
    with col2:
        st.metric("추천 매도가", f"{sell_price:,.0f}원" if sell_price else "조건 미충족")
except Exception:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# --- 종목 평가 및 투자 전략 (전문가 설명) ---
st.subheader("📋 종목 평가 / 투자 전략")
eval_lines = []
try:
    per = float(row["PER"])
    pbr = float(row["PBR"])
    eps = float(row["EPS"])
    bps = float(row["BPS"])
    div = float(row["배당률"])
    score = float(row["score"])
    급등확률 = float(row["급등확률"])

    if per < 7:
        eval_lines.append("✔️ PER 7 미만: 저평가 구간, 실적 지속시 매력")
    elif per > 20:
        eval_lines.append("⚠️ PER 20 초과: 고평가 유의(성장·미래 기대 확인 필요)")
    if pbr < 1:
        eval_lines.append("✔️ PBR 1 미만: 순자산가치 대비 저평가")
    if div >= 3:
        eval_lines.append("💰 배당률 3%↑: 배당투자자에게 우수")
    if eps < 0:
        eval_lines.append("🔴 EPS<0: 최근 적자, 재무점검 필요")
    if 급등확률 > 1.5:
        eval_lines.append("🚀 최근 거래량/변동성 급증, 단기 급등 신호")
    if score > df["score"].quantile(0.8):
        eval_lines.append("✅ 종합 진단: 투자매력도 상위권, 적극적 매수관심")
    elif score < df["score"].quantile(0.2):
        eval_lines.append("❌ 투자매력 하위권, 보수적 접근 권장")
    else:
        eval_lines.append("☑️ 시장 평균수준, 분할매수 또는 모니터링")
    st.markdown("\n".join(f"- {line}" for line in eval_lines))
except Exception as e:
    st.info(f"데이터 부족/분석불가: {e}")

# --- 최신 뉴스 ---
st.subheader("📰 최신 뉴스")
try:
    news_list = fetch_google_news(row["종목명"])
    if news_list:
        for n in news_list:
            st.markdown(f"- {n}")
    else:
        st.info("관련 뉴스 없음")
except Exception:
    st.info("뉴스 수집 불가")

# --- TOP10, 급등 TOP10 ---
st.subheader("투자 매력점수 TOP10")
st.dataframe(df.sort_values("score", ascending=False).head(10), use_container_width=True)

st.subheader("🔥 급등 예상종목 TOP10")
st.dataframe(df.sort_values("급등확률", ascending=False).head(10), use_container_width=True)

with st.expander("📊 투자점수·급등확률 공식/의미 설명(클릭)"):
    st.markdown("""
- **투자매력점수(score)**: PER/PBR/EPS/BPS/배당률/거래량 등 종합 가중 공식  
- **급등확률**: 최근 거래량, 저PER, 변동성 등으로 급등 기대치 산정  
- 공식 및 용어설명은 코드 내 FIELD_EXPLAIN 참고
    """)

st.markdown("---")
st.image("logo_tynex.png", width=180, use_column_width=False)
