import plotly.graph_objs as go

def plot_price_rsi_macd(df):
    fig = go.Figure()
    # 종가 라인
    fig.add_trace(go.Scatter(x=df.index, y=df['종가'], name="종가"))
    # EMA
    if 'EMA_20' in df:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name="EMA(20)", line=dict(dash='dash')))
    fig.update_layout(title="가격 및 EMA", yaxis_title="가격", legend_title="지표")
    # RSI, MACD는 서브차트로 따로 그리는 것이 일반적 (생략 또는 필요시 추가)
    return fig
