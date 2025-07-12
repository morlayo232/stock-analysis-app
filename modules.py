import yfinance as yf
import pandas as pd
import ta

TOOLTIP_EXPLANATIONS = {
    "RSI": "상대강도지수: 과매수/과매도 상태 판단 (70↑ 과매수, 30↓ 과매도)",
    "EMA": "지수이동평균선: 최근 가격에 가중치를 둔 추세 지표",
    "MACD": "이동평균 간 차이를 이용한 추세 반전 지표",
    "PER": "주가수익비율: 수익 대비 주가 수준 (낮을수록 저평가)",
    "PBR": "주가순자산비율: 자산 대비 주가 수준 (1보다 낮으면 저평가)",
    "배당수익률": "연 배당금 ÷ 주가 = 배당 투자 수익률",
    "score": "PER, PBR, ROE 기반의 z-score로 산출한 정량 투자 매력 점수"
}

def load_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        df.reset_index(inplace=True)
        if df.empty or len(df) < 10:
            raise ValueError("No data")
        return df
    except:
        return pd.DataFrame()

def calculate_indicators(df):
    df['EMA5'] = ta.trend.EMAIndicator(df['Close'], window=5).ema_indicator()
    df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()
    return df

def calc_investment_score(df, style):
    score = 0
    if style == '공격적':
        if df['RSI'].iloc[-1] < 30:
            score += 15
        if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]:
            score += 10
    elif style == '안정적':
        if df['EMA5'].iloc[-1] > df['EMA20'].iloc[-1]:
            score += 10
    elif style == '배당형':
        score += 5  # 실제 배당률 반영은 추후

    if 'score' in df.columns:
        try:
            score += float(df['score'].iloc[-1])  # 정량 투자 점수 반영
        except:
            pass
    return float(score)
