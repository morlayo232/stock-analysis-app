# modules/chart_utils.py

import plotly.graph_objs as go

def plot_price_rsi_macd(df):
    # 날짜 x축 처리
    if "날짜" in df.columns:
        x = df["날짜"]
    elif df.index.name is not None and "date" in str(df.index.name).lower():
        x = df.index
    else:
        x = list(range(len(df)))

    # 가격 메인 차트
    fig = go.Figure()
    try:
        fig.add_trace(go.Scatter(x=x, y=df['종가'], name="종가", line=dict(color='#3366CC', width=2)))
        if 'EMA20' in df.columns:
            fig.add_trace(go.Scatter(x=x, y=df['EMA20'], name="EMA(20)", line=dict(color='#FF9900', dash='dot', width=2)))
        if 'BB_low' in df.columns:
            fig.add_trace(go.Scatter(x=x, y=df['BB_low'], name="BB_low", line=dict(color='#B0B0B0', dash='dot')))
        if 'BB_high' in df.columns:
            fig.add_trace(go.Scatter(x=x, y=df['BB_high'], name="BB_high", line=dict(color='#B0B0B0', dash='dot')))
        fig.update_layout(
            title="가격(종가), EMA(20), 볼린저밴드",
            yaxis_title="가격(원)", legend_title="지표",
            template="plotly_white", height=260, font=dict(size=13), margin=dict(t=30, b=30)
        )
    except Exception as e:
        return None, None, None

    # RSI 차트
    fig_rsi = go.Figure()
    try:
        if 'RSI' in df.columns:
            fig_rsi.add_trace(go.Scatter(x=x, y=df['RSI'],
                                         name="RSI(14)", line=dict(color='#9900CC', width=2)))
            fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
            fig_rsi.add_hline(y=30, line_dash='dash', line_color='blue')
            fig_rsi.update_layout(title="RSI(14)", height=200, template="plotly_white", font=dict(size=13), yaxis=dict(range=[0, 100]), margin=dict(t=30, b=30))
        else:
            fig_rsi.update_layout(title="RSI 데이터 없음", height=200, template="plotly_white")
    except Exception as e:
        fig_rsi = None

    # MACD 차트
    fig_macd = go.Figure()
    try:
        if 'MACD' in df.columns and 'Signal' in df.columns:
            fig_macd.add_trace(go.Scatter(x=x, y=df['MACD'],
                                          name="MACD", line=dict(color='#008800', width=2)))
            fig_macd.add_trace(go.Scatter(x=x, y=df['Signal'],
                                          name="Signal", line=dict(color='#FF6600', width=2)))
            fig_macd.add_hline(y=0, line_dash='dash', line_color='black')
            fig_macd.update_layout(title="MACD & Signal", height=200, template="plotly_white", font=dict(size=13), margin=dict(t=30, b=30))
        else:
            fig_macd.update_layout(title="MACD 데이터 없음", height=200, template="plotly_white")
    except Exception as e:
        fig_macd = None

    # 반드시 3개 반환!
    return fig, fig_rsi, fig_macd
