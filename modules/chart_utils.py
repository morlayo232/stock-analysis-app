import plotly.graph_objects as go
from modules.calculate_indicators import calc_ema, calc_rsi, calc_macd

def plot_price_rsi_macd_bb(df: pd.DataFrame):
    df = df.copy()
    # Bollinger Bands
    df["MA20"] = df["종가"].rolling(20).mean()
    df["STD20"]= df["종가"].rolling(20).std()
    df["BB_high"] = df["MA20"] + 2*df["STD20"]
    df["BB_low"]  = df["MA20"] - 2*df["STD20"]
    df["EMA20"]   = calc_ema(df,20,"종가")
    # Price + BB
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df["종가"], name="종가"))
    fig_price.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA20", line=dict(dash="dash")))
    fig_price.add_trace(go.Scatter(x=df.index, y=df["BB_high"], name="BB 상단", line=dict(color="lightgray")))
    fig_price.add_trace(go.Scatter(x=df.index, y=df["BB_low"],  name="BB 하단", line=dict(color="lightgray")))
    fig_price.update_layout(title="주가 + EMA20 + Bollinger Bands", height=400)
    # RSI
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=calc_rsi(df), name="RSI(14)"))
    fig_rsi.update_layout(title="RSI (14)", height=350)
    # MACD
    macd, sig, hist = calc_macd(df)
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar(x=df.index, y=hist, name="히스토그램"))
    fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name="MACD"))
    fig_macd.add_trace(go.Scatter(x=df.index, y=sig,  name="Signal"))
    fig_macd.update_layout(title="MACD", height=350)
    return fig_price, fig_rsi, fig_macd
