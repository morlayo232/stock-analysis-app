import streamlit as st
import pandas as pd
import numpy as np
import os
from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd
from update_stock_database import update_single_stock, update_database

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

# 종목 검색
raw_df = pd.read_csv("filtered_stocks.csv")
all_names = list(raw_df["종목명"].dropna().unique())
search = st.selectbox("🔎 종목 검색", all_names, index=0, help="종목명 일부 입력 추천")

code = raw_df.loc[raw_df["종목명"] == search, "종목코드"].values[0]
st.markdown(f"### {search} ({code})", unsafe_allow_html=True)

# 개별/전체 갱신 버튼
col1, col2 = st.columns([1,1])
with col1:
    if st.button("🔄 개별갱신"):
        update_single_stock(code)
with col2:
    if st.button("🔄 전체갱신"):
        update_database()

# 최신 재무정보 2열(컬럼) + 툴팁
info = raw_df[raw_df["종목코드"] == code].iloc[0]
col3, col4 = st.columns(2)
fields = [("PER", "주가수익비율, 낮을수록 저평가 가능성"), 
          ("PBR", "주가순자산비율, 1보다 낮으면 저평가"), 
          ("EPS", "주당순이익, 높을수록 좋음"), 
          ("BPS", "주당순자산, 높을수록 자산 많음"), 
          ("배당률", "배당수익률, 높을수록 현금흐름"), 
          ("score", "내부 통합점수, 높을수록 투자매력")]
for i in range(0, len(fields), 2):
    with col3:
        f, expl = fields[i]
        val = info[f] if f in info else "-"
        st.markdown(
            f"<b>{f}</b> <span style='font-size:11px;' title='{expl}'>❔</span><br><span style='font-size:32px'>{val:,.2f if isinstance(val, (int,float)) else val}</span>", 
            unsafe_allow_html=True
        )
    if i+1 < len(fields):
        with col4:
            f, expl = fields[i+1]
            val = info[f] if f in info else "-"
            st.markdown(
                f"<b>{f}</b> <span style='font-size:11px;' title='{expl}'>❔</span><br><span style='font-size:32px'>{val:,.2f if isinstance(val, (int,float)) else val}</span>", 
                unsafe_allow_html=True
            )

# 차트구간
price_path = f"prices/{code}.csv"
if os.path.exists(price_path):
    df_price = pd.read_csv(price_path)
    if not df_price.empty:
        fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_rsi, use_container_width=True)
        st.plotly_chart(fig_macd, use_container_width=True)
    else:
        st.warning("주가 데이터가 없습니다.")
else:
    st.warning("주가 데이터가 없습니다.")

# 차트/지표 도움말
with st.expander("📈 차트/지표 도움말 (클릭)"):
    st.markdown("""
- **EMA(20)**: 최근 20일의 지수이동평균선(단기 추세)
- **볼린저밴드**: 변동성(표준편차) 기준 상·하한 범위
- **RSI**: 과매수(>60), 과매도(<40) 신호
- **MACD**: 단기/장기 추세선, 크로스는 매매시그널
- **골든/데드크로스**: 상승/하락 전환 포착
""")

# 추천 매수/매도
st.subheader("추천 매수가/매도가")
# (추천가 연산 함수 추가 가능)

# 종목 평가 및 전략
st.markdown("### 📋 종목 평가 및 투자 전략(전문가 의견)")
with st.container():
    st.markdown(
        f"""
- <b>[종합진단]</b> PER이 {info['PER']}로 업종평균 대비 {"저평가" if info['PER'] < 10 else "고평가"} 상태입니다. 
- <b>[배당]</b> 배당수익률이 {info['배당률']}%로{" "}
{"동종업계 평균을 상회합니다." if info['배당률'] > 2 else "아직 낮은 편입니다."}
- <b>[안정성]</b> PBR {info['PBR']}는 {"1 미만으로 안정적입니다." if info['PBR'] < 1 else "높은 편이니 참고바랍니다."}
- <b>[기타]</b> 최근 뉴스/이슈, 시장상황 등을 종합적으로 고려하십시오.
""", unsafe_allow_html=True
    )

# 관련 뉴스
st.markdown("### 📰 관련 뉴스")
for n in fetch_google_news(search)[:5]:
    st.markdown(f"- {n}")

# TOP10/급등예상 TOP10
st.markdown("## 투자 성향별 TOP10 및 급등 예상 종목")
st.info("점수 산정 방식: score = -0.1*PER -0.2*PBR +0.2*EPS/BPS +0.05*배당률 +0.1*log(거래량)")
st.info("급등 예상 종목: 최근 거래량 급증 + 단기수익률 급등 + 변동성 등으로 산정")

top10 = raw_df.sort_values("score", ascending=False).head(10)
st.markdown("#### 투자 매력점수 TOP10")
top10_name = st.selectbox("투자 매력 TOP10 종목 선택", top10["종목명"].values)
st.dataframe(top10, use_container_width=True)

st.markdown("#### 🔥 급등 예상종목 TOP10")
hot10 = raw_df.sort_values("거래량", ascending=False).head(10)
hot10_name = st.selectbox("급등 예상 TOP10 종목 선택", hot10["종목명"].values)
st.dataframe(hot10, use_container_width=True)

# 하단 로고
st.image("logo_tynex.png", width=300, use_column_width=False, caption=None)
