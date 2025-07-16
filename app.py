# app.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath("modules"))

from modules.score_utils import finalize_scores, assess_reliability
from modules.fetch_news import fetch_google_news
from modules.chart_utils import plot_price_rsi_macd
from modules.calculate_indicators import add_tech_indicators
from pykrx import stock

# 이하 동일

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

@st.cache_data
def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv")
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
            df = pd.read_csv("filtered_stocks.csv")
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

# TOP10 종목 빠른 선택 (표 위)
st.subheader("TOP10 종목 빠른 선택")
quick_selected = st.selectbox("TOP10 종목명", top10["종목명"].tolist(), key="top10_selectbox")

st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[
    ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급"]
])

# 아래 종목 검색
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

# 최신 재무 정보 표시 (그래프 위)
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

start = "20240101"
end = datetime.today().strftime("%Y%m%d")
df_price = stock.get_market_ohlcv_by_date(start, end, code)

if df_price is None or df_price.empty:
    st.warning("가격 데이터 추적 실패")
else:
    df_price = add_tech_indicators(df_price)
    # 볼린저밴드 계산
    df_price["MA20"] = df_price["종가"].rolling(window=20).mean()
    df_price["STD20"] = df_price["종가"].rolling(window=20).std()
    df_price["BB_low"] = df_price["MA20"] - 2 * df_price["STD20"]
    df_price["BB_high"] = df_price["MA20"] + 2 * df_price["STD20"]

    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")
    st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")
    st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

    st.info(
        "- **종가/EMA(20):** 단기 추세와 매매 타이밍 참고\n"
        "- **볼린저밴드:** 주가가 상단선 돌파시 과열, 하단선 이탈시 과매도·반등 신호로 해석\n"
        "- **골든/데드크로스:** EMA20 기준, 상승·하락전환 신호(실전에서는 한 박자 뒤 액션 권장)\n"
        "- **RSI:** 30↓ 과매도(반등), 70↑ 과매수(조정)\n"
        "- **MACD:** Signal 돌파는 매수/매도 신호, 0선 전환시 추세 반전 가능성\n"
        "※ 볼린저밴드는 가격이 밴드 밖(상단, 하단)으로 나가면 되돌림 확률이 높아집니다. 하단 돌파시 저점 매수 참고!"
    )

    st.subheader("📌 추천 매수가 / 매도가")
    required_cols = ["RSI", "MACD", "Signal", "EMA20", "BB_low", "BB_high"]
    st.write("추천가 관련 최근 값:", df_price[required_cols + ['종가']].tail())

    # 추천가 산정 (볼린저밴드 활용, 과매도/과매수 + 이탈조건)
    window = 5
    recent = df_price.tail(window).reset_index()
    buy_price = None
    sell_price = None
    buy_date = None
    sell_date = None
    for i in range(1, len(recent)):
        # 매수: 종가가 BB_low 아래, RSI < 35, MACD > Signal
        if (
            (recent['종가'].iloc[i] < recent['BB_low'].iloc[i]) and
            (recent['RSI'].iloc[i] < 35) and
            (recent['MACD'].iloc[i] > recent['Signal'].iloc[i])
        ):
            buy_price = recent['종가'].iloc[i]
            buy_date = recent['날짜'].iloc[i] if '날짜' in recent.columns else recent.index[i]
        # 매도: 종가가 BB_high 위, RSI > 65, MACD < Signal
        if (
            (recent['종가'].iloc[i] > recent['BB_high'].iloc[i]) and
            (recent['RSI'].iloc[i] > 65) and
            (recent['MACD'].iloc[i] < recent['Signal'].iloc[i])
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
            eval_lines.append("✔️ [PER] 현 주가수익비율(PER)이 7 미만, 저평가 구간입니다.")
        elif per > 20:
            eval_lines.append("⚠️ [PER] PER이 20 초과, 단기적으로 고평가 구간일 수 있습니다.")
        pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
        if pbr < 1:
            eval_lines.append("✔️ [PBR] PBR이 1 미만, 자산가치보다 저평가 구간.")
        elif pbr > 2:
            eval_lines.append("⚠️ [PBR] PBR이 2 초과.")
        div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
        if div > 3:
            eval_lines.append("💰 [배당] 배당수익률이 3% 초과, 배당 투자 관점에서도 긍정적.")
        elif div < 1:
            eval_lines.append("💡 [배당] 배당수익률이 1% 미만.")
        eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
        if eps > 0:
            eval_lines.append("🟢 [EPS] 최근 분기 흑자 유지, 재무적으로 견조.")
        else:
            eval_lines.append("🔴 [EPS] 최근 분기 적자, 단기적 재무 구조점검 필요.")
        bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
        if bps > 0:
            eval_lines.append("🟢 [BPS] 자산가치 기반으로도 안정적.")
        # 볼린저밴드 상태 평가
        if 'BB_low' in df_price.columns and 'BB_high' in df_price.columns:
            last_close = df_price['종가'].iloc[-1]
            last_bb_low = df_price['BB_low'].iloc[-1]
            last_bb_high = df_price['BB_high'].iloc[-1]
            if last_close < last_bb_low:
                eval_lines.append("📉 [볼린저밴드] 과매도 구간(하단선 이탈), 저점 매수 관심 구간입니다.")
            elif last_close > last_bb_high:
                eval_lines.append("📈 [볼린저밴드] 과매수 구간(상단선 돌파), 차익실현 구간일 수 있습니다.")
        # RSI
        if "RSI" in df_price.columns and not np.isnan(df_price['RSI'].iloc[-1]):
            rsi_now = df_price['RSI'].iloc[-1]
            if rsi_now < 35:
                eval_lines.append("📉 [RSI] 단기 과매도 상태, 조정 후 반등 가능성.")
            elif rsi_now > 65:
                eval_lines.append("📈 [RSI] 단기 과매수 구간, 차익 실현 구간일 수 있음.")
        score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
        q80 = scored_df["score"].quantile(0.8)
        q20 = scored_df["score"].quantile(0.2)
        if score > q80:
            eval_lines.append("✅ [종합 진단] 현재 투자 매력도 매우 높음. 성장성, 수익성, 안정성 지표 모두 양호. 적극적 매수 또는 분할매수 고려.")
        elif score < q20:
            eval_lines.append("❌ [종합 진단] 투자 매력도 낮음. 추가 모니터링 또는 조정 후 진입 권장.")
        else:
            eval_lines.append("☑️ [종합 진단] 시장 평균 수준. 가격 조정 시 분할 매수, 장기 투자 전략 적합.")
        for line in eval_lines:
            st.markdown(f"- {line}")
    except Exception:
        st.info("종목 평가/전략을 분석할 데이터가 부족합니다.")

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
