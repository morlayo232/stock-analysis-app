import plotly.graph_objects as go

def plot_stock_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="종가", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA5"], name="EMA 5일", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA 20일", line=dict(color="green")))

    for i in range(1, len(df)):
        if df["EMA5"].iloc[i-1] < df["EMA20"].iloc[i-1] and df["EMA5"].iloc[i] > df["EMA20"].iloc[i]:
            fig.add_trace(go.Scatter(x=[df["Date"].iloc[i]], y=[df["Close"].iloc[i]], mode="markers",
                                     marker_symbol="triangle-up", marker_color="green", marker_size=10,
                                     name="골든크로스 매수", showlegend=False))
        elif df["EMA5"].iloc[i-1] > df["EMA20"].iloc[i-1] and df["EMA5"].iloc[i] < df["EMA20"].iloc[i]:
            fig.add_trace(go.Scatter(x=[df["Date"].iloc[i]], y=[df["Close"].iloc[i]], mode="markers",
                                     marker_symbol="triangle-down", marker_color="red", marker_size=10,
                                     name="데드크로스 매도", showlegend=False))

    fig.update_layout(title="📈 주가 + 이동평균선 + 매수/매도 신호",
                      xaxis_title="날짜", yaxis_title="가격", hovermode="x unified")
    return fig

def plot_rsi_macd(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], name="RSI", line=dict(color="purple")))
    fig.add_trace(go.Scatter(x=df["Date"], y=[70]*len(df), name="과매수선 (70)", line=dict(color="red", dash="dot")))
    fig.add_trace(go.Scatter(x=df["Date"], y=[30]*len(df), name="과매도선 (30)", line=dict(color="blue", dash="dot")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color="black")))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Signal"], name="Signal", line=dict(color="orange")))

    fig.update_layout(title="📊 RSI & MACD 분석", xaxis_title="날짜", hovermode="x unified")
    return fig