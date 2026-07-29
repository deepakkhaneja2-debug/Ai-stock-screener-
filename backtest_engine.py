import pandas as pd


class BacktestEngine:

    def __init__(self):
        pass

    def run(self, data):

        results = []

        for i in range(60, len(data) - 15):

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

                status = "OPEN"

                future = data.iloc[i + 1:i + 15]

                for _, candle in future.iterrows():

                    if candle["Low"] <= sl:
                        status = "LOSS"
                        break

                    if candle["High"] >= target:
                        status = "WIN"
                        break

                results.append({
                    "Date": next_row.name,
                    "Entry": round(entry, 2),
                    "SL": round(sl, 2),
                    "Target": round(target, 2),
                    "Status": status
                })

        wins = sum(1 for x in results if x["Status"] == "WIN")
        losses = sum(1 for x in results if x["Status"] == "LOSS")
        opens = sum(1 for x in results if x["Status"] == "OPEN")

        total = len(results)

        win_rate = round((wins / total) * 100, 2) if total else 0

        return {
            "Total Trades": total,
            "Wins": wins,
            "Losses": losses,
            "Open": opens,
            "Win Rate": win_rate,
            "Trades": results
        }