import pandas as pd


class BacktestAnalyzer:

    def __init__(self):
        pass

    # =========================================
    # ANALYZE ONE BACKTEST REPORT
    # =========================================

    def analyze(self, report):

        if not isinstance(report, dict):
            return {}

        trades = report.get("Trades", [])

        if not trades:
            return {
                "Total Trades": 0,
                "Closed Trades": 0,
                "Wins": 0,
                "Losses": 0,
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
                "Status": "NO TRADES"
            }

        # =========================================
        # BASIC COUNTS
        # =========================================

        total = len(trades)

        wins = sum(
            1
            for trade in trades
            if trade.get("Status") == "WIN"
        )

        losses = sum(
            1
            for trade in trades
            if trade.get("Status") == "LOSS"
        )

        opens = sum(
            1
            for trade in trades
            if trade.get("Status") == "OPEN"
        )

        closed = wins + losses

        # =========================================
        # WIN / LOSS RATE
        # =========================================

        if closed > 0:

            win_rate = round(
                wins / closed * 100,
                2
            )

            loss_rate = round(
                losses / closed * 100,
                2
            )

        else:

            win_rate = 0
            loss_rate = 0

        # =========================================
        # P&L
        # =========================================

        pnls = [
            float(trade.get("PnL", 0))
            for trade in trades
        ]

        total_pnl = round(
            sum(pnls),
            2
        )

        # =========================================
        # PROFIT / LOSS
        # =========================================

        profits = [
            pnl
            for pnl in pnls
            if pnl > 0
        ]

        losses_list = [
            pnl
            for pnl in pnls
            if pnl < 0
        ]

        if profits:

            average_profit = round(
                sum(profits) / len(profits),
                2
            )

        else:

            average_profit = 0

        if losses_list:

            average_loss = round(
                sum(losses_list) / len(losses_list),
                2
            )

        else:

            average_loss = 0

        # =========================================
        # PROFIT FACTOR
        # =========================================

        gross_profit = sum(profits)

        gross_loss = abs(
            sum(losses_list)
        )

        if gross_loss > 0:

            profit_factor = round(
                gross_profit / gross_loss,
                2
            )

        else:

            profit_factor = 0

        # =========================================
        # BEST / WORST TRADE
        # =========================================

        best_trade = round(
            max(pnls),
            2
        )

        worst_trade = round(
            min(pnls),
            2
        )

        # =========================================
        # MAX DRAWDOWN
        # =========================================

        equity = 0
        peak = 0
        max_drawdown = 0

        for pnl in pnls:

            equity += pnl

            peak = max(
                peak,
                equity
            )

            drawdown = equity - peak

            max_drawdown = min(
                max_drawdown,
                drawdown
            )

        max_drawdown = round(
            max_drawdown,
            2
        )

        # =========================================
        # TARGETS
        # =========================================

        target1_wins = sum(
            1
            for trade in trades
            if trade.get("TargetHit") == "TARGET1"
        )

        target2_wins = sum(
            1
            for trade in trades
            if trade.get("TargetHit") == "TARGET2"
        )

        target3_wins = sum(
            1
            for trade in trades
            if trade.get("TargetHit") == "TARGET3"
        )

        # =========================================
        # CONSECUTIVE WINS / LOSSES
        # =========================================

        current_wins = 0
        current_losses = 0

        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for trade in trades:

            status = trade.get("Status")

            if status == "WIN":

                current_wins += 1
                current_losses = 0

            elif status == "LOSS":

                current_losses += 1
                current_wins = 0

            else:

                continue

            max_consecutive_wins = max(
                max_consecutive_wins,
                current_wins
            )

            max_consecutive_losses = max(
                max_consecutive_losses,
                current_losses
            )

        # =========================================
        # EXPECTANCY
        # =========================================

        if closed > 0:

            expectancy = round(
                total_pnl / closed,
                2
            )

        else:

            expectancy = 0

        # =========================================
        # STRATEGY STATUS
        # =========================================

        if closed < 10:

            strategy_status = "INSUFFICIENT DATA"

        elif profit_factor > 1.5 and expectancy > 0:

            strategy_status = "STRONG"

        elif profit_factor > 1.0 and expectancy > 0:

            strategy_status = "PROFITABLE"

        else:

            strategy_status = "WEAK"

        # =========================================
        # FINAL ANALYSIS
        # =========================================

        return {

            "Total Trades": total,

            "Closed Trades": closed,

            "Wins": wins,

            "Losses": losses,

            "Open": opens,

            "Win Rate": win_rate,

            "Loss Rate": loss_rate,

            "Total PnL": total_pnl,

            "Average Profit": average_profit,

            "Average Loss": average_loss,

            "Profit Factor": profit_factor,

            "Max Drawdown": max_drawdown,

            "Target1 Wins": target1_wins,

            "Target2 Wins": target2_wins,

            "Target3 Wins": target3_wins,

            "Best Trade": best_trade,

            "Worst Trade": worst_trade,

            "Consecutive Wins": max_consecutive_wins,

            "Consecutive Losses": max_consecutive_losses,

            "Expectancy": expectancy,

            "Status": strategy_status
        }