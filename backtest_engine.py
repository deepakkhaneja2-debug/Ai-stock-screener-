import pandas as pd


class BacktestEngine:

    def __init__(self):
        pass

    def run(self, data):

        trades = []
        capital = 100000
results = []

for i in range(60, len(data) - 1):

    row = data.iloc[i]
    next_row = data.iloc[i + 1]

    buy = (
        row["EMA20"] > row["EMA50"]
        and row["MACD"] > row["MACD_SIGNAL"]
        and row["RSI"] > 55
    )

    if buy:

        entry = float(next_row["Open"])
        sl = entry - float(row["ATR"]) * 1.5
        target = entry + (entry - sl) * 3

        results.append({
            "Date": next_row.name,
            "Entry": entry,
            "SL": sl,
            "Target": target
        })
future = data.iloc[i + 1 : i + 15]

status = "OPEN"

for _, candle in future.iterrows():

    if candle["Low"] <= sl:
        status = "LOSS"
        break

    if candle["High"] >= target:
        status = "WIN"
        break

results[-1]["Status"] = status
        return {
            "Total Trades": 0,
            "Wins": 0,
            "Losses": 0,
            "Win Rate": 0,
            "Net Profit": 0,
            "Capital": capital,
            "Trades": trades
        }