import pandas as pd
import plotly.graph_objs as go

def plot_price_rsi_macd_bb(df):
    """
    주가 차트: 종가 + EMA20 + Bollinger Bands
    RSI 차트: 14일 RSI
    MACD 차트: MACD, Signal, Histogram
    """
    df = df.copy()
    # Bollinger Bands
    df['MA20'] = df['종가'].rolling(window=20).mean()
    df['STD20'] = df['종가'].rolling(window=20).std()
    df['BB_low'] = df['MA20'] - 2 * df['STD20']
    df['BB_high'] = df['MA20'] + 2 * df['STD20']
    # EMA20
    df['EMA20'] = df['종가'].ewm(span=20, adjust=False).mean()

    # 1) 가격 + EMA20 + BB
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['종가'], name="종가"))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA(20)", line=dict(dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_low'], name="BB 하단", line=dict(color='lightgrey')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_high'], name="BB 상단", line=dict(color='lightgrey')))
    fig_price.update_layout(
        title="주가 & EMA20 + Bollinger Bands",
        yaxis_title="가격",
        height=400,
        margin=dict(t=50, b=20)
    )

    # 2) RSI(14)
    delta = df['종가'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(window=14, min_periods=1).mean()
    ma_down = down.rolling(window=14, min_periods=1).mean()
    rs = ma_up / (ma_down + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI(14)"))
    fig_rsi.update_layout(
        title="RSI (14)",
        yaxis_title="RSI",
        height=350,
        margin=dict(t=50, b=20)
    )

    # 3) MACD
    ema12 = df['종가'].ewm(span=12, adjust=False).mean()
    ema26 = df['종가'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar(x=df.index, y=hist, name="MACD 히스토그램"))
    fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name="MACD"))
    fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name="Signal"))
    fig_macd.update_layout(
        title="MACD",
        yaxis_title="값",
        height=350,
        margin=dict(t=50, b=20)
    )

    return fig_price, fig_rsi, fig_macd
