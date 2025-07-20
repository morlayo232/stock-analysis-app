# app.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from PIL import Image

sys.path.append(os.path.abspath("modules"))

from score_utils import finalize_scores, assess_reliability
from fetch_news import fetch_google_news
from chart_utils import plot_price_rsi_macd
from calculate_indicators import add_tech_indicators
from price_utils import calculate_recommended_sell
from datetime import datetime
from pykrx import stock

# 3등분 columns 사용해 중앙 열에 이미지 배치
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.write("")

with col2:
    try:
        logo_img = Image.open("logo_tynex.png")  # 로컬 파일
        st.image(logo_img, width=250)  # 크기 조절
    except Exception:
        st.write("로고 이미지 로드 실패")

with col3:
    st.write("")



@st.cache_data(ttl=3600, show_spinner=False)
def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
        expected = ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률"]
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

style = st.sidebar.radio("투자 성향", ["aggressive", "stable", "dividend"], horizontal=True)

raw_df = load_filtered_data()
if not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
top10 = scored_df.sort_values("score", ascending=False).head(10)

st.subheader("TOP10 종목 빠른 선택")
quick_selected = st.selectbox("TOP10 종목명", top10["종목명"].tolist(), key="top10_selectbox")

st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[["종목명","종목코드","현재가","PER","PBR","EPS","BPS","배당률","score","신뢰등급"]])

st.subheader("종목 검색")
keyword = st.text_input("종목명을 입력하세요")

if keyword:
    filtered = scored_df[scored_df["종목명"].str.contains(keyword, case=False, na=False)]
    select_candidates = filtered["종목명"].tolist()
else:
    select_candidates = [quick_selected] if quick_selected else scored_df["종목명"].tolist()

if select_candidates:
    selected = st.selectbox("종목 선택", select_candidates, index=0, key="main_selectbox")
    code = scored_df[scored_df["종목명"] == selected]["종목코드"].values[0]
else:
    st.warning("해당 종목이 없습니다.")
    st.stop()

st.subheader("📊 최신 재무 정보")
try:
    info_row = scored_df[scored_df["종목명"] == selected].iloc[0]
    cols = st.columns(6)
    cols[0].metric("PER", f"{info_row['PER']:.2f}" if pd.notna(info_row['PER']) else "-")
    cols[1].metric("PBR", f"{info_row['PBR']:.2f}" if pd.notna(info_row['PBR']) else "-")
    cols[2].metric("EPS", f"{int(info_row['EPS']):,}" if pd.notna(info_row['EPS']) else "-")
    cols[3].metric("BPS", f"{int(info_row['BPS']):,}" if pd.notna(info_row['BPS']) else "-")
    cols[4].metric("배당률(%)", f"{info_row['배당률']:.2f}" if pd.notna(info_row['배당률']) else "-")
    cols[5].metric("점수", f"{info_row['score']:.3f}" if pd.notna(info_row['score']) else "-")
except Exception:
    st.info("재무 데이터가 부족합니다.")

start = (datetime.today() - pd.Timedelta(days=365)).strftime("%Y%m%d")
end = datetime.today().strftime("%Y%m%d")
df_price = stock.get_market_ohlcv_by_date(start, end, code)

if df_price is None or df_price.empty:
    st.warning("가격 데이터가 없습니다.")
else:
    df_price = add_tech_indicators(df_price)
    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    fig.update_layout(height=400)
    fig_rsi.update_layout(height=400)
    fig_macd.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")
    st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")
    st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

st.info(
    "- **종가/EMA(20):** 단기 추세 및 매매 타이밍 참고\n"
    "- **골든크로스:** 상승전환 신호, 매수 타이밍으로 활용\n"
    "- **데드크로스:** 하락전환 신호, 주의 또는 매도 타이밍\n"
    "- **RSI:** 30 이하 과매도 신호, 반등 가능성 높음\n"
    "- **RSI:** 70 이상 과매수 신호, 조정 가능성 있음\n"
    "- **MACD:** MACD가 Signal 상향 돌파 시 매수 신호\n"
    "- **MACD:** MACD가 Signal 하향 돌파 시 매도 신호"
)

st.subheader("📌 추천 매수가 / 매도가")
required_cols = ["RSI_14", "MACD", "MACD_SIGNAL", "EMA_20"]
st.write("추천가 관련 최근 값:", df_price[required_cols + ['종가']].tail())

if not all(col in df_price.columns for col in required_cols):
    st.info("기술적 지표 컬럼이 부족합니다.")
elif df_price[required_cols].tail(3).isna().any().any():
    st.info("기술적 지표의 최근 값에 결측치가 있어 추천가 계산 불가")
