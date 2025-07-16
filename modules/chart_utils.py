# modules/chart_utils.py

import plotly.graph_objects as go

def plot_price_rsi_macd(df):
    # 날짜 컬럼이 '날짜' or index라면 df = df.reset_index() 처리
    if '날짜' in df.columns:
        x = df['날짜']
    elif df.index.name is not None:
        x = df.index
    else:
        x = list(range(len(df)))
    # 가격
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df['종가'], mode='lines', name='종가'))
    if 'EMA20' in df.columns:
        fig.add_trace(go.Scatter(x=x, y=df['EMA20'], mode='lines', name='EMA(20)'))
    if 'BB_low' in df.columns and 'BB_high' in df.columns:
        fig.add_trace(go.Scatter(x=x, y=df['BB_low'], mode='lines', name='BB_low', line=dict(dash='dot')))
        fig.add_trace(go.Scatter(x=x, y=df['BB_high'], mode='lines', name='BB_high', line=dict(dash='dot')))
    fig.update_layout(height=350, margin=dict(t=30, b=30))

    # RSI
    fig_rsi = go.Figure()
    if 'RSI' in df.columns:
        fig_rsi.add_trace(go.Scatter(x=x, y=df['RSI'], mode='lines', name='RSI', line=dict(color='magenta')))
        fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
        fig_rsi.add_hline(y=30, line_dash='dash', line_color='blue')
        fig_rsi.update_layout(height=220, margin=dict(t=30, b=30))

    # MACD
    fig_macd = go.Figure()
    if 'MACD' in df.columns and 'Signal' in df.columns:
        fig_macd.add_trace(go.Scatter(x=x, y=df['MACD'], mode='lines', name='MACD', line=dict(color='green')))
        fig_macd.add_trace(go.Scatter(x=x, y=df['Signal'], mode='lines', name='Signal', line=dict(color='orange')))
        fig_macd.update_layout(height=220, margin=dict(t=30, b=30))

    return fig, fig_rsi, fig_macd
