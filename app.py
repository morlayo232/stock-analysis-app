# app.py

import streamlit as st
import pandas as pd
from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd
from update_stock_database import update_single_stock, update_database

st.set_page_config(page_title="투자 매니저", layout="wide")

# ====== 헤더 ======
st.title("투자 매니저")

# ====== 종목 검색 ======
st.subheader("🔎 종목 검색")
code_or_name = st.text_input("종목명 또는 코드 입력", "")

# CSV 데이터 로딩 및 예외처리
@st.cache_data
def load_filtered():
    try:
        df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
        return df
    except Exception:
        st.error("filtered_stocks.csv 파일을 읽을 수 없습니다.")
        st.stop()
df = load_filtered()

if code_or_name:
    # 코드 or 이름 검색, 첫 결과만 자동 선택
    df_match = df[df['종목명'].str.contains(code_or_name, na=False) | df['종목코드'].astype(str).str.contains(code_or_name)]
    if len(df_match) > 0:
        selected_code = df_match.iloc[0]['종목코드']
        selected_name = df_match.iloc[0]['종목명']
    else:
        st.warning("해당 종목을 찾을 수 없습니다.")
        selected_code = None
        selected_name = None
else:
    selected_code = df.iloc[0]['종목코드']
    selected_name = df.iloc[0]['종목명']

if selected_code is None:
    st.stop()

st.markdown(f"### {selected_name} ({selected_code})")

# ====== 최신 재무정보 2열 레이아웃 ======
st.subheader("📊 최신 재무 정보")
col1, col2 = st.columns(2)
fields = ["PER", "PBR", "EPS", "BPS", "배당률", "점수"]
data = df[df['종목코드'] == selected_code].iloc[0]
with col1:
    for f in fields[0:3]:
        st.metric(f, f"{data[f]:,.2f}" if '점수' not in f else f"{data[f]:.3f}")
with col2:
    for f in fields[3:]:
        st.metric(f, f"{data[f]:,.2f}" if '점수' not in f else f"{data[f]:.3f}")

# ====== 주가 차트 및 지표 ======
df_price = pd.DataFrame()  # fetch_price(selected_code) 등으로 대체
if not df_price.empty:
    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig_rsi, use_container_width=True)
    st.plotly_chart(fig_macd, use_container_width=True)
else:
    st.warning("주가 데이터를 불러올 수 없습니다.")

# ====== 차트 도움말(주식초보 안내) ======
st.info("""
- **볼린저밴드**: 상단, 하단 밴드 이탈시 단기 과매수/과매도 신호.
- **RSI**: 70 이상 과매수, 30 이하 과매도.
- **MACD**: Signal 상향돌파(매수), 하향돌파(매도) 참고.
""")

# ====== 종목 평가/투자 전략 (전문가의견 스타일) ======
st.subheader("📋 종목 평가 및 투자 전략(전문가 의견)")
evals = []
# 논리적/설득력있게 자동생성
if data['PBR'] > 2:
    evals.append("⚠️ [PBR] PBR이 2를 초과, 단기 과열 또는 성장주 주의 필요.")
if data['배당률'] < 1:
    evals.append("💡 [배당] 배당수익률이 1% 미만으로, 배당 매력은 낮은 편입니다.")
if data['점수'] < 0:
    evals.append("❗ [종합진단] 단기 투자 매력도가 낮은 구간입니다. 장기 모니터링 추천.")
else:
    evals.append("✅ [종합진단] 재무 및 수급 양호, 단기 상승세 진입 가능성 관찰.")
for e in evals:
    st.markdown("- " + e)

# ====== 관련 뉴스 ======
st.subheader("📰 관련 뉴스")
try:
    news_list = fetch_google_news(selected_name)
    for title, url in news_list:
        st.markdown(f"- [{title}]({url})")
except Exception:
    st.info("뉴스 데이터를 불러올 수 없습니다.")

# ====== 투자 매력 점수 TOP10 ======
st.subheader("투자 성향(aggressive) 통합 점수 TOP 10")
score_top10 = df.sort_values("score", ascending=False).head(10)
top10_options = score_top10["종목명"].tolist()
top10_sel = st.selectbox("TOP10 종목명", top10_options, key="top10")
st.dataframe(score_top10, use_container_width=True)

# ====== 급등 예상 종목 TOP10 ======
st.subheader("🔥 급등 예상종목 TOP10 (거래량/신호기준)")
# 예시: 거래량 급증, 볼린저밴드 돌파, RSI < 30 등
vol_col = "거래량" if "거래량" in df.columns else None
if vol_col:
    surge = df.sort_values(vol_col, ascending=False).head(10)
    surge_options = surge["종목명"].tolist()
    surge_sel = st.selectbox("🔥 급등 예상종목 TOP10", surge_options, key="surge10")
    st.dataframe(surge, use_container_width=True)
else:
    st.info("급등 예상 종목 계산을 위한 거래량 컬럼이 없습니다.")

# ====== 로고 ======
st.markdown("---")
st.image("logo_tynex.png", width=300, output_format="auto", use_column_width=False, caption=None)

# ====== 기타 ======
st.caption("© TYNEX All rights reserved.")
