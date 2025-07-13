import ta

def calculate_indicators(df):
    df["EMA5"] = ta.trend.EMAIndicator(df["Close"], window=5).ema_indicator()
    df["EMA20"] = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["Signal"] = macd.macd_signal()
<<<<<<< HEAD
    return df
=======
    return df
>>>>>>> 4a27f38146733656025b2d13e5b4cc219821c6cb
