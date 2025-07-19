# 1. 기본 임포트 및 설정
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

# 2. 데이터 로딩 함수
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

# 3. 투자 성향 선택 UI
style = st.sidebar.radio("투자 성향", ["aggressive", "stable", "dividend"], horizontal=True)

# 4. 데이터 준비 및 점수 계산
raw_df = load_filtered_data()
if not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
top10 = scored_df.sort_values("score", ascending=False).head(10)

# 5. TOP10 종목 빠른 선택 UI
st.subheader("TOP10 종목 빠른 선택")
quick_selected = st.selectbox("TOP10 종목명", top10["종목명"].tolist(), key="top10_selectbox")

# 6. TOP10 데이터 테이블 표시
st.subheader(f"투자 성향({style}) 통합 점수 TOP 10")
st.dataframe(top10[["종목명","종목코드","현재가","PER","PBR","EPS","BPS","배당률","score","신뢰등급"]])

# 7. 종목 검색 및 선택 UI
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

# 8. 최신 재무 정보 표시
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

# 9. 주가 및 기술지표 차트 (크기 통일 400)
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

# 10. 투자 지표 설명
st.info(
    "- **종가/EMA(20):** 단기 추세 및 매매 타이밍 참고\n"
    "- **골든크로스:** 상승전환 신호, 매수 타이밍으로 활용\n"
    "- **데드크로스:** 하락전환 신호, 주의 또는 매도 타이밍\n"
    "- **RSI:** 30 이하 과매도 신호, 반등 가능성 높음\n"
    "- **RSI:** 70 이상 과매수 신호, 조정 가능성 있음\n"
    "- **MACD:** MACD가 Signal 상향 돌파 시 매수 신호\n"
    "- **MACD:** MACD가 Signal 하향 돌파 시 매도 신호"
)

# 11. 추천 매수가 / 매도가 계산 및 출력
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

# 12. 종목 평가 및 투자 전략 (전문가 의견) - 상세 & 초보 친화적
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
        eval_lines.append("🟢 [BPS] 자산가

# 9. 주가 및 기술지표 차트 (크기 통일 400)
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

# 10. 투자 지표 설명
st.info(
    "- **종가/EMA(20):** 단기 추세 및 매매 타이밍 참고\n"
    "- **골든크로스:** 상승전환 신호, 매수 타이밍으로 활용\n"
    "- **데드크로스:** 하락전환 신호, 주의 또는 매도 타이밍\n"
    "- **RSI:** 30 이하 과매도 신호, 반등 가능성 높음\n"
    "- **RSI:** 70 이상 과매수 신호, 조정 가능성 있음\n"
    "- **MACD:** MACD가 Signal 상향 돌파 시 매수 신호\n"
    "- **MACD:** MACD가 Signal 하향 돌파 시 매도 신호"
)

# 11. 추천 매수가 / 매도가 계산 및 출력
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

# 12. 종목 평가 및 투자 전략 (전문가 의견) - 상세 & 초보 친화적
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

    # 14. 개별 종목 데이터 즉시 갱신 버튼 및 처리

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

    # 15. 최신 뉴스 표시

st.subheader("최신 뉴스")
news = fetch_google_news(selected)
if news:
    for n in news:
        st.markdown(f"- {n}")
else:
    st.info("뉴스 정보 없음")
    # 17. (Optional) 추가 개선 사항 안내
# - 투자 성향별 점수 산출식 고도화(필요 시 modules/score_utils.py 수정)
# - 추가 기술지표(볼린저밴드, 스토캐스틱 등) 차트 및 추천 반영 가능
# - UI/UX 개선을 위한 카드형 레이아웃 등 적용 가능
# - 각 지표 및 평가 항목에 마우스 오버 툴팁으로 상세 설명 추가
# - 종목 즐겨찾기 및 보유 종목 관리 기능 확장

# 필요 시 다음과 같은 모듈 추가 개발 및 연결 작업 진행 바랍니다.
