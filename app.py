# app.py

import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from pykrx import stock

from modules.evaluate_stock import evaluate_stock

sys.path.append(os.path.abspath("modules"))
from score_utils import assess_reliability, finalize_scores
from fetch_news import fetch_google_news
from chart_utils import plot_price_rsi_macd
from calculate_indicators import add_tech_indicators
from price_utils import calculate_recommended_sell

NOTES_FILE = "notes.json"

# 3등분 columns 사용해 중앙 열에 이미지 배치
col1, col2, col3 = st.columns([1, 6, 1])

with col1:
    st.write("")

with col2:
    try:
        logo_img = Image.open("logo_tynex.png")  # 로컬 파일
        st.image(logo_img, width=350)  # 크기 조절
    except Exception:
        st.write("로고 이미지 로드 실패")

with col3:
    st.write("")

# 점수 계산 설명
def show_score_formula(style):
    if style == "aggressive":
        st.markdown("""
        #### 공격적 투자 성향 점수 계산식
        - score = -0.25 * z_PER - 0.2 * z_PBR + 0.2 * z_EPS + 0.1 * z_BPS + 0.1 * z_배당률 + 0.15 * z_거래대금
        - EPS가 양수일 경우 0.1점 가산
        - z_변수는 표준화 지표(Z-Score)입니다.
        """)
    elif style == "stable":
        st.markdown("""
        #### 안정적 투자 성향 점수 계산식
        - score = -0.3 * z_PER - 0.35 * z_PBR + 0.2 * z_BPS + 0.1 * z_배당률 + 0.05 * z_거래대금
        - BPS가 중간값 이상일 경우 0.1점 가산
        """)
    elif style == "dividend":
        st.markdown("""
        #### 배당형 투자 성향 점수 계산식
        - score = 0.7 * z_배당률 - 0.15 * z_PBR - 0.1 * z_PER + 0.05 * z_거래대금
        - 배당률 3% 이상일 경우 0.15점 가산
        """)
    else:
        st.markdown("투자 성향에 맞는 점수 계산식이 없습니다.")


@st.cache_data(ttl=3600, show_spinner=False)
def load_market_universe():
    kospi = set(stock.get_market_ticker_list(market="KOSPI"))
    kosdaq = set(stock.get_market_ticker_list(market="KOSDAQ"))
    return kospi, kosdaq


@st.cache_data(ttl=1800, show_spinner=False)
def load_price_window(code: str, days: int = 180):
    end = datetime.today()
    start = end - pd.Timedelta(days=days)
    df = stock.get_market_ohlcv_by_date(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), code)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    if "날짜" in df.columns:
        df = df.set_index("날짜")
    df = add_tech_indicators(df)
    return df


def _safe_norm(value: float, scale: float = 1.0):
    if value is None or np.isnan(value):
        return 0.0
    return float(np.tanh(value / scale))


def compute_momentum_supply(df_price: pd.DataFrame):
    if df_price is None or df_price.empty or "종가" not in df_price.columns:
        return 0.0, 0.0, 0.0, "데이터 부족"

    price = df_price["종가"]
    volume = df_price.get("거래량", pd.Series([np.nan] * len(df_price)))
    momentum_short = price.iloc[-1] / price.iloc[-20] - 1 if len(price) > 20 else 0
    momentum_mid = price.iloc[-1] / price.iloc[-60] - 1 if len(price) > 60 else 0
    slope_base = price.tail(30)
    slope = np.polyfit(np.arange(len(slope_base)), slope_base, 1)[0] if len(slope_base) >= 2 else 0
    momentum_score = (
        0.45 * _safe_norm(momentum_short, 0.15)
        + 0.35 * _safe_norm(momentum_mid, 0.25)
        + 0.2 * _safe_norm(slope, price.tail(30).mean() if len(price) >= 30 else 1)
    )

    signed_volume = np.sign(price.diff().fillna(0)) * volume.fillna(0)
    obv = signed_volume.cumsum()
    obv_section = obv.tail(30)
    obv_slope = np.polyfit(np.arange(len(obv_section)), obv_section, 1)[0] if len(obv_section) >= 2 else 0
    volume_ratio = volume.iloc[-1] / volume.tail(20).mean() - 1 if len(volume.dropna()) >= 20 else 0
    supply_score = 0.6 * _safe_norm(obv_slope, 1e9) + 0.4 * _safe_norm(volume_ratio, 1.5)

    pattern_score = 0.0
    pattern_comment = []
    if "RSI_14" in df_price.columns and pd.notna(df_price["RSI_14"].iloc[-1]):
        rsi_value = df_price["RSI_14"].iloc[-1]
        if rsi_value < 35:
            pattern_score += 0.25
            pattern_comment.append("RSI 과매도 구간")
        elif rsi_value > 65:
            pattern_score -= 0.2
            pattern_comment.append("RSI 과매수 경계")
    if "MACD" in df_price.columns and "MACD_SIGNAL" in df_price.columns:
        macd_diff = df_price["MACD"].iloc[-1] - df_price["MACD_SIGNAL"].iloc[-1]
        pattern_score += 0.25 if macd_diff > 0 else -0.15
        pattern_comment.append("MACD 상승" if macd_diff > 0 else "MACD 하락")
    if "EMA_20" in df_price.columns:
        ema20 = df_price["EMA_20"].iloc[-1]
        last_close = price.iloc[-1]
        if last_close > ema20:
            pattern_score += 0.15
            pattern_comment.append("EMA20 상방")
        else:
            pattern_score -= 0.1
            pattern_comment.append("EMA20 하방")

    return float(momentum_score), float(supply_score), float(pattern_score), ", ".join(pattern_comment)


@st.cache_data(ttl=1800, show_spinner=False)
def compute_news_score(query: str, max_items: int = 8):
    titles = fetch_google_news(query, max_items=max_items)
    if not titles:
        return 0.0, []
    positive_keywords = ["급등", "호재", "성장", "수주", "상승", "최대"]
    negative_keywords = ["하락", "리스크", "적자", "경고", "실패", "연기"]
    score = 0
    for title in titles:
        if any(k in title for k in positive_keywords):
            score += 1
        if any(k in title for k in negative_keywords):
            score -= 1
    normalized = np.clip(score / len(titles), -1, 1)
    return float(normalized), titles


def load_notes():
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_notes(notes: dict):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def build_market_top(df: pd.DataFrame, market: str):
    subset = df[df["시장"] == market].copy()
    if subset.empty:
        return pd.DataFrame()
    subset = subset.sort_values("score", ascending=False).head(30).copy()
    std = subset["score"].std()
    mean = subset["score"].mean()
    subset["펀더멘털점수"] = (subset["score"] - mean) / (std if std else 1)

    for idx, row in subset.iterrows():
        price_window = load_price_window(row["종목코드"])
        momentum_score, supply_score, pattern_score, pattern_comment = compute_momentum_supply(price_window)
        news_score, headlines = compute_news_score(row["종목명"])

        composite = (
            0.5 * subset.at[idx, "펀더멘털점수"]
            + 0.2 * momentum_score
            + 0.15 * supply_score
            + 0.1 * news_score
            + 0.05 * pattern_score
        )

        subset.at[idx, "모멘텀점수"] = momentum_score
        subset.at[idx, "수급점수"] = supply_score
        subset.at[idx, "뉴스점수"] = news_score
        subset.at[idx, "패턴점수"] = pattern_score
        subset.at[idx, "패턴요약"] = pattern_comment
        subset.at[idx, "주요뉴스"] = " | ".join(headlines[:3]) if headlines else "-"
        subset.at[idx, "통합점수"] = composite

    return subset.sort_values("통합점수", ascending=False).head(10)
        
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
kospi_codes, kosdaq_codes = load_market_universe()
scored_df["시장"] = scored_df["종목코드"].apply(
    lambda x: "KOSPI" if x in kospi_codes else ("KOSDAQ" if x in kosdaq_codes else "기타")
)

