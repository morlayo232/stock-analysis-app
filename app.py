# app.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json

sys.path.append(os.path.abspath("modules"))

from score_utils import finalize_scores, assess_reliability
from fetch_news import fetch_google_news
from chart_utils import plot_price_rsi_macd
from calculate_indicators import add_tech_indicators
from datetime import datetime
from pykrx import stock

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

FAV_FILE = "favorites.json"

def load_favorites():
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_favorites(fav_list):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(fav_list, f, ensure_ascii=False)

@st.cache_data
def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv")
        expected = [
            "종목명", "종목코드", "현재가",
            "PER", "PBR", "EPS", "BPS", "배당률", "score"
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
if not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
all_candidates = scored_df["종목명"].tolist()
top10 = scored_df.sort_values("score", ascending=False).head(10)

with st.sidebar:
    st.markdown("#### ⭐ 즐겨찾기 관리")
    fav_list = load_favorites()
    fav_selected = st.multiselect("즐겨찾기 등록/해제", all_candidates, default=fav_list, key="fav_multiselect")
    if st.button("⭐ 즐겨찾기 저장", key="fav_save"):
        save_favorites(fav_selected)
        st.rerun()
        st.stop()
    st.markdown("---")
    current_selected = st.selectbox("조회 종목 선택", all_candidates, key="main_selectbox")

selected = current_selected
code = scored_df[scored_df["종목명"] == selected]["종목코드"].values[0]

st.subheader(f"선택 종목: {selected}")
st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[
    ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급"]
])

