import plotly.graph_objs as go

def plot_stock_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="종가", line=dict(color="royalblue")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA5"], mode="lines", name="EMA 5일", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], mode="lines", name="EMA 20일", line=dict(color="green")))
    buy_signals = df[df["EMA_Cross"] == "golden"]
    sell_signals = df[df["EMA_Cross"] == "dead"]
    fig.add_trace(go.Scatter(
        x=buy_signals["Date"], y=buy_signals["Close"], mode="markers",
        name="매수", marker=dict(color="limegreen", symbol="triangle-up", size=14)
    ))
    fig.add_trace(go.Scatter(
        x=sell_signals["Date"], y=sell_signals["Close"], mode="markers",
        name="매도", marker=dict(color="red", symbol="triangle-down", size=14)
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=340,
        xaxis_title="날짜",
        yaxis_title="가격",
        template="plotly_white"
    )
    return fig

def plot_rsi_macd(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], name="RSI", line=dict(color="slateblue")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color="deeppink")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Signal"], name="Signal", line=dict(color="gray")))
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=210,
        xaxis_title="날짜",
        yaxis_title="지표",
        template="plotly_white"
    )
    return fig
