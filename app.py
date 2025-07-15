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

# 파일명
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

# ------------------ 사이드바 ------------------
style = st.sidebar.radio(
    "투자 성향", ["aggressive", "stable", "dividend"], horizontal=True
)
fav_list = load_favorites()

# 데이터 준비
raw_df = load_filtered_data()
if not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
top10 = scored_df.sort_values("score", ascending=False).head(10)

# ------------------ 종목 선택 (우선순위) ------------------
selected = None
code = None

with st.sidebar:
    st.markdown("#### ⭐ 즐겨찾기")
    # 드롭다운: 즐겨찾기한 종목만 보임
    fav_dropdown = None
    if fav_list:
        fav_dropdown = st.selectbox("즐겨찾기 선택", fav_list, key="fav_dropdown", index=0)
    # 종목 검색도 사이드바에 같이(추가)
    all_candidates = scored_df["종목명"].tolist()
    search_val = st.text_input("종목명 직접 검색", "")
    if search_val:
        filtered = [x for x in all_candidates if search_val in x]
        search_candidates = filtered if filtered else all_candidates
    else:
        search_candidates = all_candidates
    search_selected = st.selectbox("전체 종목 선택", search_candidates, key="all_selectbox")
    # 최종 선택 우선순위: 즐겨찾기 > 검색(선택) > TOP10
    if fav_dropdown:
        selected = fav_dropdown
    else:
        selected = search_selected
    code = scored_df[scored_df["종목명"] == selected]["종목코드"].values[0]
    # 즐겨찾기 등록/해제 버튼
    is_fav = selected in fav_list
    if st.button("⭐ 즐겨찾기 추가" if not is_fav else "★ 즐겨찾기 해제", key="fav_btn2"):
        if not is_fav:
            fav_list.append(selected)
        else:
            fav_list = [x for x in fav_list if x != selected]
        save_favorites(fav_list)
        st.experimental_rerun()

# ------------------ 본문(선택 종목) ------------------
if not selected or not code:
    st.warning("종목을 선택해 주세요.")
    st.stop()

st.subheader(f"선택 종목: {selected}")
st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[
    ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급"]
])

# 즐겨찾기 테이블
if fav_list:
    st.subheader("⭐ 즐겨찾기 종목")
    st.dataframe(scored_df[scored_df["종목명"].isin(fav_list)][
        ["종목명", "종목코드", "현재가", "PER", "PBR", "EPS", "BPS", "배당률", "score", "신뢰등급"]
    ])

# 최신 재무 정보
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

# 가격/차트/지표
start = "20240101"
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
        "- **종가/EMA(20):** 단기 추세·매매 타이밍 참고. EMA 하락돌파 후 반등, 상승돌파 후 조정 체크!\n"
        "- **골든크로스:** 상승전환 시그널, **데드크로스:** 하락전환 시그널(실전에서는 한 박자 뒤 조치 권고)\n"
        "- **RSI:** 40 아래 과매도, 60 위 과매수\n"
        "- **MACD:** MACD가 Signal을 상향돌파(매수), 하향돌파(매도)"
    )

    st.subheader("📌 추천 매수가 / 매도가")
    required_cols = ["RSI", "MACD", "Signal", "EMA20", "종가"]
    st.write("추천가 관련 최근 값:", df_price[required_cols].tail())

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
        if '날짜' not in recent.columns:
            recent['날짜'] = recent['index'] if 'index' in recent.columns else recent.index
        for i in range(1, len(recent)):
            try:
                rsi_now = float(recent['RSI'].iloc[i])
                macd_now = float(recent['MACD'].iloc[i])
                signal_now = float(recent['Signal'].iloc[i])
                close_now = float(recent['종가'].iloc[i])
                ema_now = float(recent['EMA20'].iloc[i])
                rolling_std = recent['종가'].rolling(window=20).std().iloc[i] if i >= 19 else None
                lower_band = ema_now - 2 * rolling_std if rolling_std is not None else None
                upper_band = ema_now + 2 * rolling_std if rolling_std is not None else None
                # 매수 조건
                if ((rsi_now < 40) or (close_now < ema_now) or (macd_now > signal_now) or (lower_band is not None and close_now < lower_band)):
                    buy_price = close_now
                    buy_date = recent['날짜'].iloc[i]
                # 매도 조건
                if ((rsi_now > 60) or (close_now > ema_now) or (macd_now < signal_now) or (upper_band is not None and close_now > upper_band)):
                    sell_price = close_now
                    sell_date = recent['날짜'].iloc[i]
            except Exception:
                continue
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
            eval_lines.append("✔️ [PER] 현 주가수익비율(PER)이 7 미만입니다. 이는 이익 대비 현재 주가가 낮게 형성돼 있다는 뜻으로, 실적 안정성이 유지된다면 저평가된 종목으로 볼 수 있습니다.")
        elif per > 20:
            eval_lines.append("⚠️ [PER] PER이 20을 초과합니다. 단기적으로 고평가 구간에 있을 수 있으므로 실적 성장 지속성, 업종 특성도 함께 체크하세요.")
        pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
        if pbr < 1:
            eval_lines.append("✔️ [PBR] PBR이 1 미만으로, 회사의 순자산보다 낮게 거래되고 있습니다.")
        elif pbr > 2:
            eval_lines.append("⚠️ [PBR] PBR이 2를 초과합니다.")
        div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
        if div > 3:
            eval_lines.append("💰 [배당] 배당수익률이 3%를 넘어, 배당 투자 관점에서도 긍정적입니다.")
        elif div < 1:
            eval_lines.append("💡 [배당] 배당수익률이 1% 미만으로 낮은 편입니다.")
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
            if rsi_now < 40:
                eval_lines.append("📉 [RSI] 단기 과매도 상태입니다. 조정 후 반등 가능성 체크 필요.")
            elif rsi_now > 60:
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

# =========================
# 👇👇👇 개별/전체 수동갱신 버튼 👇👇👇
# =========================

if st.button(f"🔄 {selected} 데이터만 즉시 갱신"):
    from update_stock_database import update_single_stock
    try:
        update_single_stock(code)
        st.success(f"{selected} 데이터만 갱신 완료!")
        st.cache_data.clear()
        st.experimental_rerun()
    except Exception:
        st.error("개별 종목 갱신 실패")

if st.button("🗂️ 전체 종목 수동 갱신"):
    from update_stock_database import update_database
    try:
        update_database()
        st.success("전체 데이터 갱신 완료!")
        st.cache_data.clear()
        st.experimental_rerun()
    except Exception:
        st.error("전체 갱신 실패")

# =========================

st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")
