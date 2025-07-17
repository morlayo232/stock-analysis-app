import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.chart_utils import plot_price_rsi_macd_bb
from update_stock_database import update_database, update_single_stock

st.set_page_config(page_title="투자 매니저", layout="wide")

# 1. 종목 검색창(자동완성)
@st.cache_data
def load_all_stocklist():
    if os.path.exists("initial_stock_list.csv"):
        df = pd.read_csv("initial_stock_list.csv")
        names = df["종목명"].astype(str).tolist()
        codes = df["종목코드"].astype(str).tolist()
        options = [f"{n} ({c})" for n, c in zip(names, codes)]
        code_map = dict(zip(options, codes))
        return options, code_map
    return [], {}

options, code_map = load_all_stocklist()

st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
selected = st.text_input("종목명 또는 코드 입력", "", key="searchbox", help="종목명 일부만 입력해도 자동완성 지원")
autocomplete = [o for o in options if selected in o] if selected else options
selected_option = None
if autocomplete:
    selected_option = st.selectbox("", autocomplete, key="autofill")
    code = code_map[selected_option]
    name = selected_option.split(" (")[0]
else:
    code, name = "", ""

if code:
    st.markdown(f"## **{name} ({code})**")
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🔄 개별갱신"):
            update_single_stock(code)
            st.success("개별 종목 데이터가 갱신되었습니다.")
            st.rerun()
    with col_btn2:
        if st.button("🌐 전체갱신"):
            with st.spinner("전체 데이터 갱신중..."):
                update_database()
                st.success("전체 데이터 갱신 완료!")
                st.rerun()

# 2. 최신 재무정보 2열+툴팁
st.markdown("### <img src='https://img.icons8.com/color/48/bar-chart' width='32' style='vertical-align:middle'/> 최신 재무 정보", unsafe_allow_html=True)
df_all = pd.read_csv("filtered_stocks.csv") if os.path.exists("filtered_stocks.csv") else pd.DataFrame()
row = df_all[df_all["종목코드"] == int(code)].iloc[0] if (code and not df_all.empty and (df_all["종목코드"] == int(code)).any()) else None
fields = ["PER", "PBR", "EPS", "BPS", "배당률", "score", "급등확률"]
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i%2]:
            st.metric(
                f"{f} <span style='font-size:13px;' title='{FIELD_EXPLAIN.get(f, '')}'>❓</span>",
                f"{row[f]:,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f, ""), label_visibility="visible", 
                key=f"metric_{f}"
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 3. 주가/지표 차트
st.markdown("### <img src='https://img.icons8.com/color/48/line-chart' width='32' style='vertical-align:middle'/> 주가 및 기술지표 차트", unsafe_allow_html=True)
try:
    price_file = f"price_{code}.csv"
    if os.path.exists(price_file):
        df_price = pd.read_csv(price_file)
        fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_rsi, use_container_width=True)
        st.plotly_chart(fig_macd, use_container_width=True)
    else:
        st.info("차트 데이터가 부족합니다.")
except Exception:
    st.info("차트 데이터가 부족합니다.")

# 4. 추천 매수가/매도가(차트 바로 아래)
st.markdown("### 📌 추천 매수/매도가")
if row is not None and "추천매수가" in row and "추천매도가" in row:
    st.write(f"추천 매수가: {row['추천매수가']}, 추천 매도가: {row['추천매도가']}")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 5. 종목평가/투자전략(전문가 스타일)
st.markdown("### 📋 종목 평가 / 투자 전략")
if row is not None:
    advices = []
    if row["PER"] > 15:
        advices.append("PER이 높아 성장 기대는 있으나 고평가 구간일 수 있습니다. 수익률 변동에 유의하세요.")
    if row["PBR"] < 1:
        advices.append("PBR 1 미만은 저평가 신호로 장기분할매수, 중장기 투자가치 있음.")
    if row["배당률"] > 3:
        advices.append("배당수익률이 높아 보수적 투자에도 적합합니다.")
    if row["급등확률"] > 0.2:
        advices.append("단기 거래량 급증 신호, 단기 급등·급락 리스크 함께 체크.")
    if not advices:
        advices.append("☑ 시장 평균수준, 분할매수 또는 모니터링 권장")
    for adv in advices:
        st.write(f"• {adv}")
else:
    st.write("정보 부족")

# 6. 관련뉴스
st.markdown("### 📰 최신 뉴스")
try:
    from modules.fetch_news import fetch_google_news
    newslist = fetch_google_news(name) if name else []
    if newslist:
        for n in newslist:
            st.markdown(f"- {n}")
    else:
        st.info("관련 뉴스 데이터가 부족합니다.")
except:
    st.info("관련 뉴스 데이터가 부족합니다.")

# 7. 투자성향/급등 top10 표/선택
st.markdown("## 투자 성향별 TOP10 및 급등 예상 종목")
style = st.selectbox("투자성향", ["aggressive", "stable", "dividend"], format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}.get(x,x))
scored_df = finalize_scores(df_all.copy(), style=style) if not df_all.empty else pd.DataFrame()
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1) if not scored_df.empty else ""
st.subheader("투자 매력점수 TOP10")
if not scored_df.empty:
    top10 = scored_df.sort_values("score", ascending=False).head(10)
    st.dataframe(top10, use_container_width=True)
else:
    st.info("데이터 부족")

st.subheader("🔥 급등 예상종목 TOP10")
if not scored_df.empty and "급등확률" in scored_df.columns:
    top_jump = scored_df.sort_values("급등확률", ascending=False).head(10)
    st.dataframe(top_jump, use_container_width=True)
else:
    st.info("데이터 부족")

with st.expander("📊 투자점수·급등확률 공식/의미 설명(클릭)"):
    st.markdown("""
    - 투자점수: PER, PBR, EPS, BPS, 배당률, 거래량 등 실적·밸류·수급 반영 가중합  
    - 급등확률: 단기 거래량 급증, 저PER, 단기 변동성 등 반영  
    - 각 성향별로 가중치(공격형: 수익/수급↑, 안정형: 저PBR/PER, 배당형: 배당↑) 자동 조정  
    """)

# 9. 로고(중앙, 크기 0.6배)
st.markdown('<div style="text-align:center;"><img src="https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png" width="220"/></div>', unsafe_allow_html=True)
