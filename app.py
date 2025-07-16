import streamlit as st
import pandas as pd
from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd
from update_stock_database import update_single_stock, update_database

st.set_page_config(page_title="투자 매니저", layout="wide")

def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv")
        expected = [
            "종목명", "종목코드", "현재가", "거래량", "거래량평균20", "PER", "PBR", "EPS", "BPS",
            "배당률", "Signal", "score", "신뢰등급"
        ]
        # 누락 컬럼 예외처리
        for col in expected:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

# 데이터 불러오기
raw_df = load_filtered_data()
if raw_df.empty:
    st.error("데이터프레임이 비어 있습니다.")
    st.stop()

scored_df = finalize_scores(raw_df)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)

st.markdown(f"<h1 style='font-size:3rem; text-align:center;'>투자 매니저</h1>", unsafe_allow_html=True)

# 종목검색창(자동완성)
st.markdown("#### 🔍 종목 검색")
selected_name = st.text_input("종목명 또는 코드 입력", "")

# 선택 종목 처리
def find_stock(df, key):
    if key.isdigit():
        res = df[df["종목코드"].str.contains(key)]
    else:
        res = df[df["종목명"].str.contains(key, case=False, na=False)]
    return res.iloc[0] if not res.empty else None

if selected_name:
    data = find_stock(scored_df, selected_name)
else:
    data = scored_df.iloc[0]

if data is None:
    st.warning("종목을 찾을 수 없습니다.")
    st.stop()

st.markdown(f"### {data['종목명']} ({data['종목코드']})", unsafe_allow_html=True)

# 개별/전체 갱신 버튼
col_g1, col_g2, col_g3 = st.columns([1,1,8])
with col_g1:
    if st.button("🔄 개별갱신"):
        update_single_stock(data['종목코드'])
        st.success("개별 종목 데이터가 갱신되었습니다.")
with col_g2:
    if st.button("🌀 전체갱신"):
        update_database()
        st.success("전체 데이터가 갱신되었습니다.")

# 최신 재무정보 (2열)
st.markdown("#### <img src='https://img.icons8.com/color/48/000000/combo-chart.png' width=32 style='vertical-align:middle'> 최신 재무 정보", unsafe_allow_html=True)
col_f1, col_f2 = st.columns(2)
fields1 = ["PER", "EPS", "점수"]
fields2 = ["PBR", "BPS", "배당률"]

with col_f1:
    for f in fields1:
        val = data.get(f, None)
        st.metric(f, f"{val:,.2f}" if isinstance(val, (int, float)) else val)
with col_f2:
    for f in fields2:
        val = data.get(f, None)
        st.metric(f, f"{val:,.2f}" if isinstance(val, (int, float)) else val)

# 차트 및 지표 시각화
st.markdown("#### 가격(종가), EMA(20), 볼린저밴드")
try:
    df_price = pd.read_csv(f"prices/{data['종목코드']}.csv")
    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig_rsi, use_container_width=True)
    st.plotly_chart(fig_macd, use_container_width=True)
except Exception as e:
    st.warning("주가 데이터가 없습니다.")

# 차트/지표 설명(초보용)
with st.expander("📈 차트/지표 도움말 (클릭)"):
    st.markdown("""
- **EMA(20):** 20일 지수이동평균선, 단기 추세와 매매 타이밍 확인
- **볼린저밴드:** 표준편차 2배 구간 표시, 상단 도달 시 과열, 하단 도달 시 과매도 경계
- **RSI:** 40 아래 과매도, 60 위 과매수
- **MACD:** 시그널 상향돌파(매수), 하향돌파(매도) 시점 참고
    """)

# 추천 매수/매도가 표시
if "추천매수" in data and "추천매도" in data:
    st.info(f"📌 추천 매수가: {data['추천매수']:,}원 / 추천 매도가: {data['추천매도']:,}원")
else:
    st.info("추천 매수/매도가 준비되지 않았습니다.")

# 종목 평가/투자전략 전문가 의견 스타일
st.markdown("#### 📋 종목 평가 및 투자 전략(전문가 의견)")
eval_msgs = []
if data['PBR'] and data['PBR'] > 2:
    eval_msgs.append("⚠️ [PBR] 기업 가치에 비해 주가가 다소 높습니다.")
if data['배당률'] and data['배당률'] < 1:
    eval_msgs.append("💡 [배당] 배당수익률이 1% 미만으로 낮습니다.")
if not eval_msgs:
    eval_msgs.append("ℹ️ [종합진단] 무난한 구간입니다. 시장 상황과 함께 참고.")
for m in eval_msgs:
    st.markdown(f"- {m}")

# 관련 뉴스
st.markdown("#### 📰 관련 뉴스")
try:
    news = fetch_google_news(data['종목명'])
    for n in news:
        st.markdown(f"- {n}")
except Exception as e:
    st.warning("관련 뉴스를 불러올 수 없습니다.")

st.markdown("---")

# 투자매력 TOP10, 급등예상 TOP10
st.markdown("#### 투자 성향별 TOP10 및 급등 예상 종목")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**투자 매력점수 TOP10**")
    st.dataframe(scored_df.sort_values("score", ascending=False).head(10), use_container_width=True)
with col2:
    st.markdown("**🔥 급등 예상종목 TOP10**")
    급등기준 = "거래량" if "거래량" in scored_df.columns else "score"
    st.dataframe(scored_df.sort_values(급등기준, ascending=False).head(10), use_container_width=True)

# 로고
st.markdown(
    "<div style='display:flex;justify-content:center;align-items:center;'>"
    "<img src='https://raw.githubusercontent.com/morlayo232/stock-analysis-app/main/logo_tynex.png' width='200'></div>",
    unsafe_allow_html=True
)
