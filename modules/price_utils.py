# modules/price_utils.py

def calculate_recommended_sell(buy_price, df_price):
    if buy_price <= 0:
        return None
    target_price = buy_price * 1.1  # 목표 10% 수익률

    ema20_last = df_price['EMA_20'].iloc[-1] if 'EMA_20' in df_price.columns else None
    recent_high = df_price['종가'].rolling(window=20).max().iloc[-1] if '종가' in df_price.columns else None

    if ema20_last and target_price < ema20_last:
        target_price = ema20_last

    if recent_high and target_price < recent_high:
        target_price = recent_high

    return target_price
