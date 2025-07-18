import pandas as pd

def calc_ema(df: pd.DataFrame, window: int = 20, col: str = '종가') -> pd.Series:
    return df[col].ewm(span=window, adjust=False).mean()

def calc_rsi(df: pd.DataFrame, window: int = 14, col: str = '종가') -> pd.Series:
    delta = df[col].diff()
    up   = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up   = up.rolling(window).mean()
    ma_down = down.rolling(window).mean()
    rs = ma_up / (ma_down + 1e-6)
    return 100 - (100 / (1 + rs))

def calc_macd(df: pd.DataFrame, col: str = '종가'):
    ema12 = df[col].ewm(span=12, adjust=False).mean()
    ema26 = df[col].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist
