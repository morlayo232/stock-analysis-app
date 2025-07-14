import streamlit as st
import pandas as pd
import json
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import finalize_scores, safe_float, DEFAULT_FIN
from modules.chart_utils import plot_stock_chart, plot_rsi_macd
from modules.fetch_price import fetch_stock_price
from modules.fetch_news import fetch_news_headlines
from update_stock_database import main as update_main

st.set_page_config(page_title="📊 한국 주식 분석", layout="wide")

FAV_FILE = "favorites.json"

@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv("filtered_stocks.csv", dtype=str)

def load_favorites():
    try:
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=2)

def search_stocks(keyword, df):
    return df[df["종목명"].str.contains(keyword, case=False)] if keyword else pd.DataFrame()

def get_score_color(score):
    try:
        score = float(score)
        if score >= 1.5:
            return "green"
        elif score >= 0.5:
            return "blue"
        elif score <= -1.5:
            return "red"
        else:
            return "black"
    except:
        return "gray"

# ---- UI 시작 ----
st.title("📊 한국 주식 시장 투자 매력도 분석")
st.info("주가 데이터를 불러올 수 없습니다.", icon="ℹ️")

# ---- 투자 성향, 종목검색 등 각종 사이드바 ----
st.sidebar.header("투자 성향 선택")
style = st.sidebar.radio("성향", ["공격적", "안정적", "배당형"])

st.sidebar.subheader("종목명 검색")
keyword = st.sidebar.text_input("검색", "")

# ---- 데이터 로드 및 가공 ----
df = load_filtered_stocks()
if not df.empty:
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.sort_values("score", ascending=False)
    # NaN score 종목 하단으로 정렬
    top10 = df[df["score"].notnull()].head(10)

    st.markdown("## 🏆 투자 성향별 추천 TOP 10")
    st.dataframe(
        top10[["종목명", "종목코드", "시장구분", "score"]],
        hide_index=True,
        column_config={
            "score": st.column_config.NumberColumn("score", format="%.2f")
        },
        use_container_width=True,
    )
else:
    st.warning("filtered_stocks.csv에 데이터가 없습니다.")

# ---- 종목 선택 및 상세 정보/차트/뉴스 등 ----
search_result = search_stocks(keyword, df) if not df.empty else pd.DataFrame()
st.sidebar.subheader("검색된 종목 선택")
selected_row = (
    st.sidebar.selectbox(
        "검색된 종목",
        search_result["종목명"] + " (" + search_result["종목코드"] + ")",
        key="searchbox",
    ) if not search_result.empty else None
)

if selected_row:
    code = selected_row.split("(")[-1].replace(")", "")
    stock = df[df["종목코드"] == code].iloc[0]
    st.markdown(f"### 📌 {stock['종목명']} ({stock['종목코드']})")
    st.write(f"투자 성향: {style} | 종합 점수: {stock['score'] if pd.notnull(stock['score']) else '—'}")

    # ---- 차트 시각화 ----
    try:
        df_price = fetch_stock_price(code)
        if not df_price.empty:
            df_price = calculate_indicators(df_price)
            st.plotly_chart(plot_stock_chart(df_price), use_container_width=True)
            st.plotly_chart(plot_rsi_macd(df_price), use_container_width=True)
        else:
            st.warning("주가 데이터 불러오기 실패")
    except Exception as e:
        st.error(f"차트 로딩 오류: {e}")

    # ---- 추천 매수/매도 등 ----
    try:
        ema_cross_buy = df_price.loc[df_price["EMA_Cross"] == "golden"]
        ema_cross_sell = df_price.loc[df_price["EMA_Cross"] == "dead"]
        latest_buy = ema_cross_buy["Close"].iloc[-1] if not ema_cross_buy.empty else None
        latest_sell = ema_cross_sell["Close"].iloc[-1] if not ema_cross_sell.empty else None
        st.markdown("### 💲 추천 매수/매도 가격")
        st.info(f"최근 골든크로스 매수: {latest_buy:.2f}원" if latest_buy else "골든크로스 신호 없음")
        st.info(f"최근 데드크로스 매도: {latest_sell:.2f}원" if latest_sell else "데드크로스 신호 없음")
    except Exception as e:
        st.error(f"추천가 계산 오류: {e}")

    # ---- 투자 판단 요약 ----
    st.markdown("### 🧭 투자 판단 요약")
    try:
        rsi = df_price["RSI"].iloc[-1]
        macd = df_price["MACD"].iloc[-1]
        signal = df_price["Signal"].iloc[-1]
        rsi_text = f"RSI 중간 → {'관망' if 40 <= rsi <= 60 else ('매수' if rsi < 40 else '매도')}"
        macd_text = (
            "상승 흐름" if macd > signal else "하락 흐름"
        )
        st.info(rsi_text)
        st.success(f"MACD > Signal → {macd_text}")
    except Exception as e:
        st.error(f"지표 요약 오류: {e}")

    # ---- 뉴스 헤드라인 ----
    st.markdown("### 📰 관련 뉴스")
    try:
        news_list = fetch_news_headlines(stock["종목명"])
        if news_list:
            for news in news_list:
                st.write(f"- [{news['title']}]({news['link']})")
        else:
            st.write("뉴스 없음")
    except Exception as e:
        st.error(f"뉴스 크롤링 오류: {e}")

# ---- 즐겨찾기 ----
st.sidebar.markdown("## ⭐ 즐겨찾기")
favs = load_favorites()
if selected_row:
    code = selected_row.split("(")[-1].replace(")", "")
    if st.sidebar.button("즐겨찾기 추가"):
        if code not in favs:
            favs.append(code)
            save_favorites(favs)
            st.sidebar.success("즐겨찾기 등록됨!")
        else:
            st.sidebar.info("이미 등록된 종목입니다.")

st.sidebar.markdown("## 🔄 수동 데이터 갱신")
if st.sidebar.button("Update Now"):
    update_main()
    st.sidebar.success("업데이트 완료!")

st.sidebar.markdown(f"마지막 업데이트: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}")
