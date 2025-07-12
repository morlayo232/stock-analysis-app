import yfinance as yf
import pandas as pd
import ta

TOOLTIP_EXPLANATIONS = {
    "RSI": "상대강도지수: 과매수/과매도 상태 판단 (70↑ 과매수, 30↓ 과매도)",
    "EMA": "지수이동평균선: 최근 가격에 가중치를 둔 추세 지표",
    "MACD": "이동평균 간 차이를 이용한 추세 반전 지표",
    "PER": "주가수익비율: 수익 대비 주가 수준 (낮을수록 저평가)",
    "PBR": "주가순자산비율: 자산 대비 주가 수준 (1보다 낮으면 저평가)",
    "배당수익률": "연 배당금 ÷ 주가 = 배당 투자 수익률"
}

# 주가 데이터 로드 (야후 파이낸스)
def load_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        df.reset_index(inplace=True)
        if df.empty or len(df) < 10:
            return pd.DataFrame()
        df = df.rename(columns={"Date": "Date"})
        return df
    except:
        return pd.DataFrame()

# 기술 지표 계산
def calculate_indicators(df):
    df['EMA5'] = ta.trend.EMAIndicator(df['Close'], window=5).ema_indicator()
    df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()
    return df

# 투자 성향별 점수 계산
def calc_investment_score(df, style):
    score = 0

    rsi = df['RSI'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    signal = df['Signal'].iloc[-1]
    ema5 = df['EMA5'].iloc[-1]
    ema20 = df['EMA20'].iloc[-1]

    if style == '공격적':
        if rsi < 30: score += 10
        if macd > signal: score += 10
    elif style == '안정적':
        if ema5 > ema20: score += 10
        if rsi < 60: score += 5
    elif style == '배당형':
        # 배당 수익률은 filtered_stocks.csv에서 보조적으로 참조됨
        score += 5
        if rsi < 50: score += 5

    return float(score)
