import streamlit as st
import pandas as pd
import json
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import finalize_scores, safe_float, DEFAULT_FIN
from modules.chart_utils import plot_stock_chart, plot_rsi_macd
from modules.fetch_price import fetch_stock_price
from modules.fetch_news import fetch_news_headlines
from update_stock_database import main as update_main

# ----------- UI/로고/설명/스코어 기준 안내 -----------
st.set_page_config(page_title="📊 한국 주식 분석", layout="wide")
LOGO_PATH = "logo_tynex.png"  # 반드시 루트에 저장

col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image(LOGO_PATH, width=90)
with col2:
    st.markdown("""
    <h1 style="margin-bottom:0;margin-top:5px;font-size:2.2rem;">한국 주식 시장 투자 매력도 분석</h1>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="padding:8px 0 5px 0; font-size:1rem; color: #444; border-bottom: 1px solid #eee;">
<b>스코어 산정 방식 안내:</b>  
PER·PBR·ROE·배당률을 z-score로 표준화, 투자 성향별 가중치로 종합.<br>
공격적: 기술지표·단기수익률↑, 안정적: 저PBR·저PER·ROE↑, 배당형: 배당률↑.<br>
상위 10점은 "투자 성향별 추천 TOP10"에 실시간 반영.  
</div>
""", unsafe_allow_html=True)

# ----------- 사이드바 -----------
st.sidebar.header("투자 성향 선택")
style = st.sidebar.radio("성향", ["공격적", "안정적", "배당형"])

st.sidebar.subheader("종목명 검색")
keyword = st.sidebar.text_input("검색", "")

st.sidebar.markdown("---")
st.sidebar.markdown("## ⭐ 즐겨찾기")
FAV_FILE = "favorites.json"
def load_favorites():
    try:
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    except:
        return []
def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=2)
favs = load_favorites()

st.sidebar.markdown("## 🔄 데이터 갱신")
if st.sidebar.button("Update Now"):
    update_main()
    st.sidebar.success("업데이트 완료!")

st.sidebar.markdown(f"마지막 업데이트: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}")

# ----------- 데이터 로딩 -----------
@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv("filtered_stocks.csv", dtype=str)
df = load_filtered_stocks()

# ----------- 성향별 추천 TOP10 테이블/링크 -----------
if not df.empty:
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df_disp = df[df["score"].notnull()].sort_values("score", ascending=False)
    top10 = df_disp.head(10)
    st.markdown("## 🏆 투자 성향별 추천 TOP 10")

    # 종목명에 바로가기 링크 (Streamlit에서 key 기반 selectbox와 연동)
    def make_link(row):
        return f'<a href="#종목_{row["종목코드"]}" style="text-decoration:none;">{row["종목명"]}</a>'
    table_html = top10.assign(종목명=top10.apply(make_link, axis=1))\
        .to_html(escape=False, index=False, columns=["종목명", "종목코드", "시장구분", "score"], float_format="%.2f", border=0)
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.warning("filtered_stocks.csv에 데이터가 없습니다.")

# ----------- 종목 상세 자동 연동/검색/하이라이트 -----------
def search_stocks(keyword, df):
    return df[df["종목명"].str.contains(keyword, case=False)] if keyword else pd.DataFrame()
search_result = search_stocks(keyword, df) if not df.empty else pd.DataFrame()
selected_row = None
if not search_result.empty:
    opt_list = search_result["종목명"] + " (" + search_result["종목코드"] + ")"
    selected_row = st.sidebar.selectbox("검색된 종목", opt_list, key="searchbox")
elif not df.empty:
    # TOP10 첫번째 자동 선택
    selected_row = f'{df_disp.iloc[0]["종목명"]} ({df_disp.iloc[0]["종목코드"]})'

if selected_row:
    code = selected_row.split("(")[-1].replace(")", "")
    stock = df[df["종목코드"] == code].iloc[0]
    # 앵커(jump) 추가
    st.markdown(f'<a id="종목_{stock["종목코드"]}"></a>', unsafe_allow_html=True)
    st.markdown(f"""
    <h2 style="margin-top:12px;">📌 {stock['종목명']} ({stock['종목코드']})</h2>
    <span style="font-size:1.1rem;">투자 성향: <b>{style}</b> | 종합 점수: <b>{stock['score'] if pd.notnull(stock['score']) else '—'}</b></span>
    """, unsafe_allow_html=True)

    # ----------- 종목 평가 설명 -----------
    def score_eval(score):
        if pd.isnull(score): return "평가 불가(데이터 부족)"
        score = float(score)
        if score > 1.5: return "매우 매력적 (상위 10%)"
        elif score > 0.8: return "양호 (상위 30%)"
        elif score > 0: return "보통 (중간)"
        elif score > -0.8: return "저평가/관망"
        else: return "매력 낮음/주의"
    st.success(f"종목 평가: {score_eval(stock['score'])}")

    # ----------- 차트(시인성 개선) -----------
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

    # ----------- 추천 매수/매도가 -----------
    try:
        if "EMA_Cross" in df_price.columns:
            ema_cross_buy = df_price.loc[df_price["EMA_Cross"] == "golden"]
            ema_cross_sell = df_price.loc[df_price["EMA_Cross"] == "dead"]
            latest_buy = ema_cross_buy["Close"].iloc[-1] if not ema_cross_buy.empty else None
            latest_sell = ema_cross_sell["Close"].iloc[-1] if not ema_cross_sell.empty else None
            st.markdown("### 💲 추천 매수/매도 가격")
            st.info(f"최근 골든크로스 매수: {latest_buy:.2f}원" if latest_buy else "골든크로스 신호 없음")
            st.info(f"최근 데드크로스 매도: {latest_sell:.2f}원" if latest_sell else "데드크로스 신호 없음")
        else:
            st.warning("추천가 계산 오류: 'EMA_Cross' 미생성")
    except Exception as e:
        st.error(f"추천가 계산 오류: {e}")

    # ----------- 투자 판단 세부 설명 -----------
    try:
        rsi = float(df_price["RSI"].iloc[-1])
        macd = float(df_price["MACD"].iloc[-1])
        signal = float(df_price["Signal"].iloc[-1])
        st.markdown("### 🧭 투자 판단 요약")
        rsi_eval = "관망" if 40 <= rsi <= 60 else ("매수" if rsi < 40 else "매도")
        rsi_text = f"RSI {rsi:.1f} → {rsi_eval} ({'과매도' if rsi<30 else ('과매수' if rsi>70 else '')})"
        macd_text = f"MACD({macd:.2f}) {'>' if macd > signal else '<'} Signal({signal:.2f}) → {'상승 흐름' if macd > signal else '하락 흐름'}"
        st.info(rsi_text)
        st.success(macd_text)
    except Exception as e:
        st.error(f"지표 요약 오류: {e}")

    # ----------- 뉴스 헤드라인(없을 시 안내) -----------
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

    # ----------- 즐겨찾기 -----------
    if st.button("⭐ 이 종목 즐겨찾기 추가"):
        if code not in favs:
            favs.append(code)
            save_favorites(favs)
            st.success("즐겨찾기 등록됨!")
        else:
            st.info("이미 등록된 종목입니다.")
