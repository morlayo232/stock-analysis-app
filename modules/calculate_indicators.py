# modules/calculate_indicators.py

import pandas as pd
import numpy as np

def add_tech_indicators(df):
    df = df.copy()
    # 종가 기준 사용
    if "종가" in df.columns:
        close = df["종가"]
    elif "현재가" in df.columns:
        close = df["현재가"]
    else:
        close = df.iloc[:, -1]  # 마지막 컬럼
        df["현재가"] = close

    # 이동평균, 볼린저밴드, RSI, MACD, 거래량평균
    df["MA20"] = close.rolling(window=20, min_periods=1).mean()
    df["STD20"] = close.rolling(window=20, min_periods=1).std()
    df["BB_high"] = df["MA20"] + 2 * df["STD20"]
    df["BB_low"] = df["MA20"] - 2 * df["STD20"]

    # RSI
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(window=14, min_periods=1).mean()
    ma_down = down.rolling(window=14, min_periods=1).mean()
    rs = ma_up / (ma_down + 1e-8)
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # 거래량 평균(20)
    if "거래량" in df.columns:
        df["거래량평균20"] = df["거래량"].rolling(window=20, min_periods=1).mean()
    else:
        df["거래량평균20"] = np.nan

    # 신호: 거래량급증(오늘 거래량/20일평균), 등락률, 최고가갱신
    if "거래량" in df.columns:
        df["거래량급증"] = df["거래량"] / (df["거래량평균20"] + 1e-8)
    else:
        df["거래량급증"] = np.nan

    df["등락률"] = close.pct_change() * 100
    df["최고가갱신"] = (close >= close.rolling(window=60, min_periods=1).max()).astype(int)

    return df