top_kospi = build_market_top(scored_df, "KOSPI")
top_kosdaq = build_market_top(scored_df, "KOSDAQ")
overall_top = pd.concat([top_kospi, top_kosdaq], ignore_index=True)
if overall_top.empty:
    overall_top = scored_df.sort_values("score", ascending=False).head(10).copy()
    overall_top["통합점수"] = overall_top["score"]
else:
    overall_top = overall_top.sort_values("통합점수", ascending=False).head(10)

st.subheader("시장별 종합 매력도 TOP 10")
col_kospi, col_kosdaq = st.columns(2)
with col_kospi:
    st.caption("KOSPI")
    if not top_kospi.empty:
        st.dataframe(
            top_kospi[
                [
                    "종목명",
                    "종목코드",
                    "통합점수",
                    "모멘텀점수",
                    "수급점수",
                    "뉴스점수",
                    "패턴요약",
                    "주요뉴스",
                ]
            ]
        )
    else:
        st.info("KOSPI 데이터가 부족합니다.")
with col_kosdaq:
    st.caption("KOSDAQ")
    if not top_kosdaq.empty:
        st.dataframe(
            top_kosdaq[
                [
                    "종목명",
                    "종목코드",
                    "통합점수",
                    "모멘텀점수",
                    "수급점수",
                    "뉴스점수",
                    "패턴요약",
                    "주요뉴스",
                ]
            ]
        )
    else:
        st.info("KOSDAQ 데이터가 부족합니다.")

show_score_formula(style)

st.subheader("TOP10 종목 빠른 선택")
quick_selected = st.selectbox("시장별 매력도 TOP10", overall_top["종목명"].tolist(), key="top10_selectbox")

st.subheader("종목 검색")
keyword = st.text_input("종목명을 입력하세요")
market_filter = st.selectbox("시장 필터", ["전체", "KOSPI", "KOSDAQ", "기타"], index=0)

filtered_df = scored_df.copy()
if market_filter != "전체":
    filtered_df = filtered_df[filtered_df["시장"] == market_filter]

if keyword:
    filtered_df = filtered_df[filtered_df["종목명"].str.contains(keyword, case=False, na=False)]

select_candidates = filtered_df["종목명"].tolist()
if not select_candidates:
    select_candidates = [quick_selected] if quick_selected else scored_df["종목명"].tolist()

selected = st.selectbox("종목 선택", select_candidates, index=0, key="main_selectbox")
code = scored_df[scored_df["종목명"] == selected]["종목코드"].values[0]
info_row = scored_df[scored_df["종목명"] == selected].iloc[0]

st.subheader("📊 최신 재무/모멘텀 스냅샷")
fund_std = scored_df["score"].std() or 1
fund_norm = (info_row["score"] - scored_df["score"].mean()) / fund_std
df_price = load_price_window(code, days=365)
momentum_score, supply_score, pattern_score, pattern_comment = compute_momentum_supply(df_price)
news_score, news_titles = compute_news_score(selected)

cols = st.columns(6)
cols[0].metric("PER", f"{info_row['PER']:.2f}" if pd.notna(info_row['PER']) else "-")
cols[1].metric("PBR", f"{info_row['PBR']:.2f}" if pd.notna(info_row['PBR']) else "-")
cols[2].metric("EPS", f"{int(info_row['EPS']):,}" if pd.notna(info_row['EPS']) else "-")
cols[3].metric("배당률(%)", f"{info_row['배당률']:.2f}" if pd.notna(info_row['배당률']) else "-")
cols[4].metric("펀더멘털 점수", f"{fund_norm:.2f}")
cols[5].metric("시장", info_row.get("시장", "-"))

