import pandas as pd

def add_tech_indicators(df):
    df['EMA_20'] = df['종가'].ewm(span=20, adjust=False).mean()
    delta = df['종가'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(window=14, min_periods=1).mean()
    ma_down = down.rolling(window=14, min_periods=1).mean()
    rs = ma_up / (ma_down + 1e-6)
    df['RSI_14'] = 100 - (100 / (1 + rs))
    ema12 = df['종가'].ewm(span=12, adjust=False).mean()
    ema26 = df['종가'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_HIST'] = df['MACD'] - df['MACD_SIGNAL']
    return df
