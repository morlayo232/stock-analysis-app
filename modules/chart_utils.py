import plotly.graph_objs as go

def plot_price_rsi_macd_bb(df):
    # Bollinger Bands
    ma20 = df['종가'].rolling(20).mean()
    std20 = df['종가'].rolling(20).std()
    upper = ma20 + 2 * std20
    lower = ma20 - 2 * std20

    # Price + BB
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['종가'], name='종가'))
    fig_price.add_trace(go.Scatter(x=df.index, y=ma20,    name='MA20', line=dict(color='gray')))
    fig_price.add_trace(go.Scatter(x=df.index, y=upper,  name='BB 상단', line=dict(color='lightblue'), fill=None))
    fig_price.add_trace(go.Scatter(x=df.index, y=lower,  name='BB 하단', line=dict(color='lightblue'), fill='tonexty'))
    fig_price.update_layout(title='가격 + Bollinger Bands', yaxis_title='원', margin=dict(t=40))

    # RSI
    from modules.calculate_indicators import calc_rsi, calc_macd
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=calc_rsi(df), name='RSI(14)'))
    fig_rsi.update_layout(title='RSI(14)', yaxis_range=[0,100], margin=dict(t=30))

    # MACD
    macd, signal, hist = calc_macd(df)
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar(    x=df.index, y=hist,   name='Histogram'))
    fig_macd.add_trace(go.Scatter(x=df.index, y=macd,   name='MACD'))
    fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal'))
    fig_macd.update_layout(title='MACD', margin=dict(t=30))

    return fig_price, fig_rsi, fig_macd
