import pandas as pd
import os
from datetime import datetime


class PerformanceAnalyzer:
    """Enhanced performance analysis with monthly P&L and metrics."""

    def __init__(self, file_name: str = "trade_history.csv"):
        self.file_name = file_name

    def _load(self) -> pd.DataFrame:
        if not os.path.exists(self.file_name):
            return pd.DataFrame()
        try:
            df = pd.read_csv(self.file_name)
            # Convert date column if exists
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            return df
        except Exception:
            return pd.DataFrame()

    def summary(self) -> dict:
        df = self._load()
        if df.empty:
            return {
                "TotalTrades": 0,
                "Wins": 0,
                "Losses": 0,
                "BreakEven": 0,
                "WinRate": 0,
                "TotalPnL": 0,
                "AverageProfit": 0,
                "AverageLoss": 0,
                "ProfitFactor": 0,
                "Expectancy": 0
            }

        total = len(df)
        wins = len(df[df["PnL"] > 0])
        losses = len(df[df["PnL"] < 0])
        break_even = len(df[df["PnL"] == 0])
        winrate = round((wins / total) * 100, 2) if total > 0 else 0

        total_pnl = df["PnL"].sum()
        avg_profit = df[df["PnL"] > 0]["PnL"].mean() if wins > 0 else 0
        avg_loss = df[df["PnL"] < 0]["PnL"].mean() if losses > 0 else 0

        gross_profit = df[df["PnL"] > 0]["PnL"].sum()
        gross_loss = abs(df[df["PnL"] < 0]["PnL"].sum())
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

        expectancy = round((wins/total * avg_profit) + (losses/total * avg_loss), 2) if total > 0 else 0

        return {
            "TotalTrades": total,
            "Wins": wins,
            "Losses": losses,
            "BreakEven": break_even,
            "WinRate": winrate,
            "TotalPnL": round(total_pnl, 2),
            "AverageProfit": round(avg_profit, 2),
            "AverageLoss": round(avg_loss, 2),
            "ProfitFactor": profit_factor,
            "Expectancy": expectancy
        }

    def monthly_report(self) -> pd.DataFrame:
        """Generate monthly P&L report."""
        df = self._load()
        if df.empty or "Date" not in df.columns:
            return pd.DataFrame()

        df["Month"] = df["Date"].dt.to_period("M")
        monthly = df.groupby("Month")["PnL"].sum().reset_index()
        monthly.columns = ["Month", "PnL"]
        return monthly.sort_values("Month")

    def equity_curve(self) -> pd.DataFrame:
        """Generate equity curve from trade history."""
        df = self._load()
        if df.empty:
            return pd.DataFrame()

        df = df.sort_values("Date")
        df["Equity"] = df["PnL"].cumsum()
        return df[["Date", "Equity"]]

    def drawdown_curve(self) -> pd.DataFrame:
        """Generate drawdown curve."""
        df = self._load()
        if df.empty:
            return pd.DataFrame()

        df = df.sort_values("Date")
        df["Equity"] = df["PnL"].cumsum()
        df["Peak"] = df["Equity"].cummax()
        df["Drawdown"] = df["Equity"] - df["Peak"]
        return df[["Date", "Drawdown"]]

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
        loss = df[df["PnL"] < 0]
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
        loss = df[df["PnL"] < 0]
        return loss["Reason"].value_counts() if not loss.empty else pd.Series()

    def win_rate_by_strategy(self) -> pd.DataFrame:
        """Calculate win rate by strategy."""
        df = self._load()
        if df.empty or "Signal" not in df.columns:
            return pd.DataFrame()
        
        stats = df.groupby("Signal").agg({
            "PnL": ["count", lambda x: (x > 0).sum(), lambda x: (x < 0).sum()]
        })
        stats.columns = ["Total", "Wins", "Losses"]
        stats["WinRate"] = (stats["Wins"] / stats["Total"] * 100).round(2)
        return stats.sort_values("WinRate", ascending=False)