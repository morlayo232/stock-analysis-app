import plotly.graph_objects as go

def plot_stock_chart(df):
    fig = go.Figure()

    # 종가, EMA 선 추가
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='종가', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA5'], name='EMA 5일', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA20'], name='EMA 20일', line=dict(color='green')))

    # 골든크로스/데드크로스 마커 추가
    for i in range(1, len(df)):
        prev_ema5 = df['EMA5'].iloc[i - 1]
        prev_ema20 = df['EMA20'].iloc[i - 1]
        curr_ema5 = df['EMA5'].iloc[i]
        curr_ema20 = df['EMA20'].iloc[i]
        if prev_ema5 < prev_ema20 and curr_ema5 > curr_ema20:
            fig.add_trace(go.Scatter(
                x=[df['Date'].iloc[i]],
                y=[df['Close'].iloc[i]],
                mode='markers',
                marker=dict(symbol='triangle-up', color='green', size=10),
                name='골든크로스'
            ))
        elif prev_ema5 > prev_ema20 and curr_ema5 < curr_ema20:
            fig.add_trace(go.Scatter(
                x=[df['Date'].iloc[i]],
                y=[df['Close'].iloc[i]],
                mode='markers',
                marker=dict(symbol='triangle-down', color='red', size=10),
                name='데드크로스'
            ))

    fig.update_layout(
        title='📈 주가 + 이동평균 + 매수/매도 신호',
        xaxis_title='날짜',
        yaxis_title='가격',
        hovermode='x unified'
    )
    return fig

def plot_rsi_macd(df):
    fig = go.Figure()

    # RSI 라인
    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='purple')))
    fig.add_trace(go.Scatter(x=df['Date'], y=[70] * len(df), name='과매수선 (70)', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Date'], y=[30] * len(df), name='과매도선 (30)', line=dict(color='blue', dash='dot')))

    # MACD & Signal
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal', line=dict(color='orange')))

    fig.update_layout(
        title='📊 RSI & MACD 분석',
        xaxis_title='날짜',
        hovermode='x unified'
    )
    return fig
