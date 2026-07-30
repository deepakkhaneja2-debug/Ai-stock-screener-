import pandas as pd


class BacktestEngine:

    def __init__(self):
        self.lookahead_days = 15
        self.risk_per_trade = 0.01
        self.min_trades_for_ranking = 3

    def run(self, data):

        results = []

        if data is None or data.empty:
            return self.summary(results)

        data = data.copy()

        required = [
            "Close", "High", "Low",
            "EMA20", "EMA50", "RSI",
            "MACD", "MACD_SIGNAL", "ATR", "VWAP"
        ]

        for column in required:
            if column not in data.columns:
                return self.summary(results)

        data = data.dropna(subset=required).copy()

        if len(data) < 61:
            return self.summary(results)

        next_available_index = 60

        for i in range(60, len(data) - 1):

            if i < next_available_index:
                continue

            row = data.iloc[i]

            try:
                ema20 = float(row["EMA20"])
                ema50 = float(row["EMA50"])
                rsi = float(row["RSI"])
                macd = float(row["MACD"])
                macd_signal = float(row["MACD_SIGNAL"])
                close = float(row["Close"])
                atr = float(row["ATR"])
                vwap = float(row["VWAP"])
            except (TypeError, ValueError):
                continue

            if atr <= 0 or close <= 0:
                continue

            buy_setup = (
                ema20 > ema50
                and macd > macd_signal
                and 55 < rsi < 70
                and close > vwap
            )

            if not buy_setup:
                continue

            entry = round(close + atr * 0.25, 2)
            stoploss = round(entry - atr * 1.5, 2)
            risk = round(entry - stoploss, 2)

            if risk <= 0:
                continue

            target1 = round(entry + risk * 1.5, 2)
            target2 = round(entry + risk * 2.5, 2)
            target3 = round(entry + risk * 4.0, 2)

            entry_index = None

            for j in range(i + 1, len(data)):

                try:
                    high = float(data.iloc[j]["High"])
                except (TypeError, ValueError):
                    continue

                if high >= entry:
                    entry_index = j
                    break

            if entry_index is None:
                continue

            status = "OPEN"
            exit_price = None
            exit_date = None
            target_hit = "NONE"

            highest_price = entry
            lowest_price = entry

            end_index = min(
                entry_index + self.lookahead_days,
                len(data)
            )

            last_index = end_index - 1

            for j in range(entry_index, end_index):

                candle = data.iloc[j]

                try:
                    low = float(candle["Low"])
                    high = float(candle["High"])
                except (TypeError, ValueError):
                    continue

                highest_price = max(highest_price, high)
                lowest_price = min(lowest_price, low)

                # Conservative same-candle rule: SL first.
                if low <= stoploss:
                    status = "LOSS"
                    exit_price = stoploss
                    exit_date = candle.name
                    break

                if high >= target3:
                    status = "WIN"
                    exit_price = target3
                    exit_date = candle.name
                    target_hit = "TARGET3"
                    break

                if high >= target2:
                    status = "WIN"
                    exit_price = target2
                    exit_date = candle.name
                    target_hit = "TARGET2"
                    break

                if high >= target1:
                    status = "WIN"
                    exit_price = target1
                    exit_date = candle.name
                    target_hit = "TARGET1"
                    break

            if status == "OPEN":

                try:
                    mark_price = float(data.iloc[last_index]["Close"])
                except (TypeError, ValueError):
                    mark_price = close

                unrealized_pnl = round(mark_price - entry, 2)
                current_price = mark_price

            else:
                unrealized_pnl = 0.0
                current_price = exit_price

            pnl = 0.0
            pnl_percent = 0.0
            r_multiple = 0.0

            if exit_price is not None:

                pnl = round(exit_price - entry, 2)

                pnl_percent = round(
                    (pnl / entry) * 100,
                    2
                )

                r_multiple = round(pnl / risk, 2)

            else:
                r_multiple = round(
                    unrealized_pnl / risk,
                    2
                )

            mfe = round(highest_price - entry, 2)
            mae = round(lowest_price - entry, 2)

            mfe_r = round(mfe / risk, 2)
            mae_r = round(mae / risk, 2)

            results.append({

                "Date": data.iloc[entry_index].name,
                "SignalDate": row.name,

                "Entry": entry,
                "CurrentPrice": current_price,
                "StopLoss": stoploss,

                "Target1": target1,
                "Target2": target2,
                "Target3": target3,

                "RR": round(
                    (target2 - entry) / risk,
                    2
                ),

                "RiskPerTrade": self.risk_per_trade,
                "Quantity": 1,

                "ExitPrice": exit_price,
                "ExitDate": exit_date,

                "TargetHit": target_hit,
                "Status": status,

                "PnL": pnl,
                "UnrealizedPnL": unrealized_pnl,

                "TotalPnL": round(
                    pnl + unrealized_pnl,
                    2
                ),

                "PnLPercent": pnl_percent,
                "RMultiple": r_multiple,

                "MFE": mfe,
                "MAE": mae,
                "MFE_R": mfe_r,
                "MAE_R": mae_r
            })

            next_available_index = max(
                entry_index + 1,
                end_index
            )

        return self.summary(results)

    def summary(self, results):

        total = len(results)

        wins = sum(
            1 for trade in results
            if trade.get("Status") == "WIN"
        )

        losses = sum(
            1 for trade in results
            if trade.get("Status") == "LOSS"
        )

        opens = sum(
            1 for trade in results
            if trade.get("Status") == "OPEN"
        )

        closed = wins + losses

        win_rate = (
            round((wins / closed) * 100, 2)
            if closed > 0 else 0.0
        )

        loss_rate = (
            round((losses / closed) * 100, 2)
            if closed > 0 else 0.0
        )

        realized_pnl = round(
            sum(float(t.get("PnL", 0)) for t in results),
            2
        )

        unrealized_pnl = round(
            sum(
                float(t.get("UnrealizedPnL", 0))
                for t in results
                if t.get("Status") == "OPEN"
            ),
            2
        )

        total_pnl = round(
            realized_pnl + unrealized_pnl,
            2
        )

        closed_pnls = [
            float(t.get("PnL", 0))
            for t in results
            if t.get("Status") in ("WIN", "LOSS")
        ]

        profits = [p for p in closed_pnls if p > 0]
        losses_list = [p for p in closed_pnls if p < 0]

        average_profit = (
            round(sum(profits) / len(profits), 2)
            if profits else 0.0
        )

        average_loss = (
            round(sum(losses_list) / len(losses_list), 2)
            if losses_list else 0.0
        )

        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))

        if gross_loss > 0:
            profit_factor = round(
                gross_profit / gross_loss,
                2
            )
        elif gross_profit > 0:
            profit_factor = 999.0
        else:
            profit_factor = 0.0

        expectancy = (
            round(realized_pnl / closed, 2)
            if closed > 0 else 0.0
        )

        closed_r = [
            float(t.get("RMultiple", 0))
            for t in results
            if t.get("Status") in ("WIN", "LOSS")
        ]

        average_r = (
            round(sum(closed_r) / len(closed_r), 2)
            if closed_r else 0.0
        )

        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for trade in results:

            if trade.get("Status") not in ("WIN", "LOSS"):
                continue

            equity += float(trade.get("PnL", 0))
            peak = max(peak, equity)

            max_drawdown = min(
                max_drawdown,
                equity - peak
            )

        max_drawdown = round(max_drawdown, 2)

        target1_wins = sum(
            1 for t in results
            if t.get("TargetHit") == "TARGET1"
        )

        target2_wins = sum(
            1 for t in results
            if t.get("TargetHit") == "TARGET2"
        )

        target3_wins = sum(
            1 for t in results
            if t.get("TargetHit") == "TARGET3"
        )

        current_wins = 0
        current_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for trade in results:

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

        if closed >= self.min_trades_for_ranking:

            pf_component = (
                min(profit_factor, 5.0) / 5.0
            ) * 30.0

            win_component = (
                win_rate / 100.0
            ) * 30.0

            expectancy_component = (
                max(min(expectancy, 100.0), -100.0) / 100.0
            ) * 20.0

            drawdown_component = max(
                0.0,
                20.0 - abs(max_drawdown) * 0.10
            )

            risk_adjusted_score = round(
                pf_component
                + win_component
                + expectancy_component
                + drawdown_component,
                2
            )

        else:
            risk_adjusted_score = 0.0

        if closed < self.min_trades_for_ranking:
            strategy_status = "INSUFFICIENT DATA"
        elif profit_factor >= 2.0 and expectancy > 0:
            strategy_status = "STRONG"
        elif profit_factor > 1.0 and expectancy > 0:
            strategy_status = "PROFITABLE"
        else:
            strategy_status = "WEAK"

        return {

            "Total Trades": total,
            "Wins": wins,
            "Losses": losses,
            "Open": opens,
            "Closed Trades": closed,

            "Win Rate": win_rate,
            "Loss Rate": loss_rate,

            "Realized PnL": realized_pnl,
            "Unrealized PnL": unrealized_pnl,
            "Total PnL": total_pnl,

            "Average Profit": average_profit,
            "Average Loss": average_loss,

            "Profit Factor": profit_factor,
            "Expectancy": expectancy,
            "Average R": average_r,

            "Max Drawdown": max_drawdown,

            "Target1 Wins": target1_wins,
            "Target2 Wins": target2_wins,
            "Target3 Wins": target3_wins,

            "Consecutive Wins": max_consecutive_wins,
            "Consecutive Losses": max_consecutive_losses,

            "Risk Adjusted Score": risk_adjusted_score,

            "Status": strategy_status,

            "Trades": results
        }
