# app.py
import os
import streamlit as st
import pandas as pd
from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from update_stock_database import update_database, update_single_stock

# 1) 작업 디렉터리 → 이 스크립트가 있는 루트로 강제 이동
os.chdir(os.path.dirname(__file__))

st.set_page_config(page_title="투자 매니저", layout="wide")

# 2) 초기 종목 리스트 로드 (자동완성)
@st.cache_data(show_spinner=False)
def load_all_stocklist(csv="initial_krx_list_test.csv"):
    if not os.path.exists(csv):
        return [], {}
    df = pd.read_csv(csv, dtype=str)
    # 6자리 코드로 통일(zfill)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    options = df["종목명"] + " (" + df["종목코드"] + ")"
    code_map = dict(zip(options, df["종목코드"]))
    return options.tolist(), code_map

options, code_map = load_all_stocklist()

# 3) UI 타이틀 & 검색
st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
q = st.text_input("종목명 또는 코드 입력", "", help="일부만 입력해도 자동완성 지원")
matches = [o for o in options if q in o] if q else options
selected_option = st.selectbox("", matches, help="아래 목록에서 종목을 선택하세요") if matches else ""
code = code_map.get(selected_option, "")
name = selected_option.split(" (")[0] if selected_option else ""

# 4) 조회 중인 종목 표시 & 갱신 버튼
if code:
    st.markdown(
        f"**조회 중인 종목: <span style='color:#55b6ff'>{name} ({code})</span>**",
        unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 개별갱신"):
            update_single_stock(code)
            st.experimental_rerun()  # 캐시 무효화 후 새로고침
    with c2:
        if st.button("🌐 전체갱신"):
            with st.spinner("전체 데이터 갱신중..."):
                update_database()
            st.success("전체 데이터 갱신 완료!")
            st.experimental_rerun()

# 5) 필터된 전체 데이터 로드
CSV = "filtered_stocks.csv"
df_all = pd.read_csv(CSV, dtype={"종목코드": str}).assign(
    종목코드=lambda d: d["종목코드"].str.zfill(6)
) if os.path.exists(CSV) else pd.DataFrame()

# 6) 선택 종목의 최신 재무 정보
st.markdown("### 📊 최신 재무 정보")
row = (
    df_all[df_all["종목코드"] == code].iloc[0]
    if code and not df_all.empty and code in df_all["종목코드"].values
    else None
)
fields = ["PER","PBR","EPS","BPS","배당률","score","급등확률"]
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i % 2]:
            st.metric(
                label=f"{f}  ❓",
                value=f"{row[f]:,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f, "")
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 7) 주가 & 기술지표 차트
st.markdown("### 📈 주가 및 기술지표 차트")
try:
    from modules.chart_utils import plot_price_rsi_macd_bb
    path = f"price_{code}.csv"
    if code and os.path.exists(path):
        df_price = pd.read_csv(path, parse_dates=True, index_col=0)
        fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_rsi, use_container_width=True)
        st.plotly_chart(fig_macd, use_container_width=True)
    else:
        st.info("차트 데이터가 부족합니다.")
except:
    st.info("차트 로드 오류")

# 8) 추천 매수가·매도가
st.markdown("### 📌 추천 매수/매도가")
if row is not None and "추천매수가" in row:
    st.success(f"매수가: {row['추천매수가']}  /  매도가: {row['추천매도가']}")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 9) 전문가 평가 / 투자 전략
st.markdown("### 📋 종목 평가 / 투자 전략")
if row is not None:
    adv = []
    # PER
    if row["PER"] > 20:
        adv.append("PER이 20 이상으로 고평가 가능성. 성장 스토리와 실적 모멘텀 확인 필요.")
    elif row["PER"] < 7:
        adv.append("저PER(7 미만)로 밸류에이션 매력적. 실적 개선주라면 저점 매수 기회.")
    else:
        adv.append("PER이 시장 평균 수준으로 적정 밸류에이션.")
    # PBR
    if row["PBR"] < 1:
        adv.append("PBR 1 미만. 자산 대비 저평가 구간, 안전마진 확보 가능.")
    elif row["PBR"] > 2:
        adv.append("PBR 2 이상. 업종 성장 기대가 주가에 반영된 상태.")
    # 배당
    if row["배당률"] > 3:
        adv.append("배당률 3% 이상. 배당투자에도 적합.")
    # 종합 점수
    if row["score"] > 1:
        adv.append("높은 투자매력 점수. 성장·가치·수급 균형 양호.")
    elif row["score"] < 0:
        adv.append("투자매력 점수 낮음. 보수적 접근 권장.")
    # 급등확률
    if row["급등확률"] > 1:
        adv.append("단기 급등 시그널 포착. 수급 모니터링 필수.")
    # 출력
    for line in adv:
        st.write(f"• {line}")
    st.write("_※ 본 평가는 참고용입니다. 실제 투자 전 개별기업 리포트·공시 확인 필수._")
else:
    st.write("정보가 없습니다.")

# 10) 최신 뉴스
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

# 11) 투자성향별 / 급등 예상 TOP10
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

# 12) 공식/설명
with st.expander("📊 공식 및 의미 설명"):
    st.markdown(
        "- **투자점수**: PER,PBR,EPS,BPS,배당률,거래량 가중합\n"
        "- **급등확률**: 단기 수급·저PER·변동성 반영\n"
        "- 성향별 가중치 자동 적용"
    )

# 13) 로고(가로폭 260px = 약 0.6배)
st.markdown(
    '<div style="text-align:center">'
    '<img src="https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png" '
    'width="260"/></div>',
    unsafe_allow_html=True
)
