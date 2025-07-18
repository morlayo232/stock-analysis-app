# app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# 모듈 임포트
from modules.score_utils      import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.calculate_indicators import calc_ema
from modules.chart_utils     import plot_price_rsi_macd_bb
from update_stock_database   import update_single_stock  # 전체 갱신은 제거하였습니다.

# 페이지 설정
st.set_page_config(page_title="투자 매니저", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# 추천가 계산 함수
def compute_recommendations(row, df_price=None):
    price = float(row["현재가"])
    per   = float(row.get("PER", np.nan))
    pbr   = float(row.get("PBR", np.nan))

    # PER/PBR 보정
    val_adj = 0.95 if per < 10 else 1.05 if per > 25 else 1.0
    pb_adj  = 1.05 if pbr > 2 else 1.0

    # 기술적 지표 EMA20 보정
    ta_adj = 1.0
    if df_price is not None and "종가" in df_price.columns:
        last_ema = calc_ema(df_price, window=20, col="종가").iloc[-1]
        ta_adj += 0.03 if price > last_ema else -0.03

    # 매수가/매도가 산출
    buy_mul  = val_adj * ta_adj * 0.98
    sell_mul = pb_adj  * ta_adj * 1.02
    buy_price  = round(price * buy_mul / 10) * 10
    sell_price = round(price * sell_mul / 10) * 10

    return int(buy_price), int(sell_price)
# ─────────────────────────────────────────────────────────────────────────────

# 1) 종목 리스트 로드 (자동완성)
@st.cache_data(show_spinner=False)
def load_stock_list(csv="initial_krx_list_test.csv"):
    if not pd.io.common.file_exists(csv):
        return [], {}
    df = pd.read_csv(csv, dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    opts = df["종목명"] + " (" + df["종목코드"] + ")"
    return opts.tolist(), dict(zip(opts, df["종목코드"]))

options, code_map = load_stock_list()

# 2) UI: 제목 및 검색
st.title("🔍 종목 검색")
q = st.text_input("종목명 또는 코드 입력", "")
matches = [o for o in options if q in o] if q else options
selected = st.selectbox("목록에서 선택하세요", matches) if matches else ""
code = code_map.get(selected, "")
name = selected.split(" (")[0] if selected else ""

# 3) 개별 갱신 버튼
if code:
    st.markdown(f"**조회: {name} ({code})**")
    if st.button("🔄 개별갱신"):
        # CSV 덮어쓰지 않고 캐시 내 데이터만 업데이트
        update_single_stock(code)
        st.experimental_rerun()

# 4) 필터된 전체 데이터 로드
CSV = "filtered_stocks.csv"
if pd.io.common.file_exists(CSV):
    df_all = (
        pd.read_csv(CSV, dtype={"종목코드":str})
          .assign(종목코드=lambda d: d["종목코드"].str.zfill(6))
    )
else:
    df_all = pd.DataFrame()

# 5) 최신 재무 정보
st.header("📊 최신 재무 정보")
row = (
    df_all[df_all["종목코드"] == code].iloc[0]
    if code and not df_all.empty and code in df_all["종목코드"].values
    else None
)
fields = ["PER","PBR","EPS","BPS","배당률","score","급등확률"]
if row is not None:
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

# 6) 주가 & 기술지표 차트
st.header("📈 주가 및 기술지표 차트")
price_path = f"price_{code}.csv"
if row is not None and pd.io.common.file_exists(price_path):
    df_price = pd.read_csv(price_path, index_col=0, parse_dates=True)
    fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
    st.plotly_chart(fig,     use_container_width=True)
    st.plotly_chart(fig_rsi, use_container_width=True)
    st.plotly_chart(fig_macd,use_container_width=True)
else:
    st.info("차트 데이터가 없습니다.")

# 7) 추천 매수가/매도가
st.header("📌 추천 매수/매도가")
if row is not None:
    df_price = None
    if pd.io.common.file_exists(price_path):
        tmp = pd.read_csv(price_path, index_col=0, parse_dates=True)
        if "종가" in tmp.columns:
            df_price = tmp
    buy, sell = compute_recommendations(row, df_price)
    st.metric("추천 매수가", f"{buy:,} 원")
    st.metric("추천 매도가", f"{sell:,} 원")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 8) 종목 평가 / 투자 전략
st.header("📋 종목 평가 / 투자 전략")
if row is not None:
    adv = []
    if row["PER"] > 20:      adv.append("고PER: 고평가 우려, 실적 모멘텀 확인 필요.")
    elif row["PER"] < 7:     adv.append("저PER: 저점 매수 기회.")
    else:                    adv.append("PER 적정 수준.")
    if row["PBR"] < 1:       adv.append("PBR<1: 안전마진 확보된 저평가.")
    elif row["PBR"] > 2:     adv.append("PBR>2: 고평가 가능성.")
    if row["배당률"] > 3:    adv.append("높은 배당률: 배당투자 적합.")
    if row["score"] > 1.0:   adv.append("높은 투자매력 점수: 적극 매수 추천.")
    elif row["score"] < 0:   adv.append("낮은 점수: 보수적 접근 권장.")
    if row["급등확률"] > 1:  adv.append("급등 시그널 포착: 수급 모니터링 필요.")
    for a in adv:
        st.write("• " + a)
    st.write("_※ 참고용 분석이며, 실제 투자 전 공시·리포트 확인 필수._")
else:
    st.write("정보가 없습니다.")

# 9) 최신 뉴스
st.header("📰 최신 뉴스")
try:
    from modules.fetch_news import fetch_google_news
    news = fetch_google_news(name) if name else []
    if news:
        for n in news:
            st.markdown(f"- {n}")
    else:
        st.info("관련 뉴스가 없습니다.")
except:
    st.info("뉴스 로드 오류")

# 10) TOP10
st.header("🔥 투자성향별 TOP10 & 급등 예상 종목")
style = st.selectbox(
    "투자성향", ["aggressive","stable","dividend"],
    format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x]
)
if not df_all.empty:
    scored = finalize_scores(df_all.copy(), style=style)
    scored["신뢰등급"] = scored.apply(assess_reliability, axis=1)
    st.subheader("◾ 투자 매력점수 TOP10")
    st.dataframe(scored.nlargest(10,"score"), use_container_width=True)
    st.subheader("🔥 급등 예상 TOP10")
    st.dataframe(scored.nlargest(10,"급등확률"), use_container_width=True)
else:
    st.info("TOP10 데이터를 불러올 수 없습니다.")

# 11) 공식 · 설명
with st.expander("📊 공식 및 의미 설명"):
    st.markdown(
        "- **투자점수**: PER·PBR·EPS·BPS·배당률 가중합\n"
        "- **급등확률**: 거래량·저PER·변동성 반영\n"
        "- **추천가**: PER·PBR·EMA20 기반 자동계산"
    )

# 12) 로고
st.markdown(
    "<div style='text-align:center'>"
    "<img src='https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png' "
    "width='260'/></div>",
    unsafe_allow_html=True
)
