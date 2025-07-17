import plotly.graph_objs as go

def plot_price_rsi_macd_bb(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["날짜"], y=df["종가"], mode='lines', name='종가'))
    if "EMA20" in df.columns:
        fig.add_trace(go.Scatter(x=df["날짜"], y=df["EMA20"], mode='lines', name='EMA20'))
    if "BB_low" in df.columns and "BB_high" in df.columns:
        fig.add_trace(go.Scatter(x=df["날짜"], y=df["BB_low"], mode='lines', name='BB_low'))
        fig.add_trace(go.Scatter(x=df["날짜"], y=df["BB_high"], mode='lines', name='BB_high'))
    fig_rsi = go.Figure()
    if "RSI" in df.columns:
        fig_rsi.add_trace(go.Scatter(x=df["날짜"], y=df["RSI"], mode='lines', name='RSI'))
    fig_macd = go.Figure()
    if "MACD" in df.columns and "Signal" in df.columns:
        fig_macd.add_trace(go.Scatter(x=df["날짜"], y=df["MACD"], mode='lines', name='MACD'))
        fig_macd.add_trace(go.Scatter(x=df["날짜"], y=df["Signal"], mode='lines', name='Signal'))
    return fig, fig_rsi, fig_macd
