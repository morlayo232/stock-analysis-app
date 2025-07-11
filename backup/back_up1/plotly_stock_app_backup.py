import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

# --- 즐겨찾기 저장파일 ---
FAV_FILE = "favorites.json"

# --- 네이버 크롤러 ---
def fetch_naver_stock_data(ticker, period_days=180):
    code = ticker.split('.')[0]
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=period_days)
    dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    page = 1
    while True:
        url = f"https://finance.naver.com/item/sise_day.nhn?code={code}&page={page}"
        res = requests.get(url)
        if res.status_code != 200:
            break
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class':'type2'})
        if not table:
            break
        rows = table.find_all('tr')[2:]
        if not rows:
            break
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 7:
                continue
            date_str = cols[0].text.strip()
            if date_str == '':
                continue
            date = datetime.datetime.strptime(date_str, '%Y.%m.%d')
            if date < start_date:
                return pd.DataFrame({
                    'Date': dates,
                    'Open': opens,
                    'High': highs,
                    'Low': lows,
                    'Close': closes,
                    'Volume': volumes
                })
            open_p = int(cols[1].text.replace(',', ''))
            high_p = int(cols[2].text.replace(',', ''))
            low_p = int(cols[3].text.replace(',', ''))
            close_p = int(cols[4].text.replace(',', ''))
            volume = int(cols[6].text.replace(',', ''))
            dates.append(date)
            opens.append(open_p)
            highs.append(high_p)
            lows.append(low_p)
            closes.append(close_p)
            volumes.append(volume)
        page += 1
    return pd.DataFrame({
        'Date': dates,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    })

# --- 투자성향별 필터 & 점수화 기준 (간단 예시) ---
def score_stock(row, strategy):
    score = 0
    # 공격형: 최근 거래량, 상승률 가중
    if strategy == "공격적":
        score += row['VolumeRank'] * 0.6 + row['ReturnRank'] * 0.4
    # 안정형: PER, PBR, 배당률 반영
    elif strategy == "안정적":
        score += (1 - row['PERRank']) * 0.5 + (1 - row['PBRRank']) * 0.3 + row['DividendRank'] * 0.2
    # 배당형: 배당률 가중
    else:
        score += row['DividendRank'] * 0.8 + (1 - row['PERRank']) * 0.2
    return score

# --- 종목 데이터 불러오기 ---
@st.cache_data(ttl=86400)
def load_filtered_stocks():
    return pd.read_csv("filtered_stocks.csv", dtype={'종목코드':str})

# --- yfinance + 네이버 크롤러 통합 ---
@st.cache_data(ttl=86400)
def load_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        df.reset_index(inplace=True)
        if df.empty or len(df) < 10:
            raise ValueError("No yfinance data")
        return df
    except:
        df = fetch_naver_stock_data(ticker)
        if df.empty:
            return None
        return df

# --- 즐겨찾기 관리 ---
def load_favorites():
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_favorites(fav_list):
    with open(FAV_FILE, 'w', encoding='utf-8') as f:
        json.dump(fav_list, f, ensure_ascii=False, indent=2)

# --- UI 시작 ---
st.title("📈 주식 분석 및 투자 매력도 평가")

strategy = st.sidebar.radio("투자 성향 선택", ["공격적", "안정적", "배당형"])

stocks_df = load_filtered_stocks()

search_input = st.sidebar.text_input("종목명 검색")
filtered_df = stocks_df[stocks_df['종목명'].str.contains(search_input, case=False)] if search_input else stocks_df

favorites = load_favorites()

# --- 종목 리스트 (즐겨찾기 포함) ---
st.sidebar.markdown("### ⭐ 즐겨찾기")
for f in favorites:
    st.sidebar.write(f)

st.sidebar.markdown("### 📋 종목 리스트")
selected_ticker = st.sidebar.selectbox("종목 선택", filtered_df['종목코드'] + " " + filtered_df['종목명'])

ticker_code = selected_ticker.split()[0]

# --- 가격 데이터 및 지표 계산 ---
price_df = load_stock_price(ticker_code)
if price_df is None or price_df.empty:
    st.error("데이터 로드 실패: 데이터를 불러올 수 없습니다.")
    st.stop()

