# modules/calculate_indicators.py

import pandas as pd

def calc_ema(df, window=20, col='종가'):
    return df[col].ewm(span=window, adjust=False).mean()

def calc_rsi(df, window=14, col='종가'):
    delta = df[col].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(window=window, min_periods=1).mean()
    ma_down = down.rolling(window=window, min_periods=1).mean()
    rs = ma_up / (ma_down + 1e-6)
    return 100 - (100 / (1 + rs))

def calc_macd(df, col='종가'):
    ema12 = df[col].ewm(span=12, adjust=False).mean()
    ema26 = df[col].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def plot_price_rsi_macd_bb(df):
    """
    종가 + 볼린저밴드, RSI, MACD를 각각 Plotly Figure 로 반환
    """
    import plotly.graph_objs as go

    # 볼린저 밴드 계산
    ma20 = df['종가'].rolling(20).mean()
    std20 = df['종가'].rolling(20).std()
    bb_high = ma20 + 2 * std20
    bb_low  = ma20 - 2 * std20

    # price + BB
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['종가'],    name='종가'))
    fig.add_trace(go.Scatter(x=df.index, y=ma20,          name='MA20', line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=bb_high,       name='BB 상단', line=dict(color='rgba(0,0,0,0.2)')))
    fig.add_trace(go.Scatter(x=df.index, y=bb_low,        name='BB 하단', line=dict(color='rgba(0,0,0,0.2)')))
    fig.update_layout(title='종가 & 볼린저밴드', yaxis_title='가격')

    # RSI
    rsi = calc_rsi(df, window=14)
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI(14)'))
    fig_rsi.update_layout(title='RSI (14)', yaxis=dict(range=[0,100]))

    # MACD
    macd, signal, hist = calc_macd(df)
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar  (x=df.index, y=hist,   name='히스토그램'))
    fig_macd.add_trace(go.Scatter(x=df.index, y=macd,   name='MACD'))
    fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(dash='dash')))
    fig_macd.update_layout(title='MACD', yaxis_title='값')

    return fig, fig_rsi, fig_macd
