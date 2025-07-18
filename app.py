import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from modules.score_utils          import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.chart_utils          import plot_price_rsi_macd_bb
from update_stock_database        import update_single_stock

# 추천 매수가·매도가 계산
from modules.calculate_indicators import calc_ema

def compute_recommendations(row, df_price=None):
    price = float(row["현재가"])
    per   = float(row["PER"])
    pbr   = float(row["PBR"])
    # 가치조정
    val_adj = 0.95 if per < 10 else (1.05 if per > 25 else 1.0)
    pb_adj  = 1.05 if pbr > 2 else 1.0
    # EMA20 기술 조정
    ta_adj = 1.0
    if df_price is not None:
        last_ema = calc_ema(df_price, window=20, col="종가").iloc[-1]
        ta_adj += 0.03 if price > last_ema else -0.03
    buy = round(price * val_adj * ta_adj * 0.98 / 10) * 10
    sell= round(price * pb_adj  * ta_adj * 1.02 / 10) * 10
    return int(buy), int(sell)

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("📈 투 자 매 니 저")

# 1) 초기 종목 리스트 로드
@st.cache_data
def load_list():
    df = pd.read_csv("initial_krx_list.csv", dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    opts = df["종목명"] + " (" + df["종목코드"] + ")"
    return opts.tolist(), dict(zip(opts, df["종목코드"]))

options, code_map = load_list()

# 2) 검색 & 선택
query = st.text_input("🔍 종목검색 (명칭·코드)", "")
matches = [o for o in options if query in o] if query else options
sel = st.selectbox("종목을 선택하세요", matches)
code = code_map.get(sel, "")
name = sel.split(" (")[0] if sel else ""

# 3) 개별갱신 버튼
if code and st.button("🔄 개별 갱신"):
    update_single_stock(code)
    st.experimental_rerun()

# 4) 전체 데이터 불러오기
if st.sidebar.button("📂 초기화면"):
    st.experimental_rerun()
try:
    df_all = pd.read_csv("filtered_stocks.csv", dtype=str)
    df_all["종목코드"] = df_all["종목코드"].str.zfill(6)
except:
    df_all = pd.DataFrame()

# 5) 최신 재무정보
st.header("🔍 최신 재무 정보")
row = df_all.loc[df_all["종목코드"] == code].squeeze() if code in df_all["종목코드"].values else None
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(["PER","PBR","배당수익률","score","급등확률"]):
        with cols[i%2]:
            st.metric(f, f"{float(row[f]):.2f}", help=FIELD_EXPLAIN.get(f,""))
    st.caption(f"⏰ 갱신일: {row['갱신일']} | 신뢰등급: {assess_reliability(row)}")
else:
    st.info("데이터 없음")

# 6) 차트
st.header("📊 주가 + 기술지표 차트")
if code:
    try:
        df_price = pd.read_csv(f"price_{code}.csv", index_col=0, parse_dates=True)
        fig1, fig2, fig3 = plot_price_rsi_macd_bb(df_price)
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)
    except:
        st.info("차트 데이터 없음")

# 7) 추천가
st.header("📌 추천 매수가/매도가")
if row is not None:
    df_price = None
    try:
        tmp = pd.read_csv(f"price_{code}.csv", index_col=0, parse_dates=True)
        df_price = tmp if "종가" in tmp.columns else None
    except:
        pass
    buy, sell = compute_recommendations(row, df_price)
    st.metric("매수가", f"{buy:,} 원")
    st.metric("매도가", f"{sell:,} 원")

# 8) 전문가 전략
st.header("📋 종목 평가 · 투자 전략")
if row is not None:
    advice=[]
    per = float(row["PER"]); pbr=float(row["PBR"]); dy=float(row["배당수익률"])
    sc  = float(row["score"]); jp=float(row["급등확률"])
    # PER
    if per>20: advice.append("• PER 20↑: 고평가 우려, 실적모멘텀 확인 권장")
    elif per<7:advice.append("• PER 7↓: 저평가 구간, 저점매수 기회")
    else:     advice.append("• PER 적정 수준")
    # PBR
    if pbr<1: advice.append("• PBR<1: 안전마진 확보")
    elif pbr>2:advice.append("• PBR>2: 성장반영 고평가 가능")
    # 배당
    if dy>3: advice.append("• 배당률 3%↑: 배당투자 적합")
    # 점수
    if sc>0.5: advice.append("• 높은 점수: 적극 매수 추천")
    elif sc<0: advice.append("• 낮은 점수: 보수적 접근 권장")
    # 급등
    if jp>0.7: advice.append("• 급등시그널↑: 수급 모니터링 필수")
    for a in advice: st.write(a)
    st.write("_※ 객관적 데이터 기반 참고용. 실제투자 전 공시·리포트 확인 필수_")

# 9) 뉴스
st.header("📰 최신 뉴스")
try:
    from modules.fetch_news import fetch_google_news
    for n in fetch_google_news(name): st.markdown(f"- {n}")
except: st.info("뉴스 없음")

# 10) TOP10
st.header("🔥 투자성향별 TOP10 · 급등예상")
style = st.selectbox("투자성향", ["aggressive","stable","dividend"],
                     format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x])
if not df_all.empty:
    df_s = finalize_scores(df_all.copy(), style=style)
    df_s["신뢰등급"] = df_s.apply(assess_reliability, axis=1)
    st.subheader("▶ 투자매력 TOP10")
    st.dataframe(df_s.nlargest(10, "score"), use_container_width=True)
    st.subheader("▶ 급등예상 TOP10")
    st.dataframe(df_s.nlargest(10, "급등확률"), use_container_width=True)

# 11) 공식 설명
with st.expander("📊 공식 및 의미"):
    st.markdown(
        "- **score**: Z-스코어 PER/PBR/배당률 + 거래량 모멘텀 가중합\n"
        "- **급등확률**: 거래량급증·저PER·변동성 반영\n"
        "- **추천가**: PER/PBR·EMA20 기술지표 혼합 자동 계산"
    )

# 12) 로고
st.markdown(
    "<div style='text-align:center; margin:30px 0;'>"
    "<img src='logo_tynex.png' width='260'/>"
    "</div>",
    unsafe_allow_html=True
)
