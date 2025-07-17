import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from modules.chart_utils import plot_price_rsi_macd
from modules.fetch_news import fetch_google_news
from update_stock_database import update_database, update_single_stock

st.set_page_config(page_title="투자 매니저", layout="wide")

# --- 종목 DB 불러오기 및 검색 자동완성 ---
@st.cache_data(ttl=600)
def load_filtered_data():
    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    return df

df_all = load_filtered_data()

def suggest_stocks(query):
    return df_all[df_all["종목명"].str.contains(query, case=False, na=False)]["종목명"].unique().tolist()[:10]

# --- 종목 검색 ---
st.title("투자 매니저")
st.markdown("#### 🔍 종목 검색")
stock_query = st.text_input("종목명 또는 코드 입력", "")
search_list = suggest_stocks(stock_query) if stock_query else []

if len(search_list) > 0:
    stock_name = st.selectbox("검색결과", search_list, key="searchselect")
else:
    stock_name = st.selectbox("검색결과", df_all["종목명"].unique().tolist(), index=0, key="searchall")

row = df_all[df_all["종목명"] == stock_name].iloc[0] if stock_name in df_all["종목명"].values else df_all.iloc[0]

col1, col2 = st.columns([1,1])
with col1:
    st.markdown(f"### {row['종목명']} ({row['종목코드']})")
with col2:
    if st.button("↻ 개별갱신"):
        update_single_stock(row["종목코드"])
        st.success("개별 갱신 완료(새로고침 필요)")
    if st.button("🌐 전체갱신"):
        msg = st.empty()
        progress = st.progress(0)
        total = len(df_all)
        for i, code in enumerate(df_all["종목코드"]):
            update_single_stock(code)
            percent = int(100 * (i+1) / total)
            progress.progress(percent)
            msg.info(f"{percent}% 완료")
        st.success("전체 갱신 완료(새로고침 필요)")

# --- 2열 재무정보(호버 설명 포함) ---
st.markdown("### 📈 최신 재무 정보")
fin_cols1 = ["PER", "EPS", "점수"]
fin_cols2 = ["PBR", "BPS", "배당률"]
col1, col2 = st.columns(2)
for f1, f2 in zip(fin_cols1, fin_cols2):
    with col1:
        st.metric(f"{f1} <span style='font-size:11px;' title='{FIELD_EXPLAIN.get(f1,'')}'>❓</span>", f"{row.get(f1,'-')}")
    with col2:
        st.metric(f"{f2} <span style='font-size:11px;' title='{FIELD_EXPLAIN.get(f2,'')}'>❓</span>", f"{row.get(f2,'-')}")

# --- 차트 영역 ---
st.markdown("### 가격(종가), EMA(20), 볼린저밴드")
try:
    df_price = pd.read_csv(f"price_data/{row['종목코드']}.csv")
    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.plotly_chart(fig_rsi, use_container_width=True, config={"displayModeBar": False})
    st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})
except Exception:
    st.warning("주가 데이터가 없습니다.")

# --- 차트/지표 도움말 ---
with st.expander("📈 차트/지표 도움말 (클릭)"):
    st.markdown("""
    - **EMA(20)**: 20일 지수이동평균선. 단기 추세 및 매수/매도 타이밍 판단에 참고.
    - **볼린저밴드**: 상단(과열), 하단(과매도) 추세를 보여주며, 밴드 돌파시 변동성 확대 가능.
    - **RSI(14)**: 40 미만 과매도, 60 초과 과매수로 해석.
    - **MACD**: 매수/매도 신호(시그널선 교차)로 활용. 단기 추세전환 시 포착 가능.
    """)

# --- 추천 매수/매도 (차트 바로 아래) ---
st.markdown("##### 🟢 추천 매수가 / 🔴 매도가")
if "추천매수" in row and "추천매도" in row:
    st.write(f"매수가: {row['추천매수']}, 매도가: {row['추천매도']}")
else:
    st.info("추천 매수/매도가 준비되지 않았습니다.")

# --- 종목평가/투자전략(전문가 설명) ---
st.markdown("### 📋 종목 평가 및 투자 전략(전문가 의견)")
eval_text = []
if float(row.get("PBR",0)) > 2:
    eval_text.append("⚠️ [PBR] PBR이 2를 초과하여 고평가 우려. 성장주라면 실적 개선을 꼭 확인.")
if float(row.get("배당률",0)) < 1:
    eval_text.append("💡 [배당] 배당수익률이 1% 미만으로 저조. 배당투자 관점에서는 보완 필요.")
if float(row.get("PER",0)) > 15:
    eval_text.append("⚠️ [PER] PER이 15를 넘어 고평가 신호. 실적 성장세 동반 여부 확인 필요.")
if len(eval_text)==0:
    eval_text.append("ℹ️ [종합진단] 특별한 위험 신호 없이 무난한 구간입니다. 시장상황과 함께 참고 바랍니다.")
st.write('\n'.join([f"- {x}" for x in eval_text]))
st.info("※ 종목 평가는 다양한 시장 상황·실적·공시를 반영해 판단해야 하며, 본 분석은 참고용입니다.")

# --- 관련 뉴스 ---
st.markdown("### 📰 관련 뉴스")
for title, url in fetch_google_news(row["종목명"]):
    st.markdown(f"- [{title}]({url})")

# --- TOP10 & 급등 TOP10 종목/표 + 종목 선택창 ---
st.markdown("## 투자 성향별 TOP10 및 급등 예상 종목")
# 데이터 준비
scored_df = finalize_scores(df_all.copy())
top10 = scored_df.sort_values("score", ascending=False).head(10)
soar10 = scored_df.sort_values("급등확률", ascending=False).head(10)
# TOP10
st.markdown("#### 투자 매력점수 TOP10")
top10_name = st.selectbox("TOP10 종목명", top10["종목명"].tolist(), key="top10sel")
st.dataframe(top10, use_container_width=True)
# 급등 TOP10
st.markdown("#### 🔥 급등 예상종목 TOP10")
soar10_name = st.selectbox("급등 예상종목 TOP10", soar10["종목명"].tolist(), key="soar10sel")
st.dataframe(soar10, use_container_width=True)

# --- 점수/급등 산정방식 설명 ---
with st.expander("📊 점수 산정방식/급등예상 공식 (클릭)"):
    st.markdown("""
- **투자매력점수**: PER, PBR, EPS, BPS, 배당률, 거래량, 기술/재무 혼합평가(z-score 보정)  
- **급등확률**: 최근 거래량 급증, 단기 변동성, 저PER/저PBR/강한 수급, 세력성 매집패턴 등 KRX 기반 계량지표로 산출  
- 모든 공식은 데이터 결측/이상치 자동제거, 산업/시장 환경을 일부 반영  
- 산정 공식은 score_utils.py 참고
    """)

# --- 로고 ---
st.markdown("---")
st.image("logo_tynex.png", width=220, output_format="png", use_column_width=False)

# --- 최신/개별 데이터 갱신일 표기 ---
st.caption(f"전체 DB 갱신일: {df_all['갱신일'].max() if '갱신일' in df_all.columns else '-'} / 해당 종목 갱신일: {row.get('갱신일','-')}")
