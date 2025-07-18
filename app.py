# app.py

import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# 1) 자체 정의 함수 & 모듈 로드
from modules.score_utils           import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.chart_utils           import plot_price_rsi_macd_bb
from update_stock_database         import update_single_stock

# 추천 매수가/매도가 계산 함수
from modules.calculate_indicators  import calc_ema

def compute_recommendations(row, df_price=None):
    price = float(row["현재가"])
    per   = float(row.get("PER", np.nan))
    pbr   = float(row.get("PBR", np.nan))

    # 1) 밸류에이션 보정
    val_adj = 0.95 if per < 10 else (1.05 if per > 25 else 1.0)
    pb_adj  = 1.05 if pbr > 2 else 1.0

    # 2) 기술적 지표 EMA20 보정
    ta_adj = 1.0
    if df_price is not None and "종가" in df_price.columns:
        last_ema = calc_ema(df_price, window=20, col="종가").iloc[-1]
        ta_adj += 0.03 if price > last_ema else -0.03

    # 3) 최종 추천가 산출
    buy_mul  = val_adj * ta_adj * 0.98
    sell_mul = pb_adj  * ta_adj * 1.02
    buy_price  = round(price * buy_mul / 10) * 10
    sell_price = round(price * sell_mul / 10) * 10

    return int(buy_price), int(sell_price)

# 2) 페이지 설정
st.set_page_config(page_title="투자 매니저", layout="wide")

# 3) 종목 리스트 로드 (자동완성)
@st.cache_data(show_spinner=False)
def load_stock_list(csv="initial_krx_list.csv"):
    if not os.path.exists(csv):
        return [], {}
    df = pd.read_csv(csv, dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    opts = df["종목명"] + " (" + df["종목코드"] + ")"
    return opts.tolist(), dict(zip(opts, df["종목코드"]))

options, code_map = load_stock_list()

# 4) UI: 제목 및 검색
st.title("📈 투자 매니저")
query = st.text_input("종목명 또는 코드로 검색", "")
matches = [o for o in options if query in o] if query else options
selected = st.selectbox("종목을 선택하세요", matches) if matches else ""
code = code_map.get(selected, "")
name = selected.split(" (")[0] if selected else ""

# 5) 개별 갱신 (세션 내 반영)
if code:
    st.markdown(f"**조회 대상:** {name}  ({code})")
    if st.button("🔄 개별 갱신"):
        update_single_stock(code)
        st.experimental_rerun()

# 6) 전체 데이터 로드
DATA_CSV = "filtered_stocks.csv"
df_all = (
    pd.read_csv(DATA_CSV, dtype=str)
      .assign(종목코드=lambda d: d["종목코드"].str.zfill(6))
      if os.path.exists(DATA_CSV) else pd.DataFrame()
)

# 7) 최신 재무 정보
st.header("🔍 최신 재무 정보")
row = (
    df_all[df_all["종목코드"] == code].iloc[0]
    if code and code in df_all["종목코드"].values else None
)

if row is not None:
    fields = ["PER","PBR","EPS","BPS","배당수익률","score","급등확률"]
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i % 2]:
            st.metric(
                label= f,
                value= f"{float(row[f]):,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f,"")
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} | 신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 8) 주가 및 기술지표 차트
st.header("📊 주가 + 기술지표 차트")
price_file = f"price_{code}.csv"
if row is not None and os.path.exists(price_file):
    df_price = pd.read_csv(price_file, index_col=0, parse_dates=True)
    fig_price, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
    st.plotly_chart(fig_price, use_container_width=True)
    st.plotly_chart(fig_rsi,  use_container_width=True)
    st.plotly_chart(fig_macd, use_container_width=True)
else:
    st.info("차트 데이터가 없습니다.")

# 9) 추천 매수가·매도가
st.header("📌 추천 매수/매도가")
if row is not None:
    df_price = None
    if os.path.exists(price_file):
        tmp = pd.read_csv(price_file, index_col=0, parse_dates=True)
        if "종가" in tmp.columns:
            df_price = tmp
    buy, sell = compute_recommendations(row, df_price)
    st.metric("추천 매수가", f"{buy:,} 원")
    st.metric("추천 매도가", f"{sell:,} 원")
