# app.py
import streamlit as st
import pandas as pd
import numpy as np
import os
from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from update_stock_database import update_database, update_single_stock

st.set_page_config(page_title="투자 매니저", layout="wide")

# 1) 초기 종목 리스트 로드 (자동완성)
@st.cache_data(show_spinner=False)
def load_all_stocklist(csv_path="initial_krx_list_test.csv"):
    if not os.path.exists(csv_path):
        return [], {}
    df = pd.read_csv(csv_path, dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    options = df["종목명"] + " (" + df["종목코드"] + ")"
    return options.tolist(), dict(zip(options, df["종목코드"]))

options, code_map = load_all_stocklist()

# 2) UI: 제목 & 검색창
st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
q = st.text_input("종목명 또는 코드 입력", "", help="일부만 입력해도 자동완성 지원")
matches = [o for o in options if q in o] if q else options
selected = st.selectbox("", matches, help="아래에서 종목을 선택하세요") if matches else ""
code = code_map.get(selected, "")
name = selected.split(" (")[0] if selected else ""

# 3) 조회중 종목 표시 + 갱신 버튼
if code:
    st.markdown(
        f"**조회 중인 종목: <span style='color:#55b6ff'>{name} ({code})</span>**",
        unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 개별갱신"):
            update_single_stock(code)
            st.success("개별 종목 데이터 갱신 완료!")
            st.experimental_rerun()
    with c2:
        if st.button("🌐 전체갱신"):
            with st.spinner("전체 데이터 갱신중..."):
                update_database()
            st.success("전체 데이터 갱신 완료!")
            st.experimental_rerun()

# 4) 필터된 전체 데이터 로드
CSV = "filtered_stocks.csv"
if os.path.exists(CSV):
    df_all = pd.read_csv(CSV, dtype=str).assign(
        종목코드=lambda d: d["종목코드"].str.zfill(6)
    )
else:
    df_all = pd.DataFrame()

# 5) 선택 종목의 최신 재무 정보
st.markdown("### 📊 최신 재무 정보")
row = None
if code and not df_all.empty:
    tmp = df_all[df_all["종목코드"] == code]
    if not tmp.empty:
        row = tmp.iloc[0]

fields = ["PER","PBR","EPS","BPS","배당률","score","급등확률"]
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i % 2]:
            val = row.get(f)
            display = f"{float(val):,.2f}" if pd.notna(val) else "-"
            st.metric(label=f, value=display, help=FIELD_EXPLAIN.get(f, ""))
    st.caption(f"⏰ 갱신일: {row['갱신일']}  |  신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 6) 주가 & 기술지표 차트
st.markdown("### 📈 주가 및 기술지표 차트")
try:
    from modules.chart_utils import plot_price_rsi_macd_bb
    price_file = f"price_{code}.csv"
    if code and os.path.exists(price_file):
        df_price = pd.read_csv(price_file, parse_dates=True, index_col=0)
        fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_rsi, use_container_width=True)
        st.plotly_chart(fig_macd, use_container_width=True)
    else:
        st.info("차트 데이터가 부족합니다.")
except:
    st.info("차트 로드 오류")

# 7) 추천 매수가·매도가
st.markdown("### 📌 추천 매수/매도가")
if row is not None and "추천매수가" in row:
    st.success(f"매수가: {row['추천매수가']}  /  매도가: {row['추천매도가']}")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 8) 전문가 평가 / 투자 전략
st.markdown("### 📋 종목 평가 / 투자 전략")
if row is not None:
    adv = []
    per = float(row.get("PER", np.nan))
    pbr = float(row.get("PBR", np.nan))
    dy  = float(row.get("배당률", np.nan))
    sc  = float(row.get("score", 0))
    jp  = float(row.get("급등확률", 0))

    # PER
    if per > 20:   adv.append("PER>20: 고평가 가능성. 성장 스토리·실적 모멘텀 확인 필요.")
    elif per < 7: adv.append("PER<7: 저평가 구간. 실적 개선 기대주 저점 매수 기회.")
    else:         adv.append("PER이 시장 평균 수준.")

    # PBR
    if pbr < 1:   adv.append("PBR<1: 안전마진 확보된 저평가 구간.")
    elif pbr > 2: adv.append("PBR>2: 성장 기대 반영된 상태.")

    # 배당수익률
    if dy >= 3:   adv.append("배당률≥3%: 배당투자에도 유리.")
    elif dy < 1: adv.append("배당률<1%: 소득형 투자자에겐 다소 매력 낮음.")

    # 종합 점수
    if sc > 1:    adv.append("높은 투자매력 점수: 적극 매수 관점.")
    elif sc < 0: adv.append("낮은 투자매력 점수: 보수적 접근 권장.")

    # 급등확률
    if jp > 1:    adv.append("단기 급등 시그널 포착: 수급 모니터링 필요.")
    else:         adv.append("단기 급등 확률 낮음: 중장기 모니터링 추천.")

    for a in adv:
        st.write(f"• {a}")
    st.write("_※ 본 평가는 참고용입니다. 투자 전 개별 기업 공시·리포트 확인 필수._")
else:
    st.write("정보가 없습니다.")

# 9) 최신 뉴스
st.markdown("### 📰 최신 뉴스")
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

# 10) 투자성향별 & 급등 예상 TOP10
st.markdown("## 🔥 투자성향별 TOP10 & 급등 예상 종목")
style = st.selectbox("투자성향", ["aggressive","stable","dividend"],
                     format_func=lambda x: {"aggressive":"공격형","stable":"안정형","dividend":"배당형"}[x])
if not df_all.empty:
    scored = finalize_scores(df_all.copy(), style=style)
    scored["신뢰등급"] = scored.apply(assess_reliability, axis=1)
    st.subheader("🔹 투자 매력점수 TOP10")
    st.dataframe(scored.nlargest(10, "score"), use_container_width=True)
    st.subheader("🔥 급등 예상 TOP10")
    st.dataframe(scored.nlargest(10, "급등확률"), use_container_width=True)
else:
    st.info("TOP10 데이터를 불러올 수 없습니다.")

# 11) 공식 및 설명
with st.expander("📊 공식 및 의미 설명"):
    st.markdown(
        "- **투자점수**: PER·PBR·EPS·BPS·배당률·거래량 반영 가중합\n"
        "- **급등확률**: 단기 수급·저PER·변동성 반영\n"
        "- 성향별 자동 가중치 조정"
    )

# 12) 로고
st.markdown(
    '<div style="text-align:center">'
    '<img src="https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png" '
    'width="260"/></div>',
    unsafe_allow_html=True
)
