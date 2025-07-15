# 📄 app.py

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

start = "20240101"
end = datetime.today().strftime("%Y%m%d")
df_price = stock.get_market_ohlcv_by_date(start, end, code)

if df_price is None or df_price.empty:
    st.warning("가격 데이터 추적 실패")
else:
    df_price = add_tech_indicators(df_price)
    # 3분할 차트(종가+EMA, RSI, MACD) 표시
    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")
    st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")
    st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

    # 지표 해설/초보 투자TIP 안내
    st.info(
        "- **종가/EMA(20):** 단기 추세·매매 타이밍 참고. EMA 하락돌파 후 반등, 상승돌파 후 조정 체크!\n"
        "- **골든크로스:** 상승전환 시그널, **데드크로스:** 하락전환 시그널(실전에서는 한 박자 뒤 조치 권고)\n"
        "- **RSI:** 30 아래 과매도, 70 위 과매수(과매도=반등, 과매수=조정, 단 급등/급락 장세는 예외)\n"
        "- **MACD:** MACD가 Signal을 상향돌파(매수), 하향돌파(매도), 0선 부근 전환은 추세 반전 가능성"
    )

    st.subheader("📌 추천 매수가 / 매도가")
    required_cols = ["RSI", "MACD", "Signal", "EMA20"]
    if (
        any(col not in df_price.columns for col in required_cols) or
        df_price[required_cols].isna().any().any() or
        len(df_price) < 3
    ):
        st.info("기술적 지표 데이터가 부족하여 추천가를 계산할 수 없습니다.")
    else:
        try:
            price_now = df_price['종가'].iloc[-1]
            price_std = df_price['종가'].std()
            ema_now = df_price['EMA20'].iloc[-1]
            rsi_now = df_price['RSI'].iloc[-1]
            rsi_prev = df_price['RSI'].iloc[-2]
            macd_now = df_price['MACD'].iloc[-1]
            macd_prev = df_price['MACD'].iloc[-2]
            signal_now = df_price['Signal'].iloc[-1]
            signal_prev = df_price['Signal'].iloc[-2]

            buy_price = None
            sell_price = None

            if (
                (rsi_now < 35 and rsi_prev < rsi_now) or
                (price_now < ema_now)
            ) and (
                macd_now > signal_now and macd_prev < signal_prev
            ):
                buy_price = price_now - price_std * 0.5

            if (
                (rsi_now > 65 and rsi_prev > rsi_now) or
                (price_now > ema_now)
            ) and (
                macd_now < signal_now and macd_prev > signal_prev
            ):
                sell_price = price_now + price_std * 0.8

            col1, col2 = st.columns(2)

            with col1:
                if buy_price:
                    st.metric("추천 매수가", f"{buy_price:,.0f} 원")
                else:
                    st.metric("추천 매수가", "조건 미충족")

            with col2:
                if sell_price:
                    st.metric("추천 매도가", f"{sell_price:,.0f} 원")
                else:
                    st.metric("추천 매도가", "조건 미충족")

        except Exception:
            st.info("추천가 계산 중 오류가 발생했습니다.")

    # ======= 종목 평가 및 투자 전략 (전문가형) =======
    st.subheader("📋 종목 평가 및 투자 전략 (전문가 의견)")
    try:
        eval_lines = []
        per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
        if per < 7:
            eval_lines.append("✔️ [PER] 현 주가수익비율(PER)이 7 미만입니다. 이는 이익 대비 현재 주가가 낮게 형성돼 있다는 뜻으로, 실적 안정성이 유지된다면 저평가된 종목으로 볼 수 있습니다. (초보 Tip: PER이 낮을수록 저평가, 단 업종별 차이 주의)")
        elif per > 20:
            eval_lines.append("⚠️ [PER] PER이 20을 초과합니다. 단기적으로 고평가 구간에 있을 수 있으므로 실적 성장 지속성, 업종 특성도 함께 체크하세요.")
        pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
        if pbr < 1:
            eval_lines.append("✔️ [PBR] PBR이 1 미만으로, 회사의 순자산보다 낮게 거래되고 있습니다. 이는 청산가치보다도 저렴하단 의미로, 가치주 투자자에게 매력적인 구간입니다.")
        elif pbr > 2:
            eval_lines.append("⚠️ [PBR] PBR이 2를 초과합니다. 시장에서 미래 성장성을 선반영하고 있거나, 자산가치에 비해 과도하게 평가받는 구간일 수 있습니다.")
        div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
        if div > 3:
            eval_lines.append("💰 [배당] 배당수익률이 3%를 넘어, 배당 투자 관점에서도 긍정적입니다. (초보 Tip: 배당주는 변동성 낮고 장기 투자자에게 유리)")
        elif div < 1:
            eval_lines.append("💡 [배당] 배당수익률이 1% 미만으로 낮은 편입니다. 성장주 또는 재투자형 기업일 가능성이 높으니 목적에 맞게 접근하세요.")
        eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
        if eps > 0:
            eval_lines.append("🟢 [EPS] 최근 분기 흑자 유지, 재무적으로 견조합니다.")
        else:
            eval_lines.append("🔴 [EPS] 최근 분기 적자, 단기적 재무 구조점검 필요.")
        bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
        if bps > 0:
            eval_lines.append("🟢 [BPS] 자산가치 기반으로도 안정적입니다.")
        if "RSI" in df_price.columns and not np.isnan(df_price['RSI'].iloc[-1]):
            rsi_now = df_price['RSI'].iloc[-1]
            if rsi_now < 35:
                eval_lines.append("📉 [RSI] 단기 과매도 상태입니다. 조정 후 반등 가능성 체크 필요.")
            elif rsi_now > 65:
                eval_lines.append("📈 [RSI] 단기 과매수 구간입니다. 단기 차익 실현 구간일 수 있습니다.")
        score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
        q80 = scored_df["score"].quantile(0.8)
        q20 = scored_df["score"].quantile(0.2)
        if score > q80:
            eval_lines.append("✅ [종합 진단] 전문가 의견: 현재 투자 매력도가 매우 높은 편입니다. 성장성, 수익성, 안정성 지표 모두 양호하므로 적극적 매수 또는 분할 매수 전략을 고려해볼 만합니다.")
        elif score < q20:
            eval_lines.append("❌ [종합 진단] 전문가 의견: 투자 매력도가 낮은 구간입니다. 추가 모니터링 또는 조정 후 진입을 권장합니다.")
        else:
            eval_lines.append("☑️ [종합 진단] 전문가 의견: 시장 평균 수준. 가격 조정 시 분할 매수, 장기 투자 전략이 적합합니다.")
        for line in eval_lines:
            st.markdown(f"- {line}")
    except Exception:
        st.info("종목 평가/전략을 분석할 데이터가 부족합니다.")

st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")

if st.button("데이터 수동 갱신"):
    from update_stock_database import update_database
    try:
        update_database()
        st.success("갱신 완료! 다시 골드리 해주세요")
    except Exception:
        st.error("수동 갱신 실패")