if fav_selected:
    st.subheader("⭐ 즐겨찾기 종목")
    st.dataframe(scored_df[scored_df["종목명"].isin(fav_selected)][
        ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급"]
    ])

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
    if "종가" in df_price.columns:
        df_price["MA20"] = df_price["종가"].rolling(window=20).mean()
        df_price["STD20"] = df_price["종가"].rolling(window=20).std()
        df_price["BB_low"] = df_price["MA20"] - 2*df_price["STD20"]
        df_price["BB_high"] = df_price["MA20"] + 2*df_price["STD20"]

    fig, fig_rsi, fig_macd = plot_price_rsi_macd(df_price)
    fig.update_layout(height=520)
    fig_rsi.update_layout(height=300)
    fig_macd.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True, key="main_chart")
    st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")
    st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

    st.info(
        "- **종가/EMA(20):** 단기 추세·매매 타이밍 참고. EMA 하락돌파 후 반등, 상승돌파 후 조정 체크!\n"
        "- **골든크로스:** 상승전환 시그널, **데드크로스:** 하락전환 시그널(실전에서는 한 박자 뒤 조치 권고)\n"
        "- **RSI:** 40 아래 과매도, 60 위 과매수\n"
        "- **MACD:** MACD가 Signal을 상향돌파(매수), 하향돌파(매도)\n"
        "- **볼린저밴드:** 하단 근접=반등 가능, 상단 돌파=단기 고점 가능"
    )

    # --------- 추천 매수/매도가 ---------
    def get_recommended_prices(df_price):
        window = min(len(df_price), 60)
        recent = df_price.tail(window)
        buy_signals, sell_signals = [], []
        for i in range(1, len(recent)):
            try:
                close = float(recent["종가"].iloc[i])
                ema = float(recent["EMA20"].iloc[i]) if "EMA20" in recent else None
                rsi = float(recent["RSI"].iloc[i]) if "RSI" in recent else None
                macd = float(recent["MACD"].iloc[i]) if "MACD" in recent else None
                signal = float(recent["Signal"].iloc[i]) if "Signal" in recent else None
                bb_low = float(recent["BB_low"].iloc[i]) if "BB_low" in recent else None
                bb_high = float(recent["BB_high"].iloc[i]) if "BB_high" in recent else None
                buy_flag = False
                if rsi is not None and macd is not None and signal is not None:
                    if (rsi < 35 and macd > signal):
                        buy_flag = True
                if ema is not None and close < ema:
                    buy_flag = True
                if bb_low is not None and close < bb_low:
                    buy_flag = True
                if buy_flag:
                    buy_signals.append((recent.index[i], close))
                sell_flag = False
                if rsi is not None and macd is not None and signal is not None:
                    if (rsi > 65 and macd < signal):
                        sell_flag = True
                if ema is not None and close > ema:
                    sell_flag = True
                if bb_high is not None and close > bb_high:
                    sell_flag = True
                if sell_flag:
                    sell_signals.append((recent.index[i], close))
            except Exception:
                continue
        buy_price, buy_date, sell_price, sell_date = None, None, None, None
        if buy_signals:
            buy_date, buy_price = min(buy_signals, key=lambda x: x[1])
        if sell_signals:
            sell_date, sell_price = max(sell_signals, key=lambda x: x[1])
        if buy_price is not None and sell_price is not None and buy_price >= sell_price:
            buy_price, buy_date = None, None
        return buy_price, buy_date, sell_price, sell_date

    st.subheader("📌 추천 매수가 / 매도가")
    buy_price, buy_date, sell_price, sell_date = get_recommended_prices(df_price)
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

    # --------- 종목 평가 및 투자 전략 (전문가 의견) ---------
    st.subheader("📋 종목 평가 및 투자 전략 (전문가 의견)")
    try:
        eval_lines = []
        per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
        if per < 7:
            eval_lines.append("✔️ [PER] 주가수익비율(PER)이 7 미만, 실적 대비 저평가 구간입니다.")
        elif per > 20:
            eval_lines.append("⚠️ [PER] PER이 20 초과, 성장성 확인 필요.")
        pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
        if pbr < 1:
            eval_lines.append("✔️ [PBR] PBR 1 미만, 순자산대비 저평가.")
        elif pbr > 2:
            eval_lines.append("⚠️ [PBR] PBR 2 초과, 과도한 평가 가능성.")
        div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
        if div > 3:
            eval_lines.append("💰 [배당] 배당수익률 3% 이상, 장기투자에 유리.")
        elif div < 1:
            eval_lines.append("💡 [배당] 배당수익률 1% 미만, 성장/재투자 기업 가능성.")
        eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
        if eps > 0:
            eval_lines.append("🟢 [EPS] 최근 분기 흑자, 재무 건전.")
        else:
            eval_lines.append("🔴 [EPS] 최근 분기 적자, 구조 점검 필요.")
        bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
        if bps > 0:
            eval_lines.append("🟢 [BPS] 자산가치 기준 안정적.")
        # ---- 추가 지표 코멘트 ----
        if "RSI" in df_price.columns and not np.isnan(df_price['RSI'].iloc[-1]):
            rsi_now = df_price['RSI'].iloc[-1]
            if rsi_now < 35:
                eval_lines.append("📉 [RSI] 단기 과매도, 반등 가능성.")
            elif rsi_now > 65:
                eval_lines.append("📈 [RSI] 단기 과매수, 차익실현 타이밍.")
        if "EMA20" in df_price.columns and not np.isnan(df_price['EMA20'].iloc[-1]):
            if df_price['종가'].iloc[-1] > df_price['EMA20'].iloc[-1]:
                eval_lines.append("🔹 [EMA20] 주가가 단기이평선(EMA20) 위, 상승 모멘텀.")
            else:
                eval_lines.append("🔸 [EMA20] 주가가 단기이평선 아래, 조정 구간.")
        if "BB_low" in df_price.columns and "종가" in df_price.columns:
            if df_price['종가'].iloc[-1] < df_price['BB_low'].iloc[-1]:
                eval_lines.append("⚡ [볼린저밴드] 주가가 밴드 하단 하회, 단기 반등 구간.")
            elif df_price['종가'].iloc[-1] > df_price['BB_high'].iloc[-1]:
                eval_lines.append("🔥 [볼린저밴드] 주가가 밴드 상단 돌파, 단기 급등/고점 신호.")
        score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
        q80 = scored_df["score"].quantile(0.8)
        q20 = scored_df["score"].quantile(0.2)
        if score > q80:
            eval_lines.append("✅ [종합 진단] 투자매력도 상위. 적극적 매수 고려.")
        elif score < q20:
            eval_lines.append("❌ [종합 진단] 투자매력 낮음. 추가 모니터링 권장.")
        else:
            eval_lines.append("☑️ [종합 진단] 평균 수준. 분할매수, 장기투자 전략 적합.")
        for line in eval_lines:
            st.markdown(f"- {line}")
    except Exception:
        st.info("종목 평가/전략 분석 데이터 부족.")

if st.button(f"🔄 {selected} 데이터만 즉시 갱신"):
    from update_stock_database import update_single_stock
    result = update_single_stock(code)
    if result:
        st.success(f"{selected} 데이터만 갱신 완료!")
        st.cache_data.clear()
        st.rerun()
    else:
        st.error("개별 종목 갱신 실패(치명적 오류 발생)")

if st.button("🗂️ 전체 종목 수동 갱신"):
    from update_stock_database import update_database
    try:
        update_database()
        st.success("전체 데이터 갱신 완료!")
        st.cache_data.clear()
        st.rerun()
    except Exception:
        st.error("전체 갱신 실패")

st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")
