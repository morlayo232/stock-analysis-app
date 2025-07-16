# chart_utils.py

import plotly.graph_objects as go
import pandas as pd

def plot_price_rsi_macd(df):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['시가'],
        high=df['고가'],
        low=df['저가'],
        close=df['종가'],
        name='Candlestick'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='orange')
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['MACD'],
        mode='lines',
        name='MACD',
        line=dict(color='blue')
    ))

    fig.update_layout(title="주식 차트 (RSI, MACD 포함)", xaxis_title="날짜", yaxis_title="가격")
    fig.show()

def plot_bollinger_band(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA20'],
        mode='lines',
        name='EMA20',
        line=dict(color='green')
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA20_upper'],
        mode='lines',
        name='Bollinger Upper',
        line=dict(color='red', dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA20_lower'],
        mode='lines',
        name='Bollinger Lower',
        line=dict(color='red', dash='dash')
    ))

    fig.update_layout(title="Bollinger Bands", xaxis_title="날짜", yaxis_title="가격")
    fig.show()
