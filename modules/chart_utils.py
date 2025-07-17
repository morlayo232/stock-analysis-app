import plotly.graph_objs as go
import pandas as pd

def plot_price_rsi_macd_bb(df):
    if df is None or df.empty or "종가" not in df:
        return None, None, None

    # 볼린저밴드
    df["MA20"] = df["종가"].rolling(20).mean()
    df["STD20"] = df["종가"].rolling(20).std()
    df["BB_high"] = df["MA20"] + 2*df["STD20"]
    df["BB_low"] = df["MA20"] - 2*df["STD20"]

    # RSI (14)
    delta = df["종가"].diff()
    gain = delta.where(delta>0,0)
    loss = -delta.where(delta<0,0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain/avg_loss
    df["RSI"] = 100 - (100/(1+rs))

    # MACD
    ema12 = df["종가"].ewm(span=12, adjust=False).mean()
    ema26 = df["종가"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # price+BB
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["일자"], y=df["종가"], mode="lines", name="종가"))
    fig.add_trace(go.Scatter(x=df["일자"], y=df["MA20"], mode="lines", name="MA20", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=df["일자"], y=df["BB_high"], mode="lines", name="BB_high", line=dict(color="lightblue")))
    fig.add_trace(go.Scatter(x=df["일자"], y=df["BB_low"], mode="lines", name="BB_low", line=dict(color="lightblue")))
    fig.update_layout(height=340, margin=dict(l=10, r=10, b=30, t=30))

    # RSI
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df["일자"], y=df["RSI"], mode="lines", line=dict(color="purple")))
    fig_rsi.add_shape(type="line", x0=min(df["일자"]), x1=max(df["일자"]), y0=70, y1=70, line=dict(dash="dash", color="red"))
    fig_rsi.add_shape(type="line", x0=min(df["일자"]), x1=max(df["일자"]), y0=30, y1=30, line=dict(dash="dash", color="blue"))
    fig_rsi.update_layout(height=180, margin=dict(l=10, r=10, b=20, t=20), yaxis=dict(range=[0,100]))

    # MACD
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df["일자"], y=df["MACD"], mode="lines", name="MACD", line=dict(color="green")))
    fig_macd.add_trace(go.Scatter(x=df["일자"], y=df["Signal"], mode="lines", name="Signal", line=dict(color="orange")))
    fig_macd.update_layout(height=180, margin=dict(l=10, r=10, b=20, t=20))
    return fig, fig_rsi, fig_macd
