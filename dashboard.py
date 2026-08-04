import pandas as pd
from typing import Dict, Any


class DashboardEngine:
    """Generates dashboard views and statistics."""

    def __init__(self):
        pass

    def top_buy(self, data: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Return top BUY signals sorted by confidence."""
        if data.empty or "Signal" not in data.columns:
            return pd.DataFrame()
        df = data[data["Signal"] == "BUY"]
        return df.sort_values("Confidence", ascending=False).head(limit)

    def top_sell(self, data: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Return top SELL signals sorted by confidence."""
        if data.empty or "Signal" not in data.columns:
            return pd.DataFrame()
        df = data[data["Signal"] == "SELL"]
        return df.sort_values("Confidence", ascending=False).head(limit)

    def watchlist(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return WATCH signals."""
        if data.empty or "Signal" not in data.columns:
            return pd.DataFrame()
        return data[data["Signal"] == "WATCH"]

    def sort(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        """Sort DataFrame by column."""
        if data.empty or column not in data.columns:
            return pd.DataFrame()
        return data.sort_values(column, ascending=False)

    def search(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Search for symbol in DataFrame."""
        if data.empty or "Symbol" not in data.columns:
            return pd.DataFrame()
        return data[data["Symbol"].str.contains(symbol, case=False)]

    def summary(self, data: pd.DataFrame) -> Dict[str, int]:
        """Return summary counts."""
        if data.empty or "Signal" not in data.columns:
            return {"BUY": 0, "SELL": 0, "WATCH": 0}
        return {
            "BUY": len(data[data["Signal"] == "BUY"]),
            "SELL": len(data[data["Signal"] == "SELL"]),
            "WATCH": len(data[data["Signal"] == "WATCH"])
        }

    def overall_stats(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall statistics from backtest reports."""
        if not reports:
            return {
                "Total Trades": 0,
                "Closed Trades": 0,
                "Wins": 0,
                "Losses": 0,
                "BreakEven": 0,
                "Win Rate": 0,
                "Total PnL": 0,
                "Profit Factor": 0,
                "AI Score": 0
            }

        all_trades = []
        for symbol, report in reports.items():
            if isinstance(report, dict) and "Trades" in report:
                all_trades.extend(report.get("Trades", []))

        if not all_trades:
            return {
                "Total Trades": 0,
                "Closed Trades": 0,
                "Wins": 0,
                "Losses": 0,
                "BreakEven": 0,
                "Win Rate": 0,
                "Total PnL": 0,
                "Profit Factor": 0,
                "AI Score": 0
            }

        total = len(all_trades)
        wins = sum(1 for t in all_trades if t.get("Status") == "WIN")
        losses = sum(1 for t in all_trades if t.get("Status") == "LOSS")
        break_even = sum(1 for t in all_trades if t.get("Status") == "BREAK_EVEN")
        closed = wins + losses + break_even

        win_rate = round((wins / closed) * 100, 2) if closed > 0 else 0

        total_pnl = round(sum(t.get("PnL", 0) for t in all_trades), 2)

        profits = [t.get("PnL", 0) for t in all_trades if t.get("Status") == "WIN"]
        losses_list = [t.get("PnL", 0) for t in all_trades if t.get("Status") == "LOSS"]

        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

        # Average AI Score across symbols
        ai_scores = []
        for symbol, report in reports.items():
            if isinstance(report, dict) and "AI Score" in report:
                ai_scores.append(report["AI Score"])
        avg_ai_score = round(sum(ai_scores) / len(ai_scores), 0) if ai_scores else 0

        return {
            "Total Trades": total,
            "Closed Trades": closed,
            "Wins": wins,
            "Losses": losses,
            "BreakEven": break_even,
            "Win Rate": win_rate,
            "Total PnL": total_pnl,
            "Profit Factor": profit_factor,
            "AI Score": avg_ai_score
        }

    def ranking_table(self, reports: Dict[str, Any]) -> pd.DataFrame:
        """Generate ranking table sorted by multiple metrics."""
        if not reports:
            return pd.DataFrame()

        rows = []
        for symbol, report in reports.items():
            if isinstance(report, dict):
                rows.append({
                    "Symbol": symbol,
                    "AI Score": report.get("AI Score", 0),
                    "Profit Factor": report.get("Profit Factor", 0),
                    "Win Rate": report.get("Win Rate", 0),
                    "Total PnL": report.get("Total PnL", 0),
                    "Total Trades": report.get("Total Trades", 0),
                    "Wins": report.get("Wins", 0),
                    "Losses": report.get("Losses", 0)
                })

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Sort by multiple criteria
        return df.sort_values(
            by=["AI Score", "Profit Factor", "Win Rate", "Total PnL"],
            ascending=[False, False, False, False]
        )