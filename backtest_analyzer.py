import pandas as pd
import numpy as np


class BacktestAnalyzer:
    """Advanced backtest analysis with AI Score and performance metrics."""

    def analyze(self, report: dict) -> dict:
        if not isinstance(report, dict):
            return {}

        trades = report.get("Trades", [])
        if not trades:
            return self._empty_analysis()

        total = len(trades)
        wins = sum(1 for t in trades if t.get("Status") == "WIN")
        losses = sum(1 for t in trades if t.get("Status") == "LOSS")
        break_even = sum(1 for t in trades if t.get("Status") == "BREAK_EVEN")
        opens = sum(1 for t in trades if t.get("Status") == "OPEN")
        closed = wins + losses + break_even

        win_rate = round((wins / closed) * 100, 2) if closed > 0 else 0
        loss_rate = round((losses / closed) * 100, 2) if closed > 0 else 0

        pnls = [float(t.get("PnL", 0)) for t in trades if t.get("Status") != "OPEN"]
        total_pnl = round(sum(pnls), 2)

        profits = [p for p in pnls if p > 0]
        losses_list = [p for p in pnls if p < 0]

        avg_profit = round(sum(profits) / len(profits), 2) if profits else 0
        avg_loss = round(sum(losses_list) / len(losses_list), 2) if losses_list else 0

        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

        best_trade = round(max(pnls), 2) if pnls else 0
        worst_trade = round(min(pnls), 2) if pnls else 0

        # Max drawdown
        equity = 0
        peak = 0
        max_dd = 0
        for p in pnls:
            equity += p
            peak = max(peak, equity)
            max_dd = min(max_dd, equity - peak)
        max_drawdown = round(max_dd, 2)

        # Target hits
        target1_wins = sum(1 for t in trades if t.get("TargetHit") == "TARGET1")
        target2_wins = sum(1 for t in trades if t.get("TargetHit") == "TARGET2")
        target3_wins = sum(1 for t in trades if t.get("TargetHit") == "TARGET3")

        # Consecutive wins/losses
        cur_w = cur_l = max_w = max_l = 0
        for t in trades:
            status = t.get("Status")
            if status == "WIN":
                cur_w += 1
                cur_l = 0
            elif status == "LOSS":
                cur_l += 1
                cur_w = 0
            else:
                continue
            max_w = max(max_w, cur_w)
            max_l = max(max_l, cur_l)

        # Expectancy
        expectancy = round(total_pnl / closed, 2) if closed > 0 else 0

        # AI Score (0-100) - combines multiple metrics
        ai_score = self._calculate_ai_score(
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            max_drawdown=max_drawdown,
            total_trades=total,
            avg_r=report.get("Average R", 0),
            avg_hold_days=report.get("Average Holding Days", 0)
        )

        # Strategy status
        if closed < 10:
            strategy_status = "INSUFFICIENT DATA"
        elif profit_factor > 1.5 and expectancy > 0:
            strategy_status = "STRONG"
        elif profit_factor > 1.0 and expectancy > 0:
            strategy_status = "PROFITABLE"
        else:
            strategy_status = "WEAK"

        return {
            "Total Trades": total,
            "Closed Trades": closed,
            "Wins": wins,
            "Losses": losses,
            "BreakEven": break_even,
            "Open": opens,
            "Win Rate": win_rate,
            "Loss Rate": loss_rate,
            "Total PnL": total_pnl,
            "Average Profit": avg_profit,
            "Average Loss": avg_loss,
            "Profit Factor": profit_factor,
            "Max Drawdown": max_drawdown,
            "Target1 Wins": target1_wins,
            "Target2 Wins": target2_wins,
            "Target3 Wins": target3_wins,
            "Best Trade": best_trade,
            "Worst Trade": worst_trade,
            "Consecutive Wins": max_w,
            "Consecutive Losses": max_l,
            "Expectancy": expectancy,
            "AI Score": ai_score,
            "Status": strategy_status
        }

    def _calculate_ai_score(self, win_rate: float, profit_factor: float,
                           expectancy: float, max_drawdown: float,
                           total_trades: int, avg_r: float,
                           avg_hold_days: float) -> int:
        """Calculate AI Score (0-100) based on multiple performance metrics."""
        if total_trades == 0:
            return 0

        # Win rate component (0-30)
        win_rate_score = min(30, win_rate * 0.3)

        # Profit factor component (0-25)
        pf_score = min(25, profit_factor * 5)

        # Expectancy component (0-20)
        exp_score = min(20, max(0, expectancy))

        # Drawdown penalty (0-15)
        dd_penalty = min(15, max_drawdown * 0.15)

        # Average R component (0-10)
        r_score = min(10, avg_r * 2)

        # Total
        raw_score = win_rate_score + pf_score + exp_score - dd_penalty + r_score
        ai_score = max(0, min(100, int(raw_score)))

        return ai_score

    def _empty_analysis(self) -> dict:
        return {
            "Total Trades": 0,
            "Closed Trades": 0,
            "Wins": 0,
            "Losses": 0,
            "BreakEven": 0,
            "Open": 0,
            "Win Rate": 0,
            "Loss Rate": 0,
            "Total PnL": 0,
            "Average Profit": 0,
            "Average Loss": 0,
            "Profit Factor": 0,
            "Max Drawdown": 0,
            "Target1 Wins": 0,
            "Target2 Wins": 0,
            "Target3 Wins": 0,
            "Best Trade": 0,
            "Worst Trade": 0,
            "Consecutive Wins": 0,
            "Consecutive Losses": 0,
            "Expectancy": 0,
            "AI Score": 0,
            "Status": "NO TRADES"
        }