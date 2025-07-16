# app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from modules.fetch_price import fetch_price
from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd

st.set_page_config(page_title="투자 매니저", layout="wide")

st.title("투자 매니저")

# 1. 데이터 로드 및 예외처리
try:
    df = pd.read_csv('filtered_stocks.csv', dtype={'종목코드': str})
except Exception as e:
    st.error("데이터 파일을 불러올 수 없습니다.")
    st.stop()

if df.empty:
    st.error("분석 가능한 데이터가 없습니다.")
    st.stop()

# 2. 종목 검색창 (자동완성)
st.subheader("🔍 종목 검색")
종목명_코드 = df['종목명'] + " (" + df['종목코드'] + ")"
검색 = st.text_input("종목명 또는 코드 입력", value="", key="search")
추천목록 = 종목명_코드[df['종목명'].str.contains(검색) | df['종목코드'].str.contains(검색)].tolist() if 검색 else 종목명_코드.tolist()
selected = st.selectbox("", options=추천목록)
선택코드 = selected.split("(")[-1].replace(")", "")

# 3. 해당 종목 데이터
data = df[df['종목코드'] == 선택코드]
if data.empty:
    st.warning("해당 종목 데이터가 없습니다.")
    st.stop()
data = data.iloc[0]

# 4. 최신 재무정보 2열 표시
st.subheader("📊 최신 재무 정보")
fin_cols = ["PER", "PBR", "EPS", "BPS", "배당률", "score"]
fin_names = ["PER", "PBR", "EPS", "BPS", "배당률(%)", "점수"]
cols = st.columns(2)
for i, f in enumerate(fin_cols):
    try:
        val = data[f]
    except Exception:
        val = "-"
    cols[i % 2].metric(fin_names[i], f"{val:,.2f}" if pd.notnull(val) and f!="score" else val)

# 5. 주가/지표 데이터 로드 및 예외처리
df_price = fetch_price(선택코드)
if df_price is None or df_price.empty:
    st.warning("주가 데이터가 없습니다.")
    st.stop()

# 6. 차트 표시
fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
if fig is not None:
    st.plotly_chart(fig, use_container_width=True)
if fig_rsi is not None:
    st.plotly_chart(fig_rsi, use_container_width=True)
if fig_macd is not None:
    st.plotly_chart(fig_macd, use_container_width=True)

# 7. 추천 매수/매도가 (MACD 아래 배치)
def calc_recommend(df_price):
    try:
        # 예시: EMA20 골든/데드크로스, MACD Signal, 볼린저밴드, 거래량 등 활용
        최근 = df_price.iloc[-1]
        매수가 = np.nan
        매도가 = np.nan
        매수가일 = ""
        매도가일 = ""
        # 골든크로스 조건
        if '골든크로스' in df_price.columns:
            gold = df_price[df_price['골든크로스'] == 1]
            if not gold.empty:
                매수가 = gold['종가'].iloc[-1]
                매수가일 = gold.index[-1].strftime("%Y-%m-%d")
        # 데드크로스 조건
        if '데드크로스' in df_price.columns:
            dead = df_price[df_price['데드크로스'] == 1]
            if not dead.empty:
                매도가 = dead['종가'].iloc[-1]
                매도가일 = dead.index[-1].strftime("%Y-%m-%d")
        return 매수가, 매수가일, 매도가, 매도가일
    except:
        return np.nan, "", np.nan, ""

매수가, 매수가일, 매도가, 매도가일 = calc_recommend(df_price)
if not np.isnan(매수가):
    st.info(f"📌 추천 매수가: {매수가:,.0f}원 ({매수가일})")
if not np.isnan(매도가):
    st.info(f"📌 추천 매도가: {매도가:,.0f}원 ({매도가일})")

# 8. 차트 도움말
with st.expander("📈 차트/지표 해설 (주식 초보를 위한 설명)", expanded=False):
    st.markdown("""
- **종가/EMA(20)/볼린저밴드**: 단기 추세/과매수·과매도 구간 참고. EMA 하락돌파 후 반등/상승돌파 후 조정 체크.
- **RSI(14)**: 40 이하 과매도, 60 이상 과매수.
- **MACD**: 시그널 상향돌파(매수), 하향돌파(매도) 신호.
- **볼린저밴드**: 상단 근접시 과열, 하단 근접시 저평가 가능.
""")

# 9. 종목 평가/투자 전략(설득력 있는 전문가 톤)
st.subheader("📝 종목 평가 및 투자 전략(전문가 의견)")
평가 = []
if pd.notnull(data["PBR"]) and float(data["PBR"]) > 2:
    평가.append("⚠️ [PBR] PBR이 2를 초과합니다. 고평가 구간일 수 있어 신중한 접근이 필요합니다.")
if pd.notnull(data["배당률"]) and float(data["배당률"]) < 1:
    평가.append("💡 [배당] 배당수익률이 1% 미만으로 낮습니다.")
if len(평가) == 0:
    평가.append("ℹ️ [종합진단] 무난한 구간입니다. 시장 상황과 함께 참고.")

for msg in 평가:
    st.markdown("- " + msg)

# 10. 관련 뉴스
st.subheader("📰 관련 뉴스")
news = fetch_google_news(data['종목명'])
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("관련 뉴스가 없습니다.")

# 11. 투자매력 TOP10, 급등예상 TOP10
st.subheader("투자 성향별 TOP10 및 급등 예상 종목")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**투자 매력점수 TOP10**")
    st.dataframe(df.sort_values("score", ascending=False).head(10), use_container_width=True)
with col2:
    st.markdown("**🔥 급등 예상종목 TOP10**")
    # 거래량 컬럼 없을 시 score로 대체
    급등기준 = "거래량" if "거래량" in df.columns else "score"
    st.dataframe(df.sort_values(급등기준, ascending=False).head(10), use_container_width=True)

# 12. 하단 로고
st.markdown("---")
st.image("logo_tynex.png", use_column_width=True)