price_df['EMA5'] = ta.trend.EMAIndicator(price_df['Close'], window=5).ema_indicator()
price_df['EMA20'] = ta.trend.EMAIndicator(price_df['Close'], window=20).ema_indicator()
price_df['RSI'] = ta.momentum.RSIIndicator(price_df['Close']).rsi()
macd = ta.trend.MACD(price_df['Close'])
price_df['MACD'] = macd.macd()
price_df['Signal'] = macd.macd_signal()

# --- 점수 계산 ---
stocks_df['VolumeRank'] = stocks_df['거래량'].rank(pct=True)
stocks_df['ReturnRank'] = stocks_df['수익률'].rank(pct=True)
stocks_df['PERRank'] = stocks_df['PER'].rank(pct=True)
stocks_df['PBRRank'] = stocks_df['PBR'].rank(pct=True)
stocks_df['DividendRank'] = stocks_df['배당률'].rank(pct=True)
stocks_df['Score'] = stocks_df.apply(lambda r: score_stock(r, strategy), axis=1)
top10_df = stocks_df.sort_values('Score', ascending=False).head(10)

st.markdown(f"### 선택 종목: {ticker_code}")
st.write(price_df.tail())

# --- 차트 ---
fig_price = go.Figure()
fig_price.add_trace(go.Scatter(x=price_df['Date'], y=price_df['Close'], name='종가', line=dict(color='blue')))
fig_price.add_trace(go.Scatter(x=price_df['Date'], y=price_df['EMA5'], name='EMA5', line=dict(color='orange')))
fig_price.add_trace(go.Scatter(x=price_df['Date'], y=price_df['EMA20'], name='EMA20', line=dict(color='green')))
fig_price.update_layout(title="주가 + 이동평균", xaxis_title="날짜", yaxis_title="가격", hovermode="x unified")
st.plotly_chart(fig_price, use_container_width=True)

fig_tech = go.Figure()
fig_tech.add_trace(go.Scatter(x=price_df['Date'], y=price_df['RSI'], name='RSI', line=dict(color='purple')))
fig_tech.add_trace(go.Scatter(x=price_df['Date'], y=[70]*len(price_df), name='과매수 (70)', line=dict(color='red', dash='dot')))
fig_tech.add_trace(go.Scatter(x=price_df['Date'], y=[30]*len(price_df), name='과매도 (30)', line=dict(color='blue', dash='dot')))
fig_tech.add_trace(go.Scatter(x=price_df['Date'], y=price_df['MACD'], name='MACD', line=dict(color='black')))
fig_tech.add_trace(go.Scatter(x=price_df['Date'], y=price_df['Signal'], name='Signal', line=dict(color='orange')))
fig_tech.update_layout(title="RSI & MACD", xaxis_title="날짜", hovermode="x unified")
st.plotly_chart(fig_tech, use_container_width=True)

# --- 투자 판단 ---
latest_rsi = price_df['RSI'].iloc[-1]
latest_macd = price_df['MACD'].iloc[-1]
latest_signal = price_df['Signal'].iloc[-1]

st.markdown("### 💡 투자 판단 요약")
if latest_rsi > 70:
    st.warning("⚠️ RSI 70 이상 → 과매수 구간으로 매도 고려")
elif latest_rsi < 30:
    st.success("✅ RSI 30 이하 → 과매도 구간으로 매수 기회")
else:
    st.info("ℹ️ RSI 중간값 → 관망")

if latest_macd > latest_signal:
    st.success("📈 MACD > Signal → 상승 전환 신호")
else:
    st.warning("📉 MACD < Signal → 하락 전환 주의")

# --- 상위 10개 종목 ---
st.markdown(f"### 💎 {strategy} 투자성향 상위 10개 추천 종목")
st.dataframe(top10_df[['종목코드', '종목명', 'Score']])

# --- 즐겨찾기 등록 ---
if st.button("즐겨찾기 추가"):
    if ticker_code not in favorites:
        favorites.append(ticker_code)
        save_favorites(favorites)
        st.success(f"{ticker_code} 가 즐겨찾기에 추가되었습니다.")
    else:
        st.info("이미 즐겨찾기에 등록된 종목입니다.")

# --- 기술 지표 설명 ---
with st.sidebar.expander("📖 기술 지표 설명 보기"):
    st.markdown("""
- **RSI (상대강도지수)**: 70 이상이면 과매수, 30 이하면 과매도로 판단  
- **MACD**: 추세 전환 지표 (MACD > Signal 이면 상승 추세로 판단)  
- **EMA**: 최근 가격에 가중치를 둔 이동 평균  
    """)
