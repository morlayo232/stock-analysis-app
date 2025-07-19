import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath("modules"))

from score_utils import finalize_scores, assess_reliability
from fetch_news import fetch_google_news
from chart_utils import plot_price_rsi_macd
from calculate_indicators import add_tech_indicators
from datetime import datetime
from pykrx import stock

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

@st.cache_data(ttl=3600, show_spinner=False)
def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
        expected = [
            "종목명", "종목코드", "현재가",
            "PER", "PBR", "EPS", "BPS", "배당률"
        ]
        for col in expected:
            if col not in df.columns:
                df[col] = np.nan
        return df
    except Exception:
        from update_stock_database import update_database
        try:
            update_database()
            df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
            for col in expected:
                if col not in df.columns:
                    df[col] = np.nan
            return df
        except Exception:
            return pd.DataFrame()

style = st.sidebar.radio(
    "투자 성향", ["aggressive", "stable", "dividend"], horizontal=True
)

raw_df = load_filtered_data()
if not isinstance(raw_df, pd.DataFrame):
    st.error("데이터가 DataFrame 형식이 아닙니다.")
    st.stop()

if raw_df.empty:
    st.error("데이터프레임이 비어 있습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
top10 = scored_df.sort_values("score", ascending=False).head(10)

st.subheader("TOP10 종목 빠른 선택")
quick_selected = st.selectbox("TOP10 종목명", top10["종목명"].tolist(), key="top10_selectbox")

st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[
    ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급"]
])

st.subheader("종목 검색")
keyword = st.text_input("종목명을 입력하세요")

if keyword:
    filtered = scored_df[scored_df["종목명"].str.contains(keyword, case=False, na=False)]
    select_candidates = filtered["종목명"].tolist()
    default_index = 0
elif quick_selected:
    select_candidates = [quick_selected]
    default_index = 0
else:
    select_candidates = scored_df["종목명"].tolist()
    default_index = 0

if select_candidates:
    selected = st.selectbox("종목 선택", select_candidates, index=default_index, key="main_selectbox")
    code = scored_df[scored_df["종목명"] == selected]["종목코드"].values[0]
else:
    st.warning("해당 종목이 없습니다.")
    st.stop()

st.subheader("📊 최신 재무 정보")
try:
    info_row = scored_df[scored_df["종목명"] == selected].iloc[0]
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("PER", f"{info_row['PER']:.2f}" if pd.notna(info_row['PER']) else "-")
    col2.metric("PBR", f"{info_row['PBR']:.2f}" if pd.notna(info_row['PBR']) else "-")
    col3.metric("EPS", f"{int(info_row['EPS']):,}" if pd.notna(info_row['EPS']) else "-")
    col4.metric("BPS", f"{int(info_row['BPS']):,}" if pd.notna(info_row['BPS']) else "-")
    col5.metric("배당률(%)", f"{info_row['배당률']:.2f}" if pd.notna(info_row['배당률']) else "-")
    col6.metric("점수", f"{info_row['score']:.3f}" if pd.notna(info_row['score']) else "-")
except Exception:
    st.info("재무 데이터가 부족합니다.")

start = (datetime.today() - pd.Timedelta(days=365)).strftime("%Y%m%d")
end = datetime.today().strftime("%Y%m%d")
df_price = stock.get_market_ohlcv_by_date(start, end, code)

if df_price is None or df_price.empty:
    st.warning("가격 데이터 추적 실패")
else:
    df_price = add_tech_indicators(df_price)

    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    fig.update_layout(height=520)
    fig_rsi.update_layout(height=300)
    fig_macd.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")
    st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")
    st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

st.info(
    "- **종가/EMA(20):** 단기 추세·매매 타이밍 참고.\n"
    "- **골든크로스:** 상승전환 시그널, **데드크로스:** 하락전환 시그널\n"
    "- **RSI:** 30 아래 과매도, 70 위 과매수\n"
    "- **MACD:** MACD가 Signal을 상향돌파(매수), 하향돌파(매도)"
)

st.subheader("📌 추천 매수가 / 매도가")
required_cols = ["RSI_14", "MACD", "MACD_SIGNAL", "EMA_20"]
st.write("추천가 관련 최근 값:", df_price[required_cols + ['종가']].tail())

if not all(col in df_price.columns for col in required_cols):
    st.info("기술적 지표 컬럼이 부족합니다.")
elif df_price[required_cols].tail(3).isna().any().any():
    st.info("기술적 지표의 최근 값에 결측치가 있어 추천가를 계산할 수 없습니다.")