cols_m = st.columns(4)
cols_m[0].metric("모멘텀", f"{momentum_score:.2f}")
cols_m[1].metric("수급/OBV", f"{supply_score:.2f}")
cols_m[2].metric("뉴스", f"{news_score:.2f}")
cols_m[3].metric("패턴", pattern_comment if pattern_comment else "-", f"{pattern_score:.2f}")

if df_price is None or df_price.empty:
    st.warning("가격 데이터가 없습니다.")
else:
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
if df_price is None or df_price.empty:
    st.info("가격 데이터 부족")
else:
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
            if (
                (recent['RSI_14'].iloc[i] < 35 and recent['RSI_14'].iloc[i-1] < recent['RSI_14'].iloc[i])
                or (recent['종가'].iloc[i] < recent['EMA_20'].iloc[i])
            ) and (
                recent['MACD'].iloc[i] > recent['MACD_SIGNAL'].iloc[i]
                and recent['MACD'].iloc[i-1] < recent['MACD_SIGNAL'].iloc[i-1]
            ):
                buy_price = recent['종가'].iloc[i]
                buy_date = recent['날짜'].iloc[i] if '날짜' in recent.columns else recent.index[i]

            if (
                (recent['RSI_14'].iloc[i] > 65 and recent['RSI_14'].iloc[i-1] > recent['RSI_14'].iloc[i])
                or (recent['종가'].iloc[i] > recent['EMA_20'].iloc[i])
            ) and (
                recent['MACD'].iloc[i] < recent['MACD_SIGNAL'].iloc[i]
                and recent['MACD'].iloc[i-1] > recent['MACD_SIGNAL'].iloc[i-1]
            ):
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

if recommended_sell and input_buy_price > 0 and df_price is not None and not df_price.empty:
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

    explanations.append(
        "종합적으로, 추천 매도 가격은 기술적 지표와 매수 가격 대비 수익률, 거래량 변동성 등을 반영한 전문가 의견입니다."
    )
    explanations.append("시장 변동성 및 개인 투자 성향을 함께 고려해 신중한 투자 판단을 하시기 바랍니다.")

    for line in explanations:
        st.markdown(f"- {line}")
else:
    st.markdown("추천 매도가가 산출되지 않아 근거 설명을 제공할 수 없습니다.")

st.subheader("📋 종목 평가 및 투자 전략 (전문가 의견)")
try:
    eval_lines = evaluate_stock(scored_df, selected, df_price)
    for line in eval_lines:
        st.markdown(f"- {line}")
except Exception:
    st.info("종목 평가 및 투자 전략 정보를 불러올 수 없습니다.")

st.subheader("🚀 향후 급등 가능성 진단")
future_potential = (
    0.35 * momentum_score
    + 0.2 * supply_score
    + 0.15 * pattern_score
    + 0.1 * news_score
    + 0.2 * fund_norm
)
st.metric("급등 가능성 종합", f"{future_potential:.2f}")
st.caption(
    "모멘텀/수급/패턴/뉴스/재무 점수를 합산한 지표로, 0.5 이상이면 공격적 매수 모니터링 구간, -0.3 이하면 보수적으로 접근을 권장합니다."
)

st.subheader("📰 최신 뉴스 & 메모")
if news_titles:
    for title in news_titles:
        st.markdown(f"- {title}")
else:
    st.info("뉴스 정보 없음")

notes = load_notes()
existing_note = notes.get(code, "")
new_note = st.text_area("개인 메모", value=existing_note, height=120)
if st.button("💾 메모 저장"):
    notes[code] = new_note
    save_notes(notes)
    st.success("메모를 저장했습니다.")

if st.button(f"🔄 {selected} 데이터만 즉시 갱신"):
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())
    from update_stock_database import update_single_stock

    try:
        update_single_stock(code)
        st.success(f"{selected} 데이터만 갱신 완료!")
        st.cache_data.clear()
    except Exception:
        st.error("개별 종목 갱신 실패")
