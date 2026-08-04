import pandas as pd


class DashboardEngine:
    """Generates top BUY/SELL, watchlist, and summary tables."""

    def top_buy(self, data: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        if data.empty or "Signal" not in data.columns:
            return pd.DataFrame()
        df = data[data["Signal"] == "BUY"]
        return df.sort_values("Confidence", ascending=False).head(limit)

    def top_sell(self, data: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        if data.empty or "Signal" not in data.columns:
            return pd.DataFrame()
        df = data[data["Signal"] == "SELL"]
        return df.sort_values("Confidence", ascending=False).head(limit)

    def watchlist(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty or "Signal" not in data.columns:
            return pd.DataFrame()
        return data[data["Signal"] == "WATCH"]

    def sort(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        if data.empty or column not in data.columns:
            return pd.DataFrame()
        return data.sort_values(column, ascending=False)

    def search(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        if data.empty or "Symbol" not in data.columns:
            return pd.DataFrame()
        return data[data["Symbol"].str.contains(symbol, case=False)]

    def summary(self, data: pd.DataFrame) -> dict:
        if data.empty or "Signal" not in data.columns:
            return {"BUY": 0, "SELL": 0, "WATCH": 0}
        return {
            "BUY": len(data[data["Signal"] == "BUY"]),
            "SELL": len(data[data["Signal"] == "SELL"]),
            "WATCH": len(data[data["Signal"] == "WATCH"])
        }