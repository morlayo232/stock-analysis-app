# modules/chart_utils.py

import plotly.graph_objs as go

def plot_price_rsi_macd_bb(df):
    if df is None or df.empty:
        return None, None, None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['일자'], y=df['종가'], mode='lines', name='종가', line=dict(color='blue')))
    # 볼린저밴드 예시 (MA20, 상하한)
    if 'MA20' in df.columns and 'BB_upper' in df.columns and 'BB_lower' in df.columns:
        fig.add_trace(go.Scatter(x=df['일자'], y=df['MA20'], name='MA20', line=dict(color='orange', dash='dot')))
        fig.add_trace(go.Scatter(x=df['일자'], y=df['BB_upper'], name='BB_upper', line=dict(color='gray'), opacity=0.3))
        fig.add_trace(go.Scatter(x=df['일자'], y=df['BB_lower'], name='BB_lower', line=dict(color='gray'), opacity=0.3))
    fig.update_layout(height=300, title="주가 및 볼린저밴드")
    # RSI
    fig_rsi = go.Figure()
    if 'RSI' in df.columns:
        fig_rsi.add_trace(go.Scatter(x=df['일자'], y=df['RSI'], name='RSI', line=dict(color='purple')))
    fig_rsi.update_layout(height=200, title="RSI(14)")
    # MACD
    fig_macd = go.Figure()
    if 'MACD' in df.columns and 'Signal' in df.columns:
        fig_macd.add_trace(go.Scatter(x=df['일자'], y=df['MACD'], name='MACD', line=dict(color='green')))
        fig_macd.add_trace(go.Scatter(x=df['일자'], y=df['Signal'], name='Signal', line=dict(color='orange')))
    fig_macd.update_layout(height=200, title="MACD & Signal")
    return fig, fig_rsi, fig_macd
