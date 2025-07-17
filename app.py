import streamlit as st
import pandas as pd
import numpy as np
import os
from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from update_stock_database import update_database, update_single_stock

st.set_page_config(page_title="투자 매니저", layout="wide")

# 1. 종목 검색 및 연관검색/자동완성
@st.cache_data
def load_all_stocklist():
    if os.path.exists("initial_krx_list_test.csv"):
        df = pd.read_csv("initial_krx_list_test.csv")
        names = df["종목명"].astype(str).tolist()
        codes = [str(c).zfill(6) for c in df["종목코드"]]
        options = [f"{n} ({c})" for n, c in zip(names, codes)]
        code_map = dict(zip(options, codes))
        return options, code_map
    return [], {}

options, code_map = load_all_stocklist()
st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
selected = st.text_input("종목명 또는 코드 입력", "", key="searchbox", help="종목명 일부만 입력해도 자동완성 지원")
autocomplete = [o for o in options if selected in o] if selected else options
if autocomplete:
    selected_option = st.selectbox("", autocomplete, key="autofill")
    code = code_map[selected_option]
    name = selected_option.split(" (")[0]
else:
    code, name = "", ""

# 2. 조회종목명 및 데이터갱신
if code:
    code = str(code).zfill(6)
    st.markdown(f"**조회 중인 종목: <span style='color:#55b6ff'>{name} ({code})</span>**", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🔄 개별갱신"):
            update_single_stock(code)
            st.success("개별 종목 데이터 갱신 완료!")
    with col_btn2:
        if st.button("🌐 전체갱신"):
            with st.spinner("전체 데이터 갱신중..."):
                update_database()
                st.success("전체 데이터 갱신 완료!")

# 3. 최신 재무 정보 (2열+툴팁)
st.markdown("### <img src='https://img.icons8.com/color/48/bar-chart' width='32' style='vertical-align:middle'/> 최신 재무 정보", unsafe_allow_html=True)
df_all = pd.read_csv("filtered_stocks.csv") if os.path.exists("filtered_stocks.csv") else pd.DataFrame()
row = df_all[df_all["종목코드"] == code].iloc[0] if (code and not df_all.empty and (df_all["종목코드"] == code).any()) else None
fields = ["PER", "PBR", "EPS", "BPS", "배당률", "score", "급등확률"]
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i%2]:
            st.metric(
                f"{f}  \U0001F6C8",  # ❓아이콘, 필요시 f"<span ...></span>"으로 변환
                f"{row[f]:,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f, ""),
                label_visibility="visible", 
                key=f"metric_{f}"
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {assess_reliability(row)}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 4. 주가/지표 차트 (필요시 chart_utils.py 참고)
st.markdown("### <img src='https://img.icons8.com/color/48/line-chart' width='32' style='vertical-align:middle'/> 주가 및 기술지표 차트", unsafe_allow_html=True)
try:
    from modules.chart_utils import plot_price_rsi_macd_bb
    price_file = f"price_{code}.csv"
    if os.path.exists(price_file):
        df_price = pd.read_csv(price_file)
        fig, fig_rsi, fig_macd = plot_price_rsi_macd_bb(df_price)
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_rsi, use_container_width=True)
        st.plotly_chart(fig_macd, use_container_width=True)
    else:
        st.info("차트 데이터가 부족합니다.")
except Exception as e:
    st.info("차트 데이터가 부족합니다.")

# 5. 추천 매수가/매도가
st.markdown("### 📌 추천 매수/매도가")
if row is not None:
    st.info("추천가 산출을 위한 데이터가 부족합니다." if "추천매수가" not in row else f"추천 매수가: {row['추천매수가']}, 추천 매도가: {row['추천매도가']}")
else:
    st.info("추천가 산출을 위한 데이터가 부족합니다.")

