import pandas as pd
import os


class PerformanceAnalyzer:
    """Analyzes trade history from CSV."""

    def __init__(self, file_name: str = "trade_history.csv"):
        self.file_name = file_name

    def _load(self) -> pd.DataFrame:
        if not os.path.exists(self.file_name):
            return pd.DataFrame()
        try:
            return pd.read_csv(self.file_name)
        except Exception:
            return pd.DataFrame()

    def summary(self) -> dict:
        df = self._load()
        if df.empty:
            return {"TotalTrades": 0, "Wins": 0, "Losses": 0, "WinRate": 0}

        total = len(df)
        wins = len(df[df["PnL"] > 0])
        losses = len(df[df["PnL"] <= 0])
        winrate = round((wins / total) * 100, 2) if total > 0 else 0

        return {
            "TotalTrades": total,
            "Wins": wins,
            "Losses": losses,
            "WinRate": winrate
        }

    def average_profit(self) -> float:
        df = self._load()
        if df.empty:
            return 0.0
        profit = df[df["PnL"] > 0]
        return round(profit["PnL"].mean(), 2) if not profit.empty else 0.0

    def average_loss(self) -> float:
        df = self._load()
        if df.empty:
            return 0.0
        loss = df[df["PnL"] <= 0]
        return round(loss["PnL"].mean(), 2) if not loss.empty else 0.0

    def best_pattern(self) -> pd.Series:
        df = self._load()
        if df.empty or "Pattern" not in df.columns:
            return pd.Series()
        return df.groupby("Pattern")["PnL"].mean().sort_values(ascending=False).head(5)

    def loss_reason(self) -> pd.Series:
        df = self._load()
        if df.empty or "Reason" not in df.columns:
            return pd.Series()
        loss = df[df["PnL"] <= 0]
        return loss["Reason"].value_counts() if not loss.empty else pd.Series()