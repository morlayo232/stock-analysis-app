# modules/chart_utils.py

import plotly.graph_objs as go

def plot_price_rsi_macd(df):
    # 1. 메인 차트(골든/데드 텍스트 제거, 마커 소형/반투명)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['종가'], name="종가", line=dict(color='#3366CC', width=2)))
    if 'EMA20' in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], name="EMA(20)", line=dict(color='#FF9900', dash='dot', width=2)))
    if 'EMA20' in df:
        cross = (df['종가'] > df['EMA20']).astype(int).diff()
        golden = df.index[(cross == 1)].tolist()
        dead = df.index[(cross == -1)].tolist()
        # 골든크로스: 초록 삼각(위), 반투명
        if golden:
            fig.add_trace(go.Scatter(
                x=golden,
                y=[df.loc[idx, '종가'] for idx in golden],
                mode="markers",
                marker=dict(color='rgba(0,200,0,0.4)', size=10, symbol='triangle-up'),
                name="골든크로스"
            ))
        # 데드크로스: 빨강 삼각(아래), 반투명
        if dead:
            fig.add_trace(go.Scatter(
                x=dead,
                y=[df.loc[idx, '종가'] for idx in dead],
                mode="markers",
                marker=dict(color='rgba(200,0,0,0.4)', size=10, symbol='triangle-down'),
                name="데드크로스"
            ))
    fig.update_layout(
        title="가격(종가), EMA(20), 골든/데드크로스",
        yaxis_title="가격(원)", legend_title="지표",
        template="plotly_white", height=400, width=900, font=dict(size=13),
        margin=dict(t=60, b=50),  # 위아래 여백 추가
        legend=dict(itemsizing='constant')
    )

    # 2. RSI 차트
    fig_rsi = go.Figure()
    if 'RSI' in df:
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                     name="RSI(14)", line=dict(color='#9900CC', width=2)))
        fig_rsi.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=70, y1=70,
                          line=dict(color="red", width=1, dash="dash"))
        fig_rsi.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=30, y1=30,
                          line=dict(color="blue", width=1, dash="dash"))
        fig_rsi.update_layout(title="RSI(14)", height=200, width=900, template="plotly_white", font=dict(size=13), yaxis=dict(range=[0, 100]))
    else:
        fig_rsi.update_layout(title="RSI 데이터 없음", height=200, width=900, template="plotly_white")

    # 3. MACD 차트
    fig_macd = go.Figure()
    if 'MACD' in df and 'Signal' in df:
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'],
                                      name="MACD", line=dict(color='#008800', width=2)))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'],
                                      name="Signal", line=dict(color='#FF6600', width=2)))
        fig_macd.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=0, y1=0,
                           line=dict(color="black", width=1, dash="dash"))
        fig_macd.update_layout(title="MACD & Signal", height=200, width=900, template="plotly_white", font=dict(size=13))
    else:
        fig_macd.update_layout(title="MACD 데이터 없음", height=200, width=900, template="plotly_white")

    return fig, fig_rsi, fig_macd