else:
    recent = df_price.tail(5).reset_index()
    buy_price = None
    sell_price = None
    buy_date = None
    sell_date = None
    for i in range(1, len(recent)):
        if ((recent['RSI_14'].iloc[i] < 35 and recent['RSI_14'].iloc[i-1] < recent['RSI_14'].iloc[i]) or
            (recent['종가'].iloc[i] < recent['EMA_20'].iloc[i])) and \
            (recent['MACD'].iloc[i] > recent['MACD_SIGNAL'].iloc[i] and recent['MACD'].iloc[i-1] < recent['MACD_SIGNAL'].iloc[i-1]):
            buy_price = recent['종가'].iloc[i]
            buy_date = recent['날짜'].iloc[i] if '날짜' in recent.columns else recent.index[i]

        if ((recent['RSI_14'].iloc[i] > 65 and recent['RSI_14'].iloc[i-1] > recent['RSI_14'].iloc[i]) or
            (recent['종가'].iloc[i] > recent['EMA_20'].iloc[i])) and \
            (recent['MACD'].iloc[i] < recent['MACD_SIGNAL'].iloc[i] and recent['MACD'].iloc[i-1] > recent['MACD_SIGNAL'].iloc[i-1]):
            sell_price = recent['종가'].iloc[i]
            sell_date = recent['날짜'].iloc[i] if '날짜' in recent.columns else recent.index[i]

    c1, c2 = st.columns(2)
    with c1:
        if buy_price is not None:
            msg = f"{buy_price:,.0f} 원"
            if buy_date:
                msg += f"\n({buy_date} 신호)"
            st.metric("추천 매수가", msg)
        else:
            st.metric("추천 매수가", "조건 미충족")
    with c2:
        if sell_price is not None:
            msg = f"{sell_price:,.0f} 원"
            if sell_date:
                msg += f"\n({sell_date} 신호)"
            st.metric("추천 매도가", msg)
        else:
            st.metric("추천 매도가", "조건 미충족")

# 매수 가격 입력 및 추천 매도가 표시
st.subheader("📥 매수 가격 입력")
input_buy_price = st.number_input("현재 매수 가격을 입력하세요", min_value=0, step=100)

recommended_sell = None
if input_buy_price > 0 and (df_price is not None and not df_price.empty):
    recommended_sell = calculate_recommended_sell(input_buy_price, df_price)

c1, c2 = st.columns(2)
with c1:
    if input_buy_price > 0:
        st.metric("입력 매수가", f"{input_buy_price:,.0f} 원")
    else:
        st.metric("입력 매수가", "입력 없음")
with c2:
    if recommended_sell:
        st.metric("추천 매도가", f"{recommended_sell:,.0f} 원")
    else:
        st.metric("추천 매도가", "추천가 없음")

# 추천 매도가 근거 상세 설명
if recommended_sell:
    st.markdown("### 💡 추천 매도 가격 근거 상세 분석")
    explanations = []

    profit_ratio = (recommended_sell - input_buy_price) / input_buy_price * 100
    if profit_ratio >= 15:
        explanations.append(f"- 매수가 대비 {profit_ratio:.2f}% 이상 수익 실현 구간입니다. 단기 고수익 실현 타이밍으로 전문가들이 권장하는 매도 시점입니다.")
    elif profit_ratio >= 5:
        explanations.append(f"- 매수가 대비 약 {profit_ratio:.2f}% 수익권으로 분할 매도를 권장합니다.")
    elif profit_ratio > 0:
        explanations.append(f"- 매수가 대비 소폭 수익 상태이나 추가 상승 가능성도 있어 신중한 판단이 필요합니다.")
    else:
        explanations.append(f"- 현재 매수가 대비 손실 구간입니다. 손절 또는 모니터링 전략이 필요합니다.")

    if 'MACD' in df_price.columns and 'MACD_SIGNAL' in df_price.columns:
        macd_latest = df_price['MACD'].iloc[-1]
        signal_latest = df_price['MACD_SIGNAL'].iloc[-1]
        if macd_latest < signal_latest:
            explanations.append("- MACD가 Signal선 아래에 위치해 단기 하락 신호로 작용하고 있습니다.")
        else:
            explanations.append("- MACD가 Signal선을 상향 돌파해 단기 상승 모멘텀을 보여주고 있습니다.")

    if 'RSI_14' in df_price.columns:
        rsi_latest = df_price['RSI_14'].iloc[-1]
        if rsi_latest > 70:
            explanations.append("- RSI가 70 이상으로 과매수 상태이며, 조정 가능성이 있습니다.")
        elif rsi_latest < 30:
            explanations.append("- RSI가 30 이하로 과매도 상태이지만, 매도 시점에서는 신중해야 합니다.")

    if '거래량' in df_price.columns:
        recent_volume = df_price['거래량'].iloc[-1]
        avg_volume = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if recent_volume > avg_volume * 1.5:
            explanations.append("- 최근 거래량이 평균 대비 크게 증가하여 매도 압력이 강해지고 있음을 시사합니다.")
        elif recent_volume > avg_volume:
            explanations.append("- 거래량이 평균 이상으로 다소 매도세가 증가하는 추세입니다.")

    explanations.append("종합적으로, 추천 매도 가격은 기술적 지표와 매수 가격 대비 수익률, 거래량 변동성 등을 반영한 전문가 의견입니다.")
    explanations.append("시장 변동성 및 개인 투자 성향을 함께 고려해 신중한 투자 판단을 하시기 바랍니다.")

    for line in explanations:
        st.markdown(f"- {line}")
else:
    st.markdown("추천 매도가가 산출되지 않아 근거 설명을 제공할 수 없습니다.")

# 종목 평가 및 투자 전략 (전문가 의견) - 상세 & 초보 친화적
st.subheader("📋 종목 평가 및 투자 전략 (전문가 의견)")
try:
    eval_lines = []
    per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
    if per < 7:
        eval_lines.append("✔️ [PER] 현재 PER이 7 미만입니다. 이는 기업의 이익 대비 주가가 낮게 형성되어 있어 저평가 가능성이 큽니다. 단, 업종 특성에 따라 차이가 있으므로 반드시 비교가 필요합니다.")
    elif per > 20:
        eval_lines.append("⚠️ [PER] 현재 PER이 20을 초과합니다. 이는 시장에서 미래 성장 기대가 반영된 것이지만, 단기적으로 과대평가 구간일 수 있어 주의가 필요합니다.")
    pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
    if pbr < 1:
        eval_lines.append("✔️ [PBR] PBR이 1 미만으로 회사의 순자산 가치보다 주가가 낮게 평가되고 있습니다. 이는 안전마진이 크고 가치 투자에 적합한 상태입니다.")
    elif pbr > 2:
        eval_lines.append("⚠️ [PBR] PBR이 2를 넘으면 자산가치 대비 고평가되어 있을 수 있으므로 투자 시 신중해야 합니다.")
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    if div > 3:
        eval_lines.append("💰 [배당] 배당률이 3% 이상으로 안정적인 현금흐름을 기대할 수 있으며, 장기 투자자에게 매력적인 요소입니다.")
    elif div < 1:
        eval_lines.append("💡 [배당] 배당률이 1% 미만인 경우 성장 위주의 투자 대상일 수 있으며, 배당보다는 주가 상승에 중점을 둔 전략이 필요합니다.")
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps > 0:
        eval_lines.append("🟢 [EPS] 최근 분기 순이익이 흑자이며, 이는 기업의 수익성이 안정적임을 나타냅니다.")
    else:
        eval_lines.append("🔴 [EPS] 최근 분기 적자를 기록하고 있으므로 재무 상태 악화 여부와 원인 파악이 필요합니다.")
    bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
    if bps > 0:
        eval_lines.append("🟢 [BPS] 자산가치가 긍정적이며, 기업이 가진 순자산이 투자 안정성을 뒷받침합니다.")
    else:
        eval_lines.append("🔴 [BPS] 자산가치가 낮거나 불안정할 수 있어 주의가 필요합니다.")

    if "RSI_14" in df_price.columns and not np.isnan(df_price['RSI_14'].iloc[-1]):
        rsi_now = df_price['RSI_14'].iloc[-1]
        if rsi_now < 30:
            eval_lines.append("📉 [RSI] RSI가 30 이하로 단기 과매도 상태입니다. 기술적 반등 가능성이 있지만, 펀더멘털도 함께 고려해야 합니다.")
        elif rsi_now > 70:
            eval_lines.append("📈 [RSI] RSI가 70 이상으로 단기 과매수 상태입니다. 단기 조정 가능성이 있으니 매수 타이밍을 신중히 판단하세요.")

    score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
    q80 = scored_df["score"].quantile(0.8)
    q20 = scored_df["score"].quantile(0.2)
    if score > q80:
        eval_lines.append("✅ [종합 진단] 현재 종목은 투자 매력도가 매우 높아 적극적인 매수 혹은 분할 매수를 고려할 수 있습니다.")
    elif score < q20:
        eval_lines.append("❌ [종합 진단] 투자 매력도가 낮은 편이므로, 추가 모니터링 후 진입하거나 다른 종목을 고려하는 것이 좋습니다.")
    else:
        eval_lines.append("☑️ [종합 진단] 평균 수준의 투자 매력도를 가진 종목으로, 가격 조정 시 분할 매수를 통한 장기투자가 적합합니다.")

    for line in eval_lines:
        st.markdown(f"- {line}")
except Exception:
    st.info("종목 평가 및 투자 전략 정보를 불러올 수 없습니다.")

# 개별 갱신 버튼 및 처리
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

# 최신 뉴스
st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")
