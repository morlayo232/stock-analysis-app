import streamlit as st
import pandas as pd
import json
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import finalize_scores
from modules.chart_utils import plot_stock_chart, plot_rsi_macd
from modules.fetch_price import fetch_stock_price
from modules.fetch_news import fetch_news_headlines
from update_stock_database import main as update_main

# ---- 상단 로고/투자매니저 ----
st.set_page_config(page_title="투자 매니저", layout="wide")
LOGO_PATH = "logo_tynex.png"

col1, col2 = st.columns([0.18, 0.82])
with col1:
    st.image(LOGO_PATH, width=120)
with col2:
    st.markdown("""
    <div style="margin-top:26px;display:flex;align-items:center;">
        <span style="font-size:2.08rem;font-weight:800;letter-spacing:0.02em;">투자 매니저</span>
        <span style="flex:1;height:2px;background:linear-gradient(to right,#a7a7a7,#e7e7e7,#fff);margin-left:16px;"></span>
    </div>
    """, unsafe_allow_html=True)
st.markdown('<hr style="margin:0 0 14px 0;">', unsafe_allow_html=True)
st.markdown("""
<div style="padding:8px 0 7px 0; font-size:1.1rem; color:#259a51; border-bottom: 1.5px solid #e3e3e3;">
<b>스코어 산정 안내:</b>
PER·PBR·ROE·배당률을 z-score로 표준화, 투자 성향별 가중치로 종합.<br>
공격적=기술지표·수익률↑, 안정적=저PBR·저PER·ROE↑, 배당형=배당↑.  
상위 10개는 "투자 성향별 추천 TOP10"에 즉시 반영.
</div>
""", unsafe_allow_html=True)

# ---- sidebar ----
st.sidebar.header("투자 성향 선택")
style = st.sidebar.radio("성향", ["공격적", "안정적", "배당형"])

st.sidebar.subheader("종목명 검색")
keyword = st.sidebar.text_input("검색", "")

def search_stocks(keyword, df):
    return df[df["종목명"].str.contains(keyword, case=False)] if keyword else pd.DataFrame()
@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv("filtered_stocks.csv", dtype=str)

df = load_filtered_stocks()
search_result = search_stocks(keyword, df) if not df.empty else pd.DataFrame()
selected_row = None
opt_list = []
if not search_result.empty:
    opt_list = search_result["종목명"] + " (" + search_result["종목코드"] + ")"
if opt_list:
    selected_row = st.sidebar.selectbox("검색된 종목", opt_list, key="searchbox")
elif not df.empty:
    selected_row = f'{df.iloc[0]["종목명"]} ({df.iloc[0]["종목코드"]})'

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

# ---- style별 점수 자동적용/추천 TOP10 카드 ----
df = finalize_scores(df, style=style)
df["score"] = pd.to_numeric(df["score"], errors="coerce")
df_disp = df[df["score"].notnull()].sort_values("score", ascending=False)
top10 = df_disp.head(10)

st.markdown("## 🏆 투자 성향별 추천 TOP 10")
st.markdown('<div style="display:flex;flex-wrap:wrap;gap:17px;">', unsafe_allow_html=True)
for _, row in top10.iterrows():
    st.markdown(f"""
    <div style="flex:1 1 250px; background:#fff; border-radius:13px; border:1px solid #e6e6e6;
                box-shadow:0 2px 8px #0002; margin-bottom:0.6em; padding:1.15em 1em;">
        <div style="font-size:1.07em;font-weight:700;color:#333;">
            <a href="#종목_{row['종목코드']}" style="color:inherit;text-decoration:none;">{row['종목명']}</a>
        </div>
        <div style="margin:2px 0 7px 0;color:#888;">{row['종목코드']} | {row['시장구분']}</div>
        <div style="font-size:1.23em;color:#19b763;font-weight:700;">점수 {row['score']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---- 종목 상세 ----
if selected_row:
    code = selected_row.split("(")[-1].replace(")", "")
    stock = df[df["종목코드"] == code].iloc[0]
    st.markdown(f'<a id="종목_{stock["종목코드"]}"></a>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin:24px 0 7px 0;display:flex;align-items:center;">
        <span style="font-size:1.3em;font-weight:700;">📌 {stock['종목명']} ({stock['종목코드']})</span>
        <span style="margin-left:15px;color:#868;">| 투자 성향 <b>{style}</b> | 점수 <b>{stock['score'] if pd.notnull(stock['score']) else '—'}</b></span>
    </div>
    """, unsafe_allow_html=True)
    def score_eval(score):
        if pd.isnull(score): return "평가 불가(데이터 부족)"
        score = float(score)
        if score > 1.5: return "매우 매력적 (상위 10%)"
        elif score > 0.8: return "양호 (상위 30%)"
        elif score > 0: return "보통 (중간)"
        elif score > -0.8: return "저평가/관망"
        else: return "매력 낮음/주의"
    st.success(f"종목 평가: {score_eval(stock['score'])}")

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

    try:
        if "EMA_Cross" in df_price.columns and not df_price["EMA_Cross"].isnull().all():
            ema_cross_buy = df_price[df_price["EMA_Cross"] == "golden"]
            ema_cross_sell = df_price[df_price["EMA_Cross"] == "dead"]
            latest_buy = ema_cross_buy["Close"].iloc[-1] if not ema_cross_buy.empty else None
            latest_sell = ema_cross_sell["Close"].iloc[-1] if not ema_cross_sell.empty else None
            st.markdown("### 💲 추천 매수/매도 가격")
            st.info(f"최근 골든크로스 매수: {latest_buy:.2f}원" if latest_buy else "골든크로스 신호 없음")
            st.info(f"최근 데드크로스 매도: {latest_sell:.2f}원" if latest_sell else "데드크로스 신호 없음")
        else:
            st.warning("추천가 신호 없음")
    except Exception as e:
        st.error(f"추천가 계산 오류: {e}")

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

    st.markdown("### 📰 관련 뉴스")
    try:
        news_list = fetch_news_headlines(stock["종목명"])
        if news_list:
            for news in news_list:
                st.markdown(f'<div style="margin-bottom:6px;">📰 <a href="{news["link"]}" target="_blank">{news["title"]}</a></div>', unsafe_allow_html=True)
        else:
            st.info("뉴스 없음")
    except Exception as e:
        st.error(f"뉴스 크롤링 오류: {e}")

    if st.button("⭐ 이 종목 즐겨찾기 추가"):
        if code not in favs:
            favs.append(code)
            save_favorites(favs)
            st.success("즐겨찾기 등록됨!")
        else:
            st.info("이미 등록된 종목입니다.")