# 6. 종목 평가 및 투자 전략 (전문가 상세 조언)
st.markdown("### 📋 종목 평가 / 투자 전략")
if row is not None:
    advices = []
    # PER
    if row["PER"] > 20:
        advices.append("PER(주가수익비율)이 20 이상으로, 현재 주가가 기업의 이익 대비 높게 평가되고 있습니다. 단기 과열이나 고평가 신호로, 성장 스토리가 뒷받침되지 않으면 신중 접근이 필요합니다.")
    elif row["PER"] < 7:
        advices.append("PER이 7 미만으로 저평가 구간에 해당합니다. 실적 개선 및 시장 주도 섹터라면 저점매수 기회로 볼 수 있습니다.")
    else:
        advices.append("PER이 시장 평균 수준으로, 밸류에이션 측면에서 부담 없는 가격대입니다.")
    # PBR
    if row["PBR"] < 1:
        advices.append("PBR(주가순자산비율)이 1 미만. 자산 대비 주가가 낮아 안전마진 구간으로 분류됩니다. 단, 저PBR이 지속된다면 업종/성장성도 함께 체크하세요.")
    elif row["PBR"] > 2:
        advices.append("PBR 2 이상. 성장 기대가 반영된 고평가 상태일 수 있습니다. 기업의 미래 성장성이 중요한 판단 포인트입니다.")
    # 배당률
    if row["배당률"] > 3:
        advices.append("배당수익률이 3% 이상. 중장기 배당투자/현금흐름 투자자에게 적합합니다. 분기/연말 배당락도 유의하세요.")
    elif row["배당률"] < 1:
        advices.append("배당수익률이 1% 미만. 안정성과 소득투자를 중시한다면 타 종목과 비교 필요합니다.")
    # score, 급등확률, 종합
    if row["score"] > 1.5:
        advices.append("종합 투자매력 점수가 높은 편입니다. 성장성·가치·수급이 균형 잡힌 종목으로, 적극 매수/추가매수 관점에서 유망.")
    elif row["score"] < 0:
        advices.append("투자매력 점수가 낮아 보수적 접근 권장. 기업 펀더멘털 또는 업황 확인 후 분할매수, 장기 관점 유지 권장.")
    if row["급등확률"] > 1:
        advices.append("단기 급등 시그널이 포착되었습니다. 거래량·수급 변화를 주의 깊게 관찰하세요. 단, 변동성 리스크도 동반될 수 있습니다.")
    elif row["급등확률"] < 0.1:
        advices.append("단기 급등 확률이 낮은 구간입니다. 보수적으로 접근하거나, 중장기 모니터링 전략이 유리합니다.")
    # 종합 멘트
    if not advices:
        advices.append("시장 평균 수준. 펀더멘털, 업황, 수급, 뉴스 등 다양한 관점에서 추가 점검 후 투자 권장.")
    # 전문가 느낌의 친절·상세 멘트 표기
    for adv in advices:
        st.write(f"• {adv}")
    st.write("※ 본 평가는 객관적 재무/수급/시장 데이터 기반의 참고용 분석입니다. 실제 투자 전 개별기업 공시, 업황, 리스크 요인도 꼭 점검하세요.")
else:
    st.write("정보 부족")

# 7. 관련 뉴스
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

# 8. 투자 성향별/급등 top10 표
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

# 9. 점수/급등확률 공식 설명
with st.expander("📊 투자점수·급등확률 공식/의미 설명(클릭)"):
    st.markdown("""
    - **투자점수:** PER, PBR, EPS, BPS, 배당률, 거래량 등 실적·밸류·수급 반영 가중합  
    - **급등확률:** 단기 거래량 급증, 저PER, 단기 변동성 등 반영  
    - 각 성향별로 가중치(공격형: 수익/수급↑, 안정형: 저PBR/PER, 배당형: 배당↑) 자동 조정  
    """)

# 10. 로고(중앙, 크기 0.6배)
st.markdown('<div style="text-align:center;"><img src="https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png" width="260"/></div>', unsafe_allow_html=True)
