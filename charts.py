import plotly.graph_objects as go
import yfinance as yf
import ta

# 📈 종가 + 이동평균선(EMA) 차트
def plot_price_chart(ticker):
    df = yf.Ticker(ticker).history(period="6mo")
    df.reset_index(inplace=True)

    df['EMA5'] = ta.trend.EMAIndicator(df['Close'], window=5).ema_indicator()
    df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='종가', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA5'], name='EMA 5일', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA20'], name='EMA 20일', line=dict(color='green')))

    # 골든/데드크로스 시그널 표시
    for i in range(1, len(df)):
        if df['EMA5'].iloc[i-1] < df['EMA20'].iloc[i-1] and df['EMA5'].iloc[i] > df['EMA20'].iloc[i]:
            fig.add_trace(go.Scatter(x=[df['Date'].iloc[i]], y=[df['Close'].iloc[i]],
                                     mode='markers', marker_symbol='triangle-up',
                                     marker_color='green', marker_size=10, name='골든크로스'))
        elif df['EMA5'].iloc[i-1] > df['EMA20'].iloc[i-1] and df['EMA5'].iloc[i] < df['EMA20'].iloc[i]:
            fig.add_trace(go.Scatter(x=[df['Date'].iloc[i]], y=[df['Close'].iloc[i]],
                                     mode='markers', marker_symbol='triangle-down',
                                     marker_color='red', marker_size=10, name='데드크로스'))

    fig.update_layout(title=f"{ticker} 주가 차트 + 골든/데드크로스", xaxis_title="날짜", yaxis_title="가격", hovermode="x unified")
    return fig

# 📊 RSI & MACD 차트
def plot_indicators(ticker):
    df = yf.Ticker(ticker).history(period="6mo")
    df.reset_index(inplace=True)

    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='purple')))
    fig.add_trace(go.Scatter(x=df['Date'], y=[70]*len(df), name='과매수선(70)', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Date'], y=[30]*len(df), name='과매도선(30)', line=dict(color='blue', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal', line=dict(color='orange')))

    fig.update_layout(title=f"{ticker} 기술 지표 (RSI & MACD)", xaxis_title="날짜", hovermode="x unified")
    return fig
