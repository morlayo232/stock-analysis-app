import pandas as pd

def update_single_stock(code):
    # 실제 구현 필요
    df = pd.read_csv("filtered_stocks.csv")
    # ... 갱신 로직 ...
    df.to_csv("filtered_stocks.csv", index=False)

def update_database():
    # 전체 갱신 예시
    df = pd.read_csv("filtered_stocks.csv")
    # ... 전체 종목 갱신로직 ...
    df.to_csv("filtered_stocks.csv", index=False)
