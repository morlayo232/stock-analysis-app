import pandas as pd
def calc_ema(df, window=20, col='종가'):
return df[col].ewm(span=window, adjust=False).mean()
def calc_rsi(df, window=14, col='종가'):
delta = df[col].diff()
up = delta.clip(lower=0)
down = -delta.clip(upper=0)
ma_up = up.rolling(window=window, min_periods=1).mean()
ma_down = down.rolling(window=window, min_periods=1).mean()
rs = ma_up / (ma_down + 1e-6)
return 100 - (100 / (1 + rs))
def calc_macd(df, col='종가'):
ema12 = df[col].ewm(span=12, adjust=False).mean()
ema26 = df[col].ewm(span=26, adjust=False).mean()
macd = ema12 - ema26
signal = macd.ewm(span=9, adjust=False).mean()
hist = macd - signal
return macd, signal, hist
def add_tech_indicators(df):
df['EMA20'] = calc_ema(df, 20)
df['RSI'] = calc_rsi(df, 14)
macd, signal, hist = calc_macd(df)
df['MACD'] = macd
df['Signal'] = signal
df['MACD_Hist'] = hist
return df
