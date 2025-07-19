import plotly.graph_objs as go

def plot_price_rsi_macd(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['종가'], name='종가'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name='EMA(20)', line=dict(dash='dash')))
    fig.update_layout(title="가격 및 EMA(20)", yaxis_title="가격")

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], name='RSI(14)'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="blue")
    fig_rsi.update_layout(title="RSI(14)", yaxis=dict(range=[0, 100]))

    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_SIGNAL'], name='Signal'))
    fig_macd.add_hline(y=0, line_dash="dash", line_color="black")
    fig_macd.update_layout(title="MACD & Signal")

    return fig, fig_rsi, fig_macd
