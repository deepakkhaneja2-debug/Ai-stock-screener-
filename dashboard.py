import pandas as pd
from typing import Dict, Any


class DashboardEngine:
    """Generates dashboard views and statistics."""

    def __init__(self):
        pass

    # ... (other methods remain the same as before) ...

    def overall_stats(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall statistics from backtest reports.
        Each report is a dictionary containing backtest results.
        """
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
        ai_scores = []

        # Iterate through each symbol's report
        for symbol, report in reports.items():
            if not isinstance(report, dict):
                continue

            # The report already contains the metrics
            # 'Trades' is a key inside each report dictionary
            trades = report.get("Trades", [])
            if isinstance(trades, list):
                all_trades.extend(trades)

            # Collect AI Score
            ai_score = report.get("AI Score", 0)
            if isinstance(ai_score, (int, float)):
                ai_scores.append(ai_score)

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

        # Calculate aggregate stats
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

        # Sort by multiple criteria (AI Score > Profit Factor > Win Rate > Total PnL)
        return df.sort_values(
            by=["AI Score", "Profit Factor", "Win Rate", "Total PnL"],
            ascending=[False, False, False, False]
        )