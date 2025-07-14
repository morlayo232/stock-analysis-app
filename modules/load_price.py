from pykrx import stock

def load_price_history(code, start="20240101", end="20250714"): try: df = stock.get_market_ohlcv_by_date(start, end, code) return df except: return None

