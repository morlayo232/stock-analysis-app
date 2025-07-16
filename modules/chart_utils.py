# modules/chart_utils.py

import plotly.graph_objs as go

def plot_price_rsi_macd(df):
    # 1. 메인 차트 (볼린저밴드 포함, 높이 통일)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['종가'], name="종가", line=dict(color='#3366CC', width=2)))
    if 'EMA20' in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], name="EMA(20)", line=dict(color='#FF9900', dash='dot', width=2)))
    if 'BB_high' in df and 'BB_low' in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_high'], name="볼린저밴드 상단", line=dict(color='gray', width=1, dash='dot')))
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_low'], name="볼린저밴드 하단", line=dict(color='gray', width=1, dash='dot')))
    if 'EMA20' in df:
        cross = (df['종가'] > df['EMA20']).astype(int).diff()
        golden = df.index[(cross == 1)].tolist()
        dead = df.index[(cross == -1)].tolist()
        for idx in golden:
            fig.add_trace(go.Scatter(
                x=[idx], y=[df.loc[idx, '종가']],
                mode="markers+text", marker=dict(color='green', size=14, symbol='triangle-up'),
                text=["골든"], name="골든크로스", textposition="top center"))
        for idx in dead:
            fig.add_trace(go.Scatter(
                x=[idx], y=[df.loc[idx, '종가']],
                mode="markers+text", marker=dict(color='red', size=14, symbol='triangle-down'),
                text=["데드"], name="데드크로스", textposition="bottom center"))
    fig.update_layout(
        title="가격(종가), EMA(20), 볼린저밴드, 골든/데드크로스",
        yaxis_title="가격(원)", legend_title="지표",
        template="plotly_white", height=340, width=900, font=dict(size=13)
    )

    # 2. RSI 차트 (높이 통일)
    fig_rsi = go.Figure()
    if 'RSI' in df:
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                     name="RSI(14)", line=dict(color='#9900CC', width=2)))
        fig_rsi.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=70, y1=70,
                          line=dict(color="red", width=1, dash="dash"))
        fig_rsi.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=30, y1=30,
                          line=dict(color="blue", width=1, dash="dash"))
        fig_rsi.update_layout(title="RSI(14)", height=300, width=900, template="plotly_white", font=dict(size=13), yaxis=dict(range=[0, 100]))
    else:
        fig_rsi.update_layout(title="RSI 데이터 없음", height=300, width=900, template="plotly_white")

    # 3. MACD 차트 (높이 통일)
    fig_macd = go.Figure()
    if 'MACD' in df and 'Signal' in df:
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'],
                                      name="MACD", line=dict(color='#008800', width=2)))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'],
                                      name="Signal", line=dict(color='#FF6600', width=2)))
        fig_macd.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=0, y1=0,
                           line=dict(color="black", width=1, dash="dash"))
        fig_macd.update_layout(title="MACD & Signal", height=300, width=900, template="plotly_white", font=dict(size=13))
    else:
        fig_macd.update_layout(title="MACD 데이터 없음", height=300, width=900, template="plotly_white")

    return fig, fig_rsi, fig_macd