else:
    window = 5
    recent = df_price.tail(window).reset_index()
    buy_price = None
    sell_price = None
    buy_date = None
    sell_date = None
    for i in range(1, len(recent)):
        if (
            (recent['RSI_14'].iloc[i] < 35 and recent['RSI_14'].iloc[i-1] < recent['RSI_14'].iloc[i]) or
            (recent['종가'].iloc[i] < recent['EMA_20'].iloc[i])
        ) and (
            recent['MACD'].iloc[i] > recent['MACD_SIGNAL'].iloc[i] and recent['MACD'].iloc[i-1] < recent['MACD_SIGNAL'].iloc[i-1]
        ):
            buy_price = recent['종가'].iloc[i]
            buy_date = recent['날짜'].iloc[i] if '날짜' in recent.columns else recent.index[i]
        if (
            (recent['RSI_14'].iloc[i] > 65 and recent['RSI_14'].iloc[i-1] > recent['RSI_14'].iloc[i]) or
            (recent['종가'].iloc[i] > recent['EMA_20'].iloc[i])
        ) and (
            recent['MACD'].iloc[i] < recent['MACD_SIGNAL'].iloc[i] and recent['MACD'].iloc[i-1] > recent['MACD_SIGNAL'].iloc[i-1]
        ):
            sell_price = recent['종가'].iloc[i]
            sell_date = recent['날짜'].iloc[i] if '날짜' in recent.columns else recent.index[i]

    col1, col2 = st.columns(2)
    with col1:
        if buy_price is not None:
            msg = f"{buy_price:,.0f} 원"
            if buy_date:
                msg += f"\n({buy_date} 신호)"
            st.metric("추천 매수가", msg)
        else:
            st.metric("추천 매수가", "조건 미충족")
    with col2:
        if sell_price is not None:
            msg = f"{sell_price:,.0f} 원"
            if sell_date:
                msg += f"\n({sell_date} 신호)"
            st.metric("추천 매도가", msg)
        else:
            st.metric("추천 매도가", "조건 미충족")

st.subheader("📋 종목 평가 및 투자 전략 (전문가 의견)")
try:
    eval_lines = []
    per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
    if per < 7:
        eval_lines.append("✔️ [PER] 현 주가수익비율(PER)이 7 미만입니다. 이는 저평가 가능성을 의미합니다.")
    elif per > 20:
        eval_lines.append("⚠️ [PER] PER이 20 초과, 고평가 구간일 수 있습니다.")
    pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
    if pbr < 1:
        eval_lines.append("✔️ [PBR] PBR이 1 미만, 자산가치보다 저렴합니다.")
    elif pbr > 2:
        eval_lines.append("⚠️ [PBR] PBR이 2 초과, 과대평가 가능성.")
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    if div > 3:
        eval_lines.append("💰 [배당] 배당수익률 3% 이상, 안정적 배당주.")
    elif div < 1:
        eval_lines.append("💡 [배당] 배당수익률 1% 미만, 성장주 가능성.")
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps > 0:
        eval_lines.append("🟢 [EPS] 최근 분기 흑자 유지.")
    else:
        eval_lines.append("🔴 [EPS] 최근 분기 적자, 주의 필요.")
    bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
    if bps > 0:
        eval_lines.append("🟢 [BPS] 자산가치 기반 안정적.")
    if "RSI_14" in df_price.columns and not np.isnan(df_price['RSI_14'].iloc[-1]):
        rsi_now = df_price['RSI_14'].iloc[-1]
        if rsi_now < 35:
            eval_lines.append("📉 [RSI] 단기 과매도 상태.")
        elif rsi_now > 65:
            eval_lines.append("📈 [RSI] 단기 과매수 상태.")
    score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
    q80 = scored_df["score"].quantile(0.8)
    q20 = scored_df["score"].quantile(0.2)
    if score > q80:
        eval_lines.append("✅ [종합 진단] 투자 매력도 매우 높음.")
    elif score < q20:
        eval_lines.append("❌ [종합 진단] 투자 매력도 낮음.")
    else:
        eval_lines.append("☑️ [종합 진단] 투자 매력도 보통.")
    for line in eval_lines:
        st.markdown(f"- {line}")
except Exception:
    st.info("종목 평가/전략 데이터를 불러올 수 없습니다.")

if st.button(f"🔄 {selected} 데이터만 즉시 갱신"):
    from update_stock_database import update_single_stock
    try:
        update_single_stock(code)
        st.success(f"{selected} 데이터만 갱신 완료!")
        st.cache_data.clear()
        raw_df = load_filtered_data()
        scored_df = finalize_scores(raw_df, style=style)
        scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
        top10 = scored_df.sort_values("score", ascending=False).head(10)
    except Exception:
        st.error("개별 종목 갱신 실패")

if st.button("🗂️ 전체 종목 수동 갱신"):
    from update_stock_database import update_database
    try:
        update_database()
        st.success("전체 데이터 갱신 완료!")
        st.cache_data.clear()
        raw_df = load_filtered_data()
        scored_df = finalize_scores(raw_df, style=style)
        scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
        top10 = scored_df.sort_values("score", ascending=False).head(10)
    except Exception:
        st.error("전체 갱신 실패")

st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")
