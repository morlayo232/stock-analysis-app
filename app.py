import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

from modules.score_utils          import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.calculate_indicators import calc_ema
from modules.chart_utils         import plot_price_rsi_macd_bb
from update_stock_database       import update_database, update_single_stock

# 추천가 계산 (EMA20 + PER/PBR 보정)
def compute_recommendations(row, df_price=None):
    price = float(row["현재가"])
    per   = float(row.get("PER", np.nan))
    pbr   = float(row.get("PBR", np.nan))

    val_adj = 1.0 - 0.05 * (per < 10) + 0.05 * (per > 25)
    pb_adj  = 1.0 + 0.05 * (pbr > 2)
    ta_adj  = 1.0
    if df_price is not None and "종가" in df_price.columns:
        ema20 = calc_ema(df_price, window=20, col="종가").iloc[-1]
        ta_adj += 0.03 if price > ema20 else -0.03

    buy_mul  = val_adj * ta_adj * 0.98
    sell_mul = pb_adj  * ta_adj * 1.02

    buy_price  = round(price * buy_mul / 10) * 10
    sell_price = round(price * sell_mul / 10) * 10

    return int(buy_price), int(sell_price)

st.set_page_config(page_title="투자 매니저", layout="wide")

# 종목 리스트 로드
@st.cache_data
def load_list(path="initial_krx_list_test.csv"):
    if not os.path.exists(path):
        return [], {}
    df0 = pd.read_csv(path, dtype=str)
    df0["종목코드"] = df0["종목코드"].str.zfill(6)
    opts = df0["종목명"] + " (" + df0["종목코드"] + ")"
    return opts.tolist(), dict(zip(opts, df0["종목코드"]))

options, code_map = load_list()

# UI: 검색
st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
q = st.text_input("종목명 또는 코드 입력")
matches = [o for o in options if q in o] if q else options
selected = st.selectbox("", matches) if matches else ""
code = code_map.get(selected, "")
name = selected.split(" (")[0] if selected else ""

# 업데이트 버튼
if code:
    st.markdown(f"**조회: {name} ({code})**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 개별갱신"):
            update_single_stock(code)
            st.experimental_rerun()
    with c2:
        if st.button("🌐 전체갱신"):
            update_database()
            st.experimental_rerun()

# 데이터 로드
CSV = "filtered_stocks.csv"
df_all = (
    pd.read_csv(CSV, dtype={"종목코드":str})
      .assign(종목코드=lambda d: d["종목코드"].str.zfill(6))
    if os.path.exists(CSV) else pd.DataFrame()
)

# 최신 재무
st.markdown("### 📊 최신 재무 정보")
row = (
    df_all[df_all["종목코드"] == code].iloc[0]
    if code and not df_all.empty and code in df_all["종목코드"].values
    else None
)
fields = ["PER","PBR","EPS","BPS","배당률","score","급등확률"]
if isinstance(row, pd.Series):
    cols = st.columns(2)
    for i,f in enumerate(fields):
        with cols[i%2]:
            st.metric(
                label=f,
                value=f"{row[f]:,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f, "")
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 차트
st.markdown("### 📈 주가 및 기술지표 차트")
pf = f"price_{code}.csv"
if code and os.path.exists(pf):
    df_price = pd.read_csv(pf, index_col=0, parse_dates=True)
    fig, rsi, macd = plot_price_rsi_macd_bb(df_price)
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(rsi, use_container_width=True)
    st.plotly_chart(macd, use_container_width=True)
else:
    st.info("차트 데이터가 없습니다.")

# 추천가
st.markdown("### 📌 추천 매수/매도가")
if isinstance(row, pd.Series):
    df_price = pd.read_csv(pf, index_col=0, parse_dates=True) if os.path.exists(pf) else None
    buy, sell = compute_recommendations(row, df_price)
    st.metric("추천 매수가", f"{buy:,} 원")
    st.metric("추천 매도가", f"{sell:,} 원")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 투자 전략
st.markdown("### 📋 종목 평가 / 투자 전략")
if isinstance(row, pd.Series):
    advice = []
    if row["PER"] > 20:
        advice.append("PER 20 이상: 고평가 우려")
    elif row["PER"] < 7:
        advice.append("PER 7 미만: 저평가 매수 기회")
    else:
        advice.append("PER 적정 수준")

    if row["PBR"] < 1:
        advice.append("PBR 1 미만: 저평가 구간")
    elif row["PBR"] > 2:
        advice.append("PBR 2 이상: 고평가 가능성")

    if row["배당률"] > 3:
        advice.append("배당률 3% 이상: 배당투자 적합")

    if row["score"] > 1:
        advice.append("높은 투자매력 점수: 적극 매수")
    elif row["score"] < 0:
        advice.append("낮은 점수: 보수적 접근")

    if row["급등확률"] > 1:
        advice.append("단기 급등 시그널 포착")

    for a in advice:
        st.write(f"• {a}")
    st.write("_※ 본 평가는 참고용입니다._")
else:
    st.write("정보가 없습니다.")

# 최신 뉴스
st.markdown("### 📰 최신 뉴스")
try:
    from modules.fetch_news import fetch_google_news
    news = fetch_google_news(name) if name else []
    if news:
        for n in news: st.markdown(f"- {n}")
    else:
        st.info("관련 뉴스가 없습니다.")
except:
    st.info("뉴스 로드 오류")

# TOP10
st.markdown("## 🔥 투자성향별 TOP10 & 급등 예상 종목")
style = st.selectbox("투자성향", ["aggressive","stable","dividend"],
                     format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x])
if not df_all.empty:
    scored = finalize_scores(df_all.copy(), style=style)
    scored["신뢰등급"] = scored.apply(assess_reliability, axis=1)
    st.subheader("🔹 투자 매력점수 TOP10")
    st.dataframe(scored.nlargest(10,"score"), use_container_width=True)
    st.subheader("🔥 급등 예상 TOP10")
    st.dataframe(scored.nlargest(10,"급등확률"), use_container_width=True)
else:
    st.info("TOP10 데이터가 없습니다.")

# 공식·설명
with st.expander("📊 공식 및 의미 설명"):
    st.markdown(
      "- **투자점수**: PER·PBR·EPS·BPS·배당률·거래량 가중합\n"
      "- **급등확률**: 단기 수급·저PER·변동성 반영\n"
      "- **추천가**: PER·PBR·EMA20 기반 자동 계산"
    )

# 로고
st.markdown(
    "<div style='text-align:center'>"
    "<img src='https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png' width='260'/>"
    "</div>",
    unsafe_allow_html=True
)
