import pandas as pd


class DashboardEngine:

    def __init__(self):
        pass

    # ==============================
    # TOP BUY
    # ==============================

    def top_buy(self, data, limit=10):

        df = data.copy()

        df = df[df["Signal"] == "BUY"]

        df = df.sort_values(
            "Confidence",
            ascending=False
        )

        return df.head(limit)

    # ==============================
    # TOP SELL
    # ==============================

    def top_sell(self, data, limit=10):

        df = data.copy()

        df = df[df["Signal"] == "SELL"]

        df = df.sort_values(
            "Confidence",
            ascending=False
        )

        return df.head(limit)

    # ==============================
    # WATCHLIST
    # ==============================

    def watchlist(self, data):

        return data[data["Signal"] == "WATCH"]

    # ==============================
    # SORT
    # ==============================

    def sort(self, data, column):

        return data.sort_values(
            column,
            ascending=False
        )

    # ==============================
    # SEARCH
    # ==============================

    def search(self, data, symbol):

        return data[
            data["Symbol"].str.contains(
                symbol,
                case=False
            )
        ]

    # ==============================
    # SUMMARY
    # ==============================

    def summary(self, data):

        return {

            "BUY":
            len(data[data["Signal"] == "BUY"]),

            "SELL":
            len(data[data["Signal"] == "SELL"]),

            "WATCH":
            len(data[data["Signal"] == "WATCH"])

        }
