# app.py
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.calculate_indicators import calc_ema
from modules.chart_utils import plot_price_rsi_macd_bb
from update_stock_database import fetch_price_history, fetch_krx_data  # 수집 함수
from update_stock_database import update_database  # 전체 워크플로우용
from functools import lru_cache

# ────────────────────────────────────────────────────────────────
# 개별 종목 캐시 수집 (세션 종료 전까지 유지)
@st.cache_data(show_spinner=False)
def cached_single_update(code: str):
    fin = fetch_krx_data(code)
    hist = fetch_price_history(code)
    return fin, hist

# ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="투자 매니저", layout="wide")
os.chdir(os.path.dirname(__file__))

# 1) 종목 리스트 로드
@st.cache_data(show_spinner=False)
def load_stock_list(csv="initial_krx_list_test.csv"):
    if not os.path.exists(csv):
        return [], {}
    df = pd.read_csv(csv, dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    options = df["종목명"] + " (" + df["종목코드"] + ")"
    return options.tolist(), dict(zip(options, df["종목코드"]))

options, code_map = load_stock_list()

# 2) UI: 검색
st.title("🔍 종목 검색")
q = st.text_input("종목명 또는 코드 입력")
matches = [o for o in options if q in o] if q else options
selected = st.selectbox("", matches) if matches else ""
code = code_map.get(selected, "")
name = selected.split(" (")[0] if selected else ""

# 3) 표시 & 개별 갱신
if code:
    st.markdown(f"**조회: <span style='color:#55b6ff'>{name} ({code})</span>**", unsafe_allow_html=True)
    if st.button("🔄 개별갱신"):
        fin, hist = cached_single_update(code)
        st.success("개별 데이터 갱신 완료! (세션 캐시에 반영)")
else:
    fin, hist = None, None

# 4) 전체 filtered CSV 로드
df_all = pd.read_csv("filtered_stocks.csv", dtype={"종목코드": str}).assign(
    종목코드=lambda d: d["종목코드"].str.zfill(6)
) if os.path.exists("filtered_stocks.csv") else pd.DataFrame()

# 5) 최신 재무 정보
st.header("📊 최신 재무 정보")
row = None
if code and not df_all.empty:
    mask = df_all["종목코드"] == code
    if mask.any():
        row = df_all.loc[mask].iloc[0]

if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(["PER","PBR","EPS","BPS","배당률","score","급등확률"]):
        with cols[i % 2]:
            st.metric(f, f"{row[f]:,.2f}" if pd.notna(row[f]) else "-", help=FIELD_EXPLAIN.get(f, ""))
    st.caption(f"⏰ 갱신일: {row['갱신일']}  |  신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 6) 주가 차트
st.header("📈 주가 및 기술지표 차트")
if hist is None and code:
    # 아직 cached_single_update 안 눌렀다면 CSV 로드
    path = f"price_{code}.csv"
    if os.path.exists(path):
        hist = pd.read_csv(path, index_col=0, parse_dates=True)
if hist is not None and not hist.empty:
    fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(hist)
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig_rsi, use_container_width=True)
    st.plotly_chart(fig_macd, use_container_width=True)
else:
    st.info("차트 데이터가 부족합니다.")

# 7) 추천 매수/매도가
st.header("📌 추천 매수/매도가")
if (row is not None) and ((fin is not None) or (row is not None)):
    # fin: 개별갱신 시, row: CSV 기반
    base = fin if fin is not None else row.to_dict()
    df_tmp = hist if hist is not None else None

    # 추천가 계산
    price = float(base["현재가"])
    per   = float(base.get("PER", np.nan))
    pbr   = float(base.get("PBR", np.nan))
    # 밸류·EMA 기반 적정 매수가/매도가
    adj = 1.0 + ( -0.05 if per<10 else (0.05 if per>25 else 0) )
    emaline = calc_ema(df_tmp, 20, "종가") if df_tmp is not None else None
    adj += (0.03 if emaline is not None and price>emaline.iloc[-1] else -0.03)
    buy = int(round(price*adj*0.98/10)*10)
    sell= int(round(price*(1+0.02)*adj/10)*10)

    st.metric("추천 매수가", f"{buy:,} 원")
    st.metric("추천 매도가", f"{sell:,} 원")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 8) 종목 평가·전략
st.header("📋 종목 평가 / 투자 전략")
if row is not None:
    adv = []
    if row["PER"] > 20: adv.append("고PER(>20): 성장 모멘텀 확인 권장")
    elif row["PER"] < 7: adv.append("저PER(<7): 저점 매수 기회")
    else: adv.append("PER: 시장 평균 수준")

    if row["PBR"] < 1: adv.append("PBR<1: 안전마진 확보된 저평가")
    elif row["PBR"] > 2: adv.append("PBR>2: 고평가 가능성")

    if row["배당률"] > 3: adv.append("배당률>3%: 배당투자 적합")

    if row["score"] > 1: adv.append("높은 점수: 적극 매수 추천")
    elif row["score"] < 0: adv.append("낮은 점수: 보수적 접근 권장")

    if row["급등확률"] > 1: adv.append("단기 급등 시그널 포착: 모니터링 필요")

    for v in adv:
        st.write(f"• {v}")
    st.caption("_※ 참고용 분석입니다. 실제 투자 전 공시·리포트 확인 필수._")
else:
    st.write("정보가 없습니다.")

# 9) 최신 뉴스
st.header("📰 최신 뉴스")
try:
    from modules.fetch_news import fetch_google_news
    news = fetch_google_news(name) if name else []
    if news:
        for n in news: st.write(f"- {n}")
    else:
        st.info("관련 뉴스가 없습니다.")
except:
    st.info("뉴스 로드 오류")

# 10) TOP10
st.header("🔥 투자성향별 TOP10 & 급등 예상")
style = st.selectbox("투자성향", ["aggressive","stable","dividend"],
                     format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x])
if not df_all.empty:
    sc = finalize_scores(df_all.copy(), style=style)
    sc["신뢰등급"] = sc.apply(assess_reliability, axis=1)

    st.subheader("투자매력점수 TOP10")
    st.dataframe(sc.nlargest(10, "score"), use_container_width=True)

    st.subheader("급등예상 TOP10")
    st.dataframe(sc.nlargest(10, "급등확률"), use_container_width=True)
else:
    st.info("TOP10 데이터를 불러올 수 없습니다.")

# 11) 공식 설명
with st.expander("📊 공식 및 의미 설명"):
    st.write("""
    - 투자점수: PER·PBR·EPS·BPS·배당률·거래량 반영 가중합  
    - 급등확률: 단기 수급·저PER·변동성 지표 반영  
    - 추천가: PER·EMA 기반 자동 계산  
    """)

# 12) 로고
st.markdown(
    "<div style='text-align:center;'>"
    "<img src='https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png' width='260'/>"
    "</div>",
    unsafe_allow_html=True
)