else:
    st.info("추천가 산출을 위한 충분한 데이터가 없습니다.")

# 10) 전문가 수준의 종목 평가 · 투자 전략
st.header("📋 종목 평가 / 투자 전략")
if row is not None:
    advice = []
    # PER
    per = float(row["PER"])
    if per > 20:
        advice.append("• PER이 20 이상으로 시장 대비 고평가 가능성, 실적 모멘텀 확인이 필요합니다.")
    elif per < 7:
        advice.append("• PER이 7 미만인 저평가 구간, 실적 개선 기대주라면 저점 매수 기회를 탐색하세요.")
    else:
        advice.append("• PER이 시장 평균 수준, 밸류에이션 부담이 크지 않습니다.")
    # PBR
    pbr = float(row["PBR"])
    if pbr < 1:
        advice.append("• PBR 1 미만: 자산 대비 주가 저평가, 안전마진 확보 구간입니다.")
    elif pbr > 2:
        advice.append("• PBR 2 이상: 성장 기대치 반영된 고평가 상태일 수 있습니다.")
    # 배당
    div_yield = float(row["배당수익률"])
    if div_yield > 3:
        advice.append("• 배당수익률 3% 이상: 안정적 현금흐름 투자자에게 매력적입니다.")
    # 점수
    score = float(row["score"])
    if score > 1:
        advice.append("• 투자매력점수가 높아 성장·가치·수급이 균형 잡힌 종목입니다.")
    elif score < 0:
        advice.append("• 투자매력점수가 낮아 보수적 접근 또는 분할매수 전략이 권장됩니다.")
    # 급등확률
    jump = float(row["급등확률"])
    if jump > 0.7:
        advice.append("• 단기 급등 시그널 강함: 거래량·수급 변화 모니터링이 필수입니다.")
    # 종합 멘트
    advice.append("※ 본 분석은 객관적 재무·수급 데이터 기반 참고용입니다. 투자 전 공시·리포트·업황 점검을 권장합니다.")
    for line in advice:
        st.write(line)
else:
    st.write("충분한 데이터가 없어 전략을 제시할 수 없습니다.")

# 11) 최신 뉴스
st.header("📰 최신 뉴스")
try:
    from modules.fetch_news import fetch_google_news
    news = fetch_google_news(name) if name else []
    if news:
        for item in news:
            st.markdown(f"- {item}")
    else:
        st.info("관련 뉴스가 없습니다.")
except:
    st.info("뉴스를 불러오는 중 오류가 발생했습니다.")

# 12) 투자성향별 TOP10 & 급등 예상 종목
st.header("🔥 투자성향별 TOP10 & 급등 예상 종목")
style = st.selectbox("투자 성향", ["aggressive","stable","dividend"],
                     format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x])
if not df_all.empty:
    scored = finalize_scores(df_all.copy(), style=style)
    scored["신뢰등급"] = scored.apply(assess_reliability, axis=1)
    st.subheader("▶ 투자매력점수 TOP10")
    st.dataframe(scored.nlargest(10,"score"), use_container_width=True)
    st.subheader("▶ 급등 예상 TOP10")
    st.dataframe(scored.nlargest(10,"급등확률"), use_container_width=True)
else:
    st.info("TOP10 데이터를 불러올 수 없습니다.")

# 13) 공식 및 설명
with st.expander("📊 공식 및 의미 설명"):
    st.markdown(
        "- **투자매력점수**: Z-스코어 기반 PER·PBR·EPS·BPS·배당률·거래량 반영 가중합\n"
        "- **급등확률**: 단기 거래량 모멘텀, 저PER, 변동성 반영 (0~1)\n"
        "- **추천가**: PER·PBR 가치 보정 + EMA20 기술지표 자동 보정"
    )

# 14) 로고
st.markdown(
    "<div style='text-align:center;margin-top:30px'>"
    "<img src='https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png' "
    "width='260'/></div>",
    unsafe_allow_html=True
)
