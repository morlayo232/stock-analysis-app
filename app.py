# app.py

import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.chart_utils import plot_price_rsi_macd_bb
from update_stock_database import update_single_stock

st.set_page_config(page_title="투자 매니저", layout="wide")

# ─── 1) 초기 필터된 데이터 로드 (세션에 1회) ─────────────────────────────
@st.cache_data(show_spinner=False)
def load_filtered():
    path = "filtered_stocks.csv"
    if os.path.exists(path):
        df = pd.read_csv(path, dtype={"종목코드": str})
        df["종목코드"] = df["종목코드"].str.zfill(6)
        return finalize_scores(df)
    return pd.DataFrame()

if "df_all" not in st.session_state:
    st.session_state.df_all = load_filtered()

df_all = st.session_state.df_all

# ─── 2) 종목 리스트 + 자동완성 ─────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_stock_list():
    csv = "initial_krx_list_test.csv"
    if os.path.exists(csv):
        df0 = pd.read_csv(csv, dtype=str)
        df0["종목코드"] = df0["종목코드"].str.zfill(6)
        opts = df0["종목명"] + " (" + df0["종목코드"] + ")"
        return opts.tolist(), dict(zip(opts, df0["종목코드"]))
    return [], {}

options, code_map = load_stock_list()

# ─── 3) UI: 검색창 ────────────────────────────────────────────────────
st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
q = st.text_input("종목명 또는 코드 입력", "", help="일부만 입력해도 자동완성")
matches = [o for o in options if q in o] if q else options
selected = st.selectbox("", matches) if matches else ""
code = code_map.get(selected, "")
name = selected.split(" (")[0] if selected else ""

# ─── 4) 개별 갱신 버튼 ────────────────────────────────────────────────
if code:
    st.markdown(f"**조회 종목: <span style='color:#55b6ff'>{name} ({code})</span>**",
                unsafe_allow_html=True)
    if st.button("🔄 개별 갱신"):
        try:
            st.session_state.df_all = update_single_stock(st.session_state.df_all, code)
            st.success("개별 종목 데이터가 갱신되었습니다.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"갱신 실패: {e}")

# ─── 5) 최신 재무정보 (2열 + 툴팁) ───────────────────────────────────
st.markdown("### 📊 최신 재무 정보")
row = None
if code and not df_all.empty and code in df_all["종목코드"].values:
    row = df_all[df_all["종목코드"] == code].iloc[0]

fields = ["PER","PBR","EPS","BPS","배당률","score","급등확률"]
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i % 2]:
            st.metric(
                label=f,
                value=f"{row[f]:,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f, "")
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# ─── 6) 주가·기술지표 차트 ────────────────────────────────────────────
st.markdown("### 📈 주가 및 기술지표 차트")
if code:
    price_file = f"price_{code}.csv"
    try:
        if os.path.exists(price_file):
            df_price = pd.read_csv(price_file, index_col=0, parse_dates=True)
            fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
            st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(fig_rsi, use_container_width=True)
            st.plotly_chart(fig_macd, use_container_width=True)
        else:
            st.info("차트 데이터가 없습니다.")
    except:
        st.info("차트 로드 오류")

# ─── 7) 추천 매수/매도가 (실시간 계산) ───────────────────────────────
if row is not None:
    st.markdown("### 📌 추천 매수/매도가")
    from modules.calculate_indicators import calc_ema  # 이미 설치된 모듈 경로 확인
    # 간단 예시: 직전 EMA20 기준으로
    df_p = None
    pf = f"price_{code}.csv"
    if os.path.exists(pf):
        tmp = pd.read_csv(pf, index_col=0, parse_dates=True)
        df_p = tmp
    # 여기 원하는 추천가 알고리즘 직접 구현
    st.info("추천가 계산 로직을 여기에 구현하세요.")
else:
    st.markdown("### 📌 추천 매수/매도가")
    st.info("추천가 산출을 위한 데이터가 없습니다.")

# ─── 8) 전문가 평가 / 투자 전략 ─────────────────────────────────────
st.markdown("### 📋 종목 평가 / 투자 전략")
if row is not None:
    adv = []
    # PER 예시
    if row["PER"] > 20:
        adv.append("PER이 20 이상으로 고평가 우려, 실적 모멘텀 확인 권장.")
    elif row["PER"] < 7:
        adv.append("PER 7 미만, 저평가 구간으로 저점 매수 기회.")
    else:
        adv.append("PER 시장 평균 수준으로 적정 밸류에이션.")
    # PBR 예시
    if row["PBR"] < 1:
        adv.append("PBR 1 미만: 안전마진 확보된 저평가.")
    # 급등확률 예시
    if row["급등확률"] > 1:
        adv.append("급등 시그널 포착, 수급 모니터링 필요.")
    for line in adv:
        st.write(f"• {line}")
    st.write("_※ 본 분석은 참고용입니다._")
else:
    st.write("정보가 없습니다.")

# ─── 9) 최신 뉴스 ───────────────────────────────────────────────────
st.markdown("### 📰 최신 뉴스")
from modules.fetch_news import fetch_google_news
if name:
    news = fetch_google_news(name)
    if news:
        for n in news:
            st.markdown(f"- {n}")
    else:
        st.info("관련 뉴스가 없습니다.")
else:
    st.info("종목을 먼저 선택하세요.")

# ─── 10) 투자성향별 · 급등예상 TOP10 ─────────────────────────────────
st.markdown("## 🔥 투자성향별 TOP10 & 급등예상 종목")
style = st.selectbox("투자성향", ["aggressive","stable","dividend"],
                    format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x])
if not df_all.empty:
    scored = finalize_scores(df_all.copy(), style=style)
    scored["신뢰등급"] = scored.apply(assess_reliability, axis=1)
    st.subheader("🔹 투자매력 TOP10")
    st.dataframe(scored.nlargest(10, "score"), use_container_width=True)
    st.subheader("🔥 급등예상 TOP10")
    st.dataframe(scored.nlargest(10, "급등확률"), use_container_width=True)
else:
    st.info("데이터가 없습니다.")

# ─── 11) 공식 설명 & 로고 ────────────────────────────────────────────
with st.expander("📊 공식 및 의미"):
    st.markdown(
        "- 투자점수: PER,PBR,EPS,BPS,배당률,거래량 모멘텀 반영  \n"
        "- 급등확률: 단기 거래량 급증·저PER·변동성 신호 반영"
    )

st.markdown(
    '<div style="text-align:center;"><img src="logo_tynex.png" width="260"/></div>',
    unsafe_allow_html=True
)
